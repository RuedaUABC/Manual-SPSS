from __future__ import annotations

import re
from pathlib import Path

from manual_spss.content_model import ManualRepository

CONTENT_ROOT = Path(__file__).parents[2] / "content"
SOURCE_PAGE_RANGES = {
    "chapter-1": range(1, 5),
    "chapter-2": range(5, 10),
    "chapter-3": range(1, 10),
    "chapter-4": range(10, 14),
    "chapter-5": range(1, 7),
    "chapter-6": range(7, 12),
    "chapter-7": range(1, 14),
    "chapter-8": range(14, 18),
}
SEARCHABLE_CONTENT = {
    "chapter-1": "Statistical Package for the Social Sciences",
    "chapter-2": "valores perdidos",
    "chapter-3": "respuestas múltiples",
    "chapter-4": "tablas cruzadas",
    "chapter-5": "H₀",
    "chapter-6": "Tukey",
    "chapter-7": "gráfico de dispersión",
    "chapter-8": "-0.075",
}


def test_complete_manual_catalog_loads_with_source_pages_and_local_figures() -> None:
    repository = ManualRepository.load(CONTENT_ROOT)

    chapters = repository.root_sections()
    assert [chapter.id for chapter in chapters] == list(SOURCE_PAGE_RANGES)
    assert [chapter.order for chapter in chapters] == list(range(1, 9))
    assert len(repository.sections_in_reading_order()) == 8

    for chapter in chapters:
        assert len(chapter.plain_text) > 600
        page_numbers = {
            int(value)
            for value in re.findall(r'data-source-page="(\d+)"', chapter.body_html)
        }
        assert page_numbers == set(SOURCE_PAGE_RANGES[chapter.id])
        expected_text = SEARCHABLE_CONTENT[chapter.id].casefold()
        assert expected_text in chapter.plain_text.casefold()
        assert chapter.resources
        assert all(resource.path.is_file() for resource in chapter.resources)
        assert all(resource.alt_text.strip() for resource in chapter.resources)
        image_alts = re.findall(r'<img\b[^>]*\balt="([^"]*)"', chapter.body_html)
        assert image_alts and all(
            alt.strip() and len(alt) <= 140 for alt in image_alts
        )
        assert all(
            not alt.casefold().startswith(("captura de", "imagen de"))
            for alt in image_alts
        )
        assert chapter.attributions
        assert chapter.attributions[0].license is None
        assert chapter.attributions[0].author is None

    assert sum(len(chapter.resources) for chapter in chapters) >= 40
