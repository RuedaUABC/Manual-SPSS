"""Reusable PyQt6 application shell for the Manual SPSS reader."""

from __future__ import annotations

import re
from collections.abc import Sequence
from html import escape, unescape
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QFont, QIcon, QResizeEvent, QShowEvent
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

from manual_spss.ui.models import ManualPage
from manual_spss.ui.theme import Theme, stylesheet_for, tokens_for

_ICON_SIZE = 50
_PAGE_ROLE = int(Qt.ItemDataRole.UserRole)


def _asset_path(filename: str) -> Path:
    """Resolve a bundled UI asset from the installed package directory."""
    return Path(__file__).with_name("assets") / filename


class _AudioPreview(QWidget):
    """Non-interactive preview of the audio controls until the TTS module lands."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(528, 100)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName(
            "Controles de audio. Se habilitarán al integrar la lectura en voz alta."
        )
        self.setToolTip("Los controles de audio se habilitarán con el motor de voz")

        background = QSvgWidget(str(_asset_path("audio-menu.svg")), self)
        background.setGeometry(0, -53, 528, 131)

        speed = QFrame(self)
        speed.setObjectName("audioSpeed")
        speed.setGeometry(41, 21, 132, 23)
        speed.setStyleSheet(
            "QFrame#audioSpeed { background: #a8454d; border-radius: 12px; }"
            "QLabel { color: white; font-size: 14px; font-weight: 600; }"
        )
        speed_layout = QHBoxLayout(speed)
        speed_layout.setContentsMargins(6, 0, 6, 0)
        speed_layout.setSpacing(18)
        speed_toggle = QSvgWidget(str(_asset_path("audio-speed-toggle.svg")))
        speed_toggle.setFixedSize(10, 10)
        speed_layout.addWidget(speed_toggle)
        speed_label = QLabel("x1.0")
        speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        speed_layout.addWidget(speed_label)

        controls = QSvgWidget(str(_asset_path("audio-controls.svg")), self)
        controls.setGeometry(196, 13, 291, 41)

        progress_track = QFrame(self)
        progress_track.setGeometry(16, 66, 496, 6)
        progress_track.setStyleSheet(
            "background: #b98486; border: 1px solid rgba(221,239,242,0.7);"
            "border-radius: 3px;"
        )
        progress_fill = QFrame(self)
        progress_fill.setGeometry(16, 66, 11, 6)
        progress_fill.setStyleSheet(
            "background: #2b1517; border: 1px solid rgba(221,239,242,0.7);"
            "border-radius: 3px;"
        )

        audio_tab = QSvgWidget(str(_asset_path("audio-tab.svg")), self)
        audio_tab.setGeometry(228, 77, 72, 30)


class ManualWindow(QMainWindow):
    """Desktop shell with chapter navigation, reader, settings and themes."""

    def __init__(
        self,
        pages: Sequence[ManualPage],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pages = tuple(pages)
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
        layout.setContentsMargins(0, 0, 0, 10)
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
        workspace_layout.setContentsMargins(0, 0, 16, 0)
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
        card_layout.setContentsMargins(42, 24, 28, 20)
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

        navigation = QHBoxLayout()
        navigation.addStretch(1)
        self.previous_button = self._icon_button(
            "previous.svg", "Capítulo anterior", "previousButton"
        )
        self.next_button = self._icon_button(
            "next.svg", "Capítulo siguiente", "nextButton"
        )
        navigation.addWidget(self.previous_button)
        navigation.addWidget(self.next_button)
        card_layout.addLayout(navigation)
        workspace_layout.addWidget(self.reader_card, 1)
        layout.addWidget(workspace, 1)

        self.audio_preview = _AudioPreview(reader)
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

        voice_page = self._settings_section(
            "Voz",
            "Elige cómo se lee el manual en voz alta.",
            "La interfaz está preparada. La selección de voz y reproducción se "
            "habilitarán al integrar el motor de voz.",
        )
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
        if page.base_url is not None and document is not None:
            document.setBaseUrl(QUrl.fromLocalFile(str(page.base_url)))
        scrollbar = self.content_browser.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scroll_position)

    def _page_html(self, page: ManualPage, row: int) -> str:
        colors = tokens_for(self._theme)
        body_html = page.body_html
        body_font_size = 30 if self.width() >= 1200 else 22
        if row == 0:
            logo_url = QUrl.fromLocalFile(str(_asset_path("spss-logo.png"))).toString()
            logo_size = 380 if self.width() >= 1200 else 270

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
                intro_row = (
                    '<table class="intro-layout" width="100%" cellspacing="0" '
                    'cellpadding="8" border="0"><tr><td width="62%" valign="top">'
                    f'{intro.group(0)}</td><td width="38%" align="center" '
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
            font-size: {body_font_size}px; line-height: 1.45; }}
        h1, h2, h3 {{ color: {colors.text}; line-height: 1.2; }}
        h2 {{ margin-top: 1.25em; font-size: 1.25em; }}
        p, li {{ margin-bottom: 0.8em; }}
        figure {{ margin: 1em 0; text-align: center; }}
        figure img {{ max-width: 100%; height: auto; }}
        figcaption {{ color: {colors.secondary_text}; font-size: 0.8em; }}
        table {{ border-collapse: collapse; }}
        table.intro-layout, table.intro-layout td {{ border: 0; }}
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
        title_size = 46 if not wide_layout else 60
        self.title_label.setFont(
            QFont(self._font_family, title_size, QFont.Weight.Bold)
        )
        nav_size = 14 if self.width() < 1200 else 16
        for button_name in ("voice_button", "appearance_button", "credits_button"):
            button = getattr(self, button_name, None)
            if button is not None:
                button.setStyleSheet(f"font-size: {nav_size}px;")
        row = self.chapter_list.currentRow()
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

    def _position_audio_preview(self) -> None:
        if not hasattr(self, "audio_preview"):
            return
        self.audio_preview.move((self.reader_page.width() - 528) // 2, 0)
        self.audio_preview.raise_()
