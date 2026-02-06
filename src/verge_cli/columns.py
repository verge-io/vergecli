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
    """Column definition with display and styling hints."""

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
    """Default formatter for cell values."""
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
