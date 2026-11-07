"""Tests for offline Spanish voice selection and previews."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from manual_spss.tts_engine.models import VoiceInfo
from manual_spss.ui.theme import Theme, tokens_for
from manual_spss.ui.voice_settings import VoiceSettings


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def voices() -> tuple[VoiceInfo, ...]:
    return (
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


def test_voice_options_show_language_region_and_current_selection(
    voices: tuple[VoiceInfo, ...],
) -> None:
    settings = VoiceSettings(voices, selected_voice_id=voices[1].id)

    assert settings.voice_combo.count() == 2
    assert settings.voice_combo.currentData() == voices[1].id
    assert settings.voice_combo.itemText(0) == "Español (México) — Ald"
    assert settings.voice_combo.itemText(1) == "Español (España) — Davefx"
    assert settings.voice_combo.accessibleName() == "Voz en español"


def test_selection_and_preview_emit_the_chosen_local_voice(
    voices: tuple[VoiceInfo, ...],
) -> None:
    settings = VoiceSettings(voices)
    selected: list[str] = []
    previews: list[str] = []
    settings.voice_selected.connect(selected.append)
    settings.preview_requested.connect(previews.append)

    settings.voice_combo.setCurrentIndex(1)
    settings.preview_button.click()

    assert selected == [voices[1].id]
    assert previews == [voices[1].id]
    assert settings.preview_button.accessibleName() == "Probar la voz seleccionada"


def test_missing_voice_assets_disable_preview_with_explanation() -> None:
    settings = VoiceSettings((), unavailable_message="No hay voces locales")

    assert settings.voice_combo.count() == 0
    assert not settings.voice_combo.isEnabled()
    assert not settings.preview_button.isEnabled()
    assert settings.status_label.text() == "No hay voces locales"


def test_voice_load_failure_can_be_shown_without_disabling_other_actions(
    voices: tuple[VoiceInfo, ...],
) -> None:
    settings = VoiceSettings(voices)

    settings.set_error("No se pudo cargar la voz")

    assert settings.status_label.text() == "No se pudo cargar la voz"
    assert settings.voice_combo.isEnabled()


def test_dark_theme_keeps_native_voice_controls_readable(
    voices: tuple[VoiceInfo, ...],
) -> None:
    settings = VoiceSettings(voices)
    settings.apply_theme(tokens_for(Theme.DARK))

    assert "color: #f2f2f2" in settings.voice_combo.styleSheet()
    assert "background: #242424" in settings.voice_combo.styleSheet()
    assert "color: #1a1a1a" in settings.preview_button.styleSheet()
