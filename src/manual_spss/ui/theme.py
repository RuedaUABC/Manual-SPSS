"""Design tokens and styles for the Manual SPSS desktop interface."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Theme(StrEnum):
    """Supported appearance modes."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Colors shared by the reader, settings and reusable controls."""

    background: str
    surface: str
    card: str
    sidebar: str
    sidebar_text: str
    selected: str
    selected_text: str
    text: str
    secondary_text: str
    accent: str
    border: str


_TOKENS: dict[Theme, ThemeTokens] = {
    Theme.LIGHT: ThemeTokens(
        background="#f3dedd",
        surface="#fff6f5",
        card="#ffffff",
        sidebar="#7f3f43",
        sidebar_text="#ffffff",
        selected="#fbe3e1",
        selected_text="#5a2528",
        text="#171313",
        secondary_text="#5a2528",
        accent="#a8454d",
        border="#ebd0d0",
    ),
    Theme.DARK: ThemeTokens(
        background="#101010",
        surface="#181818",
        card="#242424",
        sidebar="#1e1e1e",
        sidebar_text="#f2f2f2",
        selected="#d4d4d4",
        selected_text="#1a1a1a",
        text="#f2f2f2",
        secondary_text="#bdbdbd",
        accent="#d4d4d4",
        border="#343434",
    ),
}


def tokens_for(theme: Theme) -> ThemeTokens:
    """Return the immutable palette corresponding to ``theme``."""
    return _TOKENS[theme]


def stylesheet_for(theme: Theme) -> str:
    """Build the app-wide stylesheet from the selected Figma-derived palette."""
    colors = tokens_for(theme)
    return f"""
        QWidget {{
            color: {colors.text};
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
        }}
        QWidget#appRoot {{ background: {colors.background}; }}
        QFrame#readerSidebar, QFrame#settingsSidebar {{
            background: {colors.sidebar};
            border: 0;
            border-radius: 10px;
        }}
        QFrame#readerCard, QFrame#settingsContent {{
            background: {colors.surface};
            border: 0;
            border-radius: 10px;
        }}
        QListWidget#chapterList {{
            background: transparent;
            border: 0;
            outline: 0;
            padding: 4px;
            font-size: 15px;
            font-weight: 600;
        }}
        QListWidget#chapterList::item {{
            color: {colors.sidebar_text};
            border-bottom: 1px solid rgba(255, 255, 255, 0.20);
            border-radius: 8px;
            padding: 10px 5px;
            min-height: 72px;
        }}
        QListWidget#chapterList::item:selected {{
            background: {colors.selected};
            color: {colors.selected_text};
        }}
        QListWidget#chapterList::item:focus {{
            border: 2px solid {colors.accent};
        }}
        QPushButton#iconButton, QToolButton#iconButton {{
            background: transparent;
            border: 2px solid transparent;
            border-radius: 9px;
            padding: 2px;
        }}
        QPushButton#iconButton:hover, QToolButton#iconButton:hover {{
            background: {colors.selected};
        }}
        QPushButton#iconButton:focus, QToolButton#iconButton:focus {{
            border-color: {colors.accent};
        }}
        QToolButton#audioToggleButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 0;
        }}
        QToolButton#audioToggleButton:hover {{
            background: rgba(168, 69, 77, 0.10);
        }}
        QToolButton#audioToggleButton:focus {{
            border: 2px solid {colors.accent};
        }}
        QTextBrowser#readerBody {{
            background: {colors.surface};
            border: 0;
            selection-background-color: {colors.accent};
        }}
        QScrollBar:vertical {{
            width: 14px;
            background: {colors.sidebar};
            border-radius: 7px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            min-height: 40px;
            background: {colors.accent};
            border-radius: 7px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QPushButton#settingNavButton {{
            background: transparent;
            color: {colors.sidebar_text};
            border: 2px solid transparent;
            border-radius: 10px;
            text-align: left;
            padding: 12px 14px;
            min-height: 38px;
            font-size: 16px;
            font-weight: 600;
        }}
        QPushButton#settingNavButton:checked {{
            background: {colors.selected};
            color: {colors.selected_text};
        }}
        QPushButton#settingNavButton:focus {{ border-color: {colors.accent}; }}
        QPushButton#themeToggle {{
            background: {colors.card};
            color: {colors.text};
            border: 1px solid {colors.border};
            border-radius: 9px;
            padding: 12px 16px;
            min-height: 38px;
            font-size: 15px;
            font-weight: 600;
        }}
        QPushButton#returnButton {{
            background: {colors.selected};
            color: {colors.selected_text};
            border: 1px solid {colors.border};
            border-radius: 9px;
            padding: 12px 12px;
            min-height: 38px;
            font-size: 15px;
            font-weight: 600;
        }}
        QPushButton#themeToggle:checked {{
            background: {colors.accent};
            color: {colors.selected_text if theme is Theme.DARK else '#ffffff'};
        }}
        QPushButton#returnButton:hover {{
            background: {colors.accent};
            color: {colors.selected_text if theme is Theme.DARK else '#ffffff'};
        }}
        QPushButton#themeToggle:focus, QPushButton#returnButton:focus {{
            border: 2px solid {colors.accent};
        }}
        QFrame#settingsCard {{
            background: {colors.card};
            border: 1px solid {colors.border};
            border-radius: 12px;
        }}
        QLabel#settingsDescription, QLabel#secondaryText {{
            color: {colors.secondary_text};
        }}
        QLabel#emptyState {{
            background: {colors.card};
            border: 1px dashed {colors.border};
            border-radius: 10px;
            padding: 24px;
        }}
    """
