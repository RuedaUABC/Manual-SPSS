"""Tests for UI-facing content adapters."""

from pathlib import Path

import pytest

from manual_spss.ui.models import ManualPage


def test_manual_page_keeps_display_html_and_speech_text_separate() -> None:
    page = ManualPage(
        identifier="chapter-1",
        title="Introducción",
        body_html="<p>Texto para mostrar</p>",
        plain_text="Texto para leer",
    )

    assert page.body_html == "<p>Texto para mostrar</p>"
    assert page.plain_text == "Texto para leer"


def test_manual_page_rejects_non_string_speech_text() -> None:
    with pytest.raises(TypeError, match="plain_text"):
        ManualPage("chapter-1", "Título", "<p>Texto</p>", plain_text=None)  # type: ignore[arg-type]


def test_existing_base_url_and_attributions_remain_supported() -> None:
    page = ManualPage(
        "chapter-1",
        "Título",
        "<p>Texto</p>",
        Path("chapter.html"),
        ("Fuente",),
    )

    assert page.base_url == Path("chapter.html")
    assert page.attributions == ("Fuente",)
