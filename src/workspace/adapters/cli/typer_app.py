from __future__ import annotations

import typer

from workspace.adapters.cli.rich_view import RichCliView
from workspace.application.use_cases import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    WorkspaceError,
)
from workspace.bootstrap.container import build_workspace_service, resolve_workspace_root

app = typer.Typer(
    add_completion=False,
    help="Manage repositories stored under the local workspace projects directory.",
)
view = RichCliView(workspace_root=resolve_workspace_root())


@app.command("list")
def list_repositories() -> None:
    service = build_workspace_service()
    repositories = service.list_repositories()
    if not repositories:
        view.print_empty_state()
        return

    view.print_repository_table(repositories)


@app.command("clone")
def clone_repository(
    target: str = typer.Argument(
        ...,
        help="Repository URL or a project name already configured in projects.json.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Remove the existing local directory before cloning again.",
    ),
) -> None:
    service = build_workspace_service()
    try:
        repository = service.clone_repository(target=target, force=force)
    except (ProjectAlreadyExistsError, ProjectNotFoundError, WorkspaceError) as error:
        raise typer.Exit(code=_print_error(str(error))) from error

    view.print_clone_success(repository.name, repository.path)


@app.command("delete")
def delete_repository(
    name: str = typer.Argument(..., help="Project name to delete from projects/."),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip the confirmation prompt.",
    ),
) -> None:
    if not force:
        confirmed = typer.confirm(f"Delete project '{name}' from the workspace?", default=False)
        if not confirmed:
            view.print_cancelled()
            raise typer.Exit

    service = build_workspace_service()
    try:
        service.delete_repository(name)
    except ProjectNotFoundError as error:
        raise typer.Exit(code=_print_error(str(error))) from error

    view.print_delete_success(name)


@app.command("sync")
def sync_workspace() -> None:
    service = build_workspace_service()
    members = service.sync_workspace_members()
    view.print_sync_success(members)


def _print_error(message: str) -> int:
    view.print_error(message)
    return 1
