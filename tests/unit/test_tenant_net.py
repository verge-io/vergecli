"""Tests for tenant networking sub-resource commands."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


# --- Network Block fixtures ---


@pytest.fixture
def mock_net_block() -> MagicMock:
    """Create a mock Network Block object."""
    block = MagicMock()
    block.key = 300
    block.name = "block-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 300,
            "cidr": "10.0.0.0/24",
            "network_name": "DMZ",
            "description": "DMZ network block",
        }
        return data.get(key, default)

    block.get = mock_get
    return block


# --- External IP fixtures ---


@pytest.fixture
def mock_ext_ip() -> MagicMock:
    """Create a mock External IP object."""
    ip = MagicMock()
    ip.key = 400
    ip.name = "ext-ip-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 400,
            "ip_address": "203.0.113.10",
            "network_name": "External",
            "hostname": "web.acme.com",
        }
        return data.get(key, default)

    ip.get = mock_get
    return ip


# --- L2 Network fixtures ---


@pytest.fixture
def mock_l2() -> MagicMock:
    """Create a mock L2 Network object."""
    l2 = MagicMock()
    l2.key = 500
    l2.name = "l2-trunk"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 500,
            "network_name": "Trunk VLAN",
            "network_type": "physical",
            "enabled": True,
        }
        return data.get(key, default)

    l2.get = mock_get
    return l2


# ===== Network Block Tests =====


def test_net_block_list(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block list should list network blocks."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = [mock_net_block]

    result = cli_runner.invoke(app, ["tenant", "net-block", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "10.0.0.0/24" in result.output
    mock_tenant.network_blocks.list.assert_called_once()


def test_net_block_create(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block create should create a network block."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.create.return_value = mock_net_block

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "net-block",
            "create",
            "acme-corp",
            "--cidr",
            "10.0.0.0/24",
            "--network",
            "1",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.network_blocks.create.assert_called_once()
    call_kwargs = mock_tenant.network_blocks.create.call_args[1]
    assert call_kwargs["cidr"] == "10.0.0.0/24"
    assert call_kwargs["network"] == 1


def test_net_block_delete(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block delete should remove a block with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = [mock_net_block]

    result = cli_runner.invoke(
        app, ["tenant", "net-block", "delete", "acme-corp", "block-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.network_blocks.delete.assert_called_once_with(300)


def test_net_block_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant net-block list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "net-block", "list", "acme-corp"])

    assert result.exit_code == 0


# ===== External IP Tests =====


def test_ext_ip_list(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip list should list external IPs."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.list.return_value = [mock_ext_ip]

    result = cli_runner.invoke(app, ["tenant", "ext-ip", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "203.0.113.10" in result.output
    mock_tenant.external_ips.list.assert_called_once()


def test_ext_ip_create(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip create should create an external IP."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.create.return_value = mock_ext_ip

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "ext-ip",
            "create",
            "acme-corp",
            "--ip",
            "203.0.113.10",
            "--network",
            "2",
            "--hostname",
            "web.acme.com",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.external_ips.create.assert_called_once()
    call_kwargs = mock_tenant.external_ips.create.call_args[1]
    assert call_kwargs["ip"] == "203.0.113.10"
    assert call_kwargs["network"] == 2
    assert call_kwargs["hostname"] == "web.acme.com"


def test_ext_ip_delete(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip delete should remove an IP with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.list.return_value = [mock_ext_ip]

    result = cli_runner.invoke(
        app, ["tenant", "ext-ip", "delete", "acme-corp", "ext-ip-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.external_ips.delete.assert_called_once_with(400)


# ===== L2 Network Tests =====


def test_l2_list(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 list should list L2 networks."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.list.return_value = [mock_l2]

    result = cli_runner.invoke(app, ["tenant", "l2", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "Trunk VLAN" in result.output
    mock_tenant.l2_networks.list.assert_called_once()


def test_l2_create(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 create should create an L2 network."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.create.return_value = mock_l2

    result = cli_runner.invoke(
        app,
        ["tenant", "l2", "create", "acme-corp", "--network-name", "Trunk VLAN"],
    )

    assert result.exit_code == 0
    mock_tenant.l2_networks.create.assert_called_once()
    call_kwargs = mock_tenant.l2_networks.create.call_args[1]
    assert call_kwargs["network_name"] == "Trunk VLAN"


def test_l2_delete(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 delete should remove an L2 network with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.list.return_value = [mock_l2]

    result = cli_runner.invoke(app, ["tenant", "l2", "delete", "acme-corp", "l2-trunk", "--yes"])

    assert result.exit_code == 0
    mock_tenant.l2_networks.delete.assert_called_once_with(500)
