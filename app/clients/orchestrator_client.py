import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def execute_interaction(text: str) -> str:
    """
    Sends the transcribed text to the Orchestrator and returns the response speech.
    Expected request: {"text": "qué tiempo hace hoy"}
    Expected response: {"success": true, "speech": "Actualmente hace 22 grados"}
    """
    url = f"{settings.ORCHESTRATOR_BASE_URL}/api/v1/execute"
    logger.info(f"Sending text to Orchestrator ({url}): {text}")
    
    async with httpx.AsyncClient() as client:
        payload = {"text": text}
        response = await client.post(url, json=payload)
        
        response.raise_for_status()
        result = response.json()
        if not result.get("success"):
            logger.warning(f"Orchestrator returned unsuccessful response: {result}")
        return result.get("speech", "")
