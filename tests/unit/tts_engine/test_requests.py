"""Tests for choosing and normalizing text for local speech requests."""

from manual_spss.tts_engine.requests import reading_text


def test_uses_selected_text_when_selection_contains_content() -> None:
    assert reading_text("Texto de la página", "Solo esta selección") == (
        "Solo esta selección"
    )


def test_blank_selection_falls_back_to_plain_page_text() -> None:
    assert reading_text("Texto de la página", " \n\t ") == "Texto de la página"


def test_normalizes_qtextbrowser_paragraph_and_line_separators() -> None:
    selected = "  Primer párrafo\u2029  Segunda\u2028línea  "

    assert reading_text("No usado", selected) == "Primer párrafo\nSegunda\nlínea"


def test_normalizes_blank_lines_and_repeated_inline_whitespace() -> None:
    selected = "  Un   texto.  \n\n\n  Otro\ttexto. "

    assert reading_text("", selected) == "Un texto.\n\nOtro texto."


def test_returns_empty_when_page_and_selection_are_empty() -> None:
    assert reading_text(" \n ", "\u2029\t") == ""
