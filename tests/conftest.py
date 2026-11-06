"""Fixtures compartidos por las pruebas del proyecto."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def write_content_catalog(tmp_path: Path) -> Any:
    """Create a helper for writing small, valid catalogs in a temporary root."""

    def write_catalog(
        sections: list[dict[str, Any]],
        *,
        manifest_updates: dict[str, Any] | None = None,
    ) -> Path:
        content_root = tmp_path / "content"
        (content_root / "sections").mkdir(parents=True, exist_ok=True)
        (content_root / "assets").mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {
            "schema_version": 1,
            "manual_id": "manual-spss-test",
            "title": "Manual SPSS de prueba",
            "version": "0.1.0",
            "locale": "es-MX",
            "sections": sections,
        }
        if manifest_updates:
            manifest.update(manifest_updates)

        (content_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )

        for section in sections:
            body_path = section.get("body")
            if body_path:
                destination = content_root / body_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    f"<article><h1>{section['title']}</h1>"
                    "<p>Contenido de prueba.</p></article>",
                    encoding="utf-8",
                )
            for resource in section.get("resources", []):
                resource_path = content_root / resource["path"]
                resource_path.parent.mkdir(parents=True, exist_ok=True)
                resource_path.write_bytes(b"test-resource")

        return content_root

    return write_catalog
