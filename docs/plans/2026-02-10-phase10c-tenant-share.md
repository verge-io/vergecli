# Phase 10c: Tenant Share (Shared Objects) Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg tenant share` sub-command — shared object management for tenant VM sharing
**Dependencies:** None (tenant.py already exists)
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Shared Objects | `shared_objects` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/shared_objects.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/tenant_management.py`

---

## Overview

Add shared object management as a sub-command of `vrg tenant`. Shared objects allow VMs (or VM snapshots) to be shared from the host environment to tenants. The tenant can then import the shared object to receive a copy of the VM.

**Design decision:** The release plan listed this as `vrg shared-object`, but per user direction this will be `vrg tenant share` to match the VergeOS UI naming and follow existing tenant sub-command conventions (like `vrg tenant snapshot`, `vrg tenant node`, etc.).

**Key details:**
- Shared object keys are integers
- `SharedObjectManager` is not a standard `ResourceManager` subclass — it's a standalone class
- The manager supports tenant-scoped listing: `list(tenant_key=...)` or `list_for_tenant(tenant)`
- `create()` accepts `vm_key` or `vm_name` (auto-resolves), plus optional `snapshot_name` to share a snapshot instead of the live VM
- `import_object()` imports a shared object into the tenant (creates a VM copy)
- `refresh_object()` refreshes the shared data
- There's an `inbox_only` filter — inbox items are objects that have been shared but not yet imported
- No `update()` method exists — shared objects are create + import + delete only

**Reference implementations:** `tenant_snapshot.py` for tenant sub-command pattern.

## Commands

```
vrg tenant share list <TENANT> [--inbox]
vrg tenant share get <TENANT> <SHARE_ID>
vrg tenant share create <TENANT> --vm <VM_NAME|KEY> [--name NAME] [--description DESC] [--snapshot SNAPSHOT_NAME]
vrg tenant share import <TENANT> <SHARE_ID>
vrg tenant share refresh <TENANT> <SHARE_ID>
vrg tenant share delete <TENANT> <SHARE_ID> [--yes]
```

### Command Details

#### `vrg tenant share list`

- Positional: `TENANT` (tenant name or key)
- Options:
  - `--inbox` (flag) — show only inbox items (shared but not yet imported)
- Steps:
  1. Resolve tenant: `resolve_resource_id(client.tenants, tenant, "Tenant")`
  2. List shared objects for tenant
- SDK: `shared_objects.list(tenant_key=tenant_key, inbox_only=inbox)`

#### `vrg tenant share get`

- Positional: `TENANT` (tenant name or key), `SHARE` (numeric share key or name)
- Steps:
  1. Resolve tenant
  2. If `SHARE` is numeric → `shared_objects.get(key=int(share))`
  3. If name → `shared_objects.get(tenant_key=tenant_key, name=share)`
- SDK: `shared_objects.get(key=...)` or `shared_objects.get(tenant_key=..., name=...)`

#### `vrg tenant share create`

- Positional: `TENANT` (tenant name or key)
- Required: `--vm` (VM name or key to share)
- Optional:
  - `--name` (str) — display name for the shared object
  - `--description` (str) — description
  - `--snapshot` (str) — share a specific snapshot of the VM instead of the live VM
- Steps:
  1. Resolve tenant
  2. Resolve VM: `resolve_resource_id(client.vms, vm, "VM")` to get vm_key
  3. Create shared object
- SDK: `shared_objects.create(tenant_key=tenant_key, vm_key=vm_key, name=name, description=description, snapshot_name=snapshot)`

#### `vrg tenant share import`

- Positional: `TENANT` (tenant name or key), `SHARE` (numeric share key)
- Imports the shared object into the tenant — creates a VM copy
- SDK: `shared_objects.import_object(key=int(share))`
- Output: success message with import result

#### `vrg tenant share refresh`

- Positional: `TENANT` (tenant name or key), `SHARE` (numeric share key)
- Refreshes the shared object data from the source
- SDK: `shared_objects.refresh_object(key=int(share))`
- Output: success message

#### `vrg tenant share delete`

- Positional: `TENANT` (tenant name or key), `SHARE` (numeric share key or name)
- `--yes / -y` — skip confirmation
- SDK: `shared_objects.delete(key=int(share_key))`

## Files

### New Files

1. **`src/verge_cli/commands/tenant_share.py`** — Tenant share sub-commands
   - Typer app with: list, get, create, import, refresh, delete
   - Columns: `SHARE_COLUMNS`
   - Helpers: `_share_to_dict()`, `_resolve_share()`
   - Pattern follows `tenant_snapshot.py`

2. **`tests/unit/test_tenant_share.py`** — Tests for tenant share commands

### Modified Files

3. **`src/verge_cli/commands/tenant.py`**
   - Add: `from verge_cli.commands import tenant_share`
   - Add: `app.add_typer(tenant_share.app, name="share")`

4. **`tests/conftest.py`**
   - Add `mock_shared_object` fixture

## Column Definition

### SHARE_COLUMNS

```python
SHARE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("tenant_name", header="Tenant"),
    ColumnDef("object_type", header="Type"),
    ColumnDef("is_inbox", header="Inbox", format_fn=format_bool_yn, style_map={"Y": "yellow", "-": "dim"}),
    ColumnDef("description", wide_only=True),
    ColumnDef("created_at", header="Created", format_fn=format_epoch, wide_only=True),
]
```

## Data Mapping

```python
def _share_to_dict(obj: Any) -> dict[str, Any]:
    return {
        "$key": int(obj.key),
        "name": obj.name,
        "description": obj.description or "",
        "tenant_name": obj.tenant_name or "",
        "object_type": obj.object_type or "",
        "is_inbox": obj.is_inbox,
        "created_at": obj.created_at.timestamp() if obj.created_at else None,
    }
```

## Test Fixture

```python
@pytest.fixture
def mock_shared_object() -> MagicMock:
    obj = MagicMock()
    obj.key = 15
    obj.name = "shared-web-server"
    obj.description = "Web server VM shared to dev tenant"
    obj.tenant_key = 3
    obj.tenant_name = "dev-tenant"
    obj.object_type = "vm"
    obj.object_id = "vms/42"
    obj.snapshot_path = None
    obj.snapshot_key = None
    obj.is_inbox = True
    obj.created_at = datetime(2026, 2, 10, 0, 0, 0)
    return obj
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_share_list` | Lists shared objects for a tenant |
| 2 | `test_share_list_inbox` | `--inbox` filter |
| 3 | `test_share_get_by_key` | Get by numeric key |
| 4 | `test_share_get_by_name` | Get by name with tenant context |
| 5 | `test_share_create` | Create shared object for tenant + VM |
| 6 | `test_share_create_with_snapshot` | Create with `--snapshot` |
| 7 | `test_share_import` | Import shared object |
| 8 | `test_share_refresh` | Refresh shared object |
| 9 | `test_share_delete_confirm` | Delete with --yes |
| 10 | `test_share_delete_no_confirm` | Delete without --yes aborts |
| 11 | `test_share_tenant_not_found` | Tenant resolution error (exit 6) |

## Task Checklist

- [x] Create `tenant_share.py` with list, get, create, import, refresh, delete commands
- [x] Register `share` sub-command in `tenant.py`
- [x] Add `mock_shared_object` fixture to `conftest.py`
- [x] Create `test_tenant_share.py`
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
