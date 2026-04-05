from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from workspace.adapters.git import DulwichGitClient

if TYPE_CHECKING:
    import pytest


def test_dulwich_clone_passes_ssh_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_clone(source: str, target: str, **kwargs: str) -> None:
        captured["source"] = source
        captured["target"] = target
        captured["kwargs"] = kwargs

    monkeypatch.setattr("workspace.adapters.git.porcelain.clone", fake_clone)

    client = DulwichGitClient()
    client.clone(
        repository_url="git@github.com:org/api.git",
        destination=Path("/tmp/projects/api"),
        ssh_key_path=Path("/tmp/.secrets/id_workspace"),
    )

    assert captured == {
        "source": "git@github.com:org/api.git",
        "target": "/tmp/projects/api",
        "kwargs": {
            "key_filename": "/tmp/.secrets/id_workspace",
            "ssh_command": "ssh -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new",
        },
    }


def test_dulwich_clone_omits_ssh_configuration_for_https(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_clone(source: str, target: str, **kwargs: str) -> None:
        captured["source"] = source
        captured["target"] = target
        captured["kwargs"] = kwargs

    monkeypatch.setattr("workspace.adapters.git.porcelain.clone", fake_clone)

    client = DulwichGitClient()
    client.clone(
        repository_url="https://github.com/org/api.git",
        destination=Path("/tmp/projects/api"),
        ssh_key_path=Path("/tmp/.secrets/id_workspace"),
    )

    assert captured == {
        "source": "https://github.com/org/api.git",
        "target": "/tmp/projects/api",
        "kwargs": {},
    }
