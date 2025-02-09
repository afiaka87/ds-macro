# main.py
import logging
import time
from controller import DSController
from routines import AVAILABLE_ROUTINES

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    ds = DSController()
    logger = logging.getLogger(__name__)

    logger.info("Starting Death Stranding controller in 3 seconds...")
    time.sleep(3)

    try:
        # Execute a patrol routine
        routine = AVAILABLE_ROUTINES["patrol"]
        ds.execute_routine(routine)

    except Exception as e:
        logger.error(f"Controller error: {e}")
        raise


if __name__ == "__main__":
    main()
