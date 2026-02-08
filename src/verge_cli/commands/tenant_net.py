"""Tenant networking sub-resource commands (net-block, ext-ip, l2)."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import (
    TENANT_EXT_IP_COLUMNS,
    TENANT_L2_COLUMNS,
    TENANT_NET_BLOCK_COLUMNS,
)
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

# ---------------------------------------------------------------------------
# Three Typer apps for three networking sub-resources
# ---------------------------------------------------------------------------

net_block_app = typer.Typer(
    name="net-block",
    help="Manage tenant network blocks.",
    no_args_is_help=True,
)

ext_ip_app = typer.Typer(
    name="ext-ip",
    help="Manage tenant external IPs.",
    no_args_is_help=True,
)

l2_app = typer.Typer(
    name="l2",
    help="Manage tenant L2 networks.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


# ---------------------------------------------------------------------------
# Sub-resource resolvers
# ---------------------------------------------------------------------------


def _resolve_net_block(tenant_obj: Any, identifier: str) -> int:
    """Resolve a network block name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    blocks = tenant_obj.network_blocks.list()
    matches = [b for b in blocks if b.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple network blocks match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Network block '{identifier}' not found.", err=True)
    raise typer.Exit(6)


def _resolve_ext_ip(tenant_obj: Any, identifier: str) -> int:
    """Resolve an external IP name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    ips = tenant_obj.external_ips.list()
    matches = [i for i in ips if i.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple external IPs match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: External IP '{identifier}' not found.", err=True)
    raise typer.Exit(6)


def _resolve_l2(tenant_obj: Any, identifier: str) -> int:
    """Resolve an L2 network name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    l2s = tenant_obj.l2_networks.list()
    matches = [net for net in l2s if net.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple L2 networks match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: L2 network '{identifier}' not found.", err=True)
    raise typer.Exit(6)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------


def _net_block_to_dict(block: Any) -> dict[str, Any]:
    """Convert a Network Block object to a dict for output."""
    return {
        "$key": block.key,
        "cidr": block.get("cidr", ""),
        "network_name": block.get("network_name", ""),
        "description": block.get("description", ""),
    }


def _ext_ip_to_dict(ip: Any) -> dict[str, Any]:
    """Convert an External IP object to a dict for output."""
    return {
        "$key": ip.key,
        "ip_address": ip.get("ip_address", ""),
        "network_name": ip.get("network_name", ""),
        "hostname": ip.get("hostname", ""),
    }


def _l2_to_dict(l2: Any) -> dict[str, Any]:
    """Convert an L2 Network object to a dict for output."""
    return {
        "$key": l2.key,
        "network_name": l2.get("network_name", ""),
        "network_type": l2.get("network_type", ""),
        "is_enabled": l2.get("enabled"),
    }


# ===== Network Block Commands =====


@net_block_app.command("list")
@handle_errors()
def net_block_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List network blocks allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    blocks = tenant_obj.network_blocks.list()
    data = [_net_block_to_dict(b) for b in blocks]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_NET_BLOCK_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@net_block_app.command("create")
@handle_errors()
def net_block_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    cidr: Annotated[str, typer.Option("--cidr", help="CIDR block (e.g., 10.0.0.0/24)")],
    network: Annotated[int, typer.Option("--network", help="Network key")],
) -> None:
    """Allocate a network block to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    block_obj = tenant_obj.network_blocks.create(
        cidr=cidr,
        network=network,
    )

    output_success(
        f"Created network block (key: {block_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _net_block_to_dict(block_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@net_block_app.command("delete")
@handle_errors()
def net_block_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    block: Annotated[str, typer.Argument(help="Network block name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a network block from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    block_key = _resolve_net_block(tenant_obj, block)

    if not confirm_action(f"Delete network block '{block}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.network_blocks.delete(block_key)
    output_success(f"Deleted network block '{block}'", quiet=vctx.quiet)


# ===== External IP Commands =====


@ext_ip_app.command("list")
@handle_errors()
def ext_ip_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List external IPs allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    ips = tenant_obj.external_ips.list()
    data = [_ext_ip_to_dict(i) for i in ips]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_EXT_IP_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@ext_ip_app.command("create")
@handle_errors()
def ext_ip_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    ip: Annotated[str, typer.Option("--ip", help="IP address")],
    network: Annotated[int, typer.Option("--network", help="Network key")],
    hostname: Annotated[str | None, typer.Option("--hostname", help="Hostname for the IP")] = None,
) -> None:
    """Allocate an external IP to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    ip_obj = tenant_obj.external_ips.create(
        ip=ip,
        network=network,
        hostname=hostname,
    )

    output_success(
        f"Created external IP (key: {ip_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _ext_ip_to_dict(ip_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@ext_ip_app.command("delete")
@handle_errors()
def ext_ip_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    ip: Annotated[str, typer.Argument(help="External IP name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove an external IP from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    ip_key = _resolve_ext_ip(tenant_obj, ip)

    if not confirm_action(f"Delete external IP '{ip}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.external_ips.delete(ip_key)
    output_success(f"Deleted external IP '{ip}'", quiet=vctx.quiet)


# ===== L2 Network Commands =====


@l2_app.command("list")
@handle_errors()
def l2_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List L2 networks allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    l2s = tenant_obj.l2_networks.list()
    data = [_l2_to_dict(net) for net in l2s]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_L2_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@l2_app.command("create")
@handle_errors()
def l2_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    network_name: Annotated[
        str, typer.Option("--network-name", help="Network name for the L2 connection")
    ],
) -> None:
    """Allocate an L2 network to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    l2_obj = tenant_obj.l2_networks.create(
        network_name=network_name,
    )

    output_success(
        f"Created L2 network (key: {l2_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _l2_to_dict(l2_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@l2_app.command("delete")
@handle_errors()
def l2_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    l2: Annotated[str, typer.Argument(help="L2 network name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove an L2 network from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    l2_key = _resolve_l2(tenant_obj, l2)

    if not confirm_action(f"Delete L2 network '{l2}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.l2_networks.delete(l2_key)
    output_success(f"Deleted L2 network '{l2}'", quiet=vctx.quiet)
