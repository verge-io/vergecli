"""Tests for VM reset command."""

from __future__ import annotations

from verge_cli.cli import app


def test_vm_reset(cli_runner, mock_client, mock_vm):
    """vrg vm reset --yes should hard reset a running VM."""
    mock_vm.is_running = True
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "reset", "test-vm", "--yes"])

    assert result.exit_code == 0
    mock_vm.reset.assert_called_once()


def test_vm_reset_not_running(cli_runner, mock_client, mock_vm):
    """vrg vm reset on stopped VM should fail."""
    mock_vm.is_running = False
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "reset", "test-vm", "--yes"])

    assert result.exit_code == 1
    mock_vm.reset.assert_not_called()


def test_vm_reset_cancelled(cli_runner, mock_client, mock_vm):
    """vrg vm reset without --yes should prompt and cancel on 'n'."""
    mock_vm.is_running = True
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "reset", "test-vm"], input="n\n")

    assert result.exit_code == 0
    mock_vm.reset.assert_not_called()
