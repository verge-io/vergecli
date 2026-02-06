"""VM commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.commands import vm_drive
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id, wait_for_state

app = typer.Typer(
    name="vm",
    help="Manage virtual machines.",
    no_args_is_help=True,
)

app.add_typer(vm_drive.app, name="drive")

# Default columns for VM list output
VM_LIST_COLUMNS = ["name", "status", "cpu_cores", "ram", "cluster_name", "node_name", "restart"]


@app.command("list")
@handle_errors()
def vm_list(
    ctx: typer.Context,
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="Filter by status (running, stopped, etc.)"),
    ] = None,
    filter: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression (e.g., \"name eq 'foo'\")"),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output format (table, json)"),
    ] = None,
    query: Annotated[
        str | None,
        typer.Option("--query", help="Extract field using dot notation (e.g., 'name')"),
    ] = None,
) -> None:
    """List virtual machines."""
    vctx = get_context(ctx)

    # Build filter
    odata_filter = filter
    if status:
        status_filter = f"status eq '{status}'"
        odata_filter = f"({odata_filter}) and {status_filter}" if odata_filter else status_filter

    vms = vctx.client.vms.list(filter=odata_filter)

    # Convert to dicts for output
    data = [_vm_to_dict(vm) for vm in vms]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=VM_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def vm_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output format (table, json)"),
    ] = None,
    query: Annotated[
        str | None,
        typer.Option("--query", help="Extract field using dot notation (e.g., 'status')"),
    ] = None,
) -> None:
    """Get details of a virtual machine."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    output_result(
        _vm_to_dict(vm_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def vm_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="VM name")],
    ram: Annotated[int, typer.Option("--ram", "-r", help="RAM in MB")] = 1024,
    cpu: Annotated[int, typer.Option("--cpu", "-c", help="Number of CPU cores")] = 1,
    description: Annotated[str, typer.Option("--description", "-d", help="VM description")] = "",
    os_family: Annotated[
        str,
        typer.Option("--os", help="OS family (linux, windows, freebsd, other)"),
    ] = "linux",
) -> None:
    """Create a new virtual machine."""
    vctx = get_context(ctx)

    vm_obj = vctx.client.vms.create(
        name=name,
        ram=ram,
        cpu_cores=cpu,
        description=description,
        os_family=os_family,
    )

    output_success(f"Created VM '{vm_obj.name}' (key: {vm_obj.key})", quiet=vctx.quiet)

    output_result(
        _vm_to_dict(vm_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def vm_update(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New VM name")] = None,
    ram: Annotated[int | None, typer.Option("--ram", "-r", help="RAM in MB")] = None,
    cpu: Annotated[int | None, typer.Option("--cpu", "-c", help="Number of CPU cores")] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="VM description"),
    ] = None,
) -> None:
    """Update a virtual machine."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if ram is not None:
        updates["ram"] = ram
    if cpu is not None:
        updates["cpu_cores"] = cpu
    if description is not None:
        updates["description"] = description

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    vm_obj = vctx.client.vms.update(key, **updates)

    output_success(f"Updated VM '{vm_obj.name}'", quiet=vctx.quiet)

    output_result(
        _vm_to_dict(vm_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def vm_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="Force delete running VM")] = False,
) -> None:
    """Delete a virtual machine."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    # Check if running and not forcing
    if vm_obj.is_running and not force:
        typer.echo(f"Error: VM '{vm_obj.name}' is running. Use --force to delete anyway.", err=True)
        raise typer.Exit(7)

    if not confirm_action(f"Delete VM '{vm_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.vms.delete(key)
    output_success(f"Deleted VM '{vm_obj.name}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def vm_start(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for VM to start")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Start a virtual machine."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    if vm_obj.is_running:
        typer.echo(f"VM '{vm_obj.name}' is already running.")
        return

    vm_obj.power_on()
    output_success(f"Starting VM '{vm_obj.name}'", quiet=vctx.quiet)

    if wait:
        vm_obj = wait_for_state(
            get_resource=vctx.client.vms.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="VM",
            quiet=vctx.quiet,
        )
        output_success(f"VM '{vm_obj.name}' is now running", quiet=vctx.quiet)


@app.command("stop")
@handle_errors()
def vm_stop(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Force power off")] = False,
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for VM to stop")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Stop a virtual machine."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    if not vm_obj.is_running:
        typer.echo(f"VM '{vm_obj.name}' is not running.")
        return

    vm_obj.power_off(force=force)
    action = "Forcing power off" if force else "Stopping"
    output_success(f"{action} VM '{vm_obj.name}'", quiet=vctx.quiet)

    if wait:
        vm_obj = wait_for_state(
            get_resource=vctx.client.vms.get,
            resource_key=key,
            target_state=["stopped", "offline"],
            timeout=timeout,
            state_field="status",
            resource_type="VM",
            quiet=vctx.quiet,
        )
        output_success(f"VM '{vm_obj.name}' is now stopped", quiet=vctx.quiet)


@app.command("restart")
@handle_errors()
def vm_restart(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for VM to restart")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Restart a virtual machine (graceful stop then start).

    This performs a graceful shutdown followed by power on. For a hard reset
    (like pressing the reset button), use 'vrg vm reset' instead.
    """
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    if not vm_obj.is_running:
        typer.echo(f"VM '{vm_obj.name}' is not running. Use 'vrg vm start' instead.")
        raise typer.Exit(1)

    # Graceful stop
    vm_obj.power_off(force=False)
    output_success(f"Stopping VM '{vm_obj.name}'...", quiet=vctx.quiet)

    # Wait for stop
    vm_obj = wait_for_state(
        get_resource=vctx.client.vms.get,
        resource_key=key,
        target_state=["stopped", "offline"],
        timeout=timeout // 2,  # Use half timeout for stop
        state_field="status",
        resource_type="VM",
        quiet=True,
    )

    # Start
    vm_obj.power_on()
    output_success(f"Starting VM '{vm_obj.name}'...", quiet=vctx.quiet)

    if wait:
        vm_obj = wait_for_state(
            get_resource=vctx.client.vms.get,
            resource_key=key,
            target_state="running",
            timeout=timeout // 2,
            state_field="status",
            resource_type="VM",
            quiet=vctx.quiet,
        )
        output_success(f"VM '{vm_obj.name}' has restarted", quiet=vctx.quiet)


@app.command("reset")
@handle_errors()
def vm_reset(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
) -> None:
    """Hard reset a virtual machine (like pressing the reset button)."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    if not vm_obj.is_running:
        typer.echo(f"VM '{vm_obj.name}' is not running.")
        raise typer.Exit(1)

    vm_obj.reset()
    output_success(f"Reset VM '{vm_obj.name}'", quiet=vctx.quiet)


def _vm_to_dict(vm: Any) -> dict[str, Any]:
    """Convert a VM object to a dictionary for output."""
    return {
        "key": vm.key,
        "name": vm.name,
        "description": vm.get("description", ""),
        "status": vm.status,
        "running": vm.is_running,
        "cpu_cores": vm.get("cpu_cores"),
        "ram": vm.get("ram"),
        "os_family": vm.get("os_family"),
        "cluster_name": vm.cluster_name,
        "node_name": vm.node_name,
        "created": vm.get("created"),
        "modified": vm.get("modified"),
        # Status flag for pending changes
        "needs_restart": vm.get("need_restart", False),
        # Short alias for list column (Y or empty string)
        "restart": "Y" if vm.get("need_restart", False) else "",
    }
