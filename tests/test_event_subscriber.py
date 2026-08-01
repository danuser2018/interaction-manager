import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from nova_event_bus import EventBus
from app.events import SpeechCapturedEvent
from app.services.event_subscriber import InteractionEventSubscriber
from app.config import settings


@pytest.mark.asyncio
async def test_start_subscribes_to_event(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    await subscriber.start()

    mock_bus.connect.assert_awaited_once()
    mock_bus.subscribe.assert_awaited_once_with(SpeechCapturedEvent, subscriber._handle_speech_captured)


@pytest.mark.asyncio
async def test_stop_disconnects(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    await subscriber.stop()

    mock_bus.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_speech_captured_success(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("shutil.move")
    mocker.patch("shutil.copy")
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio bytes")
    mocker.patch("os.remove")
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())

    evt = SpeechCapturedEvent(correlation_id="corr_123", channel="voice", audio_path="test.wav")
    await subscriber._handle_speech_captured(evt)

    output_path = os.path.join(settings.OUTPUT_DIR, "test.wav")
    mock_open_file.assert_called_with(output_path, "wb")
    mock_open_file().write.assert_called_with(b"audio bytes")


@pytest.mark.asyncio
async def test_handle_speech_captured_file_not_found(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mocker.patch("os.path.exists", return_value=False)
    mock_handle_error = mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio")

    evt = SpeechCapturedEvent(correlation_id="corr_123", channel="voice", audio_path="missing.wav")
    await subscriber._handle_speech_captured(evt)

    mock_handle_error.assert_awaited_once()
    args, _ = mock_handle_error.call_args
    assert isinstance(args[0], FileNotFoundError)


@pytest.mark.asyncio
async def test_handle_speech_captured_path_traversal(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mock_handle_error = mocker.patch("app.services.error_handler.handle_error")

    evt = SpeechCapturedEvent(correlation_id="corr_123", channel="voice", audio_path="../../etc/passwd")
    await subscriber._handle_speech_captured(evt)

    mock_handle_error.assert_not_called()


@pytest.mark.asyncio
async def test_handle_speech_captured_pipeline_error_moves_to_error_dir(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    mock_move = mocker.patch("shutil.move")
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio")
    mocker.patch("os.remove")
    mocker.patch("builtins.open", mocker.mock_open())

    evt = SpeechCapturedEvent(correlation_id="corr_123", channel="voice", audio_path="test.wav")
    await subscriber._handle_speech_captured(evt)

    processing_path = os.path.join(settings.PROCESSING_DIR, "test.wav")
    error_path = os.path.join(settings.ERROR_DIR, "test.wav")

    assert mock_move.call_count == 2
    mock_move.assert_any_call(os.path.join(settings.INPUT_DIR, "test.wav"), processing_path)
    mock_move.assert_any_call(processing_path, error_path)


@pytest.mark.asyncio
async def test_handle_speech_captured_duplicate_idempotency(mocker):
    mock_bus = AsyncMock(spec=EventBus)
    subscriber = InteractionEventSubscriber(mock_bus)

    # Resolved path in INPUT_DIR is missing, but file exists in OUTPUT_DIR (already processed)
    def mock_exists(path):
        if path == os.path.join(settings.OUTPUT_DIR, "already_processed.wav"):
            return True
        return False

    mocker.patch("os.path.exists", side_effect=mock_exists)
    mock_handle_error = mocker.patch("app.services.error_handler.handle_error")
    mock_logger_warning = mocker.patch("app.services.event_subscriber.logger.warning")

    evt = SpeechCapturedEvent(correlation_id="corr_123", channel="voice", audio_path="already_processed.wav")
    await subscriber._handle_speech_captured(evt)

    # Warning logged for duplicate event, error_handler not called
    mock_logger_warning.assert_called_once()
    assert "Duplicate SpeechCapturedEvent" in mock_logger_warning.call_args[0][0]
    mock_handle_error.assert_not_called()
