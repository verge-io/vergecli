"""Tenant management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
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


@app.command("create")
@handle_errors()
def tenant_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Tenant name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Tenant description")
    ] = "",
    password: Annotated[
        str | None, typer.Option("--password", help="Admin password for tenant")
    ] = None,
    url: Annotated[str | None, typer.Option("--url", help="Tenant URL slug")] = None,
    note: Annotated[str | None, typer.Option("--note", help="Internal note")] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Create a new tenant."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {"name": name, "description": description}
    if password is not None:
        kwargs["password"] = password
    if url is not None:
        kwargs["url"] = url
    if note is not None:
        kwargs["note"] = note
    if expose_cloud_snapshots is not None:
        kwargs["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        kwargs["allow_branding"] = allow_branding

    tenant_obj = vctx.client.tenants.create(**kwargs)

    output_success(
        f"Created tenant '{tenant_obj.name}' (key: {tenant_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def tenant_update(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New tenant name")] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Tenant description")
    ] = None,
    url: Annotated[str | None, typer.Option("--url", help="Tenant URL slug")] = None,
    note: Annotated[str | None, typer.Option("--note", help="Internal note")] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Update a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if url is not None:
        updates["url"] = url
    if note is not None:
        updates["note"] = note
    if expose_cloud_snapshots is not None:
        updates["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        updates["allow_branding"] = allow_branding

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    tenant_obj = vctx.client.tenants.update(key, **updates)

    output_success(f"Updated tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
