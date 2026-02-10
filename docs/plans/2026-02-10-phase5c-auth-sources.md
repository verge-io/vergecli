# Phase 5c: Authentication Sources Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg auth-source` commands for SSO/OAuth identity provider management
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Auth Sources | `auth_sources` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/auth_sources.py` |
| Auth Source States | `auth_source_states` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/auth_sources.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/user_management_example.py`

---

## Overview

Add authentication source management for external identity providers (Azure AD, Google, GitLab, Okta, OpenID Connect, OAuth2, VergeOS). Auth sources allow users to sign in via SSO/federation. The SDK supports driver-specific settings, debug mode toggling, and an ephemeral state sub-resource for OAuth flows.

## Commands

```
vrg auth-source list [--driver DRIVER] [--filter ODATA]
vrg auth-source get <ID|NAME> [--show-settings]
vrg auth-source create --name NAME --driver DRIVER [--client-id ID] [--client-secret SECRET] [--tenant-id TENANT] [--scope SCOPE] [--redirect-uri URI] [--auto-create-users] [--show-on-login] [--button-icon ICON] [--button-bg-color COLOR] [--button-text-color COLOR] [--settings-json JSON]
vrg auth-source update <ID|NAME> [--name NAME] [--client-id ID] [--client-secret SECRET] [--scope SCOPE] [--redirect-uri URI] [--auto-create-users BOOL] [--show-on-login BOOL] [--button-icon ICON] [--button-bg-color COLOR] [--button-text-color COLOR] [--settings-json JSON]
vrg auth-source delete <ID|NAME> [--yes]
vrg auth-source debug-on <ID|NAME>
vrg auth-source debug-off <ID|NAME>
```

### Command Details

#### `vrg auth-source list`

- Options:
  - `--driver` (str, choices: azure/google/gitlab/okta/openid/oauth2/verge.io) — filter by provider type
  - `--filter` (str) — OData filter
- SDK: `auth_sources.list(driver=driver)`

#### `vrg auth-source get`

- Positional: `AUTH_SOURCE` (name or key)
- `--show-settings` (flag) — include sensitive settings JSON in output
- SDK: `auth_sources.get(key, include_settings=show_settings)`
- When `--show-settings`, add settings dict to output (JSON format only recommended)

#### `vrg auth-source create`

- Required: `--name`, `--driver`
- Common settings (mapped into `settings` dict):
  - `--client-id` (str)
  - `--client-secret` (str)
  - `--tenant-id` (str, Azure-specific)
  - `--scope` (str)
  - `--redirect-uri` (str)
  - `--auto-create-users` (flag)
- Display options:
  - `--show-on-login` (flag) — show on login page (`menu=True`)
  - `--button-icon` (str) — Bootstrap Icon class (e.g., `bi-google`)
  - `--button-bg-color` (str) — CSS color value
  - `--button-text-color` (str) — CSS color value
- `--settings-json` (str) — raw JSON string for driver-specific settings (merged with individual flags, flags take precedence)
- Build settings dict: start with `--settings-json` (parsed), overlay individual flags
- SDK: `auth_sources.create(name=..., driver=..., settings=..., menu=..., button_fa_icon=..., button_background_color=..., button_color=...)`

#### `vrg auth-source update`

- Positional: `AUTH_SOURCE` (name or key)
- All fields optional, same as create minus `--driver` (cannot change driver)
- Settings are merged with existing (SDK handles merge)
- SDK: `auth_sources.update(key, name=..., settings=..., menu=..., ...)`

#### `vrg auth-source delete`

- Positional: `AUTH_SOURCE` (name or key)
- `--yes / -y` — skip confirmation
- Note: fails if users or OIDC applications reference this source
- SDK: `auth_sources.delete(key)`

#### `vrg auth-source debug-on`

- Positional: `AUTH_SOURCE` (name or key)
- Enables debug logging for the auth source (auto-disables after 1 hour)
- SDK: `auth_source_obj.enable_debug()`
- Output: success message noting 1-hour auto-disable

#### `vrg auth-source debug-off`

- Positional: `AUTH_SOURCE` (name or key)
- Disables debug logging
- SDK: `auth_source_obj.disable_debug()`

## Design Decisions

### Settings Handling

Auth source settings are driver-specific. Rather than trying to expose every driver's settings as individual CLI flags, we use a hybrid approach:

1. **Common flags** (`--client-id`, `--client-secret`, `--scope`, etc.) — cover the most-used settings across drivers
2. **Raw JSON** (`--settings-json '{"custom_field": "value"}'`) — escape hatch for driver-specific or advanced settings
3. **Merge strategy**: Parse `--settings-json` first, then overlay individual flag values. This lets users provide a JSON base and override specific fields.

### No State Sub-Commands

The `AuthSourceStateManager` manages ephemeral OAuth flow states (15-min TTL). These are internal to the OAuth dance and not useful for CLI users. We skip exposing state commands.

## Files

### New Files

1. **`src/verge_cli/commands/auth_source.py`**
   - Typer app with: list, get, create, update, delete, debug-on, debug-off
   - Helper: `_auth_source_to_dict(source)` — convert SDK AuthSource to output dict
   - Helper: `_build_settings()` — merge JSON + individual flags into settings dict

2. **`tests/unit/test_auth_source.py`**

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import auth_source`
   - Add: `app.add_typer(auth_source.app, name="auth-source")`

4. **`src/verge_cli/columns.py`**
   - Add `AUTH_SOURCE_COLUMNS`

5. **`tests/conftest.py`**
   - Add `mock_auth_source` fixture

## Column Definition

```python
AUTH_SOURCE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("driver"),
    ColumnDef("show_on_login", header="Login Menu", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("debug", header="Debug", format_fn=format_bool_yn, style_map=FLAG_STYLES),
    # wide-only
    ColumnDef("button_icon", header="Icon", wide_only=True),
    ColumnDef("button_bg_color", header="BG Color", wide_only=True),
]
```

## Data Mapping

```python
def _auth_source_to_dict(source: Any) -> dict[str, Any]:
    button_style = source.button_style if hasattr(source, "button_style") else {}
    return {
        "$key": int(source.key),
        "name": source.name,
        "driver": source.driver,
        "show_on_login": source.is_menu,
        "debug": source.is_debug_enabled,
        "button_icon": button_style.get("icon", ""),
        "button_bg_color": button_style.get("background_color", ""),
        "button_text_color": button_style.get("text_color", ""),
        "icon_color": button_style.get("icon_color", ""),
    }
```

### Settings Builder

```python
def _build_settings(
    settings_json: str | None,
    client_id: str | None,
    client_secret: str | None,
    tenant_id: str | None,
    scope: str | None,
    redirect_uri: str | None,
    auto_create_users: bool | None,
) -> dict[str, Any] | None:
    """Build settings dict from JSON base + individual flags."""
    settings: dict[str, Any] = {}
    if settings_json:
        settings = json.loads(settings_json)

    flag_map = {
        "client_id": client_id,
        "client_secret": client_secret,
        "tenant_id": tenant_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "auto_create_users": auto_create_users,
    }
    for k, v in flag_map.items():
        if v is not None:
            settings[k] = v

    return settings if settings else None
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_auth_source_list` | Lists auth sources |
| 2 | `test_auth_source_list_by_driver` | `--driver azure` filter |
| 3 | `test_auth_source_get` | Get by name |
| 4 | `test_auth_source_get_by_key` | Get by numeric key |
| 5 | `test_auth_source_get_show_settings` | `--show-settings` includes settings |
| 6 | `test_auth_source_create_basic` | Create with name + driver only |
| 7 | `test_auth_source_create_azure` | Create Azure source with client-id, tenant-id, etc. |
| 8 | `test_auth_source_create_with_json` | `--settings-json` raw settings |
| 9 | `test_auth_source_create_json_flag_merge` | JSON + individual flags (flags override) |
| 10 | `test_auth_source_create_login_menu` | `--show-on-login` and button styling |
| 11 | `test_auth_source_update` | Update name and settings |
| 12 | `test_auth_source_delete` | Delete with --yes |
| 13 | `test_auth_source_delete_no_confirm` | Delete without --yes aborts |
| 14 | `test_auth_source_debug_on` | Enable debug mode |
| 15 | `test_auth_source_debug_off` | Disable debug mode |
| 16 | `test_auth_source_not_found` | Name resolution error (exit 6) |

## Test Fixture

```python
@pytest.fixture
def mock_auth_source() -> MagicMock:
    source = MagicMock()
    source.key = 40
    source.name = "azure-sso"
    source.driver = "azure"
    source.is_menu = True
    source.is_debug_enabled = False
    source.is_azure = True
    source.is_google = False
    source.is_gitlab = False
    source.is_okta = False
    source.is_openid = False
    source.is_oauth2 = False
    source.is_vergeos = False
    source.button_style = {
        "background_color": "#0078d4",
        "text_color": "#ffffff",
        "icon": "bi-microsoft",
        "icon_color": "#ffffff",
    }
    source.settings = {
        "client_id": "abc-123",
        "tenant_id": "tenant-456",
        "scope": "openid profile email",
    }
    return source
```

## Task Checklist

- [x] Add `AUTH_SOURCE_COLUMNS` to `columns.py`
- [x] Add `mock_auth_source` fixture to `conftest.py`
- [x] Create `auth_source.py` with all commands (list, get, create, update, delete, debug-on, debug-off)
- [x] Register in `cli.py`
- [x] Create `test_auth_source.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
