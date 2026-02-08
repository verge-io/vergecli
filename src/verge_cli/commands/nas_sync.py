"""NAS volume sync management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource, resolve_resource_id

app = typer.Typer(
    name="sync",
    help="Manage NAS volume sync jobs.",
    no_args_is_help=True,
)

NAS_SYNC_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef(
        "enabled",
        format_fn=format_bool_yn,
        style_map={"Yes": "green", "No": "red"},
    ),
    ColumnDef("status", style_map={"idle": "dim", "syncing": "green", "error": "red"}),
    ColumnDef("sync_method", header="Method"),
    ColumnDef("workers"),
    ColumnDef("source_volume_key", header="Source Vol", wide_only=True),
    ColumnDef("destination_volume_key", header="Dest Vol", wide_only=True),
    ColumnDef("dest_delete", header="Dest Delete", wide_only=True),
    ColumnDef("description", wide_only=True),
]


def _sync_to_dict(sync: Any) -> dict[str, Any]:
    """Convert a NAS volume sync SDK object to a dict for output."""
    return {
        "$key": sync.key,
        "name": sync.name,
        "enabled": sync.get("enabled"),
        "status": sync.get("status"),
        "sync_method": sync.get("sync_method"),
        "workers": sync.get("workers"),
        "source_volume_key": sync.get("source_volume"),
        "destination_volume_key": sync.get("destination_volume"),
        "dest_delete": sync.get("destination_delete"),
        "description": sync.get("description", ""),
    }


def _split_patterns(patterns: str | None) -> list[str] | None:
    """Split comma-separated patterns into a list.

    Returns None if input is None or empty.
    """
    if not patterns:
        return None
    return [p.strip() for p in patterns.split(",") if p.strip()]


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    service: Annotated[
        str | None,
        typer.Option("--service", help="Filter by NAS service name or key"),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Filter by enabled state"),
    ] = None,
) -> None:
    """List all NAS volume sync jobs."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if service is not None:
        svc_key = resolve_resource_id(vctx.client.nas_services, service, "NAS service")
        kwargs["service"] = svc_key
    if enabled is not None:
        kwargs["enabled"] = enabled

    syncs = vctx.client.volume_syncs.list(**kwargs)
    data = [_sync_to_dict(s) for s in syncs]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NAS_SYNC_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
) -> None:
    """Get details of a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")
    item = vctx.client.volume_syncs.get(key=key)
    output_result(
        _sync_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Sync job name")],
    service: Annotated[
        str,
        typer.Option("--service", help="NAS service name or key"),
    ],
    source_volume: Annotated[
        str,
        typer.Option("--source-volume", help="Source volume name or key"),
    ],
    dest_volume: Annotated[
        str,
        typer.Option("--dest-volume", help="Destination volume name or key"),
    ],
    source_path: Annotated[
        str | None,
        typer.Option("--source-path", help="Subdirectory within source volume"),
    ] = None,
    dest_path: Annotated[
        str | None,
        typer.Option("--dest-path", help="Subdirectory within destination volume"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Sync job description"),
    ] = None,
    sync_method: Annotated[
        str,
        typer.Option("--sync-method", help="Sync method: ysync or rsync"),
    ] = "ysync",
    dest_delete: Annotated[
        str,
        typer.Option(
            "--dest-delete",
            help="Destination delete mode: never, delete, delete-before, delete-during, delete-delay, delete-after",
        ),
    ] = "never",
    workers: Annotated[
        int,
        typer.Option("--workers", help="Parallel workers (1-128)"),
    ] = 4,
    include: Annotated[
        str | None,
        typer.Option("--include", help="Comma-separated include patterns"),
    ] = None,
    exclude: Annotated[
        str | None,
        typer.Option("--exclude", help="Comma-separated exclude patterns"),
    ] = None,
    preserve_acls: Annotated[
        bool,
        typer.Option("--preserve-acls/--no-preserve-acls", help="Preserve ACLs"),
    ] = True,
    preserve_permissions: Annotated[
        bool,
        typer.Option(
            "--preserve-permissions/--no-preserve-permissions",
            help="Preserve file permissions",
        ),
    ] = True,
    preserve_owner: Annotated[
        bool,
        typer.Option("--preserve-owner/--no-preserve-owner", help="Preserve file owner"),
    ] = True,
    preserve_groups: Annotated[
        bool,
        typer.Option("--preserve-groups/--no-preserve-groups", help="Preserve file groups"),
    ] = True,
    preserve_mod_time: Annotated[
        bool,
        typer.Option(
            "--preserve-mod-time/--no-preserve-mod-time",
            help="Preserve modification time",
        ),
    ] = True,
    preserve_xattrs: Annotated[
        bool,
        typer.Option(
            "--preserve-xattrs/--no-preserve-xattrs",
            help="Preserve extended attributes",
        ),
    ] = True,
    copy_symlinks: Annotated[
        bool,
        typer.Option("--copy-symlinks/--no-copy-symlinks", help="Copy symbolic links"),
    ] = True,
    freeze_filesystem: Annotated[
        bool,
        typer.Option("--freeze-filesystem", help="Freeze filesystem before snapshot"),
    ] = False,
) -> None:
    """Create a new NAS volume sync job."""
    vctx = get_context(ctx)

    # Resolve service name to key
    svc_key = resolve_resource_id(vctx.client.nas_services, service, "NAS service")

    # Resolve volume names to keys
    src_vol_key = resolve_nas_resource(vctx.client.nas_volumes, source_volume, "NAS volume")
    dst_vol_key = resolve_nas_resource(vctx.client.nas_volumes, dest_volume, "NAS volume")

    create_kwargs: dict[str, Any] = {
        "name": name,
        "service": svc_key,
        "source_volume": src_vol_key,
        "destination_volume": dst_vol_key,
        "sync_method": sync_method,
        "destination_delete": dest_delete,
        "workers": workers,
        "preserve_acls": preserve_acls,
        "preserve_permissions": preserve_permissions,
        "preserve_owner": preserve_owner,
        "preserve_groups": preserve_groups,
        "preserve_mod_time": preserve_mod_time,
        "preserve_xattrs": preserve_xattrs,
        "copy_symlinks": copy_symlinks,
        "freeze_filesystem": freeze_filesystem,
    }
    if source_path is not None:
        create_kwargs["source_path"] = source_path
    if dest_path is not None:
        create_kwargs["destination_path"] = dest_path
    if description is not None:
        create_kwargs["description"] = description

    include_list = _split_patterns(include)
    if include_list is not None:
        create_kwargs["include"] = include_list

    exclude_list = _split_patterns(exclude)
    if exclude_list is not None:
        create_kwargs["exclude"] = exclude_list

    result = vctx.client.volume_syncs.create(**create_kwargs)
    sync_name = result.name if result else name
    sync_key = result.key if result else "?"
    output_success(
        f"Created volume sync '{sync_name}' (key: {sync_key})",
        quiet=vctx.quiet,
    )


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Sync job description"),
    ] = None,
    source_path: Annotated[
        str | None,
        typer.Option("--source-path", help="Subdirectory within source volume"),
    ] = None,
    dest_path: Annotated[
        str | None,
        typer.Option("--dest-path", help="Subdirectory within destination volume"),
    ] = None,
    sync_method: Annotated[
        str | None,
        typer.Option("--sync-method", help="Sync method: ysync or rsync"),
    ] = None,
    dest_delete: Annotated[
        str | None,
        typer.Option(
            "--dest-delete",
            help="Destination delete mode: never, delete, delete-before, delete-during, delete-delay, delete-after",
        ),
    ] = None,
    workers: Annotated[
        int | None,
        typer.Option("--workers", help="Parallel workers (1-128)"),
    ] = None,
    include: Annotated[
        str | None,
        typer.Option("--include", help="Comma-separated include patterns"),
    ] = None,
    exclude: Annotated[
        str | None,
        typer.Option("--exclude", help="Comma-separated exclude patterns"),
    ] = None,
    preserve_acls: Annotated[
        bool | None,
        typer.Option("--preserve-acls/--no-preserve-acls", help="Preserve ACLs"),
    ] = None,
    preserve_permissions: Annotated[
        bool | None,
        typer.Option(
            "--preserve-permissions/--no-preserve-permissions",
            help="Preserve file permissions",
        ),
    ] = None,
    preserve_owner: Annotated[
        bool | None,
        typer.Option("--preserve-owner/--no-preserve-owner", help="Preserve file owner"),
    ] = None,
    preserve_groups: Annotated[
        bool | None,
        typer.Option("--preserve-groups/--no-preserve-groups", help="Preserve file groups"),
    ] = None,
    preserve_mod_time: Annotated[
        bool | None,
        typer.Option(
            "--preserve-mod-time/--no-preserve-mod-time",
            help="Preserve modification time",
        ),
    ] = None,
    preserve_xattrs: Annotated[
        bool | None,
        typer.Option(
            "--preserve-xattrs/--no-preserve-xattrs",
            help="Preserve extended attributes",
        ),
    ] = None,
    copy_symlinks: Annotated[
        bool | None,
        typer.Option("--copy-symlinks/--no-copy-symlinks", help="Copy symbolic links"),
    ] = None,
    freeze_filesystem: Annotated[
        bool | None,
        typer.Option(
            "--freeze-filesystem/--no-freeze-filesystem",
            help="Freeze filesystem before snapshot",
        ),
    ] = None,
) -> None:
    """Update a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")

    kwargs: dict[str, Any] = {}
    if description is not None:
        kwargs["description"] = description
    if source_path is not None:
        kwargs["source_path"] = source_path
    if dest_path is not None:
        kwargs["destination_path"] = dest_path
    if sync_method is not None:
        kwargs["sync_method"] = sync_method
    if dest_delete is not None:
        kwargs["destination_delete"] = dest_delete
    if workers is not None:
        kwargs["workers"] = workers
    if preserve_acls is not None:
        kwargs["preserve_acls"] = preserve_acls
    if preserve_permissions is not None:
        kwargs["preserve_permissions"] = preserve_permissions
    if preserve_owner is not None:
        kwargs["preserve_owner"] = preserve_owner
    if preserve_groups is not None:
        kwargs["preserve_groups"] = preserve_groups
    if preserve_mod_time is not None:
        kwargs["preserve_mod_time"] = preserve_mod_time
    if preserve_xattrs is not None:
        kwargs["preserve_xattrs"] = preserve_xattrs
    if copy_symlinks is not None:
        kwargs["copy_symlinks"] = copy_symlinks
    if freeze_filesystem is not None:
        kwargs["freeze_filesystem"] = freeze_filesystem

    include_list = _split_patterns(include)
    if include_list is not None:
        kwargs["include"] = include_list

    exclude_list = _split_patterns(exclude)
    if exclude_list is not None:
        kwargs["exclude"] = exclude_list

    vctx.client.volume_syncs.update(key, **kwargs)
    output_success(f"Updated volume sync '{sync}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")

    if not confirm_action(f"Delete volume sync '{sync}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.volume_syncs.delete(key)
    output_success(f"Deleted volume sync '{sync}'", quiet=vctx.quiet)


@app.command("enable")
@handle_errors()
def enable_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
) -> None:
    """Enable a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")
    vctx.client.volume_syncs.enable(key)
    output_success(f"Enabled volume sync '{sync}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
) -> None:
    """Disable a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")
    vctx.client.volume_syncs.disable(key)
    output_success(f"Disabled volume sync '{sync}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def start_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
) -> None:
    """Start a NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")
    vctx.client.volume_syncs.start(key)
    output_success(f"Started volume sync '{sync}'", quiet=vctx.quiet)


@app.command("stop")
@handle_errors()
def stop_cmd(
    ctx: typer.Context,
    sync: Annotated[str, typer.Argument(help="Sync job name or hex key")],
) -> None:
    """Stop a running NAS volume sync job."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.volume_syncs, sync, "volume sync")
    vctx.client.volume_syncs.stop(key)
    output_success(f"Stopped volume sync '{sync}'", quiet=vctx.quiet)
