"""Tests for network IP alias commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_aliases():
    """Create a mock Network for alias operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"
    return net


@pytest.fixture
def mock_alias():
    """Create a mock NetworkAlias object."""
    alias = MagicMock()
    alias.key = 200
    alias.name = "webserver"
    alias.ip = "10.0.0.100"
    alias.hostname = "webserver"

    def mock_get(key: str, default=None):
        data = {
            "ip": "10.0.0.100",
            "hostname": "webserver",
            "description": "Main web server",
            "mac": "",
        }
        return data.get(key, default)

    alias.get = mock_get
    return alias


def test_alias_list(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias list should show aliases for a network."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]

    result = cli_runner.invoke(app, ["network", "alias", "list", "test-network"])

    assert result.exit_code == 0
    assert "webserver" in result.output


def test_alias_get(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias get should show alias details."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    result = cli_runner.invoke(app, ["network", "alias", "get", "test-network", "webserver"])

    assert result.exit_code == 0
    assert "webserver" in result.output
    assert "10.0.0.100" in result.output


def test_alias_create(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias create should create a new alias."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.create.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        [
            "network",
            "alias",
            "create",
            "test-network",
            "--ip",
            "10.0.0.100",
            "--name",
            "webserver",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.create.assert_called_once()


def test_alias_create_with_description(
    cli_runner, mock_client, mock_network_for_aliases, mock_alias
):
    """Alias create with description should pass description to SDK."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.create.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        [
            "network",
            "alias",
            "create",
            "test-network",
            "--ip",
            "10.0.0.100",
            "--name",
            "webserver",
            "--description",
            "Main web server",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.create.assert_called_once_with(
        ip="10.0.0.100", name="webserver", description="Main web server"
    )


def test_alias_delete(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias delete should delete an alias."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        ["network", "alias", "delete", "test-network", "webserver", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.delete.assert_called_once_with(200)


def test_alias_delete_by_ip(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias delete should work when looking up by IP address."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        ["network", "alias", "delete", "test-network", "10.0.0.100", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.delete.assert_called_once_with(200)


def test_alias_update(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias update should delete and recreate alias with new values."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    # Create a new mock for the recreated alias
    new_alias = MagicMock()
    new_alias.key = 201
    new_alias.hostname = "webserver-updated"
    new_alias.ip = "10.0.0.100"
    new_alias.get = lambda k, d=None: {"ip": "10.0.0.100", "hostname": "webserver-updated"}.get(
        k, d
    )
    mock_network_for_aliases.aliases.create.return_value = new_alias

    result = cli_runner.invoke(
        app,
        [
            "network",
            "alias",
            "update",
            "test-network",
            "webserver",
            "--name",
            "webserver-updated",
        ],
    )

    assert result.exit_code == 0
    # Should delete the old alias
    mock_network_for_aliases.aliases.delete.assert_called_once_with(200)
    # Should create a new alias with updated name
    mock_network_for_aliases.aliases.create.assert_called_once()


def test_alias_update_no_changes(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias update with no options should fail."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        ["network", "alias", "update", "test-network", "webserver"],
    )

    assert result.exit_code == 2
    assert "No updates specified" in result.output
