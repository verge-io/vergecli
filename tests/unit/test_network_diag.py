"""Tests for network diagnostics commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_diag():
    """Create a mock Network for diagnostics operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        return {"running": True}.get(key, default)

    net.get = mock_get
    return net


@pytest.fixture
def mock_lease():
    """Create a mock DHCP lease entry."""
    return {
        "mac": "00:50:56:01:02:03",
        "ip": "10.0.0.100",
        "hostname": "workstation-1",
        "expires": "2026-02-06T10:00:00Z",
        "state": "active",
    }


@pytest.fixture
def mock_address():
    """Create a mock network address entry."""
    return {
        "ip": "10.0.0.1",
        "mac": "00:50:56:00:00:01",
        "interface": "eth0",
        "type": "static",
    }


@pytest.fixture
def mock_stats():
    """Create mock network statistics."""
    return {
        "bytes_in": 1024000,
        "bytes_out": 512000,
        "packets_in": 10000,
        "packets_out": 8000,
        "errors_in": 0,
        "errors_out": 0,
    }


def test_diag_leases(cli_runner, mock_client, mock_network_for_diag, mock_lease):
    """Diag leases should show DHCP leases for a network."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = [mock_lease]

    result = cli_runner.invoke(app, ["network", "diag", "leases", "test-network"])

    assert result.exit_code == 0
    mock_network_for_diag.diagnostics.assert_called_once_with(diagnostic_type="dhcp_leases")
    assert "10.0.0.100" in result.output
    assert "workstation-1" in result.output


def test_diag_leases_empty(cli_runner, mock_client, mock_network_for_diag):
    """Diag leases should handle empty lease list."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = []

    result = cli_runner.invoke(app, ["network", "diag", "leases", "test-network"])

    assert result.exit_code == 0
    assert "No results" in result.output or result.output.strip() == ""


def test_diag_leases_json_output(cli_runner, mock_client, mock_network_for_diag, mock_lease):
    """Diag leases should support JSON output."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = [mock_lease]

    result = cli_runner.invoke(app, ["network", "diag", "leases", "test-network", "-o", "json"])

    assert result.exit_code == 0
    assert "10.0.0.100" in result.output
    assert "workstation-1" in result.output


def test_diag_addresses(cli_runner, mock_client, mock_network_for_diag, mock_address):
    """Diag addresses should show network addresses."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = [mock_address]

    result = cli_runner.invoke(app, ["network", "diag", "addresses", "test-network"])

    assert result.exit_code == 0
    mock_network_for_diag.diagnostics.assert_called_once_with(diagnostic_type="addresses")
    assert "10.0.0.1" in result.output


def test_diag_addresses_empty(cli_runner, mock_client, mock_network_for_diag):
    """Diag addresses should handle empty address list."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = []

    result = cli_runner.invoke(app, ["network", "diag", "addresses", "test-network"])

    assert result.exit_code == 0
    assert "No results" in result.output or result.output.strip() == ""


def test_diag_addresses_json_output(cli_runner, mock_client, mock_network_for_diag, mock_address):
    """Diag addresses should support JSON output."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = [mock_address]

    result = cli_runner.invoke(app, ["network", "diag", "addresses", "test-network", "-o", "json"])

    assert result.exit_code == 0
    assert "10.0.0.1" in result.output


def test_diag_stats(cli_runner, mock_client, mock_network_for_diag, mock_stats):
    """Diag stats should show network statistics."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.statistics.return_value = mock_stats

    result = cli_runner.invoke(app, ["network", "diag", "stats", "test-network"])

    assert result.exit_code == 0
    mock_network_for_diag.statistics.assert_called_once()
    # Check for bytes (may be formatted)
    assert "1024000" in result.output or "bytes" in result.output.lower()


def test_diag_stats_json_output(cli_runner, mock_client, mock_network_for_diag, mock_stats):
    """Diag stats should support JSON output."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.statistics.return_value = mock_stats

    result = cli_runner.invoke(app, ["network", "diag", "stats", "test-network", "-o", "json"])

    assert result.exit_code == 0
    assert "bytes_in" in result.output
    assert "1024000" in result.output


def test_diag_stats_dict_response(cli_runner, mock_client, mock_network_for_diag):
    """Diag stats should handle dict-like response from SDK."""
    mock_client.networks.list.return_value = [mock_network_for_diag]
    mock_client.networks.get.return_value = mock_network_for_diag

    # Create a mock object that supports both dict-like and attribute access
    stats_obj = MagicMock()
    stats_obj.get.side_effect = lambda k, d=None: {
        "bytes_in": 2048000,
        "bytes_out": 1024000,
        "packets_in": 20000,
        "packets_out": 16000,
    }.get(k, d)
    mock_network_for_diag.statistics.return_value = stats_obj

    result = cli_runner.invoke(app, ["network", "diag", "stats", "test-network"])

    assert result.exit_code == 0


def test_diag_network_not_found(cli_runner, mock_client):
    """Diag commands should error when network not found."""
    mock_client.networks.list.return_value = []

    result = cli_runner.invoke(app, ["network", "diag", "leases", "nonexistent"])

    assert result.exit_code != 0


def test_diag_with_network_key(cli_runner, mock_client, mock_network_for_diag, mock_lease):
    """Diag commands should work with numeric network key."""
    mock_client.networks.get.return_value = mock_network_for_diag
    mock_network_for_diag.diagnostics.return_value = [mock_lease]

    result = cli_runner.invoke(app, ["network", "diag", "leases", "1"])

    assert result.exit_code == 0
    mock_client.networks.get.assert_called_with(1)


def test_diag_help(cli_runner):
    """Diag command should show help."""
    result = cli_runner.invoke(app, ["network", "diag", "--help"])

    assert result.exit_code == 0
    assert "leases" in result.output
    assert "addresses" in result.output
    assert "stats" in result.output
