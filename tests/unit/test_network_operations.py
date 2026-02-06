"""Tests for network apply and restart operations."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_running_network():
    """Create a mock running Network."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        data = {
            "running": True,
            "status": "running",
            "need_restart": True,
            "need_fw_apply": True,
            "need_dns_apply": True,
            "need_proxy_apply": False,
        }
        return data.get(key, default)

    net.get = mock_get
    return net


@pytest.fixture
def mock_stopped_network():
    """Create a mock stopped Network."""
    net = MagicMock()
    net.key = 2
    net.name = "stopped-network"

    def mock_get(key: str, default=None):
        data = {
            "running": False,
            "status": "stopped",
            "need_restart": False,
            "need_fw_apply": False,
            "need_dns_apply": False,
        }
        return data.get(key, default)

    net.get = mock_get
    return net


def test_network_apply_rules(cli_runner, mock_client, mock_running_network):
    """Apply rules command should call network.apply_rules()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "apply-rules", "test-network"])

    assert result.exit_code == 0
    mock_running_network.apply_rules.assert_called_once()


def test_network_apply_rules_not_running(cli_runner, mock_client, mock_stopped_network):
    """Apply rules should fail if network is not running."""
    mock_client.networks.list.return_value = [mock_stopped_network]
    mock_client.networks.get.return_value = mock_stopped_network

    result = cli_runner.invoke(app, ["network", "apply-rules", "stopped-network"])

    assert result.exit_code == 1
    assert "not running" in result.output
    mock_stopped_network.apply_rules.assert_not_called()


def test_network_apply_dns(cli_runner, mock_client, mock_running_network):
    """Apply DNS command should call network.apply_dns()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "apply-dns", "test-network"])

    assert result.exit_code == 0
    mock_running_network.apply_dns.assert_called_once()


def test_network_apply_dns_not_running(cli_runner, mock_client, mock_stopped_network):
    """Apply DNS should fail if network is not running."""
    mock_client.networks.list.return_value = [mock_stopped_network]
    mock_client.networks.get.return_value = mock_stopped_network

    result = cli_runner.invoke(app, ["network", "apply-dns", "stopped-network"])

    assert result.exit_code == 1
    assert "not running" in result.output
    mock_stopped_network.apply_dns.assert_not_called()


def test_network_restart(cli_runner, mock_client, mock_running_network):
    """Restart command should call network.restart()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "restart", "test-network"])

    assert result.exit_code == 0
    mock_running_network.restart.assert_called_once()


def test_network_restart_with_no_apply_rules(cli_runner, mock_client, mock_running_network):
    """Restart with --no-apply-rules should pass apply_rules=False."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "restart", "test-network", "--no-apply-rules"])

    assert result.exit_code == 0
    mock_running_network.restart.assert_called_once_with(apply_rules=False)


def test_network_status(cli_runner, mock_client, mock_running_network):
    """Status command should show detailed status flags."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "status", "test-network"])

    assert result.exit_code == 0
    assert "test-network" in result.output


def test_network_status_json_output(cli_runner, mock_client, mock_running_network):
    """Status command with JSON output should include all flags."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["--output", "json", "network", "status", "test-network"])

    assert result.exit_code == 0
    assert "needs_restart" in result.output
    assert "needs_rule_apply" in result.output
    assert "needs_dns_apply" in result.output
