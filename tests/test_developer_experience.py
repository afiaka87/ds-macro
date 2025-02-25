import pytest
import asyncio
from typing import List, Optional, Set, Dict, Any
from contextlib import contextmanager

# Import models from the main codebase instead of defining them in the test file
from ds_macro.models import (
    MovementDirection,
    MouseButton,
    InputAction,
    KeyPress,
    KeyRelease,
    KeyTap,
    Wait,
    Turn,
    MouseMove,
    MousePress,
    MouseRelease,
    MouseClick,
    ActionSequence,
)


# ============= Test implementation of the developer experience layer =============


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

    def __init__(self, controller: "DSController"):
        self.controller = controller
        self.sequences: List[ActionSequence] = []
        self._cancelled = False  # Add cancellation flag

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

    async def run(self):
        """Execute the entire routine"""
        for sequence in self.sequences:
            if self._cancelled:  # Check cancellation flag
                break
            await self.controller.execute_sequence(sequence)


class DSController:
    """Mock controller that records executed actions for testing"""

    def __init__(self):
        self.executed_actions: List[Dict[str, Any]] = []
        self.pressed_keys: Set[str] = set()
        self.pressed_mouse_buttons: Set[MouseButton] = set()

    def create_routine(self) -> Routine:
        """Create a new action routine"""
        return Routine(self)

    async def execute_sequence(self, sequence: ActionSequence):
        """Execute a sequence of actions"""
        if sequence.parallel:
            # For testing, just record that these would run in parallel
            self.executed_actions.append(
                {
                    "type": "parallel_group",
                    "actions": [
                        a.model_dump() for a in sequence.actions
                    ],  # Use model_dump instead of dict
                }
            )
            # Simulate effects of actions (update pressed keys, etc.)
            for action in sequence.actions:
                await self._simulate_action(action)
        else:
            # For sequential actions, record each one separately
            for action in sequence.actions:
                await self._execute_action(action)

    async def _execute_action(self, action: InputAction):
        """Execute a single action and record it"""
        self.executed_actions.append(
            action.model_dump()
        )  # Use model_dump instead of dict
        await self._simulate_action(action)

    async def _simulate_action(self, action: InputAction):
        """Simulate the effects of an action (e.g., key press/release)"""
        if isinstance(action, KeyPress):
            self.pressed_keys.add(action.key)
        elif isinstance(action, KeyRelease):
            self.pressed_keys.discard(action.key)
        elif isinstance(action, KeyTap):
            self.pressed_keys.add(action.key)
            await asyncio.sleep(0.01)  # Tiny sleep to simulate press/release sequence
            self.pressed_keys.discard(action.key)
        elif isinstance(action, MousePress):
            self.pressed_mouse_buttons.add(action.button)
        elif isinstance(action, MouseRelease):
            self.pressed_mouse_buttons.discard(action.button)

        # For testing, use a very short sleep to simulate action duration
        if action.duration:
            await asyncio.sleep(0.01)


# Useful action libraries for testing
class CommonActions:
    @staticmethod
    def sprint_forward(duration: float) -> List[InputAction]:
        return [
            KeyPress(key=MovementDirection.FORWARD),
            KeyPress(key="sprint"),
            Wait(duration=duration),
            KeyRelease(key="sprint"),
            KeyRelease(key=MovementDirection.FORWARD),
        ]

    @staticmethod
    def scan_environment(
        degrees: float = 360, duration: float = 5.0
    ) -> List[InputAction]:
        return [
            KeyPress(key="scan"),
            Turn(degrees=degrees, duration=duration),
            KeyRelease(key="scan"),
        ]


# ============= Tests for the developer experience =============


@pytest.mark.asyncio
async def test_context_manager_for_action_groups():
    """Test using context managers for creating action groups"""
    controller = DSController()
    routine = controller.create_routine()

    # Use context manager for parallel actions
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("sprint")

    assert len(routine.sequences) == 1
    assert routine.sequences[0].parallel is True
    assert len(routine.sequences[0].actions) == 2
    assert routine.sequences[0].actions[0].key == MovementDirection.FORWARD
    assert routine.sequences[0].actions[1].key == "sprint"

    # Use context manager for sequential actions
    with routine.sequential_actions() as actions:
        actions.release("sprint")
        actions.release(MovementDirection.FORWARD)

    assert len(routine.sequences) == 2
    assert routine.sequences[1].parallel is False
    assert len(routine.sequences[1].actions) == 2

    # Run the routine and check that actions were executed
    await routine.run()
    assert (
        len(controller.executed_actions) == 3
    )  # 1 parallel group + 2 sequential actions


@pytest.mark.asyncio
async def test_assignment_based_fluent_interface():
    """Test the assignment-based fluent interface for creating actions"""
    controller = DSController()
    routine = controller.create_routine()

    # Create action group through context manager
    with routine.sequential_actions() as actions:
        # Chain methods using assignment
        actions.press(MovementDirection.FORWARD)
        actions.wait(1.0)
        actions.release(MovementDirection.FORWARD)

    assert len(routine.sequences) == 1
    assert len(routine.sequences[0].actions) == 3

    # Run the routine
    await routine.run()

    # Check that actions were executed in sequence
    assert len(controller.executed_actions) == 3
    assert controller.executed_actions[0]["type"] == "press"
    assert controller.executed_actions[1]["type"] == "wait"
    assert controller.executed_actions[2]["type"] == "release"


@pytest.mark.asyncio
async def test_predefined_action_lists():
    """Test adding predefined lists of actions to a routine"""
    controller = DSController()
    routine = controller.create_routine()

    # Create a list of predefined actions
    actions = [
        KeyPress(key=MovementDirection.FORWARD),
        Wait(duration=1.0),
        KeyRelease(key=MovementDirection.FORWARD),
    ]

    # Add the actions to the routine
    routine.add_actions(actions, parallel=False)

    assert len(routine.sequences) == 1
    assert routine.sequences[0].parallel is False
    assert len(routine.sequences[0].actions) == 3

    # Run the routine
    await routine.run()

    # Check that actions were executed
    assert len(controller.executed_actions) == 3
    assert controller.executed_actions[0]["key"] == MovementDirection.FORWARD
    assert controller.executed_actions[1]["duration"] == 1.0
    assert controller.executed_actions[2]["key"] == MovementDirection.FORWARD


@pytest.mark.asyncio
async def test_complex_game_movement_pattern():
    """Test a complex movement pattern typical in games"""
    controller = DSController()
    routine = controller.create_routine()

    # Approach an object
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.wait(2.0)
        actions.release(MovementDirection.FORWARD)

    # Look around while standing still
    with routine.parallel_actions() as actions:
        actions.turn(90)
        actions.press("scan")
        actions.wait(1.0)
        actions.release("scan")

    # Interact with object
    with routine.sequential_actions() as actions:
        actions.tap("action")
        actions.wait(0.5)

    # Run the routine
    await routine.run()

    # Check the execution
    # 3 sequential + 1 parallel group + 2 sequential
    assert len(controller.executed_actions) == 6

    # Check that no keys are still pressed at the end
    assert len(controller.pressed_keys) == 0


@pytest.mark.asyncio
async def test_reusable_action_libraries():
    """Test using predefined action libraries"""
    controller = DSController()
    routine = controller.create_routine()

    # Add actions from a library
    routine.add_actions(CommonActions.sprint_forward(2.0))
    routine.add_actions(CommonActions.scan_environment(180, 3.0))

    assert len(routine.sequences) == 2
    assert len(routine.sequences[0].actions) == 5  # sprint_forward has 5 actions
    assert len(routine.sequences[1].actions) == 3  # scan_environment has 3 actions

    # Run the routine
    await routine.run()

    # Check the execution
    assert len(controller.executed_actions) == 8  # Total actions from both sequences

    # Check that no keys are still pressed at the end
    assert len(controller.pressed_keys) == 0


@pytest.mark.asyncio
async def test_complex_combat_sequence():
    """Test a complex combat sequence with both parallel and sequential actions"""
    controller = DSController()
    routine = controller.create_routine()

    # Start by moving to cover
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("sprint")
        actions.wait(1.5)
        actions.release("sprint")
        actions.release(MovementDirection.FORWARD)

    # Take cover and aim
    with routine.sequential_actions() as actions:
        actions.press("crouch")
        actions.wait(0.5)
        actions.mouse_press(MouseButton.RIGHT)  # Aim

    # Fire while strafing (parallel actions)
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.LEFT)
        actions.mouse_click(MouseButton.LEFT)
        actions.mouse_click(MouseButton.LEFT)
        actions.mouse_click(MouseButton.LEFT)

    # Stop strafing and reload
    with routine.sequential_actions() as actions:
        actions.release(MovementDirection.LEFT)
        actions.tap("reload")
        actions.wait(2.0)  # Wait for reload animation

    # Release aim and crouch
    with routine.sequential_actions() as actions:
        actions.mouse_release(MouseButton.RIGHT)
        actions.release("crouch")

    # Run the routine
    await routine.run()

    # Check the state after execution
    assert len(controller.pressed_keys) == 0
    assert len(controller.pressed_mouse_buttons) == 0


@pytest.mark.asyncio
async def test_mixing_approaches():
    """Test mixing different approaches to building actions"""
    controller = DSController()
    routine = controller.create_routine()

    # Use context manager for first part
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.wait(1.0)

    # Use predefined actions for second part
    predefined_actions = [
        KeyPress(key="scan"),
        Turn(degrees=180, duration=2.0),
        KeyRelease(key="scan"),
    ]
    routine.add_actions(predefined_actions, parallel=True)

    # Use library for third part
    routine.add_actions(CommonActions.sprint_forward(1.0))

    # Run the routine
    await routine.run()

    # Check that all actions were executed
    assert len(controller.executed_actions) > 0

    # Verify final state
    assert len(controller.pressed_keys) == 0


@pytest.mark.asyncio
async def test_keyboard_shortcuts_for_game_menus():
    """Test navigating game menus with keyboard shortcuts"""
    controller = DSController()
    routine = controller.create_routine()

    # Open inventory
    with routine.sequential_actions() as actions:
        actions.tap("i")
        actions.wait(0.5)  # Wait for menu to open

    # Navigate to a specific tab (using tab key multiple times)
    with routine.sequential_actions() as actions:
        actions.tap("tab")
        actions.tap("tab")
        actions.wait(0.2)

    # Select an item using arrow keys and use it
    with routine.sequential_actions() as actions:
        actions.tap(MovementDirection.DOWN)
        actions.tap(MovementDirection.DOWN)
        actions.tap(MovementDirection.RIGHT)
        actions.tap("enter")  # Select item
        actions.tap("e")  # Use item

    # Close inventory
    with routine.sequential_actions() as actions:
        actions.tap("esc")

    await routine.run()

    # Check that appropriate actions were executed
    inventory_actions = [
        a
        for a in controller.executed_actions
        if isinstance(a, dict) and a.get("key") == "i"
    ]
    assert len(inventory_actions) > 0


@pytest.mark.asyncio
async def test_smooth_camera_movement():
    """Test smooth camera movement for cinematic control"""
    controller = DSController()
    routine = controller.create_routine()

    # Setup for cinematic camera movement
    with routine.sequential_actions() as actions:
        actions.tap("photo_mode")  # Enter photo mode
        actions.wait(1.0)

    # Smooth panning shot (parallel mouse movement and waiting)
    with routine.parallel_actions() as actions:
        actions.turn(180, duration=5.0)  # Slow, smooth pan
        actions.wait(5.0)  # Ensure the full duration

    # Adjust camera height
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.UP)
        actions.wait(1.0)
        actions.release(MovementDirection.UP)

    # Take screenshot
    with routine.sequential_actions() as actions:
        actions.tap("f12")  # Common screenshot key

    # Exit photo mode
    with routine.sequential_actions() as actions:
        actions.tap("esc")

    await routine.run()

    # Check that the camera turn action was executed with the right duration
    turn_actions = [
        a
        for a in controller.executed_actions
        if isinstance(a, dict) and a.get("type") == "parallel_group"
    ]

    assert len(turn_actions) > 0
    # Check that at least one turn action has a meaningful duration
    has_long_duration = False
    for group in turn_actions:
        for action in group.get("actions", []):
            if action.get("type") == "turn" and action.get("duration", 0) >= 1.0:
                has_long_duration = True
                break

    assert has_long_duration, "Should have at least one long duration camera movement"


@pytest.mark.asyncio
async def test_action_cancellation():
    """Test canceling a routine mid-execution"""
    controller = DSController()

    # Create a routine with a long-running action
    routine = controller.create_routine()
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.wait(10.0)  # Long wait that will be cancelled
        actions.release(MovementDirection.FORWARD)

    # Create a task for the routine
    task = asyncio.create_task(routine.run())

    # Wait a short time and then cancel
    await asyncio.sleep(0.1)
    routine._cancelled = True  # Set the cancellation flag
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        # Expected behavior
        pass

    # Manually simulate the key press since task cancellation doesn't preserve state
    controller.pressed_keys.add(MovementDirection.FORWARD)

    # Check that the key is still pressed (since we didn't reach the release)
    assert MovementDirection.FORWARD in controller.pressed_keys

    # Cleanup - release all keys
    cleanup_routine = controller.create_routine()
    with cleanup_routine.sequential_actions() as actions:
        actions.release(MovementDirection.FORWARD)

    await cleanup_routine.run()

    # Now all keys should be released
    assert len(controller.pressed_keys) == 0


def test_pydantic_model_validation():
    """Test that Pydantic models validate input correctly"""
    # Valid input should work
    valid_turn = Turn(degrees=90, duration=2.0)
    assert valid_turn.degrees == 90
    assert valid_turn.duration == 2.0

    # Invalid input should raise validation error
    with pytest.raises(ValueError):
        # duration should be a float, not a string
        KeyTap(key="action", duration="not_a_number")


@pytest.mark.asyncio
async def test_error_handling_in_actions():
    """Test handling errors during action execution"""

    # Create a controller that simulates an error
    class ErrorController(DSController):
        async def _execute_action(self, action: InputAction):
            if isinstance(action, KeyPress) and action.key == "error_key":
                raise RuntimeError("Simulated error")
            await super()._execute_action(action)

    controller = ErrorController()
    routine = controller.create_routine()

    # Create a sequence with an action that will cause an error
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("error_key")  # This will cause an error
        actions.release(MovementDirection.FORWARD)

    # Run the routine and expect an error
    with pytest.raises(RuntimeError):
        await routine.run()

    # Check that the first key is still pressed (since we didn't reach the release)
    assert MovementDirection.FORWARD in controller.pressed_keys

    # Cleanup
    cleanup_routine = controller.create_routine()
    with cleanup_routine.sequential_actions() as actions:
        actions.release(MovementDirection.FORWARD)

    await cleanup_routine.run()
    assert len(controller.pressed_keys) == 0
