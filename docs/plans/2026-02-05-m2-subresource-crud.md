# Milestone 2: Sub-Resource CRUD Commands ✅

> **Status:** Complete — merged via PR #4 on 2026-02-06.

**Goal:** Add `vrg vm drive`, `vrg vm nic`, and `vrg vm device` sub-commands as thin SDK wrappers.

**Architecture:** Three new command modules registered as sub-Typer apps on `vm.app`. Each command fetches the parent VM first, then accesses sub-resources via `vm.drives`, `vm.nics`, `vm.devices`. New shared fixtures in conftest.py.

**Tech Stack:** Python 3.10+, Typer, pyvergeos SDK, pytest

**Depends on:** M1 (units.py for `--size` parsing, resolver.py for `--network` resolution)

---

### Task 1: Add test fixtures for sub-resources

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Add mock drive, NIC, and device fixtures**

Add these fixtures after the existing `mock_dns_view` fixture:

```python
@pytest.fixture
def mock_drive() -> MagicMock:
    """Create a mock Drive object."""
    drive = MagicMock()
    drive.key = 10
    drive.name = "OS Disk"
    drive.size_gb = 50.0
    drive.used_gb = 12.5
    drive.interface_display = "VirtIO SCSI"
    drive.media_display = "Disk"
    drive.is_enabled = True
    drive.is_readonly = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 10,
            "name": "OS Disk",
            "description": "Operating System Disk",
            "interface": "virtio-scsi",
            "media": "disk",
            "disksize": 53687091200,
            "preferred_tier": 3,
            "enabled": True,
            "readonly": False,
            "machine": 38,
        }
        return data.get(key, default)

    drive.get = mock_get
    return drive


@pytest.fixture
def mock_nic() -> MagicMock:
    """Create a mock NIC object."""
    nic = MagicMock()
    nic.key = 20
    nic.name = "Primary Network"
    nic.interface_display = "VirtIO"
    nic.is_enabled = True
    nic.mac_address = "52:54:00:12:34:56"
    nic.ip_address = "10.0.0.100"
    nic.network_name = "DMZ Internal"
    nic.network_key = 3

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 20,
            "name": "Primary Network",
            "description": "LAN connection",
            "interface": "virtio",
            "enabled": True,
            "mac": "52:54:00:12:34:56",
            "ipaddress": "10.0.0.100",
            "vnet": 3,
            "vnet_name": "DMZ Internal",
            "machine": 38,
        }
        return data.get(key, default)

    nic.get = mock_get
    return nic


@pytest.fixture
def mock_device() -> MagicMock:
    """Create a mock Device object (TPM)."""
    device = MagicMock()
    device.key = 30
    device.name = "TPM"
    device.device_type = "TPM"
    device.device_type_raw = "tpm"
    device.is_enabled = True
    device.is_optional = False
    device.is_tpm = True
    device.is_gpu = False
    device.is_usb = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 30,
            "name": "TPM",
            "type": "tpm",
            "enabled": True,
            "optional": False,
            "settings_args": {"model": "crb", "version": "2"},
            "machine": 38,
        }
        return data.get(key, default)

    device.get = mock_get
    return device
```

**Step 2: Verify existing tests still pass**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add mock fixtures for drives, NICs, and devices"
```

---

### Task 2: Create vm_drive.py

**Files:**
- Create: `src/verge_cli/commands/vm_drive.py`
- Create: `tests/unit/test_vm_drive.py`

**Context — SDK method signatures:**
```python
# DriveManager (accessed via vm.drives)
vm.drives.list(filter=None, media=None) -> list[Drive]
vm.drives.get(key=None, name=None) -> Drive
vm.drives.create(size_gb=None, name=None, interface="virtio-scsi", media="disk",
                  tier=None, description="", readonly=False, enabled=True,
                  media_source=None) -> Drive
vm.drives.update(key, **kwargs) -> Drive
vm.drives.delete(key) -> None
vm.drives.import_drive(file_key=None, file_name=None, name=None,
                        interface="virtio-scsi", tier=None,
                        preserve_drive_format=False, enabled=True) -> Drive
```

**Step 1: Write failing tests**

```python
# tests/unit/test_vm_drive.py
"""Tests for VM drive sub-resource commands."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_drive_list(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive list should list drives on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]

    result = cli_runner.invoke(app, ["vm", "drive", "list", "test-vm"])

    assert result.exit_code == 0
    assert "OS Disk" in result.output
    mock_vm.drives.list.assert_called_once()


def test_drive_get(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive get should show drive details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]
    mock_vm.drives.get.return_value = mock_drive

    result = cli_runner.invoke(app, ["vm", "drive", "get", "test-vm", "OS Disk"])

    assert result.exit_code == 0
    assert "OS Disk" in result.output


def test_drive_create(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive create should add a drive to a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.create.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        ["vm", "drive", "create", "test-vm", "--size", "50GB", "--name", "OS Disk"],
    )

    assert result.exit_code == 0
    mock_vm.drives.create.assert_called_once()
    call_kwargs = mock_vm.drives.create.call_args[1]
    assert call_kwargs["size_gb"] == 50
    assert call_kwargs["name"] == "OS Disk"


def test_drive_create_with_interface(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive create should accept --interface flag."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.create.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        [
            "vm", "drive", "create", "test-vm",
            "--size", "100GB",
            "--interface", "ide",
            "--media", "disk",
            "--tier", "2",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_vm.drives.create.call_args[1]
    assert call_kwargs["interface"] == "ide"
    assert call_kwargs["media"] == "disk"
    assert call_kwargs["tier"] == 2


def test_drive_delete(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive delete should remove a drive."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]

    result = cli_runner.invoke(
        app, ["vm", "drive", "delete", "test-vm", "OS Disk", "--yes"]
    )

    assert result.exit_code == 0
    mock_vm.drives.delete.assert_called_once_with(10)


def test_drive_update(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive update should update drive properties."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]
    mock_vm.drives.update.return_value = mock_drive

    result = cli_runner.invoke(
        app, ["vm", "drive", "update", "test-vm", "OS Disk", "--name", "Boot Disk"]
    )

    assert result.exit_code == 0
    mock_vm.drives.update.assert_called_once()


def test_drive_import(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive import should import a drive from file."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.import_drive.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        ["vm", "drive", "import", "test-vm", "--file-name", "disk.vmdk"],
    )

    assert result.exit_code == 0
    mock_vm.drives.import_drive.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_vm_drive.py -v`
Expected: FAIL (commands not registered yet)

**Step 3: Implement vm_drive.py**

```python
# src/verge_cli/commands/vm_drive.py
"""VM drive sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.template.units import parse_disk_size
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="drive",
    help="Manage VM drives.",
    no_args_is_help=True,
)

DRIVE_LIST_COLUMNS = ["name", "media", "interface", "size_gb", "tier", "enabled"]


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _drive_to_dict(drive: Any) -> dict[str, Any]:
    """Convert a Drive object to a dict for output."""
    return {
        "key": drive.key,
        "name": drive.name,
        "description": drive.get("description", ""),
        "media": drive.get("media", ""),
        "interface": drive.get("interface", ""),
        "size_gb": drive.size_gb,
        "tier": drive.get("preferred_tier", ""),
        "enabled": drive.is_enabled,
        "readonly": drive.is_readonly,
    }


def _resolve_drive(vm_obj: Any, identifier: str) -> int:
    """Resolve a drive name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    drives = vm_obj.drives.list()
    matches = [d for d in drives if d.name == identifier]
    if len(matches) == 1:
        return matches[0].key
    if len(matches) > 1:
        msg = f"Multiple drives match '{identifier}'. Use a numeric key."
        raise typer.Exit(7)
    msg = f"Drive '{identifier}' not found."
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def drive_list(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    media: Annotated[
        str | None, typer.Option("--media", help="Filter by media type (disk, cdrom)")
    ] = None,
) -> None:
    """List drives attached to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drives = vm_obj.drives.list(media=media)
    data = [_drive_to_dict(d) for d in drives]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=DRIVE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def drive_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
) -> None:
    """Get details of a VM drive."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)
    drive_obj = vm_obj.drives.get(drive_key)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def drive_create(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    size: Annotated[
        str | None,
        typer.Option("--size", "-s", help="Disk size (e.g., 50GB, 1TB)"),
    ] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Drive name")] = None,
    interface: Annotated[
        str, typer.Option("--interface", "-i", help="Drive interface")
    ] = "virtio-scsi",
    media: Annotated[str, typer.Option("--media", "-m", help="Media type")] = "disk",
    tier: Annotated[
        int | None, typer.Option("--tier", "-t", help="Storage tier (1-5)")
    ] = None,
    description: Annotated[str, typer.Option("--description", help="Description")] = "",
    media_source: Annotated[
        str | None, typer.Option("--media-source", help="Media file ID or name (for cdrom/import)")
    ] = None,
) -> None:
    """Add a drive to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)

    size_gb = parse_disk_size(size) if size else None

    # Resolve media_source to int if numeric
    resolved_source = None
    if media_source is not None:
        resolved_source = int(media_source) if media_source.isdigit() else media_source

    drive_obj = vm_obj.drives.create(
        size_gb=size_gb,
        name=name,
        interface=interface,
        media=media,
        tier=tier,
        description=description,
        media_source=resolved_source,
    )

    output_success(f"Created drive '{drive_obj.name}' (key: {drive_obj.key})", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def drive_update(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name")] = None,
    size: Annotated[str | None, typer.Option("--size", "-s", help="New size")] = None,
    tier: Annotated[int | None, typer.Option("--tier", "-t", help="Storage tier")] = None,
    enabled: Annotated[bool | None, typer.Option("--enabled/--disabled", help="Enable/disable")] = None,
) -> None:
    """Update a VM drive."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if size is not None:
        updates["size_gb"] = parse_disk_size(size)
    if tier is not None:
        updates["preferred_tier"] = tier
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    drive_obj = vm_obj.drives.update(drive_key, **updates)
    output_success(f"Updated drive '{drive_obj.name}'", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def drive_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    drive: Annotated[str, typer.Argument(help="Drive name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a drive from a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    drive_key = _resolve_drive(vm_obj, drive)

    if not confirm_action(f"Delete drive '{drive}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vm_obj.drives.delete(drive_key)
    output_success(f"Deleted drive '{drive}'", quiet=vctx.quiet)


@app.command("import")
@handle_errors()
def drive_import(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    file_name: Annotated[
        str | None,
        typer.Option("--file-name", help="Source file name (e.g., disk.vmdk)"),
    ] = None,
    file_key: Annotated[
        int | None, typer.Option("--file-key", help="Source file key")
    ] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Drive name")] = None,
    interface: Annotated[str, typer.Option("--interface", help="Drive interface")] = "virtio-scsi",
    tier: Annotated[int | None, typer.Option("--tier", help="Storage tier")] = None,
) -> None:
    """Import a drive from a file (VMDK, QCOW2, VHD, OVA)."""
    vctx, vm_obj = _get_vm(ctx, vm)

    if not file_name and not file_key:
        typer.echo("Error: Provide --file-name or --file-key.", err=True)
        raise typer.Exit(2)

    drive_obj = vm_obj.drives.import_drive(
        file_key=file_key,
        file_name=file_name,
        name=name,
        interface=interface,
        tier=tier,
    )

    output_success(f"Imported drive '{drive_obj.name}' (key: {drive_obj.key})", quiet=vctx.quiet)
    output_result(
        _drive_to_dict(drive_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 4: Register drive sub-command on vm app**

In `src/verge_cli/commands/vm.py`, add at the top imports:
```python
from verge_cli.commands import vm_drive
```

And after the `app = typer.Typer(...)` definition, add:
```python
app.add_typer(vm_drive.app, name="drive")
```

**Step 5: Run tests**

Run: `uv run pytest tests/unit/test_vm_drive.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/verge_cli/commands/vm_drive.py tests/unit/test_vm_drive.py src/verge_cli/commands/vm.py
git commit -m "feat: add vrg vm drive sub-resource commands"
```

---

### Task 3: Create vm_nic.py

**Files:**
- Create: `src/verge_cli/commands/vm_nic.py`
- Create: `tests/unit/test_vm_nic.py`

**Context — SDK method signatures:**
```python
vm.nics.list(filter=None) -> list[NIC]
vm.nics.get(key=None, name=None) -> NIC
vm.nics.create(network=None, name=None, interface="virtio",
               mac_address=None, ip_address=None, description="",
               enabled=True) -> NIC
vm.nics.update(key, **kwargs) -> NIC
vm.nics.delete(key) -> None
```

**Note:** `network` param accepts int (key) or str (name) — SDK resolves internally.

**Step 1: Write failing tests**

```python
# tests/unit/test_vm_nic.py
"""Tests for VM NIC sub-resource commands."""

from verge_cli.cli import app


def test_nic_list(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic list should list NICs on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]

    result = cli_runner.invoke(app, ["vm", "nic", "list", "test-vm"])

    assert result.exit_code == 0
    assert "Primary Network" in result.output


def test_nic_get(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic get should show NIC details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]
    mock_vm.nics.get.return_value = mock_nic

    result = cli_runner.invoke(app, ["vm", "nic", "get", "test-vm", "Primary Network"])

    assert result.exit_code == 0
    assert "Primary Network" in result.output


def test_nic_create(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic create should add a NIC to a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.create.return_value = mock_nic

    result = cli_runner.invoke(
        app,
        ["vm", "nic", "create", "test-vm", "--network", "DMZ Internal", "--name", "eth0"],
    )

    assert result.exit_code == 0
    mock_vm.nics.create.assert_called_once()
    call_kwargs = mock_vm.nics.create.call_args[1]
    assert call_kwargs["network"] == "DMZ Internal"


def test_nic_delete(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic delete should remove a NIC."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]

    result = cli_runner.invoke(
        app, ["vm", "nic", "delete", "test-vm", "Primary Network", "--yes"]
    )

    assert result.exit_code == 0
    mock_vm.nics.delete.assert_called_once_with(20)


def test_nic_update(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic update should update NIC properties."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]
    mock_vm.nics.update.return_value = mock_nic

    result = cli_runner.invoke(
        app, ["vm", "nic", "update", "test-vm", "Primary Network", "--name", "mgmt0"]
    )

    assert result.exit_code == 0
    mock_vm.nics.update.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_vm_nic.py -v`
Expected: FAIL

**Step 3: Implement vm_nic.py**

Follow the same pattern as `vm_drive.py`:
- `_get_vm()` helper (import from vm_drive or duplicate — small enough to duplicate)
- `_nic_to_dict()` — fields: key, name, description, interface, network_name, network_key, mac_address, ip_address, enabled
- `_resolve_nic()` — resolve NIC name or ID to key
- NIC_LIST_COLUMNS = ["name", "interface", "network_name", "mac_address", "ip_address", "enabled"]
- Commands: list, get, create, update, delete
- `create` flags: `--network` (required), `--name`, `--interface` (default "virtio"), `--mac`, `--ip`, `--description`
- `update` flags: `--name`, `--enabled/--disabled`, `--network`
- Network value passed directly to SDK (it resolves names internally)

```python
# src/verge_cli/commands/vm_nic.py
"""VM NIC sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="nic",
    help="Manage VM network interfaces.",
    no_args_is_help=True,
)

NIC_LIST_COLUMNS = ["name", "interface", "network_name", "mac_address", "ip_address", "enabled"]


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _nic_to_dict(nic: Any) -> dict[str, Any]:
    """Convert a NIC object to a dict for output."""
    return {
        "key": nic.key,
        "name": nic.name,
        "description": nic.get("description", ""),
        "interface": nic.get("interface", ""),
        "network_name": nic.network_name,
        "network_key": nic.network_key,
        "mac_address": nic.mac_address,
        "ip_address": nic.ip_address,
        "enabled": nic.is_enabled,
    }


def _resolve_nic(vm_obj: Any, identifier: str) -> int:
    """Resolve a NIC name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    nics = vm_obj.nics.list()
    matches = [n for n in nics if n.name == identifier]
    if len(matches) == 1:
        return matches[0].key
    if len(matches) > 1:
        typer.echo(f"Error: Multiple NICs match '{identifier}'. Use a numeric key.", err=True)
        raise typer.Exit(7)
    typer.echo(f"Error: NIC '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def nic_list(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
) -> None:
    """List network interfaces on a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    nics = vm_obj.nics.list()
    data = [_nic_to_dict(n) for n in nics]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NIC_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def nic_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    nic: Annotated[str, typer.Argument(help="NIC name or key")],
) -> None:
    """Get details of a VM network interface."""
    vctx, vm_obj = _get_vm(ctx, vm)
    nic_key = _resolve_nic(vm_obj, nic)
    nic_obj = vm_obj.nics.get(nic_key)
    output_result(
        _nic_to_dict(nic_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def nic_create(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    network: Annotated[str, typer.Option("--network", "-N", help="Network name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="NIC name")] = None,
    interface: Annotated[str, typer.Option("--interface", "-i", help="NIC interface type")] = "virtio",
    mac: Annotated[str | None, typer.Option("--mac", help="MAC address")] = None,
    ip: Annotated[str | None, typer.Option("--ip", help="IP address")] = None,
    description: Annotated[str, typer.Option("--description", help="Description")] = "",
) -> None:
    """Add a network interface to a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)

    # Pass network as-is — SDK resolves names internally
    nic_obj = vm_obj.nics.create(
        network=network,
        name=name,
        interface=interface,
        mac_address=mac,
        ip_address=ip,
        description=description,
    )

    output_success(f"Created NIC '{nic_obj.name}' (key: {nic_obj.key})", quiet=vctx.quiet)
    output_result(
        _nic_to_dict(nic_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def nic_update(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    nic: Annotated[str, typer.Argument(help="NIC name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name")] = None,
    network: Annotated[str | None, typer.Option("--network", "-N", help="New network")] = None,
    enabled: Annotated[bool | None, typer.Option("--enabled/--disabled")] = None,
) -> None:
    """Update a VM network interface."""
    vctx, vm_obj = _get_vm(ctx, vm)
    nic_key = _resolve_nic(vm_obj, nic)

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if network is not None:
        updates["network"] = network
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    nic_obj = vm_obj.nics.update(nic_key, **updates)
    output_success(f"Updated NIC '{nic_obj.name}'", quiet=vctx.quiet)
    output_result(
        _nic_to_dict(nic_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def nic_delete(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    nic: Annotated[str, typer.Argument(help="NIC name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a network interface from a VM."""
    vctx, vm_obj = _get_vm(ctx, vm)
    nic_key = _resolve_nic(vm_obj, nic)

    if not confirm_action(f"Delete NIC '{nic}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vm_obj.nics.delete(nic_key)
    output_success(f"Deleted NIC '{nic}'", quiet=vctx.quiet)
```

**Step 4: Register in vm.py**

Add import and registration alongside vm_drive:
```python
from verge_cli.commands import vm_drive, vm_nic
app.add_typer(vm_nic.app, name="nic")
```

**Step 5: Run tests**

Run: `uv run pytest tests/unit/test_vm_nic.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/verge_cli/commands/vm_nic.py tests/unit/test_vm_nic.py src/verge_cli/commands/vm.py
git commit -m "feat: add vrg vm nic sub-resource commands"
```

---

### Task 4: Create vm_device.py (TPM only)

**Files:**
- Create: `src/verge_cli/commands/vm_device.py`
- Create: `tests/unit/test_vm_device.py`

**Context — SDK for TPM:**
```python
# Generic create (supports settings dict for model/version):
vm.devices.create(device_type="tpm", settings={"model": "crb", "version": "2"})

# Convenience method (no model/version support):
vm.devices.create_tpm(name=None, enabled=True, optional=False)
```

We use the generic `create()` with `settings` to support `--model` and `--version`.

**Step 1: Write failing tests**

```python
# tests/unit/test_vm_device.py
"""Tests for VM device sub-resource commands (TPM only)."""

from verge_cli.cli import app


def test_device_list(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device list should list devices on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]

    result = cli_runner.invoke(app, ["vm", "device", "list", "test-vm"])

    assert result.exit_code == 0
    assert "TPM" in result.output


def test_device_get(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device get should show device details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]
    mock_vm.devices.get.return_value = mock_device

    result = cli_runner.invoke(app, ["vm", "device", "get", "test-vm", "TPM"])

    assert result.exit_code == 0
    assert "TPM" in result.output


def test_device_create_tpm(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device create should add a TPM device."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.create.return_value = mock_device

    result = cli_runner.invoke(
        app,
        ["vm", "device", "create", "test-vm", "--model", "crb", "--version", "2.0"],
    )

    assert result.exit_code == 0
    mock_vm.devices.create.assert_called_once()
    call_kwargs = mock_vm.devices.create.call_args[1]
    assert call_kwargs["device_type"] == "tpm"
    assert call_kwargs["settings"]["model"] == "crb"
    assert call_kwargs["settings"]["version"] == "2.0"


def test_device_create_tpm_defaults(cli_runner, mock_client, mock_vm, mock_device):
    """TPM defaults to model=crb, version=2.0."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.create.return_value = mock_device

    result = cli_runner.invoke(app, ["vm", "device", "create", "test-vm"])

    assert result.exit_code == 0
    call_kwargs = mock_vm.devices.create.call_args[1]
    assert call_kwargs["settings"]["model"] == "crb"
    assert call_kwargs["settings"]["version"] == "2.0"


def test_device_delete(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device delete should remove a device."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]

    result = cli_runner.invoke(
        app, ["vm", "device", "delete", "test-vm", "TPM", "--yes"]
    )

    assert result.exit_code == 0
    mock_vm.devices.delete.assert_called_once_with(30)
```

**Step 2: Implement vm_device.py**

```python
# src/verge_cli/commands/vm_device.py
"""VM device sub-resource commands (TPM only)."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="device",
    help="Manage VM devices (TPM).",
    no_args_is_help=True,
)

DEVICE_LIST_COLUMNS = ["name", "device_type", "enabled", "optional"]


def _get_vm(ctx: typer.Context, vm_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and VM object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm_identifier, "VM")
    vm_obj = vctx.client.vms.get(key)
    return vctx, vm_obj


def _device_to_dict(device: Any) -> dict[str, Any]:
    """Convert a Device object to a dict for output."""
    settings = device.get("settings_args", {})
    return {
        "key": device.key,
        "name": device.name,
        "device_type": device.device_type,
        "enabled": device.is_enabled,
        "optional": device.is_optional,
        "model": settings.get("model", ""),
        "version": settings.get("version", ""),
    }


def _resolve_device(vm_obj: Any, identifier: str) -> int:
    """Resolve a device name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    devices = vm_obj.devices.list()
    matches = [d for d in devices if d.name == identifier]
    if len(matches) == 1:
        return matches[0].key
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
        columns=DEVICE_LIST_COLUMNS,
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
    version: Annotated[str, typer.Option("--version", "-V", help="TPM version (1.2, 2.0)")] = "2.0",
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
```

**Step 3: Register in vm.py**

```python
from verge_cli.commands import vm_drive, vm_nic, vm_device
app.add_typer(vm_device.app, name="device")
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_vm_device.py -v`
Expected: All PASS

**Step 5: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 6: Lint**

Run: `uv run ruff check src/verge_cli/commands/vm_drive.py src/verge_cli/commands/vm_nic.py src/verge_cli/commands/vm_device.py`
Expected: Clean

**Step 7: Commit**

```bash
git add src/verge_cli/commands/vm_device.py tests/unit/test_vm_device.py src/verge_cli/commands/vm.py
git commit -m "feat: add vrg vm device sub-resource commands (TPM)"
```

---

## Milestone 2 Complete

After M2 you should have:
- `vrg vm drive list|get|create|update|delete|import <vm>` — working
- `vrg vm nic list|get|create|update|delete <vm>` — working
- `vrg vm device list|get|create|delete <vm>` — working (TPM only)
- All registered as sub-Typer apps on `vm.app`
- Mock fixtures for drives, NICs, devices in conftest
- Full test coverage for all commands
