from typing import Any

import pytest

from manual_spss.content_model.errors import (
    ContentNotFoundError,
    ContentValidationError,
)
from manual_spss.content_model.repository import ManualRepository


def entry(
    section_id: str = "chapter-1",
    *,
    parent_id: str | None = None,
    kind: str = "chapter",
    title: str = "Capítulo 1",
    order: int = 1,
    body: str = "sections/chapter-1.html",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": section_id,
        "parent_id": parent_id,
        "kind": kind,
        "title": title,
        "order": order,
        "body": body,
        **extra,
    }


def test_repository_loads_html_and_local_resources(write_content_catalog: Any) -> None:
    root = write_content_catalog(
        [
            entry(
                resources=[
                    {
                        "path": "assets/figure.png",
                        "mime_type": "image/png",
                        "alt_text": "Captura del editor de datos",
                    }
                ],
                search_terms=["SPSS", "vista de datos"],
                attributions=[{"source": "Manual SPSS original"}],
            )
        ]
    )
    (root / "sections/chapter-1.html").write_text(
        "<article><h1>Capítulo 1</h1><p>Introducción a SPSS.</p>"
        '<img src="../assets/figure.png" alt="Captura del editor de datos">'
        "</article>",
        encoding="utf-8",
    )

    repository = ManualRepository.load(root)
    section = repository.get_section("chapter-1")

    assert repository.manual.manual_id == "manual-spss-test"
    assert section.plain_text == "Capítulo 1\nIntroducción a SPSS."
    assert section.search_terms == ("SPSS", "vista de datos")
    assert section.resources[0].path == (root / "assets/figure.png").resolve()
    assert section.attributions[0].source == "Manual SPSS original"
    assert repository.root_sections() == (section,)
    assert repository.children_of(section.id) == ()


def test_repository_rejects_missing_parent(write_content_catalog: Any) -> None:
    root = write_content_catalog(
        [
            entry(
                "chapter-1.section-1",
                parent_id="chapter-missing",
                kind="section",
                body="sections/section-1.html",
            )
        ]
    )

    with pytest.raises(ContentValidationError, match="parent section does not exist"):
        ManualRepository.load(root)


def test_repository_rejects_parent_cycles(write_content_catalog: Any) -> None:
    root = write_content_catalog(
        [
            entry(
                "section-a",
                parent_id="section-b",
                kind="section",
                body="sections/a.html",
            ),
            entry(
                "section-b",
                parent_id="section-a",
                kind="section",
                body="sections/b.html",
                order=2,
            ),
        ]
    )

    with pytest.raises(ContentValidationError, match="cycle"):
        ManualRepository.load(root)


def test_repository_rejects_duplicate_sibling_orders(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog(
        [
            entry("chapter-1", order=1, body="sections/chapter-1.html"),
            entry(
                "chapter-2",
                order=1,
                body="sections/chapter-2.html",
                title="Capítulo 2",
            ),
        ]
    )

    with pytest.raises(ContentValidationError, match="duplicate order"):
        ManualRepository.load(root)


def test_repository_reports_missing_section(write_content_catalog: Any) -> None:
    root = write_content_catalog([entry()])
    repository = ManualRepository.load(root)

    with pytest.raises(ContentNotFoundError, match="chapter-missing"):
        repository.get_section("chapter-missing")


def test_repository_rejects_non_utf8_body(write_content_catalog: Any) -> None:
    root = write_content_catalog([entry()])
    (root / "sections/chapter-1.html").write_bytes(b"\xff")

    with pytest.raises(ContentValidationError, match="UTF-8"):
        ManualRepository.load(root)


@pytest.mark.parametrize(
    "body, message",
    [
        ("<script>alert('x')</script>", "active HTML"),
        ('<img src="https://example.com/figure.png">', "local resource"),
        ('<p onclick="run()">Texto</p>', "event handler"),
    ],
)
def test_repository_rejects_active_or_remote_html(
    write_content_catalog: Any, body: str, message: str
) -> None:
    root = write_content_catalog([entry()])
    (root / "sections/chapter-1.html").write_text(body, encoding="utf-8")

    with pytest.raises(ContentValidationError, match=message):
        ManualRepository.load(root)


def test_repository_rejects_duplicate_sibling_order_within_parent(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog(
        [
            entry("chapter-1", body="sections/chapter-1.html"),
            entry(
                "chapter-1.section-1",
                parent_id="chapter-1",
                kind="section",
                order=1,
                body="sections/section-1.html",
            ),
            entry(
                "chapter-1.section-2",
                parent_id="chapter-1",
                kind="section",
                order=1,
                body="sections/section-2.html",
            ),
        ]
    )

    with pytest.raises(ContentValidationError, match="duplicate order"):
        ManualRepository.load(root)


def test_children_of_unknown_section_raises_not_found(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog([entry()])
    repository = ManualRepository.load(root)

    with pytest.raises(ContentNotFoundError):
        repository.children_of("unknown")


def test_resource_paths_must_be_declared_even_when_file_exists(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog([entry()])
    (root / "assets/other.png").write_bytes(b"other-image")
    (root / "sections/chapter-1.html").write_text(
        '<img src="../assets/other.png">', encoding="utf-8"
    )

    with pytest.raises(ContentValidationError, match="declared in manifest"):
        ManualRepository.load(root)


def test_missing_body_data_is_not_exposed_as_partial_repository(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog([entry()])
    (root / "sections/chapter-1.html").unlink()

    with pytest.raises(ContentValidationError):
        ManualRepository.load(root)


def test_repository_does_not_require_nonempty_plain_text(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog([entry()])
    (root / "sections/chapter-1.html").write_text(
        "<img alt='Decorativo'>", encoding="utf-8"
    )

    repository = ManualRepository.load(root)

    assert repository.get_section("chapter-1").plain_text == ""
