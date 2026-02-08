# Phase 3a: VM Snapshots Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg vm snapshot` sub-commands for VM snapshot management
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add VM snapshot management as a sub-resource of `vrg vm`, mirroring the existing `tenant_snapshot.py` pattern. The SDK exposes VM snapshots via `vm_obj.snapshots` (VMSnapshotManager).

## Commands

```
vrg vm snapshot list <VM>
vrg vm snapshot get <VM> <SNAPSHOT>
vrg vm snapshot create <VM> [--name NAME] [--retention SECONDS] [--quiesce] [--description DESC]
vrg vm snapshot delete <VM> <SNAPSHOT> [--yes]
vrg vm snapshot restore <VM> <SNAPSHOT> [--name NAME] [--replace] [--power-on] [--yes]
```

### Command Details

#### `list`
- Positional: `VM` (name or key)
- Lists all snapshots for the specified VM
- SDK: `vm_obj.snapshots.list()`

#### `get`
- Positional: `VM` (name or key), `SNAPSHOT` (name or key)
- Shows detailed snapshot info
- SDK: `vm_obj.snapshots.get(key)`

#### `create`
- Positional: `VM` (name or key)
- Options:
  - `--name / -n` (optional) — snapshot name, auto-generated if omitted
  - `--retention` (int, default 86400) — retention in seconds (0 = never expires)
  - `--quiesce` (flag) — quiesce filesystem (requires guest agent)
  - `--description / -d` (str, default "") — description
- SDK: `vm_obj.snapshots.create(name=..., retention=..., quiesce=..., description=...)`

#### `delete`
- Positional: `VM`, `SNAPSHOT`
- Options: `--yes / -y` — skip confirmation
- SDK: `vm_obj.snapshots.delete(key)`

#### `restore`
- Positional: `VM`, `SNAPSHOT`
- Options:
  - `--name` (str, optional) — new VM name for clone mode
  - `--replace` (flag) — replace original VM (destructive, requires confirmation)
  - `--power-on` (flag) — power on after restore
  - `--yes / -y` — skip confirmation for destructive operations
- `--replace` and `--name` are mutually exclusive (error if both given)
- Bare restore (no `--name`, no `--replace`) is allowed — SDK handles default
- `--replace` requires `--yes` or interactive confirmation
- SDK: `vm_obj.snapshots.restore(key, name=..., replace_original=..., power_on=...)`

## Files

### New Files

1. **`src/verge_cli/commands/vm_snapshot.py`**
   - Pattern: mirror `tenant_snapshot.py`
   - Helper: `_get_vm()` — resolve VM and return (vctx, vm_obj)
   - Helper: `_resolve_snapshot()` — resolve snapshot name/key to int key
   - Helper: `_snapshot_to_dict()` — convert SDK object to output dict
   - Commands: list, get, create, delete, restore

2. **`tests/unit/test_vm_snapshot.py`**
   - Fixture: `mock_vm_snapshot` — MagicMock with key=700, name="pre-upgrade"
   - Tests: see test plan below

### Modified Files

3. **`src/verge_cli/commands/vm.py`**
   - Add: `from verge_cli.commands import vm_snapshot`
   - Add: `app.add_typer(vm_snapshot.app, name="snapshot")`

4. **`src/verge_cli/columns.py`**
   - Add `VM_SNAPSHOT_COLUMNS` definition

## Column Definition

```python
VM_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("quiesced", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    return {
        "$key": snap.key,
        "name": snap.name,
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "quiesced": snap.get("quiesced"),
        "description": snap.get("description", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_snapshot_list` | Lists snapshots for a VM |
| 2 | `test_snapshot_list_empty` | Handles empty list |
| 3 | `test_snapshot_get` | Get by name resolution |
| 4 | `test_snapshot_get_by_key` | Get by numeric key |
| 5 | `test_snapshot_create` | Basic create (no name) |
| 6 | `test_snapshot_create_with_options` | --name, --retention, --quiesce, --description |
| 7 | `test_snapshot_delete` | Delete with --yes |
| 8 | `test_snapshot_restore` | Bare restore |
| 9 | `test_snapshot_restore_clone` | Restore with --name (clone mode) |
| 10 | `test_snapshot_restore_replace` | Restore with --replace --yes |
| 11 | `test_snapshot_restore_replace_and_name_error` | --replace + --name mutual exclusion |
| 12 | `test_snapshot_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [ ] Add `VM_SNAPSHOT_COLUMNS` to `columns.py`
- [ ] Create `vm_snapshot.py` with all commands
- [ ] Register sub-typer in `vm.py`
- [ ] Create `test_vm_snapshot.py` with all tests
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_vm_snapshot.py -v`
