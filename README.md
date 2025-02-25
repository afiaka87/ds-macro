# DS-Macro

DS-Macro is a Python library for automating input sequences in games. It defines and executes keyboard and mouse actions with timing control.

- **Parallel & Sequential Actions**: Run actions simultaneously or in sequence
- **Flexible Control**: Start, stop, and manage actions from anywhere in your code
- **Registry System**: Global action tracking for cancelling routines from anywhere

## Quick Start

```python
import asyncio
from ds_macro import DSController, MovementDirection, MouseButton

# Create a controller instance
controller = DSController()

# Define a simple patrol routine
async def patrol():
    routine = controller.create_routine(name="patrol", categories=["movement"])
    
    # Move forward while scanning (parallel actions)
    with routine.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("sprint")
        actions.press("scan")
        actions.turn(360, 5.0)  # Turn 360 degrees over 5 seconds
    
    # Stop all actions (sequential)
    with routine.sequential_actions() as actions:
        actions.release("scan")
        actions.release("sprint") 
        actions.release(MovementDirection.FORWARD)
    
    # Run the routine
    await routine.run()

# Run the patrol
asyncio.run(patrol())
```

## Core Concepts

### Controller

The `DSController` class is the main entry point for creating and executing input actions:

```python
from ds_macro import DSController

controller = DSController()
```

### Routines

Routines are sequences of action groups that can be executed together:

```python
# Create a routine with optional name and categories
routine = controller.create_routine(
    name="combat_sequence", 
    categories=["combat", "aggressive"]
)

# Execute the routine
await routine.run()
```

### Action Groups

Actions can be grouped to run in parallel or sequence:

```python
# Sequential actions (one after another)
with routine.sequential_actions() as actions:
    actions.press("w")
    actions.wait(1.0)
    actions.release("w")

# Parallel actions (all at once)
with routine.parallel_actions() as actions:
    actions.press("shift")
    actions.press("w")
```

### Available Actions

DS-Macro supports a wide range of input actions:

```python
# Keyboard actions
actions.press("w")                   # Press and hold a key
actions.release("w")                 # Release a held key
actions.tap("e", duration=0.1)       # Press and release a key

# Mouse actions
actions.mouse_move(dx=100, dy=0)     # Move mouse horizontally
actions.mouse_press(MouseButton.LEFT) # Press a mouse button
actions.mouse_release(MouseButton.LEFT) # Release a mouse button
actions.mouse_click(MouseButton.LEFT) # Click a mouse button

# Timing and camera
actions.wait(1.5)                    # Wait for duration
actions.turn(90, duration=1.0)       # Turn camera 90 degrees
```

## Managing Actions

DS-Macro provides robust tools for managing active routines:

### Stopping Specific Routines

```python
# Cancel a specific routine by ID
routine_id = controller.create_routine(name="patrol").id
# ...later
controller.cancel_by_id(routine_id)

# Cancel routines by name
controller.cancel_by_name("patrol")
```

### Category-based Management

```python
# Cancel all movement-related routines
controller.cancel_category("movement")

# Stop everything except essential routines
controller.cancel_all_except(categories=["essential"])

# Emergency stop (cancel all routines and release all inputs)
await controller.emergency_stop()
```

This global registry system allows you to manage routines from anywhere in your code without needing to maintain references to specific routine instances. Categories provide a flexible way to organize related actions and manage them as a group.

## Predefined Categories

DS-Macro provides constants for common routine categories:

```python
from ds_macro import RoutineCategory

routine = controller.create_routine(
    name="combat_move",
    categories=[RoutineCategory.MOVEMENT, RoutineCategory.COMBAT]
)
```

## Alternative: Action Models

For more structured code, you can define actions using Pydantic models:

```python
from ds_macro import KeyPress, KeyRelease, Wait, Turn

# Define a list of actions
actions = [
    KeyPress(key=MovementDirection.FORWARD),
    KeyPress(key="sprint"),
    Wait(duration=2.0),
    Turn(degrees=90, duration=1.0),
    KeyRelease(key="sprint"),
    KeyRelease(key=MovementDirection.FORWARD)
]

# Add to routine
routine.add_actions(actions, parallel=False)
```

## Helper Libraries

Create reusable action libraries for common patterns:

```python
class MovementPatterns:
    @staticmethod
    def sprint_forward(duration):
        return [
            KeyPress(key=MovementDirection.FORWARD),
            KeyPress(key="sprint"),
            Wait(duration=duration),
            KeyRelease(key="sprint"),
            KeyRelease(key=MovementDirection.FORWARD)
        ]

# Use the library
routine.add_actions(MovementPatterns.sprint_forward(3.0))
```

## Non-blocking Execution

Run routines without blocking your main code:

```python
# Start a routine in the background
patrol_id = controller.create_routine(name="patrol").id
asyncio.create_task(controller.run_routine_by_id(patrol_id))

# Do other things while patrol runs
await some_other_function()

# Stop the patrol when done
controller.cancel_by_id(patrol_id)
```

## Advanced: Running Multiple Routines

```python
async def run_complex_mission():
    # Start background patrol
    patrol = controller.create_routine(name="patrol", categories=["movement"])
    with patrol.parallel_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("sprint")
    patrol_task = asyncio.create_task(patrol.run())
    
    # Periodically scan while moving
    for _ in range(5):
        scan = controller.create_routine(name="scan", categories=["scanning"])
        with scan.sequential_actions() as actions:
            actions.press("scan")
            actions.turn(90, 1.0)
            actions.release("scan")
        await scan.run()
        await asyncio.sleep(2.0)
    
    # Stop patrolling
    controller.cancel_category("movement")  # Cancel by category instead of task
    
    # Or use the emergency stop if needed
    # await controller.emergency_stop()

asyncio.run(run_complex_mission())
```

This example demonstrates how to use the category system to manage multiple routines running in parallel, which is especially useful in complex gaming scenarios.

## License

MIT

## Disclaimer

This project is largely generated by Claude Sonnet 3.5 and 3.7.