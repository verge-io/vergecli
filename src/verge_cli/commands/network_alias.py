"""Network IP alias commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import ALIAS_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import ResourceNotFoundError, handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="alias",
    help="Manage network IP aliases.",
    no_args_is_help=True,
)


def _resolve_alias_id(network: Any, identifier: str) -> int:
    """Resolve an alias name, IP, or ID to a key.

    Args:
        network: Network object with aliases collection.
        identifier: Alias hostname, IP address, or numeric key.

    Returns:
        The alias key.

    Raises:
        ResourceNotFoundError: If alias not found.
    """
    aliases = network.aliases.list()
    for alias in aliases:
        hostname = alias.get("hostname") or getattr(alias, "hostname", "")
        ip = alias.get("ip") or getattr(alias, "ip", "")
        key = alias.get("$key") or getattr(alias, "key", None)
        if (hostname == identifier or ip == identifier) and key is not None:
            return int(key)

    # If numeric, treat as key
    if identifier.isdigit():
        return int(identifier)

    raise ResourceNotFoundError(f"Alias '{identifier}' not found")


def _alias_to_dict(alias: Any) -> dict[str, Any]:
    """Convert a NetworkAlias object to a dictionary for output.

    Args:
        alias: Alias object from SDK.

    Returns:
        Dictionary representation of the alias.
    """
    return {
        "key": alias.key,
        "ip": alias.get("ip", ""),
        "hostname": alias.get("hostname", ""),
        "description": alias.get("description", ""),
        "mac": alias.get("mac", ""),
    }


@app.command("list")
@handle_errors()
def alias_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
) -> None:
    """List IP aliases for a network."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    aliases = net_obj.aliases.list()
    data = [_alias_to_dict(alias) for alias in aliases]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=ALIAS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def alias_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
) -> None:
    """Get details of an IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    alias_obj = net_obj.aliases.get(alias_key)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def alias_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    ip: Annotated[str, typer.Option("--ip", "-i", help="IP address or CIDR")],
    name: Annotated[
        str, typer.Option("--name", "-n", help="Alias name (used as alias:name in rules)")
    ],
    description: Annotated[str, typer.Option("--description", "-d", help="Description")] = "",
) -> None:
    """Create a new IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_obj = net_obj.aliases.create(ip=ip, name=name, description=description)

    output_success(f"Created alias '{alias_obj.hostname}' ({alias_obj.ip})", quiet=vctx.quiet)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def alias_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
    ip: Annotated[str | None, typer.Option("--ip", "-i", help="New IP address")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="New alias name")] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="New description")
    ] = None,
) -> None:
    """Update an IP alias (delete + create).

    Since the SDK doesn't expose PUT for aliases, this command
    deletes the existing alias and recreates it with the new values.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    existing = net_obj.aliases.get(alias_key)

    # Check if any updates were specified
    if ip is None and name is None and description is None:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    # Merge updates with existing values
    new_ip = ip if ip is not None else existing.ip
    new_name = name if name is not None else (existing.hostname or "")
    new_desc = description if description is not None else (existing.get("description") or "")

    # Delete and recreate (SDK doesn't expose PUT for aliases)
    net_obj.aliases.delete(alias_key)
    alias_obj = net_obj.aliases.create(ip=new_ip, name=new_name, description=new_desc)

    output_success(f"Updated alias '{alias_obj.hostname}'", quiet=vctx.quiet)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def alias_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete an IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    alias_obj = net_obj.aliases.get(alias_key)

    alias_name = alias_obj.hostname or alias_obj.ip

    if not confirm_action(f"Delete alias '{alias_name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    net_obj.aliases.delete(alias_key)
    output_success(f"Deleted alias '{alias_name}'", quiet=vctx.quiet)
