from __future__ import annotations

import json

from workspace.adapters.catalog import JsonProjectCatalog
from workspace.domain.models import ProjectDefinition


def test_catalog_reads_legacy_string_payload(tmp_path) -> None:
    catalog_path = tmp_path / "projects.json"
    catalog_path.write_text(
        json.dumps(
            {
                "projects": {
                    "api": "git@github.com:org/api.git",
                },
            },
        ),
        encoding="utf-8",
    )

    catalog = JsonProjectCatalog(catalog_path)

    assert catalog.get_project("api") == ProjectDefinition(
        name="api",
        url="git@github.com:org/api.git",
    )


def test_catalog_persists_object_payload(tmp_path) -> None:
    catalog = JsonProjectCatalog(tmp_path / "projects.json")

    catalog.upsert_project(ProjectDefinition(name="api", url="https://github.com/org/api.git"))

    assert json.loads(catalog.path.read_text(encoding="utf-8")) == {
        "projects": {
            "api": {
                "url": "https://github.com/org/api.git",
            },
        },
    }
