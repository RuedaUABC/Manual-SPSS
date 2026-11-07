"""Integration checks for the visible Manual SPSS desktop shell."""

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox

from manual_spss.app import find_content_root, load_manual_pages, main
from manual_spss.ui import ManualWindow, Theme, tokens_for


def _window(content_root: Path) -> ManualWindow:
    return ManualWindow(load_manual_pages(content_root))


def test_chapter_list_and_controls_navigate_content(
    qapp: QApplication,  # noqa: ARG001
) -> None:
    window = _window(Path("content"))
    window.show()

    assert window.chapter_list.count() == 8
    assert window.chapter_list.currentItem().data(window.section_id_role) == "chapter-1"
    assert window.title_label.text() == "Introducción al SPSS"
    assert "SPSS (siglas de" in window.content_browser.toPlainText()
    assert window.settings_button.accessibleName() == "Abrir ajustes"

    window.chapter_list.setFocus()
    QTest.keyClick(window.chapter_list, Qt.Key.Key_Down)
    assert window.chapter_list.currentRow() == 1

    assert window.title_label.text() == "Bases de datos en SPSS"
    assert window.previous_button.isEnabled()

    window.next_button.click()
    assert window.chapter_list.currentRow() == 2
    window.home_button.click()
    assert window.chapter_list.currentRow() == 0
    window.close()


def test_settings_switch_theme_and_return_to_reader(
    qapp: QApplication,  # noqa: ARG001
) -> None:
    window = _window(Path("content"))
    window.settings_button.click()
    assert window.screen_stack.currentWidget() is window.settings_page

    window.appearance_button.click()
    window.dark_theme_button.setFocus()
    QTest.keyClick(window.dark_theme_button, Qt.Key.Key_Space)
    assert window.current_theme is Theme.DARK
    assert "#101010" in window.styleSheet()

    window.light_theme_button.click()
    assert window.current_theme is Theme.LIGHT
    assert "#f3dedd" in window.styleSheet()

    window.credits_button.click()
    assert window.settings_stack.currentIndex() == 2
    assert "cap1y2_SPSS.pdf" in window._credits_text()

    window.return_button.click()
    assert window.screen_stack.currentWidget() is window.reader_page
    window.close()


def test_empty_catalog_explains_state_and_keeps_home_action(
    qapp: QApplication,
) -> None:
    window = ManualWindow(())
    window.show()
    qapp.processEvents()

    assert window.chapter_list.count() == 0
    assert "No hay capítulos" in window.empty_state_label.text()
    assert window.empty_state_label.isVisible()
    assert window.home_button.isEnabled()
    window.close()


def test_reader_reflows_when_crossing_desktop_widths(
    qapp: QApplication,  # noqa: ARG001
) -> None:
    window = _window(Path("content"))
    window.show()
    window.resize(1440, 1024)
    qapp.processEvents()
    assert "font-size:40px" in window.content_browser.toHtml()
    assert 'width="451" height="451"' in window.content_browser.toHtml()
    assert 'width="54%"' in window.content_browser.toHtml()
    assert window.title_label.font().pointSize() == 72
    assert window._workspace_layout.contentsMargins().right() == 49
    assert window._reader_card_layout.contentsMargins().right() == 9
    assert window._reader_footer.isAncestorOf(window.previous_button)
    assert window._reader_footer.isAncestorOf(window.next_button)
    assert not window.reader_card.isAncestorOf(window.next_button)
    assert window.previous_button.mapTo(window.reader_page, QPoint(0, 0)) == QPoint(
        1313, 965
    )
    assert window.next_button.mapTo(window.reader_page, QPoint(0, 0)) == QPoint(
        1363, 965
    )

    window.resize(1024, 768)
    qapp.processEvents()
    assert "font-size:22px" in window.content_browser.toHtml()
    assert 'width="270" height="270"' in window.content_browser.toHtml()
    assert window._workspace_layout.contentsMargins().right() == 16
    assert window._reader_card_layout.contentsMargins().right() == 28
    assert window.chapter_list.currentRow() == 0
    window.close()


def test_audio_player_can_be_collapsed_and_restored_with_mouse_and_keyboard(
    qapp: QApplication,  # noqa: ARG001
) -> None:
    window = _window(Path("content"))
    window.show()
    qapp.processEvents()

    toggle = window.audio_toggle_button
    assert window.audio_preview.isVisible()
    assert toggle.accessibleName() == "Ocultar reproductor de audio"
    assert abs(
        window.audio_preview.geometry().center().x() - window.reader_page.width() // 2
    ) <= 1
    assert abs(
        window.audio_tab.geometry().center().x() - window.reader_page.width() // 2
    ) <= 1

    QTest.mouseClick(toggle, Qt.MouseButton.LeftButton)
    assert not window.audio_preview.isVisible()
    assert window.audio_tab.isVisible()
    assert toggle.accessibleName() == "Mostrar reproductor de audio"

    window.resize(1024, 768)
    qapp.processEvents()
    assert not window.audio_preview.isVisible()
    assert abs(
        window.audio_tab.geometry().center().x() - window.reader_page.width() // 2
    ) <= 1

    toggle.setFocus()
    QTest.keyClick(toggle, Qt.Key.Key_Space)
    assert window.audio_preview.isVisible()
    assert toggle.accessibleName() == "Ocultar reproductor de audio"
    window.close()


def test_catalog_path_can_be_overridden_for_a_future_installer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content_root = Path("content").resolve()
    monkeypatch.setenv("MANUAL_SPSS_CONTENT", str(content_root))

    assert find_content_root() == content_root
    assert all(
        page.base_url and page.base_url.is_file()
        for page in load_manual_pages(content_root)
    )


def test_invalid_catalog_reports_a_recovery_message(
    qapp: QApplication,  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    messages: list[tuple[str, str]] = []
    monkeypatch.setenv("MANUAL_SPSS_CONTENT", str(tmp_path))
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, title, message: messages.append((title, message)),
    )

    assert main() == 1
    assert messages[0][0] == "No se pudo abrir el manual"
    assert "Corrige el catálogo local e inicia de nuevo" in messages[0][1]


def test_application_entrypoint_opens_the_local_reader(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.delenv("MANUAL_SPSS_CONTENT", raising=False)
    monkeypatch.chdir(project_root)
    QTimer.singleShot(20, qapp.quit)

    assert main() == 0
    for widget in QApplication.topLevelWidgets():
        widget.close()


def _contrast_ratio(foreground: str, background: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def test_theme_text_colors_meet_normal_text_contrast() -> None:
    for theme in Theme:
        colors = tokens_for(theme)
        assert _contrast_ratio(colors.text, colors.surface) >= 4.5
        assert _contrast_ratio(colors.sidebar_text, colors.sidebar) >= 4.5
        assert _contrast_ratio(colors.selected_text, colors.selected) >= 4.5
