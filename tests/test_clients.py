import pytest
import httpx
from unittest.mock import AsyncMock, Mock
from app.clients import stt_client, orchestrator_client, tts_client
from app.exceptions import (
    STTUnavailableError,
    OrchestratorUnavailableError,
    OrchestratorResponseError,
    TTSUnavailableError,
)

@pytest.mark.asyncio
async def test_get_transcription(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {"text": "hola mundo"}
    
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy audio"))
    
    result = await stt_client.get_transcription("fake_path.wav")
    assert result == "hola mundo"
    mock_post.assert_called_once()
    assert "files" in mock_post.call_args[1]
    assert "audio" in mock_post.call_args[1]["files"]

@pytest.mark.asyncio
async def test_get_transcription_failure(mocker):
    mocker.patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection failed"))
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy audio"))
    
    with pytest.raises(STTUnavailableError):
        await stt_client.get_transcription("fake_path.wav")

@pytest.mark.asyncio
async def test_execute_interaction(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {"success": True, "speech": "hola a ti tambien"}
    
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    result = await orchestrator_client.execute_interaction("hola mundo")
    assert result == "hola a ti tambien"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"text": "hola mundo"}

@pytest.mark.asyncio
async def test_execute_interaction_unsuccessful(mocker):
    mock_response = Mock()
    mock_response.json.return_value = {"success": False, "speech": ""}
    
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    with pytest.raises(OrchestratorResponseError):
        await orchestrator_client.execute_interaction("hola mundo")

@pytest.mark.asyncio
async def test_execute_interaction_failure(mocker):
    mocker.patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout"))
    
    with pytest.raises(OrchestratorUnavailableError):
        await orchestrator_client.execute_interaction("hola mundo")

@pytest.mark.asyncio
async def test_synthesize_speech(mocker):
    mock_response = Mock()
    mock_response.content = b"fake audio bytes"
    
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    
    result = await tts_client.synthesize_speech("hola a ti tambien")
    assert result == b"fake audio bytes"
    mock_post.assert_called_once()
    assert mock_post.call_args[1]["json"] == {"msg": "hola a ti tambien"}

@pytest.mark.asyncio
async def test_synthesize_speech_failure(mocker):
    mocker.patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError("Internal Error", request=Mock(), response=Mock()))
    
    with pytest.raises(TTSUnavailableError):
        await tts_client.synthesize_speech("hola a ti tambien")

