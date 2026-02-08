"""Tests for outgoing site sync management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_sync_outgoing() -> MagicMock:
    """Create a mock outgoing site sync object."""
    sync = MagicMock()
    sync.key = 800
    sync.name = "prod-to-backup"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 800,
            "name": "prod-to-backup",
            "site": 100,
            "status": "online",
            "enabled": True,
            "state": "online",
            "encryption": True,
            "compression": True,
            "threads": 4,
            "last_run": 1700000000,
            "destination_tier": "1",
            "description": "Production to backup sync",
        }
        return data.get(key, default)

    sync.get = mock_get
    return sync


def test_outgoing_list(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing list should list all outgoing syncs."""
    mock_client.site_syncs.list.return_value = [mock_sync_outgoing]

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "list"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output
    mock_client.site_syncs.list.assert_called_once_with()


def test_outgoing_list_empty(cli_runner, mock_client):
    """vrg site sync outgoing list should handle empty list."""
    mock_client.site_syncs.list.return_value = []

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "list"])

    assert result.exit_code == 0


def test_outgoing_list_by_site(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing list --site should filter by site name."""
    mock_client.site_syncs.list.return_value = [mock_sync_outgoing]

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "list", "--site", "backup-site"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output
    mock_client.site_syncs.list.assert_called_once_with(site_name="backup-site")


def test_outgoing_get(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing get should resolve by name."""
    mock_client.site_syncs.list.return_value = [mock_sync_outgoing]
    mock_client.site_syncs.get.return_value = mock_sync_outgoing

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "get", "prod-to-backup"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output


def test_outgoing_get_by_key(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing get should accept numeric key."""
    mock_client.site_syncs.get.return_value = mock_sync_outgoing

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "get", "800"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output
    mock_client.site_syncs.get.assert_called_once_with(800)


def test_outgoing_enable(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing enable should enable a sync."""
    mock_client.site_syncs.list.return_value = [mock_sync_outgoing]
    mock_client.site_syncs.enable.return_value = mock_sync_outgoing

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "enable", "prod-to-backup"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.site_syncs.enable.assert_called_once_with(800)


def test_outgoing_disable(cli_runner, mock_client, mock_sync_outgoing):
    """vrg site sync outgoing disable should disable a sync."""
    mock_client.site_syncs.list.return_value = [mock_sync_outgoing]
    mock_client.site_syncs.disable.return_value = mock_sync_outgoing

    result = cli_runner.invoke(app, ["site", "sync", "outgoing", "disable", "prod-to-backup"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.site_syncs.disable.assert_called_once_with(800)
