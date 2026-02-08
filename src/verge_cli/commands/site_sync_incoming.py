"""Incoming site sync management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import SITE_SYNC_INCOMING_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="incoming",
    help="Manage incoming site syncs.",
    no_args_is_help=True,
)


def _sync_to_dict(sync: Any) -> dict[str, Any]:
    """Convert a SiteSyncIncoming SDK object to a dict for output."""
    return {
        "$key": sync.key,
        "name": sync.name,
        "site": sync.get("site"),
        "status": sync.get("status"),
        "enabled": sync.get("enabled"),
        "state": sync.get("state"),
        "last_sync": sync.get("last_sync"),
        "min_snapshots": sync.get("min_snapshots"),
        "description": sync.get("description", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    site: Annotated[
        str | None,
        typer.Option("--site", "-s", help="Filter by site (name or key)"),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option(
            "--enabled/--disabled",
            help="Filter by enabled state",
        ),
    ] = None,
) -> None:
    """List all incoming site syncs."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}

    if site is not None:
        # If numeric, use site_key; otherwise use site_name
        if site.isdigit():
            kwargs["site_key"] = int(site)
        else:
            kwargs["site_name"] = site

    if enabled is not None:
        kwargs["enabled"] = enabled

    syncs = vctx.client.site_syncs_incoming.list(**kwargs)
    data = [_sync_to_dict(s) for s in syncs]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SITE_SYNC_INCOMING_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Get details of an incoming site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs_incoming, sync, "Incoming Sync")
    item = vctx.client.site_syncs_incoming.get(key)
    output_result(
        _sync_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("enable")
@handle_errors()
def enable_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Enable an incoming site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs_incoming, sync, "Incoming Sync")
    vctx.client.site_syncs_incoming.enable(key)
    output_success(f"Enabled incoming sync '{sync}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Disable an incoming site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs_incoming, sync, "Incoming Sync")
    vctx.client.site_syncs_incoming.disable(key)
    output_success(f"Disabled incoming sync '{sync}'", quiet=vctx.quiet)
