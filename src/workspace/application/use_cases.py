from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from workspace.application.ports import (
    GitClientPort,
    ProjectCatalogPort,
    ProjectWorkspacePort,
    SecretKeyPort,
    WorkspaceMembersPort,
    WorkspaceServicePort,
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
class WorkspaceService(WorkspaceServicePort):
    catalog: ProjectCatalogPort
    git_client: GitClientPort
    workspace: ProjectWorkspacePort
    workspace_members: WorkspaceMembersPort
    secret_key_store: SecretKeyPort

    def list_repositories(self) -> list[ManagedRepository]:
        configured = {project.name: project for project in self.catalog.list_projects()}
        discovered_names = set(self.workspace.list_project_names())
        all_names = sorted(configured.keys() | discovered_names)

        repositories: list[ManagedRepository] = []
        for name in all_names:
            configured_project = configured.get(name)
            configured_url = (
                configured_project.url
                if configured_project is not None
                else self.workspace.origin_url(name)
            )
            repositories.append(
                ManagedRepository(
                    name=name,
                    path=self.workspace.project_path(name),
                    exists=self.workspace.exists(name),
                    configured_url=configured_url,
                ),
            )

        return repositories

    def clone_repository(self, target: str, *, force: bool) -> ManagedRepository:
        project = self._resolve_target(target)
        if self.workspace.exists(project.name):
            if not force:
                msg = f"Project '{project.name}' already exists. Use --force to replace it."
                raise ProjectAlreadyExistsError(
                    msg,
                )
            self.workspace.remove(project.name)

        ssh_key_path = self.secret_key_store.get_private_key_path()
        self.git_client.clone(
            repository_url=project.url,
            destination=self.workspace.project_path(project.name),
            ssh_key_path=ssh_key_path,
        )
        self.catalog.upsert_project(project)
        self.sync_workspace_members()

        return ManagedRepository(
            name=project.name,
            path=self.workspace.project_path(project.name),
            exists=True,
            configured_url=project.url,
        )

    def delete_repository(self, name: str) -> None:
        known_project = self.catalog.get_project(name)
        if not self.workspace.exists(name) and known_project is None:
            msg = f"Project '{name}' was not found in projects."
            raise ProjectNotFoundError(msg)

        if self.workspace.exists(name):
            self.workspace.remove(name)

        if known_project is not None:
            self.catalog.delete_project(name)

        self.sync_workspace_members()

    def sync_workspace_members(self) -> tuple[str, ...]:
        members = tuple(f"projects/{name}" for name in self.workspace.list_python_project_names())
        return self.workspace_members.replace_members(members)

    def _resolve_target(self, target: str) -> ProjectDefinition:
        known_project = self.catalog.get_project(target)
        if known_project is not None:
            return known_project

        if not _looks_like_repository_url(target):
            msg = (
                f"Target '{target}' is neither a configured project nor a supported repository URL."
            )
            raise ProjectNotFoundError(msg)

        project_name = _project_name_from_url(target)
        if not project_name:
            msg = f"Could not infer a project name from '{target}'."
            raise InvalidProjectTargetError(msg)

        return ProjectDefinition(name=project_name, url=target)


def _looks_like_repository_url(target: str) -> bool:
    return target.startswith("git@") or "://" in target


def _project_name_from_url(repository_url: str) -> str:
    if repository_url.startswith("git@"):
        suffix = repository_url.rsplit(":", maxsplit=1)[-1]
        return Path(suffix).stem

    parsed = urlparse(repository_url)
    return Path(parsed.path).stem
