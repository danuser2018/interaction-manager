import os
import shutil
import logging
import asyncio
import time
from nova_event_bus import EventBus
from app.config import settings
from app.events import SpeechCapturedEvent, ExecuteShortcutCommand
from app.services import interaction_pipeline, error_handler

logger = logging.getLogger(__name__)


class InteractionEventSubscriber:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def start(self) -> None:
        await self._event_bus.connect()
        await self._event_bus.subscribe(SpeechCapturedEvent, self._handle_speech_captured)
        await self._event_bus.subscribe(ExecuteShortcutCommand, self._handle_execute_shortcut)
        logger.info("InteractionEventSubscriber successfully subscribed to events and shortcut commands")

    async def stop(self) -> None:
        await self._event_bus.disconnect()
        logger.info("InteractionEventSubscriber disconnected from NATS broker")


    async def _handle_speech_captured(self, evt: SpeechCapturedEvent) -> None:
        logger.info(
            f"Received SpeechCapturedEvent: correlation_id={evt.correlation_id}, "
            f"channel={evt.channel}, audio_path={evt.audio_path}"
        )

        resolved_path = os.path.normpath(os.path.join(settings.INPUT_DIR, evt.audio_path))

        if not resolved_path.startswith(os.path.abspath(settings.INPUT_DIR)):
            logger.error(f"Path traversal detected for audio_path: {evt.audio_path}")
            return

        if not os.path.exists(resolved_path):
            filename = os.path.basename(resolved_path)
            in_processing = os.path.exists(os.path.join(settings.PROCESSING_DIR, filename))
            in_output = os.path.exists(os.path.join(settings.OUTPUT_DIR, filename))
            in_error = os.path.exists(os.path.join(settings.ERROR_DIR, filename))

            if in_processing or in_output or in_error:
                logger.warning(
                    f"Duplicate SpeechCapturedEvent received for audio_path: {evt.audio_path}. "
                    "File has already been moved or processed."
                )
                return

            logger.error(f"Audio file not found at resolved path: {resolved_path}")
            await error_handler.handle_error(FileNotFoundError(f"File missing: {resolved_path}"))
            return

        try:
            await self._process_audio_file(resolved_path)
        except Exception as e:
            logger.error(f"Error processing audio file {resolved_path}: {e}", exc_info=True)
            await error_handler.handle_error(e)

    async def _process_audio_file(self, file_path: str) -> None:
        start_time = time.perf_counter()
        filename = os.path.basename(file_path)
        processing_path = os.path.join(settings.PROCESSING_DIR, filename)
        output_path = os.path.join(settings.OUTPUT_DIR, filename)
        error_path = os.path.join(settings.ERROR_DIR, filename)

        logger.info(f"Processing audio file: {file_path}")

        try:
            shutil.move(file_path, processing_path)
            logger.debug(f"Moved {file_path} to {processing_path}")
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Failed to move file to processing after {elapsed:.3f}s: {e}")
            await self._handle_processing_error(e, filename, output_path)
            return

        feedback_output_path = os.path.join(settings.OUTPUT_DIR, f"interaction_{filename}")
        feedback_copied = False

        try:
            if os.path.exists(settings.INTERACTION_AUDIO_FILE):
                await asyncio.to_thread(shutil.copy, settings.INTERACTION_AUDIO_FILE, feedback_output_path)
                logger.info("Started playing interaction feedback audio")
                feedback_copied = True

            audio_bytes = await interaction_pipeline.process_interaction(processing_path)

            if feedback_copied:
                self._remove_file_silent(feedback_output_path)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            elapsed = time.perf_counter() - start_time
            logger.info(f"Successfully processed interaction and saved to {output_path} in {elapsed:.3f}s")

            self._remove_file_silent(processing_path)

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Error executing interaction pipeline for {filename} after {elapsed:.3f}s: {e}", exc_info=True)

            if feedback_copied:
                self._remove_file_silent(feedback_output_path)

            if os.path.exists(processing_path):
                try:
                    shutil.move(processing_path, error_path)
                    logger.info(f"Moved failed file to {error_path}")
                except Exception as move_e:
                    logger.error(f"Failed to move file to error directory: {move_e}")

            await self._handle_processing_error(e, filename, output_path)

    async def _handle_processing_error(self, error: Exception, filename: str, output_path: str) -> None:
        try:
            error_audio = await error_handler.handle_error(error)
            if error_audio:
                with open(output_path, "wb") as f:
                    f.write(error_audio)
                logger.info(f"Saved error response audio to {output_path}")
        except Exception as handler_e:
            logger.error(f"Failed to generate and save error audio for {filename}: {handler_e}")

    def _remove_file_silent(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to remove file {path}: {e}")

    async def _handle_execute_shortcut(self, cmd: ExecuteShortcutCommand) -> None:
        logger.info(
            f"Received ExecuteShortcutCommand: correlation_id={cmd.correlation_id}, "
            f"shortcut={cmd.shortcut}, channel={cmd.channel}"
        )
        output_filename = f"shortcut_{cmd.correlation_id}.wav"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

        feedback_output_path = os.path.join(settings.OUTPUT_DIR, f"interaction_{output_filename}")
        feedback_copied = False

        try:
            if os.path.exists(settings.INTERACTION_AUDIO_FILE):
                await asyncio.to_thread(shutil.copy, settings.INTERACTION_AUDIO_FILE, feedback_output_path)
                logger.info("Started playing interaction feedback audio for shortcut")
                feedback_copied = True

            audio_bytes = await interaction_pipeline.process_shortcut_interaction(
                shortcut=cmd.shortcut,
                channel=cmd.channel,
                correlation_id=cmd.correlation_id,
            )

            if feedback_copied:
                self._remove_file_silent(feedback_output_path)

            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Successfully processed shortcut '{cmd.shortcut}' and saved response to {output_path}")

        except Exception as e:
            logger.error(
                f"Error executing shortcut '{cmd.shortcut}' [correlation_id={cmd.correlation_id}]: {e}",
                exc_info=True,
            )

            if feedback_copied:
                self._remove_file_silent(feedback_output_path)

            await self._handle_processing_error(e, output_filename, output_path)

