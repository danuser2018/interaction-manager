import pytest

@pytest.fixture(autouse=True)
def mock_security_authorize(request, mocker):
    if "unmock_security" in request.fixturenames:
        return None

    async def fake_authorize(plan, default_channel="voice"):
        steps = plan.get("steps", [])
        tokens = []
        for step in steps:
            if "security" not in step or not isinstance(step["security"], dict):
                step["security"] = {}
            step["security"]["authorization_token"] = "fake-valid-token"
            tokens.append({"action_id": step.get("plugin"), "token": "fake-valid-token"})
        return {"decision": "ALLOW", "authorization_tokens": tokens}

    return mocker.patch("app.clients.security_client.authorize_plan", side_effect=fake_authorize)

@pytest.fixture
def unmock_security():
    pass
