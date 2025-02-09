# models.py
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from enum import Enum


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class MovementDirection(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"


class KeyMapping(BaseModel):
    forward: str = "w"
    backward: str = "s"
    left: str = "a"
    right: str = "d"
    sprint: str = "shift"
    crouch: str = "c"
    jump: str = "space"
    walk: str = "ctrl"
    attack: str = "v"
    action: str = "f"
    reload: str = "r"
    ammo: str = "z"
    breath: str = "alt"
    carry: str = "e"
    cargo: str = "i"
    cuff: str = "Tab"
    tool: str = "1"
    function: str = "2"
    item: str = "3"
    equipment: str = "4"
    compass: str = "g"
    scan: str = "q"
    like: str = "5"
    photo: str = "F8"


class MouseConfig(BaseModel):
    pixels_per_degree: float = Field(default=32.5, gt=0)
    steps_per_second: int = Field(default=60, gt=0)


class ControllerConfig(BaseModel):
    keys: KeyMapping = Field(default_factory=KeyMapping)
    mouse: MouseConfig = Field(default_factory=MouseConfig)
    mouse_buttons: Dict[MouseButton, int] = Field(
        default={MouseButton.LEFT: 1, MouseButton.RIGHT: 3}
    )


class ActionType(str, Enum):
    """Types of actions that can be performed"""

    MOVE = "move"
    TURN = "turn"
    MOVE_AND_TURN = "move_and_turn"
    SPRINT = "sprint"
    SPRINT_AND_TURN = "sprint_and_turn"
    HOLD_KEY = "hold_key"
    HOLD_MOUSE = "hold_mouse"
    WAIT = "wait"  # Simple delay
    SCAN = "scan"


class Action(BaseModel):
    """Single action in a routine"""

    type: ActionType
    duration: Optional[float] = None
    params: Optional[dict] = None

    class Config:
        extra = "forbid"


class Routine(BaseModel):
    """A sequence of actions to be performed"""

    name: str
    description: str
    actions: List[Action]
