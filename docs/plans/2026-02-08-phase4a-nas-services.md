# Phase 4a: NAS Services Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas service` commands for NAS service lifecycle and settings management
**Depends on:** None (must be implemented first in Phase 4)
**Blocks:** 4b (Volumes), 4c (Shares), 4d (Users), 4e (Syncs), 4f (Files)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add NAS service management as the foundation for all NAS operations. NAS services are VMs deployed from the "Services" recipe. The SDK exposes services via `client.nas_services` (NASServiceManager), with separate CIFS and NFS settings endpoints.

Also adds the parent `vrg nas` command group that all subsequent Phase 4 NAS plans will register under.

## Commands

```
vrg nas service list [--status running|stopped]
vrg nas service get <SERVICE>
vrg nas service create --name NAME [--hostname HOSTNAME] [--network NETWORK] [--cores CORES] [--memory-gb GB]
vrg nas service update <SERVICE> [--description DESC] [--cpu-cores CORES] [--memory-gb GB] [--max-imports N] [--max-syncs N] [--disable-swap] [--read-ahead-kb KB]
vrg nas service delete <SERVICE> [--force] [--yes]
vrg nas service power-on <SERVICE>
vrg nas service power-off <SERVICE> [--force]
vrg nas service restart <SERVICE>
vrg nas service cifs-settings <SERVICE>
vrg nas service set-cifs-settings <SERVICE> [--workgroup NAME] [--min-protocol PROTO] [--guest-mapping MODE] [--extended-acl]
vrg nas service nfs-settings <SERVICE>
vrg nas service set-nfs-settings <SERVICE> [--enable-nfsv4] [--allowed-hosts HOSTS] [--allow-all] [--squash MODE] [--data-access MODE] [--anon-uid UID] [--anon-gid GID] [--no-acl] [--insecure] [--async]
```

### Command Details

#### `list`
- Options:
  - `--status` (str, optional) — filter by "running" or "stopped"
- SDK: `client.nas_services.list(status=status)` or `list_running()` / `list_stopped()`

#### `get`
- Positional: `SERVICE` (name or key)
- SDK: `client.nas_services.get(key)` — keys are integers

#### `create`
- Options:
  - `--name / -n` (str, required) — service name
  - `--hostname` (str, optional) — hostname, auto-sanitized from name if omitted
  - `--network` (str, optional) — network name or key
  - `--cores` (int, default 4) — CPU cores
  - `--memory-gb` (int, default 8) — RAM in GB
- SDK: `client.nas_services.create(name=..., hostname=..., network=..., cores=..., memory_gb=...)`
- Note: Service creation deploys a VM from "Services" recipe. The SDK polls for availability.

#### `update`
- Positional: `SERVICE` (name or key)
- Options:
  - `--description / -d` (str, optional)
  - `--cpu-cores` (int, optional)
  - `--memory-gb` (int, optional)
  - `--max-imports` (int, optional) — max concurrent imports (1-10)
  - `--max-syncs` (int, optional) — max concurrent syncs (1-10)
  - `--disable-swap` (bool flag, optional)
  - `--read-ahead-kb` (int, optional) — buffer size (0/64/128/256/512/1024/2048/4096)
- SDK: `client.nas_services.update(key, ...)`

#### `delete`
- Positional: `SERVICE`
- Options:
  - `--force` (flag) — force delete even if volumes exist
  - `--yes / -y` — skip confirmation
- SDK: `client.nas_services.delete(key, force=force)`

#### `power-on`
- Positional: `SERVICE`
- SDK: `client.nas_services.power_on(key)`

#### `power-off`
- Positional: `SERVICE`
- Options: `--force` (flag) — hard shutdown
- SDK: `client.nas_services.power_off(key, force=force)`

#### `restart`
- Positional: `SERVICE`
- SDK: `client.nas_services.restart(key)`

#### `cifs-settings`
- Positional: `SERVICE`
- Displays current CIFS/SMB settings for the service
- SDK: `client.nas_services.get_cifs_settings(key)` → CIFSSettings object

#### `set-cifs-settings`
- Positional: `SERVICE`
- Options:
  - `--workgroup` (str, optional) — NetBIOS workgroup name
  - `--min-protocol` (str, optional) — minimum SMB protocol version (none, SMB2, SMB2_02, SMB2_10, SMB3, SMB3_00, SMB3_02, SMB3_11)
  - `--guest-mapping` (str, optional) — guest access mode ("never", "bad user", "bad password", "bad uid")
  - `--extended-acl / --no-extended-acl` (bool, optional)
- SDK: `client.nas_services.set_cifs_settings(key, workgroup=..., min_protocol=..., guest_mapping=..., extended_acl_support=...)`

#### `nfs-settings`
- Positional: `SERVICE`
- Displays current NFS settings for the service
- SDK: `client.nas_services.get_nfs_settings(key)` → NFSSettings object

#### `set-nfs-settings`
- Positional: `SERVICE`
- Options:
  - `--enable-nfsv4 / --no-nfsv4` (bool, optional)
  - `--allowed-hosts` (str, optional) — comma-separated host/CIDR list
  - `--allow-all / --no-allow-all` (bool, optional)
  - `--squash` (str, optional) — "root_squash", "all_squash", "no_root_squash"
  - `--data-access` (str, optional) — "ro" or "rw"
  - `--anon-uid` (int, optional) — anonymous user ID
  - `--anon-gid` (int, optional) — anonymous group ID
  - `--no-acl` (flag, optional)
  - `--insecure` (flag, optional)
  - `--async` (flag, optional)
- SDK: `client.nas_services.set_nfs_settings(key, enable_nfsv4=..., allowed_hosts=..., allow_all=..., squash=..., data_access=..., anon_uid=..., anon_gid=..., no_acl=..., insecure=..., async_mode=...)`

## Files

### New Files

1. **`src/verge_cli/commands/nas.py`**
   - Parent Typer app for `vrg nas` — just wires up sub-typers
   - Pattern: simple parent app, imports and registers child typers

2. **`src/verge_cli/commands/nas_service.py`**
   - Helpers: `_service_to_dict()`, `_cifs_settings_to_dict()`, `_nfs_settings_to_dict()`
   - Commands: list, get, create, update, delete, power_on, power_off, restart, cifs_settings, set_cifs_settings, nfs_settings, set_nfs_settings
   - Uses existing `resolve_resource_id()` (services use int keys)

3. **`tests/unit/test_nas_service.py`**
   - Fixture: `mock_nas_service` — MagicMock with key=1, name="nas01", vm_running=True, volume_count=3
   - Fixture: `mock_cifs_settings` — MagicMock with workgroup="WORKGROUP", min_protocol defaults
   - Fixture: `mock_nfs_settings` — MagicMock with default NFS settings
   - Tests: see test plan below

### Modified Files

4. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import nas`
   - Add: `app.add_typer(nas.app, name="nas")`

5. **`tests/conftest.py`**
   - Add fixture: `mock_nas_service`

## Column Definitions

```python
# In nas_service.py
NAS_SERVICE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("vm_running", header="Running", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("volume_count", header="Volumes"),
    ColumnDef("vm_cores", header="Cores", wide_only=True),
    ColumnDef("vm_ram", header="RAM (MB)", wide_only=True),
    ColumnDef("max_imports", header="Max Imports", wide_only=True),
    ColumnDef("max_syncs", header="Max Syncs", wide_only=True),
]

CIFS_SETTINGS_COLUMNS: list[ColumnDef] = [
    ColumnDef("workgroup"),
    ColumnDef("server_type", header="Server Type"),
    ColumnDef("server_min_protocol", header="Min Protocol"),
    ColumnDef("map_to_guest", header="Guest Mapping"),
    ColumnDef("extended_acl_support", header="Extended ACL", format_fn=format_bool_yn),
    ColumnDef("ad_status", header="AD Status", wide_only=True),
]

NFS_SETTINGS_COLUMNS: list[ColumnDef] = [
    ColumnDef("enable_nfsv4", header="NFSv4", format_fn=format_bool_yn),
    ColumnDef("allow_all", header="Allow All", format_fn=format_bool_yn),
    ColumnDef("allowed_hosts", header="Allowed Hosts"),
    ColumnDef("squash"),
    ColumnDef("data_access", header="Access"),
    ColumnDef("anonuid", header="Anon UID", wide_only=True),
    ColumnDef("anongid", header="Anon GID", wide_only=True),
]
```

## Data Mapping

```python
def _service_to_dict(svc: Any) -> dict[str, Any]:
    return {
        "$key": svc.key,
        "name": svc.name,
        "vm_running": svc.get("vm_running"),
        "volume_count": svc.get("volume_count"),
        "vm_cores": svc.get("vm_cores"),
        "vm_ram": svc.get("vm_ram"),
        "max_imports": svc.get("max_imports"),
        "max_syncs": svc.get("max_syncs"),
    }

def _cifs_settings_to_dict(settings: Any) -> dict[str, Any]:
    return {
        "workgroup": settings.get("workgroup"),
        "server_type": settings.get("server_type"),
        "server_min_protocol": settings.get("server_min_protocol"),
        "map_to_guest": settings.get("map_to_guest"),
        "extended_acl_support": settings.get("extended_acl_support"),
        "ad_status": settings.get("ad_status"),
    }

def _nfs_settings_to_dict(settings: Any) -> dict[str, Any]:
    return {
        "enable_nfsv4": settings.get("enable_nfsv4"),
        "allow_all": settings.get("allow_all"),
        "allowed_hosts": settings.get("allowed_hosts"),
        "squash": settings.get("squash"),
        "data_access": settings.get("data_access"),
        "anonuid": settings.get("anonuid"),
        "anongid": settings.get("anongid"),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_service_list` | Lists all NAS services |
| 2 | `test_service_list_running` | Filter by --status running |
| 3 | `test_service_get` | Get by name resolution |
| 4 | `test_service_get_by_key` | Get by numeric key |
| 5 | `test_service_create` | Create with defaults (4 cores, 8GB) |
| 6 | `test_service_create_with_options` | Create with --cores, --memory-gb, --network, --hostname |
| 7 | `test_service_update` | Update max-imports, max-syncs, read-ahead-kb |
| 8 | `test_service_delete` | Delete with --yes |
| 9 | `test_service_delete_force` | Delete with --force --yes |
| 10 | `test_service_power_on` | Power on service |
| 11 | `test_service_power_off` | Power off service |
| 12 | `test_service_power_off_force` | Hard power off with --force |
| 13 | `test_service_restart` | Restart service |
| 14 | `test_cifs_settings` | Display CIFS settings |
| 15 | `test_set_cifs_settings` | Update workgroup and min-protocol |
| 16 | `test_nfs_settings` | Display NFS settings |
| 17 | `test_set_nfs_settings` | Update squash, data-access, allowed-hosts |
| 18 | `test_service_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [ ] Create `src/verge_cli/commands/nas.py` parent app
- [ ] Create `src/verge_cli/commands/nas_service.py` with all commands
- [ ] Register `nas` typer in `cli.py`
- [ ] Add `mock_nas_service` fixture to `conftest.py`
- [ ] Create `tests/unit/test_nas_service.py` with all tests
- [ ] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [ ] Run `uv run pytest tests/unit/test_nas_service.py -v`

## Notes

- NAS services use **integer keys** (unlike other NAS resources which use 40-char hex keys)
- Service creation is slow — the SDK polls for availability (up to 15 attempts, 2s intervals)
- Memory is stored in MB internally but the CLI accepts GB (multiply by 1024)
- CIFS and NFS settings are separate API endpoints, not part of the service object
- `read_ahead_kb` only accepts specific values: 0, 64, 128, 256, 512, 1024, 2048, 4096
- The `nas.py` parent app is just a wiring file — it imports and registers `nas_service.app` (and later, other NAS sub-commands from 4b-4f)
