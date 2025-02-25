"""DS-Macro: A powerful Python library for automating complex input sequences in games."""

from .models import (
    MouseButton,
    MovementDirection,
    RoutineCategory,
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
from ds_macro.controller import DSController, Routine, ActionGroup
from ds_macro.patterns import CommonActions
from ds_macro.routines import AVAILABLE_ROUTINES, run_routine

__all__ = [
    "DSController",
    "Routine",
    "ActionGroup",
    "MouseButton",
    "MovementDirection",
    "RoutineCategory",
    "InputAction",
    "KeyPress",
    "KeyRelease",
    "KeyTap",
    "Wait",
    "Turn",
    "MouseMove",
    "MousePress",
    "MouseRelease",
    "MouseClick",
    "ActionSequence",
    "CommonActions",
    "RoutineCategory",
]
