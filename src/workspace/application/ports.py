from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from workspace.domain.models import ManagedRepository, ProjectDefinition


class ProjectCatalogPort(Protocol):
    def list_projects(self) -> list[ProjectDefinition]: ...

    def get_project(self, name: str) -> ProjectDefinition | None: ...

    def upsert_project(self, project: ProjectDefinition) -> None: ...

    def delete_project(self, name: str) -> None: ...


class GitClientPort(Protocol):
    def clone(
        self,
        *,
        repository_url: str,
        destination: Path,
        ssh_key_path: Path | None,
    ) -> None: ...


class ProjectWorkspacePort(Protocol):
    def list_project_names(self) -> list[str]: ...

    def list_python_project_names(self) -> list[str]: ...

    def project_path(self, name: str) -> Path: ...

    def exists(self, name: str) -> bool: ...

    def origin_url(self, name: str) -> str | None: ...

    def remove(self, name: str) -> None: ...


class SecretKeyPort(Protocol):
    def get_private_key_path(self) -> Path | None: ...


class CommandRunnerPort(Protocol):
    def run(self, command: tuple[str, ...]) -> None: ...


class WorkspaceMembersPort(Protocol):
    def replace_members(self, members: tuple[str, ...]) -> tuple[str, ...]: ...


class WorkspaceServicePort(Protocol):
    def list_repositories(self) -> list[ManagedRepository]: ...

    def clone_repository(self, target: str, *, force: bool) -> ManagedRepository: ...

    def delete_repository(self, name: str) -> None: ...

    def sync_workspace_members(self) -> tuple[str, ...]: ...
