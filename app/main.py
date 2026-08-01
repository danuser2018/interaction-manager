import os
import sys
import asyncio
import logging
from nova_event_bus import NatsEventBus, EventBusConfig
from app.config import settings
from app.services.event_subscriber import InteractionEventSubscriber


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
    logger.info("Starting Interaction Manager (Event-Driven Mode)")

    ensure_directories()

    event_bus = NatsEventBus(config=EventBusConfig(nats_url=settings.NATS_URL))
    subscriber = InteractionEventSubscriber(event_bus)

    await subscriber.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping Interaction Manager...")
    finally:
        await subscriber.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
