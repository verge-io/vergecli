"""Cluster management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import CLUSTER_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="cluster",
    help="Manage clusters.",
    no_args_is_help=True,
)


def _cluster_to_dict(cluster: Any) -> dict[str, Any]:
    """Convert a Cluster object to a dict for output."""
    # Use SDK properties for computed fields (total_ram_gb, ram_used_percent,
    # is_compute, is_storage, status) since .get() only accesses raw data.
    # Fall back to .get() for fields that may be on mock objects in tests.
    return {
        "key": cluster.key,
        "name": cluster.name,
        "status": getattr(cluster, "status", cluster.get("status", "")),
        "total_nodes": cluster.get("total_nodes"),
        "online_nodes": cluster.get("online_nodes"),
        "total_ram_gb": getattr(cluster, "total_ram_gb", cluster.get("total_ram_gb")),
        "ram_used_percent": getattr(cluster, "ram_used_percent", cluster.get("ram_used_percent")),
        "total_cores": cluster.get("total_cores"),
        "running_machines": cluster.get("running_machines"),
        "is_compute": getattr(cluster, "is_compute", cluster.get("is_compute")),
        "is_storage": getattr(cluster, "is_storage", cluster.get("is_storage")),
    }


@app.command("list")
@handle_errors()
def cluster_list(
    ctx: typer.Context,
) -> None:
    """List all clusters."""
    vctx = get_context(ctx)

    clusters = vctx.client.clusters.list()
    data = [_cluster_to_dict(c) for c in clusters]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=CLUSTER_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def cluster_get(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
) -> None:
    """Get details of a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")
    cluster_obj = vctx.client.clusters.get(key)

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
