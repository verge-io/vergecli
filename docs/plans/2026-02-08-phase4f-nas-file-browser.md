# Phase 4f: NAS File Browser Implementation Plan

**Date:** 2026-02-08
**Status:** Draft
**Scope:** `vrg nas files` commands for browsing NAS volume contents
**Depends on:** Phase 4b (NAS Volumes)
**Task Checklist:** Bottom of file — `tail -20` to check status

---

## Overview

Add read-only file browsing for NAS volumes. This allows users to list directory contents and get file information without mounting the volume. The SDK exposes the file browser via `client.nas_volumes.files(volume_key)` which returns a `NASVolumeFileManager`.

The file browser uses an **async job-based API** — the SDK submits a browse request and polls for results with exponential backoff.

## Commands

```
vrg nas files list <VOLUME> [--path PATH] [--extensions EXTS] [--sort FIELD]
vrg nas files get <VOLUME> <PATH>
```

### Command Details

#### `list`
- Positional: `VOLUME` (name or hex key)
- Options:
  - `--path / -p` (str, default "/") — directory to list
  - `--extensions` (str, optional) — comma-separated file extensions to filter (e.g., "txt,log,csv")
  - `--sort` (str, optional) — sort field (e.g., "name", "size", "date")
- SDK: `client.nas_volumes.files(volume_key).list(path=path, extensions=extensions, sort=sort)`
- Note: path "/" is converted to empty string by SDK for API compatibility

#### `get`
- Positional: `VOLUME` (name or hex key), `PATH` (file or directory path)
- Shows detailed information for a specific file or directory
- SDK: `client.nas_volumes.files(volume_key).get(path=path)`

## Files

### New Files

1. **`src/verge_cli/commands/nas_files.py`**
   - Helpers: `_file_to_dict()`, `_resolve_volume()` (get volume key from positional arg)
   - Commands: list, get
   - Note: Uses scoped manager pattern — first resolves volume, then creates file manager

2. **`tests/unit/test_nas_files.py`**
   - Fixture: `mock_nas_file` — dict-based mock with name="report.txt", type="file", size=1024, date=1700000000
   - Fixture: `mock_nas_dir` — dict-based mock with name="documents", type="directory", size=0
   - Tests: see test plan

### Modified Files

3. **`src/verge_cli/commands/nas.py`**
   - Add: `from verge_cli.commands import nas_files`
   - Add: `app.add_typer(nas_files.app, name="files")`

4. **`tests/conftest.py`**
   - Add fixtures: `mock_nas_file`, `mock_nas_dir`

## Column Definitions

```python
NAS_FILE_COLUMNS: list[ColumnDef] = [
    ColumnDef("name"),
    ColumnDef("type", style_map={"directory": "blue bold", "file": ""}),
    ColumnDef("size_display", header="Size"),
    ColumnDef("modified", header="Modified", format_fn=format_epoch),
]
```

## Data Mapping

```python
def _file_to_dict(f: Any) -> dict[str, Any]:
    """Convert NASVolumeFile (dict-based) to output dict."""
    if isinstance(f, dict):
        return {
            "name": f.get("name"),
            "type": f.get("type"),
            "size": f.get("size", 0),
            "size_display": f.get("size_display", _format_size(f.get("size", 0))),
            "modified": f.get("date"),
        }
    return {
        "name": f.name,
        "type": f.type,
        "size": f.size,
        "size_display": getattr(f, "size_display", _format_size(f.size)),
        "modified": getattr(f, "date", None),
    }

def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"
```

## Test Plan

| # | Test | Validates |
|---|------|-----------|
| 1 | `test_files_list` | Lists files in root directory |
| 2 | `test_files_list_subdir` | Lists files with --path /subdir |
| 3 | `test_files_list_with_extensions` | Filter by --extensions txt,log |
| 4 | `test_files_list_empty` | Handles empty directory |
| 5 | `test_files_get_file` | Get details of a specific file |
| 6 | `test_files_get_directory` | Get details of a directory |
| 7 | `test_files_volume_not_found` | Volume resolution error (exit 6) |
| 8 | `test_format_size` | Size formatting helper (B, KB, MB, GB, TB) |

## Task Checklist

- [x] Create `src/verge_cli/commands/nas_files.py` with all commands
- [x] Register sub-typer in `nas.py`
- [x] Add fixtures to `conftest.py`
- [x] Create `tests/unit/test_nas_files.py` with all tests
- [x] Run `uv run ruff check` and `uv run mypy src/verge_cli`
- [x] Run `uv run pytest tests/unit/test_nas_files.py -v`

## Notes

- This is a **read-only** command group — no create/update/delete operations
- The file browser uses an async job API — the SDK submits a `volume_browser` request and polls for results with exponential backoff
- NASVolumeFile objects are dict-based (not ResourceObject) — different from other NAS resources
- File size is in bytes, displayed in human-readable format (B, KB, MB, GB, TB, PB)
- The `date` field is a Unix timestamp representing modification time
- Path "/" is converted to empty string by the SDK for API compatibility
- Volume resolution uses `resolve_nas_resource()` from Phase 4b (hex keys)
- This is the smallest plan in Phase 4 — just 2 commands
