# Output Improvements Design

**Date:** 2026-02-06
**Status:** Approved
**Scope:** Pre-Phase 2 foundation work — improve table readability with column-level styling, add `wide` and `csv` output formats.

---

## Problem

The current output layer is type-aware but not domain-aware:

- `format_value()` only colorizes Python types (bool, None, datetime), not domain values like "running" or "error"
- Status strings ("running", "stopped") display as plain text with no visual distinction
- Flag columns (`restart`, `rules`, `dns_apply`) are pre-converted to `"Y"/""`strings in `_to_dict()`, bypassing bool-based styling
- Inconsistency across commands — network colors `running` (bool), VM shows `status` (uncolored string)
- Only two output formats: `table` and `json`

## Design

### Approach: Column-Level Style Hints (Option A)

Data stays pure (raw values in `_to_dict()`), presentation is declarative via `ColumnDef`, styling happens at render time.

### ColumnDef Model

New file: `src/verge_cli/columns.py`

```python
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ColumnDef:
    key: str                                                    # dict key to read from data
    header: str | None = None                                   # display header; default: key.replace("_", " ").title()
    style_map: Mapping[Any, str] | None = None                  # normalized_value → Rich style
    style_fn: Callable[[Any, dict[str, Any]], str | None] | None = None  # escape hatch: (raw_value, row) → style
    default_style: str | None = None                            # fallback when style_map and style_fn return None
    format_fn: Callable[[Any], str] | None = None               # value → display string
    normalize_fn: Callable[[Any], Any] | None = None            # value → canonical for style lookup only
    wide_only: bool = False                                     # only shown in --output wide (and csv)
```

**Header default:** `key.replace("_", " ").title()` — used for both table and CSV headers.

### Shared Style Maps

```python
STATUS_STYLES: Mapping[Any, str] = {
    "running": "green",
    "online": "green",
    "healthy": "green",
    "stopped": "dim",
    "offline": "dim",
    "starting": "yellow",
    "stopping": "yellow",
    "paused": "yellow",
    "suspended": "yellow",
    "degraded": "yellow",
    "pending": "yellow",
    "provisioning": "yellow",
    "error": "red bold",
    "failed": "red bold",
    "unreachable": "red bold",
    "unknown": "dim",
}

FLAG_STYLES: Mapping[Any, str] = {
    True: "yellow bold",
    False: "dim",
}

BOOL_STYLES: Mapping[Any, str] = {
    True: "green",
    False: "red",
}
```

### Shared Helpers

```python
def normalize_lower(value: Any) -> Any:
    """Normalize string values to lowercase for style lookups."""
    return str(value).strip().lower() if isinstance(value, str) else value

def format_bool_yn(value: Any) -> str:
    """Format bool as Y/- for flag columns."""
    if isinstance(value, bool):
        return "Y" if value else "-"
    return str(value) if value is not None else "-"
```

### Render Pipeline

New internal helper `render_cell()` — does NOT route through `format_value()`:

```
def render_cell(raw_value, row, coldef, *, for_csv=False) -> str | Text:

    # 1. Normalize for style lookup
    normalized = coldef.normalize_fn(raw_value) if coldef.normalize_fn else raw_value

    # 2. Resolve style (deterministic order, explicit None checks)
    style = None
    if coldef.style_map is not None:
        style = coldef.style_map.get(normalized)
    if style is None and coldef.style_fn is not None:
        style = coldef.style_fn(raw_value, row)
    if style is None:
        style = coldef.default_style

    # 3. Format display value
    if coldef.format_fn is not None:
        display = coldef.format_fn(raw_value)
    else:
        display = default_format(raw_value, for_csv=for_csv)

    # 4. Return
    if for_csv:
        return display  # plain string, no styling
    if style:
        return Text(display, style=style)
    return Text(display)
```

**Commitment:** Table and wide use `rich.text.Text(display, style=style)` — not markup strings. This avoids escaping issues with `[` in resource names.

**`format_value()`** remains as the legacy/default formatter for backward compat. `default_format()` is the new equivalent used inside `render_cell()`:

```python
def default_format(value: Any, *, for_csv: bool = False) -> str:
    if value is None:
        return "" if for_csv else "-"
    if isinstance(value, bool):
        return str(value) if for_csv else ("yes" if value else "no")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=json_serializer)
    return str(value)
```

Missing value sentinel: `"-"` in table/wide, `""` in CSV.

### Output Formats

| Format | Columns | Styling | Renderer |
|--------|---------|---------|----------|
| `table` | `wide_only=False` only | Full Rich (Text objects) | `format_table()` |
| `wide` | All columns | Full Rich (Text objects) | `format_table(wide=True)` |
| `json` | N/A (raw data dict) | None | `format_json()` (unchanged) |
| `csv` | All columns | None | `format_csv()` (new) |

**`wide`** is not a new renderer — it's `format_table()` with `wide=True`, which skips filtering out `wide_only` columns.

**`csv`** uses `csv.writer(sys.stdout)`, no Rich console. Calls `render_cell(..., for_csv=True)` for display values, uses same `ColumnDef.header` logic as table.

### CSV Rules for Query Results

| `--query` result type | CSV behavior |
|-----------------------|-------------|
| `list[dict]` | Normal CSV table, one row per dict |
| `list[scalar]` | 1-column CSV, header = query field name or `"value"` |
| `dict` | 1 row, dict keys as column headers |
| `scalar` | 1 row, 1 column, header = `"value"` |

### Global --output Flag

Defined once in `cli.py` root callback:

```python
output: Annotated[
    str,
    typer.Option("--output", "-o", help="Output format: table, wide, json, csv"),
] = "table"
```

Validated at the app level. Stored in `ctx.obj` / `VergeContext.output_format`. Per-command `--output` options are removed.

Commands that aren't tabular (configure, version) ignore the format or respect `json` where sensible.

### Theme Hook (Future-Proofing)

Structure `columns.py` so style maps are retrieved via function:

```python
def get_status_styles() -> Mapping[Any, str]:
    """Return status style map. Future: respect VERGE_THEME env var."""
    return STATUS_STYLES

def get_flag_styles() -> Mapping[Any, str]:
    return FLAG_STYLES

def get_bool_styles() -> Mapping[Any, str]:
    return BOOL_STYLES
```

Column definitions reference these functions. Out of scope to implement `VERGE_THEME` now, but the structure makes it painless later.

### Example Column Definitions

**VM:**
```python
VM_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("status", style_map=get_status_styles(), normalize_fn=normalize_lower),
    ColumnDef("cpu_cores", header="CPU"),
    ColumnDef("ram", header="RAM (MB)"),
    ColumnDef("cluster_name", header="Cluster"),
    ColumnDef("node_name", header="Node"),
    ColumnDef("needs_restart", header="Restart", style_map=get_flag_styles(), format_fn=format_bool_yn),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("os_family", header="OS", wide_only=True),
    ColumnDef("key", wide_only=True),
]
```

**Network:**
```python
NETWORK_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("type"),
    ColumnDef("network", header="CIDR"),
    ColumnDef("ipaddress", header="IP Address"),
    ColumnDef("status", style_map=get_status_styles(), normalize_fn=normalize_lower),
    ColumnDef("running", style_map=get_bool_styles(), format_fn=format_bool_yn),
    ColumnDef("needs_restart", header="Restart", style_map=get_flag_styles(), format_fn=format_bool_yn),
    ColumnDef("needs_rule_apply", header="Rules", style_map=get_flag_styles(), format_fn=format_bool_yn),
    ColumnDef("needs_dns_apply", header="DNS", style_map=get_flag_styles(), format_fn=format_bool_yn),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("gateway", wide_only=True),
    ColumnDef("mtu", wide_only=True),
    ColumnDef("key", wide_only=True),
]
```

### Data Cleanup in _to_dict()

Remove synthetic string aliases. Before:
```python
"restart": "Y" if net.get("need_restart", False) else "",
"rules": "Y" if net.get("need_fw_apply", False) else "",
```

After: just the raw bool:
```python
"needs_restart": net.get("need_restart", False),
"needs_rule_apply": net.get("need_fw_apply", False),
```

---

## File Change Summary

| File | Change |
|------|--------|
| `columns.py` (NEW) | ColumnDef, style maps via getter functions, shared helpers, all resource column defs |
| `output.py` | `render_cell()`, `default_format()`, updated `format_table()` for ColumnDef + Text, new `format_csv()`, updated `output_result()` |
| `cli.py` | Global `--output` as validated string, remove per-command output options |
| `context.py` | Ensure `output_format` stores validated string |
| `commands/vm.py` | Import VM_COLUMNS, remove VM_LIST_COLUMNS, clean _vm_to_dict() |
| `commands/network.py` | Import NETWORK_COLUMNS, remove NETWORK_LIST_COLUMNS, clean _network_to_dict() |
| `commands/network_rule.py` | Import columns, remove per-cmd output option |
| `commands/network_dns.py` | Same pattern |
| `commands/network_host.py` | Same pattern |
| `commands/network_alias.py` | Same pattern |
| `commands/network_diag.py` | Same pattern |
| `commands/vm_drive.py` | Same pattern |
| `commands/vm_nic.py` | Same pattern |
| `commands/vm_device.py` | Same pattern |
| `commands/system.py` | Same pattern |
| `commands/configure.py` | No change (not tabular) |
| Tests | New: render pipeline, CSV, wide. Updated: existing command tests |

**Not touched:** `auth.py`, `config.py`, `errors.py`, `utils.py`, `template/`

---

## Implementation Order

1. **columns.py** — ColumnDef, style maps, helpers (no dependencies)
2. **output.py** — render_cell, default_format, format_csv, update format_table and output_result
3. **cli.py + context.py** — global --output flag consolidation
4. **Command files** — update all commands (can be parallelized)
5. **Tests** — render pipeline unit tests, CSV/wide integration, update existing
6. **Verify** — ruff, mypy, full test suite

---

## Out of Scope

- `VERGE_THEME` env var (structure supports it, not implemented)
- YAML output format
- TSV output format
- Per-command output overrides
- Custom column selection (`--columns name,status`)
