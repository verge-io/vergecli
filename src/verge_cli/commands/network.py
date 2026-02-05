"""Network commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="network",
    help="Manage virtual networks.",
    no_args_is_help=True,
)

# Default columns for network list output
NETWORK_LIST_COLUMNS = ["name", "type", "network", "ipaddress", "status", "running"]


@app.command("list")
@handle_errors()
def network_list(
    ctx: typer.Context,
    network_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by network type"),
    ] = None,
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="Filter by status"),
    ] = None,
    filter: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression"),
    ] = None,
) -> None:
    """List virtual networks."""
    vctx = get_context(ctx)

    # Build filter
    odata_filter = filter
    if network_type:
        type_filter = f"type eq '{network_type}'"
        odata_filter = f"({odata_filter}) and {type_filter}" if odata_filter else type_filter
    if status:
        status_filter = f"machine#status#status eq '{status}'"
        odata_filter = f"({odata_filter}) and {status_filter}" if odata_filter else status_filter

    networks = vctx.client.networks.list(filter=odata_filter)

    # Convert to dicts for output
    data = [_network_to_dict(net) for net in networks]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NETWORK_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def network_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
) -> None:
    """Get details of a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    output_result(
        _network_to_dict(net_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def network_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Network name")],
    cidr: Annotated[
        str | None,
        typer.Option("--cidr", "-c", help="Network CIDR (e.g., 10.0.0.0/24)"),
    ] = None,
    ip_address: Annotated[
        str | None,
        typer.Option("--ip", "-i", help="Network interface IP address"),
    ] = None,
    gateway: Annotated[
        str | None,
        typer.Option("--gateway", "-g", help="Default gateway"),
    ] = None,
    description: Annotated[
        str,
        typer.Option("--description", "-d", help="Network description"),
    ] = "",
    dhcp: Annotated[
        bool,
        typer.Option("--dhcp/--no-dhcp", help="Enable DHCP server"),
    ] = False,
    dhcp_start: Annotated[
        str | None,
        typer.Option("--dhcp-start", help="DHCP range start IP"),
    ] = None,
    dhcp_stop: Annotated[
        str | None,
        typer.Option("--dhcp-stop", help="DHCP range end IP"),
    ] = None,
) -> None:
    """Create a new virtual network."""
    vctx = get_context(ctx)

    create_kwargs: dict[str, Any] = {
        "name": name,
        "description": description,
    }

    if cidr:
        create_kwargs["network_address"] = cidr
    if ip_address:
        create_kwargs["ip_address"] = ip_address
    if gateway:
        create_kwargs["gateway"] = gateway
    if dhcp:
        create_kwargs["dhcp_enabled"] = True
        if dhcp_start:
            create_kwargs["dhcp_start"] = dhcp_start
        if dhcp_stop:
            create_kwargs["dhcp_stop"] = dhcp_stop

    net_obj = vctx.client.networks.create(**create_kwargs)

    output_success(f"Created network '{net_obj.name}' (key: {net_obj.key})", quiet=vctx.quiet)

    output_result(
        _network_to_dict(net_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def network_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New network name")] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Network description"),
    ] = None,
    gateway: Annotated[
        str | None,
        typer.Option("--gateway", "-g", help="Default gateway"),
    ] = None,
) -> None:
    """Update a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if gateway is not None:
        updates["gateway"] = gateway

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    net_obj = vctx.client.networks.update(key, **updates)

    output_success(f"Updated network '{net_obj.name}'", quiet=vctx.quiet)

    output_result(
        _network_to_dict(net_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def network_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    if not confirm_action(f"Delete network '{net_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.networks.delete(key)
    output_success(f"Deleted network '{net_obj.name}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def network_start(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
) -> None:
    """Start a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    if net_obj.get("running"):
        typer.echo(f"Network '{net_obj.name}' is already running.")
        return

    net_obj.power_on()
    output_success(f"Started network '{net_obj.name}'", quiet=vctx.quiet)


@app.command("stop")
@handle_errors()
def network_stop(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Force stop")] = False,
) -> None:
    """Stop a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    if not net_obj.get("running"):
        typer.echo(f"Network '{net_obj.name}' is not running.")
        return

    net_obj.power_off(force=force)
    action = "Force stopped" if force else "Stopped"
    output_success(f"{action} network '{net_obj.name}'", quiet=vctx.quiet)


def _network_to_dict(net: Any) -> dict[str, Any]:
    """Convert a Network object to a dictionary for output."""
    return {
        "key": net.key,
        "name": net.name,
        "description": net.get("description", ""),
        "type": net.get("type"),
        "network": net.get("network"),
        "ipaddress": net.get("ipaddress"),
        "gateway": net.get("gateway"),
        "mtu": net.get("mtu"),
        "status": net.get("status"),
        "running": net.get("running"),
        "dhcp_enabled": net.get("dhcp_enabled"),
        "dhcp_start": net.get("dhcp_start"),
        "dhcp_stop": net.get("dhcp_stop"),
        "dns": net.get("dns"),
        "domain": net.get("domain"),
    }
