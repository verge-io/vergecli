"""NAS local user management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ColumnDef, format_bool_yn
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_nas_resource, resolve_resource_id

app = typer.Typer(
    name="user",
    help="Manage NAS local users.",
    no_args_is_help=True,
)

NAS_USER_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("displayname", header="Display Name"),
    ColumnDef(
        "enabled",
        format_fn=format_bool_yn,
        style_map={"Yes": "green", "No": "red"},
    ),
    ColumnDef("service_name", header="Service"),
    ColumnDef(
        "status",
        style_map={"online": "green", "offline": "red", "error": "yellow"},
    ),
    ColumnDef("home_share_name", header="Home Share", wide_only=True),
    ColumnDef("home_drive", header="Drive", wide_only=True),
    ColumnDef("description", wide_only=True),
]


def _user_to_dict(user: Any) -> dict[str, Any]:
    """Convert a NAS user SDK object to a dict for output."""
    return {
        "$key": user.key,
        "name": user.name,
        "displayname": user.get("displayname", ""),
        "enabled": user.get("enabled"),
        "service_name": user.get("service_name"),
        "status": user.get("status"),
        "home_share_name": user.get("home_share_name"),
        "home_drive": user.get("home_drive"),
        "description": user.get("description", ""),
    }


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
    """List all NAS local users."""
    vctx = get_context(ctx)
    kwargs: dict[str, Any] = {}
    if service is not None:
        svc_key = resolve_resource_id(vctx.client.nas_services, service, "NAS service")
        kwargs["service"] = svc_key
    if enabled is not None:
        kwargs["enabled"] = enabled

    users = vctx.client.nas_users.list(**kwargs)
    data = [_user_to_dict(u) for u in users]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NAS_USER_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def get_cmd(
    ctx: typer.Context,
    user: Annotated[str, typer.Argument(help="NAS user name or hex key")],
) -> None:
    """Get details of a NAS local user."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_users, user, "NAS user")
    item = vctx.client.nas_users.get(key=key)
    output_result(
        _user_to_dict(item),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def create_cmd(
    ctx: typer.Context,
    service: Annotated[
        str,
        typer.Option("--service", help="NAS service name or key"),
    ],
    name: Annotated[str, typer.Option("--name", "-n", help="Username")],
    password: Annotated[str, typer.Option("--password", help="User password")],
    displayname: Annotated[
        str | None,
        typer.Option("--displayname", help="Display name"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="User description"),
    ] = None,
    home_share: Annotated[
        str | None,
        typer.Option("--home-share", help="Home share name or key"),
    ] = None,
    home_drive: Annotated[
        str | None,
        typer.Option("--home-drive", help="Home drive letter (e.g., H)"),
    ] = None,
) -> None:
    """Create a new NAS local user."""
    vctx = get_context(ctx)

    # Resolve service name to key
    svc_key = resolve_resource_id(vctx.client.nas_services, service, "NAS service")

    create_kwargs: dict[str, Any] = {
        "service": svc_key,
        "name": name,
        "password": password,
    }
    if displayname is not None:
        create_kwargs["displayname"] = displayname
    if description is not None:
        create_kwargs["description"] = description
    if home_share is not None:
        create_kwargs["home_share"] = home_share
    if home_drive is not None:
        create_kwargs["home_drive"] = home_drive

    result = vctx.client.nas_users.create(**create_kwargs)
    user_name = result.name if result else name
    user_key = result.key if result else "?"
    output_success(
        f"Created NAS user '{user_name}' (key: {user_key})",
        quiet=vctx.quiet,
    )


@app.command("update")
@handle_errors()
def update_cmd(
    ctx: typer.Context,
    user: Annotated[str, typer.Argument(help="NAS user name or hex key")],
    password: Annotated[
        str | None,
        typer.Option("--password", help="New password"),
    ] = None,
    displayname: Annotated[
        str | None,
        typer.Option("--displayname", help="Display name"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="User description"),
    ] = None,
    home_share: Annotated[
        str | None,
        typer.Option("--home-share", help="Home share name or key"),
    ] = None,
    home_drive: Annotated[
        str | None,
        typer.Option("--home-drive", help="Home drive letter (e.g., H)"),
    ] = None,
) -> None:
    """Update a NAS local user."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_users, user, "NAS user")

    kwargs: dict[str, Any] = {}
    if password is not None:
        kwargs["password"] = password
    if displayname is not None:
        kwargs["displayname"] = displayname
    if description is not None:
        kwargs["description"] = description
    if home_share is not None:
        kwargs["home_share"] = home_share
    if home_drive is not None:
        kwargs["home_drive"] = home_drive

    vctx.client.nas_users.update(key, **kwargs)
    output_success(f"Updated NAS user '{user}'", quiet=vctx.quiet)


@app.command("delete")
@handle_errors()
def delete_cmd(
    ctx: typer.Context,
    user: Annotated[str, typer.Argument(help="NAS user name or hex key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a NAS local user."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_users, user, "NAS user")

    if not confirm_action(f"Delete NAS user '{user}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.nas_users.delete(key)
    output_success(f"Deleted NAS user '{user}'", quiet=vctx.quiet)


@app.command("enable")
@handle_errors()
def enable_cmd(
    ctx: typer.Context,
    user: Annotated[str, typer.Argument(help="NAS user name or hex key")],
) -> None:
    """Enable a NAS local user."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_users, user, "NAS user")
    vctx.client.nas_users.enable(key)
    output_success(f"Enabled NAS user '{user}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def disable_cmd(
    ctx: typer.Context,
    user: Annotated[str, typer.Argument(help="NAS user name or hex key")],
) -> None:
    """Disable a NAS local user."""
    vctx = get_context(ctx)
    key = resolve_nas_resource(vctx.client.nas_users, user, "NAS user")
    vctx.client.nas_users.disable(key)
    output_success(f"Disabled NAS user '{user}'", quiet=vctx.quiet)
