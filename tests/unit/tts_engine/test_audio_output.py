"""Tests for the bounded PCM queue used by Qt audio output."""

from __future__ import annotations

from threading import Event, Thread
from typing import Any

import pytest
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtMultimedia import QAudioFormat

from manual_spss.tts_engine.audio_output import (
    BoundedAudioQueue,
    QtAudioOutput,
    _convert_chunk,
)
from manual_spss.tts_engine.models import AudioChunk


def _chunk(value: int, frames: int = 2) -> AudioChunk:
    return AudioChunk(bytes([value, 0]) * frames, sample_rate=22050)


@pytest.fixture(scope="module")
def qapp() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def test_queue_enforces_chunk_and_byte_limits() -> None:
    audio_queue = BoundedAudioQueue(max_chunks=1, max_bytes=8)
    audio_queue.begin_request(1)

    assert audio_queue.put(1, _chunk(1, frames=4), Event())
    assert audio_queue.pending_chunks == 1
    assert audio_queue.pending_bytes == 8
    assert not audio_queue.put(1, _chunk(2), Event(), timeout=0.01)


def test_queue_blocks_producer_until_consumer_frees_space() -> None:
    audio_queue = BoundedAudioQueue(max_chunks=1, max_bytes=16)
    audio_queue.begin_request(1)
    assert audio_queue.put(1, _chunk(1), Event())
    accepted: list[bool] = []

    producer = Thread(
        target=lambda: accepted.append(audio_queue.put(1, _chunk(2), Event()))
    )
    producer.start()
    assert accepted == []

    assert audio_queue.take(4) == b"\x01\x00\x01\x00"
    producer.join(timeout=1)

    assert accepted == [True]
    assert audio_queue.take(4) == b"\x02\x00\x02\x00"


def test_stop_clears_queue_and_rejects_old_request_chunks() -> None:
    audio_queue = BoundedAudioQueue(max_chunks=2, max_bytes=16)
    audio_queue.begin_request(5)
    assert audio_queue.put(5, _chunk(1), Event())

    audio_queue.stop_request()

    assert audio_queue.pending_bytes == 0
    assert not audio_queue.put(5, _chunk(2), Event())
    audio_queue.begin_request(6)
    assert not audio_queue.put(5, _chunk(3), Event())
    assert audio_queue.put(6, _chunk(4), Event())


def test_cancellation_releases_a_blocked_producer() -> None:
    audio_queue = BoundedAudioQueue(max_chunks=1, max_bytes=8)
    audio_queue.begin_request(1)
    assert audio_queue.put(1, _chunk(1, frames=4), Event())
    cancelled = Event()
    accepted: list[bool] = []
    producer = Thread(
        target=lambda: accepted.append(audio_queue.put(1, _chunk(2), cancelled))
    )
    producer.start()

    cancelled.set()
    producer.join(timeout=1)

    assert accepted == [False]


def test_partial_reads_preserve_frame_alignment_and_chunk_order() -> None:
    audio_queue = BoundedAudioQueue(max_chunks=2, max_bytes=16)
    audio_queue.begin_request(1)
    assert audio_queue.put(1, _chunk(1, frames=3), Event())
    assert audio_queue.put(1, _chunk(2, frames=2), Event())

    assert audio_queue.take(3) == b"\x01\x00"
    assert audio_queue.take(4) == b"\x01\x00\x01\x00"
    assert audio_queue.take(8) == b"\x02\x00\x02\x00"
    assert audio_queue.pending_bytes == 0


def test_pcm_conversion_resamples_and_duplicates_mono_into_stereo() -> None:
    output_format = (44100, 2, QAudioFormat.SampleFormat.Int16)

    converted = _convert_chunk(
        AudioChunk(b"\xe8\x03\x18\xfc", sample_rate=22050), output_format
    )

    assert converted.sample_rate == 44100
    assert converted.channels == 2
    assert converted.frame_count == 4
    assert len(converted.pcm) == 16


class _FakeDevice:
    def __init__(self) -> None:
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(44100)
        self.audio_format.setChannelCount(2)
        self.audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

    def isNull(self) -> bool:
        return False

    def preferredFormat(self) -> QAudioFormat:
        return self.audio_format

    def isFormatSupported(self, _audio_format: QAudioFormat) -> bool:
        return True


class _FakeStream:
    def __init__(self) -> None:
        self.written = bytearray()

    def write(self, data: bytes) -> int:
        self.written.extend(data)
        return len(data)


class _FakeSink:
    def __init__(self, audio_format: QAudioFormat) -> None:
        self.stream = _FakeStream()
        self.volume = 1.0
        self.suspended = False
        self.processed_us = 0
        self.stopped = False

    def setBufferSize(self, _size: int) -> None:
        pass

    def setVolume(self, volume: float) -> None:
        self.volume = volume

    def start(self) -> _FakeStream:
        return self.stream

    def bytesFree(self) -> int:
        return 4096

    def processedUSecs(self) -> int:
        return self.processed_us

    def suspend(self) -> None:
        self.suspended = True

    def resume(self) -> None:
        self.suspended = False

    def reset(self) -> None:
        pass

    def stop(self) -> None:
        self.stopped = True

    def deleteLater(self) -> None:
        pass


def test_qt_output_controls_volume_pause_and_playback_progress(
    qapp: QCoreApplication,
) -> None:
    assert qapp is not None
    sinks: list[_FakeSink] = []

    def make_sink(_device: Any, audio_format: QAudioFormat, _parent: Any) -> _FakeSink:
        sink = _FakeSink(audio_format)
        sinks.append(sink)
        return sink

    output = QtAudioOutput(device=_FakeDevice(), sink_factory=make_sink)
    output.begin_request(7)
    sink = sinks[0]
    chunk = AudioChunk(b"\x00\x00" * 2, sample_rate=22050)
    assert output.enqueue(7, chunk, Event())

    output.pause()
    assert sink.suspended
    output.resume()
    assert not sink.suspended
    output.set_volume(0.35)
    output.set_muted(True)
    assert sink.volume == 0.0
    output.set_volume(0.7)
    output.set_muted(False)
    assert sink.volume == 0.7

    finished: list[int] = []
    output.finished.connect(finished.append)
    output.mark_synthesis_finished(7)
    output._pump()
    sink.processed_us = 100
    output._pump()

    assert len(sink.stream.written) == 16
    assert finished == [7]
    output.stop()
    assert sink.stopped
