"""Local Spanish text-to-speech contracts and playback state."""

from manual_spss.tts_engine.models import (
    AudioChunk,
    PlaybackState,
    SpeechRequest,
    SpeedPreset,
    VoiceInfo,
)
from manual_spss.tts_engine.service import InvalidTransitionError, SpeechService

__all__ = [
    "AudioChunk",
    "InvalidTransitionError",
    "PlaybackState",
    "SpeechRequest",
    "SpeechService",
    "SpeedPreset",
    "VoiceInfo",
]
