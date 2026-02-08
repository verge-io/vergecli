"""Node management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import NODE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="node",
    help="Manage nodes.",
    no_args_is_help=True,
)


def _node_to_dict(node: Any) -> dict[str, Any]:
    """Convert a Node object to a dict for output.

    Uses getattr() for SDK computed properties (ram_gb, is_physical,
    vergeos_version, status, cluster_name) which are @property accessors
    on the Node model, not available via .get().
    Falls back to .get() for raw data fields.
    """
    return {
        "key": node.key,
        "name": node.name,
        "status": getattr(node, "status", node.get("status", "")),
        "cluster_name": getattr(node, "cluster_name", node.get("cluster_name", "")),
        "ram_gb": getattr(node, "ram_gb", node.get("ram_gb")),
        "cores": node.get("cores"),
        "cpu_usage": getattr(node, "cpu_usage", node.get("cpu_usage")),
        "is_physical": getattr(node, "is_physical", node.get("is_physical")),
        "model": node.get("model", ""),
        "cpu": node.get("cpu", ""),
        "core_temp": getattr(node, "core_temp", node.get("core_temp")),
        "vergeos_version": getattr(node, "vergeos_version", node.get("vergeos_version", "")),
    }


@app.command("list")
@handle_errors()
def node_list(
    ctx: typer.Context,
    cluster: Annotated[
        str | None,
        typer.Option("--cluster", "-c", help="Filter by cluster name"),
    ] = None,
) -> None:
    """List all nodes."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {}
    if cluster is not None:
        kwargs["cluster"] = cluster

    nodes = vctx.client.nodes.list(**kwargs)
    data = [_node_to_dict(n) for n in nodes]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NODE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def node_get(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
) -> None:
    """Get details of a node."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.nodes, node, "Node")
    node_obj = vctx.client.nodes.get(key)

    output_result(
        _node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
