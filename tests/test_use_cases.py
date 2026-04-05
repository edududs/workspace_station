from __future__ import annotations

from pathlib import Path

import pytest

from workspace.application.use_cases import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    WorkspaceService,
)
from workspace.domain.models import ProjectDefinition


class InMemoryCatalog:
    def __init__(self, projects: list[ProjectDefinition] | None = None) -> None:
        self.projects = {project.name: project for project in projects or []}

    def list_projects(self) -> list[ProjectDefinition]:
        return list(self.projects.values())

    def get_project(self, name: str) -> ProjectDefinition | None:
        return self.projects.get(name)

    def upsert_project(self, project: ProjectDefinition) -> None:
        self.projects[project.name] = project

    def delete_project(self, name: str) -> None:
        self.projects.pop(name, None)


class FakeGitClient:
    def __init__(self, workspace: InMemoryWorkspace | None = None) -> None:
        self.calls: list[tuple[str, Path, Path | None]] = []
        self.workspace = workspace

    def clone(self, *, repository_url: str, destination: Path, ssh_key_path: Path | None) -> None:
        self.calls.append((repository_url, destination, ssh_key_path))
        if self.workspace is not None:
            self.workspace.names.add(destination.name)
            self.workspace.python_projects.add(destination.name)


class InMemoryWorkspace:
    def __init__(
        self,
        names: set[str] | None = None,
        origins: dict[str, str] | None = None,
        python_projects: set[str] | None = None,
    ) -> None:
        self.names = set(names or set())
        self.origins = origins or {}
        self.python_projects = set(python_projects or set(self.names))

    def list_project_names(self) -> list[str]:
        return sorted(self.names)

    def list_python_project_names(self) -> list[str]:
        return sorted(self.python_projects)

    def project_path(self, name: str) -> Path:
        return Path("/tmp/projects") / name

    def exists(self, name: str) -> bool:
        return name in self.names

    def origin_url(self, name: str) -> str | None:
        return self.origins.get(name)

    def remove(self, name: str) -> None:
        self.names.discard(name)
        self.python_projects.discard(name)


class StaticSecretStore:
    def __init__(self, key_path: Path | None = None) -> None:
        self.key_path = key_path

    def get_private_key_path(self) -> Path | None:
        return self.key_path


class FakeWorkspaceMembers:
    def __init__(self) -> None:
        self.members: tuple[str, ...] = ()

    def replace_members(self, members: tuple[str, ...]) -> tuple[str, ...]:
        self.members = members
        return members


def test_list_repositories_merges_configured_and_existing_projects() -> None:
    service = WorkspaceService(
        catalog=InMemoryCatalog([ProjectDefinition(name="api", url="git@github.com:org/api.git")]),
        git_client=FakeGitClient(),
        workspace=InMemoryWorkspace(
            {"api", "worker"},
            origins={"worker": "https://github.com/org/worker.git"},
        ),
        workspace_members=FakeWorkspaceMembers(),
        secret_key_store=StaticSecretStore(),
    )

    repositories = service.list_repositories()

    assert [repository.name for repository in repositories] == ["api", "worker"]
    assert repositories[0].configured_url == "git@github.com:org/api.git"
    assert repositories[1].configured_url == "https://github.com/org/worker.git"


def test_clone_uses_catalog_entry_when_project_name_exists() -> None:
    workspace = InMemoryWorkspace()
    git_client = FakeGitClient(workspace)
    workspace_members = FakeWorkspaceMembers()
    service = WorkspaceService(
        catalog=InMemoryCatalog([ProjectDefinition(name="api", url="git@github.com:org/api.git")]),
        git_client=git_client,
        workspace=workspace,
        workspace_members=workspace_members,
        secret_key_store=StaticSecretStore(Path("/tmp/id_workspace")),
    )

    repository = service.clone_repository("api", force=False)

    assert repository.name == "api"
    assert git_client.calls == [
        ("git@github.com:org/api.git", Path("/tmp/projects/api"), Path("/tmp/id_workspace")),
    ]
    assert workspace_members.members == ("projects/api",)


def test_clone_registers_project_when_target_is_url() -> None:
    catalog = InMemoryCatalog()
    workspace = InMemoryWorkspace()
    workspace_members = FakeWorkspaceMembers()
    service = WorkspaceService(
        catalog=catalog,
        git_client=FakeGitClient(workspace),
        workspace=workspace,
        workspace_members=workspace_members,
        secret_key_store=StaticSecretStore(),
    )

    repository = service.clone_repository("https://github.com/org/new-service.git", force=False)

    assert repository.name == "new-service"
    assert catalog.get_project("new-service") == ProjectDefinition(
        name="new-service",
        url="https://github.com/org/new-service.git",
    )
    assert workspace_members.members == ("projects/new-service",)


def test_clone_requires_force_when_project_already_exists() -> None:
    service = WorkspaceService(
        catalog=InMemoryCatalog([ProjectDefinition(name="api", url="git@github.com:org/api.git")]),
        git_client=FakeGitClient(),
        workspace=InMemoryWorkspace({"api"}),
        workspace_members=FakeWorkspaceMembers(),
        secret_key_store=StaticSecretStore(),
    )

    with pytest.raises(ProjectAlreadyExistsError):
        service.clone_repository("api", force=False)


def test_delete_removes_project_from_workspace_and_catalog() -> None:
    catalog = InMemoryCatalog([ProjectDefinition(name="api", url="git@github.com:org/api.git")])
    workspace = InMemoryWorkspace({"api"})
    workspace_members = FakeWorkspaceMembers()
    service = WorkspaceService(
        catalog=catalog,
        git_client=FakeGitClient(),
        workspace=workspace,
        workspace_members=workspace_members,
        secret_key_store=StaticSecretStore(),
    )

    service.delete_repository("api")

    assert workspace.exists("api") is False
    assert catalog.get_project("api") is None
    assert workspace_members.members == ()


def test_delete_unknown_project_raises_error() -> None:
    service = WorkspaceService(
        catalog=InMemoryCatalog(),
        git_client=FakeGitClient(),
        workspace=InMemoryWorkspace(),
        workspace_members=FakeWorkspaceMembers(),
        secret_key_store=StaticSecretStore(),
    )

    with pytest.raises(ProjectNotFoundError):
        service.delete_repository("missing")


def test_sync_workspace_members_reconciles_python_projects() -> None:
    workspace_members = FakeWorkspaceMembers()
    service = WorkspaceService(
        catalog=InMemoryCatalog(),
        git_client=FakeGitClient(),
        workspace=InMemoryWorkspace({"api", "docs"}, python_projects={"api"}),
        workspace_members=workspace_members,
        secret_key_store=StaticSecretStore(),
    )

    members = service.sync_workspace_members()

    assert members == ("projects/api",)
    assert workspace_members.members == ("projects/api",)
