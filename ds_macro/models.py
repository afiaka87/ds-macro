# models.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Set, Union
from enum import Enum


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class MovementDirection(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    UP = "up"  # Added UP direction for camera/menu controls
    DOWN = "down"  # Added DOWN direction for camera/menu controls


class ActionType(str, Enum):
    """Types of actions that can be performed"""

    MOVE = "move"
    TURN = "turn"
    MOVE_AND_TURN = "move_and_turn"
    SPRINT = "sprint"
    SPRINT_AND_TURN = "sprint_and_turn"
    HOLD_KEY = "hold_key"
    HOLD_MOUSE = "hold_mouse"
    WAIT = "wait"
    SCAN = "scan"


class RoutineCategory(str, Enum):
    """Categories for organizing routines"""

    MOVEMENT = "movement"
    COMBAT = "combat"
    SCANNING = "scanning"
    ESSENTIAL = "essential"
    INTERACTION = "interaction"


class InputAction(BaseModel):
    """Base class for all input actions"""

    type: str
    duration: Optional[float] = None


class KeyPress(InputAction):
    type: str = "press"
    key: str


class KeyRelease(InputAction):
    type: str = "release"
    key: str


class KeyTap(InputAction):
    type: str = "tap"
    key: str
    duration: float = 0.1


class Wait(InputAction):
    type: str = "wait"
    duration: float


class Turn(InputAction):
    type: str = "turn"
    degrees: float
    duration: float = 1.0


class MouseMove(InputAction):
    type: str = "mouse_move"
    dx: float
    dy: float
    duration: float = 0.1


class MousePress(InputAction):
    type: str = "mouse_press"
    button: MouseButton


class MouseRelease(InputAction):
    type: str = "mouse_release"
    button: MouseButton


class MouseClick(InputAction):
    type: str = "mouse_click"
    button: MouseButton
    duration: float = 0.1


class ActionSequence(BaseModel):
    """A sequence of actions that can be executed in parallel or sequentially"""

    actions: List[InputAction]
    parallel: bool = False


class KeyMapping(BaseModel):
    forward: str = "w"
    backward: str = "s"
    left: str = "a"
    right: str = "d"
    up: str = "up"  # Added for camera/menu navigation
    down: str = "down"  # Added for camera/menu navigation
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
    photo_mode: str = "p"  # Added for photo mode
    esc: str = "escape"  # Added for menu navigation


class MouseConfig(BaseModel):
    pixels_per_degree: float = Field(default=32.5, gt=0)
    steps_per_second: int = Field(default=60, gt=0)


class ControllerConfig(BaseModel):
    keys: KeyMapping = Field(default_factory=KeyMapping)
    mouse: MouseConfig = Field(default_factory=MouseConfig)
    mouse_buttons: Dict[MouseButton, int] = Field(
        default={MouseButton.LEFT: 1, MouseButton.RIGHT: 3, MouseButton.MIDDLE: 2}
    )


class Action(BaseModel):
    """Single action in a routine - Legacy model for backward compatibility"""

    type: ActionType
    duration: Optional[float] = None
    params: Optional[dict] = None

    class Config:
        extra = "forbid"


class Routine(BaseModel):
    """A sequence of actions to be performed - Legacy model for backward compatibility"""

    name: str
    description: str
    actions: List[Action]
