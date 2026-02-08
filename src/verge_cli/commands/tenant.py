"""Tenant management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id, wait_for_state

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


@app.command("delete")
@handle_errors()
def tenant_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force delete running tenant")
    ] = False,
) -> None:
    """Delete a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running and not force:
        typer.echo(
            f"Error: Tenant '{tenant_obj.name}' is running. Use --force to delete anyway.",
            err=True,
        )
        raise typer.Exit(7)

    if not confirm_action(f"Delete tenant '{tenant_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.tenants.delete(key)
    output_success(f"Deleted tenant '{tenant_obj.name}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def tenant_start(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for tenant to start")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Start a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is already running.")
        return

    vctx.client.tenants.power_on(key)
    output_success(f"Starting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(f"Tenant '{tenant_obj.name}' is now running", quiet=vctx.quiet)


@app.command("stop")
@handle_errors()
def tenant_stop(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for tenant to stop")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Stop a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        return

    vctx.client.tenants.power_off(key)
    output_success(f"Stopping tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state=["stopped", "offline"],
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(f"Tenant '{tenant_obj.name}' is now stopped", quiet=vctx.quiet)


@app.command("restart")
@handle_errors()
def tenant_restart(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for tenant to restart")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Restart a tenant.

    This sends a restart command to the tenant. For a hard reset
    (like pressing the reset button), use 'vrg tenant reset' instead.
    """
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running. Use 'vrg tenant start' instead.")
        raise typer.Exit(1)

    vctx.client.tenants.restart(key)
    output_success(f"Restarting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(f"Tenant '{tenant_obj.name}' has restarted", quiet=vctx.quiet)


@app.command("reset")
@handle_errors()
def tenant_reset(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Hard reset a tenant (like pressing the reset button)."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        raise typer.Exit(1)

    vctx.client.tenants.reset(key)
    output_success(f"Reset tenant '{tenant_obj.name}'", quiet=vctx.quiet)
