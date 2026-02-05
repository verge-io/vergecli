"""System commands for Verge CLI."""

from __future__ import annotations

from typing import Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result

app = typer.Typer(
    name="system",
    help="System information and management.",
    no_args_is_help=True,
)


@app.command("info")
@handle_errors()
def system_info(ctx: typer.Context) -> None:
    """Display system information and statistics."""
    vctx = get_context(ctx)

    client = vctx.client

    # Get basic system info from connection
    info: dict[str, Any] = {
        "host": vctx.config.host,
        "version": client.version,
        "os_version": client.os_version,
        "cloud_name": client.cloud_name,
    }

    # Get dashboard statistics
    try:
        stats = client.system.statistics()
        info["vms_total"] = stats.vms_total
        info["vms_online"] = stats.vms_online
        info["tenants_total"] = stats.tenants_total
        info["tenants_online"] = stats.tenants_online
        info["networks_total"] = stats.networks_total
        info["networks_online"] = stats.networks_online
        info["nodes_total"] = stats.nodes_total
        info["nodes_online"] = stats.nodes_online
        info["alarms_total"] = stats.alarms_total
    except Exception:
        # Statistics might not be available, continue with basic info
        pass

    output_result(
        info,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("version")
@handle_errors()
def system_version(ctx: typer.Context) -> None:
    """Display VergeOS version."""
    vctx = get_context(ctx)

    client = vctx.client

    version_info = {
        "version": client.version,
        "os_version": client.os_version,
    }

    if vctx.query:
        output_result(
            version_info,
            output_format=vctx.output_format,
            query=vctx.query,
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    elif vctx.output_format == "json":
        output_result(
            version_info,
            output_format="json",
            quiet=vctx.quiet,
            no_color=vctx.no_color,
        )
    else:
        # Simple output for table mode
        typer.echo(f"VergeOS Version: {client.version}")
        if client.os_version:
            typer.echo(f"OS Version: {client.os_version}")
