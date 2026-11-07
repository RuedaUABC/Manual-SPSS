"""Tests for the TTS session contract and state transitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from manual_spss.tts_engine.models import (
    PlaybackState,
    SpeedPreset,
    VoiceInfo,
)
from manual_spss.tts_engine.service import InvalidTransitionError, SpeechService


@pytest.fixture
def voices() -> tuple[VoiceInfo, ...]:
    return (
        VoiceInfo(
            id="es_MX-ald-medium",
            display_name="Español (México) — Ald",
            locale="es-MX",
            model_path=Path("ald.onnx"),
            config_path=Path("ald.onnx.json"),
        ),
        VoiceInfo(
            id="es_ES-davefx-medium",
            display_name="Español (España) — Davefx",
            locale="es-ES",
            model_path=Path("davefx.onnx"),
            config_path=Path("davefx.onnx.json"),
        ),
    )


def test_start_creates_immutable_spanish_request(voices: tuple[VoiceInfo, ...]) -> None:
    service = SpeechService(voices)

    request = service.start(
        "Análisis de datos.", "es_MX-ald-medium", SpeedPreset.NORMAL
    )

    assert request.text == "Análisis de datos."
    assert request.voice_id == "es_MX-ald-medium"
    assert request.speed is SpeedPreset.NORMAL
    assert request.request_id == 1
    assert service.state is PlaybackState.STARTING
    with pytest.raises(AttributeError):
        request.text = "cambiado"  # type: ignore[misc]


@pytest.mark.parametrize("text", ["", " \n\t "])
def test_start_rejects_empty_text_without_changing_state(
    voices: tuple[VoiceInfo, ...], text: str
) -> None:
    service = SpeechService(voices)

    with pytest.raises(ValueError, match="texto"):
        service.start(text, "es_MX-ald-medium")

    assert service.state is PlaybackState.IDLE


def test_start_rejects_unknown_or_non_spanish_voice(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)

    with pytest.raises(ValueError, match="voz"):
        service.start("Hola", "en_US-voice")

    assert service.state is PlaybackState.IDLE


def test_pause_resume_and_finish_follow_valid_transitions(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)
    request = service.start("Hola", "es_MX-ald-medium")

    assert service.mark_playing(request.request_id)
    service.pause()
    assert service.state is PlaybackState.PAUSED
    service.resume()
    assert service.state is PlaybackState.PLAYING
    assert service.finish(request.request_id)
    assert service.state is PlaybackState.FINISHED


def test_resume_restores_starting_state_if_audio_has_not_started(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)
    service.start("Hola", "es_MX-ald-medium")

    service.pause()
    service.resume()

    assert service.state is PlaybackState.STARTING


def test_invalid_transition_is_reported(voices: tuple[VoiceInfo, ...]) -> None:
    service = SpeechService(voices)

    with pytest.raises(InvalidTransitionError, match="pausar"):
        service.pause()


def test_stop_invalidates_late_worker_events_and_restart_reuses_request(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)
    old_request = service.start(
        "Resumen de resultados", "es_ES-davefx-medium", SpeedPreset.SLOW
    )

    service.stop()
    assert service.state is PlaybackState.STOPPED
    assert not service.mark_playing(old_request.request_id)
    assert not service.finish(old_request.request_id)
    assert not service.fail(old_request.request_id, "error tardío")
    assert service.state is PlaybackState.STOPPED

    new_request = service.restart()

    assert new_request.request_id > old_request.request_id
    assert new_request.text == old_request.text
    assert new_request.voice_id == old_request.voice_id
    assert new_request.speed is old_request.speed
    assert service.state is PlaybackState.STARTING


def test_new_request_makes_previous_worker_events_stale(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)
    old_request = service.start("Primero", "es_MX-ald-medium")
    new_request = service.start("Segundo", "es_ES-davefx-medium")

    assert not service.mark_playing(old_request.request_id)
    assert service.mark_playing(new_request.request_id)
    assert service.state is PlaybackState.PLAYING


def test_worker_failure_sets_recoverable_error_state(
    voices: tuple[VoiceInfo, ...],
) -> None:
    service = SpeechService(voices)
    request = service.start("Hola", "es_MX-ald-medium")

    assert service.fail(request.request_id, "No se pudo cargar el modelo")
    assert service.state is PlaybackState.ERROR
    assert service.error_message == "No se pudo cargar el modelo"

    next_request = service.start("Reintento", "es_MX-ald-medium")
    assert service.state is PlaybackState.STARTING
    assert service.error_message is None
    assert next_request.request_id > request.request_id


def test_speed_presets_map_to_piper_length_scale() -> None:
    assert SpeedPreset.SLOW.piper_length_scale == 1.25
    assert SpeedPreset.NORMAL.piper_length_scale == 1.0
    assert SpeedPreset.FAST.piper_length_scale == 0.8
