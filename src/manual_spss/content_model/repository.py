"""Read-only repository for validated local manual catalogs."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, Self

from manual_spss.content_model.errors import (
    ContentNotFoundError,
    ContentValidationError,
)
from manual_spss.content_model.html_text import (
    html_to_plain_text,
    validate_html_body,
)
from manual_spss.content_model.models import Manual, Section
from manual_spss.content_model.validation import load_manifest


class ContentRepository(Protocol):
    """Public query contract shared by manual content repositories."""

    @classmethod
    def load(cls, root: Path) -> Self: ...

    @property
    def manual(self) -> Manual: ...

    def get_section(self, section_id: str) -> Section: ...

    def root_sections(self) -> tuple[Section, ...]: ...

    def children_of(self, section_id: str) -> tuple[Section, ...]: ...

    def sections_in_reading_order(self) -> tuple[Section, ...]: ...


class ManualRepository:
    """Load a whole validated catalog and provide stable hierarchy queries."""

    def __init__(self, manual: Manual) -> None:
        self._manual = manual
        self._sections_by_id = MappingProxyType(
            {section.id: section for section in manual.sections}
        )
        children: dict[str | None, list[Section]] = defaultdict(list)
        for section in manual.sections:
            children[section.parent_id].append(section)
        self._children = {
            parent_id: tuple(sorted(siblings, key=lambda item: item.order))
            for parent_id, siblings in children.items()
        }
        self._reading_order = self._build_reading_order()

    @classmethod
    def load(cls, root: Path) -> ManualRepository:
        """Load and validate all catalog records before creating a repository."""
        descriptor = load_manifest(root)
        sections: list[Section] = []
        for item in descriptor.sections:
            try:
                body_html = item.body_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as error:
                raise ContentValidationError(
                    f"Section {item.id} body must use UTF-8 encoding"
                ) from error
            except OSError as error:
                raise ContentValidationError(
                    f"Section {item.id} body could not be read"
                ) from error

            validate_html_body(
                body_html,
                body_path=item.body_path,
                content_root=root,
                resources=item.resources,
            )
            sections.append(
                Section(
                    id=item.id,
                    parent_id=item.parent_id,
                    kind=item.kind,
                    title=item.title,
                    order=item.order,
                    body_html=body_html,
                    plain_text=html_to_plain_text(body_html),
                    search_terms=item.search_terms,
                    resources=item.resources,
                    attributions=item.attributions,
                )
            )

        manual = Manual(
            schema_version=descriptor.schema_version,
            manual_id=descriptor.manual_id,
            title=descriptor.title,
            version=descriptor.version,
            locale=descriptor.locale,
            sections=tuple(sections),
        )
        cls._validate_hierarchy(manual.sections)
        return cls(manual)

    @property
    def manual(self) -> Manual:
        """Return immutable metadata and sections for the loaded manual."""
        return self._manual

    def get_section(self, section_id: str) -> Section:
        """Return a section or raise ContentNotFoundError for an unknown ID."""
        try:
            return self._sections_by_id[section_id]
        except KeyError as error:
            raise ContentNotFoundError(
                f"Manual section not found: {section_id}"
            ) from error

    def root_sections(self) -> tuple[Section, ...]:
        """Return top-level sections ordered by their order field."""
        return self._children.get(None, ())

    def children_of(self, section_id: str) -> tuple[Section, ...]:
        """Return a section's direct children in their declared order."""
        self.get_section(section_id)
        return self._children.get(section_id, ())

    def sections_in_reading_order(self) -> tuple[Section, ...]:
        """Return a stable depth-first traversal of the manual hierarchy."""
        return self._reading_order

    def _build_reading_order(self) -> tuple[Section, ...]:
        ordered: list[Section] = []
        stack = list(reversed(self.root_sections()))
        while stack:
            section = stack.pop()
            ordered.append(section)
            stack.extend(reversed(self._children.get(section.id, ())))
        return tuple(ordered)

    @staticmethod
    def _validate_hierarchy(sections: tuple[Section, ...]) -> None:
        sections_by_id = {section.id: section for section in sections}
        sibling_orders: set[tuple[str | None, int]] = set()
        for section in sections:
            if (
                section.parent_id is not None
                and section.parent_id not in sections_by_id
            ):
                raise ContentValidationError(
                    f"Section {section.id} parent section does not exist: "
                    f"{section.parent_id}"
                )
            order_key = (section.parent_id, section.order)
            if order_key in sibling_orders:
                raise ContentValidationError(
                    f"Sections under {section.parent_id!r} have duplicate order "
                    f"{section.order}"
                )
            sibling_orders.add(order_key)

        states: dict[str, int] = {}
        for section in sections:
            current_id: str | None = section.id
            chain: list[str] = []
            while current_id is not None and states.get(current_id, 0) == 0:
                states[current_id] = 1
                chain.append(current_id)
                current_id = sections_by_id[current_id].parent_id
            if current_id is not None and states.get(current_id) == 1:
                raise ContentValidationError(
                    f"Manual section hierarchy contains a cycle at {current_id}"
                )
            for section_id in chain:
                states[section_id] = 2

        if len(states) != len(sections):
            raise ContentValidationError("Manual section hierarchy is incomplete")
