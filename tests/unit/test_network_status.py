"""Tests for network status flags."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_with_flags():
    """Create a mock Network with status flags."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        data = {
            "description": "Test Network",
            "type": "internal",
            "network": "10.0.0.0/24",
            "ipaddress": "10.0.0.1",
            "status": "running",
            "running": True,
            "need_restart": True,
            "need_fw_apply": True,
            "need_dns_apply": False,
        }
        return data.get(key, default)

    net.get = mock_get
    return net


def test_network_list_shows_status_flags(cli_runner, mock_client, mock_network_with_flags):
    """Network list should show restart/rules/dns_apply columns."""
    mock_client.networks.list.return_value = [mock_network_with_flags]

    result = cli_runner.invoke(app, ["network", "list"])

    assert result.exit_code == 0
    # Check that status flag columns appear (may be truncated in table output)
    output_lower = result.output.lower()
    assert "rest" in output_lower  # restart column (may be truncated as "rest…")
    assert "rules" in output_lower  # rules column
    assert "apply" in output_lower  # dns_apply column (truncated as "apply")


def test_network_get_shows_status_flags(cli_runner, mock_client, mock_network_with_flags):
    """Network get should show status flags in output."""
    mock_client.networks.list.return_value = [mock_network_with_flags]
    mock_client.networks.get.return_value = mock_network_with_flags

    result = cli_runner.invoke(app, ["network", "get", "test-network"])

    assert result.exit_code == 0
    assert "needs_restart" in result.output or "need_restart" in result.output
