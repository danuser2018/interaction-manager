import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def get_transcription(audio_file_path: str) -> str:
    """
    Sends the audio file to the STT service and returns the transcribed text.
    Expected response: {"text": "qué tiempo hace hoy"}
    """
    url = f"{settings.STT_BASE_URL}/v1/transcriptions"
    logger.info(f"Sending {audio_file_path} to STT Service ({url})")
    
    async with httpx.AsyncClient() as client:
        with open(audio_file_path, "rb") as f:
            files = {"audio": (audio_file_path, f, "audio/wav")}
            data = {"language": settings.DEFAULT_LANGUAGE}
            response = await client.post(url, files=files, data=data)
            
        response.raise_for_status()
        result = response.json()
        return result.get("text", "")
