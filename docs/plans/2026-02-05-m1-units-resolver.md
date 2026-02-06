# Milestone 1: Foundation — units.py + resolver.py

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create the shared utility modules that all subsequent milestones depend on.

**Architecture:** Two modules in `src/verge_cli/template/` — `units.py` for human-friendly unit parsing (RAM/disk sizes) and `resolver.py` for batch name→ID resolution via the pyvergeos SDK.

**Tech Stack:** Python 3.10+, pyvergeos SDK, pytest

**Prerequisites:** Add `pyyaml` and `jsonschema` dependencies to pyproject.toml (needed by M3+ but add now to avoid mid-plan dependency changes).

---

### Task 1: Add dependencies and create template package

**Files:**
- Modify: `pyproject.toml` (add pyyaml, jsonschema)
- Create: `src/verge_cli/template/__init__.py`

**Step 1: Add dependencies to pyproject.toml**

In the `dependencies` list, add:
```
"pyyaml>=6.0",
"jsonschema>=4.0",
```

**Step 2: Create template package**

```python
# src/verge_cli/template/__init__.py
"""Template system for declarative VM provisioning."""
```

**Step 3: Sync dependencies**

Run: `uv sync`
Expected: Clean install with new deps

**Step 4: Verify**

Run: `uv run python -c "import yaml; import jsonschema; print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/verge_cli/template/__init__.py
git commit -m "feat: add template package and pyyaml/jsonschema dependencies"
```

---

### Task 2: Create template/units.py

**Files:**
- Create: `src/verge_cli/template/units.py`
- Create: `tests/unit/test_template_units.py`

**Context:**
- RAM: SDK `client.vms.create(ram=4096)` takes MB as int
- Disk: SDK `vm.drives.create(size_gb=50)` takes GB as int
- Templates use human-friendly: `ram: 4GB`, `size: 50GB`
- Export reverses: 4096 MB → `4GB`, 50 GB → `50GB`
- Regex pattern: `^\d+(\.\d+)?\s*(MB|GB|TB)$` (case-insensitive)

**Step 1: Write failing tests**

```python
# tests/unit/test_template_units.py
"""Tests for template unit parsing."""

import pytest

from verge_cli.template.units import (
    format_disk_size,
    format_ram,
    parse_disk_size,
    parse_ram,
)


class TestParseRam:
    """Tests for RAM parsing (output: MB int)."""

    def test_megabytes(self):
        assert parse_ram("512MB") == 512

    def test_gigabytes(self):
        assert parse_ram("4GB") == 4096

    def test_terabytes(self):
        assert parse_ram("1TB") == 1048576

    def test_passthrough_int(self):
        assert parse_ram(2048) == 2048

    def test_passthrough_int_string(self):
        assert parse_ram("2048") == 2048

    def test_case_insensitive(self):
        assert parse_ram("4gb") == 4096
        assert parse_ram("512mb") == 512

    def test_with_spaces(self):
        assert parse_ram("4 GB") == 4096

    def test_fractional(self):
        assert parse_ram("1.5GB") == 1536

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid.*unit"):
            parse_ram("4PB")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid"):
            parse_ram("lots")

    def test_zero(self):
        with pytest.raises(ValueError, match="must be positive"):
            parse_ram("0GB")

    def test_negative(self):
        with pytest.raises(ValueError):
            parse_ram("-4GB")


class TestParseDiskSize:
    """Tests for disk size parsing (output: GB int)."""

    def test_megabytes(self):
        assert parse_disk_size("512MB") == 0  # rounds down, < 1GB

    def test_megabytes_large(self):
        assert parse_disk_size("2048MB") == 2

    def test_gigabytes(self):
        assert parse_disk_size("50GB") == 50

    def test_terabytes(self):
        assert parse_disk_size("1TB") == 1024

    def test_passthrough_int(self):
        assert parse_disk_size(50) == 50

    def test_passthrough_int_string(self):
        assert parse_disk_size("50") == 50

    def test_fractional(self):
        assert parse_disk_size("1.5TB") == 1536


class TestFormatRam:
    """Tests for RAM formatting (input: MB, output: human string)."""

    def test_exact_gb(self):
        assert format_ram(4096) == "4GB"

    def test_exact_tb(self):
        assert format_ram(1048576) == "1TB"

    def test_sub_gb(self):
        assert format_ram(512) == "512MB"

    def test_non_exact_gb(self):
        assert format_ram(1536) == "1536MB"

    def test_large_exact_gb(self):
        assert format_ram(32768) == "32GB"


class TestFormatDiskSize:
    """Tests for disk size formatting (input: GB, output: human string)."""

    def test_exact_gb(self):
        assert format_disk_size(50) == "50GB"

    def test_exact_tb(self):
        assert format_disk_size(1024) == "1TB"

    def test_sub_tb(self):
        assert format_disk_size(500) == "500GB"

    def test_large_exact_tb(self):
        assert format_disk_size(2048) == "2TB"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_units.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'verge_cli.template.units'`

**Step 3: Implement units.py**

```python
# src/verge_cli/template/units.py
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
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_template_units.py -v`
Expected: All PASS

**Step 5: Lint**

Run: `uv run ruff check src/verge_cli/template/units.py tests/unit/test_template_units.py`
Expected: Clean

**Step 6: Commit**

```bash
git add src/verge_cli/template/units.py tests/unit/test_template_units.py
git commit -m "feat: add unit parsing module for RAM and disk sizes"
```

---

### Task 3: Create template/resolver.py

**Files:**
- Create: `src/verge_cli/template/resolver.py`
- Create: `tests/unit/test_template_resolver.py`

**Context:**
- Templates reference resources by name or ID: `network: "DMZ Internal"` or `network: 3`
- The resolver uses pyvergeos SDK `client.<resource>.list()` to find IDs by name
- Integers pass through; strings trigger a name lookup
- Must handle: not found (error), multiple matches (error), exact match (return key)
- Used by both template builder (batch resolution) and CLI commands (`--network` flag)

**Step 1: Write failing tests**

```python
# tests/unit/test_template_resolver.py
"""Tests for template name-to-ID resolver."""

from unittest.mock import MagicMock

import pytest

from verge_cli.template.resolver import resolve_name, resolve_names


def _make_resource(key: int, name: str) -> MagicMock:
    """Helper to create a mock SDK resource."""
    r = MagicMock()
    r.key = key
    r.name = name
    return r


class TestResolveName:
    """Tests for single name resolution."""

    def test_int_passthrough(self):
        manager = MagicMock()
        assert resolve_name(manager, 3, "network") == 3
        manager.list.assert_not_called()

    def test_int_string_passthrough(self):
        manager = MagicMock()
        assert resolve_name(manager, "3", "network") == 3
        manager.list.assert_not_called()

    def test_name_exact_match(self):
        manager = MagicMock()
        manager.list.return_value = [
            _make_resource(3, "DMZ Internal"),
            _make_resource(5, "External"),
        ]
        assert resolve_name(manager, "DMZ Internal", "network") == 3

    def test_name_not_found(self):
        manager = MagicMock()
        manager.list.return_value = [_make_resource(3, "DMZ Internal")]
        with pytest.raises(ValueError, match="not found"):
            resolve_name(manager, "Missing Network", "network")

    def test_name_multiple_matches(self):
        manager = MagicMock()
        manager.list.return_value = [
            _make_resource(3, "Internal"),
            _make_resource(5, "Internal"),
        ]
        with pytest.raises(ValueError, match="[Mm]ultiple"):
            resolve_name(manager, "Internal", "network")

    def test_none_passthrough(self):
        manager = MagicMock()
        assert resolve_name(manager, None, "network") is None
        manager.list.assert_not_called()


class TestResolveNames:
    """Tests for batch name resolution."""

    def test_batch_resolve(self):
        manager = MagicMock()
        manager.list.return_value = [
            _make_resource(3, "DMZ Internal"),
            _make_resource(5, "External"),
        ]
        results = resolve_names(manager, ["DMZ Internal", "External", 7], "network")
        assert results == [3, 5, 7]
        # Should call list() only once (cached)
        manager.list.assert_called_once()

    def test_batch_empty(self):
        manager = MagicMock()
        assert resolve_names(manager, [], "network") == []
        manager.list.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_resolver.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement resolver.py**

```python
# src/verge_cli/template/resolver.py
"""Name-to-ID resolution using pyvergeos SDK managers."""

from __future__ import annotations

from typing import Any


def resolve_name(
    manager: Any,
    value: int | str | None,
    resource_type: str = "resource",
) -> int | None:
    """Resolve a name or ID to a resource key.

    Args:
        manager: pyvergeos resource manager (e.g., client.networks).
        value: Integer key, string name, or None.
        resource_type: Type name for error messages.

    Returns:
        Resource key (int) or None if value is None.

    Raises:
        ValueError: If name not found or multiple matches.
    """
    if value is None:
        return None

    # Int passthrough
    if isinstance(value, int):
        return value

    # Numeric string passthrough
    text = str(value).strip()
    if text.isdigit():
        return int(text)

    # Name lookup
    resources = manager.list()
    matches = [r for r in resources if getattr(r, "name", None) == text]

    if len(matches) == 1:
        return matches[0].key

    if len(matches) > 1:
        keys = [str(m.key) for m in matches]
        msg = (
            f"Multiple {resource_type}s match '{text}': keys {', '.join(keys)}. "
            f"Use a numeric key to disambiguate."
        )
        raise ValueError(msg)

    msg = f"{resource_type} '{text}' not found."
    raise ValueError(msg)


def resolve_names(
    manager: Any,
    values: list[int | str],
    resource_type: str = "resource",
) -> list[int]:
    """Resolve a batch of names/IDs to resource keys.

    Calls manager.list() once and resolves all names from the cached result.

    Args:
        manager: pyvergeos resource manager.
        values: List of integer keys or string names.
        resource_type: Type name for error messages.

    Returns:
        List of resource keys (int).

    Raises:
        ValueError: If any name not found or has multiple matches.
    """
    if not values:
        return []

    # Separate ints from strings that need resolution
    needs_lookup = any(
        isinstance(v, str) and not str(v).strip().isdigit() for v in values
    )

    if not needs_lookup:
        return [int(v) if isinstance(v, str) else v for v in values]

    # Fetch all resources once
    resources = manager.list()
    name_to_keys: dict[str, list[int]] = {}
    for r in resources:
        name = getattr(r, "name", None)
        if name is not None:
            name_to_keys.setdefault(name, []).append(r.key)

    result: list[int] = []
    for v in values:
        if isinstance(v, int):
            result.append(v)
            continue

        text = str(v).strip()
        if text.isdigit():
            result.append(int(text))
            continue

        keys = name_to_keys.get(text, [])
        if len(keys) == 1:
            result.append(keys[0])
        elif len(keys) > 1:
            msg = (
                f"Multiple {resource_type}s match '{text}': keys {', '.join(str(k) for k in keys)}. "
                f"Use a numeric key to disambiguate."
            )
            raise ValueError(msg)
        else:
            msg = f"{resource_type} '{text}' not found."
            raise ValueError(msg)

    return result
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_template_resolver.py -v`
Expected: All PASS

**Step 5: Lint**

Run: `uv run ruff check src/verge_cli/template/resolver.py tests/unit/test_template_resolver.py`
Expected: Clean

**Step 6: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS (no regressions)

**Step 7: Commit**

```bash
git add src/verge_cli/template/resolver.py tests/unit/test_template_resolver.py
git commit -m "feat: add name-to-ID resolver using pyvergeos SDK"
```

---

## Milestone 1 Complete

After M1 you should have:
- `src/verge_cli/template/__init__.py`
- `src/verge_cli/template/units.py` — parse/format RAM (MB) and disk (GB)
- `src/verge_cli/template/resolver.py` — resolve names to IDs via SDK
- Tests passing for both modules
- `pyyaml` and `jsonschema` in dependencies
