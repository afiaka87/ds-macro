# main.py
import asyncio
import logging
import argparse
from ds_macro.controller import DSController
from ds_macro.routines import AVAILABLE_ROUTINES, run_routine
from ds_macro.models import KeyMapping, MovementDirection, RoutineCategory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a handler for the latest log line
latest_handler = logging.FileHandler("current_log.txt", mode="w")
latest_handler.setLevel(logging.INFO)
latest_handler.setFormatter(
    logging.Formatter("%(message)s")
)  # Only include the message

# Add the handler to the root logger
logging.root.addHandler(latest_handler)

logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(
        description="DS-Macro: Control Death Stranding with macros"
    )
    parser.add_argument(
        "--routine",
        choices=list(AVAILABLE_ROUTINES.keys()),
        help="Run a predefined routine",
    )
    parser.add_argument(
        "--delay", type=float, default=3.0, help="Delay in seconds before starting"
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Run a custom example instead of a predefined routine",
    )

    args = parser.parse_args()

    # Initialize controller
    ds = DSController()

    logger.info(f"Starting Death Stranding controller in {args.delay} seconds...")
    await asyncio.sleep(args.delay)

    try:
        if args.custom:
            await run_custom_example(ds)
        elif args.routine:
            await run_routine(ds, args.routine)
        else:
            # Default to patrol routine
            await run_routine(ds, "patrol")

    except Exception as e:
        logger.error(f"Controller error: {e}")
        # Emergency stop to release all keys
        await ds.emergency_stop()
        raise


async def run_custom_example(ds: DSController):
    """Run a custom example showcasing multiple features"""
    logger.info("Running custom example with multiple routines")

    # Start a scanning routine that runs in the background
    scan_routine = ds.create_routine(
        name="background_scan",
        categories=[RoutineCategory.SCANNING, RoutineCategory.ESSENTIAL],
    )

    with scan_routine.sequential_actions() as actions:
        actions.press("scan")

    # Start the scan in the background
    scan_task = asyncio.create_task(scan_routine.run())

    # Create a movement routine
    movement = ds.create_routine(
        name="move_forward", categories=[RoutineCategory.MOVEMENT]
    )

    with movement.sequential_actions() as actions:
        actions.press(MovementDirection.FORWARD)
        actions.press("sprint")
        actions.wait(5.0)
        actions.release("sprint")
        actions.release(MovementDirection.FORWARD)

    # Run the movement routine
    await movement.run()

    # Cancel the scanning routine by category
    ds.cancel_category(RoutineCategory.SCANNING)

    # Create a new routine to finish up
    finish = ds.create_routine(name="finish")

    with finish.sequential_actions() as actions:
        actions.turn(180, 2.0)
        actions.tap("like", 0.2)

    await finish.run()

    # Make sure all routines are stopped
    await ds.emergency_stop()

    logger.info("Custom example completed")


if __name__ == "__main__":
    asyncio.run(main())
