"""Fixtures para la interfaz PyQt6 en entornos con o sin pantalla."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Share one Qt application across widget tests."""
    application = QApplication.instance() or QApplication([])
    yield application
    application.quit()
