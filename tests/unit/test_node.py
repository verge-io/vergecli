"""Tests for node commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from verge_cli.cli import app


def _mock_pci_device() -> MagicMock:
    """Create a mock NodePCIDevice."""
    pci = MagicMock()
    pci.key = 1
    pci.name = "Intel Ethernet Controller"

    def mock_get(k: str, default: Any = None) -> Any:
        data = {
            "name": "Intel Ethernet Controller",
            "slot": "00:1f.6",
            "vendor": "Intel Corporation",
            "device": "Ethernet Connection I219-LM",
            "driver": "e1000e",
            "class_display": "Network controller",
            "class": "Network controller",
        }
        return data.get(k, default)

    pci.get = mock_get
    return pci


def _mock_gpu_device() -> MagicMock:
    """Create a mock NodeGpu."""
    gpu = MagicMock()
    gpu.key = 5
    gpu.name = "NVIDIA A100"

    def mock_get(k: str, default: Any = None) -> Any:
        data = {
            "name": "NVIDIA A100",
            "slot": "3b:00.0",
            "vendor": "NVIDIA Corporation",
            "device": "A100 PCIe 40GB",
            "driver": "nvidia",
            "max_instances": 24,
        }
        return data.get(k, default)

    gpu.get = mock_get
    return gpu


def test_node_list(cli_runner, mock_client, mock_node):
    """vrg node list should list all nodes."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "node1" in result.output
    mock_client.nodes.list.assert_called_once()


def test_node_list_empty(cli_runner, mock_client):
    """vrg node list should handle empty results."""
    mock_client.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_node_list_with_cluster_filter(cli_runner, mock_client, mock_node):
    """vrg node list --cluster should filter by cluster name."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list", "--cluster", "Cluster1"])

    assert result.exit_code == 0
    assert "node1" in result.output
    call_kwargs = mock_client.nodes.list.call_args[1]
    assert call_kwargs["cluster"] == "Cluster1"


def test_node_list_json(cli_runner, mock_client, mock_node):
    """vrg node list --output json should output JSON."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["--output", "json", "node", "list"])

    assert result.exit_code == 0
    assert '"name": "node1"' in result.output


def test_node_get(cli_runner, mock_client, mock_node):
    """vrg node get should show node details."""
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "node1"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_get_by_key(cli_runner, mock_client, mock_node):
    """vrg node get by numeric key should work."""
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "10"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_maintenance_enable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --enable should enable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--enable"])

    assert result.exit_code == 0
    mock_client.nodes.enable_maintenance.assert_called_once_with(10)


def test_node_maintenance_disable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --disable should disable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--disable"])

    assert result.exit_code == 0
    mock_client.nodes.disable_maintenance.assert_called_once_with(10)


def test_node_maintenance_no_flag(cli_runner, mock_client, mock_node):
    """vrg node maintenance without --enable or --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1"])

    assert result.exit_code == 2


def test_node_maintenance_both_flags(cli_runner, mock_client, mock_node):
    """vrg node maintenance with both --enable and --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--enable", "--disable"])

    assert result.exit_code == 2


def test_node_restart(cli_runner, mock_client, mock_node):
    """vrg node restart --yes should restart the node."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "restart", "node1", "--yes"])

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_called_once_with(10)


def test_node_restart_without_yes(cli_runner, mock_client, mock_node):
    """vrg node restart without --yes should prompt and abort on 'n'."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "restart", "node1"], input="n\n")

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_not_called()


def test_node_pci_list(cli_runner, mock_client, mock_node):
    """vrg node pci-list should list PCI devices on a node."""
    mock_pci = _mock_pci_device()
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.pci_devices.return_value.list.return_value = [mock_pci]

    result = cli_runner.invoke(app, ["node", "pci-list", "node1"])

    assert result.exit_code == 0
    assert "Intel" in result.output
    mock_client.nodes.pci_devices.assert_called_once_with(10)


def test_node_pci_list_by_key(cli_runner, mock_client):
    """vrg node pci-list should accept numeric key."""
    mock_pci = _mock_pci_device()
    mock_client.nodes.pci_devices.return_value.list.return_value = [mock_pci]

    result = cli_runner.invoke(app, ["node", "pci-list", "10"])

    assert result.exit_code == 0
    mock_client.nodes.pci_devices.assert_called_once_with(10)


def test_node_gpu_list(cli_runner, mock_client, mock_node):
    """vrg node gpu-list should list GPU devices on a node."""
    mock_gpu = _mock_gpu_device()
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.gpus.return_value.list.return_value = [mock_gpu]

    result = cli_runner.invoke(app, ["node", "gpu-list", "node1"])

    assert result.exit_code == 0
    assert "NVIDIA" in result.output
    mock_client.nodes.gpus.assert_called_once_with(10)


def test_node_stats(cli_runner, mock_client, mock_node):
    """vrg node stats should display node statistics."""
    mock_stats = {"cpu_usage": 35.0, "ram_used_gb": 32.0, "ram_total_gb": 64.0}
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.get.return_value = mock_node
    mock_node.stats.get.return_value = mock_stats

    result = cli_runner.invoke(app, ["node", "stats", "node1"])

    assert result.exit_code == 0
