import pytest
from app.clients import security_client
from app.exceptions import AuthorizationDeniedError, SecurityUnavailableError

@pytest.mark.asyncio
async def test_security_client_authorize_allow(mocker, unmock_security):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "decision": "ALLOW",
        "authorization_tokens": [
            {"action_id": "set-volume", "token": "token-123"}
        ]
    }
    mock_post = mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

    plan = {
        "steps": [
            {
                "plugin": "set-volume",
                "parameters": {"volume": 50},
                "channel": "voice",
                "context": {"correlation_id": "exec-001"}
            }
        ]
    }

    res = await security_client.authorize_plan(plan, default_channel="voice")
    assert res["decision"] == "ALLOW"
    assert plan["steps"][0]["security"]["authorization_token"] == "token-123"

@pytest.mark.asyncio
async def test_security_client_authorize_deny(mocker, unmock_security):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "decision": "DENY",
        "reason": "Risk level exceeds channel limit"
    }
    mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

    plan = {
        "steps": [
            {
                "plugin": "format-disk",
                "parameters": {},
                "channel": "cli",
                "context": {"correlation_id": "exec-002"}
            }
        ]
    }

    with pytest.raises(AuthorizationDeniedError) as exc_info:
        await security_client.authorize_plan(plan, default_channel="cli")
    assert "Risk level exceeds channel limit" in str(exc_info.value)
