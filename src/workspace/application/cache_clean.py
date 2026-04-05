from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

CACHE_DIRECTORIES = frozenset(
    {
        "__pycache__",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        ".pyre",
        ".pytype",
        ".hypothesis",
        ".tox",
        ".nox",
        ".uv-cache",
    },
)

CACHE_FILES = frozenset(
    {
        ".coverage",
        ".dmypy.json",
    },
)


@dataclass(frozen=True, slots=True)
class CacheCleanSummary:
    targets: tuple[Path, ...]
    removed_paths: tuple[Path, ...]
    removed_file_count: int
    size_before_bytes: int
    size_after_bytes: int


@dataclass(slots=True)
class CacheCleanService:
    workspace_root: Path

    def clean(self, paths: tuple[Path, ...]) -> CacheCleanSummary:
        targets = paths or (self.workspace_root,)
        size_before_bytes = sum(_measure_path_size(target) for target in targets)
        candidates = _discover_cache_paths(targets)
        removed_file_count = sum(_count_files(candidate) for candidate in candidates)
        for candidate in candidates:
            _remove_path(candidate)
        size_after_bytes = sum(_measure_path_size(target) for target in targets)
        return CacheCleanSummary(
            targets=targets,
            removed_paths=candidates,
            removed_file_count=removed_file_count,
            size_before_bytes=size_before_bytes,
            size_after_bytes=size_after_bytes,
        )


def _discover_cache_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    discovered: dict[str, Path] = {}
    for root in paths:
        if not root.exists():
            continue

        for candidate in _iter_cache_candidates(root):
            discovered[str(candidate)] = candidate

    sorted_keys = sorted(
        discovered,
        key=lambda item: (len(Path(item).parts), item),
        reverse=True,
    )
    return tuple(discovered[key] for key in sorted_keys)


def _iter_cache_candidates(root: Path) -> tuple[Path, ...]:
    matches: list[Path] = []
    if _is_cache_path(root):
        matches.append(root)

    matches.extend(path for path in root.rglob("*") if _is_cache_path(path))

    return tuple(matches)


def _is_cache_path(path: Path) -> bool:
    if path.is_dir():
        return path.name in CACHE_DIRECTORIES
    if path.is_file():
        return path.name in CACHE_FILES
    return False


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        return
    if path.exists():
        path.unlink()


def _count_files(path: Path) -> int:
    if path.is_file():
        return 1
    if not path.exists():
        return 0
    return sum(1 for nested in path.rglob("*") if nested.is_file())


def _measure_path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(nested.stat().st_size for nested in path.rglob("*") if nested.is_file())
