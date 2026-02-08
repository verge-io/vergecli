"""Tests for site management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_site() -> MagicMock:
    """Create a mock Site object."""
    site = MagicMock()
    site.key = 800
    site.name = "site2"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 800,
            "name": "site2",
            "url": "https://site2.example.com",
            "status": "online",
            "enabled": True,
            "authentication_status": "authenticated",
            "config_cloud_snapshots": "send",
            "description": "DR site",
            "domain": "site2.example.com",
            "city": "Denver",
            "country": "US",
        }
        return data.get(key, default)

    site.get = mock_get
    return site


def test_site_list(cli_runner, mock_client, mock_site):
    """vrg site list should list all sites."""
    mock_client.sites.list.return_value = [mock_site]

    result = cli_runner.invoke(app, ["site", "list"])

    assert result.exit_code == 0
    assert "site2" in result.output
    mock_client.sites.list.assert_called_once_with()


def test_site_list_empty(cli_runner, mock_client):
    """vrg site list should handle empty list."""
    mock_client.sites.list.return_value = []

    result = cli_runner.invoke(app, ["site", "list"])

    assert result.exit_code == 0


def test_site_list_by_status(cli_runner, mock_client, mock_site):
    """vrg site list --status should pass filter to SDK."""
    mock_client.sites.list.return_value = [mock_site]

    result = cli_runner.invoke(app, ["site", "list", "--status", "online"])

    assert result.exit_code == 0
    assert "site2" in result.output
    mock_client.sites.list.assert_called_once_with(status="online")


def test_site_list_enabled(cli_runner, mock_client, mock_site):
    """vrg site list --enabled should filter enabled sites."""
    mock_client.sites.list.return_value = [mock_site]

    result = cli_runner.invoke(app, ["site", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.sites.list.assert_called_once_with(enabled=True)


def test_site_get(cli_runner, mock_client, mock_site):
    """vrg site get should resolve by name."""
    mock_client.sites.list.return_value = [mock_site]
    mock_client.sites.get.return_value = mock_site

    result = cli_runner.invoke(app, ["site", "get", "site2"])

    assert result.exit_code == 0
    assert "site2" in result.output


def test_site_get_by_key(cli_runner, mock_client, mock_site):
    """vrg site get should accept numeric key."""
    mock_client.sites.get.return_value = mock_site

    result = cli_runner.invoke(app, ["site", "get", "800"])

    assert result.exit_code == 0
    assert "site2" in result.output
    mock_client.sites.get.assert_called_once_with(800)


def test_site_create(cli_runner, mock_client, mock_site):
    """vrg site create should create with required options."""
    mock_client.sites.create.return_value = mock_site

    result = cli_runner.invoke(
        app,
        [
            "site",
            "create",
            "--name",
            "site2",
            "--url",
            "https://site2.example.com",
            "--username",
            "admin",
            "--password",
            "secret",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.sites.create.assert_called_once_with(
        name="site2",
        url="https://site2.example.com",
        username="admin",
        password="secret",
        allow_insecure=False,
        config_cloud_snapshots="disabled",
        auto_create_syncs=True,
    )


def test_site_create_with_options(cli_runner, mock_client, mock_site):
    """vrg site create should accept --allow-insecure, --cloud-snapshots, --no-auto-create-syncs."""
    mock_client.sites.create.return_value = mock_site

    result = cli_runner.invoke(
        app,
        [
            "site",
            "create",
            "--name",
            "site2",
            "--url",
            "https://site2.example.com",
            "--username",
            "admin",
            "--password",
            "secret",
            "--allow-insecure",
            "--cloud-snapshots",
            "both",
            "--no-auto-create-syncs",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.sites.create.assert_called_once_with(
        name="site2",
        url="https://site2.example.com",
        username="admin",
        password="secret",
        allow_insecure=True,
        config_cloud_snapshots="both",
        auto_create_syncs=False,
    )


def test_site_update(cli_runner, mock_client, mock_site):
    """vrg site update should update name, description, cloud-snapshots."""
    mock_client.sites.list.return_value = [mock_site]

    result = cli_runner.invoke(
        app,
        [
            "site",
            "update",
            "site2",
            "--name",
            "site2-renamed",
            "--description",
            "Updated description",
            "--cloud-snapshots",
            "receive",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.sites.update.assert_called_once_with(
        800,
        name="site2-renamed",
        description="Updated description",
        config_cloud_snapshots="receive",
    )


def test_site_delete(cli_runner, mock_client, mock_site):
    """vrg site delete should remove a site with --yes."""
    mock_client.sites.list.return_value = [mock_site]

    result = cli_runner.invoke(app, ["site", "delete", "site2", "--yes"])

    assert result.exit_code == 0
    mock_client.sites.delete.assert_called_once_with(800)
    assert "Deleted" in result.output


def test_site_enable(cli_runner, mock_client, mock_site):
    """vrg site enable should enable a site."""
    mock_client.sites.list.return_value = [mock_site]
    mock_client.sites.enable.return_value = mock_site

    result = cli_runner.invoke(app, ["site", "enable", "site2"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.sites.enable.assert_called_once_with(800)


def test_site_disable(cli_runner, mock_client, mock_site):
    """vrg site disable should disable a site."""
    mock_client.sites.list.return_value = [mock_site]
    mock_client.sites.disable.return_value = mock_site

    result = cli_runner.invoke(app, ["site", "disable", "site2"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.sites.disable.assert_called_once_with(800)


def test_site_reauth(cli_runner, mock_client, mock_site):
    """vrg site reauth should re-authenticate with new credentials."""
    mock_client.sites.list.return_value = [mock_site]
    mock_client.sites.reauthenticate.return_value = mock_site

    result = cli_runner.invoke(
        app,
        [
            "site",
            "reauth",
            "site2",
            "--username",
            "new-admin",
            "--password",
            "new-secret",
        ],
    )

    assert result.exit_code == 0
    assert "Re-authenticated" in result.output
    mock_client.sites.reauthenticate.assert_called_once_with(800, "new-admin", "new-secret")


def test_site_refresh(cli_runner, mock_client, mock_site):
    """vrg site refresh should refresh site connection."""
    mock_client.sites.list.return_value = [mock_site]
    mock_client.sites.refresh_site.return_value = mock_site

    result = cli_runner.invoke(app, ["site", "refresh", "site2"])

    assert result.exit_code == 0
    assert "Refreshed" in result.output
    mock_client.sites.refresh_site.assert_called_once_with(800)


def test_site_not_found(cli_runner, mock_client):
    """vrg site get with unknown name should exit 6."""
    mock_client.sites.list.return_value = []

    result = cli_runner.invoke(app, ["site", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
