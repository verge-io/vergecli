"""Unit tests for column definitions and formatting helpers."""

from __future__ import annotations

from verge_cli.columns import (
    ADDRESS_COLUMNS,
    ALIAS_COLUMNS,
    BOOL_STYLES,
    DEVICE_COLUMNS,
    DRIVE_COLUMNS,
    FLAG_STYLES,
    HOST_COLUMNS,
    LEASE_COLUMNS,
    NETWORK_COLUMNS,
    NIC_COLUMNS,
    RECORD_COLUMNS,
    RULE_COLUMNS,
    STATUS_STYLES,
    VIEW_COLUMNS,
    VM_COLUMNS,
    ZONE_COLUMNS,
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
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass


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
        vm_wide = [c for c in VM_COLUMNS if c.wide_only]
        net_wide = [c for c in NETWORK_COLUMNS if c.wide_only]
        assert len(vm_wide) > 0
        assert len(net_wide) > 0
