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
    "maintenance": "yellow",
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


def format_epoch(value: Any, *, for_csv: bool = False) -> str:
    """Format an epoch timestamp as a datetime string."""
    if value is None:
        return "" if for_csv else "-"
    if isinstance(value, (int, float)) and value > 0:
        dt = datetime.fromtimestamp(value)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def format_epoch_or_never(value: Any, *, for_csv: bool = False) -> str:
    """Format an epoch timestamp, treating 0/None as 'Never'."""
    if value is None or value == 0:
        return "" if for_csv else "Never"
    return format_epoch(value, for_csv=for_csv)


def style_percent_threshold(value: Any, row: dict[str, Any]) -> str | None:
    """Style function for percentage values — red >80, yellow >60."""
    if isinstance(value, (int, float)):
        if value > 80:
            return "red bold"
        if value > 60:
            return "yellow"
    return None


# ---------------------------------------------------------------------------
# Resource column definitions
# ---------------------------------------------------------------------------

VM_COLUMNS = [
    ColumnDef("$key", header="Key"),
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
]

NETWORK_COLUMNS = [
    ColumnDef("$key", header="Key"),
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
]

RULE_COLUMNS = [
    ColumnDef("$key", header="Key"),
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
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("media"),
    ColumnDef("interface"),
    ColumnDef("size_gb", header="Size (GB)"),
    ColumnDef("tier"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
]

NIC_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("interface"),
    ColumnDef("network_name", header="Network"),
    ColumnDef("mac_address", header="MAC"),
    ColumnDef("ip_address", header="IP"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
]

DEVICE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("device_type", header="Type"),
    ColumnDef("enabled", style_map=BOOL_STYLES, format_fn=format_bool_yn),
    ColumnDef("optional", style_map=BOOL_STYLES, format_fn=format_bool_yn),
]

TENANT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("state"),
    ColumnDef(
        "is_isolated",
        header="Isolated",
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("network_name", header="Network", wide_only=True),
    ColumnDef("ui_address_ip", header="UI IP", wide_only=True),
    ColumnDef("uuid", wide_only=True),
]

CLUSTER_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("total_nodes", header="Nodes"),
    ColumnDef("online_nodes", header="Online"),
    ColumnDef("total_ram_gb", header="RAM GB"),
    ColumnDef("ram_used_percent", header="RAM %", style_fn=style_percent_threshold),
    ColumnDef("total_cores", header="Cores"),
    # wide-only
    ColumnDef("running_machines", header="Running VMs", wide_only=True),
    ColumnDef(
        "is_compute",
        header="Compute",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    ColumnDef(
        "is_storage",
        header="Storage",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
]

NODE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("cluster_name", header="Cluster"),
    ColumnDef("ram_gb", header="RAM GB"),
    ColumnDef("cores"),
    ColumnDef("cpu_usage", header="CPU %", style_fn=style_percent_threshold),
    # wide-only
    ColumnDef(
        "is_physical",
        header="Physical",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    ColumnDef("model", wide_only=True),
    ColumnDef("cpu", header="CPU", wide_only=True),
    ColumnDef("core_temp", header="Temp °C", wide_only=True, style_fn=style_percent_threshold),
    ColumnDef("vergeos_version", header="Version", wide_only=True),
]

STORAGE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("tier", header="Tier #"),
    ColumnDef("description"),
    ColumnDef("capacity_gb", header="Capacity GB"),
    ColumnDef("used_gb", header="Used GB"),
    ColumnDef("free_gb", header="Free GB"),
    ColumnDef("used_percent", header="Used %", style_fn=style_percent_threshold),
    # wide-only
    ColumnDef("dedupe_ratio", header="Dedupe", wide_only=True),
    ColumnDef("dedupe_savings_percent", header="Savings %", wide_only=True),
    ColumnDef("read_ops", header="Read IOPS", wide_only=True),
    ColumnDef("write_ops", header="Write IOPS", wide_only=True),
]

VSAN_STATUS_COLUMNS = [
    ColumnDef("cluster_name", header="Cluster"),
    ColumnDef(
        "health_status",
        header="Health",
        style_map={
            "Healthy": "green",
            "Degraded": "yellow",
            "Critical": "red bold",
            "Offline": "red",
        },
    ),
    ColumnDef("total_nodes", header="Nodes"),
    ColumnDef("online_nodes", header="Online"),
    ColumnDef("used_ram_gb", header="RAM Used GB"),
    ColumnDef("online_ram_gb", header="RAM Total GB"),
    ColumnDef("ram_used_percent", header="RAM %", style_fn=style_percent_threshold),
    # wide-only
    ColumnDef("total_cores", header="Cores", wide_only=True),
    ColumnDef("online_cores", header="Online Cores", wide_only=True),
    ColumnDef("used_cores", header="Used Cores", wide_only=True),
    ColumnDef(
        "core_used_percent", header="Core %", wide_only=True, style_fn=style_percent_threshold
    ),
    ColumnDef("running_machines", header="Running VMs", wide_only=True),
]

TENANT_NODE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("cpu_cores", header="CPU"),
    ColumnDef("ram_gb", header="RAM GB"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("is_enabled", header="Enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    # wide-only
    ColumnDef("cluster_name", header="Cluster", wide_only=True),
    ColumnDef("host_node", header="Host Node", wide_only=True),
]

TENANT_STORAGE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("tier_name", header="Tier"),
    ColumnDef("provisioned_gb", header="Provisioned GB"),
    # wide-only
    ColumnDef("used_gb", header="Used GB", wide_only=True),
    ColumnDef(
        "used_percent",
        header="Used %",
        wide_only=True,
        style_fn=style_percent_threshold,
    ),
]

TENANT_NET_BLOCK_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("cidr", header="CIDR"),
    ColumnDef("network_name", header="Network"),
    # wide-only
    ColumnDef("description", wide_only=True),
]

TENANT_EXT_IP_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("ip_address", header="IP"),
    ColumnDef("network_name", header="Network"),
    # wide-only
    ColumnDef("hostname", wide_only=True),
]

TENANT_L2_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("network_name", header="Network"),
    ColumnDef("network_type", header="Type"),
    ColumnDef("is_enabled", header="Enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
]

VM_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("quiesced", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("description", wide_only=True),
]

TENANT_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("profile", wide_only=True),
]

TENANT_STATS_COLUMNS = [
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("cpu_percent", header="CPU %", style_fn=style_percent_threshold),
    ColumnDef("ram_used_mb", header="RAM Used MB"),
    ColumnDef("ram_total_mb", header="RAM Total MB"),
    ColumnDef("disk_read_ops", header="Disk Read IOPS"),
    ColumnDef("disk_write_ops", header="Disk Write IOPS"),
]

TENANT_LOG_COLUMNS = [
    ColumnDef("timestamp", header="Time"),
    ColumnDef("type", header="Type"),
    ColumnDef("message", header="Message"),
]

CLOUD_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("immutable", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("private", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("description", wide_only=True),
]

CLOUD_SNAPSHOT_VM_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
]

CLOUD_SNAPSHOT_TENANT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
]

SNAPSHOT_PROFILE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("description", wide_only=True),
]

SITE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("url", header="URL"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    ColumnDef("authentication_status", header="Auth Status"),
    # wide-only
    ColumnDef("config_cloud_snapshots", header="Cloud Snapshots", wide_only=True),
    ColumnDef("description", wide_only=True),
    ColumnDef("domain", wide_only=True),
    ColumnDef("city", wide_only=True),
    ColumnDef("country", wide_only=True),
]

SNAPSHOT_PROFILE_PERIOD_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("frequency"),
    ColumnDef("retention", header="Retention (s)"),
    ColumnDef("min_snapshots", header="Min Snaps"),
    ColumnDef("max_tier", header="Max Tier"),
    # wide-only
    ColumnDef("minute", wide_only=True),
    ColumnDef("hour", wide_only=True),
    ColumnDef("day_of_week", header="Day of Week", wide_only=True),
    ColumnDef("quiesce", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef("immutable", format_fn=format_bool_yn, style_map=BOOL_STYLES, wide_only=True),
    ColumnDef(
        "skip_missed",
        header="Skip Missed",
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
        wide_only=True,
    ),
]
