"""Unit tests for utility functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from verge_cli.errors import MultipleMatchesError, ResourceNotFoundError
from verge_cli.utils import resolve_resource_id


class TestResolveResourceId:
    """Tests for resource ID resolution."""

    def test_numeric_id_fallback_returns_int(self) -> None:
        """Test that numeric identifiers fall back to int if no name match."""
        manager = MagicMock()
        # No VM with name "123"
        manager.list.return_value = [
            {"name": "web-server", "$key": 42},
        ]

        result = resolve_resource_id(manager, "123", "VM")

        assert result == 123
        manager.list.assert_called_once()  # Should query API first

    def test_numeric_name_resolved_by_name(self) -> None:
        """Test that numeric names are properly resolved by name first."""
        manager = MagicMock()
        # VM with numeric name "123" exists with key 999
        manager.list.return_value = [
            {"name": "123", "$key": 999},
            {"name": "web-server", "$key": 42},
        ]

        result = resolve_resource_id(manager, "123", "VM")

        # Should find by name, not treat "123" as a key
        assert result == 999
        manager.list.assert_called_once()

    def test_name_single_match(self) -> None:
        """Test resolving a name with single match."""
        manager = MagicMock()
        manager.list.return_value = [
            {"name": "web-server", "$key": 42},
            {"name": "db-server", "$key": 43},
        ]

        result = resolve_resource_id(manager, "web-server", "VM")

        assert result == 42
        manager.list.assert_called_once()

    def test_name_no_match_raises_not_found(self) -> None:
        """Test that no match raises ResourceNotFoundError."""
        manager = MagicMock()
        manager.list.return_value = [
            {"name": "web-server", "$key": 42},
        ]

        with pytest.raises(ResourceNotFoundError, match="not found"):
            resolve_resource_id(manager, "nonexistent", "VM")

    def test_name_multiple_matches_raises_conflict(self) -> None:
        """Test that multiple matches raises MultipleMatchesError."""
        manager = MagicMock()
        manager.list.return_value = [
            {"name": "web-server", "$key": 42},
            {"name": "web-server", "$key": 43},  # Duplicate name
        ]

        with pytest.raises(MultipleMatchesError) as exc_info:
            resolve_resource_id(manager, "web-server", "VM")

        error = exc_info.value
        assert len(error.matches) == 2
        assert error.resource_type == "VM"
        assert error.name == "web-server"

    def test_handles_object_responses(self) -> None:
        """Test handling of object responses (not dicts)."""
        manager = MagicMock()

        # Create mock objects with attributes
        vm1 = MagicMock()
        vm1.name = "web-server"
        vm1.key = 42

        vm2 = MagicMock()
        vm2.name = "db-server"
        vm2.key = 43

        manager.list.return_value = [vm1, vm2]

        result = resolve_resource_id(manager, "db-server", "VM")

        assert result == 43

    def test_empty_list_raises_not_found_for_name(self) -> None:
        """Test that empty list raises ResourceNotFoundError for non-numeric names."""
        manager = MagicMock()
        manager.list.return_value = []

        with pytest.raises(ResourceNotFoundError):
            resolve_resource_id(manager, "anything", "VM")

    def test_empty_list_with_numeric_id_returns_int(self) -> None:
        """Test that empty list with numeric ID falls back to integer."""
        manager = MagicMock()
        manager.list.return_value = []

        # Should fall back to treating "456" as a key
        result = resolve_resource_id(manager, "456", "VM")
        assert result == 456

    def test_list_error_raises_not_found(self) -> None:
        """Test that list errors are wrapped in ResourceNotFoundError."""
        manager = MagicMock()
        manager.list.side_effect = Exception("API Error")

        with pytest.raises(ResourceNotFoundError, match="Failed to list"):
            resolve_resource_id(manager, "web-server", "VM")


class TestMultipleMatchesError:
    """Tests for MultipleMatchesError."""

    def test_error_message_format(self) -> None:
        """Test that error message lists all matches."""
        matches = [
            {"name": "web-server", "$key": 42},
            {"name": "web-server", "$key": 43},
        ]

        error = MultipleMatchesError("VM", "web-server", matches)

        assert "Multiple VMs match 'web-server'" in str(error)
        assert "42" in str(error)
        assert "43" in str(error)

    def test_error_attributes(self) -> None:
        """Test error attributes are set correctly."""
        matches = [{"name": "test", "$key": 1}]

        error = MultipleMatchesError("network", "test-net", matches)

        assert error.resource_type == "network"
        assert error.name == "test-net"
        assert error.matches == matches
        assert error.exit_code == 7  # Conflict error code
