import os

# Base URLs
STT_BASE_URL = os.getenv("STT_BASE_URL", "http://stt:8000")
ORCHESTRATOR_BASE_URL = os.getenv("ORCHESTRATOR_BASE_URL", "http://orchestrator:8000")
TTS_BASE_URL = os.getenv("TTS_BASE_URL", "http://tts:8000")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Directories
INPUT_DIR = os.getenv("INPUT_DIR", "/data/input")
PROCESSING_DIR = os.getenv("PROCESSING_DIR", "/data/processing")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/data/output")
ERROR_DIR = os.getenv("ERROR_DIR", "/data/error")

# Config
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "auto")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TTS_TIMEOUT = float(os.getenv("TTS_TIMEOUT", "30.0"))
EMERGENCY_AUDIO_DIR = os.getenv(
    "EMERGENCY_AUDIO_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audio", "emergency"))
)
INTERACTION_AUDIO_FILE = os.getenv(
    "INTERACTION_AUDIO_FILE",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audio", "system", "interaction.wav"))
)
