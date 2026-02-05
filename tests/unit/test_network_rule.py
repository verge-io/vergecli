"""Tests for network firewall rule commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_rules():
    """Create a mock Network for rule operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        return {"running": True}.get(key, default)

    net.get = mock_get
    return net


@pytest.fixture
def mock_rule():
    """Create a mock NetworkRule object."""
    rule = MagicMock()
    rule.key = 100
    rule.name = "Allow-HTTPS"

    def mock_get(key: str, default=None):
        data = {
            "name": "Allow-HTTPS",
            "direction": "incoming",
            "action": "accept",
            "protocol": "tcp",
            "destination_ports": "443",
            "enabled": True,
            "orderid": 1,
            "system_rule": False,
        }
        return data.get(key, default)

    rule.get = mock_get
    rule.is_system_rule = False
    rule.is_enabled = True
    return rule


def test_rule_list(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule list should show rules for a network."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]

    result = cli_runner.invoke(app, ["network", "rule", "list", "test-network"])

    assert result.exit_code == 0
    # Output may truncate names in table format, check for partial match
    assert "Allow" in result.output
    assert "incoming" in result.output
    assert "accept" in result.output


def test_rule_get(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule get should show rule details."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(app, ["network", "rule", "get", "test-network", "Allow-HTTPS"])

    assert result.exit_code == 0
    assert "Allow-HTTPS" in result.output


def test_rule_create(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule create should create a new rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.create.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        [
            "network",
            "rule",
            "create",
            "test-network",
            "--name",
            "Allow-HTTPS",
            "--direction",
            "incoming",
            "--action",
            "accept",
            "--protocol",
            "tcp",
            "--dest-ports",
            "443",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_rules.rules.create.assert_called_once()


def test_rule_delete(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule delete should delete a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "delete", "test-network", "Allow-HTTPS", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_rules.rules.delete.assert_called_once_with(100)


def test_rule_enable(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule enable should enable a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "enable", "test-network", "Allow-HTTPS"],
    )

    assert result.exit_code == 0
    mock_rule.enable.assert_called_once()


def test_rule_disable(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule disable should disable a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "disable", "test-network", "Allow-HTTPS"],
    )

    assert result.exit_code == 0
    mock_rule.disable.assert_called_once()
