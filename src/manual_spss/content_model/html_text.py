"""Deterministic plain-text extraction from local section HTML."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from manual_spss.content_model.errors import ContentValidationError
from manual_spss.content_model.models import Resource

_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "blockquote",
        "br",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)
_IGNORED_TAGS = frozenset({"script", "style"})


class _PlainTextParser(HTMLParser):
    """Collect visible text while retaining readable block boundaries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._fragments: list[str] = []
        self._ignored_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if self._ignored_tag is not None:
            return
        if tag in _IGNORED_TAGS:
            self._ignored_tag = tag
        elif tag in _BLOCK_TAGS:
            self._fragments.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._ignored_tag is not None:
            if tag == self._ignored_tag:
                self._ignored_tag = None
            return
        if tag in _BLOCK_TAGS:
            self._fragments.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_tag is None:
            self._fragments.append(data)

    def plain_text(self) -> str:
        lines = [
            re.sub(r"[^\S\n]+", " ", line).strip()
            for line in "".join(self._fragments).splitlines()
        ]
        return "\n".join(line for line in lines if line)


def html_to_plain_text(body_html: str) -> str:
    """Return visible, whitespace-normalized text from an HTML fragment."""
    if not isinstance(body_html, str):
        raise TypeError("body_html must be a string")

    parser = _PlainTextParser()
    parser.feed(body_html)
    parser.close()
    return parser.plain_text()


class _HTMLPolicyParser(HTMLParser):
    """Reject active markup and image references outside the local catalog."""

    _ACTIVE_TAGS = frozenset(
        {
            "audio",
            "base",
            "button",
            "embed",
            "form",
            "iframe",
            "input",
            "link",
            "meta",
            "object",
            "script",
            "source",
            "style",
            "video",
        }
    )

    def __init__(
        self,
        body_path: Path,
        content_root: Path,
        resources: tuple[Resource, ...],
    ) -> None:
        super().__init__(convert_charrefs=True)
        self._body_path = body_path
        self._content_root = content_root.resolve()
        self._resource_paths = {resource.path.resolve() for resource in resources}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._ACTIVE_TAGS:
            raise ContentValidationError(
                f"Section HTML contains active HTML element: <{tag}>"
            )

        for name, value in attrs:
            attribute = name.lower()
            if attribute.startswith("on"):
                raise ContentValidationError(
                    f"Section HTML contains an event handler: {attribute}"
                )
            if attribute == "style":
                raise ContentValidationError(
                    "Section HTML cannot contain inline styles"
                )
            if attribute in {"srcset", "poster", "data"}:
                raise ContentValidationError(
                    "Section HTML uses an unsupported remote-capable attribute: "
                    f"{attribute}"
                )
            if attribute == "src":
                if tag != "img" or value is None:
                    raise ContentValidationError(
                        "Section HTML source must be a local image resource"
                    )
                self._validate_image_source(value)
            if attribute == "href" and value is not None:
                parsed_url = urlsplit(value)
                if parsed_url.scheme.lower() in {"javascript", "data", "file"}:
                    raise ContentValidationError(
                        "Section HTML contains an unsafe hyperlink"
                    )

    def _validate_image_source(self, source: str) -> None:
        parsed_url = urlsplit(source)
        if (
            not source
            or parsed_url.scheme
            or parsed_url.netloc
            or source.startswith("//")
            or "\\" in source
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ContentValidationError(
                "Section image must reference a local resource"
            )

        try:
            image_path = (self._body_path.parent / source).resolve(strict=True)
            image_path.relative_to(self._content_root)
        except (OSError, RuntimeError, ValueError) as error:
            raise ContentValidationError(
                "Section image must reference a local resource"
            ) from error
        if image_path not in self._resource_paths:
            raise ContentValidationError(
                "Section image must be declared in manifest resources"
            )


def validate_html_body(
    body_html: str,
    *,
    body_path: Path,
    content_root: Path,
    resources: tuple[Resource, ...],
) -> None:
    """Reject active markup and nonlocal or undeclared image references."""
    parser = _HTMLPolicyParser(body_path, content_root, resources)
    parser.feed(body_html)
    parser.close()
