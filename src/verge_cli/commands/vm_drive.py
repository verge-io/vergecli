"""VM drive sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.template.units import parse_disk_size
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="drive",
    help="Manage VM drives.",
    no_args_is_help=True,
)

DRIVE_LIST_COLUMNS = ["name", "media", "interface", "size_gb", "tier", "enabled"]


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _drive_to_dict(drive: Any) -> dict[str, Any]:
    """Convert a Drive object to a dict for output."""
    return {
        "key": drive.key,
        "name": drive.name,
        "description": drive.get("description", ""),
        "media": drive.get("media", ""),
        "interface": drive.get("interface", ""),
        "size_gb": drive.size_gb,
        "tier": drive.get("preferred_tier", ""),
        "enabled": drive.is_enabled,
        "readonly": drive.is_readonly,
    }


def _resolve_drive(vm_obj: Any, identifier: str) -> int:
    """Resolve a drive name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    drives = vm_obj.drives.list()
    matches = [d for d in drives if d.name == identifier]
    if len(matches) == 1:
        return matches[0].key
    if len(matches) > 1:
        typer.echo(f"Error: Multiple drives match '{identifier}'. Use a numeric key.", err=True)
        raise typer.Exit(7)
    typer.echo(f"Error: Drive '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def drive_list(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    media: Annotated[
        str | None, typer.Option("--media", help="Filter by media type (disk, cdrom)")
    ] = None,
) -> None:
    """List drives attached to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drives = vm_obj.drives.list(media=media)
    data = [_drive_to_dict(d) for d in drives]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=DRIVE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def drive_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
) -> None:
    """Get details of a VM drive."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)
    drive_obj = vm_obj.drives.get(drive_key)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def drive_create(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    size: Annotated[
        str | None,
        typer.Option("--size", "-s", help="Disk size (e.g., 50GB, 1TB)"),
    ] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Drive name")] = None,
    interface: Annotated[
        str, typer.Option("--interface", "-i", help="Drive interface")
    ] = "virtio-scsi",
    media: Annotated[str, typer.Option("--media", "-m", help="Media type")] = "disk",
    tier: Annotated[int | None, typer.Option("--tier", "-t", help="Storage tier (1-5)")] = None,
    description: Annotated[str, typer.Option("--description", help="Description")] = "",
    media_source: Annotated[
        str | None, typer.Option("--media-source", help="Media file ID or name (for cdrom/import)")
    ] = None,
) -> None:
    """Add a drive to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)

    size_gb = parse_disk_size(size) if size else None

    # Resolve media_source to int if numeric
    resolved_source = None
    if media_source is not None:
        resolved_source = int(media_source) if media_source.isdigit() else media_source

    drive_obj = vm_obj.drives.create(
        size_gb=size_gb,
        name=name,
        interface=interface,
        media=media,
        tier=tier,
        description=description,
        media_source=resolved_source,
    )

    output_success(f"Created drive '{drive_obj.name}' (key: {drive_obj.key})", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def drive_update(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name")] = None,
    size: Annotated[str | None, typer.Option("--size", "-s", help="New size")] = None,
    tier: Annotated[int | None, typer.Option("--tier", "-t", help="Storage tier")] = None,
    enabled: Annotated[
        bool | None, typer.Option("--enabled/--disabled", help="Enable/disable")
    ] = None,
) -> None:
    """Update a VM drive."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if size is not None:
        updates["size_gb"] = parse_disk_size(size)
    if tier is not None:
        updates["preferred_tier"] = tier
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    drive_obj = vm_obj.drives.update(drive_key, **updates)
    output_success(f"Updated drive '{drive_obj.name}'", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def drive_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a drive from a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)

    if not confirm_action(f"Delete drive '{drive}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vm_obj.drives.delete(drive_key)
    output_success(f"Deleted drive '{drive}'", quiet=vctx.quiet)


@app.command("import")
@handle_errors()
def drive_import(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    file_name: Annotated[
        str | None,
        typer.Option("--file-name", help="Source file name (e.g., disk.vmdk)"),
    ] = None,
    file_key: Annotated[int | None, typer.Option("--file-key", help="Source file key")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Drive name")] = None,
    interface: Annotated[str, typer.Option("--interface", help="Drive interface")] = "virtio-scsi",
    tier: Annotated[int | None, typer.Option("--tier", help="Storage tier")] = None,
) -> None:
    """Import a drive from a file (VMDK, QCOW2, VHD, OVA)."""
    vctx, vm_obj = _get_vm(ctx, vm)

    if not file_name and not file_key:
        typer.echo("Error: Provide --file-name or --file-key.", err=True)
        raise typer.Exit(2)

    drive_obj = vm_obj.drives.import_drive(
        file_key=file_key,
        file_name=file_name,
        name=name,
        interface=interface,
        tier=tier,
    )

    output_success(f"Imported drive '{drive_obj.name}' (key: {drive_obj.key})", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
