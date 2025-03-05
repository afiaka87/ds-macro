import pytest
import asyncio
from unittest.mock import MagicMock, patch
from ds_macro.models import MouseButton, MovementDirection, RoutineCategory
from ds_macro.controller import DSController
import ds_macro.routines as routines


@pytest.mark.asyncio
async def test_balance_left_routine_creation():
    """Test creating a balance_left routine directly"""
    controller = DSController()
    
    # Mock the run method to avoid execution and side effects
    with patch.object(controller, 'execute_sequence', return_value=None):
        # Create a routine directly instead of using the create_balance_left function
        routine = controller.create_routine(
            name="balance_left_test", categories=["movement", "balance"]
        )
        
        # Add the balance left actions
        with routine.sequential_actions() as actions:
            actions.mouse_press(MouseButton.LEFT)
            actions.wait(2.0)
            actions.mouse_release(MouseButton.LEFT)
        
        # Verify routine properties
        assert routine.name == "balance_left_test"
        assert "movement" in routine.categories
        assert "balance" in routine.categories
        
        # Verify sequence structure
        assert len(routine.sequences) == 1
        sequence = routine.sequences[0]
        assert not sequence.parallel
        
        # Verify actions
        actions = sequence.actions
        assert len(actions) == 3
        assert actions[0].type == "mouse_press" and actions[0].button == MouseButton.LEFT
        assert actions[1].type == "wait" and actions[1].duration == 2.0
        assert actions[2].type == "mouse_release" and actions[2].button == MouseButton.LEFT


@pytest.mark.asyncio
async def test_balance_right_routine_creation():
    """Test creating a balance_right routine directly"""
    controller = DSController()
    
    # Mock the run method to avoid execution and side effects
    with patch.object(controller, 'execute_sequence', return_value=None):
        # Create a routine directly
        routine = controller.create_routine(
            name="balance_right_test", categories=["movement", "balance"]
        )
        
        # Add the balance right actions
        with routine.sequential_actions() as actions:
            actions.mouse_press(MouseButton.RIGHT)
            actions.wait(2.0)
            actions.mouse_release(MouseButton.RIGHT)
        
        # Verify routine properties
        assert routine.name == "balance_right_test"
        assert "movement" in routine.categories
        assert "balance" in routine.categories
        
        # Verify sequence structure
        assert len(routine.sequences) == 1
        sequence = routine.sequences[0]
        assert not sequence.parallel
        
        # Verify actions
        actions = sequence.actions
        assert len(actions) == 3
        assert actions[0].type == "mouse_press" and actions[0].button == MouseButton.RIGHT
        assert actions[1].type == "wait" and actions[1].duration == 2.0
        assert actions[2].type == "mouse_release" and actions[2].button == MouseButton.RIGHT


@pytest.mark.asyncio
async def test_balance_both_routine_creation():
    """Test creating a balance_both routine directly"""
    controller = DSController()
    
    # Mock the run method to avoid execution and side effects
    with patch.object(controller, 'execute_sequence', return_value=None):
        # Create a routine directly
        routine = controller.create_routine(
            name="balance_both_test", categories=["movement", "balance"]
        )
        
        # Add the parallel press actions
        with routine.parallel_actions() as actions:
            actions.mouse_press(MouseButton.LEFT)
            actions.mouse_press(MouseButton.RIGHT)
            
        # Add the wait action
        with routine.sequential_actions() as actions:
            actions.wait(2.0)
            
        # Add the release actions
        with routine.sequential_actions() as actions:
            actions.mouse_release(MouseButton.LEFT)
            actions.mouse_release(MouseButton.RIGHT)
        
        # Verify routine properties
        assert routine.name == "balance_both_test"
        assert "movement" in routine.categories
        assert "balance" in routine.categories
        
        # Verify sequence structure - should have 3 sequences
        assert len(routine.sequences) == 3
        
        # First sequence: parallel actions to press both buttons
        sequence1 = routine.sequences[0]
        assert sequence1.parallel
        actions1 = sequence1.actions
        assert len(actions1) == 2
        assert actions1[0].type == "mouse_press" and actions1[0].button == MouseButton.LEFT
        assert actions1[1].type == "mouse_press" and actions1[1].button == MouseButton.RIGHT
        
        # Second sequence: wait
        sequence2 = routine.sequences[1]
        assert not sequence2.parallel
        actions2 = sequence2.actions
        assert len(actions2) == 1
        assert actions2[0].type == "wait" and actions2[0].duration == 2.0
        
        # Third sequence: release both buttons
        sequence3 = routine.sequences[2]
        assert not sequence3.parallel
        actions3 = sequence3.actions
        assert len(actions3) == 2
        assert actions3[0].type == "mouse_release" and actions3[0].button == MouseButton.LEFT
        assert actions3[1].type == "mouse_release" and actions3[1].button == MouseButton.RIGHT


@pytest.mark.asyncio
async def test_balance_left_moving_routine_creation():
    """Test creating a balance_left_moving routine directly"""
    controller = DSController()
    
    # Mock the run method to avoid execution and side effects
    with patch.object(controller, 'execute_sequence', return_value=None):
        # Create a routine directly
        routine = controller.create_routine(
            name="balance_left_moving_test", categories=["movement", "balance"]
        )
        
        # Add the parallel press actions
        with routine.parallel_actions() as actions:
            actions.press(MovementDirection.FORWARD)
            actions.mouse_press(MouseButton.LEFT)
            
        # Add the wait action
        with routine.sequential_actions() as actions:
            actions.wait(5.0)
            
        # Add the release actions
        with routine.sequential_actions() as actions:
            actions.release(MovementDirection.FORWARD)
            actions.mouse_release(MouseButton.LEFT)
        
        # Verify routine properties
        assert routine.name == "balance_left_moving_test"
        assert "movement" in routine.categories
        assert "balance" in routine.categories
        
        # Verify sequence structure - should have 3 sequences
        assert len(routine.sequences) == 3
        
        # First sequence: parallel press forward and left mouse
        sequence1 = routine.sequences[0]
        assert sequence1.parallel
        actions1 = sequence1.actions
        assert len(actions1) == 2
        assert actions1[0].type == "press" and actions1[0].key == MovementDirection.FORWARD
        assert actions1[1].type == "mouse_press" and actions1[1].button == MouseButton.LEFT
        
        # Second sequence: wait while moving
        sequence2 = routine.sequences[1]
        assert not sequence2.parallel
        actions2 = sequence2.actions
        assert len(actions2) == 1
        assert actions2[0].type == "wait" and actions2[0].duration == 5.0
        
        # Third sequence: release forward and left mouse
        sequence3 = routine.sequences[2]
        assert not sequence3.parallel
        actions3 = sequence3.actions
        assert len(actions3) == 2
        assert actions3[0].type == "release" and actions3[0].key == MovementDirection.FORWARD
        assert actions3[1].type == "mouse_release" and actions3[1].button == MouseButton.LEFT


@pytest.mark.asyncio
async def test_integration_balance_routines():
    """Integration test for balance routines with an actual controller"""
    controller = DSController()
    
    # Mock xdotool execution to avoid actual keypress and also mock _unregister_routine
    # to keep registry state intact for testing
    with patch.object(controller, '_execute_xdotool', return_value=None), \
         patch.object(controller, '_unregister_routine', return_value=None):
        # Create a balance routine
        balance_routine = controller.create_routine(
            name="balance_test", categories=["balance", "test"]
        )
        
        # Register it manually since we're patching _unregister_routine
        controller._register_routine(balance_routine)
        
        # Add some balance actions
        with balance_routine.sequential_actions() as actions:
            actions.mouse_press(MouseButton.LEFT)
            actions.wait(0.5)
            actions.mouse_release(MouseButton.LEFT)
        
        # Set the cancellation flag directly instead of running the routine
        balance_routine._cancelled = False
        
        # Verify the routine is in the registry
        assert "balance" in controller._routine_registry
        assert "test" in controller._routine_registry
        assert balance_routine in controller._routine_registry["balance"]
        
        # Test that cancellation works
        assert controller.cancel_category("balance")
        
        # Verify the routine's cancelled flag is set
        assert balance_routine._cancelled


@pytest.mark.asyncio
async def test_multiple_balance_routines_cancellation():
    """Test cancellation of multiple balance routines"""
    controller = DSController()
    
    # Mock xdotool execution and _unregister_routine to avoid actual execution
    # and keep registry state for testing
    with patch.object(controller, '_execute_xdotool', return_value=None), \
         patch.object(controller, '_unregister_routine', return_value=None):
        
        # Create multiple balance routines
        routines = []
        for i in range(3):
            routine = controller.create_routine(
                name=f"balance_test_{i}", 
                categories=["balance", "test"]
            )
            
            # Register manually since we mocked _unregister_routine
            controller._register_routine(routine)
            
            with routine.sequential_actions() as actions:
                actions.mouse_press(MouseButton.LEFT if i % 2 == 0 else MouseButton.RIGHT)
                actions.wait(0.5)
                actions.mouse_release(MouseButton.LEFT if i % 2 == 0 else MouseButton.RIGHT)
            
            # Set not cancelled state
            routine._cancelled = False
            routines.append(routine)
        
        # Verify routines are registered
        assert len(controller._routine_registry.get("balance", set())) == 3
        
        # Test cancellation by category
        controller.cancel_category("balance")
        
        # Verify all routines were marked as cancelled
        for routine in routines:
            assert routine._cancelled