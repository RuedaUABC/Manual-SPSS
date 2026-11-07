"""Framework-independent playback request and state management."""

from __future__ import annotations

from manual_spss.tts_engine.models import (
    PlaybackState,
    SpeechRequest,
    SpeedPreset,
    VoiceInfo,
)


class InvalidTransitionError(RuntimeError):
    """Raised when a playback control is invalid in the current state."""


class SpeechService:
    """Manage request identity and playback states without a UI dependency."""

    def __init__(self, voices: tuple[VoiceInfo, ...]) -> None:
        if not voices:
            raise ValueError("Se necesita al menos una voz española local")
        if any(not voice.locale.lower().startswith("es-") for voice in voices):
            raise ValueError("Solo se admiten voces en español")
        if len({voice.id for voice in voices}) != len(voices):
            raise ValueError("Los identificadores de voz deben ser únicos")
        self._voices = voices
        self._state = PlaybackState.IDLE
        self._next_request_id = 1
        self._active_request: SpeechRequest | None = None
        self._last_request: SpeechRequest | None = None
        self._paused_from: PlaybackState | None = None
        self._error_message: str | None = None

    @property
    def state(self) -> PlaybackState:
        """Return the current playback state."""
        return self._state

    @property
    def error_message(self) -> str | None:
        """Return a recoverable error for the current session, if any."""
        return self._error_message

    @property
    def current_request(self) -> SpeechRequest | None:
        """Return the active request, or the last one after it has stopped."""
        return self._active_request or self._last_request

    def voices(self) -> tuple[VoiceInfo, ...]:
        """Return the configured Spanish voices."""
        return self._voices

    def start(
        self,
        text: str,
        voice_id: str,
        speed: SpeedPreset = SpeedPreset.NORMAL,
    ) -> SpeechRequest:
        """Start a new request, invalidating any events from the old request."""
        if not text.strip():
            raise ValueError("No hay texto para leer")
        if voice_id not in {voice.id for voice in self._voices}:
            raise ValueError(f"No está disponible la voz española: {voice_id}")
        if not isinstance(speed, SpeedPreset):
            raise ValueError("La velocidad seleccionada no es válida")
        request = SpeechRequest(
            request_id=self._next_request_id,
            text=text,
            voice_id=voice_id,
            speed=speed,
        )
        self._next_request_id += 1
        self._active_request = request
        self._last_request = request
        self._state = PlaybackState.STARTING
        self._paused_from = None
        self._error_message = None
        return request

    def pause(self) -> None:
        """Pause a request that is being prepared or played."""
        if self._state not in (PlaybackState.STARTING, PlaybackState.PLAYING):
            raise InvalidTransitionError("No se puede pausar en este estado")
        self._paused_from = self._state
        self._state = PlaybackState.PAUSED

    def resume(self) -> None:
        """Resume a paused request in the state it had reached."""
        if self._state is not PlaybackState.PAUSED or self._paused_from is None:
            raise InvalidTransitionError("No se puede reanudar en este estado")
        self._state = self._paused_from
        self._paused_from = None

    def stop(self) -> None:
        """Invalidate the active request so late worker events are ignored."""
        if self._active_request is None:
            raise InvalidTransitionError("No hay una lectura que detener")
        self._active_request = None
        self._state = PlaybackState.STOPPED
        self._paused_from = None
        self._error_message = None

    def restart(self) -> SpeechRequest:
        """Start the last text again with the same voice and speed."""
        request = self._last_request
        if request is None:
            raise InvalidTransitionError("No hay una lectura que reiniciar")
        return self.start(request.text, request.voice_id, request.speed)

    def mark_playing(self, request_id: int) -> bool:
        """Accept a worker's first-audio event if it belongs to this request."""
        if not self._is_active(request_id):
            return False
        if self._state is PlaybackState.PAUSED:
            self._paused_from = PlaybackState.PLAYING
            return True
        if self._state is not PlaybackState.STARTING:
            return False
        self._state = PlaybackState.PLAYING
        return True

    def finish(self, request_id: int) -> bool:
        """Finish the current request; ignore completion from stale workers."""
        if not self._is_active(request_id):
            return False
        if self._state not in (
            PlaybackState.STARTING,
            PlaybackState.PLAYING,
            PlaybackState.PAUSED,
        ):
            return False
        self._active_request = None
        self._state = PlaybackState.FINISHED
        self._paused_from = None
        return True

    def fail(self, request_id: int, message: str) -> bool:
        """Expose a recoverable worker error if it belongs to this request."""
        if not self._is_active(request_id):
            return False
        if self._state not in (
            PlaybackState.STARTING,
            PlaybackState.PLAYING,
            PlaybackState.PAUSED,
        ):
            return False
        self._active_request = None
        self._state = PlaybackState.ERROR
        self._paused_from = None
        self._error_message = message.strip() or "Error al generar la voz"
        return True

    def _is_active(self, request_id: int) -> bool:
        return (
            self._active_request is not None
            and self._active_request.request_id == request_id
        )
