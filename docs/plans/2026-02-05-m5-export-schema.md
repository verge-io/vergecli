# Milestone 5: Export & JSON Schema Packaging

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `vrg vm export` command to reverse-engineer VMs into portable `.vrg.yaml` templates, and package the JSON schema for distribution.

**Architecture:** `template/exporter.py` iterates pyvergeos resource objects (VM, drives, NICs, devices) and maps them back to template YAML. The export command outputs to stdout or file.

**Tech Stack:** Python 3.10+, pyvergeos SDK, PyYAML, pytest

**Depends on:** M1 (units for format_ram/format_disk_size), M3 (schema structure knowledge)

---

### Task 1: Create template/exporter.py

**Files:**
- Create: `src/verge_cli/template/exporter.py`
- Create: `tests/unit/test_template_exporter.py`

**Context — SDK object attributes used for export:**
```python
# VM object
vm.key, vm.name, vm.status, vm.machine_key
vm.get("description"), vm.get("os_family"), vm.get("cpu_cores"), vm.get("ram")
vm.get("machine_type"), vm.get("boot_order"), vm.get("uefi"), vm.get("secure_boot")
vm.get("console"), vm.get("video"), vm.get("guest_agent"), vm.get("rtc_base")
vm.get("allow_hotplug"), vm.get("ha_group"), vm.get("advanced_options")
vm.cluster_name, vm.node_name

# Drive object
drive.key, drive.name, drive.size_gb, drive.is_enabled, drive.is_readonly
drive.get("interface"), drive.get("media"), drive.get("preferred_tier")
drive.get("description"), drive.get("media_source")

# NIC object
nic.key, nic.name, nic.network_name, nic.network_key, nic.is_enabled
nic.get("interface"), nic.get("description"), nic.mac_address

# Device object
device.key, device.name, device.device_type_raw, device.is_enabled
device.get("settings_args")
```

**Step 1: Write failing tests**

```python
# tests/unit/test_template_exporter.py
"""Tests for template exporter (VM → .vrg.yaml)."""

from unittest.mock import MagicMock

import yaml

from verge_cli.template.exporter import export_vm


def _make_vm(
    name="test-vm",
    ram=4096,
    cpu_cores=2,
    os_family="linux",
    machine_type="pc-q35-10.0",
    drives=None,
    nics=None,
    devices=None,
):
    """Create a mock VM with sub-resources."""
    vm = MagicMock()
    vm.key = 42
    vm.name = name
    vm.machine_key = 38
    vm.cluster_name = "Cluster1"
    vm.node_name = "Node1"

    data = {
        "description": "Test VM",
        "os_family": os_family,
        "cpu_cores": cpu_cores,
        "ram": ram,
        "machine_type": machine_type,
        "boot_order": "cd",
        "uefi": True,
        "secure_boot": False,
        "console": "vnc",
        "video": "virtio",
        "guest_agent": True,
        "rtc_base": "utc",
        "allow_hotplug": True,
        "ha_group": None,
        "advanced_options": None,
    }

    def mock_get(key, default=None):
        return data.get(key, default)

    vm.get = mock_get
    vm.drives.list.return_value = drives or []
    vm.nics.list.return_value = nics or []
    vm.devices.list.return_value = devices or []

    return vm


def _make_drive(name="OS Disk", size_gb=50, interface="virtio-scsi", media="disk", tier=3):
    drive = MagicMock()
    drive.key = 10
    drive.name = name
    drive.size_gb = size_gb
    drive.is_enabled = True
    drive.is_readonly = False

    data = {
        "interface": interface,
        "media": media,
        "preferred_tier": tier,
        "description": "",
        "media_source": None,
    }
    drive.get = lambda k, d=None: data.get(k, d)
    return drive


def _make_nic(name="Primary", network_name="DMZ Internal", network_key=3, interface="virtio"):
    nic = MagicMock()
    nic.key = 20
    nic.name = name
    nic.network_name = network_name
    nic.network_key = network_key
    nic.is_enabled = True
    nic.mac_address = "52:54:00:12:34:56"

    data = {"interface": interface, "description": ""}
    nic.get = lambda k, d=None: data.get(k, d)
    return nic


def _make_device_tpm():
    device = MagicMock()
    device.key = 30
    device.name = "TPM"
    device.device_type_raw = "tpm"
    device.is_enabled = True

    data = {"settings_args": {"model": "crb", "version": "2"}}
    device.get = lambda k, d=None: data.get(k, d)
    return device


class TestExportVm:
    """Tests for VM export."""

    def test_minimal_export(self):
        vm = _make_vm()
        result = export_vm(vm)

        assert "apiVersion: v4" in result
        assert "kind: VirtualMachine" in result
        assert "name: test-vm" in result
        assert "os_family: linux" in result

    def test_export_parses_as_valid_yaml(self):
        vm = _make_vm()
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert data["apiVersion"] == "v4"
        assert data["kind"] == "VirtualMachine"
        assert data["vm"]["name"] == "test-vm"

    def test_export_ram_human_friendly(self):
        vm = _make_vm(ram=4096)
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert data["vm"]["ram"] == "4GB"

    def test_export_machine_type_short(self):
        vm = _make_vm(machine_type="pc-q35-10.0")
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert data["vm"]["machine_type"] == "q35"

    def test_export_with_drives(self):
        drive = _make_drive()
        vm = _make_vm(drives=[drive])
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert len(data["vm"]["drives"]) == 1
        assert data["vm"]["drives"][0]["name"] == "OS Disk"
        assert data["vm"]["drives"][0]["size"] == "50GB"

    def test_export_with_nics(self):
        nic = _make_nic()
        vm = _make_vm(nics=[nic])
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert len(data["vm"]["nics"]) == 1
        assert data["vm"]["nics"][0]["network"] == "DMZ Internal"
        # MAC should be omitted (auto-generated on re-create)
        assert "mac" not in data["vm"]["nics"][0]

    def test_export_with_tpm(self):
        device = _make_device_tpm()
        vm = _make_vm(devices=[device])
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert len(data["vm"]["devices"]) == 1
        assert data["vm"]["devices"][0]["type"] == "tpm"
        assert data["vm"]["devices"][0]["model"] == "crb"

    def test_export_includes_header_comment(self):
        vm = _make_vm()
        result = export_vm(vm)

        assert "# Exported from VM:" in result
        assert "static snapshot" in result.lower()

    def test_export_nic_falls_back_to_key(self):
        nic = _make_nic(network_name=None, network_key=7)
        vm = _make_vm(nics=[nic])
        result = export_vm(vm)
        data = yaml.safe_load(result)

        assert data["vm"]["nics"][0]["network"] == 7
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_exporter.py -v`
Expected: FAIL

**Step 3: Implement exporter.py**

```python
# src/verge_cli/template/exporter.py
"""Export a VM to a .vrg.yaml template."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yaml

from verge_cli.template.units import format_disk_size, format_ram

# Machine type mapping (SDK → template shorthand)
_MACHINE_TYPE_MAP = {
    "pc-q35-10.0": "q35",
    "pc-i440fx-10.0": "pc",
}

# VM fields to export (template field name → vm.get() key)
_VM_EXPORT_FIELDS = [
    ("description", "description"),
    ("os_family", "os_family"),
    ("os_description", "os_description"),
    ("cpu_cores", "cpu_cores"),
    ("cpu_type", "cpu_type"),
    ("boot_order", "boot_order"),
    ("allow_hotplug", "allow_hotplug"),
    ("uefi", "uefi"),
    ("secure_boot", "secure_boot"),
    ("console", "console"),
    ("video", "video"),
    ("guest_agent", "guest_agent"),
    ("rtc_base", "rtc_base"),
    ("ha_group", "ha_group"),
    ("advanced_options", "advanced_options"),
]

# Default values to skip when exporting (don't clutter the template)
_DEFAULTS = {
    "description": "",
    "os_description": "",
    "cpu_type": "auto",
    "boot_order": "cd",
    "allow_hotplug": True,
    "uefi": False,
    "secure_boot": False,
    "console": "vnc",
    "video": "std",
    "guest_agent": False,
    "rtc_base": "utc",
}


def export_vm(vm: Any) -> str:
    """Export a VM to a .vrg.yaml template string.

    Args:
        vm: pyvergeos VM object with drives, nics, devices sub-resources.

    Returns:
        YAML string with header comment.
    """
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build VM config
    vm_config: dict[str, Any] = {}

    vm_config["name"] = vm.name

    # Map fields, skipping defaults and None
    for template_key, sdk_key in _VM_EXPORT_FIELDS:
        value = vm.get(sdk_key)
        if value is None:
            continue
        # Skip if it matches the default
        if template_key in _DEFAULTS and value == _DEFAULTS[template_key]:
            continue
        vm_config[template_key] = value

    # OS family (always include)
    os_family = vm.get("os_family")
    if os_family:
        vm_config["os_family"] = os_family

    # RAM — convert to human-friendly
    ram = vm.get("ram")
    if ram is not None:
        vm_config["ram"] = format_ram(ram)

    # Machine type — convert to shorthand
    machine_type = vm.get("machine_type", "")
    short_mt = _MACHINE_TYPE_MAP.get(machine_type, machine_type)
    if short_mt and short_mt != "q35":  # q35 is default, skip
        vm_config["machine_type"] = short_mt
    elif short_mt == "q35":
        vm_config["machine_type"] = "q35"

    # Cluster name
    if vm.cluster_name:
        vm_config["cluster"] = vm.cluster_name

    # Drives
    drives = vm.drives.list()
    if drives:
        vm_config["drives"] = [_export_drive(d) for d in drives]

    # NICs
    nics = vm.nics.list()
    if nics:
        vm_config["nics"] = [_export_nic(n) for n in nics]

    # Devices
    devices = vm.devices.list()
    if devices:
        exported_devices = [_export_device(d) for d in devices]
        exported_devices = [d for d in exported_devices if d is not None]
        if exported_devices:
            vm_config["devices"] = exported_devices

    # Build full template
    template = {
        "apiVersion": "v4",
        "kind": "VirtualMachine",
        "vm": vm_config,
    }

    # Serialize to YAML
    yaml_str = yaml.dump(template, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Add header comment
    header = (
        f"# Exported from VM: {vm.name} (key: {vm.key})\n"
        f"# Date: {now}\n"
        f"# Note: This is a static snapshot. Variables have been resolved.\n"
        f"# Cloud-init contents are not available after VM creation.\n"
    )

    return header + yaml_str


def _export_drive(drive: Any) -> dict[str, Any]:
    """Export a single drive to template dict."""
    result: dict[str, Any] = {}

    if drive.name:
        result["name"] = drive.name

    media = drive.get("media", "disk")
    if media != "disk":
        result["media"] = media
    else:
        result["media"] = "disk"

    interface = drive.get("interface", "virtio-scsi")
    if interface != "virtio-scsi":
        result["interface"] = interface
    else:
        result["interface"] = "virtio-scsi"

    if media == "disk" and drive.size_gb:
        result["size"] = format_disk_size(int(drive.size_gb))

    tier = drive.get("preferred_tier")
    if tier is not None:
        result["preferred_tier"] = tier

    source = drive.get("media_source")
    if source is not None:
        result["media_source"] = source

    return result


def _export_nic(nic: Any) -> dict[str, Any]:
    """Export a single NIC to template dict."""
    result: dict[str, Any] = {}

    if nic.name:
        result["name"] = nic.name

    interface = nic.get("interface", "virtio")
    if interface != "virtio":
        result["interface"] = interface

    # Prefer network name, fall back to key
    if nic.network_name:
        result["network"] = nic.network_name
    elif nic.network_key:
        result["network"] = nic.network_key
    else:
        result["network"] = "unknown"

    # Omit MAC address — auto-generated on re-create

    return result


def _export_device(device: Any) -> dict[str, Any] | None:
    """Export a single device to template dict."""
    device_type = device.device_type_raw

    if device_type == "tpm":
        result: dict[str, Any] = {"type": "tpm"}
        if device.name:
            result["name"] = device.name
        settings = device.get("settings_args", {})
        if "model" in settings:
            result["model"] = settings["model"]
        if "version" in settings:
            result["version"] = settings["version"]
        return result

    # Skip unsupported device types
    return None
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_template_exporter.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/verge_cli/template/exporter.py tests/unit/test_template_exporter.py
git commit -m "feat: add template exporter for VM-to-YAML reverse engineering"
```

---

### Task 2: Add `vrg vm export` command

**Files:**
- Modify: `src/verge_cli/commands/vm.py`
- Create: `tests/unit/test_vm_export.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_vm_export.py
"""Tests for vrg vm export command."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def _make_exportable_vm(mock_client):
    """Create a VM mock suitable for export."""
    vm = MagicMock()
    vm.key = 42
    vm.name = "export-vm"
    vm.machine_key = 38
    vm.cluster_name = "Cluster1"
    vm.node_name = "Node1"

    data = {
        "description": "Exported VM",
        "os_family": "linux",
        "cpu_cores": 4,
        "ram": 8192,
        "machine_type": "pc-q35-10.0",
        "boot_order": "cd",
        "uefi": True,
        "secure_boot": False,
        "console": "vnc",
        "video": "virtio",
        "guest_agent": True,
        "rtc_base": "utc",
        "allow_hotplug": True,
        "ha_group": None,
        "advanced_options": None,
        "os_description": "",
        "cpu_type": "auto",
    }
    vm.get = lambda k, d=None: data.get(k, d)
    vm.drives.list.return_value = []
    vm.nics.list.return_value = []
    vm.devices.list.return_value = []

    mock_client.vms.list.return_value = [vm]
    mock_client.vms.get.return_value = vm
    return vm


def test_export_to_stdout(cli_runner, mock_client):
    """vrg vm export should print YAML to stdout."""
    _make_exportable_vm(mock_client)

    result = cli_runner.invoke(app, ["vm", "export", "export-vm"])

    assert result.exit_code == 0
    assert "apiVersion: v4" in result.output
    assert "name: export-vm" in result.output
    assert "os_family: linux" in result.output


def test_export_to_file(cli_runner, mock_client, tmp_path):
    """vrg vm export -o should write to file."""
    _make_exportable_vm(mock_client)

    output_file = tmp_path / "exported.vrg.yaml"
    result = cli_runner.invoke(
        app, ["vm", "export", "export-vm", "-o", str(output_file)]
    )

    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "apiVersion: v4" in content


def test_export_includes_header(cli_runner, mock_client):
    """Exported YAML should include hydration header."""
    _make_exportable_vm(mock_client)

    result = cli_runner.invoke(app, ["vm", "export", "export-vm"])

    assert "# Exported from VM:" in result.output
    assert "static snapshot" in result.output.lower()
```

**Step 2: Add export command to vm.py**

```python
@app.command("export")
@handle_errors()
def vm_export(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key to export")],
    output_file: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output file path (default: stdout)"),
    ] = None,
) -> None:
    """Export a VM as a .vrg.yaml template."""
    from verge_cli.template.exporter import export_vm

    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    yaml_str = export_vm(vm_obj)

    if output_file:
        from pathlib import Path
        Path(output_file).write_text(yaml_str)
        output_success(f"Exported VM '{vm_obj.name}' to {output_file}", quiet=vctx.quiet)
    else:
        typer.echo(yaml_str)
```

**Step 3: Run tests**

Run: `uv run pytest tests/unit/test_vm_export.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add src/verge_cli/commands/vm.py tests/unit/test_vm_export.py
git commit -m "feat: add vrg vm export command for VM-to-template conversion"
```

---

### Task 3: Package JSON Schema for distribution

**Files:**
- Modify: `pyproject.toml`

**Step 1: Ensure schema is included in wheel**

The schema file at `src/verge_cli/schemas/vrg-vm-template.schema.json` should already be included since it's inside the package directory. Verify by checking the hatch build config.

If not picked up automatically, add to `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/verge_cli"]
```

This already exists and should include the `schemas/` subdirectory.

**Step 2: Verify schema loads from package**

Run: `uv run python -c "from verge_cli.template.schema import _load_schema; s = _load_schema(); print(s['title'])"`
Expected: `VergeOS VM Template`

**Step 3: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 4: Lint everything**

Run: `uv run ruff check src/verge_cli/template/ src/verge_cli/commands/`
Expected: Clean (or fix any issues)

**Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore: ensure JSON schema is packaged in distribution"
```

---

### Task 4: Final integration verification

**Step 1: Verify all commands work end-to-end**

Run these to verify the CLI registers everything correctly:

```bash
uv run vrg vm --help
uv run vrg vm drive --help
uv run vrg vm nic --help
uv run vrg vm device --help
uv run vrg vm validate --help
uv run vrg vm export --help
```

Each should show the help text with no import errors.

**Step 2: Verify template validation with reference templates**

```bash
uv run vrg vm validate -f .claude/reference/web-server.vrg.yml
uv run vrg vm validate -f .claude/reference/windows-server.vrg.yml
uv run vrg vm validate -f .claude/reference/k8s-cluster.vrg.yml
```

Note: These may need minor adjustments if the templates use field names not in the schema. Fix schema or templates as needed.

**Step 3: Run full test suite with coverage**

Run: `uv run pytest tests/unit/ -v --tb=short`
Expected: All PASS

**Step 4: Final commit**

If any fixes were needed, commit them:
```bash
git add -A
git commit -m "fix: resolve integration issues from Phase 2 implementation"
```

---

## Milestone 5 Complete

After M5 you should have:
- `src/verge_cli/template/exporter.py` — VM-to-YAML export with hydration header
- `vrg vm export <vm>` — exports to stdout
- `vrg vm export <vm> -o file.vrg.yaml` — exports to file
- JSON schema packaged in the distribution
- Reference templates validate against the schema
- All commands registered and showing help
- Full test suite passing

## Phase 2 Complete

All five milestones delivered:
- **M1:** units.py + resolver.py (foundation)
- **M2:** vrg vm drive/nic/device CRUD commands
- **M3:** Template loader, schema validation, vrg vm validate
- **M4:** Template create with -f/--set/--dry-run, VirtualMachineSet
- **M5:** vrg vm export, JSON schema packaging
