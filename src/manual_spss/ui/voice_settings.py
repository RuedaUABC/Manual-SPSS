"""Settings controls for the installed offline Spanish voices."""

from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from manual_spss.tts_engine.models import VoiceInfo
from manual_spss.ui.theme import Theme, ThemeTokens, tokens_for


class VoiceSettings(QWidget):
    """Select and preview available local Spanish speech models."""

    voice_selected = pyqtSignal(str)
    preview_requested = pyqtSignal(str)

    def __init__(
        self,
        voices: Sequence[VoiceInfo],
        *,
        selected_voice_id: str | None = None,
        unavailable_message: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("voiceSettings")
        self._voices = tuple(voices)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.card = QFrame(self)
        self.card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(12)

        voice_label = QLabel("Voz de lectura", self.card)
        voice_font = voice_label.font()
        voice_font.setBold(True)
        voice_label.setFont(voice_font)
        self.voice_combo = QComboBox(self.card)
        self.voice_combo.setObjectName("spanishVoiceCombo")
        self.voice_combo.setAccessibleName("Voz en español")
        self.voice_combo.setToolTip("Selecciona una voz española local")
        for voice in self._voices:
            self.voice_combo.addItem(voice.display_name, voice.id)
            index = self.voice_combo.count() - 1
            self.voice_combo.setItemData(
                index,
                f"{voice.locale} · Calidad {voice.quality}",
                Qt.ItemDataRole.ToolTipRole,
            )
        if self._voices:
            selected_index = self.voice_combo.findData(selected_voice_id)
            self.voice_combo.setCurrentIndex(max(0, selected_index))
            self.voice_combo.setMinimumHeight(46)
        else:
            self.voice_combo.setPlaceholderText("Voces españolas no disponibles")
            self.voice_combo.setEnabled(False)

        self.preview_button = QPushButton("Probar voz", self.card)
        self.preview_button.setObjectName("voicePreviewButton")
        self.preview_button.setAccessibleName("Probar la voz seleccionada")
        self.preview_button.setToolTip(
            "Reproduce una muestra breve en español sin cambiar de capítulo"
        )
        self.preview_button.setMinimumHeight(44)
        self.preview_button.setEnabled(bool(self._voices))

        description = QLabel(
            "Las voces se procesan en este equipo y están disponibles sin conexión.",
            self.card,
        )
        description.setObjectName("secondaryText")
        description.setWordWrap(True)
        self.status_label = QLabel(self.card)
        self.status_label.setObjectName("voiceStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Estado de la voz seleccionada")
        self.status_label.hide()

        card_layout.addWidget(voice_label)
        card_layout.addWidget(self.voice_combo)
        card_layout.addWidget(description)
        preview_row = QHBoxLayout()
        preview_row.addStretch(1)
        preview_row.addWidget(self.preview_button)
        card_layout.addLayout(preview_row)
        card_layout.addWidget(self.status_label)
        layout.addWidget(self.card)

        self.voice_combo.currentIndexChanged.connect(self._emit_voice_selection)
        self.preview_button.clicked.connect(self._request_preview)
        self.apply_theme(tokens_for(Theme.LIGHT))
        if not self._voices:
            self.set_error(
                unavailable_message
                or "No se encontraron voces españolas locales."
            )

    @property
    def selected_voice_id(self) -> str | None:
        """Return the selected model identifier, if one is installed."""
        voice_id = self.voice_combo.currentData()
        return voice_id if isinstance(voice_id, str) else None

    def select_voice(self, voice_id: str) -> None:
        """Reflect a voice selection made by the speech controller."""
        index = self.voice_combo.findData(voice_id)
        if index >= 0 and index != self.voice_combo.currentIndex():
            self.voice_combo.setCurrentIndex(index)

    def set_error(self, message: str) -> None:
        """Show a recoverable local voice error."""
        self.status_label.setText(message)
        self.status_label.setVisible(bool(message))

    def apply_theme(self, colors: ThemeTokens) -> None:
        """Set explicit colors for native controls in both app themes."""
        self.voice_combo.setStyleSheet(
            "QComboBox {"
            f"color: {colors.text}; background: {colors.card}; "
            f"border: 1px solid {colors.border}; "
            "border-radius: 6px; padding: 8px; }"
            "QComboBox::drop-down { border: 0; width: 24px; }"
            "QComboBox QAbstractItemView {"
            f"color: {colors.text}; background: {colors.card}; "
            f"selection-background-color: {colors.selected}; "
            f"selection-color: {colors.selected_text}; }}"
        )
        button_text = colors.selected_text if colors.accent == "#d4d4d4" else "#ffffff"
        self.preview_button.setStyleSheet(
            "QPushButton#voicePreviewButton {"
            f"color: {button_text}; background: {colors.accent}; "
            f"border: 1px solid {colors.border}; "
            "border-radius: 8px; padding: 9px 18px; font-weight: 600; }"
            "QPushButton#voicePreviewButton:focus {"
            f"border: 2px solid {colors.text}; }}"
            "QPushButton#voicePreviewButton:disabled {"
            f"color: {colors.secondary_text}; background: {colors.card}; }}"
        )
        self.status_label.setStyleSheet(
            f"color: {colors.secondary_text}; background: transparent;"
        )

    def _emit_voice_selection(self, index: int) -> None:
        voice_id = self.voice_combo.itemData(index)
        if isinstance(voice_id, str):
            self.status_label.clear()
            self.status_label.hide()
            self.voice_selected.emit(voice_id)

    def _request_preview(self) -> None:
        voice_id = self.selected_voice_id
        if voice_id is not None:
            self.preview_requested.emit(voice_id)
