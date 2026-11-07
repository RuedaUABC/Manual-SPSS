"""Tests for the interactive reader audio panel."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from manual_spss.tts_engine.models import PlaybackState, SpeedPreset
from manual_spss.ui.audio_player import AudioPlayer


@pytest.fixture(scope="module", autouse=True)
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_audio_player_keeps_figma_geometry_and_accessible_controls() -> None:
    player = AudioPlayer()

    assert player.size().width() == 528
    assert player.size().height() == 78
    assert player.play_button.accessibleName() == "Reproducir lectura"
    assert player.pause_button.accessibleName() == "Pausar lectura"
    assert player.stop_button.accessibleName() == "Detener lectura"
    assert player.restart_button.accessibleName() == "Reiniciar lectura"
    assert player.speed_combo.accessibleName() == "Velocidad de lectura"
    assert player.volume_button.accessibleName() == "Silenciar audio"


def test_controls_emit_actions_and_speed_preset(qapp: QApplication) -> None:
    player = AudioPlayer()
    player.set_state(PlaybackState.PLAYING, has_request=True)
    actions: list[str] = []
    speeds: list[SpeedPreset] = []
    player.play_requested.connect(lambda: actions.append("play"))
    player.pause_requested.connect(lambda: actions.append("pause"))
    player.stop_requested.connect(lambda: actions.append("stop"))
    player.restart_requested.connect(lambda: actions.append("restart"))
    player.speed_changed.connect(speeds.append)

    player.set_state(PlaybackState.PAUSED, has_request=True)
    player.play_button.click()
    player.set_state(PlaybackState.PLAYING, has_request=True)
    player.pause_button.click()
    player.stop_button.click()
    player.restart_button.click()
    player.speed_combo.setCurrentIndex(2)
    qapp.processEvents()

    assert actions == ["play", "pause", "stop", "restart"]
    assert speeds == [SpeedPreset.FAST]


def test_player_reflects_state_and_progress() -> None:
    player = AudioPlayer()
    player.set_state(PlaybackState.PLAYING, has_request=True)
    player.set_progress(0.45)

    assert player.pause_button.isEnabled()
    assert player.stop_button.isEnabled()
    assert player.progress_bar.value() == 45

    player.set_state(PlaybackState.ERROR, "No se pudo cargar la voz")
    assert player.play_button.isEnabled()
    assert not player.pause_button.isEnabled()
    assert "No se pudo cargar" in player.status_label.text()


def test_volume_can_be_muted_and_changed(qapp: QApplication) -> None:
    player = AudioPlayer()
    mute_states: list[bool] = []
    volumes: list[float] = []
    player.mute_toggled.connect(mute_states.append)
    player.volume_changed.connect(volumes.append)

    player.volume_button.click()
    player.volume_slider.setValue(62)
    qapp.processEvents()

    assert mute_states == [True]
    assert volumes[-1] == 0.62
    assert player.volume_button.accessibleName() == "Activar sonido"
