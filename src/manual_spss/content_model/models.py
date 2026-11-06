"""Immutable data models for the local Manual SPSS catalog."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from manual_spss.content_model.errors import ContentValidationError

_SECTION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SECTION_KINDS = frozenset({"chapter", "section", "subsection"})


def _require_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContentValidationError(f"{field_name} must be a nonempty string")


def validate_section_id(section_id: str, field_name: str = "section ID") -> None:
    if not isinstance(section_id, str) or not _SECTION_ID_PATTERN.fullmatch(
        section_id
    ):
        raise ContentValidationError(
            f"{field_name} must be a safe section ID using lowercase ASCII "
            "letters, digits, '.', '_' or '-'."
        )


@dataclass(frozen=True, slots=True)
class Resource:
    """A local file referenced by a section's HTML body."""

    path: Path
    mime_type: str
    alt_text: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.parts:
            raise ContentValidationError("Resource path must be a pathlib.Path")
        _require_nonempty(self.mime_type, "MIME type")
        if not isinstance(self.alt_text, str):
            raise ContentValidationError("Resource alt_text must be a string")


@dataclass(frozen=True, slots=True)
class Attribution:
    """Available authorship and license information for a resource or text."""

    author: str | None = None
    source: str | None = None
    license: str | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("author", "source", "license", "url"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ContentValidationError(
                    f"Attribution {field_name} must be a string or None"
                )


@dataclass(frozen=True, slots=True)
class Section:
    """One chapter, section, or subsection in reading order."""

    id: str
    parent_id: str | None
    kind: str
    title: str
    order: int
    body_html: str
    plain_text: str
    search_terms: tuple[str, ...] = ()
    resources: tuple[Resource, ...] = ()
    attributions: tuple[Attribution, ...] = ()

    def __post_init__(self) -> None:
        validate_section_id(self.id)
        if self.parent_id is not None:
            validate_section_id(self.parent_id, "parent_id")
        if self.kind not in _SECTION_KINDS:
            raise ContentValidationError(
                "Section kind must be chapter, section, or subsection"
            )
        _require_nonempty(self.title, "Section title")
        if isinstance(self.order, bool) or not isinstance(self.order, int):
            raise ContentValidationError("Section order must be a positive integer")
        if self.order < 1:
            raise ContentValidationError("Section order must be a positive integer")
        if not isinstance(self.body_html, str):
            raise ContentValidationError("Section body_html must be a string")
        if not isinstance(self.plain_text, str):
            raise ContentValidationError("Section plain_text must be a string")

        search_terms = tuple(self.search_terms)
        if not all(isinstance(term, str) and term.strip() for term in search_terms):
            raise ContentValidationError(
                "Section search_terms must contain nonempty strings"
            )
        resources = tuple(self.resources)
        attributions = tuple(self.attributions)
        if not all(isinstance(resource, Resource) for resource in resources):
            raise ContentValidationError(
                "Section resources must contain Resource values"
            )
        if not all(
            isinstance(attribution, Attribution) for attribution in attributions
        ):
            raise ContentValidationError(
                "Section attributions must contain Attribution values"
            )
        object.__setattr__(self, "search_terms", search_terms)
        object.__setattr__(self, "resources", resources)
        object.__setattr__(self, "attributions", attributions)


@dataclass(frozen=True, slots=True)
class Manual:
    """Validated catalog metadata and its ordered section records."""

    schema_version: int
    manual_id: str
    title: str
    version: str
    locale: str
    sections: tuple[Section, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version < 1
        ):
            raise ContentValidationError("schema_version must be a positive integer")
        _require_nonempty(self.manual_id, "manual_id")
        _require_nonempty(self.title, "Manual title")
        _require_nonempty(self.version, "Manual version")
        _require_nonempty(self.locale, "Manual locale")

        sections = tuple(self.sections)
        if not sections:
            raise ContentValidationError("Manual must contain at least one section")
        if not all(isinstance(section, Section) for section in sections):
            raise ContentValidationError("Manual sections must contain Section values")
        object.__setattr__(self, "sections", sections)
