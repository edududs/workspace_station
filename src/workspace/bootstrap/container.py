from __future__ import annotations

from pathlib import Path

from workspace.adapters.catalog import JsonProjectCatalog
from workspace.adapters.git import DulwichGitClient
from workspace.adapters.secrets import FileSecretKeyStore
from workspace.adapters.workspace import LocalProjectWorkspace
from workspace.adapters.workspace_members import PyprojectWorkspaceMembers
from workspace.application.use_cases import WorkspaceService


def resolve_workspace_root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parents[3]


def build_workspace_service(root: Path | None = None) -> WorkspaceService:
    workspace_root = resolve_workspace_root(root)
    return WorkspaceService(
        catalog=JsonProjectCatalog(workspace_root / "projects.json"),
        git_client=DulwichGitClient(),
        workspace=LocalProjectWorkspace(workspace_root / "projects"),
        workspace_members=PyprojectWorkspaceMembers(workspace_root / "pyproject.toml"),
        secret_key_store=FileSecretKeyStore(workspace_root / ".secrets" / "id_workspace"),
    )
