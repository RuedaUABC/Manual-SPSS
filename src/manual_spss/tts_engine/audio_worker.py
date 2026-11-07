"""Background Piper synthesis with cooperative pause and cancellation."""

from __future__ import annotations

from threading import Event
from typing import Protocol

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from manual_spss.tts_engine.models import AudioChunk, SpeechRequest
from manual_spss.tts_engine.protocols import SpeechEngine


class AudioChunkOutput(Protocol):
    """Thread-safe destination for synthesized PCM chunks."""

    def enqueue(self, request_id: int, chunk: AudioChunk, cancel: Event) -> bool:
        """Enqueue a chunk or return false after cancellation/stopping."""

    def mark_synthesis_finished(self, request_id: int) -> None:
        """Mark completion of chunk generation for this request."""


class SpeechWorker(QThread):
    """Run one synthesis request away from the UI thread."""

    first_chunk_ready = pyqtSignal(int)
    synthesis_finished = pyqtSignal(int)
    failed = pyqtSignal(int, str)

    def __init__(
        self,
        request: SpeechRequest,
        engine: SpeechEngine,
        output: AudioChunkOutput,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.request = request
        self._engine = engine
        self._output = output
        self._cancel = Event()
        self._pause_requested = Event()

    def pause(self) -> None:
        """Stop the producer at the next synthesized chunk boundary."""
        self._pause_requested.set()

    def resume(self) -> None:
        """Allow chunk production to continue after a pause."""
        self._pause_requested.clear()

    def cancel(self) -> None:
        """Cancel synthesis and release a producer waiting on queue capacity."""
        self._cancel.set()
        self._pause_requested.clear()

    def run(self) -> None:
        """Generate chunks, apply queue backpressure and report recoverable errors."""
        first_chunk = True
        try:
            for chunk in self._engine.synthesize(self.request, self._cancel):
                while self._pause_requested.is_set() and not self._cancel.wait(0.05):
                    pass
                if self._cancel.is_set():
                    return
                accepted = self._output.enqueue(
                    self.request.request_id, chunk, self._cancel
                )
                if not accepted:
                    return
                if first_chunk:
                    first_chunk = False
                    self.first_chunk_ready.emit(self.request.request_id)
            if self._cancel.is_set():
                return
            self._output.mark_synthesis_finished(self.request.request_id)
            self.synthesis_finished.emit(self.request.request_id)
        except Exception as error:
            if not self._cancel.is_set():
                self.failed.emit(self.request.request_id, str(error))
