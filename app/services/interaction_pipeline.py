import logging
from app.clients import stt_client, orchestrator_client, tts_client
from app.exceptions import (
    STTNullResponseError,
    STTEmptyTranscriptionError,
    OrchestratorResponseError,
    TTSResponseError,
)

logger = logging.getLogger(__name__)

async def process_interaction(audio_file_path: str) -> bytes:
    """
    Executes the full interaction pipeline:
    1. STT: audio to text
    2. Orchestrator: text to response
    3. TTS: response to audio bytes
    """
    logger.info(f"Starting interaction pipeline for: {audio_file_path}")
    
    # 1. Speech-to-Text
    transcription = await stt_client.get_transcription(audio_file_path)
    if transcription is None:
        raise STTNullResponseError("STT service returned null transcription.")
    if transcription == "":
        raise STTEmptyTranscriptionError("STT service returned empty transcription.")
    logger.info(f"Transcription received: {transcription}")
    
    # 2. Orchestrator
    response_text = await orchestrator_client.execute_interaction(transcription)
    if not response_text:
        raise OrchestratorResponseError("Orchestrator returned an empty response.")
    logger.info(f"Orchestrator response received: {response_text}")
    
    # 3. Text-to-Speech
    audio_bytes = await tts_client.synthesize_speech(response_text)
    if not audio_bytes:
        raise TTSResponseError("TTS service returned empty audio.")
    logger.info("TTS audio synthesized successfully.")
    
    return audio_bytes

