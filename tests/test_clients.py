import pytest
from unittest.mock import AsyncMock, patch
from app.clients import stt_client, orchestrator_client, tts_client

@pytest.mark.asyncio
async def test_get_transcription(mocker):
    # Mock httpx.AsyncClient
    mock_post = AsyncMock()
    mock_post.return_value.json.return_value = {"text": "hola mundo"}
    mock_post.return_value.raise_for_status = AsyncMock()

    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    # Mock file open
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy audio"))
    
    result = await stt_client.get_transcription("fake_path.wav")
    assert result == "hola mundo"
    mock_post.assert_called_once()
    assert "files" in mock_post.call_args[1]
    assert "audio" in mock_post.call_args[1]["files"]

@pytest.mark.asyncio
async def test_execute_interaction(mocker):
    mock_post = AsyncMock()
    mock_post.return_value.json.return_value = {"success": True, "speech": "hola a ti tambien"}
    mock_post.return_value.raise_for_status = AsyncMock()

    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    result = await orchestrator_client.execute_interaction("hola mundo")
    assert result == "hola a ti tambien"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"text": "hola mundo"}

@pytest.mark.asyncio
async def test_synthesize_speech(mocker):
    mock_post = AsyncMock()
    mock_post.return_value.content = b"fake audio bytes"
    mock_post.return_value.raise_for_status = AsyncMock()

    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    result = await tts_client.synthesize_speech("hola a ti tambien")
    assert result == b"fake audio bytes"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"msg": "hola a ti tambien"}
