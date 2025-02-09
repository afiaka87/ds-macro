# routines.py
from typing import List
from models import Action, ActionType, Routine, MovementDirection


def create_360_scan() -> Routine:
    """Creates a routine that performs a full 360° scan"""
    return Routine(
        name="360_degree_scan",
        description="Perform a full 360° environmental scan while standing still",
        actions=[Action(type=ActionType.SCAN, duration=4.0, params={"degrees": 360})],
    )


def create_patrol_route() -> Routine:
    """Creates a patrol route that walks in a square pattern"""
    return Routine(
        name="patrol_square",
        description="Walk in a square pattern, scanning at each corner",
        actions=[
            # Walk forward and turn right
            Action(type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}),
            # Quick scan
            Action(type=ActionType.SCAN, duration=2.0, params={"degrees": 180}),
            # Walk forward and turn right
            Action(type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}),
            # Repeat two more times to complete square
            Action(type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}),
            Action(type=ActionType.MOVE_AND_TURN, duration=3.0, params={"degrees": 90}),
        ],
    )


def create_cargo_delivery() -> Routine:
    """Creates a routine for delivering cargo"""
    return Routine(
        name="deliver_cargo",
        description="Standard cargo delivery sequence",
        actions=[
            # Approach drop-off point
            Action(
                type=ActionType.MOVE,
                duration=2.0,
                params={"direction": MovementDirection.FORWARD},
            ),
            # Hold action button to initiate delivery
            Action(type=ActionType.HOLD_KEY, duration=1.0, params={"key": "action"}),
            # Wait for animation
            Action(type=ActionType.WAIT, duration=2.0),
            # Step back
            Action(
                type=ActionType.MOVE,
                duration=1.0,
                params={"direction": MovementDirection.BACKWARD},
            ),
        ],
    )


# Collection of available routines
AVAILABLE_ROUTINES = {
    "360_scan": create_360_scan(),
    "patrol": create_patrol_route(),
    "deliver": create_cargo_delivery(),
}
