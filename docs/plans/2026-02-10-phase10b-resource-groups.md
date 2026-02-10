# Phase 10b: Resource Groups Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg resource-group` commands — device passthrough group management
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Resource Groups | `resource_groups` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/resource_groups.py` |
| vGPU Profiles | `vgpu_profiles` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/gpu.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/gpu_passthrough_example.py`

---

## Overview

Add resource group management for PCI/USB/GPU device passthrough. Resource groups define collections of physical devices that can be passed through to VMs. The SDK provides a generic `create()` plus specialized factory methods for each device type (PCI, USB, Host GPU, NVIDIA vGPU, SR-IOV NIC).

**Key details:**
- Resource group keys are **UUID strings**, not integers — use `resolve_nas_resource()` pattern (hex/UUID lookup)
- Device types: `pci`, `usb`, `host-gpu`, `nvidia-vgpu`, `sriov-nic`
- Device classes: `gpu`, `vgpu`, `storage`, `hid`, `usb`, `network`, `media`, `audio`, `fpga`, `pci`, `unknown`
- The SDK has rich filtering: `list_enabled()`, `list_disabled()`, `list_by_type()`, `list_by_class()`
- Specialized create methods have many device-specific options — expose via `vrg resource-group create --type <TYPE>` with type-specific flags
- Resource groups also have a `rules` sub-manager for device matching rules, but we'll keep that for a future enhancement given complexity

**Reference implementations:** `recipe.py` for CRUD, NAS commands for string-key resolution.

## Commands

```
vrg resource-group list [--filter ODATA] [--type TYPE] [--class CLASS] [--enabled | --disabled]
vrg resource-group get <ID|NAME>
vrg resource-group create --name NAME --type pci|usb|host-gpu|nvidia-vgpu|sriov-nic [--description DESC] [--device-class CLASS] [--enabled | --no-enabled] [type-specific options...]
vrg resource-group update <ID|NAME> [--name NAME] [--description DESC] [--enabled BOOL]
vrg resource-group delete <ID|NAME> [--yes]
```

### Command Details

#### `vrg resource-group list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--type` (str) — filter by device type (pci/usb/host-gpu/nvidia-vgpu/sriov-nic)
  - `--class` (str) — filter by device class (gpu/storage/network/usb/pci/etc.)
  - `--enabled / --disabled` (flag pair)
- SDK routing:
  - `--enabled`: `resource_groups.list_enabled()`
  - `--disabled`: `resource_groups.list_disabled()`
  - `--type X`: `resource_groups.list_by_type(device_type=X, enabled=enabled)`
  - `--class X`: `resource_groups.list_by_class(device_class=X, enabled=enabled)`
  - Default: `resource_groups.list()`

#### `vrg resource-group get`

- Positional: `GROUP` (UUID string or name)
- Resolution: if it looks like a UUID, pass directly; otherwise `resource_groups.get(name=name)`
- SDK: `resource_groups.get(key=uuid)` or `resource_groups.get(name=name)`

#### `vrg resource-group create`

- Required: `--name`, `--type` (device type)
- Common options: `--description`, `--enabled / --no-enabled` (default enabled)
- Type-specific routing:
  - `--type pci` → `resource_groups.create_pci(name, device_class=..., ...)`
  - `--type usb` → `resource_groups.create_usb(name, allow_guest_reset=..., ...)`
  - `--type host-gpu` → `resource_groups.create_host_gpu(name, ...)`
  - `--type nvidia-vgpu` → `resource_groups.create_nvidia_vgpu(name, driver_file=..., ...)`
  - `--type sriov-nic` → `resource_groups.create_sriov_nic(name, vf_count=..., ...)`

Type-specific options (only shown/required when matching `--type`):

**USB options:**
- `--allow-guest-reset / --no-allow-guest-reset` (default True)

**NVIDIA vGPU options:**
- `--driver-file` (str, required) — driver file path/key
- `--vgpu-profile` (str) — NVIDIA vGPU profile
- `--make-guest-driver-iso` (flag)
- `--driver-iso` (str) — driver ISO file

**SR-IOV NIC options:**
- `--vf-count` (int, default 1) — virtual function count
- `--native-vlan` (int, default 0)

**Implementation note:** Use a single `create` command with optional flags. Validate that required type-specific flags are provided based on `--type`. Don't create separate commands per type — that's over-engineering for CLI users.

#### `vrg resource-group update`

- Positional: `GROUP` (UUID or name)
- Optional: `--name`, `--description`, `--enabled / --no-enabled`
- SDK: `resource_groups.update(key, ...)`

#### `vrg resource-group delete`

- Positional: `GROUP` (UUID or name)
- `--yes / -y` — skip confirmation
- SDK: `resource_groups.delete(key)`

### Device Type Mapping

```python
DEVICE_TYPE_MAP: dict[str, str] = {
    "pci": "node_pci_devices",
    "usb": "node_usb_devices",
    "host-gpu": "node_host_gpu_devices",
    "nvidia-vgpu": "node_nvidia_vgpu_devices",
    "sriov-nic": "node_sriov_nic_devices",
}

# Reverse for display
DEVICE_TYPE_DISPLAY: dict[str, str] = {
    "node_pci_devices": "PCI",
    "node_usb_devices": "USB",
    "node_host_gpu_devices": "Host GPU",
    "node_nvidia_vgpu_devices": "NVIDIA vGPU",
    "node_sriov_nic_devices": "SR-IOV NIC",
}
```

### Resource Group Resolution

Resource groups use UUID string keys. The SDK's `get()` supports `key=`, `name=`, and `uuid=` lookups:

```python
import re

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

def _resolve_resource_group(client: Any, identifier: str) -> str:
    """Resolve resource group identifier (UUID or name) to UUID key."""
    if _UUID_PATTERN.match(identifier):
        return identifier
    group = client.resource_groups.get(name=identifier)
    return str(group.key)
```

## Files

### New Files

1. **`src/verge_cli/commands/resource_group.py`** — Resource group commands
   - Typer app with: list, get, create, update, delete
   - Columns: `RESOURCE_GROUP_COLUMNS`
   - Helpers: `_group_to_dict()`, `_resolve_resource_group()`
   - Constants: `DEVICE_TYPE_MAP`, `DEVICE_TYPE_DISPLAY`

2. **`tests/unit/test_resource_group.py`** — Tests for resource group commands

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import resource_group`
   - Add: `app.add_typer(resource_group.app, name="resource-group")`

4. **`tests/conftest.py`**
   - Add `mock_resource_group` fixture

## Column Definition

### RESOURCE_GROUP_COLUMNS

```python
RESOURCE_GROUP_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="UUID"),
    ColumnDef("name"),
    ColumnDef("device_type", header="Device Type"),
    ColumnDef("device_class", header="Class"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Y": "green", "-": "red"}),
    ColumnDef("resource_count", header="Devices"),
    ColumnDef("description", wide_only=True),
    ColumnDef("created_at", header="Created", format_fn=format_epoch, wide_only=True),
]
```

## Data Mapping

```python
def _group_to_dict(group: Any) -> dict[str, Any]:
    return {
        "$key": str(group.key),  # UUID string
        "name": group.name,
        "device_type": group.device_type_display,
        "device_class": group.device_class_display,
        "enabled": group.is_enabled,
        "resource_count": group.resource_count,
        "description": group.description,
        "created_at": group.created_at.timestamp() if group.created_at else None,
    }
```

## Test Fixture

```python
@pytest.fixture
def mock_resource_group() -> MagicMock:
    group = MagicMock()
    group.key = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    group.uuid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    group.name = "gpu-passthrough"
    group.device_type = "node_pci_devices"
    group.device_type_display = "PCI"
    group.device_class = "gpu"
    group.device_class_display = "GPU"
    group.is_enabled = True
    group.resource_count = 2
    group.description = "GPU passthrough group"
    group.created_at = datetime(2026, 2, 10, 0, 0, 0)
    group.modified_at = datetime(2026, 2, 10, 0, 0, 0)
    return group
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_group_list` | Lists resource groups |
| 2 | `test_group_list_enabled` | `--enabled` filter |
| 3 | `test_group_list_disabled` | `--disabled` filter |
| 4 | `test_group_list_by_type` | `--type pci` filter |
| 5 | `test_group_list_by_class` | `--class gpu` filter |
| 6 | `test_group_get_by_uuid` | Get by UUID string |
| 7 | `test_group_get_by_name` | Get by name |
| 8 | `test_group_create_pci` | Create PCI group |
| 9 | `test_group_create_usb` | Create USB group |
| 10 | `test_group_create_host_gpu` | Create host GPU group |
| 11 | `test_group_create_nvidia_vgpu` | Create vGPU group with driver-file |
| 12 | `test_group_create_sriov_nic` | Create SR-IOV NIC group |
| 13 | `test_group_update` | Update description and enabled |
| 14 | `test_group_delete_confirm` | Delete with --yes |
| 15 | `test_group_delete_no_confirm` | Delete without --yes aborts |
| 16 | `test_group_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Create `resource_group.py` with list, get, create, update, delete commands
- [x] Register `resource-group` in `cli.py`
- [x] Add `mock_resource_group` fixture to `conftest.py`
- [x] Create `test_resource_group.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
