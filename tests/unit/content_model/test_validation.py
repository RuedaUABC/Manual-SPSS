import json
from pathlib import Path
from typing import Any

import pytest

from manual_spss.content_model.errors import ContentValidationError
from manual_spss.content_model.validation import (
    _mapping,
    load_manifest,
    parse_manifest,
    resolve_content_path,
)


def section_entry(**updates: Any) -> dict[str, Any]:
    section: dict[str, Any] = {
        "id": "chapter-1.intro",
        "parent_id": None,
        "kind": "chapter",
        "title": "Introducción",
        "order": 1,
        "body": "sections/intro.html",
        "search_terms": ["SPSS", "introducción"],
        "resources": [
            {
                "path": "assets/logo.png",
                "mime_type": "image/png",
                "alt_text": "Logo SPSS",
            }
        ],
        "attributions": [{"author": "Equipo editorial"}],
    }
    section.update(updates)
    return section


def make_root(root: Path) -> Path:
    (root / "sections").mkdir(parents=True, exist_ok=True)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    (root / "sections/intro.html").write_text(
        "<p>Introducción</p>", encoding="utf-8"
    )
    (root / "assets/logo.png").write_bytes(b"image")
    return root


def manifest_payload(sections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "manual_id": "manual-spss",
        "title": "Manual SPSS",
        "version": "0.1.0",
        "locale": "es-MX",
        "sections": [section_entry()] if sections is None else sections,
    }


def test_parse_manifest_returns_typed_entries_and_resolved_paths(
    tmp_path: Path,
) -> None:
    root = make_root(tmp_path / "content")

    result = parse_manifest(manifest_payload(), root)

    assert result.manual_id == "manual-spss"
    assert result.sections[0].body_path == (root / "sections/intro.html").resolve()
    assert result.sections[0].resources[0].path == (root / "assets/logo.png").resolve()
    assert result.sections[0].search_terms == ("SPSS", "introducción")
    assert result.sections[0].attributions[0].author == "Equipo editorial"


def test_parse_manifest_accepts_optional_additive_fields(tmp_path: Path) -> None:
    root = make_root(tmp_path / "content")
    section = section_entry()
    section.pop("resources")
    section.pop("attributions")
    section.pop("search_terms")
    payload = manifest_payload([section])
    payload["future_optional_field"] = {"ignored": True}

    result = parse_manifest(payload, root)

    assert result.sections[0].resources == ()
    assert result.sections[0].attributions == ()
    assert result.sections[0].search_terms == ()


@pytest.mark.parametrize("payload", [None, [], "manifest", 5])
def test_parse_manifest_rejects_non_object_documents(
    tmp_path: Path, payload: object
) -> None:
    root = make_root(tmp_path / "content")

    with pytest.raises(ContentValidationError, match="object"):
        parse_manifest(payload, root)


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"schema_version": True}, "schema_version"),
        ({"schema_version": 2}, "Unsupported schema_version"),
        ({"title": " "}, "title"),
        ({"sections": []}, "at least one section"),
        ({"sections": "chapter"}, "sections must be a list"),
    ],
)
def test_parse_manifest_rejects_invalid_top_level_fields(
    tmp_path: Path, updates: dict[str, Any], message: str
) -> None:
    root = make_root(tmp_path / "content")
    payload = manifest_payload()
    payload.update(updates)

    with pytest.raises(ContentValidationError, match=message):
        parse_manifest(payload, root)


@pytest.mark.parametrize(
    "relative_path",
    [
        "../outside.html",
        "/tmp/intro.html",
        "C:/manual/intro.html",
        r"sections\\intro.html",
        "https://example.com/intro.html",
        "sections/./intro.html",
        "sections//intro.html",
    ],
)
def test_resolve_content_path_rejects_unsafe_or_nonlocal_paths(
    tmp_path: Path, relative_path: str
) -> None:
    root = make_root(tmp_path / "content")

    with pytest.raises(ContentValidationError, match="body"):
        resolve_content_path(
            root,
            relative_path,
            field_name="section.body",
            expected_directory="sections",
            suffix=".html",
        )


def test_parse_manifest_rejects_missing_body_or_resource_files(
    tmp_path: Path,
) -> None:
    root = make_root(tmp_path / "content")
    section = section_entry(body="sections/missing.html")

    with pytest.raises(ContentValidationError, match=r"sections\[0\].body"):
        parse_manifest(manifest_payload([section]), root)

    section = section_entry(
        resources=[
            {"path": "assets/missing.png", "mime_type": "image/png"}
        ]
    )
    with pytest.raises(
        ContentValidationError, match=r"sections\[0\].resources\[0\].path"
    ):
        parse_manifest(manifest_payload([section]), root)


def test_resolve_content_path_rejects_symlink_that_escapes_root(
    tmp_path: Path,
) -> None:
    root = make_root(tmp_path / "content")
    outside_file = tmp_path / "outside.html"
    outside_file.write_text("<p>Fuera</p>", encoding="utf-8")
    linked_file = root / "sections/linked.html"
    linked_file.symlink_to(outside_file)

    with pytest.raises(ContentValidationError, match="section.body"):
        resolve_content_path(
            root,
            "sections/linked.html",
            field_name="section.body",
            expected_directory="sections",
            suffix=".html",
        )


def test_parse_manifest_rejects_duplicate_section_ids(tmp_path: Path) -> None:
    root = make_root(tmp_path / "content")
    duplicate = section_entry(id="chapter-1.intro")

    with pytest.raises(ContentValidationError, match="Duplicate section ID"):
        parse_manifest(manifest_payload([section_entry(), duplicate]), root)


@pytest.mark.parametrize(
    "manifest_bytes, message",
    [(b"not json", "valid JSON"), (b"\xff", "UTF-8")],
)
def test_load_manifest_normalizes_file_encoding_errors(
    tmp_path: Path, manifest_bytes: bytes, message: str
) -> None:
    root = make_root(tmp_path / "content")
    (root / "manifest.json").write_bytes(manifest_bytes)

    with pytest.raises(ContentValidationError, match=message):
        load_manifest(root)


def test_load_manifest_reports_missing_manifest(tmp_path: Path) -> None:
    root = make_root(tmp_path / "content")

    with pytest.raises(ContentValidationError, match="manifest.json"):
        load_manifest(root)


def test_load_manifest_returns_valid_catalog(tmp_path: Path) -> None:
    root = make_root(tmp_path / "content")
    (root / "manifest.json").write_text(
        json.dumps(manifest_payload()), encoding="utf-8"
    )

    result = load_manifest(root)

    assert result.manual_id == "manual-spss"


def test_mapping_rejects_non_string_object_keys() -> None:
    with pytest.raises(ContentValidationError, match="keys must be strings"):
        _mapping({1: "invalid"}, "manifest")


@pytest.mark.parametrize(
    "relative_path, message",
    [
        ("", "relative file path"),
        (" sections/intro.html ", "surrounding whitespace"),
        ("sections", "point inside sections"),
        ("other/intro.html", "point inside sections"),
        ("sections/intro.txt", "extension"),
    ],
)
def test_resolve_content_path_rejects_invalid_local_paths(
    tmp_path: Path, relative_path: str, message: str
) -> None:
    root = make_root(tmp_path / "content")

    with pytest.raises(ContentValidationError, match=message):
        resolve_content_path(
            root,
            relative_path,
            field_name="section.body",
            expected_directory="sections",
            suffix=".html",
        )


def test_resolve_content_path_rejects_missing_and_non_directory_roots(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContentValidationError, match="accessible content directory"):
        resolve_content_path(
            tmp_path / "missing",
            "sections/intro.html",
            field_name="section.body",
            expected_directory="sections",
        )

    file_root = tmp_path / "content-file"
    file_root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(
        ContentValidationError, match="content root must be a directory"
    ):
        resolve_content_path(
            file_root,
            "sections/intro.html",
            field_name="section.body",
            expected_directory="sections",
        )


def test_resolve_content_path_rejects_directory_instead_of_file(
    tmp_path: Path,
) -> None:
    root = make_root(tmp_path / "content")
    (root / "sections/folder.html").mkdir()

    with pytest.raises(ContentValidationError, match="existing file"):
        resolve_content_path(
            root,
            "sections/folder.html",
            field_name="section.body",
            expected_directory="sections",
            suffix=".html",
        )


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"search_terms": "SPSS"}, "search_terms must be a list"),
        ({"search_terms": ["SPSS", " "]}, "nonempty strings"),
        ({"kind": "unknown"}, "kind must be chapter"),
        ({"parent_id": 1}, "parent_id must be a string or null"),
        ({"parent_id": "!invalid"}, "safe section ID"),
        ({"resources": "assets/logo.png"}, "resources must be a list"),
        ({"attributions": "author"}, "attributions must be a list"),
        (
            {"resources": [{"path": "assets/logo.png", "mime_type": "png"}]},
            "mime_type must use the type/subtype form",
        ),
        (
            {
                "resources": [
                    {
                        "path": "assets/logo.png",
                        "mime_type": "image/png",
                        "alt_text": 4,
                    }
                ]
            },
            "alt_text must be a string",
        ),
        ({"attributions": [{"author": 5}]}, "author must be a string or null"),
    ],
)
def test_parse_manifest_rejects_invalid_section_fields(
    tmp_path: Path, updates: dict[str, Any], message: str
) -> None:
    root = make_root(tmp_path / "content")
    section = section_entry(**updates)
    if "parent_id" in updates and updates["parent_id"] is None:
        section.pop("parent_id")

    with pytest.raises(ContentValidationError, match=message):
        parse_manifest(manifest_payload([section]), root)


def test_parse_manifest_requires_parent_id_field(tmp_path: Path) -> None:
    root = make_root(tmp_path / "content")
    section = section_entry()
    section.pop("parent_id")

    with pytest.raises(ContentValidationError, match="parent_id is required"):
        parse_manifest(manifest_payload([section]), root)
