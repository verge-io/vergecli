# Phase 7b: OIDC Applications (Core) Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg oidc` core commands for OIDC application management (VergeOS as IdP)
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| OIDC Applications | `oidc_applications` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/oidc_applications.py` |

**SDK example:** None (follow `certificate.py` or `recipe.py` patterns)

---

## Overview

Add OIDC application management commands. VergeOS can act as an OpenID Connect Identity Provider, issuing tokens to registered applications. Each OIDC application has a client_id/client_secret pair (auto-generated), configurable scopes (profile, email, groups), redirect URIs, and optional access restrictions.

This plan covers the core OIDC application CRUD. Phase 7c adds user/group ACL and log sub-resources.

**Note:** The release plan lists `regenerate-secret` as a command. The SDK does not have a `regenerate_secret()` method — the client_secret is auto-generated on `create()` and is immutable. We omit this command and note the limitation.

## Commands

```
vrg oidc list [--filter ODATA] [--enabled | --disabled]
vrg oidc get <ID|NAME> [--show-secret] [--show-well-known]
vrg oidc create --name NAME [--redirect-uri URI,...] [--description DESC] [--disabled] [--restrict-access] [--force-auth-source SOURCE] [--map-user USER] [--scope-profile | --no-scope-profile] [--scope-email | --no-scope-email] [--scope-groups | --no-scope-groups]
vrg oidc update <ID|NAME> [--name NAME] [--redirect-uri URI,...] [--description DESC] [--enabled BOOL] [--restrict-access BOOL] [--force-auth-source SOURCE] [--map-user USER] [--scope-profile BOOL] [--scope-email BOOL] [--scope-groups BOOL]
vrg oidc delete <ID|NAME> [--yes]
vrg oidc enable <ID|NAME>
vrg oidc disable <ID|NAME>
```

### Command Details

#### `vrg oidc list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--enabled` (flag) — show only enabled applications
  - `--disabled` (flag) — show only disabled applications (mutually exclusive with --enabled)
- SDK: `oidc_applications.list(enabled=True|False)`

#### `vrg oidc get`

- Positional: `APP` (name or key)
- `--show-secret` (flag) — include client_secret in output
- `--show-well-known` (flag) — include well-known configuration URL
- SDK: `oidc_applications.get(key, include_secret=show_secret, include_well_known=show_well_known)` after resolving identifier
- Resolution: if numeric → get by key; if string → get by name (SDK supports `get(name=...)`)

#### `vrg oidc create`

- Required: `--name`
- Optional:
  - `--redirect-uri` (str, comma-separated) — callback URLs (wildcards supported)
  - `--description` (str)
  - `--disabled` (flag, default enabled)
  - `--restrict-access` (flag) — restrict to allowed users/groups (managed in Phase 7c)
  - `--force-auth-source` (str) — auth source name or key to auto-redirect login
  - `--map-user` (str) — user name or key to map all logins to
  - `--scope-profile / --no-scope-profile` (default: enabled) — grant profile scope
  - `--scope-email / --no-scope-email` (default: enabled) — grant email scope
  - `--scope-groups / --no-scope-groups` (default: enabled) — grant groups scope
- Parse `--redirect-uri` from comma-separated string to list
- Resolve `--force-auth-source` via `resolve_resource_id(client.auth_sources, ...)` if provided
- Resolve `--map-user` via `resolve_resource_id(client.users, ...)` if provided
- SDK: `oidc_applications.create(name=..., redirect_uri=..., ...)`
- **IMPORTANT**: The create response includes `client_secret` — display it prominently with a warning (same pattern as API key create)

#### `vrg oidc update`

- Positional: `APP` (name or key)
- All fields optional
- Note: `client_id` and `client_secret` are immutable — cannot be changed
- Resolve `--force-auth-source` and `--map-user` if provided
- SDK: `oidc_applications.update(key, ...)`

#### `vrg oidc delete`

- Positional: `APP` (name or key)
- `--yes / -y` — skip confirmation
- SDK: `oidc_applications.delete(key)`

#### `vrg oidc enable` / `vrg oidc disable`

- Positional: `APP` (name or key)
- SDK: resolve key, get object, call `app.enable()` / `app.disable()`

## Design Decisions

### OIDC Resolution

The SDK supports `get(key=...)` and `get(name=...)`. We use a custom resolver similar to certificates:

```python
def _resolve_oidc_app(client: Any, identifier: str) -> int:
    """Resolve OIDC app identifier (key or name) to key."""
    if identifier.isdigit():
        app = client.oidc_applications.get(key=int(identifier))
    else:
        app = client.oidc_applications.get(name=identifier)
    return int(app.key)
```

Actually, we can use the standard `resolve_resource_id()` pattern since the OIDC manager likely supports `.list()` with filtering. Let me check — yes, the manager supports name-based get and list, so `resolve_resource_id(client.oidc_applications, identifier, "OIDC Application")` should work.

### No regenerate-secret

The SDK does not expose a `regenerate_secret()` method. The client_secret is generated once during `create()` and cannot be changed. If users need a new secret, they must delete and recreate the application. We document this in help text.

### Secret Display on Create

Same pattern as `vrg api-key create` — show client_id and client_secret prominently with a warning that the secret cannot be retrieved again (unless `--show-secret` is used on get, which does return it in this case — unlike API keys, OIDC secrets CAN be retrieved later with `include_secret=True`).

## Files

### New Files

1. **`src/verge_cli/commands/oidc.py`**
   - Typer app with: list, get, create, update, delete, enable, disable
   - Helper: `_oidc_app_to_dict(app)` — convert SDK OidcApplication to output dict
   - Sub-typer registration points for Phase 7c (user, group, log)

2. **`tests/unit/test_oidc.py`**

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import oidc`
   - Add: `app.add_typer(oidc.app, name="oidc")`

4. **`src/verge_cli/columns.py`**
   - Add `OIDC_APP_COLUMNS`

5. **`tests/conftest.py`**
   - Add `mock_oidc_app` fixture

## Column Definition

```python
OIDC_APP_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("client_id", header="Client ID"),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("scopes", header="Scopes"),
    ColumnDef("restrict_access", header="Restricted", format_fn=format_bool_yn, style_map=FLAG_STYLES),
    # wide-only
    ColumnDef("redirect_uris_display", header="Redirect URIs", wide_only=True),
    ColumnDef("force_auth_source_display", header="Auth Source", wide_only=True),
    ColumnDef("description", wide_only=True),
]
```

## Data Mapping

```python
def _oidc_app_to_dict(app: Any, include_secret: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "$key": int(app.key),
        "name": app.name,
        "description": app.get("description", ""),
        "client_id": app.get("client_id", ""),
        "enabled": app.is_enabled,
        "restrict_access": app.is_access_restricted,
        "redirect_uris": app.redirect_uris,
        "redirect_uris_display": ", ".join(app.redirect_uris) if app.redirect_uris else "",
        "scopes": ", ".join(app.scopes),
        "scope_profile": app.get("scope_profile", True),
        "scope_email": app.get("scope_email", True),
        "scope_groups": app.get("scope_groups", True),
        "force_auth_source": app.force_auth_source_key,
        "force_auth_source_display": app.get("force_auth_source", ""),
        "map_user": app.map_user_key,
        "created": app.get("created"),
    }
    if include_secret:
        result["client_secret"] = app.get("client_secret", "")
    return result
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_oidc_list` | Lists OIDC applications |
| 2 | `test_oidc_list_enabled` | `--enabled` filter |
| 3 | `test_oidc_list_disabled` | `--disabled` filter |
| 4 | `test_oidc_get` | Get by name |
| 5 | `test_oidc_get_by_key` | Get by numeric key |
| 6 | `test_oidc_get_show_secret` | `--show-secret` includes client_secret |
| 7 | `test_oidc_get_show_well_known` | `--show-well-known` includes config URL |
| 8 | `test_oidc_create` | Basic create, verify client_id/secret in output |
| 9 | `test_oidc_create_with_options` | All optional flags |
| 10 | `test_oidc_create_redirect_uris` | Comma-separated redirect URIs |
| 11 | `test_oidc_create_scopes` | Custom scope flags |
| 12 | `test_oidc_update` | Update name, description |
| 13 | `test_oidc_update_scopes` | Update scope flags |
| 14 | `test_oidc_delete` | Delete with --yes |
| 15 | `test_oidc_delete_no_confirm` | Delete without --yes aborts |
| 16 | `test_oidc_enable` | Enable application |
| 17 | `test_oidc_disable` | Disable application |
| 18 | `test_oidc_not_found` | Name resolution error (exit 6) |

## Test Fixture

```python
@pytest.fixture
def mock_oidc_app() -> MagicMock:
    app = MagicMock()
    app.key = 80
    app.name = "grafana"
    app.is_enabled = True
    app.is_access_restricted = False
    app.redirect_uris = ["https://grafana.example.com/callback"]
    app.scopes = ["openid", "profile", "email", "groups"]
    app.force_auth_source_key = None
    app.map_user_key = None

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Grafana SSO",
            "client_id": "oidc_abc123",
            "client_secret": "oidc_secret_xyz789",
            "enabled": True,
            "redirect_uri": "https://grafana.example.com/callback",
            "restrict_access": False,
            "scope_profile": True,
            "scope_email": True,
            "scope_groups": True,
            "force_auth_source": "",
            "map_user": "",
            "created": 1707000000,
            "well_known_configuration": "https://verge.example.com/.well-known/openid-configuration",
        }
        return data.get(key, default)

    app.get = mock_get
    return app
```

## Task Checklist

- [x] Add `OIDC_APP_COLUMNS` to `columns.py`
- [x] Add `mock_oidc_app` fixture to `conftest.py`
- [x] Create `oidc.py` with all commands (list, get, create, update, delete, enable, disable)
- [x] Register in `cli.py`
- [x] Create `test_oidc.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
