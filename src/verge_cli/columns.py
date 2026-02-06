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
    ColumnDef(
        "needs_restart",
        header="Restart",
        style_map=FLAG_STYLES,
        format_fn=format_bool_yn,
    ),
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
    ColumnDef(
        "needs_restart",
        header="Restart",
        style_map=FLAG_STYLES,
        format_fn=format_bool_yn,
    ),
    ColumnDef(
        "needs_rule_apply",
        header="Rules",
        style_map=FLAG_STYLES,
        format_fn=format_bool_yn,
    ),
    ColumnDef(
        "needs_dns_apply",
        header="DNS",
        style_map=FLAG_STYLES,
        format_fn=format_bool_yn,
    ),
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
