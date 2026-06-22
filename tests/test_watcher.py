import pytest
import os
import asyncio
from unittest.mock import mock_open, patch
from app.services.file_watcher import AudioFileHandler
from app.config import settings

@pytest.mark.asyncio
async def test_handle_new_file_success(mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.copy")  # Mock copy for audio feedback
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio data")
    mocker.patch("os.remove")
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    mock_open_file.assert_called_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open_file().write.assert_called_with(b"audio data")

@pytest.mark.asyncio
async def test_handle_new_file_pipeline_error_moves_to_error_dir(mocker):
    mock_move = mocker.patch("shutil.move")
    mocker.patch("shutil.copy")  # Mock copy for audio feedback
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio")
    mocker.patch("os.remove")
    mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify: first move from input → processing, then processing → error
    processing_path = os.path.join(settings.PROCESSING_DIR, "test.wav")
    error_path = os.path.join(settings.ERROR_DIR, "test.wav")
    
    assert mock_move.call_count == 2
    mock_move.assert_any_call("/data/input/test.wav", processing_path)
    mock_move.assert_any_call(processing_path, error_path)

@pytest.mark.asyncio
async def test_handle_new_file_pipeline_error_writes_error_audio(mocker):
    mocker.patch("shutil.move")
    mocker.patch("shutil.copy")  # Mock copy for audio feedback
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio bytes")
    mocker.patch("os.remove")
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify error audio is written to output_path (RF-003, RF-004)
    output_path = os.path.join(settings.OUTPUT_DIR, "test.wav")
    mock_open_file.assert_called_with(output_path, "wb")
    mock_open_file().write.assert_called_with(b"error audio bytes")


@pytest.mark.asyncio
async def test_handle_new_file_with_audio_feedback_success(mocker):
    mocker.patch("shutil.move")
    mock_copy = mocker.patch("shutil.copy")
    mock_remove = mocker.patch("os.remove")
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio data")
    mocker.patch("os.path.exists", side_effect=lambda path: path == settings.INTERACTION_AUDIO_FILE)
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify copy is called
    expected_feedback_path = os.path.join(settings.OUTPUT_DIR, "interaction_test.wav")
    mock_copy.assert_called_once_with(settings.INTERACTION_AUDIO_FILE, expected_feedback_path)
    
    # Verify remove is called for the feedback file
    mock_remove.assert_any_call(expected_feedback_path)
    
    # Verify final response is written
    mock_open_file.assert_called_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open_file().write.assert_called_with(b"audio data")


@pytest.mark.asyncio
async def test_handle_new_file_with_audio_feedback_pipeline_error(mocker):
    mocker.patch("shutil.move")
    mock_copy = mocker.patch("shutil.copy")
    mock_remove = mocker.patch("os.remove")
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio")
    
    # exists should return True for both INTERACTION_AUDIO_FILE and processing path
    mocker.patch("os.path.exists", side_effect=lambda path: True)
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify copy is called
    expected_feedback_path = os.path.join(settings.OUTPUT_DIR, "interaction_test.wav")
    mock_copy.assert_called_once_with(settings.INTERACTION_AUDIO_FILE, expected_feedback_path)
    
    # Verify remove is called for the feedback file
    mock_remove.assert_any_call(expected_feedback_path)
    
    # Verify error audio is written
    mock_open_file.assert_called_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open_file().write.assert_called_with(b"error audio")


@pytest.mark.asyncio
async def test_handle_new_file_audio_feedback_copy_error_continues(mocker):
    mocker.patch("shutil.move")
    mock_copy = mocker.patch("shutil.copy", side_effect=Exception("Copy failed"))
    mock_remove = mocker.patch("os.remove")
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio data")
    mocker.patch("os.path.exists", side_effect=lambda path: path == settings.INTERACTION_AUDIO_FILE)
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    # Should not raise copy exception, should continue and finish processing
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify copy was attempted
    mock_copy.assert_called_once()
    
    # Verify remove was NOT called for the feedback file (since feedback_copied was False)
    expected_feedback_path = os.path.join(settings.OUTPUT_DIR, "interaction_test.wav")
    assert expected_feedback_path not in [args[0] for args, _ in mock_remove.call_args_list]
    
    # Verify final response is still written
    mock_open_file.assert_called_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open_file().write.assert_called_with(b"audio data")
