from __future__ import annotations

import shutil
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from workspace.application.ports import ProjectWorkspacePort


@dataclass(slots=True)
class LocalProjectWorkspace(ProjectWorkspacePort):
    projects_root: Path

    def list_project_names(self) -> list[str]:
        if not self.projects_root.exists():
            return []

        return sorted(path.name for path in self.projects_root.iterdir() if path.is_dir())

    def list_python_project_names(self) -> list[str]:
        return sorted(
            name
            for name in self.list_project_names()
            if self._is_workspace_member_candidate(name)
        )

    def project_path(self, name: str) -> Path:
        self._validate_name(name)
        return self.projects_root / name

    def exists(self, name: str) -> bool:
        return self.project_path(name).exists()

    def origin_url(self, name: str) -> str | None:
        project_path = self.project_path(name)
        if not project_path.exists():
            return None

        try:
            result = subprocess.run(
                ["git", "-C", str(project_path), "config", "--get", "remote.origin.url"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            return None

        origin_url = result.stdout.strip()
        return origin_url or None

    def remove(self, name: str) -> None:
        target = self.project_path(name)
        if target.exists():
            shutil.rmtree(target)

    def _validate_name(self, name: str) -> None:
        candidate = Path(name)
        if candidate.name != name or name in {".", ".."}:
            msg = f"Invalid project name '{name}'."
            raise ValueError(msg)

    def _is_workspace_member_candidate(self, name: str) -> bool:
        pyproject_path = self.project_path(name) / "pyproject.toml"
        if not pyproject_path.exists():
            return False

        return not _declares_nested_uv_workspace(pyproject_path)


def _declares_nested_uv_workspace(pyproject_path: Path) -> bool:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    tool_section = payload.get("tool")
    if not isinstance(tool_section, dict):
        return False

    uv_section = tool_section.get("uv")
    if not isinstance(uv_section, dict):
        return False

    return isinstance(uv_section.get("workspace"), dict)
