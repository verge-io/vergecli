# Phase 5b: Permissions & API Keys Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg permission` and `vrg api-key` commands for access control
**Dependencies:** Phase 5a (user/group commands exist for context)
**Task Checklist:** Bottom of file — `tail -25` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Permissions | `permissions` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/permissions.py` |
| API Keys | `api_keys` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/api_keys.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/user_management_example.py`

---

## Overview

Add permission and API key management commands. These are access control primitives — permissions grant resource access to users/groups, while API keys provide programmatic authentication. Both have non-standard CRUD patterns: permissions use grant/revoke instead of create/delete, and API keys have a unique secret-on-create model with no update operation.

## Commands

### `vrg permission`

```
vrg permission list [--user USER] [--group GROUP] [--table TABLE] [--filter ODATA]
vrg permission get <ID>
vrg permission grant --table TABLE [--user USER | --group GROUP] [--row ROW_KEY] [--list] [--read] [--create] [--modify] [--delete] [--full-control]
vrg permission revoke <ID> [--yes]
vrg permission revoke-all --user USER | --group GROUP [--table TABLE] [--yes]
```

### `vrg api-key`

```
vrg api-key list [--user USER] [--filter ODATA]
vrg api-key get <ID|NAME> [--user USER]
vrg api-key create --user USER --name NAME [--description DESC] [--expires-in DURATION] [--ip-allow IP,...] [--ip-deny IP,...]
vrg api-key delete <ID|NAME> [--yes]
```

### Command Details

#### `vrg permission list`

- Options:
  - `--user` (str) — filter by user (name or key)
  - `--group` (str) — filter by group (name or key)
  - `--table` (str) — filter by resource table (e.g., `vms`, `vnets`, `/`)
  - `--filter` (str) — OData filter
- Resolve `--user` to user key via `resolve_resource_id()`, then pass to SDK
- Resolve `--group` to group key via `resolve_resource_id()`, then pass to SDK
- SDK: `permissions.list(user=user_key, group=group_key, table=table)`

#### `vrg permission get`

- Positional: `ID` (numeric key only — permissions don't have names)
- SDK: `permissions.get(key)`

#### `vrg permission grant`

- Required: `--table TABLE`
- Must specify exactly one of: `--user USER` or `--group GROUP`
- Optional flags: `--list`, `--read`, `--create`, `--modify`, `--delete`, `--full-control`
- `--full-control` overrides individual flags
- `--row ROW_KEY` (int, default 0) — 0 means table-level, non-zero for specific resource
- Resolve `--user` / `--group` via `resolve_resource_id()`
- If no permission flags given, default to `--list` only
- SDK: `permissions.grant(table=..., user=user_key, group=group_key, row_key=..., can_list=..., can_read=..., can_create=..., can_modify=..., can_delete=..., full_control=...)`
- Output: the created permission in table format

#### `vrg permission revoke`

- Positional: `ID` (permission key)
- `--yes / -y` — skip confirmation
- SDK: `permissions.revoke(key)`

#### `vrg permission revoke-all`

- Must specify exactly one of: `--user USER` or `--group GROUP`
- Optional: `--table TABLE` — revoke only for that table
- `--yes / -y` — skip confirmation
- Resolve `--user` / `--group` via `resolve_resource_id()`
- SDK: `permissions.revoke_for_user(user_key, table=table)` or `permissions.revoke_for_group(group_key, table=table)`
- Output: count of revoked permissions

#### `vrg api-key list`

- Options:
  - `--user` (str) — filter by user (name or key)
  - `--filter` (str) — OData filter
- SDK: `api_keys.list(user=user)`

#### `vrg api-key get`

- Positional: `API_KEY` (name or numeric key)
- `--user` (str) — required when looking up by name (API key names are per-user)
- SDK: `api_keys.get(key)` or `api_keys.get(name=name, user=user)`

#### `vrg api-key create`

- Required: `--user USER`, `--name NAME`
- Optional:
  - `--description` (str)
  - `--expires-in` (str, e.g. `30d`, `1w`, `3m`, `1y`, `never`)
  - `--ip-allow` (str, comma-separated IPs/CIDRs)
  - `--ip-deny` (str, comma-separated IPs/CIDRs)
- Parse `--ip-allow` / `--ip-deny` from comma-separated string to list
- SDK: `api_keys.create(user=user, name=name, description=..., expires_in=..., ip_allow_list=..., ip_deny_list=...)`
- **IMPORTANT**: Output must include the `secret` field from `APIKeyCreated` response — this is the only time the secret is shown
- Display secret prominently with a warning message

#### `vrg api-key delete`

- Positional: `API_KEY` (name or numeric key)
- `--yes / -y` — skip confirmation
- SDK: `api_keys.delete(key)`
- Warning: permanent deletion, cannot be undone

## Files

### New Files

1. **`src/verge_cli/commands/permission.py`**
   - Typer app with: list, get, grant, revoke, revoke-all
   - Helper: `_permission_to_dict(perm)` — convert SDK Permission to output dict
   - Helper: `_resolve_identity()` — resolve --user / --group to key, validate mutual exclusion
   - Uses `resolve_resource_id()` for user/group resolution

2. **`src/verge_cli/commands/api_key.py`**
   - Typer app with: list, get, create, delete
   - Helper: `_api_key_to_dict(key)` — convert SDK APIKey to output dict
   - Helper: `_api_key_created_to_dict(result)` — include secret in output
   - Special output for create: show secret with warning

3. **`tests/unit/test_permission.py`**

4. **`tests/unit/test_api_key.py`**

### Modified Files

5. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import permission, api_key`
   - Add: `app.add_typer(permission.app, name="permission")`
   - Add: `app.add_typer(api_key.app, name="api-key")`

6. **`src/verge_cli/columns.py`**
   - Add `PERMISSION_COLUMNS`, `API_KEY_COLUMNS`

7. **`tests/conftest.py`**
   - Add `mock_permission`, `mock_api_key`, `mock_api_key_created` fixtures

## Column Definitions

```python
PERMISSION_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("identity_name", header="Identity"),
    ColumnDef("table"),
    ColumnDef("row_display", header="Resource"),
    ColumnDef("can_list", header="List", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("can_read", header="Read", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("can_create", header="Create", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("can_modify", header="Modify", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("can_delete", header="Delete", format_fn=format_bool_yn, style_map=BOOL_STYLES),
]

API_KEY_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("user_name", header="User"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    ColumnDef("is_expired", header="Expired", format_fn=format_bool_yn, style_map=FLAG_STYLES),
    # wide-only
    ColumnDef("last_login", format_fn=format_epoch, wide_only=True),
    ColumnDef("last_login_ip", header="Last IP", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _permission_to_dict(perm: Any) -> dict[str, Any]:
    return {
        "$key": int(perm.key),
        "identity_name": perm.identity_name,
        "table": perm.table,
        "row_key": perm.row_key,
        "row_display": perm.row_display if perm.row_key != 0 else "(all)",
        "is_table_level": perm.is_table_level,
        "can_list": perm.can_list,
        "can_read": perm.can_read,
        "can_create": perm.can_create,
        "can_modify": perm.can_modify,
        "can_delete": perm.can_delete,
        "has_full_control": perm.has_full_control,
    }

def _api_key_to_dict(key_obj: Any) -> dict[str, Any]:
    return {
        "$key": int(key_obj.key),
        "name": key_obj.name,
        "user_name": key_obj.user_name,
        "description": key_obj.get("description", ""),
        "created": key_obj.get("created"),
        "expires": key_obj.get("expires"),
        "is_expired": key_obj.is_expired,
        "last_login": key_obj.get("last_login"),
        "last_login_ip": key_obj.get("last_login_ip", ""),
        "ip_allow_list": key_obj.ip_allow_list,
        "ip_deny_list": key_obj.ip_deny_list,
    }

def _api_key_created_to_dict(result: Any) -> dict[str, Any]:
    return {
        "$key": int(result.key),
        "name": result.name,
        "user_name": result.user_name,
        "secret": result.secret,
    }
```

## Special Output: API Key Creation

When an API key is created, the secret is shown only once. Use a special output flow:

```python
result = vctx.client.api_keys.create(...)
output_result(
    _api_key_created_to_dict(result),
    columns=API_KEY_CREATED_COLUMNS,
    output_format=vctx.output_format,
    ...
)
output_warning(
    "Store this secret securely — it cannot be retrieved again.",
    quiet=vctx.quiet,
)
```

Define a minimal `API_KEY_CREATED_COLUMNS` for the create response:

```python
API_KEY_CREATED_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("user_name", header="User"),
    ColumnDef("secret"),
]
```

## Test Plan

### Permission Tests (`test_permission.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_permission_list` | Lists all permissions |
| 2 | `test_permission_list_by_user` | `--user` filter resolves and passes |
| 3 | `test_permission_list_by_group` | `--group` filter resolves and passes |
| 4 | `test_permission_list_by_table` | `--table vms` filter |
| 5 | `test_permission_get` | Get by numeric key |
| 6 | `test_permission_grant_user` | Grant to user with flags |
| 7 | `test_permission_grant_group` | Grant to group |
| 8 | `test_permission_grant_full_control` | `--full-control` flag |
| 9 | `test_permission_grant_specific_row` | `--row 42` for specific resource |
| 10 | `test_permission_revoke` | Revoke single permission with --yes |
| 11 | `test_permission_revoke_no_confirm` | Revoke without --yes aborts |
| 12 | `test_permission_revoke_all_user` | Revoke all for a user |
| 13 | `test_permission_revoke_all_group_table` | Revoke all for group on specific table |

### API Key Tests (`test_api_key.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_api_key_list` | Lists API keys |
| 2 | `test_api_key_list_by_user` | `--user` filter |
| 3 | `test_api_key_get_by_key` | Get by numeric key |
| 4 | `test_api_key_get_by_name` | Get by name with `--user` |
| 5 | `test_api_key_create` | Basic create, verify secret in output |
| 6 | `test_api_key_create_with_options` | All optional flags |
| 7 | `test_api_key_create_ip_lists` | `--ip-allow`, `--ip-deny` parsing |
| 8 | `test_api_key_delete` | Delete with --yes |
| 9 | `test_api_key_delete_no_confirm` | Delete without --yes aborts |

## Test Fixtures

```python
@pytest.fixture
def mock_permission() -> MagicMock:
    perm = MagicMock()
    perm.key = 50
    perm.identity_name = "admin"
    perm.table = "vms"
    perm.row_key = 0
    perm.row_display = ""
    perm.is_table_level = True
    perm.can_list = True
    perm.can_read = True
    perm.can_create = False
    perm.can_modify = False
    perm.can_delete = False
    perm.has_full_control = False
    return perm

@pytest.fixture
def mock_api_key() -> MagicMock:
    key = MagicMock()
    key.key = 60
    key.name = "automation"
    key.user_name = "admin"
    key.is_expired = False
    key.ip_allow_list = []
    key.ip_deny_list = []

    def mock_get(attr: str, default: Any = None) -> Any:
        data = {
            "description": "Automation key",
            "created": 1707100000,
            "expires": 0,
            "last_login": 1707200000,
            "last_login_ip": "192.168.1.100",
        }
        return data.get(attr, default)

    key.get = mock_get
    return key

@pytest.fixture
def mock_api_key_created() -> MagicMock:
    result = MagicMock()
    result.key = 61
    result.name = "new-key"
    result.user_name = "admin"
    result.secret = "vrg_sk_abc123def456ghi789"
    return result
```

## Task Checklist

- [x] Add `PERMISSION_COLUMNS`, `API_KEY_COLUMNS`, `API_KEY_CREATED_COLUMNS` to `columns.py`
- [x] Add `mock_permission`, `mock_api_key`, `mock_api_key_created` fixtures to `conftest.py`
- [x] Create `permission.py` with all commands (list, get, grant, revoke, revoke-all)
- [x] Create `api_key.py` with all commands (list, get, create, delete)
- [x] Register both in `cli.py`
- [x] Create `test_permission.py` with all tests
- [x] Create `test_api_key.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
