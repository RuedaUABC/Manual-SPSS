from pathlib import Path

import pytest

from manual_spss.content_model.errors import ContentValidationError
from manual_spss.content_model.models import Attribution, Manual, Resource, Section


def test_section_is_immutable_and_converts_collections_to_tuples() -> None:
    resource = Resource(Path("assets/chart.png"), "image/png", "Gráfico")
    attribution = Attribution(author="Equipo editorial")

    section = Section(
        id="chapter-1.intro",
        parent_id=None,
        kind="chapter",
        title="Introducción",
        order=1,
        body_html="<p>Texto</p>",
        plain_text="Texto",
        search_terms=["SPSS", "análisis estadístico"],  # type: ignore[arg-type]
        resources=[resource],  # type: ignore[arg-type]
        attributions=[attribution],  # type: ignore[arg-type]
    )

    assert section.resources == (resource,)
    assert section.attributions == (attribution,)
    assert section.search_terms == ("SPSS", "análisis estadístico")
    with pytest.raises((AttributeError, TypeError)):
        section.title = "Otro título"  # type: ignore[misc]


@pytest.mark.parametrize(
    "section_id",
    ["", "has space", "chapter/1", "sección-1", "../outside"],
)
def test_section_rejects_unsafe_ids(section_id: str) -> None:
    with pytest.raises(ContentValidationError, match="section ID"):
        Section(
            id=section_id,
            parent_id=None,
            kind="chapter",
            title="Capítulo",
            order=1,
            body_html="",
            plain_text="",
        )


@pytest.mark.parametrize("kind", ["", "page", "Chapter"])
def test_section_rejects_unknown_kinds(kind: str) -> None:
    with pytest.raises(ContentValidationError, match="kind"):
        Section(
            id="chapter-1",
            parent_id=None,
            kind=kind,
            title="Capítulo",
            order=1,
            body_html="",
            plain_text="",
        )


@pytest.mark.parametrize("order", [0, -1, True])
def test_section_requires_a_positive_integer_order(order: int) -> None:
    with pytest.raises(ContentValidationError, match="positive integer"):
        Section(
            id="chapter-1",
            parent_id=None,
            kind="chapter",
            title="Capítulo",
            order=order,
            body_html="",
            plain_text="",
        )


def test_section_requires_a_nonempty_title() -> None:
    with pytest.raises(ContentValidationError, match="title"):
        Section(
            id="chapter-1",
            parent_id=None,
            kind="chapter",
            title="  ",
            order=1,
            body_html="",
            plain_text="",
        )


def test_section_rejects_blank_search_terms() -> None:
    with pytest.raises(ContentValidationError, match="search_terms"):
        Section(
            id="chapter-1",
            parent_id=None,
            kind="chapter",
            title="Capítulo",
            order=1,
            body_html="",
            plain_text="",
            search_terms=("SPSS", "  "),
        )


def test_resource_requires_a_path_and_mime_type() -> None:
    with pytest.raises(ContentValidationError, match="path"):
        Resource("assets/image.png", "image/png", "Imagen")  # type: ignore[arg-type]

    with pytest.raises(ContentValidationError, match="MIME type"):
        Resource(Path("assets/image.png"), "  ", "Imagen")


def test_attribution_allows_unknown_metadata_without_inventing_values() -> None:
    attribution = Attribution()

    assert attribution.author is None
    assert attribution.source is None
    assert attribution.license is None
    assert attribution.url is None


def test_manual_requires_sections_and_freezes_them() -> None:
    section = Section(
        id="chapter-1",
        parent_id=None,
        kind="chapter",
        title="Capítulo 1",
        order=1,
        body_html="<p>Contenido</p>",
        plain_text="Contenido",
    )
    manual = Manual(
        schema_version=1,
        manual_id="manual-spss",
        title="Manual SPSS",
        version="0.1.0",
        locale="es-MX",
        sections=[section],  # type: ignore[arg-type]
    )

    assert manual.sections == (section,)

    with pytest.raises(ContentValidationError, match="at least one section"):
        Manual(
            schema_version=1,
            manual_id="manual-spss",
            title="Manual SPSS",
            version="0.1.0",
            locale="es-MX",
            sections=(),
        )
