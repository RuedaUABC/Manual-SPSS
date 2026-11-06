"""Application composition root and executable entry point."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMessageBox

from manual_spss.content_model import ContentError, ManualRepository
from manual_spss.ui import ManualPage, ManualWindow


def find_content_root() -> Path:
    """Find the updateable catalog beside the app or in the project tree."""
    configured = os.environ.get("MANUAL_SPSS_CONTENT")
    if configured:
        root = Path(configured).expanduser().resolve()
        if (root / "manifest.json").is_file():
            return root
        raise FileNotFoundError(
            f"MANUAL_SPSS_CONTENT no contiene manifest.json: {root}"
        )

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    candidates = (
        Path(sys.executable).resolve().parent / "content",
        bundle_root / "content",
        Path.cwd() / "content",
        Path(__file__).resolve().parents[2] / "content",
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "manifest.json").is_file():
            return resolved
    raise FileNotFoundError(
        "No se encontró el catálogo local. Coloca la carpeta content junto al "
        "ejecutable o define MANUAL_SPSS_CONTENT."
    )


def load_manual_pages(content_root: Path) -> tuple[ManualPage, ...]:
    """Validate the catalog, then adapt its chapter records to the UI contract."""
    repository = ManualRepository.load(content_root)
    manifest = json.loads((content_root / "manifest.json").read_text(encoding="utf-8"))
    body_paths: dict[str, Path] = {
        item["id"]: content_root / item["body"]
        for item in manifest["sections"]
    }
    return tuple(
        ManualPage(
            identifier=section.id,
            title=section.title,
            body_html=section.body_html,
            base_url=body_paths[section.id],
            attributions=tuple(
                item.source for item in section.attributions if item.source
            ),
        )
        for section in repository.root_sections()
    )


def main() -> int:
    """Launch the desktop reader and report catalog errors in the UI."""
    application = QApplication.instance()
    if not isinstance(application, QApplication):
        application = QApplication(sys.argv)
    application.setApplicationName("Manual SPSS")
    application.setOrganizationName("Manual SPSS")
    application.setFont(QFont("Segoe UI", 10))
    application.setStyle("Fusion")

    try:
        content_root = find_content_root()
        pages = load_manual_pages(content_root)
    except (ContentError, OSError, ValueError, KeyError, TypeError) as error:
        QMessageBox.critical(
            None,
            "No se pudo abrir el manual",
            f"{error}\n\nCorrige el catálogo local e inicia de nuevo.",
        )
        return 1

    window = ManualWindow(pages)
    window.show()
    return application.exec()
