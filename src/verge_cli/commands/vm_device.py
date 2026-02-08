"""VM device sub-resource commands (TPM only)."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import DEVICE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="device",
    help="Manage VM devices (TPM).",
    no_args_is_help=True,
)


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _device_to_dict(device: Any) -> dict[str, Any]:
    """Convert a Device object to a dict for output."""
    return {
        "$key": device.key,
        "name": device.name,
        "device_type": device.device_type,
        "enabled": device.is_enabled,
        "optional": device.is_optional,
    }


def _resolve_device(vm_obj: Any, identifier: str) -> int:
    """Resolve a device name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    devices = vm_obj.devices.list()
    matches = [d for d in devices if d.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(f"Error: Multiple devices match '{identifier}'. Use a numeric key.", err=True)
        raise typer.Exit(7)
    typer.echo(f"Error: Device '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def device_list(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
) -> None:
    """List devices on a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    devices = vm_obj.devices.list()
    data = [_device_to_dict(d) for d in devices]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=DEVICE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def device_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    device: Annotated[str, typer.Argument(help="Device name or key")],
) -> None:
    """Get details of a VM device."""
    vctx, vm_obj = _get_vm(ctx, vm)
    device_key = _resolve_device(vm_obj, device)
    device_obj = vm_obj.devices.get(device_key)
    output_result(
        _device_to_dict(device_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def device_create(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="Device name")] = None,
    model: Annotated[str, typer.Option("--model", "-m", help="TPM model (tis, crb)")] = "crb",
    version: Annotated[str, typer.Option("--version", "-V", help="TPM version (1, 2)")] = "2",
) -> None:
    """Add a TPM device to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)

    device_obj = vm_obj.devices.create(
        device_type="tpm",
        name=name,
        settings={"model": model, "version": version},
    )

    output_success(f"Created TPM device (key: {device_obj.key})", quiet=vctx.quiet)
    output_result(
        _device_to_dict(device_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def device_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    device: Annotated[str, typer.Argument(help="Device name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a device from a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    device_key = _resolve_device(vm_obj, device)

    if not confirm_action(f"Delete device '{device}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vm_obj.devices.delete(device_key)
    output_success(f"Deleted device '{device}'", quiet=vctx.quiet)
