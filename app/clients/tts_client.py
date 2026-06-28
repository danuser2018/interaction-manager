import httpx
import logging
from app.config import settings
from app.exceptions import TTSUnavailableError

logger = logging.getLogger(__name__)

async def synthesize_speech(text: str) -> bytes:
    """
    Sends the text to the TTS service and returns the resulting WAV audio bytes.
    Expected request: {"msg": "Actualmente hace 22 grados"}
    Expected response: audio/wav
    """
    url = f"{settings.TTS_BASE_URL}/v1/synthesize"
    logger.info(f"Sending text to TTS Service ({url})")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {"msg": text}
            response = await client.post(url, json=payload)
            
        response.raise_for_status()
        return response.content
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"TTS Service request failed: {e}")
        raise TTSUnavailableError(f"TTS service is unavailable: {e}") from e

