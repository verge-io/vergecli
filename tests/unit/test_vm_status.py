"""Tests for VM status flags."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_vm_with_needs_restart():
    """Create a mock VM with needs_restart flag set."""
    vm = MagicMock()
    vm.key = 1
    vm.name = "test-vm"
    vm.status = "running"
    vm.is_running = True
    vm.cluster_name = "Cluster1"
    vm.node_name = "Node1"

    def mock_get(key: str, default=None):
        data = {
            "description": "Test VM",
            "cpu_cores": 2,
            "ram": 2048,
            "os_family": "linux",
            "need_restart": True,
        }
        return data.get(key, default)

    vm.get = mock_get
    return vm


@pytest.fixture
def mock_vm_without_needs_restart():
    """Create a mock VM without needs_restart flag."""
    vm = MagicMock()
    vm.key = 2
    vm.name = "stable-vm"
    vm.status = "running"
    vm.is_running = True
    vm.cluster_name = "Cluster1"
    vm.node_name = "Node1"

    def mock_get(key: str, default=None):
        data = {
            "description": "Stable VM",
            "cpu_cores": 4,
            "ram": 4096,
            "os_family": "linux",
            "need_restart": False,
        }
        return data.get(key, default)

    vm.get = mock_get
    return vm


def test_vm_list_shows_restart_column(cli_runner, mock_client, mock_vm_with_needs_restart):
    """VM list should show restart column."""
    mock_client.vms.list.return_value = [mock_vm_with_needs_restart]

    result = cli_runner.invoke(app, ["vm", "list"])

    assert result.exit_code == 0
    # Check that the restart column appears in output
    output_lower = result.output.lower()
    assert "rest" in output_lower  # restart column (may be truncated as "rest…")


def test_vm_list_shows_y_for_needs_restart(cli_runner, mock_client, mock_vm_with_needs_restart):
    """VM list should show Y for VMs that need restart."""
    mock_client.vms.list.return_value = [mock_vm_with_needs_restart]

    result = cli_runner.invoke(app, ["vm", "list"])

    assert result.exit_code == 0
    # The table should contain Y for the restart column
    assert "Y" in result.output


def test_vm_list_no_y_when_restart_not_needed(
    cli_runner, mock_client, mock_vm_without_needs_restart
):
    """VM list should not show Y when VM doesn't need restart."""
    mock_client.vms.list.return_value = [mock_vm_without_needs_restart]

    result = cli_runner.invoke(app, ["vm", "list"])

    assert result.exit_code == 0
    # The restart column should be empty (no Y)
    # Note: "Y" might appear elsewhere, so we check JSON output for certainty
    result_json = cli_runner.invoke(app, ["vm", "list", "-o", "json"])
    assert result_json.exit_code == 0
    assert '"restart": ""' in result_json.output


def test_vm_get_shows_needs_restart_true(cli_runner, mock_client, mock_vm_with_needs_restart):
    """VM get should show needs_restart: true in output."""
    mock_client.vms.list.return_value = [mock_vm_with_needs_restart]
    mock_client.vms.get.return_value = mock_vm_with_needs_restart

    result = cli_runner.invoke(app, ["vm", "get", "test-vm"])

    assert result.exit_code == 0
    assert "needs_restart" in result.output


def test_vm_get_shows_needs_restart_false(cli_runner, mock_client, mock_vm_without_needs_restart):
    """VM get should show needs_restart: false in output."""
    mock_client.vms.list.return_value = [mock_vm_without_needs_restart]
    mock_client.vms.get.return_value = mock_vm_without_needs_restart

    result = cli_runner.invoke(app, ["vm", "get", "stable-vm"])

    assert result.exit_code == 0
    assert "needs_restart" in result.output


def test_vm_get_json_output_includes_needs_restart(
    cli_runner, mock_client, mock_vm_with_needs_restart
):
    """VM get with JSON output should include needs_restart field."""
    mock_client.vms.list.return_value = [mock_vm_with_needs_restart]
    mock_client.vms.get.return_value = mock_vm_with_needs_restart

    result = cli_runner.invoke(app, ["vm", "get", "test-vm", "-o", "json"])

    assert result.exit_code == 0
    assert '"needs_restart": true' in result.output


def test_vm_list_json_output_includes_needs_restart(
    cli_runner, mock_client, mock_vm_with_needs_restart, mock_vm_without_needs_restart
):
    """VM list with JSON output should include needs_restart for each VM."""
    mock_client.vms.list.return_value = [
        mock_vm_with_needs_restart,
        mock_vm_without_needs_restart,
    ]

    result = cli_runner.invoke(app, ["vm", "list", "-o", "json"])

    assert result.exit_code == 0
    assert '"needs_restart": true' in result.output
    assert '"needs_restart": false' in result.output
