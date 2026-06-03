import os
import sys
import time
import asyncio
import logging
from app.config import settings
from app.services import file_watcher

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def ensure_directories():
    directories = [
        settings.INPUT_DIR,
        settings.PROCESSING_DIR,
        settings.OUTPUT_DIR,
        settings.ERROR_DIR
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logging.getLogger(__name__).debug(f"Ensured directory exists: {directory}")

async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Interaction Manager")

    ensure_directories()

    loop = asyncio.get_running_loop()
    observer = file_watcher.start_watcher(loop)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Interaction Manager")
        observer.stop()
    finally:
        observer.join()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
