"""Unit tests for output formatting."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from rich.text import Text

from verge_cli.columns import (
    FLAG_STYLES,
    STATUS_STYLES,
    ColumnDef,
    default_format,
    format_bool_yn,
    normalize_lower,
)
from verge_cli.output import (
    extract_field,
    format_csv,
    format_json,
    format_table,
    format_value,
    output_result,
    render_cell,
)


class TestExtractField:
    """Tests for dot notation field extraction."""

    def test_simple_field(self) -> None:
        """Test extracting a simple field."""
        data = {"name": "test", "status": "running"}
        assert extract_field(data, "name") == "test"
        assert extract_field(data, "status") == "running"

    def test_nested_field(self) -> None:
        """Test extracting a nested field."""
        data = {"config": {"host": "example.com", "port": 8080}}
        assert extract_field(data, "config.host") == "example.com"
        assert extract_field(data, "config.port") == 8080

    def test_array_index(self) -> None:
        """Test extracting by array index."""
        data = {"items": [{"name": "first"}, {"name": "second"}]}
        assert extract_field(data, "items.0.name") == "first"
        assert extract_field(data, "items.1.name") == "second"

    def test_array_field_extraction(self) -> None:
        """Test extracting a field from all array items."""
        data = [{"name": "vm1"}, {"name": "vm2"}, {"name": "vm3"}]
        assert extract_field(data, "name") == ["vm1", "vm2", "vm3"]

    def test_missing_field_returns_none(self) -> None:
        """Test that missing fields return None."""
        data = {"name": "test"}
        assert extract_field(data, "missing") is None
        assert extract_field(data, "deep.missing.field") is None

    def test_empty_query_returns_data(self) -> None:
        """Test that empty query returns original data."""
        data = {"name": "test"}
        assert extract_field(data, "") == data
        assert extract_field(data, None) == data  # type: ignore

    def test_none_data(self) -> None:
        """Test handling None data."""
        assert extract_field(None, "name") is None


class TestFormatJson:
    """Tests for JSON formatting."""

    def test_basic_dict(self) -> None:
        """Test formatting a basic dictionary."""
        data = {"name": "test", "count": 42}
        result = format_json(data)
        parsed = json.loads(result)

        assert parsed["name"] == "test"
        assert parsed["count"] == 42

    def test_datetime_handling(self) -> None:
        """Test that datetime objects are serialized."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        data = {"timestamp": dt}
        result = format_json(data)
        parsed = json.loads(result)

        assert parsed["timestamp"] == "2024-01-15T10:30:00"

    def test_with_query(self) -> None:
        """Test JSON formatting with query extraction."""
        data = {"config": {"host": "example.com"}}
        result = format_json(data, query="config.host")

        assert json.loads(result) == "example.com"

    def test_list_data(self) -> None:
        """Test formatting a list."""
        data = [{"name": "vm1"}, {"name": "vm2"}]
        result = format_json(data)
        parsed = json.loads(result)

        assert len(parsed) == 2
        assert parsed[0]["name"] == "vm1"


class TestFormatValue:
    """Tests for single value formatting."""

    def test_none_value(self) -> None:
        """Test None displays as dash."""
        result = format_value(None)
        assert "-" in result

    def test_bool_true(self) -> None:
        """Test True displays as yes with color."""
        result = format_value(True)
        assert "yes" in result

    def test_bool_false(self) -> None:
        """Test False displays as no with color."""
        result = format_value(False)
        assert "no" in result

    def test_datetime_formatting(self) -> None:
        """Test datetime is formatted nicely."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_value(dt)
        assert "2024-01-15" in result
        assert "10:30:45" in result

    def test_string_passthrough(self) -> None:
        """Test strings pass through unchanged."""
        assert format_value("hello") == "hello"
        assert format_value("running") == "running"

    def test_number_passthrough(self) -> None:
        """Test numbers are converted to strings."""
        assert format_value(42) == "42"
        assert format_value(3.14) == "3.14"

    def test_dict_as_json(self) -> None:
        """Test dicts are formatted as JSON."""
        result = format_value({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_list_as_json(self) -> None:
        """Test lists are formatted as JSON."""
        result = format_value([1, 2, 3])
        assert "1" in result
        assert "2" in result
        assert "3" in result


class TestOutputResult:
    """Tests for output_result function."""

    def test_list_of_simple_values_table_format(self, capsys) -> None:
        """Test that list of simple values (from --query) prints as newline-separated."""
        # This is what happens when you do: vrg vm list --query name
        data = ["vm1", "vm2", "vm3"]
        output_result(data, output_format="table", no_color=True)
        captured = capsys.readouterr()
        assert "vm1" in captured.out
        assert "vm2" in captured.out
        assert "vm3" in captured.out

    def test_list_of_simple_values_json_format(self, capsys) -> None:
        """Test that list of simple values outputs as JSON array."""
        data = ["vm1", "vm2", "vm3"]
        output_result(data, output_format="json", no_color=True)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == ["vm1", "vm2", "vm3"]

    def test_list_of_dicts_still_formats_as_table(self, capsys) -> None:
        """Test that list of dicts still uses table format."""
        data = [{"name": "vm1", "status": "running"}, {"name": "vm2", "status": "stopped"}]
        output_result(data, output_format="table", no_color=True)
        captured = capsys.readouterr()
        # Should have table headers
        assert "Name" in captured.out
        assert "Status" in captured.out

    def test_query_on_list_extracts_and_outputs_values(self, capsys) -> None:
        """Test that --query on a list extracts and outputs simple values."""
        data = [{"name": "vm1"}, {"name": "vm2"}, {"name": "vm3"}]
        output_result(data, output_format="table", query="name", no_color=True)
        captured = capsys.readouterr()
        assert "vm1" in captured.out
        assert "vm2" in captured.out
        assert "vm3" in captured.out


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
        result = render_cell("running", {}, col)
        assert result.style == "green"

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
            ColumnDef(
                "needs_restart", header="Restart", style_map=FLAG_STYLES, format_fn=format_bool_yn
            ),
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
