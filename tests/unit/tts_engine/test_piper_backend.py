"""Tests for the local Piper adapter using a fake Piper runtime."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import Any

import pytest

from manual_spss.tts_engine.models import AudioChunk, SpeechRequest, SpeedPreset
from manual_spss.tts_engine.piper_backend import (
    PiperSpeechEngine,
    SpeechEngineError,
    _text_batches,
)

VOICE_ID = "es_MX-ald-medium"


def _make_manifest(root: Path, *, language: str = "es_MX") -> Path:
    voice_root = root / "models" / VOICE_ID
    voice_root.mkdir(parents=True)
    (voice_root / f"{VOICE_ID}.onnx").write_bytes(b"fake onnx")
    (voice_root / f"{VOICE_ID}.onnx.json").write_text(
        json.dumps({"language": {"code": language}, "audio": {"quality": "medium"}}),
        encoding="utf-8",
    )
    (voice_root / "MODEL_CARD").write_text("License: Unlicense", encoding="utf-8")

    assets = {
        "model": {"path": f"{VOICE_ID}/{VOICE_ID}.onnx", "size_bytes": 9},
        "config": {
            "path": f"{VOICE_ID}/{VOICE_ID}.onnx.json",
            "size_bytes": (voice_root / f"{VOICE_ID}.onnx.json").stat().st_size,
        },
        "model_card": {
            "path": f"{VOICE_ID}/MODEL_CARD",
            "size_bytes": (voice_root / "MODEL_CARD").stat().st_size,
        },
    }
    manifest = {
        "schema_version": 1,
        "voices": [
            {
                "id": VOICE_ID,
                "display_name": "Español (México) — Ald",
                "locale": "es-MX",
                "quality": "medium",
                "dataset_license": "Unlicense",
                **assets,
            }
        ],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


class _FakeVoice:
    def __init__(self, chunks: tuple[SimpleNamespace, ...]) -> None:
        self.chunks = chunks
        self.configs: list[Any] = []
        self.texts: list[str] = []

    def synthesize(self, text: str, syn_config: Any) -> tuple[SimpleNamespace, ...]:
        self.texts.append(text)
        self.configs.append(syn_config)
        return self.chunks


def _audio_chunk(payload: bytes = b"\x01\x00\x02\x00") -> SimpleNamespace:
    return SimpleNamespace(
        audio_int16_bytes=payload,
        sample_rate=22050,
        sample_channels=1,
        sample_width=2,
    )


def test_lists_only_installed_spanish_voice_with_valid_config(
    tmp_path: Path,
) -> None:
    engine = PiperSpeechEngine(_make_manifest(tmp_path))

    voices = engine.voices()

    assert len(voices) == 1
    assert voices[0].id == VOICE_ID
    assert voices[0].locale == "es-MX"
    assert voices[0].model_path.is_file()
    assert voices[0].config_path.is_file()
    assert voices[0].dataset_license == "Unlicense"


def test_omits_voice_when_local_config_is_not_spanish(tmp_path: Path) -> None:
    engine = PiperSpeechEngine(_make_manifest(tmp_path, language="en_US"))

    assert engine.voices() == ()


def test_synthesize_maps_piper_chunks_to_contract_and_speed(
    tmp_path: Path,
) -> None:
    piper_chunk = _audio_chunk()
    fake_voice = _FakeVoice((piper_chunk,))
    loads: list[tuple[Path, Path]] = []

    def load_voice(model_path: Path, config_path: Path) -> _FakeVoice:
        loads.append((model_path, config_path))
        return fake_voice

    engine = PiperSpeechEngine(
        _make_manifest(tmp_path),
        voice_loader=load_voice,
        synthesis_config_factory=lambda **values: values,
    )
    request = SpeechRequest(1, "Análisis de datos.", VOICE_ID, SpeedPreset.FAST)

    chunks = tuple(engine.synthesize(request, Event()))

    assert chunks == (AudioChunk(b"\x01\x00\x02\x00", 22050),)
    assert len(loads) == 1
    assert fake_voice.texts == [request.text]
    assert fake_voice.configs == [{"length_scale": 0.8}]


def test_missing_model_is_reported_without_fallback(tmp_path: Path) -> None:
    manifest_path = _make_manifest(tmp_path)
    (tmp_path / "models" / VOICE_ID / f"{VOICE_ID}.onnx").unlink()
    engine = PiperSpeechEngine(manifest_path)

    assert engine.voices() == ()
    with pytest.raises(SpeechEngineError, match="no está disponible"):
        tuple(
            engine.synthesize(
                SpeechRequest(1, "Hola", VOICE_ID, SpeedPreset.NORMAL), Event()
            )
        )


def test_load_failure_is_recoverable_and_does_not_try_another_voice(
    tmp_path: Path,
) -> None:
    calls: list[Path] = []

    def fail_to_load(model_path: Path, _config_path: Path) -> Any:
        calls.append(model_path)
        raise RuntimeError("bad onnx")

    engine = PiperSpeechEngine(
        _make_manifest(tmp_path),
        voice_loader=fail_to_load,
        synthesis_config_factory=lambda **values: values,
    )

    with pytest.raises(SpeechEngineError, match="No se pudo cargar"):
        tuple(
            engine.synthesize(
                SpeechRequest(1, "Hola", VOICE_ID, SpeedPreset.NORMAL), Event()
            )
        )

    assert len(calls) == 1


def test_cancel_event_stops_before_next_sentence_chunk(tmp_path: Path) -> None:
    cancel = Event()
    fake_voice = _FakeVoice((_audio_chunk(), _audio_chunk(b"\x03\x00")))
    engine = PiperSpeechEngine(
        _make_manifest(tmp_path),
        voice_loader=lambda _model, _config: fake_voice,
        synthesis_config_factory=lambda **values: values,
    )
    request = SpeechRequest(1, "Hola. Después", VOICE_ID, SpeedPreset.NORMAL)
    chunks = engine.synthesize(request, cancel)

    assert next(chunks).pcm
    cancel.set()
    assert tuple(chunks) == ()


def test_text_batches_keep_even_a_single_long_token_bounded() -> None:
    text = "a" * 901

    batches = tuple(_text_batches(text))

    assert all(0 < len(batch) <= 400 for batch in batches)
    assert "".join(batches) == text
