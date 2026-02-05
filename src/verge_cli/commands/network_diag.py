"""Network diagnostics commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="diag",
    help="Network diagnostics and statistics.",
    no_args_is_help=True,
)

# Default columns for lease list output
LEASE_LIST_COLUMNS = [
    "mac",
    "ip",
    "hostname",
    "expires",
    "state",
]

# Default columns for address list output
ADDRESS_LIST_COLUMNS = [
    "ip",
    "mac",
    "interface",
    "type",
]


def _item_to_dict(item: Any) -> dict[str, Any]:
    """Convert a diagnostics item to a dictionary for output.

    Handles both dict and object-like responses from the SDK.

    Args:
        item: Item from SDK (dict or object).

    Returns:
        Dictionary representation.
    """
    if isinstance(item, dict):
        return dict(item)

    # Handle object-like response with .get() method
    if hasattr(item, "get"):
        result: dict[str, Any] = dict(item)
        return result

    # Handle object with __dict__
    if hasattr(item, "__dict__"):
        result = dict(vars(item))
        return result

    return {"value": str(item)}


def _stats_to_dict(stats: Any) -> dict[str, Any]:
    """Convert network statistics to a dictionary for output.

    Handles both dict and object-like responses from the SDK.

    Args:
        stats: Statistics from SDK (dict or object).

    Returns:
        Dictionary representation.
    """
    if isinstance(stats, dict):
        return dict(stats)

    # Handle MagicMock or object with .get() method
    if hasattr(stats, "get"):
        # Try common stat keys
        stat_keys = [
            "bytes_in",
            "bytes_out",
            "packets_in",
            "packets_out",
            "errors_in",
            "errors_out",
            "rx_bytes",
            "tx_bytes",
            "rx_packets",
            "tx_packets",
        ]
        result: dict[str, Any] = {}
        for key in stat_keys:
            value = stats.get(key)
            if value is not None:
                result[key] = value
        return result if result else {"data": str(stats)}

    # Handle object with __dict__
    if hasattr(stats, "__dict__"):
        result = dict(vars(stats))
        return result

    return {"data": str(stats)}


@app.command("leases")
@handle_errors()
def diag_leases(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Show DHCP leases for a network.

    Displays active and reserved DHCP leases including MAC address,
    IP address, hostname, and expiration time.

    Useful for troubleshooting DHCP issues or finding device IPs.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    result = net_obj.diagnostics(diagnostic_type="dhcp_leases")

    # SDK returns a dict with dhcp_leases key containing the actual leases
    if isinstance(result, dict) and "dhcp_leases" in result:
        leases = result["dhcp_leases"]
    else:
        leases = result

    data = [_item_to_dict(lease) for lease in leases]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=LEASE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("addresses")
@handle_errors()
def diag_addresses(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Show all network addresses.

    Displays the address table for the network including IP addresses,
    MAC addresses, interfaces, and address types.

    Useful for viewing what devices are connected to the network.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    result = net_obj.diagnostics(diagnostic_type="addresses")

    # SDK returns a dict with addresses key containing the actual addresses
    if isinstance(result, dict) and "addresses" in result:
        addresses = result["addresses"]
    else:
        addresses = result

    data = [_item_to_dict(addr) for addr in addresses]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=ADDRESS_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("stats")
@handle_errors()
def diag_stats(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Show network traffic statistics.

    Displays traffic statistics including bytes and packets
    transmitted and received, as well as error counts.

    Useful for monitoring network performance and identifying issues.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    stats = net_obj.statistics()
    data = _stats_to_dict(stats)

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
