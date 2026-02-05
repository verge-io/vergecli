"""Output formatting utilities for Verge CLI."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any

from rich.box import SIMPLE
from rich.console import Console
from rich.table import Table


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
    columns: list[str] | None = None,
    title: str | None = None,
    no_color: bool = False,
) -> None:
    """Format and print data as a table.

    Args:
        data: List of dicts or single dict to display.
        columns: Column names to display (auto-detected if None).
        title: Optional table title.
        no_color: Disable colors.
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

    # Auto-detect columns from first row if not specified
    if columns is None:
        columns = list(data[0].keys())

    table = Table(title=title, box=SIMPLE, show_header=True, header_style="bold")

    for col in columns:
        table.add_column(col.replace("_", " ").title())

    for row in data:
        table.add_row(*[format_value(row.get(col)) for col in columns])

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
