from dataclasses import dataclass
from nova_event_bus import Event, event


@event("event.speech.captured")
@dataclass
class SpeechCapturedEvent(Event):
    """Domain event received when mic-daemon completes audio capture."""
    correlation_id: str
    channel: str
    audio_path: str
