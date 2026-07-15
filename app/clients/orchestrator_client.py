import httpx
import logging
from app.config import settings
from app.exceptions import OrchestratorUnavailableError, OrchestratorResponseError

logger = logging.getLogger(__name__)

async def resolve_intent(text: str) -> dict:
    """
    Sends the user query text to the Orchestrator resolve endpoint.
    POST /api/v1/resolve
    Request payload: {"text": text}
    Returns: ExecutionPlan JSON structure (dict)
    Raises:
        OrchestratorUnavailableError: If connection/timeout issues occur.
        OrchestratorResponseError: If server responds with HTTP errors (e.g. 422).
    """
    url = f"{settings.ORCHESTRATOR_BASE_URL}/api/v1/resolve"
    logger.info(f"Sending intent to Orchestrator resolve endpoint ({url}): {text}")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {"text": text}
            response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Orchestrator resolve HTTP error: {e}")
        raise OrchestratorResponseError(f"Orchestrator resolve HTTP error: {e}") from e
    except httpx.RequestError as e:
        logger.error(f"Orchestrator resolve request failed: {e}")
        raise OrchestratorUnavailableError(f"Orchestrator resolve service is unavailable: {e}") from e


async def execute_plan(plan: dict) -> str:
    """
    Sends the ExecutionPlan JSON structure to the Orchestrator execute-plan endpoint.
    POST /api/v1/execute-plan
    Request payload: plan (ExecutionPlan schema)
    Returns: The response speech string.
    Raises:
        OrchestratorUnavailableError: If connection/timeout issues occur.
        OrchestratorResponseError: If server responds with HTTP errors (e.g. 400, 422)
                                   or if the returned 'success' field is False.
    """
    url = f"{settings.ORCHESTRATOR_BASE_URL}/api/v1/execute-plan"
    logger.info(f"Sending execution plan to Orchestrator execute-plan endpoint ({url})")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=plan)
        response.raise_for_status()
        result = response.json()
        if not result.get("success"):
            logger.warning(f"Orchestrator returned unsuccessful response: {result}")
            raise OrchestratorResponseError(f"Orchestrator returned unsuccessful response: {result}")
        return result.get("speech")
    except httpx.HTTPStatusError as e:
        logger.error(f"Orchestrator execute-plan HTTP error: {e}")
        raise OrchestratorResponseError(f"Orchestrator execute-plan HTTP error: {e}") from e
    except httpx.RequestError as e:
        logger.error(f"Orchestrator execute-plan request failed: {e}")
        raise OrchestratorUnavailableError(f"Orchestrator execute-plan service is unavailable: {e}") from e

