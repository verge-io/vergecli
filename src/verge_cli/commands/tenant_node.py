"""Tenant node (compute allocation) sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_NODE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="node",
    help="Manage tenant compute nodes.",
    no_args_is_help=True,
)


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


def _tenant_node_to_dict(node: Any) -> dict[str, Any]:
    """Convert a Tenant Node object to a dict for output."""
    raw_ram = node.get("ram")
    ram_gb = round(raw_ram / 1024, 2) if isinstance(raw_ram, (int, float)) else raw_ram
    return {
        "$key": node.key,
        "name": node.name,
        "cpu_cores": node.get("cpu_cores"),
        "ram_gb": ram_gb,
        "status": node.get("status", ""),
        "is_enabled": node.get("enabled"),
        "cluster_name": node.get("cluster_name", ""),
        "host_node": node.get("host_node", ""),
    }


def _resolve_tenant_node(tenant_obj: Any, identifier: str) -> int:
    """Resolve a tenant node name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    nodes = tenant_obj.nodes.list()
    matches = [n for n in nodes if n.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple tenant nodes match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Tenant node '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def tenant_node_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List compute nodes allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    nodes = tenant_obj.nodes.list()
    data = [_tenant_node_to_dict(n) for n in nodes]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_NODE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_node_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    node: Annotated[str, typer.Argument(help="Node name or key")],
) -> None:
    """Get details of a tenant compute node."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    node_key = _resolve_tenant_node(tenant_obj, node)
    node_obj = tenant_obj.nodes.get(node_key)
    output_result(
        _tenant_node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
