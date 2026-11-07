"""Offline Piper adapter backed only by the application's local voice assets."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from threading import Event
from typing import Any

from manual_spss.tts_engine.models import AudioChunk, SpeechRequest, VoiceInfo

_DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[3] / "assets/tts/voices/manifest.json"
)
_MAX_BATCH_CHARACTERS = 400
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…])\s+")

VoiceLoader = Callable[[Path, Path], Any]
SynthesisConfigFactory = Callable[..., Any]


class SpeechEngineError(RuntimeError):
    """Raised when a local voice cannot be loaded or used."""


class PiperSpeechEngine:
    """Load and synthesize with explicitly installed local Spanish voices."""

    def __init__(
        self,
        manifest_path: Path = _DEFAULT_MANIFEST,
        *,
        voice_loader: VoiceLoader | None = None,
        synthesis_config_factory: SynthesisConfigFactory | None = None,
    ) -> None:
        self._manifest_path = manifest_path.resolve()
        try:
            manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SpeechEngineError(
                f"No se pudo leer el manifiesto de voces: {self._manifest_path}"
            ) from error
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise SpeechEngineError("El manifiesto de voces no es compatible")
        voices = manifest.get("voices")
        if not isinstance(voices, list):
            raise SpeechEngineError("El manifiesto no contiene voces")
        self._entries = tuple(entry for entry in voices if isinstance(entry, dict))
        self._voice_loader = voice_loader or _load_piper_voice
        self._synthesis_config_factory = (
            synthesis_config_factory or _make_synthesis_config
        )
        self._voice_info: dict[str, VoiceInfo] = {}
        self._voice_cache: dict[str, Any] = {}

    def voices(self) -> tuple[VoiceInfo, ...]:
        """Return only voices with complete, Spanish local assets."""
        if self._voice_info:
            return tuple(self._voice_info.values())

        models_root = self._manifest_path.parent / "models"
        for entry in self._entries:
            try:
                info = self._voice_info_from_entry(entry, models_root)
            except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
                continue
            self._voice_info[info.id] = info
        return tuple(self._voice_info.values())

    def synthesize(
        self, request: SpeechRequest, cancel: Event
    ) -> Iterator[AudioChunk]:
        """Yield bounded signed 16-bit PCM chunks, observing cancellation."""
        info = next(
            (voice for voice in self.voices() if voice.id == request.voice_id), None
        )
        if info is None:
            raise SpeechEngineError(
                f"La voz española {request.voice_id} no está disponible localmente"
            )
        if cancel.is_set():
            return

        try:
            voice = self._voice_cache.get(info.id)
            if voice is None:
                voice = self._voice_loader(info.model_path, info.config_path)
                self._voice_cache[info.id] = voice
            config = self._synthesis_config_factory(
                length_scale=request.speed.piper_length_scale
            )
            for text_batch in _text_batches(request.text):
                if cancel.is_set():
                    return
                for piper_chunk in voice.synthesize(text_batch, syn_config=config):
                    if cancel.is_set():
                        return
                    pcm = piper_chunk.audio_int16_bytes
                    if not pcm:
                        continue
                    yield AudioChunk(
                        pcm=pcm,
                        sample_rate=int(piper_chunk.sample_rate),
                        channels=int(piper_chunk.sample_channels),
                        sample_width=int(piper_chunk.sample_width),
                    )
        except SpeechEngineError:
            raise
        except Exception as error:
            raise SpeechEngineError(
                f"No se pudo cargar o sintetizar con la voz {info.display_name}: "
                f"{error}"
            ) from error

    def _voice_info_from_entry(
        self, entry: dict[str, Any], models_root: Path
    ) -> VoiceInfo:
        voice_id = _required_string(entry, "id")
        locale = _required_string(entry, "locale")
        if not locale.lower().startswith("es-"):
            raise ValueError("Solo se aceptan modelos españoles")
        model_path = _asset_path(entry, "model", models_root)
        config_path = _asset_path(entry, "config", models_root)
        card_path = _asset_path(entry, "model_card", models_root)
        for role, path in (
            ("model", model_path),
            ("config", config_path),
            ("model_card", card_path),
        ):
            asset = entry[role]
            expected_size = asset.get("size_bytes")
            if not path.is_file() or path.stat().st_size != expected_size:
                raise ValueError(f"Falta el recurso local {path}")

        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        language = config_data.get("language", {}).get("code", "")
        if not isinstance(language, str) or language.replace("_", "-").lower() != (
            locale.lower()
        ):
            raise ValueError(f"El modelo {voice_id} no declara idioma {locale}")
        display_name = _required_string(entry, "display_name")
        return VoiceInfo(
            id=voice_id,
            display_name=display_name,
            locale=locale,
            model_path=model_path,
            config_path=config_path,
            quality=str(entry.get("quality", "medium")),
            dataset_license=str(entry.get("dataset_license", "")),
        )


def _required_string(entry: dict[str, Any], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"El manifiesto no contiene {key}")
    return value


def _asset_path(entry: dict[str, Any], role: str, root: Path) -> Path:
    asset = entry.get(role)
    if not isinstance(asset, dict):
        raise ValueError(f"El manifiesto no contiene {role}")
    relative_value = asset.get("path")
    if not isinstance(relative_value, str):
        raise ValueError(f"La ruta del recurso {role} no es válida")
    relative = Path(relative_value)
    root_resolved = root.resolve()
    target = (root_resolved / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(
        root_resolved
    ):
        raise ValueError("La ruta de voz sale de la carpeta local de recursos")
    return target


def _text_batches(text: str) -> Iterator[str]:
    """Split long text into sentence groups capped at 400 characters."""
    sentences = [
        sentence.strip() for sentence in _SENTENCE_BOUNDARY.split(text.strip())
    ]
    current = ""
    for sentence in sentences:
        words = sentence.split()
        for source_word in words:
            word = source_word
            if len(word) > _MAX_BATCH_CHARACTERS:
                if current:
                    yield current
                    current = ""
                while len(word) > _MAX_BATCH_CHARACTERS:
                    yield word[:_MAX_BATCH_CHARACTERS]
                    word = word[_MAX_BATCH_CHARACTERS:]
            candidate = f"{current} {word}".strip()
            if current and len(candidate) > _MAX_BATCH_CHARACTERS:
                yield current
                current = word
            else:
                current = candidate
        if current and sentence.endswith(('.', '!', '?', '…')):
            yield current
            current = ""
    if current:
        yield current


def _load_piper_voice(model_path: Path, config_path: Path) -> Any:
    """Load Piper explicitly in CPU mode from local model/config paths."""
    from piper import PiperVoice

    return PiperVoice.load(
        model_path=model_path,
        config_path=config_path,
        use_cuda=False,
    )


def _make_synthesis_config(**values: Any) -> Any:
    """Build Piper's synthesis options without exposing its type to callers."""
    from piper import SynthesisConfig

    return SynthesisConfig(**values)
