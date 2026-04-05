from pathlib import Path
from typing import Annotated

import typer

from workspace.adapters.cli.rich_view import RichCliView
from workspace.application.cache_clean import CacheCleanService
from workspace.bootstrap.container import resolve_workspace_root

view = RichCliView(workspace_root=resolve_workspace_root())


def run_cache_clean(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Optional paths to clean. Defaults to the workspace root."),
    ] = None,
) -> None:
    service = CacheCleanService(workspace_root=resolve_workspace_root())
    summary = service.clean(tuple(paths or []))
    view.print_cache_clean_result(summary)


def main() -> None:
    typer.run(run_cache_clean)
