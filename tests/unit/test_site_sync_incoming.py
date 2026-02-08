"""Tests for incoming site sync management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_sync_incoming() -> MagicMock:
    """Create a mock incoming site sync object."""
    sync = MagicMock()
    sync.key = 900
    sync.name = "backup-to-prod"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 900,
            "name": "backup-to-prod",
            "site": 200,
            "status": "online",
            "enabled": True,
            "state": "online",
            "last_sync": 1700000000,
            "min_snapshots": 3,
            "description": "Backup to production sync",
        }
        return data.get(key, default)

    sync.get = mock_get
    return sync


def test_incoming_list(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming list should list all incoming syncs."""
    mock_client.site_syncs_incoming.list.return_value = [mock_sync_incoming]

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "list"])

    assert result.exit_code == 0
    assert "backup-to-prod" in result.output
    mock_client.site_syncs_incoming.list.assert_called_once_with()


def test_incoming_list_empty(cli_runner, mock_client):
    """vrg site sync incoming list should handle empty list."""
    mock_client.site_syncs_incoming.list.return_value = []

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "list"])

    assert result.exit_code == 0


def test_incoming_list_by_site(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming list --site should filter by site name."""
    mock_client.site_syncs_incoming.list.return_value = [mock_sync_incoming]

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "list", "--site", "backup-site"])

    assert result.exit_code == 0
    assert "backup-to-prod" in result.output
    mock_client.site_syncs_incoming.list.assert_called_once_with(site_name="backup-site")


def test_incoming_get(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming get should resolve by name."""
    mock_client.site_syncs_incoming.list.return_value = [mock_sync_incoming]
    mock_client.site_syncs_incoming.get.return_value = mock_sync_incoming

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "get", "backup-to-prod"])

    assert result.exit_code == 0
    assert "backup-to-prod" in result.output


def test_incoming_get_by_key(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming get should accept numeric key."""
    mock_client.site_syncs_incoming.get.return_value = mock_sync_incoming

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "get", "900"])

    assert result.exit_code == 0
    assert "backup-to-prod" in result.output
    mock_client.site_syncs_incoming.get.assert_called_once_with(900)


def test_incoming_enable(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming enable should enable a sync."""
    mock_client.site_syncs_incoming.list.return_value = [mock_sync_incoming]
    mock_client.site_syncs_incoming.enable.return_value = mock_sync_incoming

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "enable", "backup-to-prod"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.site_syncs_incoming.enable.assert_called_once_with(900)


def test_incoming_disable(cli_runner, mock_client, mock_sync_incoming):
    """vrg site sync incoming disable should disable a sync."""
    mock_client.site_syncs_incoming.list.return_value = [mock_sync_incoming]
    mock_client.site_syncs_incoming.disable.return_value = mock_sync_incoming

    result = cli_runner.invoke(app, ["site", "sync", "incoming", "disable", "backup-to-prod"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.site_syncs_incoming.disable.assert_called_once_with(900)
