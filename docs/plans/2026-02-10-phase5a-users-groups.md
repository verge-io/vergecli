# Phase 5a: Users & Groups Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg user` and `vrg group` commands for identity management
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -30` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Users | `users` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/users.py` |
| Groups | `groups` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/groups.py` |
| Group members | `groups.members(key)` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/groups.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/user_management_example.py`

---

## Overview

Add user and group management commands. Users and groups are the foundation of VergeOS IAM — groups contain users (and nested groups) via a sub-resource member manager. Both support enable/disable operations.

## Commands

### `vrg user`

```
vrg user list [--filter ODATA] [--enabled | --disabled] [--type normal|api|vdi]
vrg user get <ID|NAME>
vrg user create --name NAME --password PASSWORD [--displayname DISPLAY] [--email EMAIL] [--type normal|api|vdi] [--disabled] [--change-password] [--physical-access] [--two-factor] [--two-factor-type email|totp] [--ssh-keys KEYS]
vrg user update <ID|NAME> [--displayname DISPLAY] [--email EMAIL] [--password PASSWORD] [--change-password BOOL] [--physical-access BOOL] [--two-factor BOOL] [--two-factor-type email|totp] [--ssh-keys KEYS]
vrg user delete <ID|NAME> [--yes]
vrg user enable <ID|NAME>
vrg user disable <ID|NAME>
```

### `vrg group`

```
vrg group list [--filter ODATA] [--enabled | --disabled]
vrg group get <ID|NAME>
vrg group create --name NAME [--description DESC] [--email EMAIL] [--disabled]
vrg group update <ID|NAME> [--name NAME] [--description DESC] [--email EMAIL]
vrg group delete <ID|NAME> [--yes]
vrg group enable <ID|NAME>
vrg group disable <ID|NAME>
vrg group member list <GROUP>
vrg group member add <GROUP> --user <USER> | --group <MEMBER_GROUP>
vrg group member remove <GROUP> --user <USER> | --group <MEMBER_GROUP>
```

### Command Details

#### `vrg user list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--enabled` (flag) — show only enabled users
  - `--disabled` (flag) — show only disabled users (mutually exclusive with --enabled)
  - `--type` (str, choices: normal/api/vdi) — filter by user type
- SDK: `users.list(enabled=..., user_type=...)` or `users.list_enabled()` / `users.list_disabled()` / `users.list_api_users()` / `users.list_vdi_users()`

#### `vrg user get`

- Positional: `USER` (name or key)
- SDK: `users.get(key)` after `resolve_resource_id()`

#### `vrg user create`

- Required: `--name`, `--password`
- Optional: `--displayname`, `--email`, `--type` (default: normal), `--disabled` (flag, default enabled), `--change-password` (flag), `--physical-access` (flag), `--two-factor` (flag), `--two-factor-type` (default: email), `--ssh-keys` (str, newline-separated or comma-separated)
- Note: email is required if enabling 2FA — validate and error early
- SDK: `users.create(name=..., password=..., displayname=..., email=..., user_type=..., enabled=..., change_password=..., physical_access=..., two_factor_enabled=..., two_factor_type=..., ssh_keys=...)`

#### `vrg user update`

- Positional: `USER` (name or key)
- All fields optional (only send what's provided)
- SDK: `users.update(key, ...)`

#### `vrg user delete`

- Positional: `USER` (name or key)
- `--yes / -y` skips confirmation
- SDK: `users.delete(key)` after confirmation

#### `vrg user enable` / `vrg user disable`

- Positional: `USER` (name or key)
- SDK: `users.enable(key)` / `users.disable(key)`
- Output success message with user name

#### `vrg group list`

- Options: `--filter`, `--enabled`, `--disabled` (mutually exclusive flags)
- SDK: `groups.list(enabled=...)` or convenience methods

#### `vrg group get`

- Positional: `GROUP` (name or key)
- SDK: `groups.get(key)`

#### `vrg group create`

- Required: `--name`
- Optional: `--description`, `--email`, `--disabled` (flag)
- SDK: `groups.create(name=..., description=..., email=..., enabled=...)`

#### `vrg group update`

- Positional: `GROUP` (name or key)
- Optional: `--name`, `--description`, `--email`
- SDK: `groups.update(key, ...)`

#### `vrg group delete`

- Positional: `GROUP` (name or key), `--yes / -y`
- SDK: `groups.delete(key)` after confirmation

#### `vrg group enable` / `vrg group disable`

- Positional: `GROUP` (name or key)
- SDK: `groups.enable(key)` / `groups.disable(key)`

#### `vrg group member list`

- Positional: `GROUP` (name or key)
- SDK: `groups.members(group_key).list()`
- Shows member name, type (User/Group), and key

#### `vrg group member add`

- Positional: `GROUP` (name or key)
- Must specify exactly one of: `--user USER` or `--group MEMBER_GROUP`
- Resolve both the parent group and the member (user or group) by name/key
- SDK: `groups.members(group_key).add_user(user_key)` or `.add_group(member_group_key)`

#### `vrg group member remove`

- Positional: `GROUP` (name or key)
- Must specify exactly one of: `--user USER` or `--group MEMBER_GROUP`
- SDK: `groups.members(group_key).remove_user(user_key)` or `.remove_group(member_group_key)`

## Files

### New Files

1. **`src/verge_cli/commands/user.py`**
   - Typer app with: list, get, create, update, delete, enable, disable
   - Helper: `_user_to_dict(user)` — convert SDK User to output dict
   - Pattern: follow `vm.py` for CRUD + enable/disable

2. **`src/verge_cli/commands/group.py`**
   - Typer app with: list, get, create, update, delete, enable, disable
   - Sub-Typer `member_app` with: list, add, remove
   - Helper: `_group_to_dict(group)` — convert SDK Group to output dict
   - Helper: `_member_to_dict(member)` — convert SDK GroupMember to output dict
   - Register: `app.add_typer(member_app, name="member")`

3. **`tests/unit/test_user.py`**

4. **`tests/unit/test_group.py`**

### Modified Files

5. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import user, group`
   - Add: `app.add_typer(user.app, name="user")`
   - Add: `app.add_typer(group.app, name="group")`

6. **`src/verge_cli/columns.py`**
   - Add `USER_COLUMNS`, `GROUP_COLUMNS`, `GROUP_MEMBER_COLUMNS`

7. **`tests/conftest.py`**
   - Add `mock_user`, `mock_group`, `mock_group_member` fixtures

## Column Definitions

```python
USER_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("displayname", header="Display Name"),
    ColumnDef("email"),
    ColumnDef("user_type", header="Type"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    # wide-only
    ColumnDef("last_login", format_fn=format_epoch, wide_only=True),
    ColumnDef("two_factor_enabled", header="2FA", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("is_locked", header="Locked", format_fn=format_bool_yn, style_map=FLAG_STYLES, wide_only=True),
    ColumnDef("auth_source_name", header="Auth Source", wide_only=True),
]

GROUP_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description"),
    ColumnDef("email"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("member_count", header="Members"),
    # wide-only
    ColumnDef("created", format_fn=format_epoch, wide_only=True),
]

GROUP_MEMBER_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("member_name", header="Name"),
    ColumnDef("member_type", header="Type"),
    ColumnDef("member_key", header="Member Key"),
]
```

## Data Mapping

```python
def _user_to_dict(user: Any) -> dict[str, Any]:
    return {
        "$key": int(user.key),
        "name": user.name,
        "displayname": user.get("displayname", ""),
        "email": user.get("email", ""),
        "user_type": user.get("user_type_display", user.get("user_type", "")),
        "enabled": user.is_enabled,
        "last_login": user.get("last_login"),
        "two_factor_enabled": user.get("two_factor_enabled", False),
        "is_locked": user.get("is_locked", False),
        "auth_source_name": user.get("auth_source_name", ""),
        "created": user.get("created"),
        "ssh_keys": user.get("ssh_keys", ""),
    }

def _group_to_dict(group: Any) -> dict[str, Any]:
    return {
        "$key": int(group.key),
        "name": group.name,
        "description": group.get("description", ""),
        "email": group.get("email", ""),
        "enabled": group.is_enabled,
        "member_count": group.get("member_count", 0),
        "created": group.get("created"),
    }

def _member_to_dict(member: Any) -> dict[str, Any]:
    return {
        "$key": int(member.key),
        "member_name": member.member_name,
        "member_type": member.member_type,
        "member_key": int(member.member_key),
    }
```

## Test Plan

### User Tests (`test_user.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_user_list` | Lists users, default output |
| 2 | `test_user_list_enabled` | `--enabled` flag filters |
| 3 | `test_user_list_disabled` | `--disabled` flag filters |
| 4 | `test_user_list_by_type` | `--type api` filter |
| 5 | `test_user_get` | Get by name resolution |
| 6 | `test_user_get_by_key` | Get by numeric key |
| 7 | `test_user_create` | Basic create with name + password |
| 8 | `test_user_create_with_options` | All optional flags |
| 9 | `test_user_update` | Update displayname, email |
| 10 | `test_user_delete` | Delete with --yes |
| 11 | `test_user_delete_no_confirm` | Delete without --yes aborts |
| 12 | `test_user_enable` | Enable a disabled user |
| 13 | `test_user_disable` | Disable an enabled user |
| 14 | `test_user_not_found` | Name resolution error (exit 6) |

### Group Tests (`test_group.py`)

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_group_list` | Lists groups |
| 2 | `test_group_list_enabled` | `--enabled` filter |
| 3 | `test_group_get` | Get by name |
| 4 | `test_group_create` | Basic create |
| 5 | `test_group_create_with_options` | All optional flags |
| 6 | `test_group_update` | Update name, description |
| 7 | `test_group_delete` | Delete with --yes |
| 8 | `test_group_enable` | Enable group |
| 9 | `test_group_disable` | Disable group |
| 10 | `test_group_member_list` | List members of a group |
| 11 | `test_group_member_add_user` | Add user to group |
| 12 | `test_group_member_add_group` | Add nested group |
| 13 | `test_group_member_remove_user` | Remove user from group |
| 14 | `test_group_member_remove_group` | Remove nested group |
| 15 | `test_group_not_found` | Name resolution error (exit 6) |

## Test Fixtures

```python
@pytest.fixture
def mock_user() -> MagicMock:
    user = MagicMock()
    user.key = 10
    user.name = "admin"
    user.is_enabled = True

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "displayname": "Administrator",
            "email": "admin@example.com",
            "user_type": "normal",
            "user_type_display": "Normal",
            "two_factor_enabled": False,
            "is_locked": False,
            "auth_source_name": "",
            "last_login": 1707100000,
            "created": 1707000000,
            "ssh_keys": "",
        }
        return data.get(key, default)

    user.get = mock_get
    return user

@pytest.fixture
def mock_group() -> MagicMock:
    group = MagicMock()
    group.key = 20
    group.name = "admins"
    group.is_enabled = True

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Admin group",
            "email": "admins@example.com",
            "member_count": 3,
            "created": 1707000000,
        }
        return data.get(key, default)

    group.get = mock_get
    return group

@pytest.fixture
def mock_group_member() -> MagicMock:
    member = MagicMock()
    member.key = 30
    member.member_name = "admin"
    member.member_type = "User"
    member.member_key = 10
    return member
```

## Task Checklist

- [x] Add `USER_COLUMNS`, `GROUP_COLUMNS`, `GROUP_MEMBER_COLUMNS` to `columns.py`
- [x] Add `mock_user`, `mock_group`, `mock_group_member` fixtures to `conftest.py`
- [x] Create `user.py` with all commands (list, get, create, update, delete, enable, disable)
- [x] Create `group.py` with all commands + member sub-commands
- [x] Register both in `cli.py`
- [x] Create `test_user.py` with all tests
- [x] Create `test_group.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
