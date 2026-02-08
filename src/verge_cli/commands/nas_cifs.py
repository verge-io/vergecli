"""NAS CIFS (SMB) share management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource

app = typer.Typer(
    name="cifs",
    help="Manage NAS CIFS (SMB) shares.",
    no_args_is_help=True,
)

NAS_CIFS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("volume_name", header="Volume"),
    ColumnDef(
        "enabled",
        format_fn=format_bool_yn,
        style_map={"Yes": "green", "No": "red"},
    ),
    ColumnDef("browseable", format_fn=format_bool_yn, wide_only=True),
    ColumnDef(
        "read_only",
        header="Read Only",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef(
        "guest_ok",
        header="Guest OK",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef(
        "shadow_copy_enabled",
        header="Shadow Copy",
        format_fn=format_bool_yn,
        wide_only=True,
    ),
    ColumnDef("description", wide_only=True),
]


def _cifs_share_to_dict(share: Any) -> dict[str, Any]:
    """Convert a NAS CIFS share SDK object to a dict for output."""
    return {
        "$key": share.key,
        "name": share.name,
        "volume_name": share.get("volume_name"),
        "enabled": share.get("enabled"),
        "browseable": share.get("browseable"),
        "read_only": share.get("read_only"),
        "guest_ok": share.get("guest_ok"),
        "shadow_copy_enabled": share.get("shadow_copy_enabled"),
        "share_path": share.get("share_path"),
        "description": share.get("description", ""),
    }


def _split_list(value: str | None) -> list[str] | None:
    """Split a comma-separated string into a list, or return None."""
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@app.command("list")
@handle_errors()
def list_cmd(
    ctx: typer.Context,
    volume: Annotated[
        str | None,
        typer.Option("--volume", help="Filter by volume name or hex key"),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Filter by enabled state"),
    ] = None,
) -> None:
    """List all CIFS shares."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if volume is not None:
        vol_key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")
        kwargs["volume"] = vol_key
    if enabled is not None:
        kwargs["enabled"] = enabled

    shares = vctx.client.cifs_shares.list(**kwargs)
    data = [_cifs_share_to_dict(s) for s in shares]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NAS_CIFS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    share: Annotated[str, typer.Argument(help="CIFS share name or hex key")],
) -> None:
    """Get details of a CIFS share."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.cifs_shares, share, "CIFS share")
    item = vctx.client.cifs_shares.get(key=key)
    output_result(
        _cifs_share_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Share name")],
    volume: Annotated[str, typer.Option("--volume", help="NAS volume name or hex key")],
    share_path: Annotated[
        str | None,
        typer.Option("--share-path", help="Path within volume"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Share description"),
    ] = None,
    comment: Annotated[
        str | None,
        typer.Option("--comment", help="Share comment visible to clients"),
    ] = None,
    browseable: Annotated[
        bool | None,
        typer.Option("--browseable/--no-browseable", help="Make share browseable"),
    ] = None,
    read_only: Annotated[
        bool,
        typer.Option("--read-only", help="Create as read-only"),
    ] = False,
    guest_ok: Annotated[
        bool,
        typer.Option("--guest-ok", help="Allow guest access"),
    ] = False,
    guest_only: Annotated[
        bool,
        typer.Option("--guest-only", help="Only allow guest access"),
    ] = False,
    force_user: Annotated[
        str | None,
        typer.Option("--force-user", help="Force file operations as user"),
    ] = None,
    force_group: Annotated[
        str | None,
        typer.Option("--force-group", help="Force file operations as group"),
    ] = None,
    valid_users: Annotated[
        str | None,
        typer.Option("--valid-users", help="Comma-separated user list"),
    ] = None,
    valid_groups: Annotated[
        str | None,
        typer.Option("--valid-groups", help="Comma-separated group list"),
    ] = None,
    admin_users: Annotated[
        str | None,
        typer.Option("--admin-users", help="Comma-separated admin user list"),
    ] = None,
    admin_groups: Annotated[
        str | None,
        typer.Option("--admin-groups", help="Comma-separated admin group list"),
    ] = None,
    allowed_hosts: Annotated[
        str | None,
        typer.Option("--allowed-hosts", help="Comma-separated host/CIDR list"),
    ] = None,
    denied_hosts: Annotated[
        str | None,
        typer.Option("--denied-hosts", help="Comma-separated denied host list"),
    ] = None,
    shadow_copy: Annotated[
        bool,
        typer.Option("--shadow-copy", help="Enable shadow copy"),
    ] = False,
) -> None:
    """Create a new CIFS share."""
    vctx = get_context(ctx)

    # Resolve volume name to key
    vol_key = resolve_nas_resource(vctx.client.nas_volumes, volume, "NAS volume")

    create_kwargs: dict[str, Any] = {
        "name": name,
        "volume": vol_key,
    }
    if share_path is not None:
        create_kwargs["share_path"] = share_path
    if description is not None:
        create_kwargs["description"] = description
    if comment is not None:
        create_kwargs["comment"] = comment
    if browseable is not None:
        create_kwargs["browseable"] = browseable
    if read_only:
        create_kwargs["read_only"] = True
    if guest_ok:
        create_kwargs["guest_ok"] = True
    if guest_only:
        create_kwargs["guest_only"] = True
    if force_user is not None:
        create_kwargs["force_user"] = force_user
    if force_group is not None:
        create_kwargs["force_group"] = force_group

    # Split comma-separated list fields
    if valid_users is not None:
        create_kwargs["valid_users"] = _split_list(valid_users)
    if valid_groups is not None:
        create_kwargs["valid_groups"] = _split_list(valid_groups)
    if admin_users is not None:
        create_kwargs["admin_users"] = _split_list(admin_users)
    if admin_groups is not None:
        create_kwargs["admin_groups"] = _split_list(admin_groups)
    if allowed_hosts is not None:
        create_kwargs["allowed_hosts"] = _split_list(allowed_hosts)
    if denied_hosts is not None:
        create_kwargs["denied_hosts"] = _split_list(denied_hosts)
    if shadow_copy:
        create_kwargs["shadow_copy"] = True

    result = vctx.client.cifs_shares.create(**create_kwargs)
    share_name = result.name if result else name
    share_key = result.key if result else "?"
    output_success(
        f"Created CIFS share '{share_name}' (key: {share_key})",
        quiet=vctx.quiet,
    )


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    share: Annotated[str, typer.Argument(help="CIFS share name or hex key")],
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Share description"),
    ] = None,
    comment: Annotated[
        str | None,
        typer.Option("--comment", help="Share comment visible to clients"),
    ] = None,
    browseable: Annotated[
        bool | None,
        typer.Option("--browseable/--no-browseable", help="Set browseable"),
    ] = None,
    read_only: Annotated[
        bool | None,
        typer.Option("--read-only/--no-read-only", help="Set read-only mode"),
    ] = None,
    guest_ok: Annotated[
        bool | None,
        typer.Option("--guest-ok/--no-guest-ok", help="Set guest access"),
    ] = None,
    guest_only: Annotated[
        bool | None,
        typer.Option("--guest-only/--no-guest-only", help="Set guest-only mode"),
    ] = None,
    force_user: Annotated[
        str | None,
        typer.Option("--force-user", help="Force file operations as user"),
    ] = None,
    force_group: Annotated[
        str | None,
        typer.Option("--force-group", help="Force file operations as group"),
    ] = None,
    valid_users: Annotated[
        str | None,
        typer.Option("--valid-users", help="Comma-separated user list"),
    ] = None,
    valid_groups: Annotated[
        str | None,
        typer.Option("--valid-groups", help="Comma-separated group list"),
    ] = None,
    admin_users: Annotated[
        str | None,
        typer.Option("--admin-users", help="Comma-separated admin user list"),
    ] = None,
    admin_groups: Annotated[
        str | None,
        typer.Option("--admin-groups", help="Comma-separated admin group list"),
    ] = None,
    allowed_hosts: Annotated[
        str | None,
        typer.Option("--allowed-hosts", help="Comma-separated host/CIDR list"),
    ] = None,
    denied_hosts: Annotated[
        str | None,
        typer.Option("--denied-hosts", help="Comma-separated denied host list"),
    ] = None,
    shadow_copy: Annotated[
        bool | None,
        typer.Option("--shadow-copy/--no-shadow-copy", help="Enable/disable shadow copy"),
    ] = None,
) -> None:
    """Update a CIFS share."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.cifs_shares, share, "CIFS share")

    kwargs: dict[str, Any] = {}
    if description is not None:
        kwargs["description"] = description
    if comment is not None:
        kwargs["comment"] = comment
    if browseable is not None:
        kwargs["browseable"] = browseable
    if read_only is not None:
        kwargs["read_only"] = read_only
    if guest_ok is not None:
        kwargs["guest_ok"] = guest_ok
    if guest_only is not None:
        kwargs["guest_only"] = guest_only
    if force_user is not None:
        kwargs["force_user"] = force_user
    if force_group is not None:
        kwargs["force_group"] = force_group
    if valid_users is not None:
        kwargs["valid_users"] = _split_list(valid_users)
    if valid_groups is not None:
        kwargs["valid_groups"] = _split_list(valid_groups)
    if admin_users is not None:
        kwargs["admin_users"] = _split_list(admin_users)
    if admin_groups is not None:
        kwargs["admin_groups"] = _split_list(admin_groups)
    if allowed_hosts is not None:
        kwargs["allowed_hosts"] = _split_list(allowed_hosts)
    if denied_hosts is not None:
        kwargs["denied_hosts"] = _split_list(denied_hosts)
    if shadow_copy is not None:
        kwargs["shadow_copy"] = shadow_copy

    vctx.client.cifs_shares.update(key, **kwargs)
    output_success(f"Updated CIFS share '{share}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    share: Annotated[str, typer.Argument(help="CIFS share name or hex key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a CIFS share (data is retained on volume)."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.cifs_shares, share, "CIFS share")

    if not confirm_action(f"Delete CIFS share '{share}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.cifs_shares.delete(key)
    output_success(f"Deleted CIFS share '{share}'", quiet=vctx.quiet)


@app.command("enable")
@handle_errors()
def enable_cmd(
    ctx: typer.Context,
    share: Annotated[str, typer.Argument(help="CIFS share name or hex key")],
) -> None:
    """Enable a CIFS share."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.cifs_shares, share, "CIFS share")
    vctx.client.cifs_shares.enable(key)
    output_success(f"Enabled CIFS share '{share}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    share: Annotated[str, typer.Argument(help="CIFS share name or hex key")],
) -> None:
    """Disable a CIFS share."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.cifs_shares, share, "CIFS share")
    vctx.client.cifs_shares.disable(key)
    output_success(f"Disabled CIFS share '{share}'", quiet=vctx.quiet)
