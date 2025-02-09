# controller.py
import subprocess
import time
import math
import logging
from typing import Optional, Tuple, Union
from subprocess import CalledProcessError

from models import (
    ControllerConfig,
    MouseButton,
    MovementDirection,
    Action,
    ActionType,
    Routine,
)
from exceptions import (
    MouseMovementError,
    KeyboardError,
    XdotoolError,
    DSControllerError,
)

logger = logging.getLogger(__name__)


class DSController:
    def __init__(self, config: Optional[ControllerConfig] = None):
        """Initialize controller with optional custom configuration"""
        self.config = config or ControllerConfig()
        self._get_mouse_position()
        logger.info(f"Controller initialized with position: {self.current_pos}")

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

    def _execute_xdotool(self, args: list[str]) -> None:
        """Execute an xdotool command safely"""
        try:
            subprocess.run(["xdotool"] + args, check=True)
        except CalledProcessError as e:
            raise XdotoolError(f"xdotool command failed: {e.stderr}")

    def move_mouse_relative(self, dx: float, dy: float = 0) -> None:
        """Move mouse by relative amount"""
        try:
            self._execute_xdotool(
                ["mousemove_relative", "--", str(int(dx)), str(int(dy))]
            )
        except XdotoolError as e:
            raise MouseMovementError(f"Failed to move mouse: {e}")

    def press_key(self, key: Union[str, MovementDirection]) -> None:
        """Press and hold a key"""
        try:
            actual_key = self.config.keys.dict().get(key, key)
            self._execute_xdotool(["keydown", actual_key])
        except XdotoolError as e:
            raise KeyboardError(f"Failed to press key {key}: {e}")

    def release_key(self, key: Union[str, MovementDirection]) -> None:
        """Release a held key"""
        try:
            actual_key = self.config.keys.dict().get(key, key)
            self._execute_xdotool(["keyup", actual_key])
        except XdotoolError as e:
            raise KeyboardError(f"Failed to release key {key}: {e}")

    def hold_key(self, key: Union[str, MovementDirection], duration: float) -> None:
        """Hold a key for specified duration"""
        logger.debug(f"Holding key {key} for {duration}s")
        self.press_key(key)
        time.sleep(duration)
        self.release_key(key)

    def press_mouse(self, button: MouseButton) -> None:
        """Press and hold a mouse button"""
        try:
            button_num = self.config.mouse_buttons[button]
            self._execute_xdotool(["mousedown", str(button_num)])
        except XdotoolError as e:
            raise MouseMovementError(f"Failed to press mouse button {button}: {e}")

    def release_mouse(self, button: MouseButton) -> None:
        """Release a held mouse button"""
        try:
            button_num = self.config.mouse_buttons[button]
            self._execute_xdotool(["mouseup", str(button_num)])
        except XdotoolError as e:
            raise MouseMovementError(f"Failed to release mouse button {button}: {e}")

    def hold_mouse(self, button: MouseButton, duration: float) -> None:
        """Hold a mouse button for specified duration"""
        logger.debug(f"Holding mouse button {button} for {duration}s")
        self.press_mouse(button)
        time.sleep(duration)
        self.release_mouse(button)

    # Movement Methods
    def turn_camera(self, degrees: float, duration: float) -> None:
        """Smooth camera turn with acceleration/deceleration"""
        logger.info(f"Turning camera {degrees}° over {duration}s")

        total_pixels = degrees * self.config.mouse.pixels_per_degree
        steps = self.config.mouse.steps_per_second
        total_steps = int(duration * steps)

        for i in range(total_steps):
            progress = i / total_steps
            smoothing = math.sin(progress * math.pi)
            pixels_this_step = (total_pixels / total_steps) * smoothing
            self.move_mouse_relative(pixels_this_step)
            time.sleep(duration / total_steps)

    def move(self, direction: MovementDirection, duration: float) -> None:
        """Move in a single direction"""
        logger.debug(f"Moving {direction} for {duration}s")
        self.hold_key(direction, duration)

    def move_combined(
        self, primary: MovementDirection, secondary: MovementDirection, duration: float
    ) -> None:
        """Move in two directions simultaneously"""
        logger.debug(f"Moving {primary}+{secondary} for {duration}s")
        self.press_key(primary)
        self.press_key(secondary)
        time.sleep(duration)
        self.release_key(secondary)
        self.release_key(primary)

    # Complex Actions
    def walk_and_turn(self, degrees: float, duration: float) -> None:
        """Walk forward while turning camera smoothly"""
        logger.info(f"Walking and turning {degrees}° over {duration}s")
        self.press_key(MovementDirection.FORWARD)
        self.turn_camera(degrees, duration)
        self.release_key(MovementDirection.FORWARD)

    def sprint_and_turn(self, degrees: float, duration: float) -> None:
        """Sprint while turning camera smoothly"""
        logger.info(f"Sprinting and turning {degrees}° over {duration}s")
        self.press_key(MovementDirection.FORWARD)
        self.press_key("sprint")
        self.turn_camera(degrees, duration)
        self.release_key("sprint")
        self.release_key(MovementDirection.FORWARD)

    def execute_action(self, action: Action) -> None:
        """Execute a single action"""
        logger.debug(f"Executing action: {action.type}")

        if not action.params:
            action.params = {}

        try:
            if action.type == ActionType.MOVE:
                self.move(action.params["direction"], action.duration)

            elif action.type == ActionType.TURN:
                self.turn_camera(action.params["degrees"], action.duration)

            elif action.type == ActionType.MOVE_AND_TURN:
                self.walk_and_turn(action.params["degrees"], action.duration)

            elif action.type == ActionType.SPRINT:
                self.press_key("sprint")
                self.move(action.params["direction"], action.duration)
                self.release_key("sprint")

            elif action.type == ActionType.SPRINT_AND_TURN:
                self.sprint_and_turn(action.params["degrees"], action.duration)

            elif action.type == ActionType.HOLD_KEY:
                self.hold_key(action.params["key"], action.duration)

            elif action.type == ActionType.HOLD_MOUSE:
                self.hold_mouse(action.params["button"], action.duration)

            elif action.type == ActionType.WAIT:
                time.sleep(action.duration)

            elif action.type == ActionType.SCAN:
                self.press_key("scan")
                self.turn_camera(action.params["degrees"], action.duration)
                self.release_key("scan")

            else:
                raise DSControllerError(f"Unknown action type: {action.type}")

        except Exception as e:
            logger.error(f"Failed to execute action {action.type}: {e}")
            raise

    def execute_routine(self, routine: Routine) -> None:
        """Execute a complete routine"""
        logger.info(f"Starting routine: {routine.name}")
        logger.info(f"Description: {routine.description}")

        try:
            for i, action in enumerate(routine.actions, 1):
                logger.info(f"Executing action {i}/{len(routine.actions)}")
                self.execute_action(action)
                logger.debug(f"Completed action {i}")

            logger.info(f"Routine '{routine.name}' completed successfully")

        except Exception as e:
            logger.error(f"Routine '{routine.name}' failed: {e}")
            raise
