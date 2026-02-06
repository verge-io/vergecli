# Milestone 4: Template Create & Dry-Run

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the orchestrator that provisions VMs from templates, add `-f`/`--set`/`--dry-run` flags to `vrg vm create`, and support `VirtualMachineSet` batch creation.

**Architecture:** `template/builder.py` is the translation layer from validated template dict → pyvergeos SDK method calls. It handles single VMs and batches. The existing `vm create` command gains a template-mode branch when `-f` is provided.

**Tech Stack:** Python 3.10+, pyvergeos SDK, Typer, Rich, pytest

**Depends on:** M1 (units, resolver), M3 (loader, schema)

---

### Task 1: Create template/builder.py

**Files:**
- Create: `src/verge_cli/template/builder.py`
- Create: `tests/unit/test_template_builder.py`

**Context — SDK method signatures used:**
```python
client.vms.create(name, ram=1024, cpu_cores=1, description="",
                   os_family="linux", machine_type="pc-q35-10.0",
                   cloudinit_datasource=None, cloud_init=None, **kwargs) -> VM

vm.drives.create(size_gb=None, name=None, interface="virtio-scsi",
                  media="disk", tier=None, description="",
                  media_source=None) -> Drive

vm.nics.create(network=None, name=None, interface="virtio",
               mac_address=None, ip_address=None, description="") -> NIC

vm.devices.create(device_type="tpm", settings={"model": "crb", "version": "2"}) -> Device
```

**Step 1: Write failing tests**

```python
# tests/unit/test_template_builder.py
"""Tests for template builder (VM provisioning orchestrator)."""

from unittest.mock import MagicMock, call

import pytest

from verge_cli.template.builder import (
    ProvisionError,
    ProvisionResult,
    build_dry_run,
    provision_vm,
)


@pytest.fixture
def mock_ctx():
    """Create a mock context with a pyvergeos client."""
    ctx = MagicMock()
    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "test-vm"
    mock_vm.machine_key = 38
    ctx.client.vms.create.return_value = mock_vm

    mock_drive = MagicMock()
    mock_drive.key = 10
    mock_drive.name = "OS Disk"
    mock_vm.drives.create.return_value = mock_drive

    mock_nic = MagicMock()
    mock_nic.key = 20
    mock_nic.name = "eth0"
    mock_vm.nics.create.return_value = mock_nic

    mock_device = MagicMock()
    mock_device.key = 30
    mock_device.name = "TPM"
    mock_vm.devices.create.return_value = mock_device

    return ctx


class TestProvisionVm:
    """Tests for single VM provisioning."""

    def test_minimal_vm(self, mock_ctx):
        config = {"name": "test-vm", "os_family": "linux"}
        result = provision_vm(mock_ctx.client, config)

        assert isinstance(result, ProvisionResult)
        assert result.vm_key == 1
        assert result.vm_name == "test-vm"
        mock_ctx.client.vms.create.assert_called_once()

    def test_vm_with_ram_and_cpu(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "ram": 4096,
            "cpu_cores": 4,
        }
        result = provision_vm(mock_ctx.client, config)

        call_kwargs = mock_ctx.client.vms.create.call_args[1]
        assert call_kwargs["ram"] == 4096
        assert call_kwargs["cpu_cores"] == 4

    def test_vm_with_drives(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "drives": [
                {"name": "OS Disk", "size": 50, "interface": "virtio-scsi", "media": "disk", "preferred_tier": 3},
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.drives.create.assert_called_once()
        assert result.drives_created == 1

    def test_vm_with_nics(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "nics": [
                {"name": "eth0", "network": 3, "interface": "virtio"},
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.nics.create.assert_called_once()
        assert result.nics_created == 1

    def test_vm_with_tpm(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "devices": [
                {"type": "tpm", "model": "crb", "version": "2.0"},
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.devices.create.assert_called_once()
        call_kwargs = vm.devices.create.call_args[1]
        assert call_kwargs["device_type"] == "tpm"
        assert call_kwargs["settings"]["model"] == "crb"
        assert result.devices_created == 1

    def test_vm_with_cloudinit(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "cloudinit": {
                "datasource": "nocloud",
                "files": [
                    {"name": "user-data", "content": "#cloud-config\nhostname: test"},
                ],
            },
        }
        result = provision_vm(mock_ctx.client, config)

        call_kwargs = mock_ctx.client.vms.create.call_args[1]
        assert call_kwargs["cloudinit_datasource"] == "NoCloud"

    def test_drive_failure_partial_provision(self, mock_ctx):
        vm = mock_ctx.client.vms.create.return_value
        vm.drives.create.side_effect = Exception("API error")

        config = {
            "name": "test-vm",
            "os_family": "linux",
            "drives": [{"name": "OS", "size": 50, "media": "disk"}],
        }

        with pytest.raises(ProvisionError) as exc_info:
            provision_vm(mock_ctx.client, config)

        assert exc_info.value.result.vm_key == 1
        assert len(exc_info.value.result.errors) > 0


class TestBuildDryRun:
    """Tests for dry-run output."""

    def test_dry_run_single_vm(self):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "ram": 4096,
            "cpu_cores": 2,
            "drives": [{"name": "OS Disk", "size": 50, "media": "disk"}],
            "nics": [{"name": "eth0", "network": "DMZ Internal", "interface": "virtio"}],
        }
        output = build_dry_run(config)

        assert "test-vm" in output
        assert "OS Disk" in output
        assert "DMZ Internal" in output
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_builder.py -v`
Expected: FAIL

**Step 3: Implement builder.py**

```python
# src/verge_cli/template/builder.py
"""Template builder — orchestrates VM provisioning via pyvergeos SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Mapping from template cloudinit datasource names to SDK values
_CLOUDINIT_DATASOURCE_MAP = {
    "nocloud": "NoCloud",
    "config_drive_v2": "ConfigDrive",
}

# VM fields that map directly to client.vms.create() kwargs
_VM_CREATE_FIELDS = {
    "name", "ram", "cpu_cores", "description", "os_family",
    "machine_type", "boot_order", "allow_hotplug", "uefi",
    "secure_boot", "console", "video", "guest_agent", "rtc_base",
    "cluster", "failover_cluster", "preferred_node", "ha_group",
    "snapshot_profile", "cpu_type", "enabled",
}


@dataclass
class ProvisionResult:
    """Result of provisioning a single VM."""

    vm_key: int
    vm_name: str
    drives_created: int = 0
    nics_created: int = 0
    devices_created: int = 0
    powered_on: bool = False
    errors: list[str] = field(default_factory=list)


class ProvisionError(Exception):
    """Provisioning failed (VM may be partially created)."""

    def __init__(self, message: str, result: ProvisionResult) -> None:
        self.result = result
        super().__init__(message)


def provision_vm(client: Any, vm_config: dict[str, Any]) -> ProvisionResult:
    """Provision a single VM from a validated, unit-converted config dict.

    Orchestration:
    1. Create VM via client.vms.create()
    2. Create drives via vm.drives.create()
    3. Create NICs via vm.nics.create()
    4. Create devices via vm.devices.create()
    5. Power on if requested

    Args:
        client: pyvergeos VergeClient.
        vm_config: Validated VM configuration dict (units already converted).

    Returns:
        ProvisionResult with creation details.

    Raises:
        ProvisionError: If any sub-resource creation fails (VM still exists).
    """
    # 1. Build VM create kwargs
    vm_kwargs: dict[str, Any] = {}
    for key in _VM_CREATE_FIELDS:
        if key in vm_config:
            vm_kwargs[key] = vm_config[key]

    # Handle machine_type — template uses 'q35', SDK expects 'pc-q35-10.0'
    if "machine_type" in vm_kwargs:
        mt = vm_kwargs["machine_type"]
        if mt == "q35":
            vm_kwargs["machine_type"] = "pc-q35-10.0"

    # Handle cloud-init
    cloudinit = vm_config.get("cloudinit")
    if cloudinit:
        ds = cloudinit.get("datasource", "")
        vm_kwargs["cloudinit_datasource"] = _CLOUDINIT_DATASOURCE_MAP.get(ds, ds)
        files = cloudinit.get("files")
        if files:
            cloud_init_data = {f["name"]: f["content"] for f in files}
            vm_kwargs["cloud_init"] = cloud_init_data

    # Handle advanced_options as kwargs pass-through
    if "advanced_options" in vm_config:
        vm_kwargs["advanced_options"] = vm_config["advanced_options"]

    # 2. Create VM
    vm = client.vms.create(**vm_kwargs)
    result = ProvisionResult(vm_key=vm.key, vm_name=vm.name)

    # 3. Create drives
    for drive_config in vm_config.get("drives", []):
        try:
            drive_kwargs = _build_drive_kwargs(drive_config)
            vm.drives.create(**drive_kwargs)
            result.drives_created += 1
        except Exception as e:
            result.errors.append(f"Drive '{drive_config.get('name', '?')}': {e}")

    # 4. Create NICs
    for nic_config in vm_config.get("nics", []):
        try:
            nic_kwargs = _build_nic_kwargs(nic_config)
            vm.nics.create(**nic_kwargs)
            result.nics_created += 1
        except Exception as e:
            result.errors.append(f"NIC '{nic_config.get('name', '?')}': {e}")

    # 5. Create devices (TPM only for now)
    for device_config in vm_config.get("devices", []):
        try:
            device_kwargs = _build_device_kwargs(device_config)
            vm.devices.create(**device_kwargs)
            result.devices_created += 1
        except Exception as e:
            result.errors.append(f"Device '{device_config.get('name', '?')}': {e}")

    # 6. Power on if requested
    if vm_config.get("power_on_after_create", False):
        try:
            vm.power_on()
            result.powered_on = True
        except Exception as e:
            result.errors.append(f"Power on: {e}")

    # If there were errors, raise with the partial result
    if result.errors:
        msg = f"VM '{result.vm_name}' created (key: {result.vm_key}) but with errors:\n"
        msg += "\n".join(f"  - {e}" for e in result.errors)
        raise ProvisionError(msg, result)

    return result


def _build_drive_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate drive template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {}
    if "name" in config:
        kwargs["name"] = config["name"]
    if "size" in config:
        kwargs["size_gb"] = config["size"]  # Already converted to GB by convert_units
    if "interface" in config:
        kwargs["interface"] = config["interface"]
    if "media" in config:
        kwargs["media"] = config["media"]
    if "preferred_tier" in config:
        kwargs["tier"] = config["preferred_tier"]
    if "description" in config:
        kwargs["description"] = config["description"]
    if "media_source" in config:
        kwargs["media_source"] = config["media_source"]
    if "enabled" in config:
        kwargs["enabled"] = config["enabled"]
    return kwargs


def _build_nic_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate NIC template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {}
    if "network" in config:
        kwargs["network"] = config["network"]
    if "name" in config:
        kwargs["name"] = config["name"]
    if "interface" in config:
        kwargs["interface"] = config["interface"]
    if "mac" in config:
        kwargs["mac_address"] = config["mac"]
    if "description" in config:
        kwargs["description"] = config["description"]
    if "enabled" in config:
        kwargs["enabled"] = config["enabled"]
    return kwargs


def _build_device_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate device template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {
        "device_type": config.get("type", "tpm"),
    }
    settings: dict[str, str] = {}
    if "model" in config:
        settings["model"] = config["model"]
    if "version" in config:
        settings["version"] = config["version"]
    if settings:
        kwargs["settings"] = settings
    if "name" in config:
        kwargs["name"] = config["name"]
    return kwargs


def build_dry_run(vm_config: dict[str, Any]) -> str:
    """Build a human-readable dry-run summary for a VM config.

    Args:
        vm_config: Validated VM configuration dict.

    Returns:
        Multi-line string describing what would be created.
    """
    lines: list[str] = []
    name = vm_config.get("name", "unnamed")
    os_fam = vm_config.get("os_family", "?")
    cores = vm_config.get("cpu_cores", 1)
    ram = vm_config.get("ram", "1GB")
    mt = vm_config.get("machine_type", "q35")

    lines.append(f"VM: {name} ({os_fam}, {cores} cores, {ram} RAM, {mt})")

    api_calls = 1  # VM create

    for i, drive in enumerate(vm_config.get("drives", []), 1):
        d_name = drive.get("name", f"Drive {i}")
        d_media = drive.get("media", "disk")
        d_iface = drive.get("interface", "virtio-scsi")
        d_size = drive.get("size", "")
        d_tier = drive.get("preferred_tier", "")
        d_src = drive.get("media_source", "")
        parts = [d_media, d_iface]
        if d_size:
            parts.append(f"{d_size}GB")
        if d_tier:
            parts.append(f"tier {d_tier}")
        if d_src:
            parts.append(f"media: {d_src}")
        lines.append(f"  Drive {i}: \"{d_name}\" — {', '.join(parts)}")
        api_calls += 1

    for i, nic in enumerate(vm_config.get("nics", []), 1):
        n_name = nic.get("name", f"NIC {i}")
        n_iface = nic.get("interface", "virtio")
        n_net = nic.get("network", "?")
        lines.append(f"  NIC {i}: \"{n_name}\" — {n_iface}, network: {n_net}")
        api_calls += 1

    for i, dev in enumerate(vm_config.get("devices", []), 1):
        d_name = dev.get("name", f"Device {i}")
        d_type = dev.get("type", "?")
        d_model = dev.get("model", "")
        d_ver = dev.get("version", "")
        lines.append(f"  Device {i}: \"{d_name}\" — {d_type} ({d_model} v{d_ver})")
        api_calls += 1

    cloudinit = vm_config.get("cloudinit")
    if cloudinit:
        ds = cloudinit.get("datasource", "?")
        files = cloudinit.get("files", [])
        file_names = ", ".join(f["name"] for f in files)
        lines.append(f"  Cloud-init: {ds} ({len(files)} files: {file_names})")

    power = vm_config.get("power_on_after_create", False)
    lines.append(f"  Power on after create: {'yes' if power else 'no'}")
    if power:
        api_calls += 1

    lines.append(f"\n{api_calls} API calls would be made.")
    return "\n".join(lines)
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_template_builder.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/verge_cli/template/builder.py tests/unit/test_template_builder.py
git commit -m "feat: add template builder for VM provisioning orchestration"
```

---

### Task 2: Add `-f`, `--set`, `--dry-run` to `vrg vm create`

**Files:**
- Modify: `src/verge_cli/commands/vm.py`
- Create: `tests/unit/test_vm_create_template.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_vm_create_template.py
"""Tests for vrg vm create -f (template mode)."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_create_from_template(cli_runner, mock_client, tmp_path):
    """vrg vm create -f should create VM from template."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: template-vm\n"
        "  os_family: linux\n"
        "  ram: 4GB\n"
        "  cpu_cores: 2\n"
    )

    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "template-vm"
    mock_vm.machine_key = 38
    mock_vm.drives = MagicMock()
    mock_vm.nics = MagicMock()
    mock_vm.devices = MagicMock()
    mock_client.vms.create.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template)])

    assert result.exit_code == 0
    mock_client.vms.create.assert_called_once()
    call_kwargs = mock_client.vms.create.call_args[1]
    assert call_kwargs["name"] == "template-vm"
    assert call_kwargs["ram"] == 4096


def test_create_dry_run(cli_runner, tmp_path):
    """vrg vm create -f --dry-run should print plan without creating."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: dry-run-vm\n"
        "  os_family: linux\n"
        "  drives:\n"
        "    - name: OS Disk\n"
        "      size: 50GB\n"
        "      media: disk\n"
    )

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template), "--dry-run"])

    assert result.exit_code == 0
    assert "dry-run-vm" in result.output
    assert "OS Disk" in result.output
    assert "Dry run" in result.output


def test_create_with_set_override(cli_runner, mock_client, tmp_path):
    """vrg vm create -f --set should apply overrides."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: original-name\n"
        "  os_family: linux\n"
    )

    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "overridden-name"
    mock_vm.machine_key = 38
    mock_vm.drives = MagicMock()
    mock_vm.nics = MagicMock()
    mock_vm.devices = MagicMock()
    mock_client.vms.create.return_value = mock_vm

    result = cli_runner.invoke(
        app, ["vm", "create", "-f", str(template), "--set", "vm.name=overridden-name"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.vms.create.call_args[1]
    assert call_kwargs["name"] == "overridden-name"


def test_create_vm_set(cli_runner, mock_client, tmp_path):
    """vrg vm create -f with VirtualMachineSet should create multiple VMs."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachineSet\n"
        "defaults:\n"
        "  os_family: linux\n"
        "  ram: 4GB\n"
        "vms:\n"
        "  - name: vm-01\n"
        "    os_family: linux\n"
        "  - name: vm-02\n"
        "    os_family: linux\n"
    )

    mock_vm1 = MagicMock()
    mock_vm1.key = 1
    mock_vm1.name = "vm-01"
    mock_vm1.machine_key = 38
    mock_vm1.drives = MagicMock()
    mock_vm1.nics = MagicMock()
    mock_vm1.devices = MagicMock()

    mock_vm2 = MagicMock()
    mock_vm2.key = 2
    mock_vm2.name = "vm-02"
    mock_vm2.machine_key = 39
    mock_vm2.drives = MagicMock()
    mock_vm2.nics = MagicMock()
    mock_vm2.devices = MagicMock()

    mock_client.vms.create.side_effect = [mock_vm1, mock_vm2]

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template)])

    assert result.exit_code == 0
    assert mock_client.vms.create.call_count == 2
```

**Step 2: Modify `vm_create` in vm.py**

Add new optional parameters and a template-mode branch. The key change is adding `-f`, `--set`, and `--dry-run` options, then branching based on whether `-f` is provided:

```python
@app.command("create")
@handle_errors()
def vm_create(
    ctx: typer.Context,
    name: Annotated[str | None, typer.Option("--name", "-n", help="VM name")] = None,
    ram: Annotated[int, typer.Option("--ram", "-r", help="RAM in MB")] = 1024,
    cpu: Annotated[int, typer.Option("--cpu", "-c", help="Number of CPU cores")] = 1,
    description: Annotated[str, typer.Option("--description", "-d", help="VM description")] = "",
    os_family: Annotated[str, typer.Option("--os", help="OS family")] = "linux",
    file: Annotated[str | None, typer.Option("--file", "-f", help="Template file (.vrg.yaml)")] = None,
    set_overrides: Annotated[list[str] | None, typer.Option("--set", help="Override template values")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show plan without creating")] = False,
) -> None:
    """Create a new virtual machine (inline or from template)."""
    if file:
        _create_from_template(ctx, file, set_overrides or [], dry_run)
    else:
        if not name:
            typer.echo("Error: --name is required for inline creation.", err=True)
            raise typer.Exit(2)
        _create_inline(ctx, name, ram, cpu, description, os_family)


def _create_inline(ctx, name, ram, cpu, description, os_family):
    """Original inline VM creation."""
    vctx = get_context(ctx)
    vm_obj = vctx.client.vms.create(
        name=name, ram=ram, cpu_cores=cpu,
        description=description, os_family=os_family,
    )
    output_success(f"Created VM '{vm_obj.name}' (key: {vm_obj.key})", quiet=vctx.quiet)
    output_result(
        _vm_to_dict(vm_obj),
        output_format=vctx.output_format, query=vctx.query,
        quiet=vctx.quiet, no_color=vctx.no_color,
    )


def _create_from_template(ctx, file_path, set_overrides, dry_run):
    """Template-based VM creation."""
    from verge_cli.template.builder import ProvisionError, build_dry_run, provision_vm
    from verge_cli.template.loader import load_template
    from verge_cli.template.schema import (
        ValidationError,
        convert_units,
        merge_vm_set_defaults,
        validate_template,
    )

    # Load and validate
    try:
        data = load_template(file_path, set_overrides=set_overrides)
        validate_template(data)
    except (ValueError, ValidationError) as e:
        typer.echo(f"Template error: {e}", err=True)
        raise typer.Exit(8)

    # Collect VM configs
    if data["kind"] == "VirtualMachineSet":
        defaults = data.get("defaults", {})
        vm_configs = merge_vm_set_defaults(defaults, data["vms"])
    else:
        vm_configs = [data["vm"]]

    # Convert units for all configs
    for vm_config in vm_configs:
        convert_units(vm_config)

    # Dry run
    if dry_run:
        typer.echo("Dry run — no resources will be created.\n")
        for vm_config in vm_configs:
            typer.echo(build_dry_run(vm_config))
            typer.echo("")
        return

    # Provision
    vctx = get_context(ctx)
    results = []
    had_errors = False

    for vm_config in vm_configs:
        try:
            result = provision_vm(vctx.client, vm_config)
            results.append(result)
            output_success(
                f"Created VM '{result.vm_name}' (key: {result.vm_key}) — "
                f"{result.drives_created} drives, {result.nics_created} NICs, "
                f"{result.devices_created} devices",
                quiet=vctx.quiet,
            )
        except ProvisionError as e:
            results.append(e.result)
            had_errors = True
            typer.echo(f"Warning: {e}", err=True)

    if had_errors:
        raise typer.Exit(1)
```

**Step 3: Run tests**

Run: `uv run pytest tests/unit/test_vm_create_template.py -v`
Expected: All PASS

**Step 4: Run full suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS (no regressions)

**Step 5: Commit**

```bash
git add src/verge_cli/commands/vm.py tests/unit/test_vm_create_template.py
git commit -m "feat: add template-based VM creation with -f, --set, --dry-run"
```

---

## Milestone 4 Complete

After M4 you should have:
- `src/verge_cli/template/builder.py` — VM provisioning orchestrator
- `vrg vm create -f template.vrg.yaml` — creates VMs from template
- `vrg vm create -f template.vrg.yaml --dry-run` — prints plan
- `vrg vm create -f template.vrg.yaml --set vm.name=x` — with overrides
- `VirtualMachineSet` support — batch creation from templates
- Partial failure handling — reports what succeeded
- Full test coverage
