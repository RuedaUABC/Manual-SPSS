"""Interactive, Figma-sized audio controls for the reader."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QMenu,
    QProgressBar,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from manual_spss.tts_engine.models import PlaybackState, SpeedPreset

_ASSET_DIR = Path(__file__).with_name("assets")


class AudioPlayer(QWidget):
    """Provide keyboard-accessible playback, speed, volume and progress controls."""

    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    restart_requested = pyqtSignal()
    speed_changed = pyqtSignal(object)
    volume_changed = pyqtSignal(float)
    mute_toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("audioPlayer")
        self.setFixedSize(528, 78)
        self.setAccessibleName("Reproductor de audio del manual")

        background = QSvgWidget(str(_ASSET_DIR / "audio-menu.svg"), self)
        background.setGeometry(0, -53, 528, 131)
        background.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        controls_art = QSvgWidget(str(_ASSET_DIR / "audio-controls.svg"), self)
        controls_art.setGeometry(196, 13, 291, 41)
        controls_art.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.speed_combo = QComboBox(self)
        self.speed_combo.setObjectName("audioSpeedCombo")
        self.speed_combo.setGeometry(41, 21, 132, 23)
        self.speed_combo.setAccessibleName("Velocidad de lectura")
        self.speed_combo.setToolTip("Velocidad de lectura")
        for preset in (SpeedPreset.SLOW, SpeedPreset.NORMAL, SpeedPreset.FAST):
            self.speed_combo.addItem(preset.value, preset)
        self.speed_combo.setCurrentIndex(1)
        self.speed_combo.currentIndexChanged.connect(self._emit_speed)
        self.speed_combo.setStyleSheet(
            "QComboBox { color: white; background: #a8454d; border: 0; "
            "border-radius: 11px; padding-left: 9px; font-weight: 600; }"
            "QComboBox::drop-down { border: 0; width: 22px; }"
            "QComboBox QAbstractItemView { background: white; color: #171313; }"
        )

        self.volume_button = self._control_button(
            "volumeButton", "Silenciar audio", 196, 13
        )
        self.volume_button.setCheckable(True)
        self.pause_button = self._control_button(
            "pauseButton", "Pausar lectura", 258, 13
        )
        self.play_button = self._control_button(
            "playButton", "Reproducir lectura", 330, 13
        )
        self.stop_button = self._control_button(
            "stopButton", "Detener lectura", 385, 13
        )
        self.restart_button = self._control_button(
            "restartButton", "Reiniciar lectura", 447, 13
        )
        self.volume_button.clicked.connect(self._toggle_mute)
        self.pause_button.clicked.connect(self.pause_requested)
        self.play_button.clicked.connect(self.play_requested)
        self.stop_button.clicked.connect(self.stop_requested)
        self.restart_button.clicked.connect(self.restart_requested)

        volume_menu = QMenu(self.volume_button)
        volume_container = QWidget(volume_menu)
        volume_layout = QVBoxLayout(volume_container)
        volume_layout.setContentsMargins(12, 8, 12, 8)
        volume_label = QLabel("Volumen", volume_container)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, volume_container)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setAccessibleName("Volumen de lectura")
        self.volume_slider.setToolTip("Volumen de lectura")
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_action = QWidgetAction(volume_menu)
        volume_action.setDefaultWidget(volume_container)
        volume_menu.addAction(volume_action)
        self.volume_button.setMenu(volume_menu)
        self.volume_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.MenuButtonPopup
        )
        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_changed.emit(value / 100)
        )

        self.status_label = QLabel(self)
        self.status_label.setObjectName("audioStatus")
        self.status_label.setGeometry(18, 51, 492, 13)
        self.status_label.setAccessibleName("Estado de lectura en voz alta")
        self.status_label.setStyleSheet(
            "QLabel#audioStatus { color: #7f3f43; font-size: 10px; "
            "background: transparent; }"
        )
        self.status_label.hide()

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setObjectName("audioProgress")
        self.progress_bar.setGeometry(16, 66, 496, 6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("Progreso de lectura en voz alta")
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #b98486; border: 1px solid "
            "rgba(221,239,242,0.7); border-radius: 3px; }"
            "QProgressBar::chunk { background: #2b1517; border-radius: 2px; }"
        )

        self.set_state(PlaybackState.IDLE)
        self.set_volume(1.0)

    def set_state(
        self,
        state: PlaybackState,
        message: str = "",
        *,
        has_request: bool = False,
    ) -> None:
        """Update available controls and the visible state message."""
        active = state in (
            PlaybackState.STARTING,
            PlaybackState.PLAYING,
            PlaybackState.PAUSED,
        )
        self.play_button.setEnabled(
            state
            in (
                PlaybackState.IDLE,
                PlaybackState.PAUSED,
                PlaybackState.STOPPED,
                PlaybackState.FINISHED,
                PlaybackState.ERROR,
            )
        )
        self.pause_button.setEnabled(
            state in (PlaybackState.STARTING, PlaybackState.PLAYING)
        )
        self.stop_button.setEnabled(active)
        self.restart_button.setEnabled(has_request)
        if state is PlaybackState.PAUSED:
            self.play_button.setAccessibleName("Reanudar lectura")
            self.play_button.setToolTip("Reanudar lectura")
        else:
            self.play_button.setAccessibleName("Reproducir lectura")
            self.play_button.setToolTip("Reproducir lectura")

        default_messages = {
            PlaybackState.IDLE: "",
            PlaybackState.STARTING: "Preparando audio…",
            PlaybackState.PLAYING: "Leyendo en voz alta",
            PlaybackState.PAUSED: "Lectura en pausa",
            PlaybackState.STOPPED: "Lectura detenida",
            PlaybackState.FINISHED: "Lectura finalizada",
            PlaybackState.ERROR: "No se pudo iniciar la lectura",
        }
        self.status_label.setText(message or default_messages[state])
        self.status_label.setVisible(bool(self.status_label.text()))
        self.setAccessibleDescription(
            f"Estado de lectura: {self.status_label.text() or 'inactiva'}"
        )

    def set_progress(self, progress: float) -> None:
        """Set informational playback progress between zero and one."""
        self.progress_bar.setValue(round(min(1.0, max(0.0, progress)) * 100))

    def set_volume(self, volume: float) -> None:
        """Reflect the current non-muted volume in the popup slider."""
        self.volume_slider.setValue(round(min(1.0, max(0.0, volume)) * 100))

    def set_muted(self, muted: bool) -> None:
        """Update the volume button's action name and checked state."""
        self.volume_button.setChecked(muted)
        name = "Activar sonido" if muted else "Silenciar audio"
        self.volume_button.setAccessibleName(name)
        self.volume_button.setToolTip(name)

    def _control_button(
        self, object_name: str, accessible_name: str, x: int, y: int
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(object_name)
        button.setGeometry(x, y, 41, 41)
        button.setAccessibleName(accessible_name)
        button.setToolTip(accessible_name)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        button.setStyleSheet(
            "QToolButton { background: transparent; border: 2px solid transparent; "
            "border-radius: 9px; }"
            "QToolButton:hover { background: rgba(168,69,77,0.10); }"
            "QToolButton:focus { border-color: #a8454d; }"
            "QToolButton:disabled { background: transparent; }"
        )
        return button

    def _emit_speed(self, index: int) -> None:
        preset = self.speed_combo.itemData(index)
        if isinstance(preset, SpeedPreset):
            self.speed_changed.emit(preset)

    def _toggle_mute(self) -> None:
        muted = self.volume_button.isChecked()
        self.set_muted(muted)
        self.mute_toggled.emit(muted)
