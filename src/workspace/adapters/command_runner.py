from __future__ import annotations

from dataclasses import dataclass, field
from subprocess import CalledProcessError, run

from rich.console import Console

from workspace.application.ports import CommandRunnerPort


class CommandExecutionError(RuntimeError):
    """Raised when an external quality command fails."""


@dataclass(slots=True)
class SubprocessCommandRunner(CommandRunnerPort):
    console: Console = field(default_factory=Console)

    def run(self, command: tuple[str, ...]) -> None:
        self.console.print(f"[cyan]$ {' '.join(command)}[/cyan]")
        try:
            run(command, check=True)
        except CalledProcessError as error:
            msg = f"Command failed: {' '.join(command)}"
            raise CommandExecutionError(msg) from error
