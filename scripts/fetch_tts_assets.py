"""Prepare the pinned offline Piper voices for development or packaging."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import IO, Any
from urllib.parse import urlsplit

_DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1] / "assets/tts/voices/manifest.json"
)
_ASSET_ROLES = ("model", "config", "model_card")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_CHUNK_SIZE = 1024 * 1024

Response = AbstractContextManager[IO[bytes]]
URLOpener = Callable[[str], Response]


class AssetFetchError(RuntimeError):
    """Raised when local TTS assets are missing, invalid, or unsafe."""


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssetFetchError(f"Cannot read TTS asset manifest: {path}") from error

    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise AssetFetchError("Unsupported TTS asset manifest schema")
    repository = manifest.get("repository")
    revision = manifest.get("revision")
    voices = manifest.get("voices")
    if (
        not isinstance(repository, str)
        or urlsplit(repository).scheme != "https"
        or not isinstance(revision, str)
        or not _REVISION_PATTERN.fullmatch(revision)
        or not isinstance(voices, list)
        or not voices
    ):
        raise AssetFetchError("TTS asset manifest has invalid repository metadata")

    voice_ids: set[str] = set()
    for voice in voices:
        if not isinstance(voice, dict):
            raise AssetFetchError("Each voice entry must be an object")
        voice_id = voice.get("id")
        if not isinstance(voice_id, str) or not voice_id or voice_id in voice_ids:
            raise AssetFetchError("Voice IDs must be nonempty and unique")
        voice_ids.add(voice_id)
        for role in _ASSET_ROLES:
            asset = voice.get(role)
            if not isinstance(asset, dict):
                raise AssetFetchError(f"Voice {voice_id} has no {role} asset")
            source_path = asset.get("source_path")
            relative_path = asset.get("path")
            checksum = asset.get("sha256")
            size_bytes = asset.get("size_bytes")
            if not isinstance(source_path, str) or not isinstance(relative_path, str):
                raise AssetFetchError(f"Voice {voice_id} has an invalid {role} path")
            if not _SHA256_PATTERN.fullmatch(str(checksum)):
                raise AssetFetchError(f"Voice {voice_id} has an invalid {role} SHA-256")
            if (
                isinstance(size_bytes, bool)
                or not isinstance(size_bytes, int)
                or size_bytes < 1
            ):
                raise AssetFetchError(f"Voice {voice_id} has an invalid {role} size")
            _safe_relative_path(source_path, Path("."))
            _safe_relative_path(relative_path, path.parent / "models")
    return manifest


def _safe_relative_path(value: str, root: Path) -> Path:
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise AssetFetchError("Voice asset paths must stay inside the models directory")
    root_resolved = root.resolve()
    target = (root_resolved / relative).resolve()
    if not target.is_relative_to(root_resolved):
        raise AssetFetchError("Voice asset paths must stay inside the models directory")
    return target


def _is_valid_file(path: Path, *, size_bytes: int, sha256: str) -> bool:
    if not path.is_file() or path.stat().st_size != size_bytes:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as asset_file:
        for chunk in iter(lambda: asset_file.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest() == sha256


def _download_file(
    url: str,
    destination: Path,
    *,
    size_bytes: int,
    sha256: str,
    opener: URLOpener,
) -> None:
    temporary_path: Path | None = None
    digest = hashlib.sha256()
    bytes_written = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with opener(url) as response:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".part",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                while chunk := response.read(_CHUNK_SIZE):
                    bytes_written += len(chunk)
                    if bytes_written > size_bytes:
                        raise AssetFetchError(
                            f"Unexpected size while downloading {url}"
                        )
                    digest.update(chunk)
                    temporary_file.write(chunk)
        if bytes_written != size_bytes:
            raise AssetFetchError(f"Unexpected size while downloading {url}")
        if digest.hexdigest() != sha256:
            raise AssetFetchError(f"SHA-256 mismatch while downloading {url}")
        os.replace(temporary_path, destination)
        temporary_path = None
    except OSError as error:
        raise AssetFetchError(f"Cannot download TTS asset: {url}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def fetch_assets(
    manifest_path: Path = _DEFAULT_MANIFEST,
    *,
    opener: URLOpener | None = None,
) -> tuple[Path, ...]:
    """Download the manifest's assets and verify each size and SHA-256."""
    manifest_path = manifest_path.resolve()
    manifest = _load_manifest(manifest_path)
    repository = str(manifest["repository"]).rstrip("/")
    revision = str(manifest["revision"])
    models_root = manifest_path.parent / "models"
    open_url = opener or (
        lambda url: urllib.request.urlopen(url, timeout=60)  # noqa: S310
    )
    fetched: list[Path] = []

    for voice in manifest["voices"]:
        for role in _ASSET_ROLES:
            asset = voice[role]
            source_relative = str(asset["source_path"])
            _safe_relative_path(source_relative, Path("."))
            destination = _safe_relative_path(str(asset["path"]), models_root)
            expected_size = int(asset["size_bytes"])
            expected_hash = str(asset["sha256"])
            url = (
                f"{repository}/resolve/{revision}/"
                f"{Path(source_relative).as_posix()}"
            )
            if not _is_valid_file(
                destination, size_bytes=expected_size, sha256=expected_hash
            ):
                _download_file(
                    url,
                    destination,
                    size_bytes=expected_size,
                    sha256=expected_hash,
                    opener=open_url,
                )
            fetched.append(destination)
    return tuple(fetched)


def main() -> int:
    """Run the developer-only asset preparation command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=_DEFAULT_MANIFEST,
        help="Voice manifest to prepare",
    )
    args = parser.parse_args()
    try:
        paths = fetch_assets(args.manifest)
    except AssetFetchError as error:
        parser.exit(1, f"error: {error}\n")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
