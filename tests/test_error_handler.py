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
    mocker.patch("builtins.open", mock_open(read_data=b"emergency stt not understood bytes"))
    
    result = await error_handler.handle_error(STTEmptyTranscriptionError("empty"))
    
    assert result == b"emergency stt not understood bytes"
    mock_tts.assert_called_once_with("No he entendido lo que has dicho.")

@pytest.mark.asyncio
async def test_handle_error_tts_error_direct_emergency(mocker):
    mock_tts = mocker.patch("app.clients.tts_client.synthesize_speech")
    mocker.patch("builtins.open", mock_open(read_data=b"emergency fatal error bytes"))
    
    result = await error_handler.handle_error(TTSUnavailableError("down"))
    
    assert result == b"emergency fatal error bytes"
    mock_tts.assert_not_called()

@pytest.mark.asyncio
async def test_handle_error_all_mappings(mocker):
    # Test that each exception maps to correct emergency file when TTS fails
    mocker.patch("app.clients.tts_client.synthesize_speech", side_effect=Exception("skip tts"))
    
    test_cases = [
        (STTEmptyTranscriptionError(""), "stt_not_understood.wav"),
        (STTNullResponseError(""), "operation_failed.wav"),
        (STTUnavailableError(""), "stt_unavailable.wav"),
        (OrchestratorResponseError(""), "operation_failed.wav"),
        (OrchestratorUnavailableError(""), "service_unavailable.wav"),
        (TTSResponseError(""), "fatal_error.wav"),
        (TTSUnavailableError(""), "fatal_error.wav"),
        (ValueError("generic error"), "fatal_error.wav"),
    ]
    
    for exc, expected_filename in test_cases:
        opened_path = []
        def my_open(path, mode):
            opened_path.append(path)
            return mock_open(read_data=f"bytes of {expected_filename}".encode())(path, mode)
            
        with patch("builtins.open", my_open):
            result = await error_handler.handle_error(exc)
            assert result == f"bytes of {expected_filename}".encode()
            assert expected_filename in opened_path[0]
