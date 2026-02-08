"""Tests for tenant node sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant_node() -> MagicMock:
    """Create a mock Tenant Node object."""
    node = MagicMock()
    node.key = 100
    node.name = "tenant-node-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data: dict[str, Any] = {
            "$key": 100,
            "name": "tenant-node-1",
            "cpu_cores": 4,
            "ram": 8192,
            "status": "running",
            "enabled": True,
            "cluster": 1,
            "cluster_name": "Cluster1",
            "host_node": "Node1",
        }
        return data.get(key, default)

    node.get = mock_get
    return node


def test_tenant_node_list(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node list should list nodes on a tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(app, ["tenant", "node", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output
    mock_tenant.nodes.list.assert_called_once()


def test_tenant_node_get(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node get should show node details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]
    mock_tenant.nodes.get.return_value = mock_tenant_node

    result = cli_runner.invoke(app, ["tenant", "node", "get", "acme-corp", "tenant-node-1"])

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output


def test_tenant_node_get_by_key(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node get should accept numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.get.return_value = mock_tenant_node

    result = cli_runner.invoke(app, ["tenant", "node", "get", "acme-corp", "100"])

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output


def test_tenant_node_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant node list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "node", "list", "acme-corp"])

    assert result.exit_code == 0


def test_tenant_node_create(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node create should create a compute node."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.create.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "create",
            "acme-corp",
            "--cpu-cores",
            "4",
            "--ram-gb",
            "8",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.nodes.create.assert_called_once()
    call_kwargs = mock_tenant.nodes.create.call_args[1]
    assert call_kwargs["cpu_cores"] == 4
    assert call_kwargs["ram_gb"] == 8


def test_tenant_node_create_with_options(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node create should accept optional flags."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.create.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "create",
            "acme-corp",
            "--cpu-cores",
            "8",
            "--ram-gb",
            "16",
            "--cluster",
            "1",
            "--name",
            "big-node",
            "--preferred-node",
            "2",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.nodes.create.call_args[1]
    assert call_kwargs["cpu_cores"] == 8
    assert call_kwargs["ram_gb"] == 16
    assert call_kwargs["cluster"] == 1
    assert call_kwargs["name"] == "big-node"
    assert call_kwargs["preferred_node"] == 2


def test_tenant_node_update(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node update should update node properties."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]
    mock_tenant.nodes.update.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "update",
            "acme-corp",
            "tenant-node-1",
            "--cpu-cores",
            "8",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.nodes.update.assert_called_once()


def test_tenant_node_update_no_changes(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node update with no flags should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(app, ["tenant", "node", "update", "acme-corp", "tenant-node-1"])

    assert result.exit_code == 2


def test_tenant_node_delete(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node delete should remove a node with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(
        app, ["tenant", "node", "delete", "acme-corp", "tenant-node-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.nodes.delete.assert_called_once_with(100)


def test_tenant_node_delete_cancelled(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node delete without --yes should prompt and cancel on 'n'."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(
        app, ["tenant", "node", "delete", "acme-corp", "tenant-node-1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_tenant.nodes.delete.assert_not_called()
