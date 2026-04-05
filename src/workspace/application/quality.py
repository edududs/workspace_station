from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workspace.application.ports import CommandRunnerPort

DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
}


@dataclass(slots=True)
class QualityService:
    runner: CommandRunnerPort

    def run_checks(
        self,
        paths: tuple[Path, ...],
        ignore_patterns: tuple[str, ...] = (),
    ) -> tuple[Path, ...]:
        targets = discover_python_targets(paths, ignore_patterns)
        for command in build_commands(targets):
            self.runner.run(command)
        return targets


def resolve_targets(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    if paths:
        return paths
    return (Path.cwd(),)


def discover_python_targets(
    paths: tuple[Path, ...],
    ignore_patterns: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    discovered: dict[str, Path] = {}
    for path in resolve_targets(paths):
        if path.is_file():
            if _is_python_file(path) and not _matches_ignore(path, ignore_patterns):
                discovered[str(path)] = path
            continue

        if not path.exists():
            continue

        for file_path in _iter_python_files(path, ignore_patterns):
            discovered[str(file_path)] = file_path

    return tuple(discovered[key] for key in sorted(discovered))


def build_commands(paths: tuple[Path, ...]) -> tuple[tuple[str, ...], ...]:
    serialized_paths = tuple(str(path) for path in paths)
    return (
        ("basedpyright", *serialized_paths),
        ("ruff", "check", "--fix", "--unsafe-fixes", *serialized_paths),
        ("ruff", "format", *serialized_paths),
    )


def _iter_python_files(root: Path, ignore_patterns: tuple[str, ...]) -> tuple[Path, ...]:
    matches: list[Path] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in DEFAULT_IGNORED_DIRECTORIES for part in file_path.parts):
            continue
        if not _is_python_file(file_path):
            continue
        if _matches_ignore(file_path, ignore_patterns):
            continue
        matches.append(file_path)
    return tuple(matches)


def _is_python_file(path: Path) -> bool:
    return path.suffix in {".py", ".pyi"}


def _matches_ignore(path: Path, ignore_patterns: tuple[str, ...]) -> bool:
    if not ignore_patterns:
        return False

    normalized_path = path.as_posix()
    return any(pattern in normalized_path for pattern in ignore_patterns if pattern)
