class InteractionManagerError(Exception):
    """Base exception for all Interaction Manager errors."""
    pass


class STTError(InteractionManagerError):
    """Base exception for all STT errors."""
    pass


class STTEmptyTranscriptionError(STTError):
    """Raised when STT returns empty transcription."""
    pass


class STTNullResponseError(STTError):
    """Raised when STT returns null transcription."""
    pass


class STTUnavailableError(STTError):
    """Raised when STT service is unavailable or times out."""
    pass


class OrchestratorError(InteractionManagerError):
    """Base exception for all Orchestrator errors."""
    pass


class OrchestratorResponseError(OrchestratorError):
    """Raised when Orchestrator returns unsuccessful or empty response."""
    pass


class OrchestratorUnavailableError(OrchestratorError):
    """Raised when Orchestrator service is unavailable or times out."""
    pass


class TTSError(InteractionManagerError):
    """Base exception for all TTS errors."""
    pass


class TTSResponseError(TTSError):
    """Raised when TTS returns empty audio."""
    pass


class TTSUnavailableError(TTSError):
    """Raised when TTS service is unavailable or times out."""
    pass
