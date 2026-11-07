"""Tests for background synthesis and output backpressure."""

from __future__ import annotations

from threading import Event

import pytest
from PyQt6.QtCore import QCoreApplication

from manual_spss.tts_engine.audio_worker import SpeechWorker
from manual_spss.tts_engine.models import AudioChunk, SpeechRequest, SpeedPreset


class _FakeEngine:
    def __init__(self, chunks: tuple[AudioChunk, ...]) -> None:
        self.chunks = chunks
        self.cancel_events: list[Event] = []

    def synthesize(self, _request: SpeechRequest, cancel: Event):
        self.cancel_events.append(cancel)
        for chunk in self.chunks:
            if cancel.is_set():
                return
            yield chunk


class _FakeOutput:
    def __init__(self) -> None:
        self.received: list[tuple[int, AudioChunk]] = []
        self.accept = True

    def enqueue(self, request_id: int, chunk: AudioChunk, _cancel: Event) -> bool:
        self.received.append((request_id, chunk))
        return self.accept

    def mark_synthesis_finished(self, _request_id: int) -> None:
        pass


@pytest.fixture(scope="module")
def qapp() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _request() -> SpeechRequest:
    return SpeechRequest(4, "Prueba de audio", "es_MX-ald-medium", SpeedPreset.NORMAL)


def _chunk(value: int) -> AudioChunk:
    return AudioChunk(bytes([value, 0]) * 4, sample_rate=22050)


def test_worker_synthesizes_off_thread_and_signals_completion(
    qapp: QCoreApplication,
) -> None:
    engine = _FakeEngine((_chunk(1), _chunk(2)))
    output = _FakeOutput()
    worker = SpeechWorker(_request(), engine, output)
    queued = Event()
    finished = Event()
    worker.first_chunk_ready.connect(lambda _request_id: queued.set())
    worker.synthesis_finished.connect(lambda _request_id: finished.set())

    worker.start()
    assert worker.wait(2000)
    qapp.processEvents()

    assert queued.is_set()
    assert finished.is_set()
    assert [chunk.pcm[:2] for _, chunk in output.received] == [b"\x01\x00", b"\x02\x00"]


def test_worker_pause_and_resume_preserve_request() -> None:
    engine = _FakeEngine((_chunk(1), _chunk(2)))
    output = _FakeOutput()
    worker = SpeechWorker(_request(), engine, output)
    worker.pause()

    worker.start()
    assert not worker.wait(30)
    worker.resume()
    assert worker.wait(2000)

    assert len(output.received) == 2


def test_worker_cancel_stops_synthesis_and_does_not_finish() -> None:
    engine = _FakeEngine((_chunk(1), _chunk(2)))
    output = _FakeOutput()
    worker = SpeechWorker(_request(), engine, output)
    finished = Event()
    worker.synthesis_finished.connect(lambda _request_id: finished.set())

    worker.cancel()
    worker.start()
    assert worker.wait(2000)

    assert output.received == []
    assert not finished.is_set()


def test_worker_reports_engine_errors(qapp: QCoreApplication) -> None:
    class BrokenEngine:
        def synthesize(self, _request: SpeechRequest, _cancel: Event):
            raise RuntimeError("modelo roto")
            yield _chunk(1)

    output = _FakeOutput()
    worker = SpeechWorker(_request(), BrokenEngine(), output)
    received: list[str] = []
    worker.failed.connect(lambda _request_id, message: received.append(message))

    worker.start()
    assert worker.wait(2000)
    qapp.processEvents()

    assert received == ["modelo roto"]
