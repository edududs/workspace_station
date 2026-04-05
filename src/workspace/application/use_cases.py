from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from workspace.application.ports import (
    GitClientPort,
    ProjectCatalogPort,
    ProjectWorkspacePort,
    SecretKeyPort,
)
from workspace.domain.models import ManagedRepository, ProjectDefinition


class WorkspaceError(Exception):
    """Base application error."""


class ProjectNotFoundError(WorkspaceError):
    """Raised when a project alias cannot be found."""


class ProjectAlreadyExistsError(WorkspaceError):
    """Raised when a destination already exists and force was not requested."""


class InvalidProjectTargetError(WorkspaceError):
    """Raised when the target cannot be resolved into a project."""


@dataclass(slots=True)
class WorkspaceService:
    catalog: ProjectCatalogPort
    git_client: GitClientPort
    workspace: ProjectWorkspacePort
    secret_key_store: SecretKeyPort

    def list_repositories(self) -> list[ManagedRepository]:
        configured = {project.name: project for project in self.catalog.list_projects()}
        discovered_names = set(self.workspace.list_project_names())
        all_names = sorted(configured.keys() | discovered_names)

        return [
            ManagedRepository(
                name=name,
                path=self.workspace.project_path(name),
                exists=self.workspace.exists(name),
                configured_url=(
                    configured.get(name).url if name in configured else self.workspace.origin_url(name)
                ),
            )
            for name in all_names
        ]

    def clone_repository(self, target: str, *, force: bool) -> ManagedRepository:
        project = self._resolve_target(target)
        if self.workspace.exists(project.name):
            if not force:
                raise ProjectAlreadyExistsError(
                    f"Project '{project.name}' already exists. Use --force to replace it."
                )
            self.workspace.remove(project.name)

        ssh_key_path = self.secret_key_store.get_private_key_path()
        self.git_client.clone(
            repository_url=project.url,
            destination=self.workspace.project_path(project.name),
            ssh_key_path=ssh_key_path,
        )
        self.catalog.upsert_project(project)

        return ManagedRepository(
            name=project.name,
            path=self.workspace.project_path(project.name),
            exists=True,
            configured_url=project.url,
        )

    def delete_repository(self, name: str) -> None:
        known_project = self.catalog.get_project(name)
        if not self.workspace.exists(name) and known_project is None:
            raise ProjectNotFoundError(f"Project '{name}' was not found in projects.")

        if self.workspace.exists(name):
            self.workspace.remove(name)

        if known_project is not None:
            self.catalog.delete_project(name)

    def _resolve_target(self, target: str) -> ProjectDefinition:
        known_project = self.catalog.get_project(target)
        if known_project is not None:
            return known_project

        if not _looks_like_repository_url(target):
            raise ProjectNotFoundError(
                f"Target '{target}' is neither a configured project nor a supported repository URL."
            )

        project_name = _project_name_from_url(target)
        if not project_name:
            raise InvalidProjectTargetError(f"Could not infer a project name from '{target}'.")

        return ProjectDefinition(name=project_name, url=target)


def _looks_like_repository_url(target: str) -> bool:
    return target.startswith("git@") or "://" in target


def _project_name_from_url(repository_url: str) -> str:
    if repository_url.startswith("git@"):
        suffix = repository_url.rsplit(":", maxsplit=1)[-1]
        return Path(suffix).stem

    parsed = urlparse(repository_url)
    return Path(parsed.path).stem
