"""Coordinate domain state, background synthesis and Qt audio output."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from manual_spss.tts_engine.audio_output import QtAudioOutput
from manual_spss.tts_engine.audio_worker import SpeechWorker
from manual_spss.tts_engine.models import (
    PlaybackState,
    SpeechRequest,
    SpeedPreset,
    VoiceInfo,
)
from manual_spss.tts_engine.protocols import SpeechEngine
from manual_spss.tts_engine.service import InvalidTransitionError, SpeechService

_VOICE_SAMPLE = (
    "Esta es una muestra de voz en español para el Manual SPSS. "
    "Puedes elegir la voz que prefieras en los ajustes."
)


class SpeechController(QObject):
    """Bridge user actions to the speech service and local audio backend."""

    state_changed = pyqtSignal(object, str, bool)
    progress_changed = pyqtSignal(float)
    voice_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        engine: SpeechEngine,
        service: SpeechService,
        output: QtAudioOutput,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._service = service
        self._output = output
        voices = service.voices()
        self._selected_voice_id = voices[0].id
        self._speed = SpeedPreset.NORMAL
        self._local_error = ""
        self._workers: set[SpeechWorker] = set()
        self._output.finished.connect(self._on_audio_finished)
        self._output.progress_changed.connect(self._on_progress)
        self._output.error_occurred.connect(self._on_audio_error)

    @property
    def voices(self) -> tuple[VoiceInfo, ...]:
        """Return locally installed Spanish voice options."""
        return self._service.voices()

    @property
    def selected_voice_id(self) -> str:
        """Return the voice used for the next reading or preview."""
        return self._selected_voice_id

    @property
    def speed(self) -> SpeedPreset:
        """Return the selected speed preset."""
        return self._speed

    @property
    def state(self) -> PlaybackState:
        """Return service state, including a local request validation error."""
        if self._local_error:
            return PlaybackState.ERROR
        return self._service.state

    def select_voice(self, voice_id: str) -> bool:
        """Select an installed voice for the next reading."""
        if voice_id not in {voice.id for voice in self.voices}:
            self._set_local_error("La voz seleccionada no está instalada")
            return False
        self._selected_voice_id = voice_id
        self._local_error = ""
        self.voice_changed.emit(voice_id)
        self._publish_state()
        return True

    def set_speed(self, speed: SpeedPreset) -> None:
        """Set the preset used by the next request."""
        self._speed = speed

    def start(self, text: str) -> bool:
        """Start reading plain text with the selected voice and speed."""
        try:
            request = self._service.start(
                text, self._selected_voice_id, self._speed
            )
        except (TypeError, ValueError) as error:
            self._set_local_error(str(error))
            return False
        self._local_error = ""
        self._cancel_workers()
        return self._launch(request)

    def preview_voice(self, voice_id: str | None = None) -> bool:
        """Read a short Spanish sample without touching the active manual page."""
        if voice_id is not None and not self.select_voice(voice_id):
            return False
        return self.start(_VOICE_SAMPLE)

    def pause(self) -> bool:
        """Pause synthesis and audio output while preserving queued chunks."""
        try:
            self._service.pause()
        except InvalidTransitionError:
            return False
        for worker in tuple(self._workers):
            worker.pause()
        self._output.pause()
        self._publish_state()
        return True

    def resume(self) -> bool:
        """Resume synthesis and output for the paused request."""
        try:
            self._service.resume()
        except InvalidTransitionError:
            return False
        request = self._service.current_request
        if request is not None:
            for worker in tuple(self._workers):
                if worker.request.request_id == request.request_id:
                    worker.resume()
        self._output.resume()
        self._publish_state()
        return True

    def stop(self) -> bool:
        """Cancel active synthesis and clear pending audio."""
        try:
            self._service.stop()
        except InvalidTransitionError:
            return False
        self._cancel_workers()
        self._output.stop()
        self._local_error = ""
        self._publish_state()
        return True

    def restart(self) -> bool:
        """Restart the last text from its beginning using the same options."""
        try:
            request = self._service.restart()
        except InvalidTransitionError as error:
            self._set_local_error(str(error))
            return False
        self._local_error = ""
        self._cancel_workers()
        return self._launch(request)

    def set_volume(self, volume: float) -> None:
        """Set output volume without changing the current request."""
        self._output.set_volume(volume)

    def set_muted(self, muted: bool) -> None:
        """Mute or restore audio output."""
        self._output.set_muted(muted)

    def shutdown(self) -> None:
        """Cancel all worker threads and release the output device."""
        for worker in tuple(self._workers):
            worker.cancel()
        self._output.stop()
        for worker in tuple(self._workers):
            worker.wait()
        self._workers.clear()

    def _launch(self, request: SpeechRequest) -> bool:
        try:
            self._output.begin_request(request.request_id)
        except Exception as error:
            self._service.fail(request.request_id, str(error))
            self._local_error = str(error)
            self._publish_state()
            self.error_occurred.emit(str(error))
            return False

        worker = SpeechWorker(request, self._engine, self._output, self)
        self._workers.add(worker)
        worker.first_chunk_ready.connect(self._on_first_chunk_ready)
        worker.failed.connect(self._on_worker_failed)
        worker.finished.connect(lambda worker=worker: self._workers.discard(worker))
        worker.start()
        self._publish_state()
        return True

    def _cancel_workers(self) -> None:
        for worker in tuple(self._workers):
            worker.cancel()

    def _on_first_chunk_ready(self, request_id: int) -> None:
        if self._service.mark_playing(request_id):
            self._publish_state()

    def _on_audio_finished(self, request_id: int) -> None:
        if self._service.finish(request_id):
            self._local_error = ""
            self.progress_changed.emit(1.0)
            self._publish_state()

    def _on_worker_failed(self, request_id: int, message: str) -> None:
        if self._service.fail(request_id, message):
            self._output.stop()
            self._local_error = ""
            self._publish_state()
            self.error_occurred.emit(message)

    def _on_audio_error(self, request_id: int, message: str) -> None:
        if self._service.fail(request_id, message):
            self._cancel_workers()
            self._publish_state()
            self.error_occurred.emit(message)

    def _on_progress(self, request_id: int, progress: float) -> None:
        request = self._service.current_request
        if request is not None and request.request_id == request_id:
            self.progress_changed.emit(progress)

    def _set_local_error(self, message: str) -> None:
        self._local_error = message
        self._publish_state()
        self.error_occurred.emit(message)

    def _publish_state(self) -> None:
        request = self._service.current_request
        message = self._local_error or self._service.error_message or ""
        self.state_changed.emit(self.state, message, request is not None)
