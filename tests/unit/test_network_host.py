"""Tests for network host override commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_hosts():
    """Create a mock Network for host operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"
    return net


@pytest.fixture
def mock_host():
    """Create a mock NetworkHost object."""
    host = MagicMock()
    host.key = 300

    def mock_get(key: str, default=None):
        data = {
            "$key": 300,
            "host": "webserver.local",
            "ip": "10.0.0.50",
            "type": "host",
        }
        return data.get(key, default)

    host.get = mock_get
    return host


def test_host_list(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host list should show host overrides for a network."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]

    result = cli_runner.invoke(app, ["network", "host", "list", "test-network"])

    assert result.exit_code == 0
    assert "webserver.local" in result.output


def test_host_get(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host get should show host override details."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    result = cli_runner.invoke(app, ["network", "host", "get", "test-network", "webserver.local"])

    assert result.exit_code == 0
    assert "webserver.local" in result.output
    assert "10.0.0.50" in result.output


def test_host_get_by_ip(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host get should work when looking up by IP address."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    result = cli_runner.invoke(app, ["network", "host", "get", "test-network", "10.0.0.50"])

    assert result.exit_code == 0
    assert "webserver.local" in result.output


def test_host_create(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host create should create a new host override."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.create.return_value = mock_host

    result = cli_runner.invoke(
        app,
        [
            "network",
            "host",
            "create",
            "test-network",
            "--hostname",
            "webserver.local",
            "--ip",
            "10.0.0.50",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_hosts.hosts.create.assert_called_once_with(
        hostname="webserver.local", ip="10.0.0.50", host_type="host"
    )


def test_host_create_domain_type(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host create with domain type should pass type to SDK."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.create.return_value = mock_host

    result = cli_runner.invoke(
        app,
        [
            "network",
            "host",
            "create",
            "test-network",
            "--hostname",
            "example.com",
            "--ip",
            "10.0.0.60",
            "--type",
            "domain",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_hosts.hosts.create.assert_called_once_with(
        hostname="example.com", ip="10.0.0.60", host_type="domain"
    )


def test_host_update(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host update should update host override with new values."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    # Create updated mock
    updated_host = MagicMock()
    updated_host.key = 300
    updated_host.get = lambda k, d=None: {
        "$key": 300,
        "host": "webserver.local",
        "ip": "10.0.0.99",
        "type": "host",
    }.get(k, d)
    mock_network_for_hosts.hosts.update.return_value = updated_host

    result = cli_runner.invoke(
        app,
        [
            "network",
            "host",
            "update",
            "test-network",
            "webserver.local",
            "--ip",
            "10.0.0.99",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_hosts.hosts.update.assert_called_once_with(
        300, hostname="webserver.local", ip="10.0.0.99", host_type="host"
    )


def test_host_update_no_changes(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host update with no options should fail."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    result = cli_runner.invoke(
        app,
        ["network", "host", "update", "test-network", "webserver.local"],
    )

    assert result.exit_code == 2
    assert "No updates specified" in result.output


def test_host_delete(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host delete should delete a host override."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    result = cli_runner.invoke(
        app,
        ["network", "host", "delete", "test-network", "webserver.local", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_hosts.hosts.delete.assert_called_once_with(300)


def test_host_delete_by_ip(cli_runner, mock_client, mock_network_for_hosts, mock_host):
    """Host delete should work when looking up by IP address."""
    mock_client.networks.list.return_value = [mock_network_for_hosts]
    mock_client.networks.get.return_value = mock_network_for_hosts
    mock_network_for_hosts.hosts.list.return_value = [mock_host]
    mock_network_for_hosts.hosts.get.return_value = mock_host

    result = cli_runner.invoke(
        app,
        ["network", "host", "delete", "test-network", "10.0.0.50", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_hosts.hosts.delete.assert_called_once_with(300)
