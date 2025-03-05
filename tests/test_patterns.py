import pytest
from typing import List
from ds_macro.patterns import CommonActions
from ds_macro.models import (
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


class TestCommonActions:
    """Tests for CommonActions patterns"""

    def test_sprint_forward(self):
        """Test sprint_forward returns correct action sequence"""
        duration = 3.0
        actions = CommonActions.sprint_forward(duration)
        
        assert len(actions) == 5
        assert isinstance(actions[0], KeyPress)
        assert actions[0].key == MovementDirection.FORWARD
        assert isinstance(actions[1], KeyPress)
        assert actions[1].key == "sprint"
        assert isinstance(actions[2], Wait)
        assert actions[2].duration == duration
        assert isinstance(actions[3], KeyRelease)
        assert actions[3].key == "sprint"
        assert isinstance(actions[4], KeyRelease)
        assert actions[4].key == MovementDirection.FORWARD

    def test_strafe_movements(self):
        """Test strafing movements return correct action sequences"""
        # Test strafe left
        duration = 1.5
        left_actions = CommonActions.strafe_left(duration)
        
        assert len(left_actions) == 3
        assert isinstance(left_actions[0], KeyPress)
        assert left_actions[0].key == MovementDirection.LEFT
        assert isinstance(left_actions[1], Wait)
        assert left_actions[1].duration == duration
        assert isinstance(left_actions[2], KeyRelease)
        assert left_actions[2].key == MovementDirection.LEFT
        
        # Test strafe right
        right_actions = CommonActions.strafe_right(duration)
        
        assert len(right_actions) == 3
        assert isinstance(right_actions[0], KeyPress)
        assert right_actions[0].key == MovementDirection.RIGHT
        assert isinstance(right_actions[1], Wait)
        assert right_actions[1].duration == duration
        assert isinstance(right_actions[2], KeyRelease)
        assert right_actions[2].key == MovementDirection.RIGHT
        
        # Test backstep
        back_actions = CommonActions.backstep(duration)
        
        assert len(back_actions) == 3
        assert isinstance(back_actions[0], KeyPress)
        assert back_actions[0].key == MovementDirection.BACKWARD
        assert isinstance(back_actions[1], Wait)
        assert back_actions[1].duration == duration
        assert isinstance(back_actions[2], KeyRelease)
        assert back_actions[2].key == MovementDirection.BACKWARD

    def test_aim_and_fire(self):
        """Test aim_and_fire returns correct action sequence with proper shot count"""
        # Single shot (default)
        actions = CommonActions.aim_and_fire()
        
        assert len(actions) == 3  # Right press, Left click, Right release
        assert isinstance(actions[0], MousePress) 
        assert actions[0].button == MouseButton.RIGHT
        assert isinstance(actions[1], MouseClick)
        assert actions[1].button == MouseButton.LEFT
        assert isinstance(actions[2], MouseRelease)
        assert actions[2].button == MouseButton.RIGHT
        
        # Multiple shots with delay
        shots = 3
        delay = 0.3
        multi_actions = CommonActions.aim_and_fire(shots=shots, delay=delay)
        
        # Right press, (Left click, Wait) * (shots-1), Left click, Right release
        expected_length = 1 + (shots * 2 - 1) + 1  # MousePress + (clicks and waits) + MouseRelease
        assert len(multi_actions) == expected_length
        assert isinstance(multi_actions[0], MousePress)
        assert multi_actions[0].button == MouseButton.RIGHT
        
        # Check that we have the right number of clicks and delays
        clicks = [a for a in multi_actions if isinstance(a, MouseClick)]
        delays = [a for a in multi_actions if isinstance(a, Wait)]
        
        assert len(clicks) == shots
        assert len(delays) == shots - 1  # One less delay than shots
        
        for d in delays:
            assert d.duration == delay

    def test_quick_actions(self):
        """Test simple quick actions like crouch, jump, etc."""
        # Test crouch toggle
        crouch_actions = CommonActions.crouch_toggle()
        assert len(crouch_actions) == 1
        assert isinstance(crouch_actions[0], KeyTap)
        assert crouch_actions[0].key == "crouch"
        
        # Test jump
        jump_actions = CommonActions.jump()
        assert len(jump_actions) == 1
        assert isinstance(jump_actions[0], KeyTap)
        assert jump_actions[0].key == "jump"
        
        # Test reload
        reload_actions = CommonActions.reload()
        assert len(reload_actions) == 1
        assert isinstance(reload_actions[0], KeyTap)
        assert reload_actions[0].key == "reload"
        
        # Test interact
        interact_actions = CommonActions.interact()
        assert len(interact_actions) == 1
        assert isinstance(interact_actions[0], KeyTap)
        assert interact_actions[0].key == "action"
        assert interact_actions[0].duration == 0.5  # Special duration for interact
        
        # Test menu actions
        open_inventory = CommonActions.open_inventory()
        assert len(open_inventory) == 1
        assert isinstance(open_inventory[0], KeyTap)
        assert open_inventory[0].key == "cargo"
        
        close_menu = CommonActions.close_menu()
        assert len(close_menu) == 1
        assert isinstance(close_menu[0], KeyTap)
        assert close_menu[0].key == "esc"

    def test_scan_environment(self):
        """Test scan_environment returns correct action sequence"""
        actions = CommonActions.scan_environment()
        
        assert len(actions) == 2
        assert isinstance(actions[0], KeyPress)
        assert actions[0].key == "scan"
        assert isinstance(actions[1], KeyRelease)
        assert actions[1].key == "scan"