"""OIDC application user ACL commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import OIDC_USER_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import ResourceNotFoundError, handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="user",
    help="Manage OIDC application allowed users (ACL).",
    no_args_is_help=True,
)


def _resolve_oidc_app(client: Any, identifier: str) -> int:
    """Resolve OIDC application identifier (key or name) to key."""
    if identifier.isdigit():
        oidc_app = client.oidc_applications.get(key=int(identifier))
    else:
        oidc_app = client.oidc_applications.get(name=identifier)
    return int(oidc_app.key)


def _oidc_user_to_dict(entry: Any) -> dict[str, Any]:
    """Convert SDK OIDC user ACL entry to output dict."""
    return {
        "$key": int(entry.key),
        "user_key": entry.get("user"),
        "user_display": entry.get("user_display", ""),
    }


def _find_acl_entry(entries: list[Any], member_key: int, member_field: str) -> int:
    """Find ACL entry key by member key."""
    for entry in entries:
        if entry.get(member_field) == member_key:
            return int(entry.key)
    raise ResourceNotFoundError(f"No ACL entry found for {member_field} key {member_key}")


@app.command("list")
@handle_errors()
def oidc_user_list(
    ctx: typer.Context,
    oidc_app: Annotated[str, typer.Argument(help="OIDC application name or key.")],
) -> None:
    """List allowed users for an OIDC application."""
    vctx = get_context(ctx)
    app_key = _resolve_oidc_app(vctx.client, oidc_app)
    users_mgr = vctx.client.oidc_applications.allowed_users(app_key)
    entries = users_mgr.list()

    output_result(
        [_oidc_user_to_dict(e) for e in entries],
        output_format=vctx.output_format,
        query=vctx.query,
        columns=OIDC_USER_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("add")
@handle_errors()
def oidc_user_add(
    ctx: typer.Context,
    oidc_app: Annotated[str, typer.Argument(help="OIDC application name or key.")],
    user: Annotated[str, typer.Argument(help="User name or key to add.")],
) -> None:
    """Add a user to the OIDC application's allowed list."""
    vctx = get_context(ctx)
    app_key = _resolve_oidc_app(vctx.client, oidc_app)
    user_key = resolve_resource_id(vctx.client.users, user, "User")

    users_mgr = vctx.client.oidc_applications.allowed_users(app_key)
    users_mgr.add(user_key=user_key)

    output_success(f"Added user '{user}' to OIDC application", quiet=vctx.quiet)


@app.command("remove")
@handle_errors()
def oidc_user_remove(
    ctx: typer.Context,
    oidc_app: Annotated[str, typer.Argument(help="OIDC application name or key.")],
    user_or_key: Annotated[str, typer.Argument(help="User name/key or ACL entry key.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Remove a user from the OIDC application's allowed list."""
    vctx = get_context(ctx)
    app_key = _resolve_oidc_app(vctx.client, oidc_app)
    users_mgr = vctx.client.oidc_applications.allowed_users(app_key)

    # Resolve entry key: try as user first, then as direct entry key
    if user_or_key.isdigit():
        # Could be user key or ACL entry key — try user key first
        user_key = int(user_or_key)
        entries = users_mgr.list()
        matching = [e for e in entries if e.get("user") == user_key]
        if matching:
            entry_key = int(matching[0].key)
        else:
            # Treat as direct ACL entry key
            entry_key = user_key
    else:
        # Resolve user name
        user_key = resolve_resource_id(vctx.client.users, user_or_key, "User")
        entries = users_mgr.list()
        entry_key = _find_acl_entry(entries, user_key, "user")

    if not confirm_action(f"Remove user '{user_or_key}' from OIDC application?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    users_mgr.delete(entry_key)
    output_success(f"Removed user '{user_or_key}' from OIDC application", quiet=vctx.quiet)
