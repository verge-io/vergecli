# Phase 4c: NAS CIFS & NFS Shares Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas cifs` and `vrg nas nfs` commands for share management
**Depends on:** Phase 4b (NAS Volumes)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add CIFS (SMB) and NFS share management as separate command groups under `vrg nas`. CIFS and NFS shares have significantly different options so they are implemented as separate sub-commands rather than a unified `share` command. The SDK exposes shares via `client.cifs_shares` (NASCIFSShareManager) and `client.nfs_shares` (NASNFSShareManager).

Both share types use **40-character hex string keys** and the `resolve_nas_resource()` utility from Phase 4b.

## Commands

### CIFS Shares
```
vrg nas cifs list [--volume VOLUME] [--enabled | --disabled]
vrg nas cifs get <SHARE>
vrg nas cifs create --name NAME --volume VOLUME [--share-path PATH] [--description DESC] [--comment COMMENT] [--browseable | --no-browseable] [--read-only] [--guest-ok] [--guest-only] [--force-user USER] [--force-group GROUP] [--valid-users USERS] [--valid-groups GROUPS] [--admin-users USERS] [--admin-groups GROUPS] [--allowed-hosts HOSTS] [--denied-hosts HOSTS] [--shadow-copy]
vrg nas cifs update <SHARE> [--description DESC] [--comment COMMENT] [--browseable | --no-browseable] [--read-only | --no-read-only] [--guest-ok | --no-guest-ok] [--guest-only | --no-guest-only] [--force-user USER] [--force-group GROUP] [--valid-users USERS] [--valid-groups GROUPS] [--admin-users USERS] [--admin-groups GROUPS] [--allowed-hosts HOSTS] [--denied-hosts HOSTS] [--shadow-copy | --no-shadow-copy]
vrg nas cifs delete <SHARE> [--yes]
vrg nas cifs enable <SHARE>
vrg nas cifs disable <SHARE>
```

### NFS Shares
```
vrg nas nfs list [--volume VOLUME] [--enabled | --disabled]
vrg nas nfs get <SHARE>
vrg nas nfs create --name NAME --volume VOLUME [--share-path PATH] [--description DESC] [--allowed-hosts HOSTS] [--allow-all] [--data-access MODE] [--squash MODE] [--anon-uid UID] [--anon-gid GID] [--async] [--insecure] [--no-acl] [--filesystem-id FSID]
vrg nas nfs update <SHARE> [--description DESC] [--allowed-hosts HOSTS] [--allow-all | --no-allow-all] [--data-access MODE] [--squash MODE] [--anon-uid UID] [--anon-gid GID] [--async | --no-async] [--insecure | --no-insecure] [--no-acl | --acl] [--filesystem-id FSID]
vrg nas nfs delete <SHARE> [--yes]
vrg nas nfs enable <SHARE>
vrg nas nfs disable <SHARE>
```

### Command Details

#### CIFS `list`
- Options:
  - `--volume` (str, optional) — filter by volume name or key
  - `--enabled / --disabled` (optional) — filter by enabled state
- SDK: `client.cifs_shares.list(volume=volume, enabled=enabled)`

#### CIFS `get`
- Positional: `SHARE` (name or hex key)
- SDK: `client.cifs_shares.get(key=key)` or `get(name=name, volume=volume)`
- Uses `resolve_nas_resource()`

#### CIFS `create`
- Required: `--name`, `--volume`
- Options:
  - `--share-path` (str, optional) — path within volume (default: root)
  - `--description / -d` (str, optional)
  - `--comment` (str, optional) — share comment visible to clients
  - `--browseable / --no-browseable` (bool, default True)
  - `--read-only` (flag, default False)
  - `--guest-ok` (flag, default False)
  - `--guest-only` (flag, default False)
  - `--force-user` (str, optional) — force file operations as user
  - `--force-group` (str, optional)
  - `--valid-users` (str, optional) — comma-separated user list
  - `--valid-groups` (str, optional) — comma-separated group list
  - `--admin-users` (str, optional) — comma-separated admin user list
  - `--admin-groups` (str, optional) — comma-separated admin group list
  - `--allowed-hosts` (str, optional) — comma-separated host/CIDR list
  - `--denied-hosts` (str, optional) — comma-separated denied host list
  - `--shadow-copy` (flag, default False) — enable shadow copy (vfs_shadow_copy2)
- SDK: `client.cifs_shares.create(name=..., volume=..., ...)`
- List fields (valid_users, etc.): split comma-separated CLI input into Python lists for SDK

#### CIFS `update`
- Positional: `SHARE` (name or hex key)
- Same options as create minus --name and --volume
- SDK: `client.cifs_shares.update(key, ...)`

#### CIFS `delete`
- Positional: `SHARE`
- Options: `--yes / -y`
- SDK: `client.cifs_shares.delete(key)`
- Note: Data is retained on volume, only share definition removed

#### CIFS `enable` / `disable`
- SDK: `client.cifs_shares.enable(key)` / `disable(key)`

#### NFS `list`
- Options: `--volume` (str, optional), `--enabled / --disabled` (optional)
- SDK: `client.nfs_shares.list(volume=volume, enabled=enabled)`

#### NFS `get`
- Positional: `SHARE` (name or hex key)
- SDK: `client.nfs_shares.get(key=key)` or `get(name=name)`

#### NFS `create`
- Required: `--name`, `--volume`
- Options:
  - `--share-path` (str, optional)
  - `--description / -d` (str, optional)
  - `--allowed-hosts` (str, optional) — comma-separated host/CIDR list (required if not --allow-all)
  - `--allow-all` (flag, default False)
  - `--data-access` (str, default "ro") — "ro" or "rw"
  - `--squash` (str, default "root_squash") — "root_squash", "all_squash", "no_root_squash"
  - `--anon-uid` (int, optional)
  - `--anon-gid` (int, optional)
  - `--async` (flag, default False)
  - `--insecure` (flag, default False)
  - `--no-acl` (flag, default False)
  - `--filesystem-id` (str, optional) — custom fsid
- SDK: `client.nfs_shares.create(name=..., volume=..., ...)`
- Note: requires either --allowed-hosts or --allow-all

#### NFS `update`
- Positional: `SHARE` (name or hex key)
- Same options as create minus --name and --volume
- SDK: `client.nfs_shares.update(key, ...)`

#### NFS `delete`, `enable`, `disable`
- Same pattern as CIFS

## Files

### New Files

1. **`src/verge_cli/commands/nas_cifs.py`**
   - Helpers: `_cifs_share_to_dict()`, `_split_list()` (comma-split helper)
   - Commands: list, get, create, update, delete, enable, disable

2. **`src/verge_cli/commands/nas_nfs.py`**
   - Helpers: `_nfs_share_to_dict()`
   - Commands: list, get, create, update, delete, enable, disable

3. **`tests/unit/test_nas_cifs.py`**
   - Fixture: `mock_cifs_share` — MagicMock with key="abc123...(40)", name="users", volume_name="UserData", browseable=True
   - Tests: see test plan

4. **`tests/unit/test_nas_nfs.py`**
   - Fixture: `mock_nfs_share` — MagicMock with key="def456...(40)", name="linuxapps", volume_name="LinuxApps", data_access="rw"
   - Tests: see test plan

### Modified Files

5. **`src/verge_cli/commands/nas.py`**
   - Add: `from verge_cli.commands import nas_cifs, nas_nfs`
   - Add: `app.add_typer(nas_cifs.app, name="cifs")`
   - Add: `app.add_typer(nas_nfs.app, name="nfs")`

6. **`tests/conftest.py`**
   - Add fixtures: `mock_cifs_share`, `mock_nfs_share`

## Column Definitions

```python
# In nas_cifs.py
NAS_CIFS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("volume_name", header="Volume"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("browseable", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("read_only", header="Read Only", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("guest_ok", header="Guest OK", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("shadow_copy_enabled", header="Shadow Copy", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("description", wide_only=True),
]

# In nas_nfs.py
NAS_NFS_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("volume_name", header="Volume"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("data_access", header="Access"),
    ColumnDef("squash"),
    ColumnDef("allowed_hosts", header="Allowed Hosts", wide_only=True),
    ColumnDef("allow_all", header="Allow All", format_fn=format_bool_yn, wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _cifs_share_to_dict(share: Any) -> dict[str, Any]:
    return {
        "$key": share.key,
        "name": share.name,
        "volume_name": share.get("volume_name"),
        "enabled": share.get("enabled"),
        "browseable": share.get("browseable"),
        "read_only": share.get("read_only"),
        "guest_ok": share.get("guest_ok"),
        "shadow_copy_enabled": share.get("shadow_copy_enabled"),
        "share_path": share.get("share_path"),
        "description": share.get("description", ""),
    }

def _nfs_share_to_dict(share: Any) -> dict[str, Any]:
    return {
        "$key": share.key,
        "name": share.name,
        "volume_name": share.get("volume_name"),
        "enabled": share.get("enabled"),
        "data_access": share.get("data_access"),
        "squash": share.get("squash"),
        "allowed_hosts": share.get("allowed_hosts"),
        "allow_all": share.get("allow_all"),
        "description": share.get("description", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_cifs_list` | Lists all CIFS shares |
| 2 | `test_cifs_list_by_volume` | Filter by --volume |
| 3 | `test_cifs_get` | Get by name |
| 4 | `test_cifs_get_by_hex_key` | Get by hex key |
| 5 | `test_cifs_create` | Create with required args |
| 6 | `test_cifs_create_with_users` | Create with --valid-users, --admin-users (comma-separated) |
| 7 | `test_cifs_create_with_shadow_copy` | Create with --shadow-copy |
| 8 | `test_cifs_update` | Update description and read-only |
| 9 | `test_cifs_delete` | Delete with --yes |
| 10 | `test_cifs_enable` | Enable share |
| 11 | `test_nfs_list` | Lists all NFS shares |
| 12 | `test_nfs_list_by_volume` | Filter by --volume |
| 13 | `test_nfs_get` | Get by name |
| 14 | `test_nfs_create` | Create with --allowed-hosts |
| 15 | `test_nfs_create_allow_all` | Create with --allow-all |
| 16 | `test_nfs_create_with_squash` | Create with --squash, --data-access |
| 17 | `test_nfs_update` | Update data-access and squash |
| 18 | `test_nfs_delete` | Delete with --yes |
| 19 | `test_nfs_enable` | Enable share |
| 20 | `test_nfs_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Create `src/verge_cli/commands/nas_cifs.py` with all commands
- [x] Create `src/verge_cli/commands/nas_nfs.py` with all commands
- [x] Register sub-typers in `nas.py`
- [x] Add fixtures to `conftest.py`
- [x] Create `tests/unit/test_nas_cifs.py`
- [x] Create `tests/unit/test_nas_nfs.py`
- [x] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [x] Run `uv run pytest tests/unit/test_nas_cifs.py tests/unit/test_nas_nfs.py -v`

## Notes

- CIFS and NFS have very different option sets — CIFS has guest access, shadow copy, user/group lists; NFS has squash modes, fsid, data access modes
- List fields (valid_users, admin_users, allowed_hosts, denied_hosts) are comma-separated in CLI input, split into Python lists for SDK. The API stores them as newline-delimited strings but the SDK handles the conversion.
- CIFS `delete` retains data on the volume — only the share definition is removed
- NFS `create` requires either `--allowed-hosts` or `--allow-all` — validate this in the CLI before calling SDK
- Volume resolution for `--volume` option uses `resolve_nas_resource()` from Phase 4b
- Share keys are 40-char hex strings
