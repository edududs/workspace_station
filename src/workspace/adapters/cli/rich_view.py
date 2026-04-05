from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from workspace.domain.models import ManagedRepository


@dataclass(slots=True)
class RichCliView:
    workspace_root: Path
    console: Console = field(default_factory=Console)

    def print_empty_state(self) -> None:
        self.console.print(
            Panel(
                "Nenhum repositório configurado ou clonado ainda.",
                title="workspace",
                border_style="cyan",
            )
        )

    def print_repository_table(self, repositories: list[ManagedRepository]) -> None:
        table = Table(
            title="Workspace Repositories",
            header_style="bold bright_white",
            border_style="cyan",
            row_styles=["none", "dim"],
        )
        table.add_column("Name", style="bold green")
        table.add_column("State", justify="center")
        table.add_column("Path", style="blue")
        table.add_column("Configured URL", style="magenta")

        for repository in repositories:
            table.add_row(
                repository.name,
                self._state_text(repository.state),
                self._display_path(repository.path),
                repository.configured_url or "[dim]-[/dim]",
            )

        self.console.print(table)

    def print_clone_success(self, name: str, path: Path) -> None:
        self.console.print(
            Panel.fit(
                f"[bold green]{name}[/bold green]\n[path]{self._display_path(path)}[/path]",
                title="Clone Complete",
                border_style="green",
            )
        )

    def print_delete_success(self, name: str) -> None:
        self.console.print(
            Panel.fit(
                f"[bold red]{name}[/bold red] removido do workspace.",
                title="Deleted",
                border_style="red",
            )
        )

    def print_cancelled(self) -> None:
        self.console.print("[yellow]Operação cancelada.[/yellow]")

    def print_error(self, message: str) -> None:
        self.console.print(
            Panel.fit(
                f"[bold red]{message}[/bold red]",
                title="Error",
                border_style="red",
            ),
            stderr=True,  # pyright: ignore[reportCallIssue]
        )

    def _state_text(self, state: str) -> Text:
        if state == "present":
            return Text("present", style="bold green")
        return Text("missing", style="bold yellow")

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.workspace_root))
        except ValueError:
            return str(path)
