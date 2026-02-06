# Output Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add column-level styling with semantic colors and `wide`/`csv` output formats to the CLI, establishing the output pattern for all future commands.

**Architecture:** New `columns.py` defines `ColumnDef` dataclass + style maps. `output.py` gets `render_cell()` pipeline using `Text()` objects (not markup). All command files migrate from `list[str]` column definitions to `list[ColumnDef]`. Global `--output` flag consolidated in `cli.py`.

**Tech Stack:** Python 3.10+, Rich (`Text`, `Table`), csv stdlib, Typer `Literal`

**Design doc:** `docs/plans/2026-02-06-output-improvements-design.md`

---

### Task 1: Create columns.py — ColumnDef, style maps, helpers

**Files:**
- Create: `src/verge_cli/columns.py`
- Test: `tests/unit/test_columns.py`

**Step 1: Write the test file for ColumnDef, helpers, and style maps**

```python
# tests/unit/test_columns.py
"""Unit tests for column definitions and formatting helpers."""

from __future__ import annotations

from verge_cli.columns import (
    BOOL_STYLES,
    FLAG_STYLES,
    STATUS_STYLES,
    ColumnDef,
    format_bool_yn,
    normalize_lower,
)


class TestNormalizeLower:
    def test_string(self) -> None:
        assert normalize_lower("Running") == "running"

    def test_string_with_whitespace(self) -> None:
        assert normalize_lower("  Running  ") == "running"

    def test_non_string_passthrough(self) -> None:
        assert normalize_lower(True) is True
        assert normalize_lower(42) == 42
        assert normalize_lower(None) is None


class TestFormatBoolYn:
    def test_true_table(self) -> None:
        assert format_bool_yn(True) == "Y"

    def test_false_table(self) -> None:
        assert format_bool_yn(False) == "-"

    def test_true_csv(self) -> None:
        assert format_bool_yn(True, for_csv=True) == "true"

    def test_false_csv(self) -> None:
        assert format_bool_yn(False, for_csv=True) == "false"

    def test_none_table(self) -> None:
        assert format_bool_yn(None) == "-"

    def test_none_csv(self) -> None:
        assert format_bool_yn(None, for_csv=True) == ""

    def test_string_passthrough(self) -> None:
        assert format_bool_yn("yes") == "yes"


class TestStyleMaps:
    def test_status_running_is_green(self) -> None:
        assert STATUS_STYLES["running"] == "green"

    def test_status_stopped_is_dim(self) -> None:
        assert STATUS_STYLES["stopped"] == "dim"

    def test_status_error_is_red_bold(self) -> None:
        assert STATUS_STYLES["error"] == "red bold"

    def test_flag_true_is_yellow_bold(self) -> None:
        assert FLAG_STYLES[True] == "yellow bold"

    def test_flag_false_is_dim(self) -> None:
        assert FLAG_STYLES[False] == "dim"

    def test_bool_true_is_green(self) -> None:
        assert BOOL_STYLES[True] == "green"

    def test_bool_false_is_red(self) -> None:
        assert BOOL_STYLES[False] == "red"


class TestColumnDef:
    def test_default_header(self) -> None:
        col = ColumnDef("cpu_cores")
        assert col.resolved_header == "Cpu Cores"

    def test_custom_header(self) -> None:
        col = ColumnDef("cpu_cores", header="CPU")
        assert col.resolved_header == "CPU"

    def test_wide_only_default_false(self) -> None:
        col = ColumnDef("name")
        assert col.wide_only is False

    def test_frozen(self) -> None:
        col = ColumnDef("name")
        try:
            col.key = "other"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_columns.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'verge_cli.columns'`

**Step 3: Create `columns.py` with ColumnDef, style maps, and helpers**

```python
# src/verge_cli/columns.py
"""Column definitions and styling for CLI output."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


class FormatFn(Protocol):
    """Canonical signature for format functions. Must return str, never Text."""

    def __call__(self, value: Any, *, for_csv: bool = False) -> str: ...


@dataclass(frozen=True)
class ColumnDef:
    """Column definition with display and styling hints.

    Attributes:
        key: Dict key to read from row data.
        header: Display header. Default: key.replace("_", " ").title().
        style_map: Mapping of normalized_value → Rich style string.
        style_fn: Escape hatch: (raw_value, row) → style or None.
        default_style: Fallback style when style_map and style_fn return None.
        format_fn: (value, *, for_csv=False) → display string.
        normalize_fn: value → canonical value for style lookup only. Must be pure.
        wide_only: If True, only shown in --output wide and csv.
    """

    key: str
    header: str | None = None
    style_map: Mapping[Any, str] | None = None
    style_fn: Callable[[Any, dict[str, Any]], str | None] | None = None
    default_style: str | None = None
    format_fn: FormatFn | None = None
    normalize_fn: Callable[[Any], Any] | None = None
    wide_only: bool = False

    @property
    def resolved_header(self) -> str:
        """Return the display header, using default if not set."""
        if self.header is not None:
            return self.header
        return self.key.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Shared style maps
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def normalize_lower(value: Any) -> Any:
    """Normalize string values to lowercase for style lookups."""
    return str(value).strip().lower() if isinstance(value, str) else value


def format_bool_yn(value: Any, *, for_csv: bool = False) -> str:
    """Format bool as Y/- for flag columns."""
    if isinstance(value, bool):
        if for_csv:
            return "true" if value else "false"
        return "Y" if value else "-"
    if value is None:
        return "" if for_csv else "-"
    return str(value)


def json_serializer(obj: Any) -> str:
    """JSON serializer for datetime and other types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def default_format(value: Any, *, for_csv: bool = False) -> str:
    """Default formatter for cell values.

    Args:
        value: Raw value to format.
        for_csv: If True, use machine-friendly representations.

    Returns:
        Display string. Never returns Text or Rich renderables.
    """
    if value is None:
        return "" if for_csv else "-"
    if isinstance(value, bool):
        if for_csv:
            return "true" if value else "false"
        return "yes" if value else "no"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=json_serializer)
    return str(value)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_columns.py -v`
Expected: All PASS

**Step 5: Run linting and type checks**

Run: `uv run ruff check src/verge_cli/columns.py tests/unit/test_columns.py && uv run mypy src/verge_cli/columns.py`
Expected: No errors

**Step 6: Commit**

```bash
git add src/verge_cli/columns.py tests/unit/test_columns.py
git commit -m "feat: add ColumnDef, style maps, and formatting helpers"
```

---

### Task 2: Add render_cell() and default_format() to output.py

**Files:**
- Modify: `src/verge_cli/output.py`
- Test: `tests/unit/test_output.py` (add new test class)

**Step 1: Write failing tests for render_cell and default_format**

Append to `tests/unit/test_output.py`:

```python
from rich.text import Text

from verge_cli.columns import (
    BOOL_STYLES,
    FLAG_STYLES,
    STATUS_STYLES,
    ColumnDef,
    default_format,
    format_bool_yn,
    normalize_lower,
)
from verge_cli.output import render_cell


class TestDefaultFormat:
    def test_none_table(self) -> None:
        assert default_format(None) == "-"

    def test_none_csv(self) -> None:
        assert default_format(None, for_csv=True) == ""

    def test_bool_true_table(self) -> None:
        assert default_format(True) == "yes"

    def test_bool_false_table(self) -> None:
        assert default_format(False) == "no"

    def test_bool_true_csv(self) -> None:
        assert default_format(True, for_csv=True) == "true"

    def test_bool_false_csv(self) -> None:
        assert default_format(False, for_csv=True) == "false"

    def test_string_passthrough(self) -> None:
        assert default_format("hello") == "hello"

    def test_int_passthrough(self) -> None:
        assert default_format(42) == "42"

    def test_datetime(self) -> None:
        from datetime import datetime
        dt = datetime(2024, 1, 15, 10, 30, 45)
        assert default_format(dt) == "2024-01-15 10:30:45"


class TestRenderCell:
    def test_plain_text_no_style(self) -> None:
        col = ColumnDef("name")
        result = render_cell("test-vm", {}, col)
        assert isinstance(result, Text)
        assert str(result) == "test-vm"

    def test_style_map_applied(self) -> None:
        col = ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower)
        result = render_cell("running", {}, col)
        assert isinstance(result, Text)
        assert str(result) == "running"
        assert result.style == "green"

    def test_style_map_with_normalize(self) -> None:
        col = ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower)
        result = render_cell("Running", {}, col)
        assert isinstance(result, Text)
        assert result.style == "green"

    def test_flag_bool_styled(self) -> None:
        col = ColumnDef("needs_restart", style_map=FLAG_STYLES, format_fn=format_bool_yn)
        result = render_cell(True, {}, col)
        assert isinstance(result, Text)
        assert str(result) == "Y"
        assert result.style == "yellow bold"

    def test_flag_false_dim(self) -> None:
        col = ColumnDef("needs_restart", style_map=FLAG_STYLES, format_fn=format_bool_yn)
        result = render_cell(False, {}, col)
        assert isinstance(result, Text)
        assert str(result) == "-"
        assert result.style == "dim"

    def test_csv_returns_string(self) -> None:
        col = ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower)
        result = render_cell("running", {}, col, for_csv=True)
        assert isinstance(result, str)
        assert result == "running"

    def test_csv_flag_machine_friendly(self) -> None:
        col = ColumnDef("needs_restart", style_map=FLAG_STYLES, format_fn=format_bool_yn)
        result = render_cell(True, {}, col, for_csv=True)
        assert isinstance(result, str)
        assert result == "true"

    def test_default_style_fallback(self) -> None:
        col = ColumnDef("notes", default_style="dim")
        result = render_cell("some text", {}, col)
        assert isinstance(result, Text)
        assert result.style == "dim"

    def test_style_fn_escape_hatch(self) -> None:
        def warn_high_ram(value: Any, row: dict[str, Any]) -> str | None:
            if isinstance(value, int) and value > 8000:
                return "red bold"
            return None

        col = ColumnDef("ram", style_fn=warn_high_ram)
        result = render_cell(16384, {"ram": 16384}, col)
        assert isinstance(result, Text)
        assert result.style == "red bold"

    def test_style_resolution_order(self) -> None:
        """style_map wins over style_fn wins over default_style."""
        col = ColumnDef(
            "status",
            style_map={"running": "green"},
            style_fn=lambda v, r: "yellow",
            default_style="dim",
            normalize_fn=normalize_lower,
        )
        # style_map match -> green
        result = render_cell("running", {}, col)
        assert result.style == "green"

        # No style_map match -> style_fn -> yellow
        result = render_cell("unknown_value", {}, col)
        assert result.style == "yellow"

    def test_none_value_table(self) -> None:
        col = ColumnDef("notes")
        result = render_cell(None, {}, col)
        assert isinstance(result, Text)
        assert str(result) == "-"

    def test_none_value_csv(self) -> None:
        col = ColumnDef("notes")
        result = render_cell(None, {}, col, for_csv=True)
        assert result == ""
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_output.py::TestRenderCell -v`
Expected: FAIL — `ImportError: cannot import name 'render_cell' from 'verge_cli.output'`

**Step 3: Add render_cell() to output.py**

Add these imports at the top of `src/verge_cli/output.py`:

```python
from rich.text import Text

from verge_cli.columns import ColumnDef, default_format
```

Add `render_cell()` function after the existing `format_value()` function (after line 132):

```python
def render_cell(
    raw_value: Any,
    row: dict[str, Any],
    coldef: ColumnDef,
    *,
    for_csv: bool = False,
) -> str | Text:
    """Render a single table cell using column definition.

    This is the core render pipeline. format_fn must return str, never Text.
    render_cell is the only place that constructs Text objects.

    Args:
        raw_value: The raw value from the data dict.
        row: The full row dict (for style_fn context).
        coldef: Column definition with style/format hints.
        for_csv: If True, return plain str with no styling.

    Returns:
        Text object for table/wide, plain str for CSV.
    """
    # 1. Normalize for style lookup
    normalized = coldef.normalize_fn(raw_value) if coldef.normalize_fn else raw_value

    # 2. Resolve style (deterministic order, explicit None checks)
    style: str | None = None
    if coldef.style_map is not None:
        style = coldef.style_map.get(normalized)
    if style is None and coldef.style_fn is not None:
        style = coldef.style_fn(raw_value, row)
    if style is None:
        style = coldef.default_style

    # 3. Format display value
    if coldef.format_fn is not None:
        display = coldef.format_fn(raw_value, for_csv=for_csv)
    else:
        display = default_format(raw_value, for_csv=for_csv)

    # 4. Return
    if for_csv:
        return display
    if style:
        return Text(display, style=style)
    return Text(display)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_output.py -v`
Expected: All PASS

**Step 5: Run linting and type checks**

Run: `uv run ruff check src/verge_cli/output.py tests/unit/test_output.py && uv run mypy src/verge_cli/output.py`
Expected: No errors

**Step 6: Commit**

```bash
git add src/verge_cli/output.py tests/unit/test_output.py
git commit -m "feat: add render_cell() pipeline for column-aware styling"
```

---

### Task 3: Update format_table() to accept ColumnDef lists

**Files:**
- Modify: `src/verge_cli/output.py:67-112`
- Test: `tests/unit/test_output.py` (add new tests)

**Step 1: Write failing tests for ColumnDef-based format_table**

Append to `tests/unit/test_output.py`:

```python
from verge_cli.output import format_table


class TestFormatTableWithColumnDefs:
    def test_list_of_dicts_with_coldefs(self, capsys) -> None:
        data = [
            {"name": "vm1", "status": "running", "desc": "Web server"},
            {"name": "vm2", "status": "stopped", "desc": "DB server"},
        ]
        cols = [
            ColumnDef("name"),
            ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
            ColumnDef("desc", wide_only=True),
        ]
        format_table(data, columns=cols, no_color=True)
        out = capsys.readouterr().out
        assert "Name" in out
        assert "Status" in out
        assert "vm1" in out
        assert "vm2" in out
        # wide_only column should be hidden in non-wide mode
        assert "Desc" not in out

    def test_wide_mode_shows_all_columns(self, capsys) -> None:
        data = [
            {"name": "vm1", "status": "running", "desc": "Web server"},
        ]
        cols = [
            ColumnDef("name"),
            ColumnDef("status"),
            ColumnDef("desc", header="Description", wide_only=True),
        ]
        format_table(data, columns=cols, wide=True, no_color=True)
        out = capsys.readouterr().out
        assert "Description" in out
        assert "Web server" in out

    def test_empty_list_shows_message(self, capsys) -> None:
        cols = [ColumnDef("name")]
        format_table([], columns=cols, no_color=True)
        out = capsys.readouterr().out
        assert "No results found" in out

    def test_single_dict_key_value(self, capsys) -> None:
        """Single dict still renders as key-value table."""
        data = {"name": "vm1", "status": "running"}
        format_table(data, no_color=True)
        out = capsys.readouterr().out
        assert "name" in out
        assert "vm1" in out

    def test_backward_compat_string_columns(self, capsys) -> None:
        """list[str] columns still work for backward compatibility."""
        data = [{"name": "vm1", "status": "running"}]
        format_table(data, columns=["name", "status"], no_color=True)
        out = capsys.readouterr().out
        assert "Name" in out
        assert "vm1" in out
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_output.py::TestFormatTableWithColumnDefs -v`
Expected: FAIL — `format_table() got an unexpected keyword argument 'wide'`

**Step 3: Update format_table() to handle ColumnDef lists**

Replace `format_table()` in `src/verge_cli/output.py` (lines 67-112) with:

```python
def format_table(
    data: list[dict[str, Any]] | dict[str, Any],
    columns: list[ColumnDef] | list[str] | None = None,
    title: str | None = None,
    no_color: bool = False,
    wide: bool = False,
) -> None:
    """Format and print data as a table.

    Args:
        data: List of dicts or single dict to display.
        columns: ColumnDef list, string list (backward compat), or None (auto-detect).
        title: Optional table title.
        no_color: Disable colors.
        wide: If True, include wide_only columns.
    """
    console = get_console(no_color)

    # Handle single dict (convert to key-value table)
    if isinstance(data, dict):
        table = Table(title=title, box=SIMPLE, show_header=True, header_style="bold")
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        for key, value in data.items():
            table.add_row(str(key), format_value(value))

        console.print(table)
        return

    # Handle empty list
    if not data:
        console.print("[dim]No results found.[/dim]")
        return

    # Resolve columns
    coldefs: list[ColumnDef] | None = None
    str_columns: list[str] | None = None

    if columns is not None and len(columns) > 0:
        if isinstance(columns[0], ColumnDef):
            coldefs = columns  # type: ignore[assignment]
        else:
            str_columns = columns  # type: ignore[assignment]
    else:
        # Auto-detect from first row
        str_columns = list(data[0].keys())

    # ColumnDef path
    if coldefs is not None:
        # Filter wide_only unless wide mode
        visible = [c for c in coldefs if wide or not c.wide_only]

        table = Table(title=title, box=SIMPLE, show_header=True, header_style="bold")
        for col in visible:
            table.add_column(col.resolved_header)

        for row in data:
            cells = [render_cell(row.get(col.key), row, col) for col in visible]
            table.add_row(*cells)

        console.print(table)
        return

    # Legacy string-columns path (backward compatibility)
    assert str_columns is not None
    table = Table(title=title, box=SIMPLE, show_header=True, header_style="bold")
    for col in str_columns:
        table.add_column(col.replace("_", " ").title())

    for row in data:
        table.add_row(*[format_value(row.get(col)) for col in str_columns])

    console.print(table)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_output.py -v`
Expected: All PASS

**Step 5: Run linting**

Run: `uv run ruff check src/verge_cli/output.py tests/unit/test_output.py`
Expected: No errors

**Step 6: Commit**

```bash
git add src/verge_cli/output.py tests/unit/test_output.py
git commit -m "feat: update format_table() to accept ColumnDef lists with wide mode"
```

---

### Task 4: Add format_csv() and update output_result()

**Files:**
- Modify: `src/verge_cli/output.py:196-244`
- Test: `tests/unit/test_output.py` (add new tests)

**Step 1: Write failing tests for CSV and updated output_result**

Append to `tests/unit/test_output.py`:

```python
from verge_cli.output import format_csv


class TestFormatCsv:
    def test_list_of_dicts(self, capsys) -> None:
        data = [
            {"name": "vm1", "status": "running"},
            {"name": "vm2", "status": "stopped"},
        ]
        cols = [
            ColumnDef("name"),
            ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
        ]
        format_csv(data, columns=cols)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[0] == "Name,Status"
        assert lines[1] == "vm1,running"
        assert lines[2] == "vm2,stopped"

    def test_includes_wide_only_columns(self, capsys) -> None:
        data = [{"name": "vm1", "desc": "Web server"}]
        cols = [
            ColumnDef("name"),
            ColumnDef("desc", header="Description", wide_only=True),
        ]
        format_csv(data, columns=cols)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[0] == "Name,Description"
        assert lines[1] == "vm1,Web server"

    def test_bool_flag_csv_output(self, capsys) -> None:
        data = [{"name": "net1", "needs_restart": True}]
        cols = [
            ColumnDef("name"),
            ColumnDef("needs_restart", header="Restart", style_map=FLAG_STYLES, format_fn=format_bool_yn),
        ]
        format_csv(data, columns=cols)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[1] == "net1,true"

    def test_none_value_is_empty(self, capsys) -> None:
        data = [{"name": "vm1", "desc": None}]
        cols = [ColumnDef("name"), ColumnDef("desc")]
        format_csv(data, columns=cols)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[1] == "vm1,"

    def test_empty_list(self, capsys) -> None:
        cols = [ColumnDef("name")]
        format_csv([], columns=cols)
        out = capsys.readouterr().out
        # Should just have the header
        lines = out.strip().split("\n")
        assert lines[0] == "Name"
        assert len(lines) == 1

    def test_csv_quoting(self, capsys) -> None:
        data = [{"name": "vm with, comma", "status": "running"}]
        cols = [ColumnDef("name"), ColumnDef("status")]
        format_csv(data, columns=cols)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert '"vm with, comma"' in lines[1]


class TestOutputResultFormats:
    def test_csv_format(self, capsys) -> None:
        data = [{"name": "vm1", "status": "running"}]
        cols = [ColumnDef("name"), ColumnDef("status")]
        output_result(data, output_format="csv", columns=cols)
        out = capsys.readouterr().out
        assert "Name,Status" in out
        assert "vm1,running" in out

    def test_wide_format(self, capsys) -> None:
        data = [{"name": "vm1", "desc": "Web server"}]
        cols = [
            ColumnDef("name"),
            ColumnDef("desc", header="Description", wide_only=True),
        ]
        output_result(data, output_format="wide", columns=cols, no_color=True)
        out = capsys.readouterr().out
        assert "Description" in out
        assert "Web server" in out

    def test_csv_query_list_scalar(self, capsys) -> None:
        data = [{"name": "vm1"}, {"name": "vm2"}]
        output_result(data, output_format="csv", query="name")
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[0] == "value"
        assert lines[1] == "vm1"
        assert lines[2] == "vm2"

    def test_csv_query_dict(self, capsys) -> None:
        data = {"name": "vm1", "status": "running"}
        output_result(data, output_format="csv", query=None)
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert "name" in lines[0]
        assert "status" in lines[0]
        assert "vm1" in lines[1]

    def test_csv_query_scalar(self, capsys) -> None:
        data = [{"name": "vm1"}]
        output_result(data, output_format="csv", query="0.name")
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert lines[0] == "value"
        assert lines[1] == "vm1"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_output.py::TestFormatCsv -v`
Expected: FAIL — `ImportError: cannot import name 'format_csv' from 'verge_cli.output'`

**Step 3: Add format_csv() to output.py**

Add after the `render_cell()` function:

```python
import csv


def format_csv(
    data: list[dict[str, Any]],
    columns: list[ColumnDef] | None = None,
) -> None:
    """Format and print data as CSV.

    All columns (including wide_only) are included in CSV output.
    Uses render_cell with for_csv=True for machine-friendly values.

    Args:
        data: List of dicts to output.
        columns: ColumnDef list. Auto-detects from data if None.
    """
    if columns is not None:
        coldefs = columns
    elif data:
        coldefs = [ColumnDef(k) for k in data[0].keys()]
    else:
        coldefs = []

    writer = csv.writer(sys.stdout, lineterminator="\n")

    # Header row
    writer.writerow([col.resolved_header for col in coldefs])

    # Data rows
    for row in data:
        cells = [render_cell(row.get(col.key), row, col, for_csv=True) for col in coldefs]
        writer.writerow(cells)
```

**Step 4: Update output_result() to handle all four formats**

Replace `output_result()` in `src/verge_cli/output.py` with:

```python
def output_result(
    data: Any,
    output_format: str = "table",
    query: str | None = None,
    columns: list[ColumnDef] | list[str] | None = None,
    title: str | None = None,
    quiet: bool = False,
    no_color: bool = False,
) -> None:
    """Output data in the specified format.

    Args:
        data: Data to output.
        output_format: Format type ("table", "wide", "json", "csv").
        query: Optional dot-notation query for field extraction.
        columns: ColumnDef or string list for table/csv output.
        title: Optional title for table output.
        quiet: If True, output minimal data (just the value for queries).
        no_color: Disable colored output.
    """
    # Apply query extraction
    if query:
        data = extract_field(data, query)
        if quiet:
            if isinstance(data, (list, dict)):
                print(json.dumps(data, default=json_serializer))
            else:
                print(data if data is not None else "")
            return

    # JSON format — raw data, no styling
    if output_format == "json":
        print(format_json(data))
        return

    # CSV format
    if output_format == "csv":
        _output_csv(data, columns=columns, query=query)
        return

    # Table or wide format
    wide = output_format == "wide"
    if isinstance(data, list):
        if data and not isinstance(data[0], dict):
            # List of simple values (e.g., from --query name)
            console = get_console(no_color)
            for item in data:
                console.print(item if item is not None else "[dim]-[/dim]")
        else:
            format_table(data, columns=columns, title=title, no_color=no_color, wide=wide)
    elif isinstance(data, dict):
        format_table(data, title=title, no_color=no_color)
    else:
        console = get_console(no_color)
        console.print(data if data is not None else "[dim]No result[/dim]")


def _output_csv(
    data: Any,
    columns: list[ColumnDef] | list[str] | None = None,
    query: str | None = None,
) -> None:
    """Route data to CSV output based on data type.

    Handles all query result shapes: list[dict], list[scalar], dict, scalar.
    """
    writer = csv.writer(sys.stdout, lineterminator="\n")

    # list[dict] — normal CSV with columns
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # Convert list[str] columns to ColumnDef if needed
        coldefs: list[ColumnDef] | None = None
        if columns is not None and len(columns) > 0:
            if isinstance(columns[0], ColumnDef):
                coldefs = columns  # type: ignore[assignment]
            else:
                coldefs = [ColumnDef(k) for k in columns]  # type: ignore[union-attr]
        format_csv(data, columns=coldefs)
        return

    # list[scalar] — one column
    if isinstance(data, list):
        header = query.split(".")[-1] if query else "value"
        writer.writerow([header])
        for item in data:
            writer.writerow([default_format(item, for_csv=True)])
        return

    # dict — one row, keys as headers (insertion order)
    if isinstance(data, dict):
        writer.writerow(list(data.keys()))
        writer.writerow([default_format(v, for_csv=True) for v in data.values()])
        return

    # scalar — one row, one column
    writer.writerow(["value"])
    writer.writerow([default_format(data, for_csv=True)])
```

**Step 4b: Add the `csv` import at the top of output.py**

Add to the imports at the top of `src/verge_cli/output.py`:

```python
import csv
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_output.py -v`
Expected: All PASS

**Step 6: Run linting and type checks**

Run: `uv run ruff check src/verge_cli/output.py tests/unit/test_output.py && uv run mypy src/verge_cli/output.py`
Expected: No errors

**Step 7: Commit**

```bash
git add src/verge_cli/output.py tests/unit/test_output.py
git commit -m "feat: add CSV output format and update output_result for wide/csv"
```

---

### Task 5: Update cli.py and context.py — global --output flag

**Files:**
- Modify: `src/verge_cli/cli.py:87-94, 155`
- Modify: `src/verge_cli/context.py:26`

**Step 1: Write failing test for Literal output validation**

Add to `tests/unit/test_cli.py` (or create a new test if the existing test doesn't cover output flags):

```python
# In tests/unit/test_cli.py — add or find test for global --output
def test_output_flag_accepts_valid_formats(cli_runner, mock_client):
    """Test that --output accepts table, wide, json, csv."""
    from verge_cli.cli import app

    for fmt in ["table", "wide", "json", "csv"]:
        result = cli_runner.invoke(app, ["--output", fmt, "system", "info"])
        # Should not fail with invalid format error
        assert result.exit_code != 2, f"--output {fmt} rejected: {result.output}"
```

**Step 2: Run test to verify current behavior**

Run: `uv run pytest tests/unit/test_cli.py::test_output_flag_accepts_valid_formats -v`
Expected: May fail on "wide" or "csv" if we haven't added the Literal yet — or may pass if str accepts anything.

**Step 3: Update cli.py**

In `src/verge_cli/cli.py`, change the `output` parameter (lines 87-94):

Replace:
```python
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output format (table, json).",
        ),
    ] = "table",
```

With:
```python
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output format: table, wide, json, csv.",
        ),
    ] = "table",
```

**Note:** Typer doesn't support `Literal` directly for `typer.Option`. Keep as `str` but update help text. Validation happens naturally because `output_result()` handles the routing. The design doc's `Literal` type is aspirational — Typer's `click` backend doesn't enforce it. If needed, add a `click.Choice` constraint instead:

```python
    output: Annotated[
        str,
        typer.Option(
            "--output",
            "-o",
            help="Output format.",
            click_type=click.Choice(["table", "wide", "json", "csv"]),
        ),
    ] = "table",
```

This requires adding `import click` at the top of `cli.py`.

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_cli.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/verge_cli/cli.py tests/unit/test_cli.py
git commit -m "feat: update global --output flag to support table, wide, json, csv"
```

---

### Task 6: Add column definitions for all resources to columns.py

**Files:**
- Modify: `src/verge_cli/columns.py`
- Test: `tests/unit/test_columns.py` (add validation tests)

**Step 1: Write tests that validate column definitions exist and have correct keys**

Append to `tests/unit/test_columns.py`:

```python
from verge_cli.columns import (
    VM_COLUMNS,
    NETWORK_COLUMNS,
    RULE_COLUMNS,
    ZONE_COLUMNS,
    RECORD_COLUMNS,
    VIEW_COLUMNS,
    HOST_COLUMNS,
    ALIAS_COLUMNS,
    LEASE_COLUMNS,
    ADDRESS_COLUMNS,
    DRIVE_COLUMNS,
    NIC_COLUMNS,
    DEVICE_COLUMNS,
)


class TestColumnDefinitions:
    def test_vm_columns_has_name_and_status(self) -> None:
        keys = [c.key for c in VM_COLUMNS]
        assert "name" in keys
        assert "status" in keys
        assert "needs_restart" in keys

    def test_vm_columns_status_has_style(self) -> None:
        status_col = next(c for c in VM_COLUMNS if c.key == "status")
        assert status_col.style_map is not None
        assert status_col.normalize_fn is not None

    def test_network_columns_has_flags(self) -> None:
        keys = [c.key for c in NETWORK_COLUMNS]
        assert "needs_restart" in keys
        assert "needs_rule_apply" in keys
        assert "needs_dns_apply" in keys

    def test_all_column_lists_are_non_empty(self) -> None:
        for name, cols in [
            ("VM", VM_COLUMNS),
            ("NETWORK", NETWORK_COLUMNS),
            ("RULE", RULE_COLUMNS),
            ("ZONE", ZONE_COLUMNS),
            ("RECORD", RECORD_COLUMNS),
            ("VIEW", VIEW_COLUMNS),
            ("HOST", HOST_COLUMNS),
            ("ALIAS", ALIAS_COLUMNS),
            ("LEASE", LEASE_COLUMNS),
            ("ADDRESS", ADDRESS_COLUMNS),
            ("DRIVE", DRIVE_COLUMNS),
            ("NIC", NIC_COLUMNS),
            ("DEVICE", DEVICE_COLUMNS),
        ]:
            assert len(cols) > 0, f"{name}_COLUMNS is empty"

    def test_wide_only_columns_exist(self) -> None:
        """At least VM and NETWORK should have wide_only columns."""
        vm_wide = [c for c in VM_COLUMNS if c.wide_only]
        net_wide = [c for c in NETWORK_COLUMNS if c.wide_only]
        assert len(vm_wide) > 0
        assert len(net_wide) > 0
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_columns.py::TestColumnDefinitions -v`
Expected: FAIL — `ImportError: cannot import name 'VM_COLUMNS'`

**Step 3: Add all column definitions to columns.py**

Append to `src/verge_cli/columns.py`:

```python
# ---------------------------------------------------------------------------
# Resource column definitions
# ---------------------------------------------------------------------------

VM_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("cpu_cores", header="CPU"),
    ColumnDef("ram", header="RAM (MB)"),
    ColumnDef("cluster_name", header="Cluster"),
    ColumnDef("node_name", header="Node"),
    ColumnDef("needs_restart", header="Restart", style_map=FLAG_STYLES, format_fn=format_bool_yn),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("os_family", header="OS", wide_only=True),
    ColumnDef("key", wide_only=True),
]

NETWORK_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("type"),
    ColumnDef("network", header="CIDR"),
    ColumnDef("ipaddress", header="IP Address"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("running", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    ColumnDef("needs_restart", header="Restart", style_map=FLAG_STYLES, format_fn=format_bool_yn),
    ColumnDef("needs_rule_apply", header="Rules", style_map=FLAG_STYLES, format_fn=format_bool_yn),
    ColumnDef("needs_dns_apply", header="DNS", style_map=FLAG_STYLES, format_fn=format_bool_yn),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("gateway", wide_only=True),
    ColumnDef("mtu", wide_only=True),
    ColumnDef("key", wide_only=True),
]

RULE_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("direction"),
    ColumnDef("action"),
    ColumnDef("protocol"),
    ColumnDef("source_ip", header="Source"),
    ColumnDef("dest_ports", header="Dest Ports"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    ColumnDef("order"),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("dest_ip", header="Dest IP", wide_only=True),
    ColumnDef("key", wide_only=True),
]

ZONE_COLUMNS = [
    ColumnDef("id"),
    ColumnDef("domain"),
    ColumnDef("type"),
    ColumnDef("view_name", header="View"),
    ColumnDef("serial"),
]

RECORD_COLUMNS = [
    ColumnDef("id"),
    ColumnDef("host"),
    ColumnDef("type"),
    ColumnDef("value"),
    ColumnDef("ttl", header="TTL"),
    ColumnDef("priority"),
]

VIEW_COLUMNS = [
    ColumnDef("id"),
    ColumnDef("name"),
    ColumnDef("recursion", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    ColumnDef("match_clients", header="Match Clients"),
]

HOST_COLUMNS = [
    ColumnDef("host"),
    ColumnDef("ip", header="IP"),
    ColumnDef("type"),
]

ALIAS_COLUMNS = [
    ColumnDef("hostname"),
    ColumnDef("ip", header="IP"),
    ColumnDef("description"),
]

LEASE_COLUMNS = [
    ColumnDef("mac", header="MAC"),
    ColumnDef("ip", header="IP"),
    ColumnDef("hostname"),
    ColumnDef("expires"),
    ColumnDef("state"),
]

ADDRESS_COLUMNS = [
    ColumnDef("ip", header="IP"),
    ColumnDef("mac", header="MAC"),
    ColumnDef("interface"),
    ColumnDef("type"),
]

DRIVE_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("media"),
    ColumnDef("interface"),
    ColumnDef("size_gb", header="Size (GB)"),
    ColumnDef("tier"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    # wide-only
    ColumnDef("key", wide_only=True),
]

NIC_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("interface"),
    ColumnDef("network_name", header="Network"),
    ColumnDef("mac_address", header="MAC"),
    ColumnDef("ip_address", header="IP"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    # wide-only
    ColumnDef("key", wide_only=True),
]

DEVICE_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("device_type", header="Type"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    ColumnDef("optional", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    # wide-only
    ColumnDef("key", wide_only=True),
]
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_columns.py -v`
Expected: All PASS

**Step 5: Run linting**

Run: `uv run ruff check src/verge_cli/columns.py`
Expected: No errors

**Step 6: Commit**

```bash
git add src/verge_cli/columns.py tests/unit/test_columns.py
git commit -m "feat: add column definitions for all resource types"
```

---

### Task 7: Migrate vm.py — clean _vm_to_dict(), use VM_COLUMNS, remove per-cmd --output

**Files:**
- Modify: `src/verge_cli/commands/vm.py:26, 41-44, 64-70, 79-82, 94-100, 474-493`
- Test: Run existing `tests/unit/test_vm_status.py` to verify no regressions

**Step 1: Update vm.py**

1. Remove `VM_LIST_COLUMNS` (line 26)
2. Remove `--output` and `--query` options from `vm_list` and `vm_get` commands
3. Import `VM_COLUMNS` from `columns.py`
4. Update `output_result()` calls to pass `VM_COLUMNS`
5. Clean `_vm_to_dict()` — remove synthetic `"restart": "Y"/""`

In `src/verge_cli/commands/vm.py`:

Change imports to include:
```python
from verge_cli.columns import VM_COLUMNS
```

Remove `VM_LIST_COLUMNS` constant (line 26).

In `vm_list()`, remove the `output` and `query` parameters and update the `output_result()` call:
```python
@app.command("list")
@handle_errors()
def vm_list(
    ctx: typer.Context,
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="Filter by status (running, stopped, etc.)"),
    ] = None,
    filter: Annotated[
        str | None,
        typer.Option("--filter", help="OData filter expression (e.g., \"name eq 'foo'\")"),
    ] = None,
) -> None:
    """List virtual machines."""
    vctx = get_context(ctx)

    odata_filter = filter
    if status:
        status_filter = f"status eq '{status}'"
        odata_filter = f"({odata_filter}) and {status_filter}" if odata_filter else status_filter

    vms = vctx.client.vms.list(filter=odata_filter)
    data = [_vm_to_dict(vm) for vm in vms]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=VM_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

In `vm_get()`, remove the `output` and `query` parameters:
```python
@app.command("get")
@handle_errors()
def vm_get(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
) -> None:
    """Get details of a virtual machine."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    output_result(
        _vm_to_dict(vm_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

Clean `_vm_to_dict()` — remove the synthetic `"restart"` alias:
```python
def _vm_to_dict(vm: Any) -> dict[str, Any]:
    """Convert a VM object to a dictionary for output."""
    return {
        "key": vm.key,
        "name": vm.name,
        "description": vm.get("description", ""),
        "status": vm.status,
        "running": vm.is_running,
        "cpu_cores": vm.get("cpu_cores"),
        "ram": vm.get("ram"),
        "os_family": vm.get("os_family"),
        "cluster_name": vm.cluster_name,
        "node_name": vm.node_name,
        "created": vm.get("created"),
        "modified": vm.get("modified"),
        "needs_restart": vm.get("need_restart", False),
    }
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/unit/test_vm_status.py tests/unit/test_vm_create_template.py -v`
Expected: All PASS (existing tests should not break since they test via cli_runner)

**Step 3: Run linting**

Run: `uv run ruff check src/verge_cli/commands/vm.py`
Expected: No errors

**Step 4: Commit**

```bash
git add src/verge_cli/commands/vm.py
git commit -m "refactor: migrate vm.py to ColumnDef, clean _vm_to_dict"
```

---

### Task 8: Migrate network.py — clean _network_to_dict(), use NETWORK_COLUMNS

**Files:**
- Modify: `src/verge_cli/commands/network.py:35-45, 64-67, 90-97, 105-108, 120-126, 405-408, 435-461`

**Step 1: Update network.py**

Same pattern as Task 7:

1. Remove `NETWORK_LIST_COLUMNS` (lines 35-45)
2. Import `NETWORK_COLUMNS` from `columns.py`
3. Remove `--output` and `--query` from `network_list`, `network_get`, `network_status`
4. Update all `output_result()` calls
5. Clean `_network_to_dict()` — remove synthetic `"restart"`, `"rules"`, `"dns_apply"` aliases

Replace `_network_to_dict()` with:
```python
def _network_to_dict(net: Any) -> dict[str, Any]:
    """Convert a Network object to a dictionary for output."""
    return {
        "key": net.key,
        "name": net.name,
        "description": net.get("description", ""),
        "type": net.get("type"),
        "network": net.get("network"),
        "ipaddress": net.get("ipaddress"),
        "gateway": net.get("gateway"),
        "mtu": net.get("mtu"),
        "status": net.get("status"),
        "running": net.get("running"),
        "dhcp_enabled": net.get("dhcp_enabled"),
        "dhcp_start": net.get("dhcp_start"),
        "dhcp_stop": net.get("dhcp_stop"),
        "dns": net.get("dns"),
        "domain": net.get("domain"),
        "needs_restart": net.get("need_restart", False),
        "needs_rule_apply": net.get("need_fw_apply", False),
        "needs_dns_apply": net.get("need_dns_apply", False),
    }
```

**Step 2: Run existing tests**

Run: `uv run pytest tests/unit/test_network_operations.py tests/unit/test_network_status.py tests/unit/test_network_create.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add src/verge_cli/commands/network.py
git commit -m "refactor: migrate network.py to ColumnDef, clean _network_to_dict"
```

---

### Task 9: Migrate remaining command files (batch)

**Files:**
- Modify: `src/verge_cli/commands/network_rule.py`
- Modify: `src/verge_cli/commands/network_dns.py`
- Modify: `src/verge_cli/commands/network_host.py`
- Modify: `src/verge_cli/commands/network_alias.py`
- Modify: `src/verge_cli/commands/network_diag.py`
- Modify: `src/verge_cli/commands/vm_drive.py`
- Modify: `src/verge_cli/commands/vm_nic.py`
- Modify: `src/verge_cli/commands/vm_device.py`

**Pattern for each file:**
1. Remove the `XXX_LIST_COLUMNS` string list constant
2. Add import: `from verge_cli.columns import XXX_COLUMNS`
3. Remove per-command `--output` and `--query` options (where they exist)
4. Update `output_result()` calls to use `columns=XXX_COLUMNS`
5. If `_to_dict()` has synthetic string aliases, replace with raw bools

**Specific mapping:**

| File | Old constant | New import | Has per-cmd --output |
|------|-------------|-----------|---------------------|
| `network_rule.py` | `RULE_LIST_COLUMNS` | `RULE_COLUMNS` | Yes |
| `network_dns.py` | `ZONE_LIST_COLUMNS`, `RECORD_LIST_COLUMNS`, `VIEW_LIST_COLUMNS` | `ZONE_COLUMNS`, `RECORD_COLUMNS`, `VIEW_COLUMNS` | Yes |
| `network_host.py` | `HOST_LIST_COLUMNS` | `HOST_COLUMNS` | Yes |
| `network_alias.py` | `ALIAS_LIST_COLUMNS` | `ALIAS_COLUMNS` | Yes |
| `network_diag.py` | `LEASE_LIST_COLUMNS`, `ADDRESS_LIST_COLUMNS` | `LEASE_COLUMNS`, `ADDRESS_COLUMNS` | Yes |
| `vm_drive.py` | `DRIVE_LIST_COLUMNS` | `DRIVE_COLUMNS` | No |
| `vm_nic.py` | `NIC_LIST_COLUMNS` | `NIC_COLUMNS` | No |
| `vm_device.py` | `DEVICE_LIST_COLUMNS` | `DEVICE_COLUMNS` | No |

**Step 1: Apply pattern to all 8 files**

Each file follows the exact same mechanical transformation. See Task 7/8 for the detailed pattern.

**Step 2: Run all tests**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 3: Run linting on all modified files**

Run: `uv run ruff check src/verge_cli/commands/`
Expected: No errors

**Step 4: Commit**

```bash
git add src/verge_cli/commands/network_rule.py src/verge_cli/commands/network_dns.py \
    src/verge_cli/commands/network_host.py src/verge_cli/commands/network_alias.py \
    src/verge_cli/commands/network_diag.py src/verge_cli/commands/vm_drive.py \
    src/verge_cli/commands/vm_nic.py src/verge_cli/commands/vm_device.py
git commit -m "refactor: migrate all remaining commands to ColumnDef"
```

---

### Task 10: Update mock_vm and mock_network fixtures for new dict keys

**Files:**
- Modify: `tests/conftest.py:66-75, 88-104`

**Step 1: Update mock_vm fixture**

The `mock_vm` fixture needs `need_restart` in its mock data so `_vm_to_dict()` can read it:

In `tests/conftest.py`, update `mock_get` in `mock_vm()`:
```python
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Test VM",
            "cpu_cores": 2,
            "ram": 2048,
            "os_family": "linux",
            "created": "2024-01-01T00:00:00Z",
            "modified": "2024-01-02T00:00:00Z",
            "need_restart": False,
        }
        return data.get(key, default)
```

Update `mock_network()` to include the flag fields:
```python
    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Test Network",
            "type": "internal",
            "network": "10.0.0.0/24",
            "ipaddress": "10.0.0.1",
            "gateway": "10.0.0.1",
            "mtu": 1500,
            "status": "running",
            "running": True,
            "dhcp_enabled": True,
            "dhcp_start": "10.0.0.100",
            "dhcp_stop": "10.0.0.200",
            "dns": "10.0.0.1",
            "domain": "test.local",
            "need_restart": False,
            "need_fw_apply": False,
            "need_dns_apply": False,
        }
        return data.get(key, default)
```

**Step 2: Run all tests**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: update fixtures with flag fields for ColumnDef migration"
```

---

### Task 11: Full verification

**Files:** None (verification only)

**Step 1: Run full test suite**

Run: `uv run pytest tests/unit/ -v --tb=short`
Expected: All PASS

**Step 2: Run linting**

Run: `uv run ruff check`
Expected: No errors

**Step 3: Run type checking**

Run: `uv run mypy .`
Expected: No errors (or only pre-existing issues)

**Step 4: Spot check CLI behavior**

Run: `uv run vrg --help`
Expected: Shows `--output` with updated help text

Run: `uv run vrg --output csv vm list --help`
Expected: Help text renders, no crash

**Step 5: Commit any fixes from verification**

If any issues found, fix and commit with descriptive message.

**Step 6: Final commit (if all clean)**

```bash
git add -A
git commit -m "chore: output improvements verification — all checks pass"
```

(Only if there are unstaged fixes. Skip if everything was already committed.)

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|-----------|
| 1 | columns.py — ColumnDef, style maps, helpers | 6 |
| 2 | render_cell() + default_format() in output.py | 6 |
| 3 | Update format_table() for ColumnDef lists | 6 |
| 4 | format_csv() + update output_result() | 7 |
| 5 | cli.py + context.py — global --output flag | 5 |
| 6 | Column definitions for all resources | 6 |
| 7 | Migrate vm.py | 4 |
| 8 | Migrate network.py | 3 |
| 9 | Migrate remaining 8 command files (batch) | 4 |
| 10 | Update test fixtures | 3 |
| 11 | Full verification | 6 |
