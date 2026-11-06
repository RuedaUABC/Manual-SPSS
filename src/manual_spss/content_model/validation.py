"""Validation and path confinement for external manual catalogs."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from manual_spss.content_model.errors import ContentValidationError
from manual_spss.content_model.models import (
    Attribution,
    Resource,
    validate_section_id,
)

_SUPPORTED_SCHEMA_VERSION = 1
_MIME_TYPE_PATTERN = re.compile(r"^[a-zA-Z0-9.+-]+/[a-zA-Z0-9.+-]+$")


@dataclass(frozen=True, slots=True)
class SectionDescriptor:
    """Validated section metadata before the HTML body is loaded."""

    id: str
    parent_id: str | None
    kind: str
    title: str
    order: int
    body_path: Path
    search_terms: tuple[str, ...]
    resources: tuple[Resource, ...]
    attributions: tuple[Attribution, ...]


@dataclass(frozen=True, slots=True)
class ManifestDescriptor:
    """Validated manifest metadata and local section descriptors."""

    schema_version: int
    manual_id: str
    title: str
    version: str
    locale: str
    sections: tuple[SectionDescriptor, ...]


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ContentValidationError(f"{field_name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise ContentValidationError(f"{field_name} object keys must be strings")
    return cast(Mapping[str, object], value)


def _required_string(
    values: Mapping[str, object], key: str, field_name: str
) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContentValidationError(f"{field_name} must be a nonempty string")
    return value


def _required_integer(
    values: Mapping[str, object], key: str, field_name: str
) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContentValidationError(f"{field_name} must be a positive integer")
    return value


def _optional_string(
    values: Mapping[str, object], key: str, field_name: str, default: str = ""
) -> str:
    value = values.get(key, default)
    if not isinstance(value, str):
        raise ContentValidationError(f"{field_name} must be a string")
    return value


def _string_list(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ContentValidationError(f"{field_name} must be a list of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ContentValidationError(
            f"{field_name} must contain only nonempty strings"
        )
    return tuple(cast(list[str], value))


def _root_path(content_root: Path, field_name: str) -> Path:
    try:
        root = content_root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ContentValidationError(
            f"{field_name} does not point to an accessible content directory"
        ) from error
    if not root.is_dir():
        raise ContentValidationError(f"{field_name} must be a directory")
    return root


def resolve_content_path(
    content_root: Path,
    relative_path: object,
    *,
    field_name: str,
    expected_directory: str,
    suffix: str | None = None,
) -> Path:
    """Resolve an existing local file while blocking traversal and symlinks."""
    root = _root_path(content_root, "content root")
    if not isinstance(relative_path, str) or not relative_path:
        raise ContentValidationError(f"{field_name} must be a relative file path")
    if relative_path != relative_path.strip():
        raise ContentValidationError(f"{field_name} contains surrounding whitespace")
    if any(character in relative_path for character in ("\\", ":", "?", "#")):
        raise ContentValidationError(f"{field_name} must be a local POSIX path")

    path_parts = relative_path.split("/")
    if (
        relative_path.startswith("/")
        or any(part in {"", ".", ".."} for part in path_parts)
    ):
        raise ContentValidationError(
            f"{field_name} must not be absolute or escape its directory"
        )

    parsed_path = PurePosixPath(relative_path)
    if (
        parsed_path.is_absolute()
        or len(parsed_path.parts) < 2
        or parsed_path.parts[0] != expected_directory
    ):
        raise ContentValidationError(
            f"{field_name} must point inside {expected_directory}/"
        )
    if suffix is not None and parsed_path.suffix.lower() != suffix.lower():
        raise ContentValidationError(f"{field_name} must use the {suffix} extension")

    directory_path = root / expected_directory
    try:
        allowed_directory = directory_path.resolve(strict=True)
        allowed_directory.relative_to(root)
        resolved_path = (root / Path(*parsed_path.parts)).resolve(strict=True)
        resolved_path.relative_to(allowed_directory)
    except (OSError, RuntimeError, ValueError) as error:
        raise ContentValidationError(
            f"{field_name} is missing or resolves outside {expected_directory}/"
        ) from error

    if not allowed_directory.is_dir() or not resolved_path.is_file():
        raise ContentValidationError(f"{field_name} must reference an existing file")
    return resolved_path


def _parse_resource(
    value: object, content_root: Path, field_name: str
) -> Resource:
    values = _mapping(value, field_name)
    relative_path = _required_string(values, "path", f"{field_name}.path")
    path = resolve_content_path(
        content_root,
        relative_path,
        field_name=f"{field_name}.path",
        expected_directory="assets",
    )
    mime_type = _required_string(values, "mime_type", f"{field_name}.mime_type")
    if not _MIME_TYPE_PATTERN.fullmatch(mime_type):
        raise ContentValidationError(
            f"{field_name}.mime_type must use the type/subtype form"
        )
    alt_text = _optional_string(
        values, "alt_text", f"{field_name}.alt_text", default=""
    )
    return Resource(path=path, mime_type=mime_type, alt_text=alt_text)


def _parse_attribution(value: object, field_name: str) -> Attribution:
    values = _mapping(value, field_name)
    fields: dict[str, str | None] = {}
    for key in ("author", "source", "license", "url"):
        item = values.get(key)
        if item is not None and not isinstance(item, str):
            raise ContentValidationError(f"{field_name}.{key} must be a string or null")
        fields[key] = item
    return Attribution(**fields)


def _parse_section(
    value: object, content_root: Path, index: int
) -> SectionDescriptor:
    prefix = f"sections[{index}]"
    values = _mapping(value, prefix)
    section_id = _required_string(values, "id", f"{prefix}.id")
    validate_section_id(section_id, f"{prefix}.id")

    if "parent_id" not in values:
        raise ContentValidationError(f"{prefix}.parent_id is required")
    parent_id_value = values["parent_id"]
    if parent_id_value is not None and not isinstance(parent_id_value, str):
        raise ContentValidationError(f"{prefix}.parent_id must be a string or null")
    parent_id = parent_id_value
    if parent_id is not None:
        validate_section_id(parent_id, f"{prefix}.parent_id")

    kind = _required_string(values, "kind", f"{prefix}.kind")
    if kind not in {"chapter", "section", "subsection"}:
        raise ContentValidationError(
            f"{prefix}.kind must be chapter, section, or subsection"
        )
    title = _required_string(values, "title", f"{prefix}.title")
    order = _required_integer(values, "order", f"{prefix}.order")
    body_path = resolve_content_path(
        content_root,
        values.get("body"),
        field_name=f"{prefix}.body",
        expected_directory="sections",
        suffix=".html",
    )

    search_terms: tuple[str, ...] = ()
    if "search_terms" in values:
        search_terms = _string_list(values["search_terms"], f"{prefix}.search_terms")

    raw_resources = values.get("resources", [])
    if not isinstance(raw_resources, list):
        raise ContentValidationError(f"{prefix}.resources must be a list")
    resources = tuple(
        _parse_resource(resource, content_root, f"{prefix}.resources[{resource_index}]")
        for resource_index, resource in enumerate(raw_resources)
    )

    raw_attributions = values.get("attributions", [])
    if not isinstance(raw_attributions, list):
        raise ContentValidationError(f"{prefix}.attributions must be a list")
    attributions = tuple(
        _parse_attribution(attribution, f"{prefix}.attributions[{attribution_index}]")
        for attribution_index, attribution in enumerate(raw_attributions)
    )

    return SectionDescriptor(
        id=section_id,
        parent_id=parent_id,
        kind=kind,
        title=title,
        order=order,
        body_path=body_path,
        search_terms=search_terms,
        resources=resources,
        attributions=attributions,
    )


def parse_manifest(payload: object, content_root: Path) -> ManifestDescriptor:
    """Validate parsed JSON and all referenced files before returning metadata."""
    _root_path(content_root, "content root")
    values = _mapping(payload, "manifest")
    schema_version = _required_integer(
        values, "schema_version", "schema_version"
    )
    if schema_version != _SUPPORTED_SCHEMA_VERSION:
        raise ContentValidationError(
            f"Unsupported schema_version: {schema_version}"
        )

    manual_id = _required_string(values, "manual_id", "manual_id")
    title = _required_string(values, "title", "title")
    version = _required_string(values, "version", "version")
    locale = _required_string(values, "locale", "locale")
    raw_sections = values.get("sections")
    if not isinstance(raw_sections, list):
        raise ContentValidationError("sections must be a list")
    if not raw_sections:
        raise ContentValidationError("Manual must contain at least one section")

    sections = tuple(
        _parse_section(section, content_root, index)
        for index, section in enumerate(raw_sections)
    )
    section_ids = [section.id for section in sections]
    if len(section_ids) != len(set(section_ids)):
        raise ContentValidationError("Duplicate section ID in manifest")

    return ManifestDescriptor(
        schema_version=schema_version,
        manual_id=manual_id,
        title=title,
        version=version,
        locale=locale,
        sections=sections,
    )


def load_manifest(content_root: Path) -> ManifestDescriptor:
    """Read and validate the UTF-8 manifest stored in a content directory."""
    root = _root_path(content_root, "content root")
    manifest_path = root / "manifest.json"
    try:
        resolved_manifest = manifest_path.resolve(strict=True)
        resolved_manifest.relative_to(root)
        raw_manifest = resolved_manifest.read_bytes()
    except (OSError, RuntimeError, ValueError) as error:
        raise ContentValidationError(
            "manifest.json is missing or resolves outside the content root"
        ) from error

    try:
        manifest_text = raw_manifest.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContentValidationError("manifest.json must use UTF-8 encoding") from error
    try:
        payload = json.loads(manifest_text)
    except json.JSONDecodeError as error:
        raise ContentValidationError("manifest.json must contain valid JSON") from error
    return parse_manifest(payload, root)
