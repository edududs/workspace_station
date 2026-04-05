from __future__ import annotations

from dataclasses import dataclass
from subprocess import CalledProcessError, run
from typing import TYPE_CHECKING

from dulwich import porcelain
from dulwich.errors import GitProtocolError, HangupException

from workspace.application.ports import GitClientPort

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(slots=True)
class DulwichGitClient(GitClientPort):
    """Git adapter backed by dulwich for clone operations."""

    def clone(self, *, repository_url: str, destination: Path, ssh_key_path: Path | None) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            if ssh_key_path is not None and _uses_ssh(repository_url):
                porcelain.clone(
                    repository_url,
                    target=str(destination),
                    key_filename=str(ssh_key_path),
                    ssh_command=_ssh_command(),
                )
            else:
                porcelain.clone(repository_url, target=str(destination))
        except (GitProtocolError, HangupException) as error:
            msg = f"Git clone failed for '{destination.name}'."
            raise RuntimeError(msg) from error


@dataclass(slots=True)
class SubprocessGitClient(GitClientPort):
    """Alternative adapter backed by the local `git` CLI binary."""

    executable: str = "git"

    def clone(self, *, repository_url: str, destination: Path, ssh_key_path: Path | None) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)

        command = [self.executable, "clone", repository_url, str(destination)]
        if ssh_key_path is not None and _uses_ssh(repository_url):
            ssh_command = (
                f"ssh -i {ssh_key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
            )
            command = [
                "env",
                f"GIT_SSH_COMMAND={ssh_command}",
                *command,
            ]

        try:
            run(command, check=True)
        except CalledProcessError as error:
            msg = f"Git clone failed for '{destination.name}'."
            raise RuntimeError(msg) from error


def _uses_ssh(repository_url: str) -> bool:
    return repository_url.startswith(("git@", "ssh://"))


def _ssh_command() -> str:
    return "ssh -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
