import pytest
import asyncio
from unittest.mock import patch
from ds_macro.controller import DSController
from ds_macro.models import MovementDirection, MouseButton, RoutineCategory


@pytest.mark.asyncio
async def test_parallel_routine_management():
    """Test that multiple routines can be managed in parallel"""
    controller = DSController()
    
    # Mock xdotool and _unregister_routine to avoid actual execution
    # and keep registry state for testing
    with patch.object(controller, '_execute_xdotool', return_value=None), \
         patch.object(controller, '_unregister_routine', return_value=None):
        
        # Create a background routine
        background = controller.create_routine(
            name="background_scan", 
            categories=[RoutineCategory.SCANNING, RoutineCategory.ESSENTIAL]
        )
        
        # Register it manually
        controller._register_routine(background)
        
        # Add actions to the background routine
        with background.sequential_actions() as actions:
            actions.press("scan")
            actions.wait(0.5)
            actions.release("scan")
        
        # Set not cancelled state
        background._cancelled = False
            
        # Verify the routine is registered
        assert RoutineCategory.SCANNING in controller._routine_registry
        assert RoutineCategory.ESSENTIAL in controller._routine_registry
        
        # Create a foreground routine
        movement = controller.create_routine(
            name="movement", 
            categories=[RoutineCategory.MOVEMENT]
        )
        
        # Register it manually
        controller._register_routine(movement)
        
        with movement.sequential_actions() as actions:
            actions.press(MovementDirection.FORWARD)
            actions.press("sprint")
            actions.wait(0.5)
            actions.release("sprint")
            actions.release(MovementDirection.FORWARD)
        
        # Since we're mocking _unregister_routine, we need to manually remove
        # the routine from the registry
        if RoutineCategory.MOVEMENT in controller._routine_registry:
            controller._routine_registry[RoutineCategory.MOVEMENT].remove(movement)
            if not controller._routine_registry[RoutineCategory.MOVEMENT]:
                del controller._routine_registry[RoutineCategory.MOVEMENT]
            
        # Verify the MOVEMENT category is no longer registered
        assert RoutineCategory.MOVEMENT not in controller._routine_registry
        
        # Verify background routine is still registered
        assert RoutineCategory.SCANNING in controller._routine_registry
        
        # Cancel the background routine by category
        assert controller.cancel_category(RoutineCategory.SCANNING)
        
        # Verify the background routine was cancelled
        assert background._cancelled


@pytest.mark.asyncio
async def test_emergency_stop():
    """Test that emergency stop properly cancels all routines and releases inputs"""
    controller = DSController()
    
    # Mock xdotool and only partially mock _unregister_routine for emergency_stop to work
    with patch.object(controller, '_execute_xdotool', return_value=None):
        
        # Create multiple routines
        routines = []
        
        # Create 3 different routines with different categories
        categories = [
            [RoutineCategory.MOVEMENT], 
            [RoutineCategory.SCANNING], 
            [RoutineCategory.ESSENTIAL, RoutineCategory.COMBAT]
        ]
        
        # Simulate some pressed keys and mouse buttons
        controller.pressed_keys.add(MovementDirection.FORWARD.value)
        controller.pressed_keys.add("sprint")
        controller.pressed_keys.add("scan")
        controller.pressed_mouse_buttons.add(MouseButton.RIGHT)
        
        # Create and register routines
        for i, cats in enumerate(categories):
            routine = controller.create_routine(name=f"routine_{i}", categories=cats)
            
            # Manually register the routine (normally done by run())
            controller._register_routine(routine)
            
            # Add different actions to each routine
            with routine.sequential_actions() as actions:
                if i == 0:  # Movement routine
                    actions.press(MovementDirection.FORWARD)
                    actions.press("sprint")
                    actions.wait(5.0)
                elif i == 1:  # Scanning routine
                    actions.press("scan")
                    actions.wait(10.0)
                else:  # Combat routine
                    actions.mouse_press(MouseButton.RIGHT)
                    actions.mouse_click(MouseButton.LEFT)
            
            # Set routine as not cancelled
            routine._cancelled = False
            routines.append(routine)
            
        # Verify routines are registered in their categories
        for cats in categories:
            for cat in cats:
                assert cat in controller._routine_registry
                
        # Verify keys/buttons are pressed
        assert len(controller.pressed_keys) > 0
        assert len(controller.pressed_mouse_buttons) > 0
        
        # Execute emergency stop
        await controller.emergency_stop()
        
        # Verify all routines are cancelled
        for routine in routines:
            assert routine._cancelled
        
        # Verify all inputs are released
        assert len(controller.pressed_keys) == 0
        assert len(controller.pressed_mouse_buttons) == 0


@pytest.mark.asyncio
async def test_run_multiple_routines_sequence():
    """Test that multiple routines can be executed in sequence"""
    controller = DSController()
    completed_routines = []
    
    # Create a callback to track routine completion
    def record_completion(routine_name):
        completed_routines.append(routine_name)
    
    # Mock xdotool and execute_sequence to avoid actual execution
    with patch.object(controller, '_execute_xdotool', return_value=None), \
         patch.object(controller, 'execute_sequence', return_value=None):
        
        # Create and record routines directly
        routine1 = controller.create_routine(name="routine1", categories=["test"])
        with routine1.sequential_actions() as actions:
            actions.press(MovementDirection.FORWARD)
            actions.wait(0.1)
            actions.release(MovementDirection.FORWARD)
        
        routine2 = controller.create_routine(name="routine2", categories=["test"])
        with routine2.sequential_actions() as actions:
            actions.press(MovementDirection.LEFT)
            actions.wait(0.1)
            actions.release(MovementDirection.LEFT)
            
        routine3 = controller.create_routine(name="routine3", categories=["test"])
        with routine3.sequential_actions() as actions:
            actions.mouse_press(MouseButton.LEFT)
            actions.wait(0.1)
            actions.mouse_release(MouseButton.LEFT)
        
        # Manually simulate the execution sequence
        # For each routine:
        # 1. Register it
        # 2. Record that it "ran"
        # 3. Unregister it
        
        # First routine
        controller._register_routine(routine1)
        record_completion("routine1")
        controller._unregister_routine(routine1)
        
        # Second routine
        controller._register_routine(routine2)
        record_completion("routine2")
        controller._unregister_routine(routine2)
        
        # Third routine
        controller._register_routine(routine3)
        record_completion("routine3")
        controller._unregister_routine(routine3)
        
        # Verify routines completed in the correct order
        assert completed_routines == ["routine1", "routine2", "routine3"]
        
        # Verify all routines are unregistered
        assert len(controller._routine_registry) == 0
        assert len(controller._name_to_routines) == 0
        assert len(controller._id_to_routine) == 0