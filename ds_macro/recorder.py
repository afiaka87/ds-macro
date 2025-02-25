# recorder.py
import logging
import time
from typing import List, Optional, Dict, Set
from pydantic import BaseModel
from pynput import mouse, keyboard

from models import (
    Action,
    ActionType,
    Routine,
    MovementDirection,
    MouseButton,
    KeyMapping,
)

logger = logging.getLogger(__name__)


class RecorderConfig(BaseModel):
    """Configuration for input recording"""
    # Minimum time in seconds between recorded mouse movements
    mouse_movement_threshold: float = 0.05
    # Minimum mouse movement in pixels to record
    min_pixel_movement: float = 5.0
    # How many degrees of rotation one pixel represents
    pixels_per_degree: float = 32.5


class InputRecorder:
    def __init__(self, config: Optional[RecorderConfig] = None):
        """Initialize recorder with optional custom configuration"""
        self.config = config or RecorderConfig()
        self.actions: List[Action] = []
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.last_mouse_pos: Optional[tuple[int, int]] = None
        self.pressed_keys: Set[str] = set()
        self.cumulative_mouse_movement: float = 0.0
        self.is_recording = False  # Track recording state
        self.TOGGLE_KEY = '`'  # Backtick/grave accent key
        
        # Initialize listeners
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        # Key mappings
        self.key_mapping = KeyMapping()
        self.reverse_key_map = {v: k for k, v in self.key_mapping.model_dump().items()}
        
        # Special key mappings for arrow keys etc
        self.special_key_map = {
            'left': MovementDirection.LEFT.value,
            'right': MovementDirection.RIGHT.value,
            'up': MovementDirection.FORWARD.value,
            'down': MovementDirection.BACKWARD.value,
            'space': 'space',
            'shift': 'shift',
            'shift_r': 'shift',
            'ctrl': 'ctrl',
            'ctrl_r': 'ctrl',
            'alt': 'alt',
            'alt_r': 'alt',
            'tab': 'tab',
            'escape': 'esc',
            'grave': self.TOGGLE_KEY  # Map grave/backtick
        }
        
        # Start listeners immediately
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        logger.info(f"Input recorder initialized - press {self.TOGGLE_KEY} key to start/stop recording")
        self.reverse_key_map = {v: k for k, v in self.key_mapping.dict().items()}
        
        # Special key mappings for arrow keys etc
        self.special_key_map = {
            'left': MovementDirection.LEFT.value,
            'right': MovementDirection.RIGHT.value,
            'up': MovementDirection.FORWARD.value,
            'down': MovementDirection.BACKWARD.value,
            'space': 'space',
            'shift': 'shift',
            'shift_r': 'shift',
            'ctrl': 'ctrl',
            'ctrl_r': 'ctrl',
            'alt': 'alt',
            'alt_r': 'alt',
            'tab': 'tab',
            'escape': 'esc'
        }
        
        logger.debug(f"Initialized with key mappings: {self.reverse_key_map}")
        logger.debug(f"Special key mappings: {self.special_key_map}")

    def _get_time_since_last(self) -> float:
        """Get time since last action, updating last_action_time"""
        current_time = time.time()
        if self.last_action_time is None:
            duration = 0.0
        else:
            duration = current_time - self.last_action_time
        self.last_action_time = current_time
        return duration

    def _on_mouse_move(self, x: int, y: int) -> None:
        """Handle mouse movement events"""
        if self.start_time is None:
            return
            
        logger.debug(f"Mouse moved to ({x}, {y})")
            
        if self.last_mouse_pos is None:
            self.last_mouse_pos = (x, y)
            return

        dx = x - self.last_mouse_pos[0]
        self.last_mouse_pos = (x, y)
        
        # Accumulate horizontal movement (for turning)
        self.cumulative_mouse_movement += dx
        
        # Only record movement if it exceeds threshold
        if abs(self.cumulative_mouse_movement) >= self.config.min_pixel_movement:
            degrees = self.cumulative_mouse_movement / self.config.pixels_per_degree
            duration = self._get_time_since_last()
            
            # If keys are being held while turning, record as combined action
            if MovementDirection.FORWARD.value in self.pressed_keys:
                if "sprint" in self.pressed_keys:
                    action_type = ActionType.SPRINT_AND_TURN
                else:
                    action_type = ActionType.MOVE_AND_TURN
            else:
                action_type = ActionType.TURN
                
            self.actions.append(
                Action(
                    type=action_type,
                    duration=duration,
                    params={"degrees": degrees}
                )
            )
            self.cumulative_mouse_movement = 0.0

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Handle mouse click events"""
        if self.start_time is None:
            return
            
        logger.debug(f"Mouse button {button} {'pressed' if pressed else 'released'} at ({x}, {y})")
            
        # Convert pynput button to our MouseButton enum
        button_map = {
            mouse.Button.left: MouseButton.LEFT,
            mouse.Button.right: MouseButton.RIGHT,
        }
        
        if button in button_map:
            duration = self._get_time_since_last()
            self.actions.append(
                Action(
                    type=ActionType.HOLD_MOUSE,
                    duration=duration,
                    params={"button": button_map[button].value}
                )
            )

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Handle mouse scroll events - currently not used but included for completeness"""
        logger.debug(f"Mouse scroll at ({x}, {y}): dx={dx}, dy={dy}")

    def _on_key_press(self, key: keyboard.Key) -> None:
        """Handle key press events"""
        # Debug raw key input
        logger.debug(f"Raw key press detected: {key} (type: {type(key)})")
            
        try:
            # Handle different key types
            if isinstance(key, keyboard.KeyCode):
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.lower()
                    logger.debug(f"Character key pressed: {key_str}")
                else:
                    key_str = str(key.vk)
                    logger.debug(f"Virtual key pressed: {key_str}")
            elif isinstance(key, keyboard.Key):
                key_str = key.name.lower()
                logger.debug(f"Special key pressed: {key_str}")
                if key_str in self.special_key_map:
                    key_str = self.special_key_map[key_str]
                    logger.debug(f"Mapped special key to: {key_str}")

            # Check if this is the toggle key press
            if key_str == self.TOGGLE_KEY:
                if not self.is_recording:
                    self.start_recording()
                else:
                    self.stop_recording()
                return

            # Only process other keys if recording
            if not self.is_recording:
                return
                
            # Check if this key is in our mapping
            mapped_key = key_str
            if key_str in self.reverse_key_map:
                mapped_key = self.reverse_key_map[key_str]
                logger.debug(f"Found key in reverse mapping: {key_str} -> {mapped_key}")
            elif key_str in MovementDirection.__members__.values():
                mapped_key = key_str
                logger.debug(f"Key is already a movement direction: {mapped_key}")
            else:
                logger.debug(f"Key not found in mappings: {key_str}")
                return

            self.pressed_keys.add(mapped_key)
            logger.debug(f"Current pressed keys: {self.pressed_keys}")
                
            # For movement keys, create a MOVE action
            if mapped_key in MovementDirection.__members__.values():
                duration = self._get_time_since_last()
                # Check if sprinting
                if "sprint" in self.pressed_keys:
                    action = Action(
                        type=ActionType.SPRINT,
                        duration=duration,
                        params={"direction": mapped_key}
                    )
                    logger.debug(f"Recording sprint action in direction {mapped_key} for {duration:.2f}s")
                    self.actions.append(action)
                else:
                    action = Action(
                        type=ActionType.MOVE,
                        duration=duration,
                        params={"direction": mapped_key}
                    )
                    logger.debug(f"Recording move action in direction {mapped_key} for {duration:.2f}s")
                    self.actions.append(action)
            else:
                # For other keys, create a HOLD_KEY action
                duration = self._get_time_since_last()
                action = Action(
                    type=ActionType.HOLD_KEY,
                    duration=duration,
                    params={"key": mapped_key}
                )
                logger.debug(f"Recording key hold action for key {mapped_key} for {duration:.2f}s")
                self.actions.append(action)
                    
        except Exception as e:
            logger.error(f"Error processing key press: {e}", exc_info=True)
                
            # Check if this key is in our mapping
            mapped_key = key_str
            if key_str in self.reverse_key_map:
                mapped_key = self.reverse_key_map[key_str]
                logger.debug(f"Found key in reverse mapping: {key_str} -> {mapped_key}")
            elif key_str in MovementDirection.__members__.values():
                mapped_key = key_str
                logger.debug(f"Key is already a movement direction: {mapped_key}")
            else:
                logger.debug(f"Key not found in mappings: {key_str}")
                return

            self.pressed_keys.add(mapped_key)
            logger.debug(f"Current pressed keys: {self.pressed_keys}")
                
            # For movement keys, create a MOVE action
            if mapped_key in MovementDirection.__members__.values():
                duration = self._get_time_since_last()
                # Check if sprinting
                if "sprint" in self.pressed_keys:
                    action = Action(
                        type=ActionType.SPRINT,
                        duration=duration,
                        params={"direction": mapped_key}
                    )
                    logger.debug(f"Recording sprint action in direction {mapped_key} for {duration:.2f}s")
                    self.actions.append(action)
                else:
                    action = Action(
                        type=ActionType.MOVE,
                        duration=duration,
                        params={"direction": mapped_key}
                    )
                    logger.debug(f"Recording move action in direction {mapped_key} for {duration:.2f}s")
                    self.actions.append(action)
            else:
                # For other keys, create a HOLD_KEY action
                duration = self._get_time_since_last()
                action = Action(
                    type=ActionType.HOLD_KEY,
                    duration=duration,
                    params={"key": mapped_key}
                )
                logger.debug(f"Recording key hold action for key {mapped_key} for {duration:.2f}s")
                self.actions.append(action)
                    
        except Exception as e:
            logger.error(f"Error processing key press: {e}", exc_info=True)
                
            # Check if this key is in our mapping
            if key_str in self.reverse_key_map:
                mapped_key = self.reverse_key_map[key_str]
                self.pressed_keys.add(mapped_key)
                
                # For movement keys, create a MOVE action
                if mapped_key in MovementDirection.__members__.values():
                    duration = self._get_time_since_last()
                    # Check if sprinting
                    if "sprint" in self.pressed_keys:
                        self.actions.append(
                            Action(
                                type=ActionType.SPRINT,
                                duration=duration,
                                params={"direction": mapped_key}
                            )
                        )
                    else:
                        self.actions.append(
                            Action(
                                type=ActionType.MOVE,
                                duration=duration,
                                params={"direction": mapped_key}
                            )
                        )
                else:
                    # For other keys, create a HOLD_KEY action
                    duration = self._get_time_since_last()
                    action = Action(
                        type=ActionType.HOLD_KEY,
                        duration=duration,
                        params={"key": mapped_key}
                    )
                    logger.debug(f"Recording key hold action for key {mapped_key} for {duration:.2f}s")
                    self.actions.append(action)
                    
        except AttributeError:
            logger.warning(f"Unmapped key pressed: {key}")

    def _on_key_release(self, key: keyboard.Key) -> None:
        """Handle key release events"""
        if self.start_time is None:
            return
            
        # Debug raw key input
        logger.debug(f"Raw key release detected: {key} (type: {type(key)})")
            
        try:
            # Handle different key types
            if isinstance(key, keyboard.KeyCode):
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.lower()
                    logger.debug(f"Character key released: {key_str}")
                else:
                    key_str = str(key.vk)
                    logger.debug(f"Virtual key released: {key_str}")
            elif isinstance(key, keyboard.Key):
                key_str = key.name.lower()
                logger.debug(f"Special key released: {key_str}")
                # Map special keys (like arrow keys) to our format
                if key_str in self.special_key_map:
                    key_str = self.special_key_map[key_str]
                    logger.debug(f"Mapped special key to: {key_str}")

            # Check mappings
            mapped_key = key_str
            if key_str in self.reverse_key_map:
                mapped_key = self.reverse_key_map[key_str]
                logger.debug(f"Found key in reverse mapping: {key_str} -> {mapped_key}")
            elif key_str in MovementDirection.__members__.values():
                mapped_key = key_str
                logger.debug(f"Key is already a movement direction: {mapped_key}")
            else:
                logger.debug(f"Key not found in mappings: {key_str}")
                return

            self.pressed_keys.discard(mapped_key)
            logger.debug(f"Current pressed keys: {self.pressed_keys}")
                    
        except Exception as e:
            logger.error(f"Error processing key release: {e}", exc_info=True)
                
            # Remove from pressed keys if it was mapped
            if key_str in self.reverse_key_map:
                mapped_key = self.reverse_key_map[key_str]
                self.pressed_keys.discard(mapped_key)
                
        except AttributeError:
            logger.warning(f"Unmapped key released: {key}")

    def start_recording(self) -> None:
        """Start recording inputs"""
        logger.info("Starting input recording...")
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.last_mouse_pos = None
        self.pressed_keys.clear()
        self.cumulative_mouse_movement = 0.0
        self.is_recording = True
        print("\nRecording started - press ` again to stop")

    def stop_recording(self) -> None:
        """Stop recording inputs and save routine"""
        if not self.is_recording:
            return
            
        logger.info("Stopping input recording...")
        print("\nRecording stopped")
        
        # Release any held keys
        for key in self.pressed_keys.copy():
            self._on_key_release(keyboard.KeyCode.from_char(key))
            
        self.is_recording = False
        self.start_time = None
        
        # Save routine if any actions were recorded
        if self.actions:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"recorded_routine_{timestamp}"
            routine = self.save_routine(
                name=name,
                description=f"Recorded routine at {timestamp}"
            )
            print(f"\nSaved routine with {len(routine.actions)} actions to routines/{name}.json")

    def save_routine(self, name: str, description: str, directory: str = "routines") -> Routine:
        """Save recorded actions as a routine both in memory and to file"""
        logger.info(f"Saving routine: {name}")
        
        # Clean up any zero-duration actions
        actions = [action for action in self.actions if action.duration > 0]
        
        routine = Routine(
            name=name,
            description=description,
            actions=actions
        )

        # Create routines directory if it doesn't exist
        import os
        os.makedirs(directory, exist_ok=True)
        
        # Save to JSON file
        import json
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/{name}_{timestamp}.json"
        
        # Convert routine to dict, handling Enum values
        routine_dict = json.loads(routine.model_dump_json())
        
        with open(filename, 'w') as f:
            json.dump(routine_dict, f, indent=2)
            
        logger.info(f"Saved routine to {filename}")
        
        return routine

    def discard_recording(self) -> None:
        """Discard current recording"""
        logger.info("Discarding recording...")
        self.actions = []
        self.start_time = None
        self.last_action_time = None
        self.last_mouse_pos = None
        self.pressed_keys.clear()
        self.cumulative_mouse_movement = 0.0


if __name__ == "__main__":
    import logging
    import time

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    recorder = InputRecorder()
    print(f"Press {recorder.TOGGLE_KEY} to start/stop recording")
    print("Press Ctrl+C to save and exit")

    try:
        while True:
            time.sleep(0.1)  # Reduce CPU usage

    except KeyboardInterrupt:
        if recorder.is_recording:
            recorder.stop_recording()
        if recorder.actions:
            routine = recorder.save_routine("test", "test recording")
            print(f"\nRecorded {len(routine.actions)} actions:")
            for action in routine.actions:
                print(f"- {action.type}: {action.params} ({action.duration:.2f}s)")
        else:
            print("\nNo actions recorded")
