# Phase 7a: Certificate Management Implementation Plan

**Date:** 2026-02-10
**Status:** Draft
**Scope:** `vrg certificate` commands for TLS certificate management
**Dependencies:** None
**Task Checklist:** Bottom of file — `tail -20` to check status

## SDK Reference

| CLI concept | SDK manager (`client.<name>`) | SDK source file |
|-------------|-------------------------------|-----------------|
| Certificates | `certificates` | `/Users/larry/Development/pyvergeos/pyvergeos/resources/certificates.py` |

**SDK example:** `/Users/larry/Development/pyvergeos/examples/certificate_example.py`

---

## Overview

Add TLS certificate management commands. VergeOS supports three certificate types: self-signed, Let's Encrypt (ACME), and manual (user-provided PEM). The SDK provides CRUD plus renew/refresh and several list filters (expiring, expired, by type).

**Note:** The release plan lists `import` and `generate-csr` commands. The SDK does not have separate `import_cert()` or `generate_csr()` methods — manual certificates are imported via `create(cert_type="Manual", public_key=..., private_key=...)` and self-signed/LE certs are generated via `create()` with appropriate type. We map `vrg certificate import` to create with type=Manual for a better UX.

## Commands

```
vrg certificate list [--filter ODATA] [--type manual|letsencrypt|self-signed] [--valid | --expired] [--expiring-in DAYS]
vrg certificate get <ID|DOMAIN> [--show-keys]
vrg certificate create --domain DOMAIN [--type self-signed|letsencrypt|manual] [--domains DOMAIN,...] [--description DESC] [--key-type ecdsa|rsa] [--rsa-key-size 2048|3072|4096] [--acme-server URL] [--contact-user USER] [--agree-tos]
vrg certificate import --domain DOMAIN --public-key FILE --private-key FILE [--chain FILE] [--domains DOMAIN,...] [--description DESC]
vrg certificate update <ID|DOMAIN> [--description DESC] [--domains DOMAIN,...] [--public-key FILE] [--private-key FILE] [--chain FILE] [--key-type ecdsa|rsa] [--rsa-key-size SIZE] [--acme-server URL] [--contact-user USER] [--agree-tos BOOL]
vrg certificate delete <ID|DOMAIN> [--yes]
vrg certificate renew <ID|DOMAIN> [--force]
```

### Command Details

#### `vrg certificate list`

- Options:
  - `--filter` (str) — OData filter expression
  - `--type` (str, choices: manual/letsencrypt/self-signed) — filter by certificate type
  - `--valid` (flag) — show only valid (non-expired) certificates
  - `--expired` (flag) — show only expired certificates (mutually exclusive with --valid)
  - `--expiring-in` (int) — show certificates expiring within N days
- SDK:
  - `certificates.list(cert_type=type)` for type filter
  - `certificates.list_valid()` for --valid
  - `certificates.list_expired()` for --expired
  - `certificates.list_expiring(days=N)` for --expiring-in
  - Map CLI type names: "self-signed" → "SelfSigned", "letsencrypt" → "LetsEncrypt", "manual" → "Manual"

#### `vrg certificate get`

- Positional: `CERT` (numeric key or domain name)
- `--show-keys` (flag) — include PEM certificate/key/chain in output
- Resolution: if numeric → `certificates.get(key=int(cert))`; if string → `certificates.get(domain=cert)`
- SDK: `certificates.get(key=..., include_keys=show_keys)` or `certificates.get(domain=..., include_keys=show_keys)`
- Note: don't use `resolve_resource_id()` — certificates use domain lookup, not name lookup

#### `vrg certificate create`

- Required: `--domain` (str) — primary domain
- Optional:
  - `--type` (str, default "self-signed", choices: self-signed/letsencrypt/manual)
  - `--domains` (str, comma-separated) — Subject Alternative Names
  - `--description` (str)
  - `--key-type` (str, choices: ecdsa/rsa)
  - `--rsa-key-size` (int, choices: 2048/3072/4096)
  - `--acme-server` (str) — Let's Encrypt ACME server URL
  - `--contact-user` (int) — user key for Let's Encrypt contact
  - `--agree-tos` (flag) — agree to Let's Encrypt TOS (required for LE)
- Parse `--domains` from comma-separated string to list
- Map type names: "self-signed" → "SelfSigned", "letsencrypt" → "LetsEncrypt", "manual" → "Manual"
- Validate: manual type requires using `vrg certificate import` instead (error with guidance)
- SDK: `certificates.create(domain=..., cert_type=..., domain_list=..., ...)`

#### `vrg certificate import`

- A UX wrapper around `create(cert_type="Manual", ...)`
- Required: `--domain`, `--public-key FILE`, `--private-key FILE`
- Optional:
  - `--chain FILE` — certificate chain PEM file
  - `--domains` (str, comma-separated) — SANs
  - `--description` (str)
- Read PEM file contents from the provided file paths
- SDK: `certificates.create(domain=..., cert_type="Manual", public_key=pem_content, private_key=key_content, chain=chain_content, ...)`

#### `vrg certificate update`

- Positional: `CERT` (key or domain)
- All fields optional
- File-based options (`--public-key`, `--private-key`, `--chain`) read file contents
- SDK: `certificates.update(key, ...)`

#### `vrg certificate delete`

- Positional: `CERT` (key or domain)
- `--yes / -y` — skip confirmation
- SDK: `certificates.delete(key)`

#### `vrg certificate renew`

- Positional: `CERT` (key or domain)
- `--force` (flag) — renew even if not near expiry
- SDK: `certificates.renew(key, force=force)`
- For self-signed: regenerates the certificate
- For Let's Encrypt: triggers ACME renewal
- For manual: error (manual certs can't be auto-renewed)

## Design Decisions

### Certificate Resolution (not `resolve_resource_id`)

Certificates don't have a `name` field — they use `domain` as their identifier. The SDK's `get()` supports `key=` or `domain=` lookups. We implement a custom resolver:

```python
def _resolve_certificate(client: Any, identifier: str) -> int:
    """Resolve certificate identifier (key or domain) to key."""
    if identifier.isdigit():
        cert = client.certificates.get(key=int(identifier))
    else:
        cert = client.certificates.get(domain=identifier)
    return int(cert.key)
```

### Import vs Create

The release plan lists `import` as a separate command. Since the SDK uses `create(cert_type="Manual")` for imports, we provide `vrg certificate import` as a convenience alias that:
- Sets `cert_type="Manual"` automatically
- Uses `--public-key FILE` and `--private-key FILE` (reads file contents)
- Provides a clearer UX for the manual certificate workflow

### PEM File Reading

```python
def _read_pem_file(path: str) -> str:
    """Read PEM file contents."""
    file_path = Path(path)
    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {path}")
    return file_path.read_text()
```

## Files

### New Files

1. **`src/verge_cli/commands/certificate.py`**
   - Typer app with: list, get, create, import, update, delete, renew
   - Helper: `_cert_to_dict(cert)` — convert SDK Certificate to output dict
   - Helper: `_resolve_certificate(client, identifier)` — resolve key or domain to key
   - Helper: `_read_pem_file(path)` — read PEM file contents

2. **`tests/unit/test_certificate.py`**

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import certificate`
   - Add: `app.add_typer(certificate.app, name="certificate")`

4. **`src/verge_cli/columns.py`**
   - Add `CERTIFICATE_COLUMNS`

5. **`tests/conftest.py`**
   - Add `mock_certificate` fixture

## Column Definition

```python
CERTIFICATE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("domain"),
    ColumnDef("type_display", header="Type"),
    ColumnDef("key_type_display", header="Key Type"),
    ColumnDef("valid", header="Valid", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("days_until_expiry", header="Expires In"),
    # wide-only
    ColumnDef("domain_list", header="SANs", wide_only=True),
    ColumnDef("expires", format_fn=format_epoch, wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("autocreated", header="Auto", format_fn=format_bool_yn, style_map=FLAG_STYLES, wide_only=True),
]
```

## Data Mapping

```python
def _cert_to_dict(cert: Any, include_keys: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "$key": int(cert.key),
        "domain": cert.get("domain", cert.get("domainname", "")),
        "domain_list": cert.get("domainlist", ""),
        "description": cert.get("description", ""),
        "type": cert.get("type", ""),
        "type_display": cert.cert_type_display,
        "key_type": cert.get("key_type", ""),
        "key_type_display": cert.key_type_display,
        "valid": cert.is_valid,
        "days_until_expiry": cert.days_until_expiry,
        "expires": cert.get("expires"),
        "created": cert.get("created"),
        "autocreated": cert.get("autocreated", False),
    }
    if include_keys:
        result["public"] = cert.get("public", "")
        result["private"] = cert.get("private", "")
        result["chain"] = cert.get("chain", "")
    return result
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_cert_list` | Lists certificates |
| 2 | `test_cert_list_by_type` | `--type letsencrypt` filter |
| 3 | `test_cert_list_valid` | `--valid` filter |
| 4 | `test_cert_list_expired` | `--expired` filter |
| 5 | `test_cert_list_expiring` | `--expiring-in 30` filter |
| 6 | `test_cert_get_by_key` | Get by numeric key |
| 7 | `test_cert_get_by_domain` | Get by domain name |
| 8 | `test_cert_get_show_keys` | `--show-keys` includes PEM data |
| 9 | `test_cert_create_self_signed` | Create self-signed cert |
| 10 | `test_cert_create_letsencrypt` | Create LE cert with --agree-tos |
| 11 | `test_cert_create_with_sans` | `--domains` comma-separated SANs |
| 12 | `test_cert_import` | Import manual cert from PEM files |
| 13 | `test_cert_import_file_not_found` | Error on missing PEM file |
| 14 | `test_cert_update` | Update description |
| 15 | `test_cert_delete` | Delete with --yes |
| 16 | `test_cert_delete_no_confirm` | Delete without --yes aborts |
| 17 | `test_cert_renew` | Renew certificate |
| 18 | `test_cert_renew_force` | Renew with --force |
| 19 | `test_cert_not_found` | Domain resolution error (exit 6) |

## Test Fixture

```python
@pytest.fixture
def mock_certificate() -> MagicMock:
    cert = MagicMock()
    cert.key = 70
    cert.is_valid = True
    cert.cert_type_display = "Self-Signed"
    cert.key_type_display = "ECDSA"
    cert.days_until_expiry = 350

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "domain": "example.com",
            "domainname": "example.com",
            "domainlist": "*.example.com,api.example.com",
            "description": "Main wildcard cert",
            "type": "self_signed",
            "key_type": "ecdsa",
            "valid": True,
            "expires": 1738000000,
            "created": 1707000000,
            "autocreated": False,
            "public": "-----BEGIN CERTIFICATE-----\nMIIB...",
            "private": "-----BEGIN PRIVATE KEY-----\nMIIE...",
            "chain": "",
        }
        return data.get(key, default)

    cert.get = mock_get
    return cert
```

## Task Checklist

- [x] Add `CERTIFICATE_COLUMNS` to `columns.py`
- [x] Add `mock_certificate` fixture to `conftest.py`
- [x] Create `certificate.py` with all commands (list, get, create, import, update, delete, renew)
- [x] Register in `cli.py`
- [x] Create `test_certificate.py` with all tests
- [x] Run `uv run ruff check && uv run mypy src/verge_cli && uv run pytest`
