from __future__ import annotations

import shutil
from pathlib import Path

from manual_spss.content_model import ManualRepository

PROJECT_CONTENT = Path(__file__).parents[3] / "content"


def test_catalog_loads_from_external_distribution_content(tmp_path: Path) -> None:
    development_repository = ManualRepository.load(PROJECT_CONTENT)
    distribution_content = tmp_path / "dist" / "ManualSPSS" / "content"
    distribution_content.parent.mkdir(parents=True)
    shutil.copytree(PROJECT_CONTENT, distribution_content)

    installed_repository = ManualRepository.load(distribution_content)

    assert (
        installed_repository.manual.manual_id
        == development_repository.manual.manual_id
    )
    assert installed_repository.manual.title == development_repository.manual.title
    installed_ids = [
        section.id for section in installed_repository.sections_in_reading_order()
    ]
    development_ids = [
        section.id for section in development_repository.sections_in_reading_order()
    ]
    assert installed_ids == development_ids

    root = distribution_content.resolve()
    for section in installed_repository.sections_in_reading_order():
        source_section = development_repository.get_section(section.id)
        assert section.body_html == source_section.body_html
        assert section.plain_text == source_section.plain_text
        assert section.resources
        for resource in section.resources:
            assert resource.path.is_relative_to(root)
            assert resource.path.is_file()
