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
    mocker.patch("app.clients.orchestrator_client.resolve_intent", return_value={"steps": []})
    mocker.patch("app.clients.orchestrator_client.execute_plan", return_value="hola de vuelta")
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
    mocker.patch("app.clients.orchestrator_client.resolve_intent", side_effect=OrchestratorResponseError("Resolve failure"))
    
    with pytest.raises(OrchestratorResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_tts_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.resolve_intent", return_value={"steps": []})
    mocker.patch("app.clients.orchestrator_client.execute_plan", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"")
    
    with pytest.raises(TTSResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_execute_plan_failure(mocker):
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.resolve_intent", return_value={"steps": []})
    mocker.patch("app.clients.orchestrator_client.execute_plan", side_effect=OrchestratorResponseError("Execute plan failure"))
    
    with pytest.raises(OrchestratorResponseError):
        await interaction_pipeline.process_interaction("fake/path.wav")

@pytest.mark.asyncio
async def test_process_interaction_logs_timing(mocker, caplog):
    import logging
    caplog.set_level(logging.INFO)
    
    mocker.patch("app.clients.stt_client.get_transcription", return_value="hola")
    mocker.patch("app.clients.orchestrator_client.resolve_intent", return_value={"steps": []})
    mocker.patch("app.clients.orchestrator_client.execute_plan", return_value="hola de vuelta")
    mocker.patch("app.clients.tts_client.synthesize_speech", return_value=b"audio bytes")
    
    await interaction_pipeline.process_interaction("fake/path.wav")
    
    log_messages = [record.message for record in caplog.records]
    
    # Check sequential info logs
    assert "Resolving user intent..." in log_messages
    assert "ExecutionPlan received." in log_messages
    assert "Executing plan..." in log_messages
    assert "Assistant response received." in log_messages
    
    # Check order of sequential logs
    idx1 = log_messages.index("Resolving user intent...")
    idx2 = log_messages.index("ExecutionPlan received.")
    idx3 = log_messages.index("Executing plan...")
    idx4 = log_messages.index("Assistant response received.")
    assert idx1 < idx2 < idx3 < idx4
    
    # Check timings in logs
    timing_logs = [msg for msg in log_messages if "time:" in msg]
    assert len(timing_logs) >= 3
    assert any("Resolution time:" in msg and msg.endswith("s") for msg in timing_logs)
    assert any("Execution time:" in msg and msg.endswith("s") for msg in timing_logs)
    assert any("Total time:" in msg and msg.endswith("s") for msg in timing_logs)


