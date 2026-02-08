"""Tests for VM snapshot sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_vm_snapshot() -> MagicMock:
    """Create a mock VM Snapshot object."""
    snap = MagicMock()
    snap.key = 700
    snap.name = "pre-upgrade"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 700,
            "name": "pre-upgrade",
            "created": 1707300000,
            "expires": 1707386400,
            "quiesced": True,
            "description": "Before system upgrade",
        }
        return data.get(key, default)

    snap.get = mock_get
    return snap


def test_snapshot_list(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot list should list snapshots for a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(app, ["vm", "snapshot", "list", "test-vm"])

    assert result.exit_code == 0
    assert "pre-upgrade" in result.output
    mock_vm.snapshots.list.assert_called_once()


def test_snapshot_list_empty(cli_runner, mock_client, mock_vm):
    """vrg vm snapshot list should handle empty list."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "snapshot", "list", "test-vm"])

    assert result.exit_code == 0


def test_snapshot_get(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot get should resolve by name."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]
    mock_vm.snapshots.get.return_value = mock_vm_snapshot

    result = cli_runner.invoke(app, ["vm", "snapshot", "get", "test-vm", "pre-upgrade"])

    assert result.exit_code == 0
    assert "pre-upgrade" in result.output


def test_snapshot_get_by_key(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot get should accept numeric key."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.get.return_value = mock_vm_snapshot

    result = cli_runner.invoke(app, ["vm", "snapshot", "get", "test-vm", "700"])

    assert result.exit_code == 0
    assert "pre-upgrade" in result.output


def test_snapshot_create(cli_runner, mock_client, mock_vm):
    """vrg vm snapshot create should create a snapshot with defaults."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.create.return_value = {"name": "auto-snapshot", "$key": 701}

    result = cli_runner.invoke(app, ["vm", "snapshot", "create", "test-vm"])

    assert result.exit_code == 0
    mock_vm.snapshots.create.assert_called_once_with(
        name=None,
        retention=86400,
        quiesce=False,
        description="",
    )


def test_snapshot_create_with_options(cli_runner, mock_client, mock_vm):
    """vrg vm snapshot create should accept --name, --retention, --quiesce, --description."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.create.return_value = {"name": "pre-upgrade", "$key": 702}

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "snapshot",
            "create",
            "test-vm",
            "--name",
            "pre-upgrade",
            "--retention",
            "172800",
            "--quiesce",
            "--description",
            "Before system upgrade",
        ],
    )

    assert result.exit_code == 0
    mock_vm.snapshots.create.assert_called_once_with(
        name="pre-upgrade",
        retention=172800,
        quiesce=True,
        description="Before system upgrade",
    )


def test_snapshot_delete(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot delete should remove a snapshot with --yes."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(app, ["vm", "snapshot", "delete", "test-vm", "pre-upgrade", "--yes"])

    assert result.exit_code == 0
    mock_vm.snapshots.delete.assert_called_once_with(700)


def test_snapshot_restore(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot restore should restore a snapshot (bare restore)."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(app, ["vm", "snapshot", "restore", "test-vm", "pre-upgrade"])

    assert result.exit_code == 0
    mock_vm.snapshots.restore.assert_called_once_with(
        700,
        name=None,
        replace_original=False,
        power_on=False,
    )


def test_snapshot_restore_clone(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot restore --name should clone to a new VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "snapshot",
            "restore",
            "test-vm",
            "pre-upgrade",
            "--name",
            "test-vm-clone",
        ],
    )

    assert result.exit_code == 0
    mock_vm.snapshots.restore.assert_called_once_with(
        700,
        name="test-vm-clone",
        replace_original=False,
        power_on=False,
    )
    assert "Cloned" in result.output


def test_snapshot_restore_replace(cli_runner, mock_client, mock_vm, mock_vm_snapshot):
    """vrg vm snapshot restore --replace --yes should replace the original."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "snapshot",
            "restore",
            "test-vm",
            "pre-upgrade",
            "--replace",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    mock_vm.snapshots.restore.assert_called_once_with(
        700,
        name=None,
        replace_original=True,
        power_on=False,
    )
    assert "Restored" in result.output


def test_snapshot_restore_replace_and_name_error(
    cli_runner, mock_client, mock_vm, mock_vm_snapshot
):
    """vrg vm snapshot restore --replace --name should fail (mutually exclusive)."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = [mock_vm_snapshot]

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "snapshot",
            "restore",
            "test-vm",
            "pre-upgrade",
            "--replace",
            "--name",
            "clone-name",
            "--yes",
        ],
    )

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_snapshot_not_found(cli_runner, mock_client, mock_vm):
    """vrg vm snapshot get with unknown name should exit 6."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "snapshot", "get", "test-vm", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output
