from __future__ import annotations

from workspace.application.cache_clean import CacheCleanService


def test_cache_clean_defaults_to_workspace_root(tmp_path) -> None:
    cache_dir = tmp_path / ".ruff_cache"
    cache_dir.mkdir()
    nested_file = cache_dir / "data.bin"
    nested_file.write_bytes(b"1234")
    cache_file = tmp_path / ".coverage"
    cache_file.write_text("data", encoding="utf-8")
    source_file = tmp_path / "main.py"
    source_file.write_text("print('ok')\n", encoding="utf-8")

    service = CacheCleanService(workspace_root=tmp_path)

    summary = service.clean(())

    assert cache_dir in summary.removed_paths
    assert cache_file in summary.removed_paths
    assert summary.removed_file_count == 2
    assert summary.size_before_bytes > summary.size_after_bytes
    assert summary.size_after_bytes == source_file.stat().st_size
    assert not cache_dir.exists()
    assert not cache_file.exists()


def test_cache_clean_respects_explicit_paths(tmp_path) -> None:
    inside = tmp_path / "inside"
    outside = tmp_path / "outside"
    inside.mkdir()
    outside.mkdir()
    inside_cache = inside / "__pycache__"
    outside_cache = outside / ".pytest_cache"
    inside_cache.mkdir()
    outside_cache.mkdir()

    service = CacheCleanService(workspace_root=tmp_path)

    summary = service.clean((inside,))

    assert summary.removed_paths == (inside_cache,)
    assert not inside_cache.exists()
    assert outside_cache.exists()
