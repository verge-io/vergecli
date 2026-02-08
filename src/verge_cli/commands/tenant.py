"""Tenant management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="tenant",
    help="Manage tenants.",
    no_args_is_help=True,
)


def _tenant_to_dict(tenant: Any) -> dict[str, Any]:
    """Convert a Tenant object to a dictionary for output."""
    return {
        "$key": tenant.key,
        "name": tenant.name,
        "status": tenant.status,
        "state": tenant.get("state", ""),
        "is_isolated": tenant.get("is_isolated", False),
        "description": tenant.get("description", ""),
        "network_name": tenant.get("network_name", ""),
        "ui_address_ip": tenant.get("ui_address_ip", ""),
        "uuid": tenant.get("uuid", ""),
        "url": tenant.get("url", ""),
        "note": tenant.get("note", ""),
        "expose_cloud_snapshots": tenant.get("expose_cloud_snapshots", False),
        "allow_branding": tenant.get("allow_branding", False),
    }


@app.command("list")
@handle_errors()
def tenant_list(ctx: typer.Context) -> None:
    """List tenants."""
    vctx = get_context(ctx)
    tenants = vctx.client.tenants.list()
    data = [_tenant_to_dict(t) for t in tenants]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Get details of a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
