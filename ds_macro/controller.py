import asyncio
import logging
import subprocess
import time
import math
import json
from contextlib import contextmanager
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable
from subprocess import CalledProcessError

from .models import (
    ControllerConfig,
    MouseButton,
    MovementDirection,
    InputAction,
    ActionSequence,
    KeyPress,
    KeyRelease,
    KeyTap,
    Wait,
    Turn,
    MouseMove,
    MousePress,
    MouseRelease,
    MouseClick,
)
from .exceptions import (
    MouseMovementError,
    KeyboardError,
    XdotoolError,
    DSControllerError,
)

logger = logging.getLogger(__name__)


class ActionGroup:
    """A group of actions that can be executed together"""

    def __init__(self, parallel: bool = True):
        self.actions: List[InputAction] = []
        self.parallel = parallel

    def press(self, key: str):
        """Press a key and hold it"""
        self.actions.append(KeyPress(key=key))
        return self

    def release(self, key: str):
        """Release a previously pressed key"""
        self.actions.append(KeyRelease(key=key))
        return self

    def tap(self, key: str, duration: float = 0.1):
        """Tap a key (press and release)"""
        self.actions.append(KeyTap(key=key, duration=duration))
        return self

    def wait(self, duration: float):
        """Wait for specified duration"""
        self.actions.append(Wait(duration=duration))
        return self

    def turn(self, degrees: float, duration: float = 1.0):
        """Turn camera by specified degrees"""
        self.actions.append(Turn(degrees=degrees, duration=duration))
        return self

    def mouse_move(self, dx: float, dy: float = 0, duration: float = 0.1):
        """Move mouse by relative amount"""
        self.actions.append(MouseMove(dx=dx, dy=dy, duration=duration))
        return self

    def mouse_press(self, button: MouseButton):
        """Press a mouse button and hold it"""
        self.actions.append(MousePress(button=button))
        return self

    def mouse_release(self, button: MouseButton):
        """Release a previously pressed mouse button"""
        self.actions.append(MouseRelease(button=button))
        return self

    def mouse_click(self, button: MouseButton, duration: float = 0.1):
        """Click a mouse button (press and release)"""
        self.actions.append(MouseClick(button=button, duration=duration))
        return self


class Routine:
    """A collection of action sequences to be executed"""

    def __init__(
        self,
        controller: "DSController",
        routine_id: int = 0,
        name: Optional[str] = None,
        categories: Optional[List[str]] = None,
    ):
        self.controller = controller
        self.id = routine_id
        self.name = name
        self.categories = categories or []
        self.sequences: List[ActionSequence] = []
        self._cancelled = False
        self._task = None

    @contextmanager
    def parallel_actions(self):
        """Create a group of parallel actions using a context manager"""
        group = ActionGroup(parallel=True)
        yield group
        self.sequences.append(ActionSequence(actions=group.actions, parallel=True))

    @contextmanager
    def sequential_actions(self):
        """Create a group of sequential actions using a context manager"""
        group = ActionGroup(parallel=False)
        yield group
        self.sequences.append(ActionSequence(actions=group.actions, parallel=False))

    def add_actions(self, actions: List[InputAction], parallel: bool = False):
        """Add a list of predefined actions"""
        self.sequences.append(ActionSequence(actions=actions, parallel=parallel))
        return self

    def cancel(self):
        """Cancel this routine"""
        logger.info(f"Cancelling routine: {self.name or f'id={self.id}'}")
        self._cancelled = True
        if self._task:
            self._task.cancel()

    async def run(self):
        """Execute the entire routine"""
        routine_name = self.name or f"id={self.id}"
        logger.info(f"Starting routine: {routine_name}")
        if self.categories:
            logger.info(f"  Categories: {', '.join(self.categories)}")

        # Register with controller's registry system
        self.controller._register_routine(self)

        try:
            for i, sequence in enumerate(self.sequences):
                if self._cancelled:
                    logger.info(
                        f"Routine {routine_name} was cancelled, stopping execution"
                    )
                    break

                if sequence.parallel:
                    action_count = len(sequence.actions)
                    logger.info(
                        f"Executing parallel sequence with {action_count} actions"
                    )
                else:
                    logger.info(
                        f"Executing sequential sequence {i+1}/{len(self.sequences)}"
                    )

                await self.controller.execute_sequence(sequence)

            logger.info(f"Completed routine: {routine_name}")
        except Exception as e:
            logger.error(f"Error in routine {routine_name}: {e}")
            raise
        finally:
            # Unregister from controller when done
            self.controller._unregister_routine(self)


class DSController:
    def __init__(self, config: Optional[ControllerConfig] = None):
        """Initialize controller with optional custom configuration"""
        self.config = config or ControllerConfig()

        # State tracking
        self.pressed_keys: Set[str] = set()
        self.pressed_mouse_buttons: Set[MouseButton] = set()
        self.current_x = 0
        self.current_y = 0

        # Global registry for routine management
        self._routine_registry = {}  # category -> set of routines
        self._id_to_routine = {}  # id -> routine reference
        self._name_to_routines = {}  # name -> set of routines
        self._next_routine_id = 0

        # Initialize mouse position
        try:
            self._get_mouse_position()
            logger.info(f"Controller initialized with position: {self.current_pos}")
        except Exception as e:
            logger.warning(f"Could not get initial mouse position: {e}")
            logger.info("Controller initialized with default position: (0, 0)")

    @property
    def current_pos(self) -> Tuple[int, int]:
        """Current mouse position"""
        return (self.current_x, self.current_y)

    def _get_mouse_position(self) -> None:
        """Update current mouse position"""
        try:
            result = subprocess.run(
                ["xdotool", "getmouselocation"],
                capture_output=True,
                text=True,
                check=True,
            )
            parts = result.stdout.split()
            self.current_x = int(parts[0].split(":")[1])
            self.current_y = int(parts[1].split(":")[1])
        except CalledProcessError as e:
            raise XdotoolError(f"Failed to get mouse position: {e.stderr}")
        except (IndexError, ValueError) as e:
            raise MouseMovementError(f"Failed to parse mouse position: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning("xdotool not found, using default position")

    def _execute_xdotool(self, args: list[str]) -> None:
        """Execute an xdotool command safely"""
        cmd = ["xdotool"] + args
        logger.debug(f"Executing command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except CalledProcessError as e:
            logger.error(f"xdotool command failed: {' '.join(cmd)}")
            raise XdotoolError(f"xdotool command failed: {e.stderr}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating: {' '.join(cmd)}")

    def create_routine(self, name=None, categories=None) -> Routine:
        """Create a new action routine with optional name and categories"""
        routine_id = self._next_routine_id
        self._next_routine_id += 1

        routine = Routine(
            self, routine_id=routine_id, name=name, categories=categories or []
        )
        logger.info(f"Created routine: {name or f'id={routine_id}'}")
        return routine

    def _register_routine(self, routine: Routine) -> None:
        """Register routine in global registry"""
        self._id_to_routine[routine.id] = routine

        # Register by name if provided
        if routine.name:
            if routine.name not in self._name_to_routines:
                self._name_to_routines[routine.name] = set()
            self._name_to_routines[routine.name].add(routine)

        # Register in all specified categories
        for category in routine.categories:
            if category not in self._routine_registry:
                self._routine_registry[category] = set()
            self._routine_registry[category].add(routine)

        logger.debug(
            f"Registered routine {routine.name or f'id={routine.id}'} in registry"
        )

    def _unregister_routine(self, routine: Routine) -> None:
        """Remove routine from registry"""
        self._id_to_routine.pop(routine.id, None)

        # Remove from name registry
        if routine.name and routine.name in self._name_to_routines:
            self._name_to_routines[routine.name].discard(routine)
            if not self._name_to_routines[routine.name]:
                del self._name_to_routines[routine.name]

        # Remove from category registry
        for category in routine.categories:
            if category in self._routine_registry:
                self._routine_registry[category].discard(routine)
                if not self._routine_registry[category]:
                    del self._routine_registry[category]

        logger.debug(
            f"Unregistered routine {routine.name or f'id={routine.id}'} from registry"
        )

    def cancel_by_id(self, routine_id: int) -> bool:
        """Cancel a specific routine by ID"""
        if routine_id in self._id_to_routine:
            logger.info(f"Cancelling routine by ID: {routine_id}")
            self._id_to_routine[routine_id].cancel()
            return True
        logger.warning(f"Failed to cancel routine: no routine with ID {routine_id}")
        return False

    def cancel_by_name(self, name: str) -> bool:
        """Cancel all routines with the given name"""
        if name not in self._name_to_routines:
            logger.warning(f"Failed to cancel routines: no routines with name '{name}'")
            return False

        logger.info(f"Cancelling all routines with name: {name}")
        count = len(self._name_to_routines[name])
        for routine in list(self._name_to_routines[name]):
            routine.cancel()
        logger.info(f"Cancelled {count} routines")
        return True

    def cancel_category(self, category: str) -> bool:
        """Cancel all routines in a category"""
        if category not in self._routine_registry:
            logger.warning(
                f"Failed to cancel routines: no routines in category '{category}'"
            )
            return False

        logger.info(f"Cancelling all routines in category: {category}")
        count = len(self._routine_registry[category])
        for routine in list(self._routine_registry[category]):
            routine.cancel()
        logger.info(f"Cancelled {count} routines")
        return True

    def cancel_all_except(self, categories: Optional[List[str]] = None) -> None:
        """Cancel all routines except those in specified categories"""
        categories = categories or []
        logger.info(
            f"Cancelling all routines except categories: {', '.join(categories) or 'none'}"
        )

        exempt_routines = set()
        for category in categories:
            if category in self._routine_registry:
                exempt_routines.update(self._routine_registry[category])

        cancelled_count = 0
        for routine in list(self._id_to_routine.values()):
            if routine not in exempt_routines:
                routine.cancel()
                cancelled_count += 1

        logger.info(f"Cancelled {cancelled_count} routines")

    async def emergency_stop(self) -> None:
        """Immediately stop all routines and release all inputs"""
        logger.warning("EMERGENCY STOP triggered")

        # Cancel all routines
        routine_count = len(self._id_to_routine)
        for routine in list(self._id_to_routine.values()):
            routine.cancel()
        logger.info(f"Cancelled {routine_count} routines")

        # Release all pressed keys - continue even if some fail
        key_count = len(self.pressed_keys)
        if key_count > 0:
            logger.info(
                f"Releasing {key_count} pressed keys: {', '.join(self.pressed_keys)}"
            )

        for key in list(self.pressed_keys):
            try:
                await self._release_key_safely(key)
                logger.debug(f"Released key: {key}")
            except Exception as e:
                logger.error(f"Error releasing key {key} during emergency stop: {e}")
                # Continue to the next key despite the error
                self.pressed_keys.discard(
                    key
                )  # Make sure state is updated even if command fails

        # Release all pressed mouse buttons - continue even if some fail
        button_count = len(self.pressed_mouse_buttons)
        if button_count > 0:
            button_names = [button.value for button in self.pressed_mouse_buttons]
            logger.info(
                f"Releasing {button_count} pressed mouse buttons: {', '.join(button_names)}"
            )

        for button in list(self.pressed_mouse_buttons):
            try:
                await self._release_mouse_safely(button)
                logger.debug(f"Released mouse button: {button.value}")
            except Exception as e:
                logger.error(
                    f"Error releasing mouse button {button} during emergency stop: {e}"
                )
                # Continue to the next button despite the error
                self.pressed_mouse_buttons.discard(
                    button
                )  # Update state even if command fails

        logger.info("Emergency stop completed")

    async def _release_key_safely(self, key: str) -> None:
        """Release a key and update state, handling errors gracefully"""
        try:
            await self._execute_key_release(KeyRelease(key=key))
        except KeyboardError:
            # Still update our internal state even if the external command failed
            self.pressed_keys.discard(key)
            raise

    async def _release_mouse_safely(self, button: MouseButton) -> None:
        """Release a mouse button and update state, handling errors gracefully"""
        try:
            await self._execute_mouse_release(MouseRelease(button=button))
        except MouseMovementError:
            # Still update our internal state even if the external command failed
            self.pressed_mouse_buttons.discard(button)
            raise

    async def execute_sequence(self, sequence: ActionSequence) -> None:
        """Execute a sequence of actions"""
        if sequence.parallel:
            # For parallel actions, execute all at once
            logger.debug(f"Executing {len(sequence.actions)} actions in parallel")
            tasks = []
            for action in sequence.actions:
                task = asyncio.create_task(self._execute_action(action))
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            logger.debug("Parallel execution completed")
        else:
            # For sequential actions, execute one after another
            logger.debug(f"Executing {len(sequence.actions)} actions sequentially")
            for i, action in enumerate(sequence.actions):
                logger.debug(
                    f"Sequential action {i+1}/{len(sequence.actions)}: {action.type}"
                )
                await self._execute_action(action)
            logger.debug("Sequential execution completed")

    async def _execute_action(self, action: InputAction) -> None:
        """Execute a single action based on its type"""
        action_details = action.model_dump()
        log_action = f"{action.type}"
        if hasattr(action, "key") and action.key:
            log_action += f" key='{action.key}'"
        if hasattr(action, "button") and action.button:
            log_action += f" button='{action.button}'"
        if hasattr(action, "duration") and action.duration:
            log_action += f" duration={action.duration:.2f}s"
        if hasattr(action, "degrees") and action.degrees:
            log_action += f" degrees={action.degrees}°"
        if hasattr(action, "dx") and action.dx:
            log_action += f" dx={action.dx}"
        if hasattr(action, "dy") and action.dy:
            log_action += f" dy={action.dy}"

        logger.info(f"Executing action: {log_action}")

        try:
            if action.type == "press":
                await self._execute_key_press(action)
            elif action.type == "release":
                await self._execute_key_release(action)
            elif action.type == "tap":
                await self._execute_key_tap(action)
            elif action.type == "wait":
                await self._execute_wait(action)
            elif action.type == "turn":
                await self._execute_turn(action)
            elif action.type == "mouse_move":
                await self._execute_mouse_move(action)
            elif action.type == "mouse_press":
                await self._execute_mouse_press(action)
            elif action.type == "mouse_release":
                await self._execute_mouse_release(action)
            elif action.type == "mouse_click":
                await self._execute_mouse_click(action)
            else:
                logger.warning(f"Unknown action type: {action.type}")

            # If the action has a duration, wait for it (except for wait actions which already waited)
            if (
                hasattr(action, "duration")
                and action.duration
                and action.type != "wait"
            ):
                logger.debug(f"Waiting for action duration: {action.duration:.2f}s")
                await asyncio.sleep(action.duration)

            logger.debug(f"Action completed: {log_action}")
            # Log the current state
            if self.pressed_keys:
                logger.debug(f"Current pressed keys: {', '.join(self.pressed_keys)}")
            if self.pressed_mouse_buttons:
                button_names = [btn.value for btn in self.pressed_mouse_buttons]
                logger.debug(
                    f"Current pressed mouse buttons: {', '.join(button_names)}"
                )

        except Exception as e:
            logger.error(f"Failed to execute action {action.type}: {e}")
            raise

    async def _execute_key_press(self, action: KeyPress) -> None:
        """Press and hold a key"""
        key = action.key
        try:
            # Use model_dump instead of dict
            actual_key = self.config.keys.model_dump().get(key, key)
            logger.debug(f"Pressing key '{key}' (actual: '{actual_key}')")
            self._execute_xdotool(["keydown", actual_key])
            self.pressed_keys.add(key)
            logger.debug(f"Key '{key}' pressed successfully")
        except XdotoolError as e:
            logger.error(f"Failed to press key '{key}': {e}")
            raise KeyboardError(f"Failed to press key {key}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating press of key: {key}")
            self.pressed_keys.add(key)  # Still update internal state

    async def _execute_key_release(self, action: KeyRelease) -> None:
        """Release a held key"""
        key = action.key
        try:
            # Use model_dump instead of dict
            actual_key = self.config.keys.model_dump().get(key, key)
            logger.debug(f"Releasing key '{key}' (actual: '{actual_key}')")
            self._execute_xdotool(["keyup", actual_key])
            self.pressed_keys.discard(key)
            logger.debug(f"Key '{key}' released successfully")
        except XdotoolError as e:
            logger.error(f"Failed to release key '{key}': {e}")
            raise KeyboardError(f"Failed to release key {key}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating release of key: {key}")
            self.pressed_keys.discard(key)  # Still update internal state

    async def _execute_key_tap(self, action: KeyTap) -> None:
        """Tap a key (press and release)"""
        key = action.key
        duration = action.duration
        try:
            # Use model_dump instead of dict
            actual_key = self.config.keys.model_dump().get(key, key)
            logger.debug(
                f"Tapping key '{key}' (actual: '{actual_key}') for {duration:.2f}s"
            )
            self._execute_xdotool(["keydown", actual_key])
            self.pressed_keys.add(key)
            await asyncio.sleep(duration)
            self._execute_xdotool(["keyup", actual_key])
            self.pressed_keys.discard(key)
            logger.debug(f"Key '{key}' tapped successfully")
        except XdotoolError as e:
            logger.error(f"Failed to tap key '{key}': {e}")
            raise KeyboardError(f"Failed to tap key {key}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating tap of key: {key}")
            self.pressed_keys.add(key)
            await asyncio.sleep(duration)
            self.pressed_keys.discard(key)

    async def _execute_wait(self, action: Wait) -> None:
        """Wait for specified duration"""
        logger.debug(f"Waiting for {action.duration:.2f}s")
        await asyncio.sleep(action.duration)
        logger.debug(f"Wait completed")

    async def _execute_turn(self, action: Turn) -> None:
        """Turn camera by specified degrees"""
        degrees = action.degrees
        duration = action.duration
        logger.debug(f"Turning camera {degrees}° over {duration:.2f}s")

        total_pixels = degrees * self.config.mouse.pixels_per_degree
        steps = self.config.mouse.steps_per_second
        total_steps = int(duration * steps)

        logger.debug(f"Turn details: {total_pixels} pixels, {total_steps} steps")

        for i in range(total_steps):
            progress = i / total_steps
            # Use sine curve for smooth acceleration/deceleration
            smoothing = math.sin(progress * math.pi)
            pixels_this_step = (total_pixels / total_steps) * smoothing

            await self._execute_mouse_move(
                MouseMove(dx=pixels_this_step, dy=0, duration=0)
            )
            await asyncio.sleep(duration / total_steps)

            if (
                i % 10 == 0 or i == total_steps - 1
            ):  # Log every 10 steps or the final step
                logger.debug(
                    f"Turn progress: {i+1}/{total_steps} steps ({(i+1)/total_steps*100:.1f}%)"
                )

        logger.debug(f"Turn completed: {degrees}°")

    async def _execute_mouse_move(self, action: MouseMove) -> None:
        """Move mouse by relative amount"""
        try:
            dx, dy = int(action.dx), int(action.dy)
            logger.debug(f"Moving mouse by dx={dx}, dy={dy}")
            self._execute_xdotool(["mousemove_relative", "--", str(dx), str(dy)])

            # Update internal position
            self.current_x += dx
            self.current_y += dy
            logger.debug(f"New mouse position: ({self.current_x}, {self.current_y})")
        except XdotoolError as e:
            logger.error(f"Failed to move mouse: {e}")
            raise MouseMovementError(f"Failed to move mouse: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(
                f"xdotool not found, simulating mouse move: dx={action.dx}, dy={action.dy}"
            )
            self.current_x += int(action.dx)
            self.current_y += int(action.dy)

    async def _execute_mouse_press(self, action: MousePress) -> None:
        """Press and hold a mouse button"""
        button = action.button
        try:
            button_num = self.config.mouse_buttons[button]
            logger.debug(f"Pressing mouse button: {button.value} (button {button_num})")
            self._execute_xdotool(["mousedown", str(button_num)])
            self.pressed_mouse_buttons.add(button)
            logger.debug(f"Mouse button {button.value} pressed successfully")
        except XdotoolError as e:
            logger.error(f"Failed to press mouse button {button.value}: {e}")
            raise MouseMovementError(f"Failed to press mouse button {button}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating mouse press: {button.value}")
            self.pressed_mouse_buttons.add(button)

    async def _execute_mouse_release(self, action: MouseRelease) -> None:
        """Release a held mouse button"""
        button = action.button
        try:
            button_num = self.config.mouse_buttons[button]
            logger.debug(
                f"Releasing mouse button: {button.value} (button {button_num})"
            )
            self._execute_xdotool(["mouseup", str(button_num)])
            self.pressed_mouse_buttons.discard(button)
            logger.debug(f"Mouse button {button.value} released successfully")
        except XdotoolError as e:
            logger.error(f"Failed to release mouse button {button.value}: {e}")
            raise MouseMovementError(f"Failed to release mouse button {button}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(
                f"xdotool not found, simulating mouse release: {button.value}"
            )
            self.pressed_mouse_buttons.discard(button)

    async def _execute_mouse_click(self, action: MouseClick) -> None:
        """Click a mouse button (press and release)"""
        button = action.button
        duration = action.duration
        try:
            button_num = self.config.mouse_buttons[button]
            logger.debug(
                f"Clicking mouse button: {button.value} (button {button_num}) for {duration:.2f}s"
            )
            self._execute_xdotool(["mousedown", str(button_num)])
            self.pressed_mouse_buttons.add(button)
            await asyncio.sleep(duration)
            self._execute_xdotool(["mouseup", str(button_num)])
            self.pressed_mouse_buttons.discard(button)
            logger.debug(f"Mouse button {button.value} clicked successfully")
        except XdotoolError as e:
            logger.error(f"Failed to click mouse button {button.value}: {e}")
            raise MouseMovementError(f"Failed to click mouse button {button}: {e}")
        except FileNotFoundError:
            # For testing environments where xdotool isn't available
            logger.warning(f"xdotool not found, simulating mouse click: {button.value}")
            self.pressed_mouse_buttons.add(button)
            await asyncio.sleep(duration)
            self.pressed_mouse_buttons.discard(button)

    # Support for legacy routine execution (for backward compatibility)
    async def execute_routine(self, legacy_routine):
        """Execute a legacy routine"""
        logger.info(f"Converting legacy routine: {legacy_routine.name}")

        # Create a new routine with the same name
        routine = self.create_routine(name=legacy_routine.name, categories=[])

        # Convert legacy actions to new action sequences
        for action in legacy_routine.actions:
            await self._convert_legacy_action(routine, action)

        # Run the routine
        await routine.run()

    async def _convert_legacy_action(self, routine, legacy_action):
        """Convert a legacy action to new action sequences"""
        # This is a simplified conversion - would need to be expanded for a full implementation
        if not legacy_action.params:
            legacy_action.params = {}

        action_type = str(legacy_action.type)
        logger.debug(
            f"Converting legacy action: {action_type}, duration={legacy_action.duration}"
        )

        with routine.sequential_actions() as actions:
            if legacy_action.type == "move":
                direction = legacy_action.params.get("direction", "forward")
                logger.debug(
                    f"Legacy move action: direction={direction}, duration={legacy_action.duration}"
                )
                actions.press(direction)
                actions.wait(legacy_action.duration)
                actions.release(direction)
            elif legacy_action.type == "turn":
                degrees = legacy_action.params.get("degrees", 90)
                logger.debug(
                    f"Legacy turn action: degrees={degrees}, duration={legacy_action.duration}"
                )
                actions.turn(degrees, legacy_action.duration)
            elif legacy_action.type == "wait":
                logger.debug(f"Legacy wait action: duration={legacy_action.duration}")
                actions.wait(legacy_action.duration)
            # Add other action type conversions as needed
