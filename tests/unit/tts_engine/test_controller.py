"""Tests for playback coordination across service, worker and audio output."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Event

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal

from manual_spss.tts_engine.controller import SpeechController
from manual_spss.tts_engine.models import (
    AudioChunk,
    PlaybackState,
    SpeechRequest,
    SpeedPreset,
    VoiceInfo,
)
from manual_spss.tts_engine.service import SpeechService

VOICES = (
    VoiceInfo(
        "es_MX-ald-medium",
        "Español (México) — Ald",
        "es-MX",
        Path("ald.onnx"),
        Path("ald.onnx.json"),
    ),
    VoiceInfo(
        "es_ES-davefx-medium",
        "Español (España) — Davefx",
        "es-ES",
        Path("davefx.onnx"),
        Path("davefx.onnx.json"),
    ),
)


class _FakeEngine:
    def __init__(self) -> None:
        self.requests: list[SpeechRequest] = []

    def voices(self) -> tuple[VoiceInfo, ...]:
        return VOICES

    def synthesize(self, request: SpeechRequest, cancel: Event):
        self.requests.append(request)
        if not cancel.is_set():
            yield AudioChunk(b"\x01\x00" * 8, 22050)


class _FakeOutput(QObject):
    progress_changed = pyqtSignal(int, float)
    finished = pyqtSignal(int)
    error_occurred = pyqtSignal(int, str)

    def __init__(self, *, fail_begin: bool = False) -> None:
        super().__init__()
        self.fail_begin = fail_begin
        self.request_id: int | None = None
        self.received: list[tuple[int, AudioChunk]] = []
        self.paused = False
        self.stopped = False
        self.volume = 1.0
        self.muted = False

    def begin_request(self, request_id: int) -> None:
        if self.fail_begin:
            raise RuntimeError("No hay dispositivo de audio")
        self.request_id = request_id
        self.stopped = False
        self.received.clear()

    def enqueue(self, request_id: int, chunk: AudioChunk, _cancel: Event) -> bool:
        if request_id != self.request_id:
            return False
        self.received.append((request_id, chunk))
        return True

    def mark_synthesis_finished(self, _request_id: int) -> None:
        pass

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def stop(self) -> None:
        self.stopped = True
        self.request_id = None

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def set_muted(self, muted: bool) -> None:
        self.muted = muted


@pytest.fixture(scope="module")
def qapp() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _controller(
    engine: _FakeEngine | None = None,
    output: _FakeOutput | None = None,
) -> tuple[SpeechController, _FakeEngine, _FakeOutput]:
    speech_engine = engine or _FakeEngine()
    audio_output = output or _FakeOutput()
    service = SpeechService(VOICES)
    return (
        SpeechController(speech_engine, service, audio_output),
        speech_engine,
        audio_output,
    )


def _wait_for_workers(controller: SpeechController, qapp: QCoreApplication) -> None:
    for worker in tuple(controller._workers):
        assert worker.wait(2000)
    qapp.processEvents()


def test_start_uses_selected_voice_and_speed_then_finishes_from_audio_event(
    qapp: QCoreApplication,
) -> None:
    controller, engine, output = _controller()
    assert controller.select_voice("es_ES-davefx-medium")
    controller.set_speed(SpeedPreset.FAST)

    assert controller.start("Resultados de la encuesta.")
    _wait_for_workers(controller, qapp)

    assert engine.requests[0].voice_id == "es_ES-davefx-medium"
    assert engine.requests[0].speed is SpeedPreset.FAST
    assert controller.state is PlaybackState.PLAYING
    assert output.received

    output.finished.emit(engine.requests[0].request_id)
    qapp.processEvents()
    assert controller.state is PlaybackState.FINISHED
    controller.shutdown()


def test_empty_text_does_not_start_audio(qapp: QCoreApplication) -> None:
    controller, engine, output = _controller()

    assert not controller.start(" \n ")

    assert engine.requests == []
    assert output.request_id is None
    assert controller.state is PlaybackState.ERROR
    controller.shutdown()


def test_pause_resume_and_stop_control_the_active_request(
    qapp: QCoreApplication,
) -> None:
    controller, _engine, output = _controller()
    assert controller.start("Lectura de prueba")
    _wait_for_workers(controller, qapp)

    assert controller.pause()
    assert controller.state is PlaybackState.PAUSED
    assert output.paused
    assert controller.resume()
    assert controller.state is PlaybackState.PLAYING
    assert not output.paused
    assert controller.stop()
    assert controller.state is PlaybackState.STOPPED
    assert output.stopped
    controller.shutdown()


def test_audio_device_failure_is_recoverable(qapp: QCoreApplication) -> None:
    controller, engine, output = _controller(output=_FakeOutput(fail_begin=True))

    assert not controller.start("Lectura de prueba")

    assert engine.requests == []
    assert controller.state is PlaybackState.ERROR
    assert "No hay dispositivo" in controller._service.error_message
    controller.shutdown()


def test_shutdown_cancels_worker_and_releases_audio_output(
    qapp: QCoreApplication,
) -> None:
    controller, _engine, output = _controller()
    assert controller.start("Lectura de cierre")
    workers = tuple(controller._workers)

    controller.shutdown()

    assert output.stopped
    assert all(not worker.isRunning() for worker in workers)
