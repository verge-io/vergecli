# Phase 4b: NAS Volumes & Snapshots Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas volume` commands for volume CRUD and `vrg nas volume snapshot` sub-commands
**Depends on:** Phase 4a (NAS Services)
**Blocks:** 4c (Shares), 4e (Syncs), 4f (Files)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add NAS volume management with snapshot sub-resources. Volumes are the core storage units in the NAS subsystem. The SDK exposes volumes via `client.nas_volumes` (NASVolumeManager) and snapshots via `client.nas_volume_snapshots` (NASVolumeSnapshotManager) or scoped via `client.nas_volumes.snapshots(volume_key)`.

NAS volumes use **40-character hex string keys** (not integers like most VergeOS resources). This plan also introduces a `resolve_nas_resource()` utility for hex-key resolution.

## Commands

```
vrg nas volume list [--service SERVICE] [--fs-type TYPE]
vrg nas volume get <VOLUME>
vrg nas volume create --name NAME --service SERVICE --size-gb GB [--tier TIER] [--description DESC] [--read-only] [--owner-user USER] [--owner-group GROUP] [--snapshot-profile PROFILE]
vrg nas volume update <VOLUME> [--description DESC] [--size-gb GB] [--tier TIER] [--read-only | --no-read-only] [--owner-user USER] [--owner-group GROUP] [--snapshot-profile PROFILE] [--automount-snapshots | --no-automount-snapshots]
vrg nas volume delete <VOLUME> [--yes]
vrg nas volume enable <VOLUME>
vrg nas volume disable <VOLUME>
vrg nas volume reset <VOLUME>
vrg nas volume snapshot list <VOLUME>
vrg nas volume snapshot get <VOLUME> <SNAPSHOT>
vrg nas volume snapshot create <VOLUME> --name NAME [--expires-days DAYS] [--never-expires] [--quiesce] [--description DESC]
vrg nas volume snapshot delete <VOLUME> <SNAPSHOT> [--yes]
```

### Command Details

#### `volume list`
- Options:
  - `--service` (str, optional) — filter by NAS service name or key
  - `--fs-type` (str, optional) — filter by filesystem type (ext4, cifs, nfs, ybfs, verge_vm_export)
- SDK: `client.nas_volumes.list(service=service, fs_type=fs_type)`

#### `volume get`
- Positional: `VOLUME` (name or hex key)
- SDK: `client.nas_volumes.get(key=key)` or `get(name=name)`
- Uses new `resolve_nas_resource()` for hex key detection

#### `volume create`
- Options:
  - `--name / -n` (str, required)
  - `--service` (str, required) — NAS service name or key
  - `--size-gb` (int, required) — volume size in GB
  - `--tier` (int, optional) — preferred storage tier (1-5)
  - `--description / -d` (str, optional)
  - `--read-only` (flag, optional)
  - `--owner-user` (str, optional)
  - `--owner-group` (str, optional)
  - `--snapshot-profile` (str, optional) — snapshot profile name or key
- SDK: `client.nas_volumes.create(name=..., service=..., size_gb=..., tier=..., ...)`
- Size is stored in bytes internally (SDK converts GB × 1073741824)

#### `volume update`
- Positional: `VOLUME` (name or hex key)
- Options: same as create minus --name and --service, plus --automount-snapshots / --no-automount-snapshots
- SDK: `client.nas_volumes.update(key, ...)`

#### `volume delete`
- Positional: `VOLUME`
- Options: `--yes / -y` — skip confirmation
- SDK: `client.nas_volumes.delete(key)`

#### `volume enable` / `volume disable`
- Positional: `VOLUME`
- SDK: `client.nas_volumes.enable(key)` / `disable(key)`

#### `volume reset`
- Positional: `VOLUME`
- Resets volume to recover from error state
- SDK: `client.nas_volumes.reset(key)`

#### `volume snapshot list`
- Positional: `VOLUME` (name or hex key)
- Lists all snapshots for the volume
- SDK: `client.nas_volumes.snapshots(volume_key).list()` or `client.nas_volume_snapshots.list(volume=volume_key)`

#### `volume snapshot get`
- Positional: `VOLUME`, `SNAPSHOT` (name or hex key)
- SDK: `client.nas_volume_snapshots.get(key=key)` or `get(name=name)`

#### `volume snapshot create`
- Positional: `VOLUME`
- Options:
  - `--name / -n` (str, required)
  - `--expires-days` (int, default 3) — retention in days
  - `--never-expires` (flag) — mutually exclusive with --expires-days
  - `--quiesce` (flag) — quiesce filesystem before snapshot
  - `--description / -d` (str, optional)
- SDK: `client.nas_volume_snapshots.create(name=..., volume=volume_key, expires_days=..., never_expires=..., quiesce=...)`

#### `volume snapshot delete`
- Positional: `VOLUME`, `SNAPSHOT`
- Options: `--yes / -y`
- SDK: `client.nas_volume_snapshots.delete(key)`

## Files

### New Files

1. **`src/verge_cli/commands/nas_volume.py`**
   - Helpers: `_volume_to_dict()`
   - Commands: list, get, create, update, delete, enable, disable, reset
   - Uses new `resolve_nas_resource()` from `utils.py`

2. **`src/verge_cli/commands/nas_volume_snapshot.py`**
   - Helpers: `_snapshot_to_dict()`, `_resolve_volume()` (gets volume key from positional arg)
   - Commands: list, get, create, delete
   - Pattern: mirrors Phase 3a vm_snapshot.py structure

3. **`tests/unit/test_nas_volume.py`**
   - Fixture: `mock_nas_volume` — MagicMock with key="a1b2c3...(40 chars)", name="data-vol", max_size=53687091200, enabled=True
   - Tests: see test plan

4. **`tests/unit/test_nas_volume_snapshot.py`**
   - Fixture: `mock_nas_volume_snapshot` — MagicMock with key="d4e5f6...(40 chars)", name="snap-001"
   - Tests: see test plan

### Modified Files

5. **`src/verge_cli/commands/nas.py`**
   - Add: `from verge_cli.commands import nas_volume, nas_volume_snapshot`
   - Add: `app.add_typer(nas_volume.app, name="volume")`
   - Wire snapshot sub-typer inside volume app

6. **`src/verge_cli/utils.py`**
   - Add: `resolve_nas_resource()` function for hex key resolution

7. **`tests/conftest.py`**
   - Add fixtures: `mock_nas_volume`, `mock_nas_volume_snapshot`

## Utility Addition

```python
# In utils.py
import re

_HEX_KEY_PATTERN = re.compile(r"^[0-9a-f]{40}$")

def resolve_nas_resource(
    manager: Any,
    identifier: str,
    resource_type: str = "resource",
) -> str:
    """Resolve a name or hex key to a NAS resource key.

    NAS resources (volumes, shares, users, syncs) use 40-character
    hex string keys instead of integer keys.

    Args:
        manager: pyvergeos NAS resource manager.
        identifier: Either a 40-char hex key or a resource name.
        resource_type: Type name for error messages.

    Returns:
        Resource key (str, 40-char hex).

    Raises:
        ResourceNotFoundError: No resource matches.
        MultipleMatchesError: Multiple resources match name.
    """
    # If it looks like a hex key, use it directly
    if _HEX_KEY_PATTERN.match(identifier):
        return identifier

    # Search by name
    try:
        resources = manager.list()
    except Exception as e:
        raise ResourceNotFoundError(f"Failed to list {resource_type}s: {e}") from e

    matches = []
    for resource in resources:
        if isinstance(resource, dict):
            name = resource.get("name", "")
            key = resource.get("$key", resource.get("key"))
        else:
            name = getattr(resource, "name", "")
            key = getattr(resource, "key", getattr(resource, "$key", None))

        if name == identifier:
            matches.append({"name": name, "$key": key})

    if len(matches) == 1:
        return str(matches[0]["$key"])

    if len(matches) > 1:
        raise MultipleMatchesError(resource_type, identifier, matches)

    raise ResourceNotFoundError(f"{resource_type} '{identifier}' not found")
```

## Column Definitions

```python
# In nas_volume.py
NAS_VOLUME_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("size_gb", header="Size (GB)"),
    ColumnDef("used_gb", header="Used (GB)", wide_only=True),
    ColumnDef("fs_type", header="FS Type", wide_only=True),
    ColumnDef("preferred_tier", header="Tier", wide_only=True),
    ColumnDef("description", wide_only=True),
]

# In nas_volume_snapshot.py
NAS_VOLUME_SNAPSHOT_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _volume_to_dict(vol: Any) -> dict[str, Any]:
    return {
        "$key": vol.key,
        "name": vol.name,
        "enabled": vol.get("enabled"),
        "size_gb": vol.max_size_gb if hasattr(vol, "max_size_gb") else vol.get("max_size", 0) / 1073741824,
        "used_gb": vol.used_gb if hasattr(vol, "used_gb") else None,
        "fs_type": vol.get("fs_type"),
        "preferred_tier": vol.get("preferred_tier"),
        "description": vol.get("description", ""),
    }

def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    return {
        "$key": snap.key,
        "name": snap.name,
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "description": snap.get("description", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_volume_list` | Lists all volumes |
| 2 | `test_volume_list_by_service` | Filter by --service |
| 3 | `test_volume_list_by_fs_type` | Filter by --fs-type |
| 4 | `test_volume_get` | Get by name resolution |
| 5 | `test_volume_get_by_hex_key` | Get by 40-char hex key |
| 6 | `test_volume_create` | Create with required args (name, service, size-gb) |
| 7 | `test_volume_create_with_options` | Create with --tier, --owner-user, --snapshot-profile |
| 8 | `test_volume_update` | Update size-gb and tier |
| 9 | `test_volume_delete` | Delete with --yes |
| 10 | `test_volume_enable` | Enable volume |
| 11 | `test_volume_disable` | Disable volume |
| 12 | `test_volume_reset` | Reset errored volume |
| 13 | `test_volume_not_found` | Name resolution error (exit 6) |
| 14 | `test_snapshot_list` | List snapshots for a volume |
| 15 | `test_snapshot_get` | Get snapshot by name |
| 16 | `test_snapshot_create` | Create with --name, --expires-days |
| 17 | `test_snapshot_create_never_expires` | Create with --never-expires |
| 18 | `test_snapshot_delete` | Delete snapshot with --yes |
| 19 | `test_snapshot_not_found` | Snapshot name resolution error |
| 20 | `test_resolve_nas_resource_hex_key` | Hex key passes through directly |

## Task Checklist

- [ ] Add `resolve_nas_resource()` to `utils.py`
- [ ] Create `src/verge_cli/commands/nas_volume.py` with all commands
- [ ] Create `src/verge_cli/commands/nas_volume_snapshot.py` with all commands
- [ ] Register sub-typers in `nas.py`
- [ ] Add fixtures to `conftest.py`
- [ ] Create `tests/unit/test_nas_volume.py` with all tests
- [ ] Create `tests/unit/test_nas_volume_snapshot.py` with all tests
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_nas_volume.py tests/unit/test_nas_volume_snapshot.py -v`

## Notes

- Volume keys are **40-char hex strings** — the new `resolve_nas_resource()` detects these via regex `^[0-9a-f]{40}$`
- Size is stored in bytes internally (max_size field); the SDK provides `max_size_gb` property
- Preferred tier is a string "1"-"5" in the API but exposed as int in the CLI
- Snapshot expiry is calculated by the SDK: `current_time + (expires_days × 86400)` as Unix timestamp
- `--never-expires` and `--expires-days` are mutually exclusive
- Volume snapshots can also be accessed via the global `client.nas_volume_snapshots` manager
