"""Unit tests for output formatting."""

from __future__ import annotations

import json
from datetime import datetime

from verge_cli.output import extract_field, format_json, format_value


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
