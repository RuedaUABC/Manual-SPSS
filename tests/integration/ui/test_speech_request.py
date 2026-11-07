"""UI integration coverage for selecting plain text for speech."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QApplication

from manual_spss.app import load_manual_pages
from manual_spss.tts_engine.models import PlaybackState, SpeedPreset, VoiceInfo
from manual_spss.tts_engine.requests import reading_text
from manual_spss.ui import ManualWindow


class _RecordingSpeechController(QObject):
    state_changed = pyqtSignal(object, str, bool)
    progress_changed = pyqtSignal(float)
    voice_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.state = PlaybackState.IDLE
        self.speed = SpeedPreset.NORMAL
        self.read_requests: list[str] = []
        self.voices = (
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
        self.selected_voice_id = self.voices[0].id
        self.previews: list[str] = []

    def start(self, text: str) -> bool:
        self.read_requests.append(text)
        self.state = PlaybackState.STARTING
        self.state_changed.emit(self.state, "", True)
        return True

    def pause(self) -> bool:
        self.state = PlaybackState.PAUSED
        self.state_changed.emit(self.state, "", True)
        return True

    def resume(self) -> bool:
        self.state = PlaybackState.PLAYING
        self.state_changed.emit(self.state, "", True)
        return True

    def stop(self) -> bool:
        self.state = PlaybackState.STOPPED
        self.state_changed.emit(self.state, "", True)
        return True

    def restart(self) -> bool:
        self.state = PlaybackState.STARTING
        self.state_changed.emit(self.state, "", True)
        return True

    def set_speed(self, speed: SpeedPreset) -> None:
        self.speed = speed

    def select_voice(self, voice_id: str) -> bool:
        self.selected_voice_id = voice_id
        self.voice_changed.emit(voice_id)
        return True

    def preview_voice(self, voice_id: str) -> bool:
        self.previews.append(voice_id)
        return True

    def set_volume(self, _volume: float) -> None:
        pass

    def set_muted(self, _muted: bool) -> None:
        pass

    def shutdown(self) -> None:
        pass

def test_reader_selection_request_uses_selected_plain_text(
    qapp: QApplication,
) -> None:
    page = load_manual_pages(Path("content"))[0]
    window = ManualWindow((page,))
    cursor = window.content_browser.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    cursor.movePosition(
        cursor.MoveOperation.NextCharacter,
        QTextCursor.MoveMode.KeepAnchor,
        20,
    )
    window.content_browser.setTextCursor(cursor)
    selected = window.content_browser.textCursor().selectedText()

    text = reading_text(page.plain_text, selected)

    assert text == selected
    assert text != page.plain_text
    assert "<p" not in text
    assert "<article" not in text
    window.close()


def test_audio_player_sends_only_the_current_selection_to_speech_controller(
    qapp: QApplication,
) -> None:
    page = load_manual_pages(Path("content"))[0]
    controller = _RecordingSpeechController()
    window = ManualWindow((page,), speech_controller=controller)  # type: ignore[arg-type]
    cursor = window.content_browser.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    cursor.movePosition(
        cursor.MoveOperation.NextCharacter,
        QTextCursor.MoveMode.KeepAnchor,
        30,
    )
    window.content_browser.setTextCursor(cursor)
    selected = window.content_browser.textCursor().selectedText()

    window.audio_player.play_button.click()

    assert controller.read_requests == [reading_text(page.plain_text, selected)]
    assert controller.read_requests[0] != page.body_html
    assert window.audio_player.pause_button.isEnabled()
    window.close()


def test_voice_settings_selects_and_previews_without_changing_chapter(
    qapp: QApplication,
) -> None:
    pages = load_manual_pages(Path("content"))
    controller = _RecordingSpeechController()
    window = ManualWindow(pages, speech_controller=controller)  # type: ignore[arg-type]
    window.settings_button.click()
    window.voice_settings.voice_combo.setCurrentIndex(1)
    window.voice_settings.preview_button.click()

    assert controller.selected_voice_id == "es_ES-davefx-medium"
    assert controller.previews == ["es_ES-davefx-medium"]
    assert window.chapter_list.currentRow() == 0
    assert window.screen_stack.currentWidget() is window.settings_page
    window.close()


def test_foldable_audio_tab_keeps_playback_state_when_panel_is_hidden(
    qapp: QApplication,
) -> None:
    page = load_manual_pages(Path("content"))[0]
    controller = _RecordingSpeechController()
    window = ManualWindow((page,), speech_controller=controller)  # type: ignore[arg-type]
    window.show()
    qapp.processEvents()
    window.audio_player.play_button.click()

    window.audio_toggle_button.click()
    assert not window.audio_player.isVisible()
    assert controller.state is PlaybackState.STARTING
    window.audio_toggle_button.click()

    assert window.audio_player.isVisible()
    assert controller.state is PlaybackState.STARTING
    window.close()
