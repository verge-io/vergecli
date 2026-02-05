"""Network DNS zone and record commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import ResourceNotFoundError, handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

# Main DNS app
app = typer.Typer(
    name="dns",
    help="Manage DNS zones and records.",
    no_args_is_help=True,
)

# Zone subapp
zone_app = typer.Typer(
    name="zone",
    help="Manage DNS zones.",
    no_args_is_help=True,
)

# Record subapp
record_app = typer.Typer(
    name="record",
    help="Manage DNS records.",
    no_args_is_help=True,
)

# Register subapps
app.add_typer(zone_app, name="zone")
app.add_typer(record_app, name="record")

# Default columns for zone list output
ZONE_LIST_COLUMNS = ["domain", "type", "serial"]

# Default columns for record list output
RECORD_LIST_COLUMNS = ["host", "type", "value", "ttl", "priority"]


# =============================================================================
# Zone Helper Functions
# =============================================================================


def _resolve_zone_id(network: Any, identifier: str) -> int:
    """Resolve a zone name or ID to a key.

    Args:
        network: Network object with dns_zones collection.
        identifier: Zone name or numeric key.

    Returns:
        The zone key.

    Raises:
        ResourceNotFoundError: If zone not found.
    """
    # If numeric, treat as key directly
    if identifier.isdigit():
        return int(identifier)

    # Try to find by domain name
    zones = network.dns_zones.list()
    for zone in zones:
        domain = zone.get("domain") or getattr(zone, "domain", "")
        key = zone.get("$key") or getattr(zone, "key", None)
        if domain == identifier and key is not None:
            return int(key)

    raise ResourceNotFoundError(f"DNS zone '{identifier}' not found")


def _zone_to_dict(zone: Any) -> dict[str, Any]:
    """Convert a DNS Zone object to a dictionary for output.

    Args:
        zone: Zone object from SDK.

    Returns:
        Dictionary representation of the zone.
    """
    return {
        "key": zone.get("$key") or getattr(zone, "key", None),
        "domain": zone.get("domain", ""),
        "type": zone.get("type", "master"),
        "serial": zone.get("serial_number", 0),
    }


# =============================================================================
# Record Helper Functions
# =============================================================================


def _resolve_record_id(zone: Any, identifier: str) -> int:
    """Resolve a record name or ID to a key.

    Args:
        zone: Zone object with records collection.
        identifier: Record name or numeric key.

    Returns:
        The record key.

    Raises:
        ResourceNotFoundError: If record not found.
    """
    # If numeric, treat as key directly
    if identifier.isdigit():
        return int(identifier)

    # Try to find by name
    records = zone.records.list()
    for record in records:
        host = record.get("host") or getattr(record, "host", "")
        key = record.get("$key") or getattr(record, "key", None)
        if host == identifier and key is not None:
            return int(key)

    raise ResourceNotFoundError(f"DNS record '{identifier}' not found")


def _record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a DNS Record object to a dictionary for output.

    Args:
        record: Record object from SDK.

    Returns:
        Dictionary representation of the record.
    """
    return {
        "key": record.get("$key") or getattr(record, "key", None),
        "host": record.get("host", ""),
        "type": record.get("type", "A"),
        "value": record.get("value", ""),
        "ttl": record.get("ttl", ""),
        "priority": record.get("mx_preference", 0),
    }


# =============================================================================
# Zone Commands
# =============================================================================


@zone_app.command("list")
@handle_errors()
def zone_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List DNS zones for a network.

    Shows all BIND DNS zones configured on the network.
    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zones = net_obj.dns_zones.list()
    data = [_zone_to_dict(zone) for zone in zones]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=ZONE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@zone_app.command("get")
@handle_errors()
def zone_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Get details of a DNS zone."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    output_result(
        _zone_to_dict(zone_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@zone_app.command("create")
@handle_errors()
def zone_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    domain: Annotated[str, typer.Option("--domain", "-d", help="Zone domain name")],
    zone_type: Annotated[
        str, typer.Option("--type", "-t", help="Zone type (master/slave)")
    ] = "master",
) -> None:
    """Create a new DNS zone.

    Creates a BIND DNS zone on the network. Zone commands work on
    networks with BIND enabled. Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    create_kwargs: dict[str, Any] = {
        "domain": domain,
        "type": zone_type,
    }

    zone_obj = net_obj.dns_zones.create(**create_kwargs)

    zone_domain = zone_obj.get("domain") or getattr(zone_obj, "domain", "")
    zone_key_val = zone_obj.get("$key") or zone_obj.key
    output_success(f"Created DNS zone '{zone_domain}' (key: {zone_key_val})", quiet=vctx.quiet)

    output_result(
        _zone_to_dict(zone_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@zone_app.command("update")
@handle_errors()
def zone_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone domain or key")],
    domain: Annotated[str | None, typer.Option("--domain", "-d", help="New domain name")] = None,
    zone_type: Annotated[
        str | None, typer.Option("--type", "-t", help="Zone type (master/slave)")
    ] = None,
) -> None:
    """Update a DNS zone.

    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if domain is not None:
        updates["domain"] = domain
    if zone_type is not None:
        updates["type"] = zone_type

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    zone_obj = net_obj.dns_zones.update(zone_key, **updates)

    zone_domain = zone_obj.get("domain") or getattr(zone_obj, "domain", "")
    output_success(f"Updated DNS zone '{zone_domain}'", quiet=vctx.quiet)

    output_result(
        _zone_to_dict(zone_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@zone_app.command("delete")
@handle_errors()
def zone_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a DNS zone.

    This will delete the zone and all its records.
    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    zone_domain = zone_obj.get("domain") or str(zone_key)

    if not confirm_action(f"Delete DNS zone '{zone_domain}' and all its records?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    net_obj.dns_zones.delete(zone_key)
    output_success(f"Deleted DNS zone '{zone_domain}'", quiet=vctx.quiet)


# =============================================================================
# Record Commands
# =============================================================================


@record_app.command("list")
@handle_errors()
def record_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    record_type: Annotated[
        str | None, typer.Option("--type", "-t", help="Filter by record type (A/AAAA/CNAME/MX/TXT)")
    ] = None,
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List DNS records for a zone.

    Shows all DNS records in the specified zone.
    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    # Build filter kwargs
    filter_kwargs: dict[str, Any] = {}
    if record_type:
        filter_kwargs["type"] = record_type

    records = zone_obj.records.list(**filter_kwargs)
    data = [_record_to_dict(record) for record in records]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=RECORD_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@record_app.command("get")
@handle_errors()
def record_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    record: Annotated[str, typer.Argument(help="Record name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Get details of a DNS record."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    record_key = _resolve_record_id(zone_obj, record)
    record_obj = zone_obj.records.get(record_key)

    output_result(
        _record_to_dict(record_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@record_app.command("create")
@handle_errors()
def record_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    name: Annotated[str, typer.Option("--name", "-n", help="Record name (e.g., www, @, mail)")],
    record_type: Annotated[
        str, typer.Option("--type", "-t", help="Record type (A/AAAA/CNAME/MX/TXT/NS/PTR/SRV)")
    ],
    address: Annotated[
        str, typer.Option("--address", "-a", help="Record value/address (IP or hostname)")
    ],
    ttl: Annotated[int, typer.Option("--ttl", help="Time to live in seconds")] = 3600,
    priority: Annotated[
        int | None, typer.Option("--priority", "-p", help="Priority (for MX/SRV records)")
    ] = None,
) -> None:
    """Create a new DNS record.

    Creates a DNS record in the specified zone.
    Changes require apply-dns to take effect.

    Examples:
        vrg network dns record create mynet example.com --name www --type A --address 10.0.0.100
        vrg network dns record create mynet example.com --name @ --type MX --address mail.example.com --priority 10
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    create_kwargs: dict[str, Any] = {
        "host": name,
        "record_type": record_type,
        "value": address,
        "ttl": ttl,
    }

    if priority is not None:
        create_kwargs["mx_preference"] = priority

    record_obj = zone_obj.records.create(**create_kwargs)

    record_host = record_obj.get("host") or name
    record_value = record_obj.get("value") or address
    output_success(f"Created DNS record '{record_host}' -> {record_value}", quiet=vctx.quiet)

    output_result(
        _record_to_dict(record_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@record_app.command("update")
@handle_errors()
def record_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    record: Annotated[str, typer.Argument(help="Record name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New record name")] = None,
    record_type: Annotated[str | None, typer.Option("--type", "-t", help="Record type")] = None,
    address: Annotated[
        str | None, typer.Option("--address", "-a", help="New record value/address")
    ] = None,
    ttl: Annotated[int | None, typer.Option("--ttl", help="Time to live")] = None,
    priority: Annotated[int | None, typer.Option("--priority", "-p", help="Priority")] = None,
) -> None:
    """Update a DNS record.

    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    record_key = _resolve_record_id(zone_obj, record)

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if name is not None:
        updates["host"] = name
    if record_type is not None:
        updates["type"] = record_type
    if address is not None:
        updates["value"] = address
    if ttl is not None:
        updates["ttl"] = ttl
    if priority is not None:
        updates["mx_preference"] = priority

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    record_obj = zone_obj.records.update(record_key, **updates)

    record_host = record_obj.get("host") or record
    output_success(f"Updated DNS record '{record_host}'", quiet=vctx.quiet)

    output_result(
        _record_to_dict(record_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@record_app.command("delete")
@handle_errors()
def record_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    zone: Annotated[str, typer.Argument(help="Zone name or key")],
    record: Annotated[str, typer.Argument(help="Record name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a DNS record.

    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    zone_key = _resolve_zone_id(net_obj, zone)
    zone_obj = net_obj.dns_zones.get(zone_key)

    record_key = _resolve_record_id(zone_obj, record)
    record_obj = zone_obj.records.get(record_key)

    record_host = record_obj.get("host") or str(record_key)

    if not confirm_action(f"Delete DNS record '{record_host}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    zone_obj.records.delete(record_key)
    output_success(f"Deleted DNS record '{record_host}'", quiet=vctx.quiet)
