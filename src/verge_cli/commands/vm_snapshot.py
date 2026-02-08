"""VM snapshot sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import VM_SNAPSHOT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="snapshot",
    help="Manage VM snapshots.",
    no_args_is_help=True,
)


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    """Convert a VM Snapshot object to a dict for output."""
    return {
        "$key": snap.key,
        "name": snap.name,
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "quiesced": snap.get("quiesced"),
        "description": snap.get("description", ""),
    }


def _resolve_snapshot(vm_obj: Any, identifier: str) -> int:
    """Resolve a snapshot name or key to an integer key."""
    if identifier.isdigit():
        return int(identifier)
    snapshots = vm_obj.snapshots.list()
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
    vm: Annotated[str, typer.Argument(help="VM name or key")],
) -> None:
    """List snapshots for a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    snapshots = vm_obj.snapshots.list()
    data = [_snapshot_to_dict(s) for s in snapshots]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_SNAPSHOT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def snapshot_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
) -> None:
    """Get details of a VM snapshot."""
    vctx, vm_obj = _get_vm(ctx, vm)
    snap_key = _resolve_snapshot(vm_obj, snapshot)
    snap_obj = vm_obj.snapshots.get(snap_key)
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
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Snapshot name (auto-generated if omitted)"),
    ] = None,
    retention: Annotated[
        int,
        typer.Option("--retention", help="Retention in seconds (0 = never expires)"),
    ] = 86400,
    quiesce: Annotated[
        bool,
        typer.Option("--quiesce", help="Quiesce filesystem (requires guest agent)"),
    ] = False,
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Snapshot description"),
    ] = "",
) -> None:
    """Create a snapshot of a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)

    result = vm_obj.snapshots.create(
        name=name,
        retention=retention,
        quiesce=quiesce,
        description=description,
    )

    # create() returns dict | None
    if result:
        snap_name = result.get("name", name or "snapshot")
        snap_key = result.get("$key", "?")
        output_success(
            f"Created snapshot '{snap_name}' (key: {snap_key})",
            quiet=vctx.quiet,
        )
    else:
        output_success(f"Snapshot created for VM '{vm_obj.name}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def snapshot_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a VM snapshot."""
    vctx, vm_obj = _get_vm(ctx, vm)
    snap_key = _resolve_snapshot(vm_obj, snapshot)

    if not confirm_action(f"Delete snapshot '{snapshot}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vm_obj.snapshots.delete(snap_key)
    output_success(f"Deleted snapshot '{snapshot}'", quiet=vctx.quiet)


@app.command("restore")
@handle_errors()
def snapshot_restore(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="New VM name (clone mode)"),
    ] = None,
    replace: Annotated[
        bool,
        typer.Option("--replace", help="Replace original VM (destructive)"),
    ] = False,
    power_on: Annotated[
        bool,
        typer.Option("--power-on", help="Power on after restore"),
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Restore a VM from a snapshot."""
    # Mutual exclusion check
    if replace and name:
        typer.echo("Error: --replace and --name are mutually exclusive.", err=True)
        raise typer.Exit(2)

    vctx, vm_obj = _get_vm(ctx, vm)
    snap_key = _resolve_snapshot(vm_obj, snapshot)

    if replace:
        if not confirm_action(
            f"Replace VM '{vm_obj.name}' with snapshot '{snapshot}'? "
            "All changes since the snapshot will be lost.",
            yes=yes,
        ):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    vm_obj.snapshots.restore(
        snap_key,
        name=name,
        replace_original=replace,
        power_on=power_on,
    )

    if replace:
        output_success(
            f"Restored VM '{vm_obj.name}' from snapshot '{snapshot}'",
            quiet=vctx.quiet,
        )
    elif name:
        output_success(
            f"Cloned VM '{name}' from snapshot '{snapshot}'",
            quiet=vctx.quiet,
        )
    else:
        output_success(
            f"Restored snapshot '{snapshot}' for VM '{vm_obj.name}'",
            quiet=vctx.quiet,
        )
