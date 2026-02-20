"""Tests for network dashboard and VPN status commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from verge_cli.cli import app


def _mock_ipsec_connection() -> MagicMock:
    """Create a mock IPSecActiveConnection."""
    conn = MagicMock()
    conn.connection = "site-to-site-vpn"
    conn.status = "established"

    def mock_get(k: str, default: Any = None) -> Any:
        data = {
            "connection": "site-to-site-vpn",
            "status": "established",
            "local_ip": "10.0.0.1",
            "remote_ip": "10.1.0.1",
            "local_subnet": "10.0.0.0/24",
            "remote_subnet": "10.1.0.0/24",
        }
        return data.get(k, default)

    conn.get = mock_get
    return conn


def _mock_wg_peer_status() -> MagicMock:
    """Create a mock WireGuardPeerStatus."""
    peer = MagicMock()
    peer.peer_key = 1
    peer.endpoint = "203.0.113.1:51820"
    peer.is_connected = True
    peer.latest_handshake = "2026-02-19T10:00:00"
    peer.allowed_ips = "10.100.0.0/24"

    def mock_get(k: str, default: Any = None) -> Any:
        data = {
            "peer_key": 1,
            "endpoint": "203.0.113.1:51820",
            "is_connected": True,
            "latest_handshake": "2026-02-19T10:00:00",
            "transfer_rx": "1.2 GiB",
            "transfer_tx": "500 MiB",
            "allowed_ips": "10.100.0.0/24",
        }
        return data.get(k, default)

    peer.get = mock_get
    return peer


def test_network_dashboard_overview(cli_runner, mock_client):
    """vrg network diag dashboard overview should display dashboard data."""
    mock_client.network_dashboard.get.return_value = {"networks": 5, "online": 4}

    result = cli_runner.invoke(app, ["network", "diag", "dashboard", "overview"])

    assert result.exit_code == 0
    mock_client.network_dashboard.get.assert_called_once()


def test_ipsec_status(cli_runner, mock_client, mock_network):
    """vrg network diag dashboard ipsec-status should show IPSec connections."""
    mock_conn = _mock_ipsec_connection()
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network
    mock_network.ipsec_connections.list.return_value = [mock_conn]

    result = cli_runner.invoke(
        app, ["network", "diag", "dashboard", "ipsec-status", "test-network"]
    )

    assert result.exit_code == 0
    assert "established" in result.output


def test_ipsec_status_empty(cli_runner, mock_client, mock_network):
    """vrg network diag dashboard ipsec-status with no connections."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network
    mock_network.ipsec_connections.list.return_value = []

    result = cli_runner.invoke(
        app, ["network", "diag", "dashboard", "ipsec-status", "test-network"]
    )

    assert result.exit_code == 0


def test_wireguard_status(cli_runner, mock_client, mock_network):
    """vrg network diag dashboard wireguard-status should show WG peer status."""
    mock_peer = _mock_wg_peer_status()
    mock_iface = MagicMock()
    mock_iface.peer_status.list.return_value = [mock_peer]

    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network
    mock_network.wireguard.list.return_value = [mock_iface]

    result = cli_runner.invoke(
        app, ["network", "diag", "dashboard", "wireguard-status", "test-network"]
    )

    assert result.exit_code == 0


def test_wireguard_status_no_interfaces(cli_runner, mock_client, mock_network):
    """vrg network diag dashboard wireguard-status with no WG interfaces."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.get.return_value = mock_network
    mock_network.wireguard.list.return_value = []

    result = cli_runner.invoke(
        app, ["network", "diag", "dashboard", "wireguard-status", "test-network"]
    )

    assert result.exit_code == 0
