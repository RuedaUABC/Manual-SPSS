"""Integration checks for offline TTS application composition."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from manual_spss.app import create_speech_controller, load_manual_pages
from manual_spss.ui import ManualWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def _write_manifest(root: Path, *, install_assets: bool) -> Path:
    voice_id = "es_MX-test-medium"
    model_path = f"{voice_id}/{voice_id}.onnx"
    config_path = f"{voice_id}/{voice_id}.onnx.json"
    card_path = f"{voice_id}/MODEL_CARD"
    if install_assets:
        voice_root = root / "models" / voice_id
        voice_root.mkdir(parents=True)
        (voice_root / f"{voice_id}.onnx").write_bytes(b"fake model")
        (voice_root / f"{voice_id}.onnx.json").write_text(
            json.dumps({"language": {"code": "es_MX"}}), encoding="utf-8"
        )
        (voice_root / "MODEL_CARD").write_text("Unlicense", encoding="utf-8")
    model_size = (
        (root / "models" / model_path).stat().st_size if install_assets else 10
    )
    config_size = (
        (root / "models" / config_path).stat().st_size if install_assets else 1
    )
    card_size = (
        (root / "models" / card_path).stat().st_size if install_assets else 1
    )
    assets = {
        "model": {"path": model_path, "size_bytes": model_size},
        "config": {"path": config_path, "size_bytes": config_size},
        "model_card": {"path": card_path, "size_bytes": card_size},
    }
    manifest = {
        "schema_version": 1,
        "voices": [
            {
                "id": voice_id,
                "display_name": "Español (México) — Test",
                "locale": "es-MX",
                "quality": "medium",
                "dataset_license": "Unlicense",
                **assets,
            }
        ],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_app_composes_only_installed_voices_without_network(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _write_manifest(tmp_path, install_assets=True)
    requests: list[str] = []

    def reject_network(url: str, **_kwargs: object) -> None:
        requests.append(url)
        raise AssertionError("runtime must not download speech assets")

    monkeypatch.setattr(urllib.request, "urlopen", reject_network)
    controller, error = create_speech_controller(manifest)

    assert error == ""
    assert controller is not None
    assert [voice.id for voice in controller.voices] == ["es_MX-test-medium"]
    assert requests == []
    controller.shutdown()


def test_missing_voice_assets_keep_manual_open_and_explain_recovery(
    qapp: QApplication, tmp_path: Path
) -> None:
    manifest = _write_manifest(tmp_path, install_assets=False)
    controller, error = create_speech_controller(manifest)
    window = ManualWindow(
        load_manual_pages(Path("content")),
        speech_controller=controller,
        speech_unavailable_message=error,
    )

    assert window.chapter_list.count() == 8
    assert window.voice_settings.voice_combo.count() == 0
    assert not window.voice_settings.preview_button.isEnabled()
    assert "voces españolas locales" in window.voice_settings.status_label.text()
    assert "voces españolas locales" in window.audio_player.status_label.text()
    assert error
    window.close()
