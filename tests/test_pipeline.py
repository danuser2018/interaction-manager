import pytest
from app.services import interaction_pipeline
from app.exceptions import (
    STTEmptyTranscriptionError,
    STTNullResponseError,
    OrchestratorResponseError,
    TTSResponseError,
)

@pytest.mark.asyncio
async def test_process_interaction_success(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"audio bytes")
    
    result = await interaction_pipeline.process_interaction("fake/path.wav")
    assert result == b"audio bytes"

@pytest.mark.asyncio
async def test_process_interaction_stt_empty_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="")
    
    with pytest.raises(STTEmptyTranscriptionError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_stt_null_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value=None)
    
    with pytest.raises(STTNullResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_orchestrator_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="")
    
    with pytest.raises(OrchestratorResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_tts_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"")
    
    with pytest.raises(TTSResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

