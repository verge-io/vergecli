"""Human-friendly unit parsing and formatting for RAM and disk sizes."""

from __future__ import annotations

import re

_UNIT_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*(MB|GB|TB)$", re.IGNORECASE)

_TO_MB = {"MB": 1, "GB": 1024, "TB": 1024 * 1024}
_TO_GB = {"MB": 1 / 1024, "GB": 1, "TB": 1024}


def _parse_value_unit(value: str | int) -> tuple[float, str]:
    """Parse a value with unit suffix into (number, unit).

    Args:
        value: String like '4GB', '512MB', or int (passthrough).

    Returns:
        Tuple of (numeric_value, unit_string).

    Raises:
        ValueError: If format is invalid.
    """
    if isinstance(value, int):
        return (float(value), "RAW")

    text = str(value).strip()

    # Plain number string — passthrough
    try:
        return (float(text), "RAW")
    except ValueError:
        pass

    match = _UNIT_PATTERN.match(text)
    if not match:
        msg = f"Invalid size format: '{value}'. Expected format like '4GB', '512MB', '1TB'."
        raise ValueError(msg)

    num = float(match.group(1))
    unit = match.group(2).upper()

    if unit not in _TO_MB:
        msg = f"Invalid size unit: '{unit}'. Expected MB, GB, or TB."
        raise ValueError(msg)

    return (num, unit)


def parse_ram(value: str | int) -> int:
    """Parse a RAM value to megabytes.

    Accepts: '512MB', '4GB', '1TB', or int (treated as MB).

    Args:
        value: RAM specification.

    Returns:
        RAM in megabytes (int).

    Raises:
        ValueError: If format is invalid or value is not positive.
    """
    num, unit = _parse_value_unit(value)

    if unit == "RAW":
        mb = num
    else:
        mb = num * _TO_MB[unit]

    if mb <= 0:
        msg = f"RAM must be positive, got: {value}"
        raise ValueError(msg)

    return int(mb)


def parse_disk_size(value: str | int) -> int:
    """Parse a disk size value to gigabytes.

    Accepts: '50GB', '1TB', '512MB', or int (treated as GB).

    Args:
        value: Disk size specification.

    Returns:
        Disk size in gigabytes (int).

    Raises:
        ValueError: If format is invalid.
    """
    num, unit = _parse_value_unit(value)

    if unit == "RAW":
        gb = num
    else:
        gb = num * _TO_GB[unit]

    return int(gb)


def format_ram(mb: int) -> str:
    """Format megabytes to human-friendly string.

    Args:
        mb: RAM in megabytes.

    Returns:
        Human-friendly string like '4GB', '512MB'.
    """
    if mb >= 1048576 and mb % 1048576 == 0:
        return f"{mb // 1048576}TB"
    if mb >= 1024 and mb % 1024 == 0:
        return f"{mb // 1024}GB"
    return f"{mb}MB"


def format_disk_size(gb: int) -> str:
    """Format gigabytes to human-friendly string.

    Args:
        gb: Disk size in gigabytes.

    Returns:
        Human-friendly string like '50GB', '1TB'.
    """
    if gb >= 1024 and gb % 1024 == 0:
        return f"{gb // 1024}TB"
    return f"{gb}GB"
