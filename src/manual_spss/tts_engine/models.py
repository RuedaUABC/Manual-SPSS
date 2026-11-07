"""Immutable values shared by the TTS engine and application."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class PlaybackState(StrEnum):
    """Visible states of one speech playback session."""

    IDLE = "idle"
    STARTING = "starting"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"
    ERROR = "error"


class SpeedPreset(StrEnum):
    """Playback speed labels mapped to Piper's length scale."""

    SLOW = "Lenta"
    NORMAL = "Normal"
    FAST = "Rápida"

    @property
    def piper_length_scale(self) -> float:
        """Return the calibrated Piper duration scale for this preset."""
        return {
            SpeedPreset.SLOW: 1.25,
            SpeedPreset.NORMAL: 1.0,
            SpeedPreset.FAST: 0.8,
        }[self]


@dataclass(frozen=True, slots=True)
class VoiceInfo:
    """Metadata and local model files for an available voice."""

    id: str
    display_name: str
    locale: str
    model_path: Path
    config_path: Path
    quality: str = "medium"
    dataset_license: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.display_name.strip():
            raise ValueError("La voz debe tener identificador y nombre")
        if not self.locale.lower().startswith("es-"):
            raise ValueError("Solo se admiten voces en español")


@dataclass(frozen=True, slots=True)
class AudioChunk:
    """Interleaved signed PCM audio produced by a speech engine."""

    pcm: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = 2

    def __post_init__(self) -> None:
        if not self.pcm:
            raise ValueError("El fragmento de audio no puede estar vacío")
        if self.sample_rate <= 0 or self.channels <= 0 or self.sample_width <= 0:
            raise ValueError("Formato PCM inválido")
        frame_width = self.channels * self.sample_width
        if len(self.pcm) % frame_width:
            raise ValueError("El audio PCM debe contener fotogramas completos")

    @property
    def frame_count(self) -> int:
        """Return the number of audio frames in the chunk."""
        return len(self.pcm) // (self.channels * self.sample_width)

    @property
    def duration_seconds(self) -> float:
        """Return the chunk's duration in seconds."""
        return self.frame_count / self.sample_rate


@dataclass(frozen=True, slots=True)
class SpeechRequest:
    """One immutable request to synthesize and play Spanish text."""

    request_id: int
    text: str
    voice_id: str
    speed: SpeedPreset
