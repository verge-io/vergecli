"""Tenant stats and logs sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_LOG_COLUMNS, TENANT_STATS_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

# ---------------------------------------------------------------------------
# Two Typer apps: stats + logs
# ---------------------------------------------------------------------------

stats_app = typer.Typer(
    name="stats",
    help="View tenant resource statistics.",
    no_args_is_help=True,
)

logs_app = typer.Typer(
    name="logs",
    help="View tenant activity logs.",
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
# Converters
# ---------------------------------------------------------------------------


def _stats_current_to_dict(stats: Any) -> dict[str, Any]:
    """Convert a TenantStats object to a dict for output."""
    return {
        "ram_used_mb": stats.ram_used_mb,
        "last_update": stats.last_update,
        "tenant_key": stats.tenant_key,
    }


def _stats_history_to_dict(entry: Any) -> dict[str, Any]:
    """Convert a TenantStatsHistory object to a dict for output."""
    return {
        "timestamp": entry.get("timestamp", ""),
        "cpu_percent": entry.total_cpu,
        "ram_used_mb": entry.ram_used_mb,
        "ram_total_mb": entry.ram_allocated_mb,
        "disk_read_ops": entry.get("disk_read_ops", ""),
        "disk_write_ops": entry.get("disk_write_ops", ""),
    }


def _log_to_dict(entry: Any) -> dict[str, Any]:
    """Convert a TenantLog object to a dict for output."""
    return {
        "timestamp": str(entry.timestamp) if entry.timestamp else "",
        "type": entry.level,
        "message": entry.text,
    }


# ===== Stats Commands =====


@stats_app.command("current")
@handle_errors()
def stats_current(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Show current resource usage for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    stats = tenant_obj.stats.get()

    # Stats returns a single object — output as key-value table
    output_result(
        _stats_current_to_dict(stats),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@stats_app.command("history")
@handle_errors()
def stats_history(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of entries")] = 20,
) -> None:
    """Show historical resource usage for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    history = tenant_obj.stats.history_short(limit=limit)

    output_result(
        [_stats_history_to_dict(e) for e in history],
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_STATS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


# ===== Logs Commands =====


@logs_app.command("list")
@handle_errors()
def logs_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of entries")] = 50,
    errors_only: Annotated[
        bool, typer.Option("--errors-only", help="Show only error entries")
    ] = False,
) -> None:
    """List activity log entries for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    entries = tenant_obj.logs.list(limit=limit, errors_only=errors_only)
    data = [_log_to_dict(e) for e in entries]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
