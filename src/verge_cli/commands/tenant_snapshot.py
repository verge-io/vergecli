"""Tenant snapshot sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_SNAPSHOT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="snapshot",
    help="Manage tenant snapshots.",
    no_args_is_help=True,
)


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    """Convert a Tenant Snapshot object to a dict for output."""
    return {
        "$key": snap.key,
        "name": snap.name,
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "profile": snap.get("profile", ""),
    }


def _resolve_snapshot(tenant_obj: Any, identifier: str) -> int:
    """Resolve a snapshot name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    snapshots = tenant_obj.snapshots.list()
    matches = [s for s in snapshots if s.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple snapshots match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Snapshot '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def snapshot_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List snapshots for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snapshots = tenant_obj.snapshots.list()
    data = [_snapshot_to_dict(s) for s in snapshots]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_SNAPSHOT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def snapshot_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
) -> None:
    """Get details of a tenant snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)
    snap_obj = tenant_obj.snapshots.get(snap_key)
    output_result(
        _snapshot_to_dict(snap_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def snapshot_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[str, typer.Option("--name", "-n", help="Snapshot name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Snapshot description")
    ] = "",
    expires_in_days: Annotated[
        int,
        typer.Option("--expires-in-days", help="Days until snapshot expires (0 = never)"),
    ] = 0,
) -> None:
    """Create a snapshot of a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    snap_obj = tenant_obj.snapshots.create(
        name=name,
        description=description,
        expires_in_days=expires_in_days,
    )

    output_success(
        f"Created snapshot '{snap_obj.name}' (key: {snap_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _snapshot_to_dict(snap_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def snapshot_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a tenant snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)

    if not confirm_action(f"Delete snapshot '{snapshot}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.snapshots.delete(snap_key)
    output_success(f"Deleted snapshot '{snapshot}'", quiet=vctx.quiet)


@app.command("restore")
@handle_errors()
def snapshot_restore(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
) -> None:
    """Restore a tenant from a snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)

    tenant_obj.snapshots.restore(snap_key)
    output_success(f"Restored tenant from snapshot '{snapshot}'", quiet=vctx.quiet)
