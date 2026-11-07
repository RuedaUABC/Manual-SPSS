"""Tests for local TTS voice asset preparation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from io import BytesIO
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FETCHER_SPEC = importlib.util.spec_from_file_location(
    "manual_spss_asset_fetcher", _PROJECT_ROOT / "scripts/fetch_tts_assets.py"
)
assert _FETCHER_SPEC is not None and _FETCHER_SPEC.loader is not None
_FETCHER = importlib.util.module_from_spec(_FETCHER_SPEC)
_FETCHER_SPEC.loader.exec_module(_FETCHER)
AssetFetchError = _FETCHER.AssetFetchError
fetch_assets = _FETCHER.fetch_assets


def _write_manifest(root: Path, *, destination: str = "test/model.onnx") -> Path:
    payload = b"small voice model fixture"
    asset = {
        "source_path": "es/es_MX/test/model.onnx",
        "path": destination,
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    manifest = {
        "schema_version": 1,
        "repository": "https://huggingface.co/rhasspy/piper-voices",
        "revision": "0123456789abcdef0123456789abcdef01234567",
        "voices": [
            {
                "id": "es_MX-test-medium",
                "model": asset,
                "config": {**asset, "path": "test/model.onnx.json"},
                "model_card": {**asset, "path": "test/MODEL_CARD"},
            }
        ],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_fetch_assets_downloads_all_files_from_pinned_revision(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(tmp_path)
    payload = b"small voice model fixture"
    requested_urls: list[str] = []

    def open_url(url: str) -> BytesIO:
        requested_urls.append(url)
        return BytesIO(payload)

    fetched = fetch_assets(manifest_path, opener=open_url)

    expected_source = (
        "https://huggingface.co/rhasspy/piper-voices/resolve/"
        "0123456789abcdef0123456789abcdef01234567/es/es_MX/test/model.onnx"
    )
    assert requested_urls == [expected_source] * 3
    assert len(fetched) == 3
    assert (tmp_path / "models/test/model.onnx").read_bytes() == payload
    assert (tmp_path / "models/test/model.onnx.json").read_bytes() == payload
    assert (tmp_path / "models/test/MODEL_CARD").read_bytes() == payload


def test_fetch_assets_does_not_save_a_file_with_the_wrong_hash(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(tmp_path)
    destination = tmp_path / "models/test/model.onnx"

    with pytest.raises(AssetFetchError, match="SHA-256"):
        fetch_assets(
            manifest_path,
            opener=lambda _url: BytesIO(b"x" * len(b"small voice model fixture")),
        )

    assert not destination.exists()


def test_fetch_assets_rejects_paths_outside_the_voice_asset_directory(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(tmp_path, destination="../outside.onnx")

    with pytest.raises(AssetFetchError, match="must stay inside"):
        fetch_assets(manifest_path, opener=lambda _url: BytesIO(b"unused"))
