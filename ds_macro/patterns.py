# patterns.py
from typing import List, Callable, Optional
from .models import (
    InputAction,
    KeyPress,
    KeyRelease,
    Wait,
    MovementDirection,
    MouseButton,
    MousePress,
    MouseRelease,
    MouseClick,
    KeyTap,
)


def key_sequence(key: str, duration: float) -> List[InputAction]:
    """Create a press-wait-release sequence for a key."""
    return [
        KeyPress(key=key),
        Wait(duration=duration),
        KeyRelease(key=key),
    ]


def key_tap(key: str, duration: float = 0.1) -> List[InputAction]:
    """Generate a simple key tap action."""
    return [KeyTap(key=key, duration=duration)]


def press_release(key: str) -> List[InputAction]:
    """Generate a press-release sequence without waiting."""
    return [KeyPress(key=key), KeyRelease(key=key)]


# Movement patterns
def sprint_forward(duration: float) -> List[InputAction]:
    """Sprint forward for the specified duration."""
    return [
        KeyPress(key=MovementDirection.FORWARD),
        KeyPress(key="sprint"),
        Wait(duration=duration),
        KeyRelease(key="sprint"),
        KeyRelease(key=MovementDirection.FORWARD),
    ]


def strafe_left(duration: float) -> List[InputAction]:
    """Strafe left for the specified duration."""
    return key_sequence(MovementDirection.LEFT, duration)


def strafe_right(duration: float) -> List[InputAction]:
    """Strafe right for the specified duration."""
    return key_sequence(MovementDirection.RIGHT, duration)


def backstep(duration: float) -> List[InputAction]:
    """Step backward for the specified duration."""
    return key_sequence(MovementDirection.BACKWARD, duration)


# Interaction patterns
def scan_environment() -> List[InputAction]:
    """Perform an environmental scan in the forward direction."""
    return press_release("scan")


def interact() -> List[InputAction]:
    """Interact with object in front of player."""
    return key_tap("action", duration=0.5)


def open_inventory() -> List[InputAction]:
    """Open inventory menu."""
    return key_tap("cargo")


def close_menu() -> List[InputAction]:
    """Close current menu."""
    return key_tap("esc")


# Combat patterns
def aim_and_fire(shots: int = 1, delay: float = 0.2) -> List[InputAction]:
    """Aim down sights and fire a specified number of shots."""
    actions = [MousePress(button=MouseButton.RIGHT)]  # Aim

    for i in range(shots):
        actions.append(MouseClick(button=MouseButton.LEFT, duration=0.1))
        if i < shots - 1:  # Add delay between shots but not after the last one
            actions.append(Wait(duration=delay))

    actions.append(MouseRelease(button=MouseButton.RIGHT))  # Release aim
    return actions


def crouch_toggle() -> List[InputAction]:
    """Toggle crouch state."""
    return key_tap("crouch")


def jump() -> List[InputAction]:
    """Perform a jump."""
    return key_tap("jump")


def reload() -> List[InputAction]:
    """Reload current weapon."""
    return key_tap("reload")


# CommonActions class for backward compatibility
class CommonActions:
    """
    Legacy class for backward compatibility.
    Delegates to the functional implementations.
    """

    @staticmethod
    def sprint_forward(duration: float) -> List[InputAction]:
        return sprint_forward(duration)

    @staticmethod
    def scan_environment() -> List[InputAction]:
        return scan_environment()

    @staticmethod
    def strafe_left(duration: float) -> List[InputAction]:
        return strafe_left(duration)

    @staticmethod
    def strafe_right(duration: float) -> List[InputAction]:
        return strafe_right(duration)

    @staticmethod
    def backstep(duration: float) -> List[InputAction]:
        return backstep(duration)

    @staticmethod
    def aim_and_fire(shots: int = 1, delay: float = 0.2) -> List[InputAction]:
        return aim_and_fire(shots, delay)

    @staticmethod
    def crouch_toggle() -> List[InputAction]:
        return crouch_toggle()

    @staticmethod
    def jump() -> List[InputAction]:
        return jump()

    @staticmethod
    def reload() -> List[InputAction]:
        return reload()

    @staticmethod
    def interact() -> List[InputAction]:
        return interact()

    @staticmethod
    def open_inventory() -> List[InputAction]:
        return open_inventory()

    @staticmethod
    def close_menu() -> List[InputAction]:
        return close_menu()