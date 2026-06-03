import os

# Base URLs
STT_BASE_URL = os.getenv("STT_BASE_URL", "http://stt:8000")
ORCHESTRATOR_BASE_URL = os.getenv("ORCHESTRATOR_BASE_URL", "http://orchestrator:8000")
TTS_BASE_URL = os.getenv("TTS_BASE_URL", "http://tts:8000")

# Directories
INPUT_DIR = os.getenv("INPUT_DIR", "/data/input")
PROCESSING_DIR = os.getenv("PROCESSING_DIR", "/data/processing")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/data/output")
ERROR_DIR = os.getenv("ERROR_DIR", "/data/error")

# Config
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "1"))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "auto")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
