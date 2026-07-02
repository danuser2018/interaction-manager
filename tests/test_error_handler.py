import pytest
from unittest.mock import AsyncMock, patch, mock_open
from app.services import error_handler
from app.exceptions import (
    STTEmptyTranscriptionError,
    STTNullResponseError,
    STTUnavailableError,
    OrchestratorResponseError,
    OrchestratorUnavailableError,
    TTSResponseError,
    TTSUnavailableError,
)

@pytest.mark.asyncio
async def test_handle_error_stt_empty_tts_success(mocker):
    mock_tts = mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"synthesized empty stt")
    
    result = await error_handler.handle_error(STTEmptyTranscriptionError("empty"))
    
    assert result == b"synthesized empty stt"
    mock_tts.assert_called_once_with("No he entendido lo que has dicho.")

@pytest.mark.asyncio
async def test_handle_error_stt_empty_tts_failure(mocker):
    mock_tts = mocker.patch("app.clients.tts_client.synthesize_speech", side_effect=Exception("TTS failed"))
    opened_path = []
    
    def my_open(path, mode):
        opened_path.append(path)
        return mock_open(read_data=b"emergency bytes")(path, mode)
        
    with patch("builtins.open", my_open):
        result = await error_handler.handle_error(STTEmptyTranscriptionError("empty"))
        assert result == b"emergency bytes"
        assert opened_path[0].endswith("emergency.wav")
    mock_tts.assert_called_once_with("No he entendido lo que has dicho.")

@pytest.mark.asyncio
async def test_handle_error_tts_error_direct_emergency(mocker):
    mock_tts = mocker.patch("app.clients.tts_client.synthesize_speech")
    opened_path = []
    
    def my_open(path, mode):
        opened_path.append(path)
        return mock_open(read_data=b"emergency bytes")(path, mode)
        
    with patch("builtins.open", my_open):
        result = await error_handler.handle_error(TTSUnavailableError("down"))
        assert result == b"emergency bytes"
        assert opened_path[0].endswith("emergency.wav")
    mock_tts.assert_not_called()

@pytest.mark.asyncio
async def test_handle_error_all_mappings(mocker):
    # Test that each exception maps to emergency.wav when TTS fails
    mocker.patch("app.clients.tts_client.synthesize_speech", side_effect=Exception("skip tts"))
    
    test_cases = [
        STTEmptyTranscriptionError(""),
        STTNullResponseError(""),
        STTUnavailableError(""),
        OrchestratorResponseError(""),
        OrchestratorUnavailableError(""),
        TTSResponseError(""),
        TTSUnavailableError(""),
        ValueError("generic error"),
    ]
    
    for exc in test_cases:
        opened_path = []
        def my_open(path, mode):
            opened_path.append(path)
            return mock_open(read_data=b"emergency bytes")(path, mode)
            
        with patch("builtins.open", my_open):
            result = await error_handler.handle_error(exc)
            assert result == b"emergency bytes"
            assert opened_path[0].endswith("emergency.wav")


@pytest.mark.asyncio
async def test_handle_error_text_mappings(mocker):
    mock_tts = mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"fake tts")
    
    test_cases = [
        (STTEmptyTranscriptionError(""), "No he entendido lo que has dicho."),
        (STTNullResponseError(""), "No he podido completar la operación."),
        (STTUnavailableError(""), "El servicio de reconocimiento de voz no está disponible."),
        (OrchestratorResponseError(""), "No he podido completar la operación."),
        (OrchestratorUnavailableError(""), "El servicio solicitado no está disponible."),
        (TTSResponseError(""), "Ha ocurrido un error interno."),
        (TTSUnavailableError(""), "Ha ocurrido un error interno."),
        (ValueError(""), "Ha ocurrido un error interno."),
    ]
    
    for exc, expected_text in test_cases:
        mock_tts.reset_mock()
        if isinstance(exc, (TTSResponseError, TTSUnavailableError)):
            mocker.patch("builtins.open", mock_open(read_data=b"emergency bytes"))
            await error_handler.handle_error(exc)
            mock_tts.assert_not_called()
        else:
            await error_handler.handle_error(exc)
            mock_tts.assert_called_once_with(expected_text)

