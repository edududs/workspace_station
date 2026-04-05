from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from workspace.adapters.command_runner import CommandExecutionError, SubprocessCommandRunner
from workspace.application.quality import QualityService

console = Console(stderr=True)


def run_quality(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Optional paths to check. Defaults to the current working directory."),
    ] = None,
    ignore: Annotated[
        list[str] | None,
        typer.Option(
            "--ignore",
            "-I",
            help="Substring pattern to ignore while collecting Python files. Repeatable.",
        ),
    ] = None,
) -> None:
    service = QualityService(runner=SubprocessCommandRunner())
    try:
        service.run_checks(tuple(paths or []), tuple(ignore or []))
    except CommandExecutionError as error:
        console.print(
            Panel.fit(
                f"[bold red]{error}[/bold red]",
                title="Check Failed",
                border_style="red",
            ),
        )
        raise typer.Exit(code=1) from None


def main() -> None:
    typer.run(run_quality)
