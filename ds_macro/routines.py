# routines.py
from typing import Dict, List, Optional, Callable
import asyncio
import logging
from ds_macro.models import (
    MouseButton,
    MovementDirection,
    Routine as LegacyRoutine,
    ActionType,
    Action as LegacyAction,
)
from ds_macro.patterns import CommonActions
from ds_macro.controller import DSController

logger = logging.getLogger(__name__)


async def create_360_scan(controller: DSController) -> None:
    """Creates a routine that performs a full 360° scan"""
    routine = controller.create_routine(name="360_degree_scan", categories=["scanning"])

    # Add scan environment actions
    routine.add_actions(CommonActions.scan_environment())

    await routine.run()


async def create_patrol_route(controller: DSController) -> None:
    """Creates a patrol route that walks in a square pattern"""
    routine = controller.create_routine(
        name="patrol_square", categories=["movement", "patrol"]
    )

    # Start with a scan
    routine.add_actions(CommonActions.scan_environment())

    # Execute a square patrol pattern
    for i in range(4):
        # Walk forward
        with routine.sequential_actions() as actions:
            actions.press(MovementDirection.FORWARD)
            actions.wait(3.0)
            actions.release(MovementDirection.FORWARD)

        # Turn right
        with routine.sequential_actions() as actions:
            actions.turn(90, duration=1.0)

        # Scan after each corner
        routine.add_actions(CommonActions.scan_environment())

    await routine.run()


async def create_cargo_delivery(controller: DSController) -> None:
    """Creates a routine for delivering cargo"""
    routine = controller.create_routine(
        name="deliver_cargo", categories=["interaction"]
    )

    # Approach drop-off point
    with routine.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.wait(2.0)
        actions.release(MovementDirection.FORWARD)

    # Hold action button to initiate delivery
    with routine.sequential_actions() as actions:
        actions.press("action")
        actions.wait(1.0)
        actions.release("action")

    # Wait for animation
    with routine.sequential_actions() as actions:
        actions.wait(2.0)

    # Step back
    routine.add_actions(CommonActions.backstep(1.0))

    await routine.run()


async def create_combat_sequence(controller: DSController) -> None:
    """Creates a combat sequence with aiming and shooting"""
    routine = controller.create_routine(name="combat_sequence", categories=["combat"])

    # Take cover and aim
    with routine.sequential_actions() as actions:
        actions.press("crouch")
        actions.wait(0.5)

    # Aim and fire
    routine.add_actions(CommonActions.aim_and_fire(shots=3, delay=0.3))

    # Move to new position
    with routine.sequential_actions() as actions:
        actions.release("crouch")
        actions.press(MovementDirection.RIGHT)
        actions.press("sprint")
        actions.wait(1.0)
        actions.release("sprint")
        actions.release(MovementDirection.RIGHT)
        actions.press("crouch")

    # Aim and fire again
    routine.add_actions(CommonActions.aim_and_fire(shots=2, delay=0.3))

    # Release crouch
    with routine.sequential_actions() as actions:
        actions.release("crouch")

    await routine.run()


# Legacy routines for backward compatibility
def create_360_scan_legacy() -> LegacyRoutine:
    """Creates a routine that performs a full 360° scan"""
    return LegacyRoutine(
        name="360_degree_scan",
        description="Perform a full 360° environmental scan while standing still",
        actions=[
            LegacyAction(type=ActionType.SCAN, duration=4.0, params={"degrees": 360})
        ],
    )


def create_patrol_route_legacy() -> LegacyRoutine:
    """Creates a patrol route that walks in a square pattern"""
    return LegacyRoutine(
        name="patrol_square",
        description="Walk in a square pattern, scanning at each corner",
        actions=[
            # Walk forward and turn right
            LegacyAction(
                type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}
            ),
            # Quick scan
            LegacyAction(type=ActionType.SCAN, duration=2.0, params={"degrees": 180}),
            # Walk forward and turn right
            LegacyAction(
                type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}
            ),
            # Repeat two more times to complete square
            LegacyAction(
                type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}
            ),
            LegacyAction(
                type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}
            ),
        ],
    )


def create_cargo_delivery_legacy() -> LegacyRoutine:
    """Creates a routine for delivering cargo"""
    return LegacyRoutine(
        name="deliver_cargo",
        description="Standard cargo delivery sequence",
        actions=[
            # Approach drop-off point
            LegacyAction(
                type=ActionType.MOVE,
                duration=2.0,
                params={"direction": MovementDirection.FORWARD},
            ),
            # Hold action button to initiate delivery
            LegacyAction(
                type=ActionType.HOLD_KEY, duration=1.0, params={"key": "action"}
            ),
            # Wait for animation
            LegacyAction(type=ActionType.WAIT, duration=2.0),
            # Step back
            LegacyAction(
                type=ActionType.MOVE,
                duration=1.0,
                params={"direction": MovementDirection.BACKWARD},
            ),
        ],
    )


# Add these new functions to ds_macro/routines.py


async def create_balance_left(controller: DSController) -> None:
    """Creates a routine that holds left mouse button to center balance left"""
    routine = controller.create_routine(
        name="balance_left", categories=["movement", "balance"]
    )

    # Hold left mouse button
    with routine.sequential_actions() as actions:
        actions.mouse_press(MouseButton.LEFT)
        actions.wait(2.0)  # Hold for 2 seconds by default
        actions.mouse_release(MouseButton.LEFT)

    await routine.run()


async def create_balance_right(controller: DSController) -> None:
    """Creates a routine that holds right mouse button to center balance right"""
    routine = controller.create_routine(
        name="balance_right", categories=["movement", "balance"]
    )

    # Hold right mouse button
    with routine.sequential_actions() as actions:
        actions.mouse_press(MouseButton.RIGHT)
        actions.wait(2.0)  # Hold for 2 seconds by default
        actions.mouse_release(MouseButton.RIGHT)

    await routine.run()


async def create_balance_both(controller: DSController) -> None:
    """Creates a routine that holds both mouse buttons to fully center balance"""
    routine = controller.create_routine(
        name="balance_both", categories=["movement", "balance"]
    )

    # Hold both mouse buttons simultaneously
    with routine.parallel_actions() as actions:
        actions.mouse_press(MouseButton.LEFT)
        actions.mouse_press(MouseButton.RIGHT)

    # Wait while holding
    with routine.sequential_actions() as actions:
        actions.wait(2.0)  # Hold for 2 seconds by default

    # Release both buttons
    with routine.sequential_actions() as actions:
        actions.mouse_release(MouseButton.LEFT)
        actions.mouse_release(MouseButton.RIGHT)

    await routine.run()


async def create_balance_left_moving(controller: DSController) -> None:
    """Creates a routine that holds left mouse button while moving forward"""
    routine = controller.create_routine(
        name="balance_left_moving", categories=["movement", "balance"]
    )

    # Start moving forward and balance left simultaneously
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.mouse_press(MouseButton.LEFT)

    # Keep moving and balancing
    with routine.sequential_actions() as actions:
        actions.wait(5.0)  # Move and balance for 5 seconds

    # Stop moving and balancing
    with routine.sequential_actions() as actions:
        actions.release(MovementDirection.FORWARD)
        actions.mouse_release(MouseButton.LEFT)

    await routine.run()


async def create_balance_right_moving(controller: DSController) -> None:
    """Creates a routine that holds right mouse button while moving forward"""
    routine = controller.create_routine(
        name="balance_right_moving", categories=["movement", "balance"]
    )

    # Start moving forward and balance right simultaneously
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.mouse_press(MouseButton.RIGHT)

    # Keep moving and balancing
    with routine.sequential_actions() as actions:
        actions.wait(5.0)  # Move and balance for 5 seconds

    # Stop moving and balancing
    with routine.sequential_actions() as actions:
        actions.release(MovementDirection.FORWARD)
        actions.mouse_release(MouseButton.RIGHT)

    await routine.run()


async def create_balance_both_moving(controller: DSController) -> None:
    """Creates a routine that holds both mouse buttons while moving forward"""
    routine = controller.create_routine(
        name="balance_both_moving", categories=["movement", "balance"]
    )

    # Start moving forward and balance both sides simultaneously
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.mouse_press(MouseButton.LEFT)
        actions.mouse_press(MouseButton.RIGHT)

    # Keep moving and balancing
    with routine.sequential_actions() as actions:
        actions.wait(5.0)  # Move and balance for 5 seconds

    # Stop moving and balancing
    with routine.sequential_actions() as actions:
        actions.release(MovementDirection.FORWARD)
        actions.mouse_release(MouseButton.LEFT)
        actions.mouse_release(MouseButton.RIGHT)

    await routine.run()


# Collection of available legacy routines
LEGACY_ROUTINES = {
    "360_scan": create_360_scan_legacy(),
    "patrol": create_patrol_route_legacy(),
    "deliver": create_cargo_delivery_legacy(),
}


# Collection of available new routines
AVAILABLE_ROUTINES = {
    "360_scan": create_360_scan,
    "patrol": create_patrol_route,
    "deliver": create_cargo_delivery,
    "combat": create_combat_sequence,
    "balance_left": create_balance_left,
    "balance_right": create_balance_right,
    "balance_both": create_balance_both,
    "balance_left_moving": create_balance_left_moving,
    "balance_right_moving": create_balance_right_moving,
    "balance_both_moving": create_balance_both_moving,
}


async def run_routine(controller: DSController, routine_name: str) -> None:
    """Run a routine by name"""
    if routine_name in AVAILABLE_ROUTINES:
        await AVAILABLE_ROUTINES[routine_name](controller)
    elif routine_name in LEGACY_ROUTINES:
        logger.info(f"Using legacy routine: {routine_name}")
        await controller.execute_routine(LEGACY_ROUTINES[routine_name])
    else:
        logger.error(f"Unknown routine: {routine_name}")
        raise ValueError(f"Unknown routine: {routine_name}")
