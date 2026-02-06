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
