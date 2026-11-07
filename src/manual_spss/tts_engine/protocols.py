"""Protocols implemented by speech synthesis backends."""

from __future__ import annotations

from collections.abc import Iterator
from threading import Event
from typing import Protocol

from manual_spss.tts_engine.models import AudioChunk, SpeechRequest, VoiceInfo


class SpeechEngine(Protocol):
    """Local speech backend that yields bounded PCM chunks."""

    def voices(self) -> tuple[VoiceInfo, ...]:
        """Return the Spanish voices whose local assets are available."""

    def synthesize(
        self, request: SpeechRequest, cancel: Event
    ) -> Iterator[AudioChunk]:
        """Synthesize a request, observing cancellation between chunks."""
