"""Catalog repository management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.commands import catalog_repo_log
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="repo",
    help="Manage catalog repositories.",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(catalog_repo_log.app, name="log")

REPO_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("type"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Y": "green", "-": "red"}),
    ColumnDef("auto_refresh", header="Auto Refresh", format_fn=format_bool_yn),
    ColumnDef("url", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("max_tier", header="Max Tier", wide_only=True),
    ColumnDef("last_refreshed", header="Last Refreshed", wide_only=True),
]

REPO_STATUS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef(
        "status",
        style_map={
            "online": "green",
            "refreshing": "yellow",
            "downloading": "cyan",
            "error": "red",
        },
    ),
    ColumnDef("state"),
    ColumnDef("info"),
    ColumnDef("last_update", header="Last Update"),
]


def _repo_to_dict(repo: Any) -> dict[str, Any]:
    """Convert a CatalogRepository SDK object to a dict for output."""
    return {
        "$key": int(repo.key),
        "name": repo.name,
        "type": repo.get("type", ""),
        "description": repo.get("description", ""),
        "url": repo.get("url", ""),
        "enabled": repo.get("enabled"),
        "auto_refresh": repo.get("auto_refresh"),
        "max_tier": repo.get("max_tier", ""),
        "last_refreshed": repo.get("last_refreshed", ""),
    }


def _status_to_dict(status: Any) -> dict[str, Any]:
    """Convert a CatalogRepositoryStatus SDK object to a dict for output."""
    return {
        "$key": int(status.key),
        "status": status.get("status", ""),
        "state": status.get("state", ""),
        "info": status.get("info", ""),
        "last_update": status.get("last_update", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    filter: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression."),
    ] = None,
    type: Annotated[
        str | None,
        typer.Option(
            "--type", help="Filter by repository type (local/remote/provider/remote-git/yottabyte)."
        ),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Filter by enabled state."),
    ] = None,
) -> None:
    """List catalog repositories."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if filter is not None:
        kwargs["filter"] = filter
    if type is not None:
        kwargs["type"] = type
    if enabled is not None:
        kwargs["enabled"] = enabled
    repos = vctx.client.catalog_repositories.list(**kwargs)
    data = [_repo_to_dict(r) for r in repos]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=REPO_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    repo: Annotated[str, typer.Argument(help="Repository ID or name.")],
) -> None:
    """Get a catalog repository by ID or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.catalog_repositories,
        repo,
        "Catalog repository",
    )
    item = vctx.client.catalog_repositories.get(key=key)
    output_result(
        _repo_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=REPO_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", help="Repository name.")],
    type: Annotated[
        str,
        typer.Option("--type", help="Repository type."),
    ] = "local",
    url: Annotated[
        str | None,
        typer.Option("--url", help="URL for remote repositories."),
    ] = None,
    user: Annotated[
        str | None,
        typer.Option("--user", help="Username for authentication."),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option("--password", help="Password for authentication."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", help="Repository description."),
    ] = None,
    allow_insecure: Annotated[
        bool,
        typer.Option("--allow-insecure", help="Allow insecure SSL certificates."),
    ] = False,
    no_auto_refresh: Annotated[
        bool,
        typer.Option("--no-auto-refresh", help="Disable automatic refresh."),
    ] = False,
    max_tier: Annotated[
        str,
        typer.Option("--max-tier", help="Maximum storage tier for downloads (1-5)."),
    ] = "1",
    override_default_scope: Annotated[
        str,
        typer.Option(
            "--override-default-scope",
            help="Override default publishing scope (none/private/global/tenant).",
        ),
    ] = "none",
) -> None:
    """Create a new catalog repository."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {
        "name": name,
        "type": type,
        "auto_refresh": not no_auto_refresh,
        "max_tier": max_tier,
        "override_default_scope": override_default_scope,
    }
    if url is not None:
        kwargs["url"] = url
    if user is not None:
        kwargs["user"] = user
    if password is not None:
        kwargs["password"] = password
    if description is not None:
        kwargs["description"] = description
    if allow_insecure:
        kwargs["allow_insecure"] = True
    result = vctx.client.catalog_repositories.create(**kwargs)
    output_result(
        _repo_to_dict(result),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=REPO_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    repo: Annotated[str, typer.Argument(help="Repository ID or name.")],
    name: Annotated[
        str | None,
        typer.Option("--name", help="New repository name."),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", help="New description."),
    ] = None,
    url: Annotated[
        str | None,
        typer.Option("--url", help="New URL."),
    ] = None,
    user: Annotated[
        str | None,
        typer.Option("--user", help="New username."),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option("--password", help="New password."),
    ] = None,
    allow_insecure: Annotated[
        bool | None,
        typer.Option("--allow-insecure/--no-allow-insecure", help="Allow insecure SSL."),
    ] = None,
    auto_refresh: Annotated[
        bool | None,
        typer.Option("--auto-refresh/--no-auto-refresh", help="Enable or disable auto refresh."),
    ] = None,
    max_tier: Annotated[
        str | None,
        typer.Option("--max-tier", help="Maximum storage tier."),
    ] = None,
    override_default_scope: Annotated[
        str | None,
        typer.Option("--override-default-scope", help="Override default scope."),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Enable or disable repository."),
    ] = None,
) -> None:
    """Update a catalog repository."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.catalog_repositories,
        repo,
        "Catalog repository",
    )
    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if description is not None:
        kwargs["description"] = description
    if url is not None:
        kwargs["url"] = url
    if user is not None:
        kwargs["user"] = user
    if password is not None:
        kwargs["password"] = password
    if allow_insecure is not None:
        kwargs["allow_insecure"] = allow_insecure
    if auto_refresh is not None:
        kwargs["auto_refresh"] = auto_refresh
    if max_tier is not None:
        kwargs["max_tier"] = max_tier
    if override_default_scope is not None:
        kwargs["override_default_scope"] = override_default_scope
    if enabled is not None:
        kwargs["enabled"] = enabled
    result = vctx.client.catalog_repositories.update(key, **kwargs)
    output_result(
        _repo_to_dict(result),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=REPO_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    repo: Annotated[str, typer.Argument(help="Repository ID or name.")],
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Delete a catalog repository."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.catalog_repositories,
        repo,
        "Catalog repository",
    )
    if not confirm_action(f"Delete catalog repository {repo}?", yes=yes):
        raise typer.Abort()
    vctx.client.catalog_repositories.delete(key)
    output_success(f"Catalog repository '{repo}' deleted.", quiet=vctx.quiet)


@app.command("refresh")
@handle_errors()
def refresh_cmd(
    ctx: typer.Context,
    repo: Annotated[str, typer.Argument(help="Repository ID or name.")],
) -> None:
    """Refresh a catalog repository to fetch latest catalogs."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.catalog_repositories,
        repo,
        "Catalog repository",
    )
    vctx.client.catalog_repositories.refresh(key)
    output_success(f"Catalog repository '{repo}' refresh initiated.", quiet=vctx.quiet)


@app.command("status")
@handle_errors()
def status_cmd(
    ctx: typer.Context,
    repo: Annotated[str, typer.Argument(help="Repository ID or name.")],
) -> None:
    """Show catalog repository status."""
    vctx = get_context(ctx)
    key = resolve_resource_id(
        vctx.client.catalog_repositories,
        repo,
        "Catalog repository",
    )
    status = vctx.client.catalog_repositories.get_status(key)
    output_result(
        _status_to_dict(status),
        output_format=vctx.output_format,
        query=vctx.query,
        columns=REPO_STATUS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
