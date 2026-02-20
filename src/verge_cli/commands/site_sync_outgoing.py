"""Outgoing site sync management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import SITE_SYNC_OUTGOING_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="outgoing",
    help="Manage outgoing site syncs.",
    no_args_is_help=True,
)


def _sync_to_dict(sync: Any) -> dict[str, Any]:
    """Convert a SiteSyncOutgoing SDK object to a dict for output."""
    return {
        "$key": sync.key,
        "name": sync.name,
        "site": sync.get("site"),
        "status": sync.get("status"),
        "enabled": sync.get("enabled"),
        "state": sync.get("state"),
        "encryption": sync.get("encryption"),
        "compression": sync.get("compression"),
        "threads": sync.get("threads"),
        "last_run": sync.get("last_run"),
        "destination_tier": sync.get("destination_tier"),
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
    """List all outgoing site syncs."""
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

    syncs = vctx.client.site_syncs.list(**kwargs)
    data = [_sync_to_dict(s) for s in syncs]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=SITE_SYNC_OUTGOING_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Get details of an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    item = vctx.client.site_syncs.get(key)
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
    """Enable an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.enable(key)
    output_success(f"Enabled outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Disable an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.disable(key)
    output_success(f"Disabled outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def start_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Trigger an outgoing site sync to run now."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.start(key)
    output_success(f"Started outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("stop")
@handle_errors()
def stop_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Stop a running outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.stop(key)
    output_success(f"Stopped outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("set-throttle")
@handle_errors()
def set_throttle_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
    mbps: Annotated[int, typer.Option("--mbps", help="Throttle limit in Mbps")],
) -> None:
    """Set bandwidth throttle on an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.set_throttle(key, mbps)
    output_success(f"Set throttle to {mbps} Mbps on outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("disable-throttle")
@handle_errors()
def disable_throttle_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Remove bandwidth throttle from an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.disable_throttle(key)
    output_success(f"Disabled throttle on outgoing sync '{sync}'", quiet=vctx.quiet)


@app.command("refresh-remote")
@handle_errors()
def refresh_remote_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync name or key")],
) -> None:
    """Refresh remote snapshots for an outgoing site sync."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.site_syncs, sync, "Outgoing Sync")
    vctx.client.site_syncs.refresh_remote_snapshots(key)
    output_success(f"Refreshed remote snapshots for outgoing sync '{sync}'", quiet=vctx.quiet)
