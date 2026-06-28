import os
import shutil
import logging
import asyncio
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.config import settings
from app.services import interaction_pipeline, error_handler

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
        start_time = time.perf_counter()
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
            elapsed = time.perf_counter() - start_time
            logger.error(f"Failed to move file to processing after {elapsed:.3f} seconds: {e}")
            # Generar audio de error para comunicación al usuario (RF-003, RF-004)
            try:
                logger.info(f"Generating error audio for failed move of {filename}")
                error_audio = await error_handler.handle_error(e)
                if error_audio:
                    with open(output_path, "wb") as f:
                        f.write(error_audio)
                    logger.info(f"Saved error output to {output_path} after initial move failure")
                else:
                    logger.warning("No error audio generated after initial move failure.")
            except Exception as handler_e:
                logger.error(f"Failed to generate and save error audio for move failure: {handler_e}")
            return

        feedback_output_path = os.path.join(settings.OUTPUT_DIR, f"interaction_{filename}")
        feedback_copied = False

        try:
            try:
                if os.path.exists(settings.INTERACTION_AUDIO_FILE):
                    await asyncio.to_thread(shutil.copy, settings.INTERACTION_AUDIO_FILE, feedback_output_path)
                    logger.info("Inicio de reproducción interaction.wav")
                    feedback_copied = True
                else:
                    logger.warning(f"Interaction audio file not found at {settings.INTERACTION_AUDIO_FILE}. Skipping audio feedback.")
            except Exception as copy_e:
                logger.error(f"Failed to copy interaction audio feedback: {copy_e}. Skipping audio feedback.")

            # Ejecutar el pipeline (pasos 3 al 8)
            audio_bytes = await interaction_pipeline.process_interaction(processing_path)

            if feedback_copied:
                logger.info("Fin de reproducción interaction.wav")
                try:
                    os.remove(feedback_output_path)
                except FileNotFoundError:
                    pass
                except Exception as remove_e:
                    logger.error(f"Failed to remove temporary feedback file {feedback_output_path}: {remove_e}")

            # 9. Almacenar en /data/output
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Successfully processed and saved output to {output_path} in {elapsed:.3f} seconds")

            # 10. Eliminar archivo de processing
            os.remove(processing_path)
            logger.debug(f"Removed original file from {processing_path}")

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Error processing {filename} after {elapsed:.3f} seconds: {e}", exc_info=True)

            if feedback_copied:
                logger.info("Fin de reproducción interaction.wav")
                try:
                    os.remove(feedback_output_path)
                except FileNotFoundError:
                    pass
                except Exception as remove_e:
                    logger.error(f"Failed to remove temporary feedback file {feedback_output_path}: {remove_e}")

            # En caso de error, mover a /data/error
            try:
                if os.path.exists(processing_path):
                    shutil.move(processing_path, error_path)
                    logger.info(f"Moved failed file to {error_path}")
            except Exception as move_e:
                logger.error(f"Failed to move file to error directory: {move_e}")

            # Generar audio de error para comunicación al usuario (RF-003, RF-004)
            try:
                logger.info(f"Generating error audio for {filename}")
                error_audio = await error_handler.handle_error(e)
                if error_audio:
                    with open(output_path, "wb") as f:
                        f.write(error_audio)
                    logger.info(f"Saved error output to {output_path}")
                else:
                    logger.warning("No error audio generated.")
            except Exception as handler_e:
                logger.error(f"Failed to generate and save error audio: {handler_e}")


def start_watcher(loop):
    event_handler = AudioFileHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, path=settings.INPUT_DIR, recursive=False)
    observer.start()
    logger.info(f"Started watching {settings.INPUT_DIR} for new .wav files")
    return observer
