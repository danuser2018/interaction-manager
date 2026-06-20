import os
import logging
from app.config import settings
from app.clients import tts_client
from app.exceptions import (
    STTEmptyTranscriptionError,
    STTNullResponseError,
    STTUnavailableError,
    OrchestratorResponseError,
    OrchestratorUnavailableError,
    TTSResponseError,
    TTSUnavailableError,
)

logger = logging.getLogger(__name__)

# Map exceptions to their UX messages and fallback emergency audio files
ERROR_MAPPING = {
    STTEmptyTranscriptionError: (
        "No he entendido lo que has dicho.",
        "stt_not_understood.wav"
    ),
    STTNullResponseError: (
        "No he podido procesar el audio.",
        "operation_failed.wav"
    ),
    STTUnavailableError: (
        "El servicio de reconocimiento de voz no está disponible.",
        "stt_unavailable.wav"
    ),
    OrchestratorResponseError: (
        "No he podido completar la operación.",
        "operation_failed.wav"
    ),
    OrchestratorUnavailableError: (
        "No he podido completar la operación.",
        "service_unavailable.wav"
    ),
    TTSResponseError: (
        "Ha ocurrido un error al generar la respuesta.",
        "fatal_error.wav"
    ),
    TTSUnavailableError: (
        "Ha ocurrido un error al generar la respuesta.",
        "fatal_error.wav"
    ),
}

async def handle_error(error: Exception) -> bytes:
    """
    Translates an exception to a UX message, attempts TTS synthesis if possible,
    and falls back to pre-recorded emergency audio if TTS fails or is unavailable.
    """
    logger.info(f"Handling error: {error} ({type(error).__name__})")
    
    # Translate exception to UX message and emergency filename
    ux_message = "Ha ocurrido un error interno."
    emergency_filename = "fatal_error.wav"
    
    for exc_class, (msg, filename) in ERROR_MAPPING.items():
        if isinstance(error, exc_class):
            ux_message = msg
            emergency_filename = filename
            break
            
    logger.debug(f"Translated to UX message: '{ux_message}', fallback audio: '{emergency_filename}'")
    
    # Try TTS synthesis unless the error is TTS-related
    if not isinstance(error, (TTSResponseError, TTSUnavailableError)):
        try:
            logger.info(f"Attempting to synthesize error UX message via TTS: '{ux_message}'")
            audio_bytes = await tts_client.synthesize_speech(ux_message)
            if audio_bytes:
                logger.info("Successfully synthesized error UX message via TTS.")
                return audio_bytes
        except Exception as tts_exc:
            logger.warning(f"Failed to synthesize error UX message via TTS: {tts_exc}. Falling back to emergency audio.")
    else:
        logger.info("Error is TTS-related. Bypassing TTS synthesis and using emergency audio directly.")

    # Fallback to emergency audio
    emergency_path = os.path.join(settings.EMERGENCY_AUDIO_DIR, emergency_filename)
    try:
        logger.info(f"Loading emergency audio from: {emergency_path}")
        with open(emergency_path, "rb") as f:
            return f.read()
    except Exception as read_exc:
        logger.error(f"Failed to read emergency audio file at {emergency_path}: {read_exc}")
        return b""
