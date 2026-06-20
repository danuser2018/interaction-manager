import pytest
import os
import asyncio
from unittest.mock import mock_open, patch
from app.services.file_watcher import AudioFileHandler
from app.config import settings

@pytest.mark.asyncio
async def test_handle_new_file_success(mocker):
    mocker.patch("shutil.move")
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio data")
    mocker.patch("os.remove")
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    mock_open_file.assert_called_once_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open_file().write.assert_called_once_with(b"audio data")

@pytest.mark.asyncio
async def test_handle_new_file_pipeline_error_moves_to_error_dir(mocker):
    mock_move = mocker.patch("shutil.move")
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio")
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
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("app.services.error_handler.handle_error", return_value=b"error audio bytes")
    mock_open_file = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Verify error audio is written to output_path (RF-003, RF-004)
    output_path = os.path.join(settings.OUTPUT_DIR, "test.wav")
    mock_open_file.assert_called_with(output_path, "wb")
    mock_open_file().write.assert_called_with(b"error audio bytes")

