import pytest
import asyncio
import subprocess
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ds_macro.models import (
    MouseButton,
    ControllerConfig,
    KeyPress,
    KeyRelease,
    KeyTap,
    MouseMove,
    Wait,
)
from ds_macro.controller import DSController
from ds_macro.exceptions import KeyboardError, MouseMovementError, XdotoolError


@pytest.mark.asyncio
async def test_xdotool_not_available():
    """Test behavior when xdotool is not available."""
    controller = DSController()

    # Mock subprocess.run to raise FileNotFoundError (when xdotool is not found)
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'xdotool'")

        # Since controller initialization calls _get_mouse_position which uses xdotool,
        # we need to test a different method
        action = KeyPress(key="w")

        # The controller should log a warning but not crash
        await controller._execute_action(action)

        # Check that the key was added to pressed_keys despite xdotool failure
        assert "w" in controller.pressed_keys


@pytest.mark.asyncio
async def test_xdotool_error_propagation():
    """Test that xdotool errors are properly converted to KeyboardError."""
    controller = DSController()

    # Mock subprocess.run to raise CalledProcessError
    with patch("subprocess.run") as mock_run:
        error = subprocess.CalledProcessError(1, ["xdotool", "keydown", "q"])
        error.stderr = "Error: DISPLAY environment variable is empty"
        mock_run.side_effect = error

        # Try to execute a key press action
        action = KeyPress(key="q")

        # Should raise a KeyboardError
        with pytest.raises(KeyboardError) as exc_info:
            await controller._execute_action(action)

        # Check the error message includes details from the original error
        assert "Failed to press key q" in str(exc_info.value)
        assert "xdotool command failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_emergency_stop_with_xdotool_error():
    """Test that emergency_stop works even when xdotool fails."""
    controller = DSController()

    # First add some keys and mouse buttons to the pressed sets
    controller.pressed_keys.add("w")
    controller.pressed_keys.add("shift")
    controller.pressed_mouse_buttons.add(MouseButton.LEFT)

    # Mock subprocess.run to raise CalledProcessError
    with patch("subprocess.run") as mock_run:
        error = subprocess.CalledProcessError(1, ["xdotool", "keyup", "w"])
        error.stderr = "Error: DISPLAY environment variable is empty"
        mock_run.side_effect = error

        # Call emergency stop
        await controller.emergency_stop()

        # Despite xdotool errors, the controller should clear its internal state
        assert len(controller.pressed_keys) == 0
        assert len(controller.pressed_mouse_buttons) == 0


@pytest.mark.asyncio
async def test_mouse_movement_with_xdotool_error():
    """Test that mouse movement errors are properly handled."""
    controller = DSController()

    # Mock subprocess.run to raise CalledProcessError
    with patch("subprocess.run") as mock_run:
        error = subprocess.CalledProcessError(
            1, ["xdotool", "mousemove_relative", "--", "10", "0"]
        )
        error.stderr = "Error: DISPLAY environment variable is empty"
        mock_run.side_effect = error

        action = MouseMove(dx=10, dy=0)

        # Should raise a MouseMovementError
        with pytest.raises(MouseMovementError) as exc_info:
            await controller._execute_action(action)

        assert "Failed to move mouse" in str(exc_info.value)


@pytest.mark.asyncio
async def test_graceful_fallback_in_testing_environment():
    """Test that controller falls back gracefully in testing environments without xdotool."""

    # Create a controller and patch get_mouse_position to avoid xdotool dependency
    with patch.object(DSController, "_get_mouse_position") as mock_get_pos:
        controller = DSController()

        # Simulate a testing environment where xdotool is not available
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError(
                "No such file or directory: 'xdotool'"
            )

            # Test a sequence that doesn't require actual input
            action = Wait(duration=0.1)
            await controller._execute_action(action)

            # Test should pass without errors
