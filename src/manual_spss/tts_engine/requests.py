"""Resolve selected or page text into clean plain-text speech input."""

from __future__ import annotations

import re

_INLINE_WHITESPACE = re.compile(r"[^\S\n]+")


def reading_text(page_text: str, selected_text: str = "") -> str:
    """Return normalized selection text or fall back to the current page."""
    selected = _normalize_text(selected_text)
    if selected:
        return selected
    return _normalize_text(page_text)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = _INLINE_WHITESPACE.sub(" ", raw_line).strip()
        if line:
            lines.append(line)
        elif lines and lines[-1]:
            lines.append("")
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)
