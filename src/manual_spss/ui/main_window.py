"""Reusable PyQt6 application shell for the Manual SPSS reader."""

from __future__ import annotations

import re
from collections.abc import Sequence
from html import escape, unescape
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QCloseEvent, QFont, QIcon, QResizeEvent, QShowEvent
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from manual_spss.tts_engine.controller import SpeechController
from manual_spss.tts_engine.models import PlaybackState, SpeedPreset
from manual_spss.tts_engine.requests import reading_text
from manual_spss.ui.audio_player import AudioPlayer
from manual_spss.ui.models import ManualPage
from manual_spss.ui.theme import Theme, stylesheet_for, tokens_for
from manual_spss.ui.voice_settings import VoiceSettings

_ICON_SIZE = 50
_PAGE_ROLE = int(Qt.ItemDataRole.UserRole)


def _asset_path(filename: str) -> Path:
    """Resolve a bundled UI asset from the installed package directory."""
    return Path(__file__).with_name("assets") / filename


class ManualWindow(QMainWindow):
    """Desktop shell with chapter navigation, reader, settings and themes."""

    def __init__(
        self,
        pages: Sequence[ManualPage],
        parent: QWidget | None = None,
        *,
        speech_controller: SpeechController | None = None,
        speech_unavailable_message: str = "",
    ) -> None:
        super().__init__(parent)
        self._pages = tuple(pages)
        self._speech_controller = speech_controller
        self._speech_unavailable_message = speech_unavailable_message
        self._page_positions: dict[str, int] = {}
        self._current_page_id: str | None = None
        self._theme = Theme.LIGHT
        self._font_family = "Segoe UI"

        self.setWindowTitle("Manual SPSS")
        self.setObjectName("manualWindow")
        screen = QApplication.primaryScreen()
        target_size = QSize(1440, 1024)
        if screen is not None:
            available_size = screen.availableGeometry().size()
            self.resize(target_size.boundedTo(available_size))
            self.setMinimumSize(QSize(820, 620).boundedTo(available_size))
        else:
            self.resize(target_size)
            self.setMinimumSize(820, 620)
        self._wide_layout = self.width() >= 1200

        root = QWidget(self)
        root.setObjectName("appRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.screen_stack = QStackedWidget(root)
        self.screen_stack.setObjectName("screenStack")
        root_layout.addWidget(self.screen_stack)

        self.reader_page = self._build_reader_page()
        self.settings_page = self._build_settings_page()
        self.screen_stack.addWidget(self.reader_page)
        self.screen_stack.addWidget(self.settings_page)

        self._populate_chapters()
        self._connect_speech_controller()
        self._apply_theme(Theme.LIGHT)
        if self._pages:
            self.chapter_list.setCurrentRow(0)
        else:
            self.empty_state_label.setVisible(True)
            self.content_browser.setVisible(False)
            self.title_label.setText("Manual SPSS")
        self._resize_title()

    @property
    def current_theme(self) -> Theme:
        """Theme currently applied to all screens."""
        return self._theme

    @property
    def section_id_role(self) -> int:
        """Qt item role holding the stable chapter identifier."""
        return _PAGE_ROLE

    def _build_reader_page(self) -> QWidget:
        reader = QWidget(self)
        reader.setObjectName("readerPage")
        layout = QVBoxLayout(reader)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget(reader)
        header.setFixedHeight(85)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 0)
        header_layout.setSpacing(0)

        self.settings_button = self._icon_button(
            "settings.svg", "Abrir ajustes", "settingsButton"
        )
        self.home_button = self._icon_button(
            "home.svg", "Volver al inicio", "homeButton"
        )
        header_layout.addWidget(self.settings_button, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addStretch(1)
        header_layout.addWidget(self.home_button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(header)

        workspace = QWidget(reader)
        workspace_layout = QHBoxLayout(workspace)
        self._workspace_layout = workspace_layout
        workspace_layout.setContentsMargins(
            0, 0, 49 if self._wide_layout else 16, 0
        )
        workspace_layout.setSpacing(15)

        self.sidebar = QFrame(workspace)
        self.sidebar.setObjectName("readerSidebar")
        self.sidebar.setFixedWidth(160)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(0)

        self.chapter_list = QListWidget(self.sidebar)
        self.chapter_list.setObjectName("chapterList")
        self.chapter_list.setAccessibleName("Capítulos del manual")
        self.chapter_list.setAccessibleDescription(
            "Selecciona un capítulo para mostrar su contenido."
        )
        self.chapter_list.setWordWrap(True)
        self.chapter_list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.chapter_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.chapter_list.setIconSize(self._scaled_icon_size(24))
        self.chapter_list.currentRowChanged.connect(self._select_page)
        sidebar_layout.addWidget(self.chapter_list)
        workspace_layout.addWidget(self.sidebar)

        self.reader_card = QFrame(workspace)
        self.reader_card.setObjectName("readerCard")
        card_layout = QVBoxLayout(self.reader_card)
        self._reader_card_layout = card_layout
        card_layout.setContentsMargins(42, 24, 9 if self._wide_layout else 28, 20)
        card_layout.setSpacing(12)

        self.title_label = QLabel(self.reader_card)
        self.title_label.setObjectName("readerTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setAccessibleName("Título del capítulo")
        card_layout.addWidget(self.title_label)

        self.content_browser = QTextBrowser(self.reader_card)
        self.content_browser.setObjectName("readerBody")
        self.content_browser.setReadOnly(True)
        self.content_browser.setOpenLinks(False)
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.setAccessibleName("Contenido del capítulo")
        card_layout.addWidget(self.content_browser, 1)

        self.empty_state_label = QLabel(
            "No hay capítulos para mostrar. Revisa el catálogo local del manual.",
            self.reader_card,
        )
        self.empty_state_label.setObjectName("emptyState")
        self.empty_state_label.setWordWrap(True)
        self.empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state_label.setAccessibleName("Catálogo sin capítulos")
        self.empty_state_label.hide()
        card_layout.addWidget(self.empty_state_label, 1)

        footer = QWidget(reader)
        footer.setObjectName("readerFooter")
        self._reader_footer = footer
        footer.setFixedHeight(66)
        navigation = QHBoxLayout(footer)
        navigation.setContentsMargins(0, 7, 27, 9)
        navigation.setSpacing(0)
        navigation.addStretch(1)
        self.previous_button = self._icon_button(
            "previous.svg", "Capítulo anterior", "previousButton"
        )
        self.next_button = self._icon_button(
            "next.svg", "Capítulo siguiente", "nextButton"
        )
        self.previous_button.setFixedSize(50, 50)
        self.next_button.setFixedSize(50, 50)
        navigation.addWidget(self.previous_button)
        navigation.addWidget(self.next_button)
        workspace_layout.addWidget(self.reader_card, 1)
        layout.addWidget(workspace, 1)
        layout.addWidget(footer)

        self.audio_player = AudioPlayer(reader)
        self.audio_preview = self.audio_player
        self.audio_tab = QWidget(reader)
        self.audio_tab.setFixedSize(72, 30)
        tab_artwork = QSvgWidget(str(_asset_path("audio-tab.svg")), self.audio_tab)
        tab_artwork.setGeometry(0, 0, 72, 30)
        tab_artwork.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.audio_toggle_button = QToolButton(self.audio_tab)
        self.audio_toggle_button.setObjectName("audioToggleButton")
        self.audio_toggle_button.setCheckable(True)
        self.audio_toggle_button.setChecked(True)
        self.audio_toggle_button.setGeometry(4, 0, 64, 22)
        self.audio_toggle_button.setAccessibleDescription(
            "Cambia la visibilidad del reproductor de audio."
        )
        self.audio_toggle_button.toggled.connect(self._set_audio_player_visible)
        self.audio_player.play_requested.connect(self._play_or_resume)
        self.audio_player.pause_requested.connect(self._pause_reading)
        self.audio_player.stop_requested.connect(self._stop_reading)
        self.audio_player.restart_requested.connect(self._restart_reading)
        self.audio_player.speed_changed.connect(self._set_reading_speed)
        self.audio_player.volume_changed.connect(self._set_reading_volume)
        self.audio_player.mute_toggled.connect(self._set_reading_muted)
        self._set_audio_player_visible(True)
        self.settings_button.clicked.connect(self._open_settings)
        self.home_button.clicked.connect(self._go_home)
        self.previous_button.clicked.connect(self._previous_page)
        self.next_button.clicked.connect(self._next_page)
        return reader

    def _build_settings_page(self) -> QWidget:
        settings = QWidget(self)
        settings.setObjectName("settingsPage")
        layout = QHBoxLayout(settings)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(24)

        self.settings_sidebar = QFrame(settings)
        self.settings_sidebar.setObjectName("settingsSidebar")
        self.settings_sidebar.setMinimumWidth(220)
        self.settings_sidebar.setMaximumWidth(340)
        sidebar_layout = QVBoxLayout(self.settings_sidebar)
        sidebar_layout.setContentsMargins(24, 20, 24, 20)
        sidebar_layout.setSpacing(10)

        settings_title = QLabel("Ajustes", self.settings_sidebar)
        settings_title.setObjectName("settingsTitle")
        settings_title.setFont(QFont(self._font_family, 30, QFont.Weight.Bold))
        settings_title.setStyleSheet("color: white;")
        sidebar_layout.addWidget(settings_title)

        self.settings_stack = QStackedWidget(settings)
        self.settings_stack.setObjectName("settingsContentStack")
        self.voice_button = self._settings_nav_button("Voz")
        self.appearance_button = self._settings_nav_button("Apariencia")
        self.credits_button = self._settings_nav_button(
            "Créditos y derechos\nde autor"
        )
        self.settings_nav_group = QButtonGroup(settings)
        self.settings_nav_group.setExclusive(True)
        for button in (
            self.voice_button,
            self.appearance_button,
            self.credits_button,
        ):
            self.settings_nav_group.addButton(button)
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)
        self.return_button = QPushButton("Volver al manual", self.settings_sidebar)
        self.return_button.setObjectName("returnButton")
        self.return_button.setAccessibleName("Volver al manual")
        self.return_button.setIcon(QIcon(str(_asset_path("return.svg"))))
        self.return_button.setIconSize(QSize(24, 24))
        self.return_button.clicked.connect(self._close_settings)
        sidebar_layout.addWidget(self.return_button)
        layout.addWidget(self.settings_sidebar)

        self.settings_content = QFrame(settings)
        self.settings_content.setObjectName("settingsContent")
        content_layout = QVBoxLayout(self.settings_content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.addWidget(self.settings_stack)
        layout.addWidget(self.settings_content, 1)

        voice_page = self._build_voice_settings_page()
        appearance_page = self._build_appearance_page()
        credits_text = self._credits_text()
        credits_page = self._settings_section(
            "Créditos y derechos de autor",
            "Fuentes y atribuciones declaradas en el catálogo local.",
            credits_text,
        )
        self.settings_stack.addWidget(voice_page)
        self.settings_stack.addWidget(appearance_page)
        self.settings_stack.addWidget(credits_page)

        self.voice_button.clicked.connect(lambda: self._show_settings_section(0))
        self.appearance_button.clicked.connect(lambda: self._show_settings_section(1))
        self.credits_button.clicked.connect(lambda: self._show_settings_section(2))
        self.voice_button.setChecked(True)
        return settings

    def _build_appearance_page(self) -> QWidget:
        page = QWidget(self.settings_stack)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("Apariencia", page)
        title.setObjectName("settingsPageTitle")
        title.setFont(QFont(self._font_family, 36, QFont.Weight.Bold))
        description = QLabel(
            "Ajusta el contraste para leer con más comodidad.", page
        )
        description.setObjectName("settingsDescription")
        description.setWordWrap(True)
        description.setFont(QFont(self._font_family, 15))
        layout.addWidget(title)
        layout.addWidget(description)

        card = QFrame(page)
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(14)
        mode_label = QLabel("Modo de contraste", card)
        mode_label.setFont(QFont(self._font_family, 17, QFont.Weight.Bold))
        card_layout.addWidget(mode_label)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self.light_theme_button = QPushButton("Claro", card)
        self.dark_theme_button = QPushButton("Oscuro", card)
        for button in (self.light_theme_button, self.dark_theme_button):
            button.setObjectName("themeToggle")
            button.setCheckable(True)
            button.setMinimumHeight(48)
            theme_row.addWidget(button, 1)
        self.theme_group = QButtonGroup(card)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.light_theme_button)
        self.theme_group.addButton(self.dark_theme_button)
        self.light_theme_button.clicked.connect(lambda: self._apply_theme(Theme.LIGHT))
        self.dark_theme_button.clicked.connect(lambda: self._apply_theme(Theme.DARK))
        card_layout.addLayout(theme_row)
        layout.addWidget(card)

        preview = QFrame(page)
        preview.setObjectName("settingsCard")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(20, 18, 20, 20)
        preview_layout.setSpacing(8)
        preview_title = QLabel("Vista previa", preview)
        preview_title.setFont(QFont(self._font_family, 17, QFont.Weight.Bold))
        preview_body = QLabel(
            "SPSS organiza información y ayuda a interpretar resultados.", preview
        )
        preview_body.setObjectName("secondaryText")
        preview_body.setWordWrap(True)
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(preview_body)
        layout.addWidget(preview)
        layout.addStretch(1)
        return page

    def _build_voice_settings_page(self) -> QWidget:
        page = QWidget(self.settings_stack)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Voz", page)
        title.setObjectName("settingsPageTitle")
        title.setFont(QFont(self._font_family, 36, QFont.Weight.Bold))
        description = QLabel(
            "Elige una voz española local y escúchala antes de leer el manual.",
            page,
        )
        description.setObjectName("settingsDescription")
        description.setWordWrap(True)
        description.setFont(QFont(self._font_family, 15))

        controller = self._speech_controller
        voices = () if controller is None else controller.voices
        selected_voice_id = (
            None if controller is None else controller.selected_voice_id
        )
        self.voice_settings = VoiceSettings(
            voices,
            selected_voice_id=selected_voice_id,
            unavailable_message=self._speech_unavailable_message,
            parent=page,
        )
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.voice_settings)
        layout.addStretch(1)
        return page

    def _settings_section(self, title: str, description: str, message: str) -> QWidget:
        page = QWidget(self.settings_stack)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        heading = QLabel(title, page)
        heading.setObjectName("settingsPageTitle")
        heading.setFont(QFont(self._font_family, 36, QFont.Weight.Bold))
        subtitle = QLabel(description, page)
        subtitle.setObjectName("settingsDescription")
        subtitle.setWordWrap(True)
        subtitle.setFont(QFont(self._font_family, 15))
        card = QFrame(page)
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        body = QLabel(message, card)
        body.setObjectName("secondaryText")
        body.setWordWrap(True)
        body.setFont(QFont(self._font_family, 15))
        card_layout.addWidget(body)
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _credits_text(self) -> str:
        sources = sorted(
            {
                source
                for page in self._pages
                for source in page.attributions
            }
        )
        if not sources:
            return "El catálogo todavía no contiene atribuciones de fuentes."
        source_lines = "\n".join(f"• {source}" for source in sources)
        return (
            f"{source_lines}\n\nLa licencia se muestra únicamente cuando "
            "está confirmada en la fuente."
        )

    def _connect_speech_controller(self) -> None:
        controller = self._speech_controller
        if controller is None:
            message = self._speech_unavailable_message or (
                "La lectura en voz alta no está disponible en esta instalación."
            )
            self.audio_player.set_state(PlaybackState.ERROR, message)
            return
        controller.state_changed.connect(self._speech_state_changed)
        controller.progress_changed.connect(self.audio_player.set_progress)
        controller.voice_changed.connect(self.voice_settings.select_voice)
        controller.error_occurred.connect(self.voice_settings.set_error)
        self.voice_settings.voice_selected.connect(controller.select_voice)
        self.voice_settings.preview_requested.connect(controller.preview_voice)
        speed_index = self.audio_player.speed_combo.findData(controller.speed)
        if speed_index >= 0:
            self.audio_player.speed_combo.setCurrentIndex(speed_index)

    def _play_or_resume(self) -> None:
        controller = self._speech_controller
        if controller is None:
            self.audio_player.set_state(
                PlaybackState.ERROR,
                self._speech_unavailable_message
                or "La lectura en voz alta no está disponible en esta instalación.",
            )
            return
        if controller.state is PlaybackState.PAUSED:
            controller.resume()
            return
        row = self.chapter_list.currentRow()
        if row < 0 or row >= len(self._pages):
            controller.start("")
            return
        selected_text = self.content_browser.textCursor().selectedText()
        text = reading_text(self._pages[row].plain_text, selected_text)
        if controller.start(text):
            self.audio_player.set_progress(0)

    def _pause_reading(self) -> None:
        if self._speech_controller is not None:
            self._speech_controller.pause()

    def _stop_reading(self) -> None:
        if self._speech_controller is not None:
            self._speech_controller.stop()

    def _restart_reading(self) -> None:
        if self._speech_controller is not None:
            if self._speech_controller.restart():
                self.audio_player.set_progress(0)

    def _set_reading_speed(self, speed: SpeedPreset) -> None:
        if self._speech_controller is not None:
            self._speech_controller.set_speed(speed)

    def _set_reading_volume(self, volume: float) -> None:
        if self._speech_controller is not None:
            self._speech_controller.set_volume(volume)

    def _set_reading_muted(self, muted: bool) -> None:
        if self._speech_controller is not None:
            self._speech_controller.set_muted(muted)

    def _speech_state_changed(
        self, state: PlaybackState, message: str, has_request: bool
    ) -> None:
        self.audio_player.set_state(state, message, has_request=has_request)

    def _populate_chapters(self) -> None:
        for index, page in enumerate(self._pages):
            if index == 0:
                item = QListWidgetItem(page.title)
            else:
                item = QListWidgetItem(QIcon(str(_asset_path("book.svg"))), page.title)
            item.setData(_PAGE_ROLE, page.identifier)
            item.setData(Qt.ItemDataRole.AccessibleTextRole, page.title)
            item.setToolTip(page.title)
            self.chapter_list.addItem(item)

        self._page_positions = {
            page.identifier: position for position, page in enumerate(self._pages)
        }
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(len(self._pages) > 1)
        self.home_button.setEnabled(True)

    def _select_page(self, row: int) -> None:
        if row < 0 or row >= len(self._pages):
            return
        page = self._pages[row]
        if self._current_page_id is not None:
            scrollbar = self.content_browser.verticalScrollBar()
            self._page_positions[self._current_page_id] = (
                scrollbar.value() if scrollbar is not None else 0
            )
        self.title_label.setText(page.title)
        self.content_browser.setAccessibleName(f"Contenido del capítulo {page.title}")
        self._render_page(row, 0)
        self._current_page_id = page.identifier
        scrollbar = self.content_browser.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(self._page_positions.get(page.identifier, 0))
        self.previous_button.setEnabled(row > 0)
        self.next_button.setEnabled(row < len(self._pages) - 1)
        self.empty_state_label.hide()
        self.content_browser.show()

    def _render_page(self, row: int, scroll_position: int) -> None:
        page = self._pages[row]
        self.content_browser.setHtml(self._page_html(page, row))
        document = self.content_browser.document()
        if document is not None:
            document.setDocumentMargin(0)
        if page.base_url is not None and document is not None:
            document.setBaseUrl(QUrl.fromLocalFile(str(page.base_url)))
        scrollbar = self.content_browser.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scroll_position)

    def _page_html(self, page: ManualPage, row: int) -> str:
        colors = tokens_for(self._theme)
        body_html = page.body_html
        wide_layout = self.width() >= 1200
        body_font_size = 40 if wide_layout else 22
        if row == 0:
            logo_url = QUrl.fromLocalFile(str(_asset_path("spss-logo.png"))).toString()
            logo_size = 451 if wide_layout else 270

            def remove_repeated_heading(match: re.Match[str]) -> str:
                heading = re.sub(r"<[^>]+>", "", match.group(1))
                heading_text = " ".join(unescape(heading).split())
                heading_text = re.sub(
                    r"^Cap[ií]tulo\s+\d+\s*:\s*", "", heading_text, flags=re.I
                )
                if heading_text.casefold() == page.title.casefold():
                    return ""
                return match.group(0)

            body_html = re.sub(
                r"<h[1-3]\b[^>]*>(.*?)</h[1-3]>",
                remove_repeated_heading,
                body_html,
                flags=re.I | re.S,
            )
            intro = re.search(r"<p\b[^>]*>.*?</p>", body_html, flags=re.I | re.S)
            if intro is not None:
                logo_html = (
                    f'<img src="{escape(logo_url, quote=True)}" '
                    f'width="{logo_size}" height="{logo_size}" '
                    'alt="Logotipo de SPSS" />'
                )
                intro_text_width = "54%" if wide_layout else "62%"
                intro_logo_width = "46%" if wide_layout else "38%"
                intro_row = (
                    '<table class="intro-layout" width="100%" cellspacing="0" '
                    f'cellpadding="0" border="0"><tr><td width="{intro_text_width}" '
                    'valign="top">'
                    f'{intro.group(0)}</td>'
                    f'<td width="{intro_logo_width}" align="right" '
                    'style="padding-right:7px" '
                    f'valign="top">{logo_html}</td></tr></table>'
                )
                body_html = (
                    body_html[: intro.start()]
                    + intro_row
                    + body_html[intro.end() :]
                )
        return f"""<!doctype html>
        <html><head><meta charset="utf-8"><style>
        body {{ color: {colors.text}; background: {colors.surface};
            font-family: '{self._font_family}', Arial, sans-serif;
            font-size: {body_font_size}px; line-height: 1.45; margin: 0; }}
        table.intro-layout p {{ line-height: 1.2; }}
        h1, h2, h3 {{ color: {colors.text}; line-height: 1.2; }}
        h2 {{ margin-top: 1.25em; font-size: 1.25em; }}
        p, li {{ margin-bottom: 0.8em; }}
        figure {{ margin: 1em 0; text-align: center; }}
        figure img {{ max-width: 100%; height: auto; }}
        figcaption {{ color: {colors.secondary_text}; font-size: 0.8em; }}
        table {{ border-collapse: collapse; }}
        table.intro-layout, table.intro-layout td {{ border: 0; padding: 0; }}
        th, td {{ border: 1px solid {colors.border}; padding: 6px 9px; }}
        </style></head><body>{body_html}</body></html>"""

    def _icon_button(self, filename: str, name: str, object_name: str) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName("iconButton")
        button.setProperty("controlName", object_name)
        button.setAccessibleName(name)
        button.setToolTip(name)
        button.setIcon(QIcon(str(_asset_path(filename))))
        button.setIconSize(self._scaled_icon_size(_ICON_SIZE))
        button.setFixedSize(54, 54)
        return button

    def _settings_nav_button(self, title: str) -> QPushButton:
        button = QPushButton(title, self.settings_sidebar)
        button.setObjectName("settingNavButton")
        button.setCheckable(True)
        button.setAccessibleName(" ".join(title.split()))
        return button

    def _scaled_icon_size(self, size: int) -> QSize:
        return QSize(size, size)

    def _show_settings_section(self, index: int) -> None:
        self.settings_stack.setCurrentIndex(index)

    def _open_settings(self) -> None:
        self.screen_stack.setCurrentWidget(self.settings_page)
        self.voice_button.setFocus(Qt.FocusReason.OtherFocusReason)

    def _close_settings(self) -> None:
        self.screen_stack.setCurrentWidget(self.reader_page)
        self.settings_button.setFocus(Qt.FocusReason.OtherFocusReason)

    def _go_home(self) -> None:
        if self._pages:
            if self.chapter_list.currentRow() == 0:
                scrollbar = self.content_browser.verticalScrollBar()
                if scrollbar is not None:
                    scrollbar.setValue(0)
            else:
                self.chapter_list.setCurrentRow(0)
        self.screen_stack.setCurrentWidget(self.reader_page)

    def _previous_page(self) -> None:
        row = self.chapter_list.currentRow()
        if row > 0:
            self.chapter_list.setCurrentRow(row - 1)

    def _next_page(self) -> None:
        row = self.chapter_list.currentRow()
        if row < len(self._pages) - 1:
            self.chapter_list.setCurrentRow(row + 1)

    def _apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.setStyleSheet(stylesheet_for(theme))
        if hasattr(self, "voice_settings"):
            self.voice_settings.apply_theme(tokens_for(theme))
        self.light_theme_button.setChecked(theme is Theme.LIGHT)
        self.dark_theme_button.setChecked(theme is Theme.DARK)
        row = self.chapter_list.currentRow()
        if 0 <= row < len(self._pages):
            scrollbar = self.content_browser.verticalScrollBar()
            scroll_position = scrollbar.value() if scrollbar is not None else 0
            self._render_page(row, scroll_position)
        self.update()

    def _resize_title(self) -> None:
        if not hasattr(self, "title_label"):
            return
        wide_layout = self.width() >= 1200
        layout_changed = wide_layout != getattr(self, "_wide_layout", wide_layout)
        self._wide_layout = wide_layout
        title_size = 46 if not wide_layout else 72
        self.title_label.setFont(
            QFont(self._font_family, title_size, QFont.Weight.Bold)
        )
        nav_size = 14 if self.width() < 1200 else 16
        for button_name in ("voice_button", "appearance_button", "credits_button"):
            button = getattr(self, button_name, None)
            if button is not None:
                button.setStyleSheet(f"font-size: {nav_size}px;")
        row = self.chapter_list.currentRow()
        if layout_changed and hasattr(self, "_workspace_layout"):
            self._workspace_layout.setContentsMargins(
                0, 0, 49 if wide_layout else 16, 0
            )
            self._reader_card_layout.setContentsMargins(
                42, 24, 9 if wide_layout else 28, 20
            )
        if layout_changed and 0 <= row < len(self._pages):
            scrollbar = self.content_browser.verticalScrollBar()
            scroll_position = scrollbar.value() if scrollbar is not None else 0
            self._render_page(row, scroll_position)

    def resizeEvent(self, event: QResizeEvent | None) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._resize_title()
        self._position_audio_preview()

    def showEvent(self, event: QShowEvent | None) -> None:  # noqa: N802
        super().showEvent(event)
        self._position_audio_preview()

    def closeEvent(self, event: QCloseEvent | None) -> None:  # noqa: N802
        if self._speech_controller is not None:
            self._speech_controller.shutdown()
        super().closeEvent(event)

    def _position_audio_preview(self) -> None:
        if not hasattr(self, "audio_preview"):
            return
        self.audio_preview.move((self.reader_page.width() - 528) // 2, 0)
        self.audio_preview.raise_()
        self.audio_tab.move((self.reader_page.width() - 72) // 2, 77)
        self.audio_tab.raise_()

    def _set_audio_player_visible(self, visible: bool) -> None:
        """Show the audio panel while keeping its tab available as a toggle."""
        self.audio_preview.setVisible(visible)
        action = "Ocultar" if visible else "Mostrar"
        accessible_name = f"{action} reproductor de audio"
        self.audio_toggle_button.setAccessibleName(accessible_name)
        self.audio_toggle_button.setToolTip(accessible_name)
