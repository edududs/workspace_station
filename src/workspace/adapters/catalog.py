from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Self

import orjson

from workspace.application.ports import ProjectCatalogPort
from workspace.domain.models import ProjectDefinition

if TYPE_CHECKING:
    from pathlib import Path

type JsonObject = dict[str, "JsonValue"]
type JsonArray = list["JsonValue"]
type JsonValue = str | int | float | bool | None | JsonObject | JsonArray


@dataclass(frozen=True, slots=True)
class StoredProjectDefinition:
    url: str

    @classmethod
    def from_json_value(cls, value: JsonValue) -> Self:
        if isinstance(value, str):
            return cls(url=value)

        if isinstance(value, dict):
            raw_url = value.get("url")
            if isinstance(raw_url, str):
                return cls(url=raw_url)

        msg = "Invalid project definition payload."
        raise ValueError(msg)

    def to_domain(self, name: str) -> ProjectDefinition:
        return ProjectDefinition(name=name, url=self.url)


@dataclass(frozen=True, slots=True)
class CatalogDocument:
    projects: dict[str, StoredProjectDefinition] = field(default_factory=dict)

    @classmethod
    def from_json_value(cls, value: JsonValue) -> Self:
        if not isinstance(value, dict):
            return cls()

        raw_projects = value.get("projects")
        if not isinstance(raw_projects, dict):
            return cls()

        projects: dict[str, StoredProjectDefinition] = {}
        for name, raw_definition in raw_projects.items():
            if not isinstance(name, str):
                continue
            projects[name] = StoredProjectDefinition.from_json_value(raw_definition)

        return cls(projects=projects)

    def to_json_object(self) -> JsonObject:
        return {
            "projects": {
                name: asdict(project_definition)
                for name, project_definition in sorted(self.projects.items())
            },
        }


@dataclass(slots=True)
class JsonProjectCatalog(ProjectCatalogPort):
    path: Path

    def list_projects(self) -> list[ProjectDefinition]:
        document = self._read()
        return [
            stored_definition.to_domain(name)
            for name, stored_definition in sorted(document.projects.items())
        ]

    def get_project(self, name: str) -> ProjectDefinition | None:
        for project in self.list_projects():
            if project.name == name:
                return project
        return None

    def upsert_project(self, project: ProjectDefinition) -> None:
        document = self._read()
        document.projects[project.name] = StoredProjectDefinition(url=project.url)
        self._write(document)

    def delete_project(self, name: str) -> None:
        document = self._read()
        document.projects.pop(name, None)
        self._write(document)

    def _read(self) -> CatalogDocument:
        if not self.path.exists():
            return CatalogDocument()

        payload = orjson.loads(self.path.read_bytes())
        return CatalogDocument.from_json_value(payload)

    def _write(self, payload: CatalogDocument) -> None:
        self.path.write_bytes(
            orjson.dumps(
                payload.to_json_object(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            + b"\n",
        )
