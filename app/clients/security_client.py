import httpx
import logging
from app.config import settings
from app.exceptions import AuthorizationDeniedError, SecurityUnavailableError

logger = logging.getLogger(__name__)

async def authorize_plan(plan: dict, default_channel: str = "voice") -> dict:
    """
    Submits an ExecutionPlan to security-service for authorization.
    POST /v1/security/authorize
    Attaches authorization_token to step.security on ALLOW.
    Raises AuthorizationDeniedError on DENY.
    Raises SecurityUnavailableError on connection failure/timeout.
    """
    url = f"{settings.SECURITY_SERVICE_BASE_URL.rstrip('/')}/v1/security/authorize"
    steps = plan.get("steps", [])
    if not steps:
        logger.warning("Empty execution plan steps provided for authorization.")
        return {"decision": "ALLOW", "authorization_tokens": []}

    first_step = steps[0]
    execution_id = (
        first_step.get("context", {}).get("correlation_id")
        or first_step.get("correlation_id")
        or "unknown-execution-id"
    )
    channel = (
        first_step.get("channel")
        or first_step.get("context", {}).get("channel")
        or default_channel
    )

    actions = []
    for step in steps:
        actions.append({
            "action_id": step.get("plugin"),
            "parameters": step.get("parameters", {})
        })

    payload = {
        "execution_plan": {
            "execution_id": execution_id,
            "actions": actions
        },
        "security_context": {
            "channel": channel
        }
    }

    logger.info(f"Submitting authorization request to security-service at {url} for execution_id={execution_id}, channel={channel}")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Security service HTTP error: {e}")
        raise SecurityUnavailableError(f"Security service HTTP error: {e}") from e
    except httpx.RequestError as e:
        logger.error(f"Security service request failed: {e}")
        raise SecurityUnavailableError(f"Security service unavailable: {e}") from e

    decision = data.get("decision")
    if decision == "DENY":
        reason = data.get("reason", "Authorization denied by security policy.")
        logger.warning(f"Plan authorization DENIED: {reason}")
        raise AuthorizationDeniedError(reason)

    tokens = data.get("authorization_tokens") or []
    token_map = {t["action_id"]: t["token"] for t in tokens if "action_id" in t and "token" in t}
    for step in steps:
        action_id = step.get("plugin")
        if action_id in token_map:
            if "security" not in step or not isinstance(step["security"], dict):
                step["security"] = {}
            step["security"]["authorization_token"] = token_map[action_id]

    return data
