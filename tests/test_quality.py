from __future__ import annotations

from pathlib import Path

from workspace.application.quality import (
    QualityService,
    build_commands,
    discover_python_targets,
    resolve_targets,
)


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def run(self, command: tuple[str, ...]) -> None:
        self.commands.append(command)


def test_resolve_targets_defaults_to_current_directory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert resolve_targets(()) == (tmp_path,)


def test_build_commands_keeps_expected_order() -> None:
    commands = build_commands((Path("src/workspace"),))

    assert commands == (
        ("basedpyright", "src/workspace"),
        ("ruff", "check", "--fix", "--unsafe-fixes", "src/workspace"),
        ("ruff", "format", "src/workspace"),
    )


def test_quality_service_runs_all_commands() -> None:
    runner = FakeRunner()
    service = QualityService(runner=runner)

    service.run_checks((Path("src/workspace"),))

    assert len(runner.commands) == 3
    assert runner.commands[0][0] == "basedpyright"
    assert runner.commands[1][:4] == ("ruff", "check", "--fix", "--unsafe-fixes")
    assert runner.commands[2][0:2] == ("ruff", "format")
    assert "src/workspace/application/quality.py" in runner.commands[0]


def test_discover_python_targets_respects_ignore_patterns(tmp_path) -> None:
    source_dir = tmp_path / "src"
    tests_dir = tmp_path / "tests"
    source_dir.mkdir()
    tests_dir.mkdir()
    (source_dir / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tests_dir / "test_app.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")

    targets = discover_python_targets((tmp_path,), ("tests",))

    assert targets == (source_dir / "app.py",)
