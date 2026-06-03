import pytest
from app.services import interaction_pipeline

@pytest.mark.asyncio
async def test_process_interaction_success(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"audio bytes")
    
    result = await interaction_pipeline.process_interaction("fake/path.wav")
    assert result == b"audio bytes"

@pytest.mark.asyncio
async def test_process_interaction_stt_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="")
    
    with pytest.raises(ValueError, match="STT service returned an empty transcription"):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_orchestrator_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="")
    
    with pytest.raises(ValueError, match="Orchestrator returned an empty response"):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_tts_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.execute_interaction", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"")
    
    with pytest.raises(ValueError, match="TTS service returned empty audio"):
        await interaction_pipeline.process_interaction("fake/path.wav")
