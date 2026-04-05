from __future__ import annotations

import textwrap

from workspace.adapters.workspace import LocalProjectWorkspace
from workspace.adapters.workspace_members import PyprojectWorkspaceMembers


def test_replace_members_updates_existing_workspace_block(tmp_path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        '[project]\nname = "workspace"\n\n[tool.uv.workspace]\nmembers = ["projects/old"]\n\n[tool.ruff]\nline-length = 100\n',
        encoding="utf-8",
    )

    adapter = PyprojectWorkspaceMembers(pyproject_path)

    members = adapter.replace_members(("projects/api", "projects/worker"))

    assert members == ("projects/api", "projects/worker")
    assert pyproject_path.read_text(encoding="utf-8") == '[project]\nname = "workspace"\n\n[tool.uv.workspace]\nmembers = ["projects/api", "projects/worker"]\n\n[tool.ruff]\nline-length = 100\n'


def test_replace_members_inserts_workspace_block_when_missing(tmp_path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        '[project]\nname = "workspace"\n\n[tool.ruff]\nline-length = 100\n',
        encoding="utf-8",
    )

    adapter = PyprojectWorkspaceMembers(pyproject_path)

    adapter.replace_members(("projects/api",))

    assert pyproject_path.read_text(encoding="utf-8") == '[project]\nname = "workspace"\n\n[tool.uv.workspace]\nmembers = ["projects/api"]\n\n[tool.ruff]\nline-length = 100\n'


def test_local_workspace_skips_nested_uv_workspace_projects(tmp_path) -> None:
    root = tmp_path / "projects"
    root.mkdir()

    plain = root / "plain"
    plain.mkdir()
    (plain / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "plain"
            version = "0.1.0"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    nested = root / "nested"
    nested.mkdir()
    (nested / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [project]
            name = "nested"
            version = "0.1.0"

            [tool.uv.workspace]
            members = ["a"]
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    workspace = LocalProjectWorkspace(root)

    assert workspace.list_python_project_names() == ["plain"]
