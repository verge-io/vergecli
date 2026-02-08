# Phase 4d: NAS Users Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas user` commands for NAS local user management
**Depends on:** Phase 4a (NAS Services)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add NAS local user management for CIFS/SMB authentication. NAS users are local accounts managed per NAS service, used for share access control. The SDK exposes users via `client.nas_users` (NASUserManager).

NAS users use **40-character hex string keys** and the `resolve_nas_resource()` utility from Phase 4b.

## Commands

```
vrg nas user list [--service SERVICE] [--enabled | --disabled]
vrg nas user get <USER>
vrg nas user create --service SERVICE --name NAME --password PASSWORD [--displayname DISPLAY] [--description DESC] [--home-share SHARE] [--home-drive LETTER]
vrg nas user update <USER> [--password PASSWORD] [--displayname DISPLAY] [--description DESC] [--home-share SHARE] [--home-drive LETTER]
vrg nas user delete <USER> [--yes]
vrg nas user enable <USER>
vrg nas user disable <USER>
```

### Command Details

#### `list`
- Options:
  - `--service` (str, optional) — filter by NAS service name or key
  - `--enabled / --disabled` (optional) — filter by enabled state
- SDK: `client.nas_users.list(service=service, enabled=enabled)`

#### `get`
- Positional: `USER` (name or hex key)
- Note: get by name requires service context in SDK (`get(name=name, service=service)`) — if no --service provided and name lookup is ambiguous, raise error
- SDK: `client.nas_users.get(key=key)` or `get(name=name, service=service)`
- Uses `resolve_nas_resource()`

#### `create`
- Required: `--service`, `--name`, `--password`
- Options:
  - `--service` (str, required) — NAS service name or key
  - `--name / -n` (str, required) — username
  - `--password` (str, required) — user password (8+ chars, complexity requirements)
  - `--displayname` (str, optional) — display name
  - `--description / -d` (str, optional)
  - `--home-share` (str, optional) — home share name or key
  - `--home-drive` (str, optional) — drive letter (single uppercase letter, e.g., "H")
- SDK: `client.nas_users.create(service=..., name=..., password=..., displayname=..., description=..., home_share=..., home_drive=...)`

#### `update`
- Positional: `USER` (name or hex key)
- Options: same as create minus --service and --name
- SDK: `client.nas_users.update(key, ...)`

#### `delete`
- Positional: `USER`
- Options: `--yes / -y`
- SDK: `client.nas_users.delete(key)`

#### `enable` / `disable`
- Positional: `USER`
- SDK: `client.nas_users.enable(key)` / `disable(key)`

## Files

### New Files

1. **`src/verge_cli/commands/nas_user.py`**
   - Helpers: `_user_to_dict()`
   - Commands: list, get, create, update, delete, enable, disable

2. **`tests/unit/test_nas_user.py`**
   - Fixture: `mock_nas_user` — MagicMock with key="aabbcc...(40)", name="nasadmin", displayname="NAS Admin", enabled=True, service_name="nas01"
   - Tests: see test plan

### Modified Files

3. **`src/verge_cli/commands/nas.py`**
   - Add: `from verge_cli.commands import nas_user`
   - Add: `app.add_typer(nas_user.app, name="user")`

4. **`tests/conftest.py`**
   - Add fixture: `mock_nas_user`

## Column Definitions

```python
NAS_USER_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("displayname", header="Display Name"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map={"Yes": "green", "No": "red"}),
    ColumnDef("service_name", header="Service"),
    ColumnDef("status", style_map={"online": "green", "offline": "red", "error": "yellow"}),
    ColumnDef("home_share_name", header="Home Share", wide_only=True),
    ColumnDef("home_drive", header="Drive", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _user_to_dict(user: Any) -> dict[str, Any]:
    return {
        "$key": user.key,
        "name": user.name,
        "displayname": user.get("displayname", ""),
        "enabled": user.get("enabled"),
        "service_name": user.get("service_name"),
        "status": user.get("status"),
        "home_share_name": user.get("home_share_name"),
        "home_drive": user.get("home_drive"),
        "description": user.get("description", ""),
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_user_list` | Lists all NAS users |
| 2 | `test_user_list_by_service` | Filter by --service |
| 3 | `test_user_list_enabled` | Filter by --enabled |
| 4 | `test_user_get` | Get by name resolution |
| 5 | `test_user_get_by_hex_key` | Get by 40-char hex key |
| 6 | `test_user_create` | Create with required args (service, name, password) |
| 7 | `test_user_create_with_options` | Create with --displayname, --home-share, --home-drive |
| 8 | `test_user_update` | Update password and displayname |
| 9 | `test_user_delete` | Delete with --yes |
| 10 | `test_user_enable` | Enable user |
| 11 | `test_user_disable` | Disable user |
| 12 | `test_user_not_found` | Name resolution error (exit 6) |

## Task Checklist

- [x] Create `src/verge_cli/commands/nas_user.py` with all commands
- [x] Register sub-typer in `nas.py`
- [x] Add `mock_nas_user` fixture to `conftest.py`
- [x] Create `tests/unit/test_nas_user.py` with all tests
- [x] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [x] Run `uv run pytest tests/unit/test_nas_user.py -v`

## Notes

- User keys are 40-char hex strings
- Password has complexity requirements (8+ chars) — enforced by the API, not the CLI
- Home drive is a single uppercase letter (e.g., "H") — no CLI-side validation needed, API handles it
- Get by name requires service context in the SDK — the CLI should pass `--service` if looking up by name, or use `resolve_nas_resource()` which lists all and filters
- User status values: "online" (Enabled), "offline" (Disabled), "error"
- Service resolution for `--service` uses existing `resolve_resource_id()` (services use int keys)
