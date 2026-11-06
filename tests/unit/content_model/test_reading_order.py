from typing import Any

from manual_spss.content_model.repository import ManualRepository


def entry(
    section_id: str,
    *,
    parent_id: str | None = None,
    kind: str,
    order: int,
    title: str,
    body: str,
) -> dict[str, Any]:
    return {
        "id": section_id,
        "parent_id": parent_id,
        "kind": kind,
        "order": order,
        "title": title,
        "body": body,
    }


def test_sections_are_returned_in_depth_first_reading_order(
    write_content_catalog: Any,
) -> None:
    root = write_content_catalog(
        [
            entry(
                "chapter-2",
                kind="chapter",
                order=1,
                title="Capítulo 2",
                body="sections/chapter-2.html",
            ),
            entry(
                "chapter-1",
                kind="chapter",
                order=2,
                title="Capítulo 1",
                body="sections/chapter-1.html",
            ),
            entry(
                "chapter-2.section-2",
                parent_id="chapter-2",
                kind="section",
                order=2,
                title="Sección 2",
                body="sections/section-2.html",
            ),
            entry(
                "chapter-2.section-1",
                parent_id="chapter-2",
                kind="section",
                order=1,
                title="Sección 1",
                body="sections/section-1.html",
            ),
            entry(
                "chapter-2.section-1.subsection-1",
                parent_id="chapter-2.section-1",
                kind="subsection",
                order=1,
                title="Subsección",
                body="sections/subsection.html",
            ),
        ]
    )
    repository = ManualRepository.load(root)

    assert tuple(section.id for section in repository.sections_in_reading_order()) == (
        "chapter-2",
        "chapter-2.section-1",
        "chapter-2.section-1.subsection-1",
        "chapter-2.section-2",
        "chapter-1",
    )
    assert tuple(section.id for section in repository.root_sections()) == (
        "chapter-2",
        "chapter-1",
    )
    assert tuple(
        section.id for section in repository.children_of("chapter-2")
    ) == ("chapter-2.section-1", "chapter-2.section-2")
