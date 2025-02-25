# patterns.py
from typing import List
from .models import (
    InputAction,
    KeyMapping,
    KeyPress,
    KeyRelease,
    Wait,
    Turn,
    MovementDirection,
    MouseButton,
    MousePress,
    MouseRelease,
    MouseClick,
    KeyTap,
)


class CommonActions:
    @staticmethod
    def sprint_forward(duration: float) -> List[InputAction]:
        """Sprint forward for the specified duration"""
        return [
            KeyPress(key=MovementDirection.FORWARD),
            KeyPress(key="sprint"),
            Wait(duration=duration),
            KeyRelease(key="sprint"),
            KeyRelease(key=MovementDirection.FORWARD),
        ]

    @staticmethod
    def scan_environment() -> List[InputAction]:
        """Perform an environmental scan in the forward direction"""
        return [
            KeyPress(key="scan"),
            KeyRelease(key="scan"),
        ]

    @staticmethod
    def strafe_left(duration: float) -> List[InputAction]:
        """Strafe left for the specified duration"""
        return [
            KeyPress(key=MovementDirection.LEFT),
            Wait(duration=duration),
            KeyRelease(key=MovementDirection.LEFT),
        ]

    @staticmethod
    def strafe_right(duration: float) -> List[InputAction]:
        """Strafe right for the specified duration"""
        return [
            KeyPress(key=MovementDirection.RIGHT),
            Wait(duration=duration),
            KeyRelease(key=MovementDirection.RIGHT),
        ]

    @staticmethod
    def backstep(duration: float) -> List[InputAction]:
        """Step backward for the specified duration"""
        return [
            KeyPress(key=MovementDirection.BACKWARD),
            Wait(duration=duration),
            KeyRelease(key=MovementDirection.BACKWARD),
        ]

    @staticmethod
    def aim_and_fire(shots: int = 1, delay: float = 0.2) -> List[InputAction]:
        """Aim down sights and fire a specified number of shots"""
        actions = [MousePress(button=MouseButton.RIGHT)]  # Aim

        for i in range(shots):
            actions.append(MouseClick(button=MouseButton.LEFT, duration=0.1))
            if i < shots - 1:  # Add delay between shots but not after the last one
                actions.append(Wait(duration=delay))

        actions.append(MouseRelease(button=MouseButton.RIGHT))  # Release aim
        return actions

    @staticmethod
    def crouch_toggle() -> List[InputAction]:
        """Toggle crouch state"""
        return [KeyTap(key="crouch", duration=0.1)]

    @staticmethod
    def jump() -> List[InputAction]:
        """Perform a jump"""
        return [KeyTap(key="jump", duration=0.1)]

    @staticmethod
    def reload() -> List[InputAction]:
        """Reload current weapon"""
        return [KeyTap(key="reload", duration=0.1)]

    @staticmethod
    def interact() -> List[InputAction]:
        """Interact with object in front of player"""
        return [KeyTap(key="action", duration=0.5)]

    @staticmethod
    def open_inventory() -> List[InputAction]:
        """Open inventory menu"""
        return [KeyTap(key="cargo", duration=0.1)]

    @staticmethod
    def close_menu() -> List[InputAction]:
        """Close current menu"""
        return [KeyTap(key="esc", duration=0.1)]
