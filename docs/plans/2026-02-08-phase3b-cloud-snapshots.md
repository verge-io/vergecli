# Phase 3b: Cloud Snapshots Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg snapshot` top-level commands for cloud snapshot management
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add cloud snapshot management as a top-level command group `vrg snapshot`. Cloud snapshots are system-wide snapshots of the entire VergeOS environment (VMs, tenants, networks, etc.). The SDK exposes cloud snapshots via `client.cloud_snapshots` (CloudSnapshotManager).

This plan implements snapshot listing, viewing, creation, deletion, and viewing snapshot contents (VMs and tenants). Restoration is explicitly excluded. Snapshot profiles will be added in Phase 3c as `vrg snapshot profile ...`.

## Commands

```
vrg snapshot list [--include-expired]
vrg snapshot get <SNAPSHOT>
vrg snapshot create [--name NAME] [--retention SECONDS] [--never-expire] [--immutable] [--private] [--wait]
vrg snapshot delete <SNAPSHOT> [--yes]
vrg snapshot vms <SNAPSHOT>
vrg snapshot tenants <SNAPSHOT>
```

### Command Details

#### `list`
- Options:
  - `--include-expired` (flag) — include expired snapshots in results
- Lists all cloud snapshots
- SDK: `client.cloud_snapshots.list(include_expired=...)`

#### `get`
- Positional: `SNAPSHOT` (name or key)
- Shows detailed snapshot info
- SDK: `client.cloud_snapshots.get(key=..., name=...)`

#### `create`
- Options:
  - `--name / -n` (str, optional) — snapshot name, auto-generated if omitted
  - `--retention` (int, optional) — retention in seconds
  - `--never-expire` (flag) — snapshot never expires (overrides --retention)
  - `--immutable` (flag) — make snapshot immutable
  - `--private` (flag) — mark snapshot as private
  - `--wait` (flag) — wait for snapshot completion
- `--retention` and `--never-expire` are mutually exclusive (error if both given)
- SDK: `client.cloud_snapshots.create(name=..., retention_seconds=..., never_expire=..., immutable=..., private=..., wait=...)`

#### `delete`
- Positional: `SNAPSHOT` (name or key)
- Options: `--yes / -y` — skip confirmation
- SDK: `client.cloud_snapshots.delete(key)`

#### `vms`
- Positional: `SNAPSHOT` (name or key)
- Lists VMs captured in the snapshot
- SDK: `client.cloud_snapshots.vms(snapshot_key).list()`

#### `tenants`
- Positional: `SNAPSHOT` (name or key)
- Lists tenants captured in the snapshot
- SDK: `client.cloud_snapshots.tenants(snapshot_key).list()`

## Files

### New Files

1. **`src/verge_cli/commands/snapshot.py`**
   - Top-level typer app (no parent resource)
   - Helper: `_resolve_snapshot()` — resolve snapshot name/key to int key
   - Helper: `_snapshot_to_dict()` — convert SDK object to output dict
   - Helper: `_vm_to_dict()` — convert snapshot VM object to output dict
   - Helper: `_tenant_to_dict()` — convert snapshot tenant object to output dict
   - Commands: list, get, create, delete, vms, tenants

2. **`tests/unit/test_snapshot.py`**
   - Fixture: `mock_cloud_snapshot` — MagicMock with key=800, name="daily-2026-02-08"
   - Tests: see test plan below

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import snapshot`
   - Add: `app.add_typer(snapshot.app, name="snapshot")`

4. **`src/verge_cli/columns.py`**
   - Add `CLOUD_SNAPSHOT_COLUMNS` definition
   - Add `CLOUD_SNAPSHOT_VM_COLUMNS` definition
   - Add `CLOUD_SNAPSHOT_TENANT_COLUMNS` definition

## Column Definitions

```python
CLOUD_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("immutable", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("private", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("description", wide_only=True),
]

CLOUD_SNAPSHOT_VM_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
]

CLOUD_SNAPSHOT_TENANT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
]
```

## Data Mapping

```python
def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    return {
        "$key": snap.key,
        "name": snap.name,
        "status": snap.get("status"),
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "immutable": snap.get("immutable"),
        "private": snap.get("private"),
        "description": snap.get("description", ""),
    }

def _vm_to_dict(vm: Any) -> dict[str, Any]:
    return {
        "$key": vm.key,
        "name": vm.name,
        "status": vm.get("status"),
    }

def _tenant_to_dict(tenant: Any) -> dict[str, Any]:
    return {
        "$key": tenant.key,
        "name": tenant.name,
        "status": tenant.get("status"),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_snapshot_list` | Basic list |
| 2 | `test_snapshot_list_include_expired` | List with --include-expired |
| 3 | `test_snapshot_list_empty` | Handles empty list |
| 4 | `test_snapshot_get` | Get by name resolution |
| 5 | `test_snapshot_get_by_key` | Get by numeric key |
| 6 | `test_snapshot_create` | Basic create (no options) |
| 7 | `test_snapshot_create_with_options` | --name, --retention, --immutable, --private |
| 8 | `test_snapshot_create_never_expire` | --never-expire |
| 9 | `test_snapshot_create_wait` | --wait for completion |
| 10 | `test_snapshot_delete` | Delete with --yes |
| 11 | `test_snapshot_vms` | List VMs in snapshot |
| 12 | `test_snapshot_tenants` | List tenants in snapshot |
| 13 | `test_snapshot_not_found` | Name resolution error (exit 6) |
| 14 | `test_snapshot_create_retention_and_never_expire_error` | --retention + --never-expire mutual exclusion |

## Task Checklist

- [ ] Add `CLOUD_SNAPSHOT_COLUMNS`, `CLOUD_SNAPSHOT_VM_COLUMNS`, `CLOUD_SNAPSHOT_TENANT_COLUMNS` to `columns.py`
- [ ] Create `snapshot.py` with all commands
- [ ] Register top-level typer in `cli.py`
- [ ] Create `test_snapshot.py` with all tests
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_snapshot.py -v`

## Notes

- The `snapshot` typer is set up to accept sub-typers later (Phase 3c will add `vrg snapshot profile ...`)
- No restore commands — restoration is explicitly excluded from cloud snapshots
- The `--include-expired` flag is only available on `list`, not `get` (SDK supports it on both, but it's semantically odd to get an expired snapshot by key/name)
- The `vms` and `tenants` commands use separate managers returned by the SDK: `client.cloud_snapshots.vms(key)` and `client.cloud_snapshots.tenants(key)`
- Snapshot status values should be styled with STATUS_STYLES (running, completed, failed, etc.)
