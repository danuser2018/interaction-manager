import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from nova_event_bus import EventBus
from app.events import ExecuteShortcutCommand
from app.services import interaction_pipeline
from app.services.event_subscriber import InteractionEventSubscriber
from app.exceptions import OrchestratorResponseError, TTSResponseError
from app.config import settings


@pytest.mark.asyncio
async def test_execute_shortcut_command_instantiation():
    cmd = ExecuteShortcutCommand(
        correlation_id="781870fc-80fe-4165-ae55-4ebdc36b1c60",
        shortcut="weather",
        channel="cli",
    )
    assert cmd.correlation_id == "781870fc-80fe-4165-ae55-4ebdc36b1c60"
    assert cmd.shortcut == "weather"
    assert cmd.channel == "cli"


@pytest.mark.asyncio
async def test_process_shortcut_interaction_success(mocker):
    mock_execute_plan = mocker.patch(
        "app.clients.orchestrator_client.execute_plan",
        return_value="En Madrid hace 20 grados",
    )
    mock_synthesize = mocker.patch(
        "app.clients.tts_client.synthesize_speech",
        return_value=b"synthesized audio bytes",
    )

    audio_bytes = await interaction_pipeline.process_shortcut_interaction(
        shortcut="weather",
        channel="cli",
        correlation_id="corr_abc123",
    )

    assert audio_bytes == b"synthesized audio bytes"
    mock_execute_plan.assert_awaited_once()
    passed_plan = mock_execute_plan.call_args[0][0]
    assert passed_plan["steps"][0]["plugin"] == "weather"
    assert passed_plan["steps"][0]["confidence"] == 100.0
    assert passed_plan["steps"][0]["channel"] == "cli"
    assert passed_plan["steps"][0]["context"]["correlation_id"] == "corr_abc123"
    mock_synthesize.assert_awaited_once_with("En Madrid hace 20 grados")


@pytest.mark.asyncio
async def test_process_shortcut_interaction_empty_orchestrator_response(mocker):
    mocker.patch(
        "app.clients.orchestrator_client.execute_plan",
        return_value="",
    )

    with pytest.raises(OrchestratorResponseError):
        await interaction_pipeline.process_shortcut_interaction(
            shortcut="weather",
            channel="cli",
            correlation_id="corr_abc123",
        )


@pytest.mark.asyncio
async def test_process_shortcut_interaction_empty_tts_response(mocker):
    mocker.patch(
        "app.clients.orchestrator_client.execute_plan",
        return_value="Speech response",
    )
    mocker.patch(
        "app.clients.tts_client.synthesize_speech",
        return_value=b"",
    )

    with pytest.raises(TTSResponseError):
        await interaction_pipeline.process_shortcut_interaction(
            shortcut="weather",
            channel="cli",
            correlation_id="corr_abc123",
        )


@pytest.mark.asyncio
async def test_subscriber_start_registers_shortcut_command(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    await subscriber.start()

    mock_bus.connect.assert_awaited_once()
    mock_bus.subscribe.assert_any_call(
        ExecuteShortcutCommand, subscriber._handle_execute_shortcut
    )


@pytest.mark.asyncio
async def test_handle_execute_shortcut_success(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mocker.patch("os.path.exists", return_value=False)
    mocker.patch(
        "app.services.interaction_pipeline.process_shortcut_interaction",
        return_value=b"shortcut audio bytes",
    )
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())

    cmd = ExecuteShortcutCommand(
        correlation_id="corr_999", shortcut="calendar", channel="cli"
    )
    await subscriber._handle_execute_shortcut(cmd)

    output_path = os.path.join(settings.OUTPUT_DIR, "shortcut_corr_999.wav")
    mock_open_file.assert_called_with(output_path, "wb")
    mock_open_file().write.assert_called_with(b"shortcut audio bytes")


@pytest.mark.asyncio
async def test_handle_execute_shortcut_error_handling(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mocker.patch("os.path.exists", return_value=False)
    mocker.patch(
        "app.services.interaction_pipeline.process_shortcut_interaction",
        side_effect=Exception("Shortcut execution error"),
    )
    mock_handle_error = mocker.patch(
        "app.services.error_handler.handle_error", return_value=b"error audio"
    )
    mocker.patch("builtins.open", mocker.mock_open())

    cmd = ExecuteShortcutCommand(
        correlation_id="corr_err", shortcut="invalid_plugin", channel="cli"
    )
    await subscriber._handle_execute_shortcut(cmd)

    mock_handle_error.assert_awaited_once()
