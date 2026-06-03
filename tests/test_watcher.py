import pytest
import os
import asyncio
from app.services.file_watcher import AudioFileHandler
from app.config import settings

@pytest.mark.asyncio
async def test_handle_new_file_success(mocker):
    mocker.patch("shutil.move")
    mocker.patch("app.services.interaction_pipeline.process_interaction", return_value=b"audio data")
    mocker.patch("os.remove")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    mock_open.assert_called_once_with(os.path.join(settings.OUTPUT_DIR, "test.wav"), "wb")
    mock_open().write.assert_called_once_with(b"audio data")

@pytest.mark.asyncio
async def test_handle_new_file_pipeline_error(mocker):
    mock_move = mocker.patch("shutil.move")
    mocker.patch("app.services.interaction_pipeline.process_interaction", side_effect=Exception("Pipeline error"))
    mocker.patch("os.path.exists", return_value=True)
    
    loop = asyncio.get_event_loop()
    handler = AudioFileHandler(loop)
    
    await handler.handle_new_file("/data/input/test.wav")
    
    # Check that it tried to move the file to error dir
    processing_path = os.path.join(settings.PROCESSING_DIR, "test.wav")
    error_path = os.path.join(settings.ERROR_DIR, "test.wav")
    
    # It first moves from input to processing, then from processing to error
    assert mock_move.call_count == 2
    mock_move.assert_any_call("/data/input/test.wav", processing_path)
    mock_move.assert_any_call(processing_path, error_path)
