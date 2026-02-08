# Phase 4h: Storage File Management (Media Catalog) Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg file` commands for media catalog file management (ISO, disk images, OVA/OVF)
**Depends on:** None (independent — not part of NAS subsystem)
**Blocks:** None

---

## Overview

Add media catalog file management as a top-level `vrg file` command group. The media catalog stores ISO images, disk images (QCOW2, VMDK, VHDX, etc.), OVA/OVF packages, and other media types used by VMs. The SDK exposes files via `client.files` (FileManager) with integer keys and supports chunked upload/download with progress callbacks.

This is **not** the NAS file browser (Phase 4f) — the media catalog is a separate concept for VM-consumable media images stored at the system level.

## Commands

```
vrg file list [--type TYPE] [--limit INT] [--offset INT]
vrg file get <IDENTIFIER>
vrg file upload <PATH> [--name NAME] [--description DESC] [--tier INT]
vrg file download <IDENTIFIER> [--destination PATH] [--filename TEXT] [--overwrite]
vrg file update <IDENTIFIER> [--name NAME] [--description DESC] [--tier INT]
vrg file delete <IDENTIFIER> [--yes]
vrg file types
```

### Command Details

#### `list`
- Options:
  - `--type / -t` (str, optional) — filter by file type (iso, qcow2, vmdk, ova, etc.)
  - `--limit` (int, optional) — max results
  - `--offset` (int, optional) — skip N results
- SDK: `client.files.list(file_type=type, limit=limit, offset=offset)`

#### `get`
- Positional: `IDENTIFIER` (name or key)
- SDK: `resolve_resource_id(client.files, identifier, "file")`, then `client.files.get(key=key)`

#### `upload`
- Positional: `PATH` — local file path
- Options:
  - `--name / -n` (str, optional) — override file name in catalog (defaults to local filename)
  - `--description / -d` (str, optional) — file description
  - `--tier` (int, optional) — preferred storage tier (1-5)
- SDK: `client.files.upload(path, name=name, description=description, tier=tier, progress_callback=...)`
- Validate local file exists before calling SDK
- Show Rich `Progress` bar during upload with bytes transferred and percentage
- On success, display the uploaded file details

#### `download`
- Positional: `IDENTIFIER` (name or key)
- Options:
  - `--destination` (Path, default ".") — target directory
  - `--filename` (str, optional) — override the downloaded filename
  - `--overwrite` (flag) — overwrite existing file
- SDK: resolve key, then `client.files.download(key=key, destination=destination, filename=filename, overwrite=overwrite, progress_callback=...)`
- Show Rich `Progress` bar during download with bytes transferred and percentage
- On success, display the download path

#### `update`
- Positional: `IDENTIFIER` (name or key)
- Options:
  - `--name / -n` (str, optional)
  - `--description / -d` (str, optional)
  - `--tier` (int, optional) — preferred storage tier (1-5)
- SDK: resolve key, then `client.files.update(key, name=name, description=description, preferred_tier=tier)` with only non-None values
- Uses read-patch-write pattern: get current file, merge non-None updates, send update

#### `delete`
- Positional: `IDENTIFIER` (name or key)
- Options: `--yes / -y` — skip confirmation
- SDK: resolve key, then `client.files.delete(key)`
- Confirm before delete via `confirm_action()` unless `--yes`
- Note: fails with API error if file is referenced by VM drives

#### `types`
- No positional args, no options
- No SDK call — display the `FILE_TYPES` constant as a table
- Output: Type | Description (e.g., "iso | ISO", "qcow2 | QCOW2 (QEMU, Xen)")

## Files

### New Files

1. **`src/verge_cli/commands/file.py`**
   - Helpers: `_file_to_dict()`, `_file_type_to_dict()`
   - Commands: list, get, upload, download, update, delete, types
   - Uses existing `resolve_resource_id()` (files use int keys)
   - Rich `Progress` bars for upload and download

2. **`tests/unit/test_file.py`**
   - Fixture: `mock_file` — MagicMock with key=1, name="ubuntu-22.04.iso", file_type="iso", size_gb=4.7, etc.
   - Tests: see test plan below

### Modified Files

3. **`src/verge_cli/cli.py`**
   - Add: `from verge_cli.commands import file`
   - Add: `app.add_typer(file.app, name="file")`

## Column Definitions

```python
# In file.py
FILE_COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("type", header="Type"),
    ColumnDef(
        "size_gb",
        header="Size (GB)",
        format_fn=lambda v, for_csv=False: f"{v:.2f}" if v else "0.00",
    ),
    ColumnDef("preferred_tier", header="Tier"),
    ColumnDef("description", wide_only=True),
    ColumnDef(
        "allocated_gb",
        header="Allocated (GB)",
        wide_only=True,
        format_fn=lambda v, for_csv=False: f"{v:.2f}" if v else "0.00",
    ),
    ColumnDef(
        "used_gb",
        header="Used (GB)",
        wide_only=True,
        format_fn=lambda v, for_csv=False: f"{v:.2f}" if v else "0.00",
    ),
    ColumnDef("creator", wide_only=True),
    ColumnDef("modified", wide_only=True),
]

FILE_TYPE_COLUMNS: list[ColumnDef] = [
    ColumnDef("type", header="Type"),
    ColumnDef("description", header="Description"),
]
```

## Data Mapping

```python
def _file_to_dict(obj: Any) -> dict[str, Any]:
    """Convert SDK File object to output dict."""
    return {
        "$key": int(obj.key),
        "name": obj.name,
        "type": obj.file_type,
        "description": obj.description,
        "size_gb": obj.size_gb,
        "allocated_gb": obj.allocated_gb,
        "used_gb": obj.used_gb,
        "preferred_tier": obj.preferred_tier,
        "creator": obj.creator,
        "modified": str(obj.modified) if obj.modified else "",
    }

def _file_type_to_dict(type_key: str, type_desc: str) -> dict[str, str]:
    """Convert FILE_TYPES entry to output dict."""
    return {
        "type": type_key,
        "description": type_desc,
    }
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_file_list` | Lists all files, verify table output |
| 2 | `test_file_list_type_filter` | `--type iso` passes file_type to SDK |
| 3 | `test_file_list_empty` | No files returns empty table |
| 4 | `test_file_get_by_name` | Get file by name resolution |
| 5 | `test_file_get_by_key` | Get file by numeric key |
| 6 | `test_file_get_not_found` | Nonexistent file returns exit code 6 |
| 7 | `test_file_upload` | Upload file, verify SDK call with path |
| 8 | `test_file_upload_with_options` | Upload with `--name`, `--description`, `--tier` |
| 9 | `test_file_upload_file_not_found` | Local file doesn't exist, error before SDK call |
| 10 | `test_file_download` | Download file, verify SDK call with key |
| 11 | `test_file_download_with_options` | Download with `--destination`, `--filename`, `--overwrite` |
| 12 | `test_file_delete_confirmed` | Delete with `--yes` skips confirmation |
| 13 | `test_file_update` | Update metadata (name, description, tier) |
| 14 | `test_file_types` | List supported file types, verify all 16 types in output |

## Implementation Steps

1. Create `src/verge_cli/commands/file.py` with all 7 commands
2. Register `file` typer in `src/verge_cli/cli.py`
3. Create `tests/unit/test_file.py` with mock fixture and all 14 tests
4. Run lint: `uv run ruff check src/verge_cli/commands/file.py tests/unit/test_file.py`
5. Run type check: `uv run mypy src/verge_cli/commands/file.py`
6. Run tests: `uv run pytest tests/unit/test_file.py -v`

## Notes

- Files use **integer keys** — use standard `resolve_resource_id()` from `utils.py`
- Upload uses Rich `Progress` bar via `progress_callback` — the SDK calls `progress_callback(bytes_uploaded, total_bytes)` per chunk
- Download uses Rich `Progress` bar similarly — `progress_callback(bytes_downloaded, total_bytes)`
- The SDK validates that the local file exists before upload and raises `FileNotFoundError`; the CLI should also validate early for a better error message
- `FILE_TYPES` dict has 16 entries: iso, img, qcow, qcow2, qed, raw, vdi, vhd, vhdx, vmdk, ova, ovf, vmx, ybvm, nvram, zip
- The `--type` option on `list` should accept any value from `FILE_TYPES` keys (case-insensitive, lowered before passing to SDK)
- File sizes: the SDK's `File` object exposes `.size_gb`, `.allocated_gb`, `.used_gb` as pre-computed float properties — no manual byte conversion needed
- The `modified` property returns a `datetime` object (or None) — convert to string for output
- The SDK's `upload()` does two-phase: POST to create entry, then PUT chunks; it auto-cleans up partial uploads on failure
- The SDK's `download()` streams content and handles `FileExistsError` if `overwrite=False`
- Delete fails with `ValidationError` from the API if the file is referenced by any VM drive — surface this error clearly
- The `update` command uses the inherited `ResourceManager.update(key, **kwargs)` method — pass only non-None keyword arguments
- `int()` wrap on `obj.key` in `_file_to_dict` to satisfy mypy strict mode (SDK returns `Any`)
- This plan is **independent** — no dependency on NAS plans (4a-4f). Media catalog lives at `vrg file`, not `vrg nas file`
