from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from workspace.application.ports import WorkspaceMembersPort

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True)
class PyprojectWorkspaceMembers(WorkspaceMembersPort):
    pyproject_path: Path

    def replace_members(self, members: tuple[str, ...]) -> tuple[str, ...]:
        serialized_members = tuple(sorted(dict.fromkeys(members)))
        content = self.pyproject_path.read_text(encoding="utf-8")
        updated_content = _replace_workspace_block(content, serialized_members)
        self.pyproject_path.write_text(updated_content, encoding="utf-8")
        return serialized_members


def _replace_workspace_block(content: str, members: tuple[str, ...]) -> str:
    block = _render_workspace_block(members)
    lines = content.splitlines()

    start_index: int | None = None
    end_index = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == "[tool.uv.workspace]":
            start_index = index
            continue
        if start_index is not None and line.startswith("[") and line.endswith("]"):
            end_index = index
            break

    if start_index is None:
        insertion_index = _find_insertion_index(lines)
        new_lines = [*lines[:insertion_index], *block, *lines[insertion_index:]]
    else:
        new_lines = [*lines[:start_index], *block, *lines[end_index:]]

    return "\n".join(new_lines).rstrip() + "\n"


def _render_workspace_block(members: tuple[str, ...]) -> list[str]:
    member_list = ", ".join(f'"{member}"' for member in members)
    return ["[tool.uv.workspace]", f"members = [{member_list}]", ""]


def _find_insertion_index(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if line.strip() == "[tool.ruff]":
            return index
    return len(lines)
