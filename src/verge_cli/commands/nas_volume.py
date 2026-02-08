"""NAS volume management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource, resolve_resource_id

app = typer.Typer(
    name="volume",
    help="Manage NAS volumes.",
    no_args_is_help=True,
)

NAS_VOLUME_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("size_gb", header="Size (GB)"),
    ColumnDef("used_gb", header="Used (GB)", wide_only=True),
    ColumnDef("fs_type", header="FS Type", wide_only=True),
    ColumnDef("preferred_tier", header="Tier", wide_only=True),
    ColumnDef("description", wide_only=True),
]


def _volume_to_dict(vol: Any) -> dict[str, Any]:
    """Convert a NAS volume SDK object to a dict for output."""
    # max_size_gb is a property on the SDK object
    if hasattr(vol, "max_size_gb"):
        size_gb = vol.max_size_gb
    else:
        max_size = vol.get("maxsize", 0) or 0
        size_gb = round(max_size / 1073741824, 2) if max_size else 0

    # used_gb is a property on the SDK object
    if hasattr(vol, "used_gb"):
        used_gb = vol.used_gb
    else:
        used_gb = None

    return {
        "$key": vol.key,
        "name": vol.name,
        "enabled": vol.get("enabled"),
        "size_gb": size_gb,
        "used_gb": used_gb,
        "fs_type": vol.get("fs_type"),
        "preferred_tier": vol.get("preferred_tier"),
        "description": vol.get("description", ""),
    }


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    service: Annotated[
        str | None,
        typer.Option("--service", help="Filter by NAS service name or key"),
    ] = None,
    fs_type: Annotated[
        str | None,
        typer.Option("--fs-type", help="Filter by filesystem type (ext4, cifs, nfs, ybfs)"),
    ] = None,
) -> None:
    """List all NAS volumes."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if service is not None:
        # Resolve service name to key if it's not numeric
        if service.isdigit():
            kwargs["service"] = int(service)
        else:
            svc_key = resolve_resource_id(vctx.client.nas_services, service, "NAS service")
            kwargs["service"] = svc_key
    if fs_type is not None:
        kwargs["fs_type"] = fs_type

    volumes = vctx.client.nas_volumes.list(**kwargs)
    data = [_volume_to_dict(v) for v in volumes]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NAS_VOLUME_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
) -> None:
    """Get details of a NAS volume."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")
    item = vctx.client.nas_volumes.get(key)
    output_result(
        _volume_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Volume name")],
    service: Annotated[str, typer.Option("--service", help="NAS service name or key")],
    size_gb: Annotated[int, typer.Option("--size-gb", help="Volume size in GB")],
    tier: Annotated[int | None, typer.Option("--tier", help="Preferred storage tier (1-5)")] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Volume description")
    ] = None,
    read_only: Annotated[bool, typer.Option("--read-only", help="Create as read-only")] = False,
    owner_user: Annotated[
        str | None, typer.Option("--owner-user", help="Volume directory owner user")
    ] = None,
    owner_group: Annotated[
        str | None, typer.Option("--owner-group", help="Volume directory owner group")
    ] = None,
    snapshot_profile: Annotated[
        str | None, typer.Option("--snapshot-profile", help="Snapshot profile name or key")
    ] = None,
) -> None:
    """Create a new NAS volume."""
    vctx = get_context(ctx)

    # Resolve service - SDK accepts int or str for service
    svc_arg: int | str
    if service.isdigit():
        svc_arg = int(service)
    else:
        svc_arg = service

    create_kwargs: dict[str, Any] = {
        "name": name,
        "service": svc_arg,
        "size_gb": size_gb,
    }
    if tier is not None:
        create_kwargs["tier"] = tier
    if description is not None:
        create_kwargs["description"] = description
    if read_only:
        create_kwargs["read_only"] = True
    if owner_user is not None:
        create_kwargs["owner_user"] = owner_user
    if owner_group is not None:
        create_kwargs["owner_group"] = owner_group
    if snapshot_profile is not None:
        # Resolve snapshot profile - it takes int key
        if snapshot_profile.isdigit():
            create_kwargs["snapshot_profile"] = int(snapshot_profile)
        else:
            sp_key = resolve_resource_id(
                vctx.client.snapshot_profiles, snapshot_profile, "Snapshot profile"
            )
            create_kwargs["snapshot_profile"] = sp_key

    result = vctx.client.nas_volumes.create(**create_kwargs)
    vol_name = result.name if result else name
    vol_key = result.key if result else "?"
    output_success(
        f"Created NAS volume '{vol_name}' (key: {vol_key})",
        quiet=vctx.quiet,
    )


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Volume description")
    ] = None,
    size_gb: Annotated[int | None, typer.Option("--size-gb", help="Volume size in GB")] = None,
    tier: Annotated[int | None, typer.Option("--tier", help="Preferred storage tier (1-5)")] = None,
    read_only: Annotated[
        bool | None,
        typer.Option("--read-only/--no-read-only", help="Set read-only mode"),
    ] = None,
    owner_user: Annotated[
        str | None, typer.Option("--owner-user", help="Volume directory owner user")
    ] = None,
    owner_group: Annotated[
        str | None, typer.Option("--owner-group", help="Volume directory owner group")
    ] = None,
    snapshot_profile: Annotated[
        str | None, typer.Option("--snapshot-profile", help="Snapshot profile name or key")
    ] = None,
    automount_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--automount-snapshots/--no-automount-snapshots",
            help="Auto-mount snapshots",
        ),
    ] = None,
) -> None:
    """Update NAS volume settings."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")

    kwargs: dict[str, Any] = {}
    if description is not None:
        kwargs["description"] = description
    if size_gb is not None:
        kwargs["size_gb"] = size_gb
    if tier is not None:
        kwargs["tier"] = tier
    if read_only is not None:
        kwargs["read_only"] = read_only
    if owner_user is not None:
        kwargs["owner_user"] = owner_user
    if owner_group is not None:
        kwargs["owner_group"] = owner_group
    if snapshot_profile is not None:
        if snapshot_profile.isdigit():
            kwargs["snapshot_profile"] = int(snapshot_profile)
        else:
            sp_key = resolve_resource_id(
                vctx.client.snapshot_profiles, snapshot_profile, "Snapshot profile"
            )
            kwargs["snapshot_profile"] = sp_key
    if automount_snapshots is not None:
        kwargs["automount_snapshots"] = automount_snapshots

    vctx.client.nas_volumes.update(key, **kwargs)
    output_success(f"Updated NAS volume '{volume}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a NAS volume."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")

    if not confirm_action(f"Delete NAS volume '{volume}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.nas_volumes.delete(key)
    output_success(f"Deleted NAS volume '{volume}'", quiet=vctx.quiet)


@app.command("enable")
@handle_errors()
def enable_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
) -> None:
    """Enable a NAS volume."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")
    vctx.client.nas_volumes.enable(key)
    output_success(f"Enabled NAS volume '{volume}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
) -> None:
    """Disable a NAS volume."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")
    vctx.client.nas_volumes.disable(key)
    output_success(f"Disabled NAS volume '{volume}'", quiet=vctx.quiet)


@app.command("reset")
@handle_errors()
def reset_cmd(
    ctx: typer.Context,
    volume: Annotated[str, typer.Argument(help="NAS volume name or hex key")],
) -> None:
    """Reset a NAS volume to recover from error state."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")
    vctx.client.nas_volumes.reset(key)
    output_success(f"Reset NAS volume '{volume}'", quiet=vctx.quiet)
