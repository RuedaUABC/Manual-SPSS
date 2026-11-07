"""Integration checks for catalog-to-reader page adaptation."""

from pathlib import Path

from manual_spss.app import load_manual_pages
from manual_spss.content_model import ManualRepository


def test_manual_pages_adapt_plain_text_without_changing_html_or_sources() -> None:
    content_root = Path("content")
    sections = ManualRepository.load(content_root).root_sections()

    pages = load_manual_pages(content_root)

    assert len(pages) == len(sections)
    for page, section in zip(pages, sections, strict=True):
        assert page.plain_text == section.plain_text
        assert page.body_html == section.body_html
        assert page.title == section.title
        assert page.attributions == tuple(
            item.source for item in section.attributions if item.source
        )
