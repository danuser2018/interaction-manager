import os
import shutil
import logging
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.config import settings
from app.services import interaction_pipeline

logger = logging.getLogger(__name__)

class AudioFileHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".wav"):
            return
        
        # Schedule the processing task in the asyncio loop
        asyncio.run_coroutine_threadsafe(
            self.handle_new_file(event.src_path), self.loop
        )

    async def handle_new_file(self, file_path: str):
        filename = os.path.basename(file_path)
        processing_path = os.path.join(settings.PROCESSING_DIR, filename)
        output_path = os.path.join(settings.OUTPUT_DIR, filename)
        error_path = os.path.join(settings.ERROR_DIR, filename)

        logger.info(f"New file detected: {file_path}")

        try:
            # 2. Mover a /data/processing
            shutil.move(file_path, processing_path)
            logger.debug(f"Moved {file_path} to {processing_path}")
        except Exception as e:
            logger.error(f"Failed to move file to processing: {e}")
            return

        try:
            # Ejecutar el pipeline (pasos 3 al 8)
            audio_bytes = await interaction_pipeline.process_interaction(processing_path)

            # 9. Almacenar en /data/output
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"Successfully processed and saved output to {output_path}")

            # 10. Eliminar archivo de processing
            os.remove(processing_path)
            logger.debug(f"Removed original file from {processing_path}")

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)
            # En caso de error, mover a /data/error
            try:
                if os.path.exists(processing_path):
                    shutil.move(processing_path, error_path)
                    logger.info(f"Moved failed file to {error_path}")
            except Exception as move_e:
                logger.error(f"Failed to move file to error directory: {move_e}")

def start_watcher(loop):
    event_handler = AudioFileHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path=settings.INPUT_DIR, recursive=False)
    observer.start()
    logger.info(f"Started watching {settings.INPUT_DIR} for new .wav files")
    return observer
