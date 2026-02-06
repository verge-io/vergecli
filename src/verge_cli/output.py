"""Output formatting utilities for Verge CLI."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

from rich.box import SIMPLE
from rich.console import Console
from rich.table import Table
from rich.text import Text

from verge_cli.columns import ColumnDef, default_format


def is_tty() -> bool:
    """Check if stdout is a TTY (interactive terminal)."""
    return sys.stdout.isatty()


def get_console(no_color: bool = False) -> Console:
    """Get a Rich console with appropriate settings.

    Args:
        no_color: Force disable colors.

    Returns:
        Console configured for current environment.
    """
    force_terminal = None
    if not is_tty():
        force_terminal = False
    return Console(
        force_terminal=force_terminal,
        no_color=no_color or not is_tty(),
    )


def json_serializer(obj: Any) -> str:
    """JSON serializer that handles datetime and other types.

    Args:
        obj: Object to serialize.

    Returns:
        String representation.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def format_json(data: Any, query: str | None = None) -> str:
    """Format data as JSON.

    Args:
        data: Data to format.
        query: Optional dot-notation query to extract specific field.

    Returns:
        JSON string.
    """
    if query:
        data = extract_field(data, query)
    return json.dumps(data, indent=2, default=json_serializer)


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


def format_value(value: Any) -> str:
    """Format a single value for table display.

    Args:
        value: Value to format.

    Returns:
        String representation.
    """
    if value is None:
        return "[dim]-[/dim]"
    if isinstance(value, bool):
        return "[green]yes[/green]" if value else "[red]no[/red]"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=json_serializer)
    return str(value)


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


def extract_field(data: Any, query: str) -> Any:
    """Extract a field using simple dot notation.

    Supports:
    - Simple field: "name" -> data["name"]
    - Nested field: "config.host" -> data["config"]["host"]
    - Array index: "items.0.name" -> data["items"][0]["name"]
    - Array field extraction: "[].name" -> [item["name"] for item in data]

    Args:
        data: Data to extract from.
        query: Dot-notation query string.

    Returns:
        Extracted value or original data if query fails.
    """
    if not query:
        return data

    parts = query.split(".")
    result = data

    for part in parts:
        if result is None:
            return None

        # Handle array extraction: []
        if part == "[]":
            if isinstance(result, list):
                continue
            return result

        # Handle array index
        if part.isdigit():
            idx = int(part)
            if isinstance(result, list) and idx < len(result):
                result = result[idx]
            else:
                return None
            continue

        # Handle list of dicts - extract field from each
        if isinstance(result, list):
            result = [item.get(part) if isinstance(item, dict) else None for item in result]
            continue

        # Handle dict field access
        if isinstance(result, dict):
            result = result.get(part)
            continue

        # Handle object attribute access
        if hasattr(result, part):
            result = getattr(result, part)
            continue

        return None

    return result


def output_result(
    data: Any,
    output_format: str = "table",
    query: str | None = None,
    columns: list[str] | None = None,
    title: str | None = None,
    quiet: bool = False,
    no_color: bool = False,
) -> None:
    """Output data in the specified format.

    Args:
        data: Data to output.
        output_format: Format type ("table" or "json").
        query: Optional dot-notation query for field extraction.
        columns: Column names for table output.
        title: Optional title for table output.
        quiet: If True, output minimal data (just the value for queries).
        no_color: Disable colored output.
    """
    # Apply query extraction
    if query:
        data = extract_field(data, query)
        if quiet:
            # In quiet mode with a query, just print the raw value
            if isinstance(data, (list, dict)):
                print(json.dumps(data, default=json_serializer))
            else:
                print(data if data is not None else "")
            return

    if output_format == "json":
        print(format_json(data))
    else:
        if isinstance(data, list):
            # Check if it's a list of simple values (not dicts) - e.g., from --query name
            if data and not isinstance(data[0], dict):
                # Print simple values as newline-separated list
                console = get_console(no_color)
                for item in data:
                    console.print(item if item is not None else "[dim]-[/dim]")
            else:
                format_table(data, columns=columns, title=title, no_color=no_color)
        elif isinstance(data, dict):
            format_table(data, title=title, no_color=no_color)
        else:
            # Simple value
            console = get_console(no_color)
            console.print(data if data is not None else "[dim]No result[/dim]")


def output_success(message: str, quiet: bool = False, no_color: bool = False) -> None:
    """Output a success message.

    Args:
        message: Success message to display.
        quiet: If True, suppress the message.
        no_color: Disable colored output.
    """
    if quiet:
        return
    console = get_console(no_color)
    console.print(f"[green]✓[/green] {message}")


def output_error(message: str, no_color: bool = False) -> None:
    """Output an error message to stderr.

    Args:
        message: Error message to display.
        no_color: Disable colored output.
    """
    console = Console(stderr=True, no_color=no_color)
    console.print(f"[red]Error:[/red] {message}")


def output_warning(message: str, quiet: bool = False, no_color: bool = False) -> None:
    """Output a warning message.

    Args:
        message: Warning message to display.
        quiet: If True, suppress the message.
        no_color: Disable colored output.
    """
    if quiet:
        return
    console = get_console(no_color)
    console.print(f"[yellow]Warning:[/yellow] {message}")
