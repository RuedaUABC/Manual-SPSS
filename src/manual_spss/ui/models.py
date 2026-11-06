"""Small UI-facing records that keep widgets independent of the content model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ManualPage:
    """A validated manual section adapted for display by the UI layer."""

    identifier: str
    title: str
    body_html: str
    base_url: Path | None = None
    attributions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError("Page identifier must not be empty")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Page title must not be empty")
        if not isinstance(self.body_html, str):
            raise TypeError("Page body_html must be a string")
        if self.base_url is not None and not isinstance(self.base_url, Path):
            raise TypeError("Page base_url must be a pathlib.Path or None")
        sources = tuple(self.attributions)
        if not all(isinstance(source, str) and source.strip() for source in sources):
            raise ValueError("Page attributions must contain nonempty strings")
        object.__setattr__(self, "attributions", sources)
