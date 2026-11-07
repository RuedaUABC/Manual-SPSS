"""Bounded PCM buffering and Qt Multimedia playback output."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Condition, Event, Lock
from time import monotonic
from typing import Any

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

from manual_spss.tts_engine.models import AudioChunk

_PIPER_SAMPLE_RATE = 22050


class AudioOutputError(RuntimeError):
    """Raised when the local audio device cannot play Piper PCM."""


@dataclass(slots=True)
class _QueuedChunk:
    pcm: bytes
    frame_width: int
    offset: int = 0


class BoundedAudioQueue:
    """A thread-safe, bounded queue that rejects audio from stale requests."""

    def __init__(self, *, max_chunks: int = 8, max_bytes: int = 1_048_576) -> None:
        if max_chunks < 1 or max_bytes < 1:
            raise ValueError("La cola de audio debe tener límites positivos")
        self._max_chunks = max_chunks
        self._max_bytes = max_bytes
        self._condition = Condition()
        self._chunks: deque[_QueuedChunk] = deque()
        self._pending_bytes = 0
        self._request_id: int | None = None
        self._format: tuple[int, int, int] | None = None

    @property
    def pending_chunks(self) -> int:
        """Return the number of chunks currently buffered."""
        with self._condition:
            return len(self._chunks)

    @property
    def pending_bytes(self) -> int:
        """Return the number of buffered audio bytes."""
        with self._condition:
            return self._pending_bytes

    @property
    def max_bytes(self) -> int:
        """Return the queue's configured byte limit."""
        return self._max_bytes

    def begin_request(self, request_id: int) -> None:
        """Reset the queue and open it for one request generation."""
        with self._condition:
            self._chunks.clear()
            self._pending_bytes = 0
            self._format = None
            self._request_id = request_id
            self._condition.notify_all()

    def put(
        self,
        request_id: int,
        chunk: AudioChunk,
        cancel: Event,
        *,
        timeout: float | None = None,
    ) -> bool:
        """Wait for capacity and enqueue a chunk for the active request."""
        frame_width = chunk.channels * chunk.sample_width
        chunk_format = (chunk.sample_rate, chunk.channels, chunk.sample_width)
        if len(chunk.pcm) > self._max_bytes:
            raise ValueError("El fragmento supera el límite de la cola de audio")
        deadline = None if timeout is None else monotonic() + timeout
        with self._condition:
            while True:
                if cancel.is_set() or self._request_id != request_id:
                    return False
                if self._format is not None and self._format != chunk_format:
                    raise ValueError("El formato PCM cambió durante la lectura")
                has_capacity = (
                    len(self._chunks) < self._max_chunks
                    and self._pending_bytes + len(chunk.pcm) <= self._max_bytes
                )
                if has_capacity:
                    self._format = chunk_format
                    self._chunks.append(_QueuedChunk(chunk.pcm, frame_width))
                    self._pending_bytes += len(chunk.pcm)
                    self._condition.notify_all()
                    return True
                if deadline is not None:
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        return False
                    self._condition.wait(min(remaining, 0.05))
                else:
                    self._condition.wait(0.05)

    def take(self, max_bytes: int) -> bytes:
        """Read aligned PCM bytes without reordering or dropping frames."""
        if max_bytes <= 0:
            return b""
        with self._condition:
            if not self._chunks:
                return b""
            first = self._chunks[0]
            available = len(first.pcm) - first.offset
            byte_count = min(max_bytes, available)
            byte_count -= byte_count % first.frame_width
            if byte_count <= 0:
                return b""
            start = first.offset
            first.offset += byte_count
            self._pending_bytes -= byte_count
            data = first.pcm[start : start + byte_count]
            if first.offset == len(first.pcm):
                self._chunks.popleft()
            self._condition.notify_all()
            return data

    def is_empty(self) -> bool:
        """Return whether the buffered queue is empty."""
        with self._condition:
            return not self._chunks

    def stop_request(self) -> None:
        """Invalidate the active generation, clear audio and wake producers."""
        with self._condition:
            self._request_id = None
            self._chunks.clear()
            self._pending_bytes = 0
            self._format = None
            self._condition.notify_all()


class QtAudioOutput(QObject):
    """Play bounded 22050 Hz mono PCM through a local QAudioSink."""

    progress_changed = pyqtSignal(int, float)
    finished = pyqtSignal(int)
    error_occurred = pyqtSignal(int, str)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        audio_queue: BoundedAudioQueue | None = None,
        device: Any | None = None,
        sink_factory: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue = audio_queue or BoundedAudioQueue()
        self._device = device
        self._sink_factory = sink_factory or QAudioSink
        self._sink: Any | None = None
        self._stream: Any | None = None
        self._request_id: int | None = None
        self._synthesis_finished = False
        self._finished_emitted = False
        self._total_frames = 0
        self._sample_rate = _PIPER_SAMPLE_RATE
        self._frame_width = 2
        self._target_format = (
            _PIPER_SAMPLE_RATE,
            1,
            QAudioFormat.SampleFormat.Int16,
        )
        self._metrics_lock = Lock()
        self._write_pending = b""
        self._volume = 1.0
        self._muted = False
        self._volume_before_mute = 1.0
        self._paused = False
        self._timer = QTimer(self)
        self._timer.setInterval(10)
        self._timer.timeout.connect(self._pump)

    @property
    def audio_queue(self) -> BoundedAudioQueue:
        """Expose the bounded buffer for worker injection and diagnostics."""
        return self._queue

    def begin_request(self, request_id: int) -> None:
        """Prepare the audio sink and clear data from any previous request."""
        self.stop()
        audio_device = self._device or QMediaDevices.defaultAudioOutput()
        if audio_device.isNull():
            raise AudioOutputError("No hay un dispositivo de salida de audio")
        audio_format = audio_device.preferredFormat()
        sample_width = _sample_width(audio_format.sampleFormat())
        sample_rate = audio_format.sampleRate()
        channels = audio_format.channelCount()
        if sample_width == 0 or sample_rate <= 0 or channels <= 0:
            raise AudioOutputError("El formato del dispositivo de audio no es válido")
        if not audio_device.isFormatSupported(audio_format):
            raise AudioOutputError("El formato preferido de audio no está disponible")

        self._sink = self._sink_factory(audio_device, audio_format, self)
        self._frame_width = sample_width * channels
        self._sample_rate = sample_rate
        self._target_format = (sample_rate, channels, audio_format.sampleFormat())
        self._sink.setBufferSize(sample_rate * self._frame_width // 4)
        self._sink.setVolume(0.0 if self._muted else self._volume)
        self._stream = self._sink.start()
        if self._stream is None:
            self._sink.stop()
            self._sink = None
            raise AudioOutputError("No se pudo abrir el dispositivo de audio")
        self._request_id = request_id
        self._queue.begin_request(request_id)
        self._synthesis_finished = False
        self._finished_emitted = False
        self._total_frames = 0
        self._write_pending = b""
        self._paused = False
        self._timer.start()

    def enqueue(self, request_id: int, chunk: AudioChunk, cancel: Event) -> bool:
        """Add a PCM chunk, blocking the synthesis thread at queue capacity."""
        converted = _convert_chunk(chunk, self._target_format)
        frame_width = converted.channels * converted.sample_width
        max_chunk_bytes = min(65_536, self._queue.max_bytes)
        max_chunk_bytes -= max_chunk_bytes % frame_width
        max_chunk_bytes = max(frame_width, max_chunk_bytes)
        chunk_frames = max_chunk_bytes // frame_width
        for start_frame in range(0, converted.frame_count, chunk_frames):
            end_frame = min(start_frame + chunk_frames, converted.frame_count)
            start_byte = start_frame * frame_width
            end_byte = end_frame * frame_width
            bounded_chunk = AudioChunk(
                pcm=converted.pcm[start_byte:end_byte],
                sample_rate=converted.sample_rate,
                channels=converted.channels,
                sample_width=converted.sample_width,
            )
            accepted = self._queue.put(request_id, bounded_chunk, cancel)
            if not accepted:
                return False
            with self._metrics_lock:
                self._total_frames += bounded_chunk.frame_count
        return True

    def mark_synthesis_finished(self, request_id: int) -> None:
        """Mark a generation complete so playback can signal when drained."""
        if self._request_id == request_id:
            self._synthesis_finished = True

    def pause(self) -> None:
        """Suspend the device while preserving buffered audio."""
        if self._sink is not None and not self._paused:
            self._sink.suspend()
            self._paused = True
            self._timer.stop()

    def resume(self) -> None:
        """Resume the device and continue draining the same queue."""
        if self._sink is not None and self._paused:
            self._sink.resume()
            self._paused = False
            self._timer.start()

    def stop(self) -> None:
        """Stop the device, invalidate queued chunks and clear pending writes."""
        self._timer.stop()
        self._queue.stop_request()
        self._write_pending = b""
        self._request_id = None
        self._synthesis_finished = False
        self._paused = False
        if self._sink is not None:
            self._sink.reset()
            self._sink.stop()
            self._sink.deleteLater()
            self._sink = None
            self._stream = None

    def set_volume(self, volume: float) -> None:
        """Set output volume from zero to one, preserving mute state."""
        self._volume = min(1.0, max(0.0, volume))
        if not self._muted and self._sink is not None:
            self._sink.setVolume(self._volume)
        self._volume_before_mute = self._volume

    def set_muted(self, muted: bool) -> None:
        """Mute output or restore the most recently selected volume."""
        if muted == self._muted:
            return
        self._muted = muted
        if muted:
            self._volume_before_mute = self._volume
        else:
            self._volume = self._volume_before_mute
        if self._sink is not None:
            self._sink.setVolume(0.0 if muted else self._volume)

    def _pump(self) -> None:
        sink = self._sink
        stream = self._stream
        request_id = self._request_id
        if sink is None or stream is None or request_id is None or self._paused:
            return
        bytes_free = max(0, int(sink.bytesFree()))
        if bytes_free >= self._frame_width:
            requested = min(bytes_free, 8192)
            requested -= requested % self._frame_width
            data = self._write_pending or self._queue.take(requested)
            if data:
                written = int(stream.write(data))
                if written < 0:
                    self._raise_output_error(request_id, "Falló la escritura de audio")
                    return
                self._write_pending = data[written:]

        if (
            self._synthesis_finished
            and self._queue.is_empty()
            and not self._write_pending
        ):
            processed_frames = max(
                0,
                int(sink.processedUSecs() * self._sample_rate / 1_000_000),
            )
            with self._metrics_lock:
                total_frames = self._total_frames
            progress = (
                1.0
                if total_frames == 0
                else min(1.0, processed_frames / total_frames)
            )
            self.progress_changed.emit(request_id, progress)
            if progress >= 1.0 and not self._finished_emitted:
                self._finished_emitted = True
                self._timer.stop()
                self.finished.emit(request_id)
        elif self._total_frames:
            processed_frames = max(
                0,
                int(sink.processedUSecs() * self._sample_rate / 1_000_000),
            )
            with self._metrics_lock:
                total_frames = self._total_frames
            self.progress_changed.emit(
                request_id, min(1.0, processed_frames / max(1, total_frames))
            )

    def _raise_output_error(self, request_id: int, message: str) -> None:
        self.stop()
        self.error_occurred.emit(request_id, message)


def _sample_width(sample_format: QAudioFormat.SampleFormat) -> int:
    return {
        QAudioFormat.SampleFormat.UInt8: 1,
        QAudioFormat.SampleFormat.Int16: 2,
        QAudioFormat.SampleFormat.Int32: 4,
        QAudioFormat.SampleFormat.Float: 4,
    }.get(sample_format, 0)


def _convert_chunk(
    chunk: AudioChunk,
    target_format: tuple[int, int, QAudioFormat.SampleFormat],
) -> AudioChunk:
    """Resample Piper mono int16 PCM to a device's preferred PCM format."""
    import numpy as np

    target_rate, target_channels, target_sample_format = target_format
    source = np.frombuffer(chunk.pcm, dtype="<i2").astype(np.float32)
    if target_rate != chunk.sample_rate:
        output_frames = max(1, round(len(source) * target_rate / chunk.sample_rate))
        source_positions = np.arange(len(source), dtype=np.float64)
        target_positions = np.linspace(0, len(source) - 1, output_frames)
        source = np.interp(target_positions, source_positions, source).astype(
            np.float32
        )
    if target_channels != 1:
        source = np.repeat(source[:, None], target_channels, axis=1).reshape(-1)

    target_width = _sample_width(target_sample_format)
    if target_sample_format is QAudioFormat.SampleFormat.UInt8:
        pcm = np.clip((source / 32768 + 1) * 127.5, 0, 255).astype("u1").tobytes()
    elif target_sample_format is QAudioFormat.SampleFormat.Int16:
        pcm = np.clip(source, -32768, 32767).astype("<i2").tobytes()
    elif target_sample_format is QAudioFormat.SampleFormat.Int32:
        pcm = (source * (2**16)).astype("<i4").tobytes()
    elif target_sample_format is QAudioFormat.SampleFormat.Float:
        pcm = (source / 32768).astype("<f4").tobytes()
    else:
        raise AudioOutputError("El formato PCM del dispositivo no está admitido")
    return AudioChunk(
        pcm=pcm,
        sample_rate=target_rate,
        channels=target_channels,
        sample_width=target_width,
    )
