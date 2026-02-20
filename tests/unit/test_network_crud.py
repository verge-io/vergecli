"""Tests for network CRUD and power operations."""

from __future__ import annotations

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_network_list_basic(cli_runner, mock_client, mock_network):
    """vrg network list should list all networks."""
    mock_client.networks.list.return_value = [mock_network]

    result = cli_runner.invoke(app, ["network", "list"])

    assert result.exit_code == 0
    assert "test" in result.output
    mock_client.networks.list.assert_called_once_with(filter=None)


def test_network_list_with_type_filter(cli_runner, mock_client, mock_network):
    """vrg network list --type internal should filter by type."""
    mock_client.networks.list.return_value = [mock_network]

    result = cli_runner.invoke(app, ["network", "list", "--type", "internal"])

    assert result.exit_code == 0
    mock_client.networks.list.assert_called_once_with(filter="type eq 'internal'")


def test_network_list_with_status_filter(cli_runner, mock_client, mock_network):
    """vrg network list --status running should filter by status."""
    mock_client.networks.list.return_value = [mock_network]

    result = cli_runner.invoke(app, ["network", "list", "--status", "running"])

    assert result.exit_code == 0
    mock_client.networks.list.assert_called_once_with(filter="status eq 'running'")


def test_network_list_combined_filters(cli_runner, mock_client, mock_network):
    """vrg network list --type --status --filter should combine all filters."""
    mock_client.networks.list.return_value = [mock_network]

    result = cli_runner.invoke(
        app,
        [
            "network",
            "list",
            "--type",
            "internal",
            "--status",
            "running",
            "--filter",
            "name eq 'dmz'",
        ],
    )

    assert result.exit_code == 0
    call_filter = mock_client.networks.list.call_args[1]["filter"]
    assert "type eq 'internal'" in call_filter
    assert "status eq 'running'" in call_filter
    assert "name eq 'dmz'" in call_filter


def test_network_get(cli_runner, mock_client, mock_network):
    """vrg network get should get network details."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "get", "test-network"])

    assert result.exit_code == 0
    assert "test-network" in result.output


def test_network_create_with_dhcp(cli_runner, mock_client, mock_network):
    """vrg network create with --dhcp options should pass DHCP config."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        [
            "network",
            "create",
            "--name",
            "test-net",
            "--cidr",
            "10.0.0.0/24",
            "--dhcp",
            "--dhcp-start",
            "10.0.0.100",
            "--dhcp-stop",
            "10.0.0.200",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["dhcp_enabled"] is True
    assert call_kwargs["dhcp_start"] == "10.0.0.100"
    assert call_kwargs["dhcp_stop"] == "10.0.0.200"


def test_network_create_with_gateway(cli_runner, mock_client, mock_network):
    """vrg network create with --gateway should pass gateway."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        [
            "network",
            "create",
            "--name",
            "test-net",
            "--cidr",
            "10.0.0.0/24",
            "--gateway",
            "10.0.0.1",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["gateway"] == "10.0.0.1"


def test_network_update(cli_runner, mock_client, mock_network):
    """vrg network update should update fields."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.update.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "update", "test-network", "--name", "renamed-net"])

    assert result.exit_code == 0
    mock_client.networks.update.assert_called_once_with(1, name="renamed-net")


def test_network_update_description(cli_runner, mock_client, mock_network):
    """vrg network update --description should update description."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.update.return_value = mock_network

    result = cli_runner.invoke(
        app,
        ["network", "update", "test-network", "--description", "New desc"],
    )

    assert result.exit_code == 0
    mock_client.networks.update.assert_called_once_with(1, description="New desc")


def test_network_update_no_changes_fails(cli_runner, mock_client, mock_network):
    """vrg network update with no options should exit with error."""
    mock_client.networks.list.return_value = [mock_network]

    result = cli_runner.invoke(app, ["network", "update", "test-network"])

    assert result.exit_code == 2


def test_network_delete_confirmed(cli_runner, mock_client, mock_network):
    """vrg network delete --yes should delete network."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "delete", "test-network", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.networks.delete.assert_called_once_with(1)


def test_network_start(cli_runner, mock_client):
    """vrg network start should start a stopped network."""
    net = MagicMock()
    net.key = 1
    net.name = "test-net"
    net.get = lambda k, d=None: {"running": False, "status": "stopped"}.get(k, d)
    mock_client.networks.list.return_value = [net]
    mock_client.networks.get.return_value = net

    result = cli_runner.invoke(app, ["network", "start", "test-net"])

    assert result.exit_code == 0
    net.power_on.assert_called_once()


def test_network_start_already_running(cli_runner, mock_client, mock_network):
    """vrg network start on running network should show message."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "start", "test-network"])

    assert result.exit_code == 0
    assert "already running" in result.output
    mock_network.power_on.assert_not_called()


def test_network_stop(cli_runner, mock_client, mock_network):
    """vrg network stop should stop a running network."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "stop", "test-network"])

    assert result.exit_code == 0
    mock_network.power_off.assert_called_once_with(force=False)


def test_network_stop_not_running(cli_runner, mock_client):
    """vrg network stop on stopped network should show message."""
    net = MagicMock()
    net.key = 2
    net.name = "stopped-net"
    net.get = lambda k, d=None: {"running": False, "status": "stopped"}.get(k, d)
    mock_client.networks.list.return_value = [net]
    mock_client.networks.get.return_value = net

    result = cli_runner.invoke(app, ["network", "stop", "stopped-net"])

    assert result.exit_code == 0
    assert "not running" in result.output
    net.power_off.assert_not_called()


def test_network_stop_force(cli_runner, mock_client, mock_network):
    """vrg network stop --force should force stop."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network

    result = cli_runner.invoke(app, ["network", "stop", "test-network", "--force"])

    assert result.exit_code == 0
    mock_network.power_off.assert_called_once_with(force=True)
