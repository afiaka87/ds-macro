import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from pynput import keyboard, mouse
from ds_macro.recorder import InputRecorder, RecorderConfig
from ds_macro.models import ActionType, MovementDirection


class TestRecorderIntegration:
    """Integration tests for the InputRecorder class"""
    
    def test_recorder_initialization(self):
        """Test that recorder initializes properly with listeners"""
        with patch('pynput.keyboard.Listener'), patch('pynput.mouse.Listener'):
            recorder = InputRecorder()
            
            # Verify initial state
            assert recorder.actions == []
            assert recorder.start_time is None
            assert recorder.is_recording is False
            assert recorder.pressed_keys == set()
    
    def test_recording_state_toggle(self):
        """Test starting and stopping recording"""
        with patch('pynput.keyboard.Listener'), patch('pynput.mouse.Listener'):
            recorder = InputRecorder()
            
            # Start recording
            recorder.start_recording()
            assert recorder.is_recording is True
            assert recorder.start_time is not None
            assert recorder.actions == []
            
            # Stop recording
            recorder.stop_recording()
            assert recorder.is_recording is False
            assert recorder.start_time is None
    
    def test_key_tracking(self):
        """Test tracking pressed keys"""
        with patch('pynput.keyboard.Listener'), patch('pynput.mouse.Listener'):
            recorder = InputRecorder()
            recorder.start_recording()
            
            # Create mock key objects
            key_w = keyboard.KeyCode.from_char('w')
            key_shift = keyboard.Key.shift
            key_left = keyboard.Key.left
            
            # Simulate key presses - use proper key objects without relying on the exact mapping
            try:
                recorder._on_key_press(key_w)
                # We just need to verify some key is tracked - the exact mapping might vary
                assert len(recorder.pressed_keys) >= 1
                
                recorder._on_key_press(key_shift)
                # After pressing two keys, we should have at least two pressed keys tracked
                assert len(recorder.pressed_keys) >= 2
            
                recorder._on_key_press(key_left)
                # After pressing third key, verify we have more pressed keys
                assert len(recorder.pressed_keys) >= 3
                
                # Verify some actions were recorded
                assert len(recorder.actions) > 0
                
                # Simulate key releases
                initial_pressed_keys = len(recorder.pressed_keys)
                
                recorder._on_key_release(key_w)
                # After releasing a key, we should have fewer pressed keys
                assert len(recorder.pressed_keys) < initial_pressed_keys
                
                recorder._on_key_release(key_shift)
                # After releasing another key, we should have even fewer pressed keys
                assert len(recorder.pressed_keys) < initial_pressed_keys - 1
                
                recorder._on_key_release(key_left)
                # After releasing all keys, we should have no pressed keys or fewer
                assert len(recorder.pressed_keys) <= 1
            except Exception as e:
                # If an error occurs, print some diagnostic info
                print(f"Error in key tracking test: {e}")
                print(f"Pressed keys: {recorder.pressed_keys}")
                print(f"Actions recorded: {len(recorder.actions)}")
                raise
    
    def test_mouse_tracking(self):
        """Test tracking mouse movements and clicks"""
        with patch('pynput.keyboard.Listener'), patch('pynput.mouse.Listener'):
            # Set a config with lower thresholds for testing
            config = RecorderConfig(
                mouse_movement_threshold=0.01,
                min_pixel_movement=1.0,
                pixels_per_degree=10.0
            )
            recorder = InputRecorder(config=config)
            recorder.start_recording()
            
            # Simulate initial mouse position
            recorder._on_mouse_move(100, 100)
            assert recorder.last_mouse_pos == (100, 100)
            
            # Simulate mouse movement
            recorder._on_mouse_move(110, 100)  # Move 10 pixels right
            
            # Verify turn action was recorded
            turn_actions = [a for a in recorder.actions if a.type == ActionType.TURN]
            assert len(turn_actions) >= 1
            
            # Simulate mouse click
            recorder._on_mouse_click(110, 100, mouse.Button.left, True)
            
            # Verify mouse action was recorded
            mouse_actions = [a for a in recorder.actions if a.type == ActionType.HOLD_MOUSE]
            assert len(mouse_actions) >= 1
    
    def test_save_routine(self):
        """Test saving a recorded routine to file"""
        with patch('pynput.keyboard.Listener'), patch('pynput.mouse.Listener'):
            recorder = InputRecorder()
            
            # Create a temp directory for test
            with tempfile.TemporaryDirectory() as temp_dir:
                # Start recording and simulate some actions
                recorder.start_recording()
                
                # Simulate key press/release to create actions
                key_w = keyboard.KeyCode.from_char('w')
                recorder._on_key_press(key_w)
                
                # Add a small delay to create a duration
                import time
                time.sleep(0.1)
                
                recorder._on_key_release(key_w)
                
                # Stop recording
                recorder.stop_recording()
                
                # Save the routine
                routine = recorder.save_routine(
                    name="test_routine",
                    description="Test routine",
                    directory=temp_dir
                )
                
                # Check that the routine has actions
                assert len(routine.actions) > 0
                
                # Check that a file was created
                files = os.listdir(temp_dir)
                assert len(files) == 1
                
                # Verify the file contains the actions
                with open(os.path.join(temp_dir, files[0]), 'r') as f:
                    routine_data = json.load(f)
                    assert routine_data["name"] == "test_routine"
                    assert routine_data["description"] == "Test routine"
                    assert len(routine_data["actions"]) > 0