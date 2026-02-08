"""Tests for cloud snapshot commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_cloud_snapshot() -> MagicMock:
    """Create a mock CloudSnapshot object."""
    snap = MagicMock()
    snap.key = 800
    snap.name = "daily-2026-02-08"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 800,
            "name": "daily-2026-02-08",
            "status": "normal",
            "created": 1707350400,
            "expires": 1707609600,
            "immutable": False,
            "private": False,
            "description": "Daily cloud snapshot",
        }
        return data.get(key, default)

    snap.get = mock_get
    return snap


@pytest.fixture
def mock_snapshot_vm() -> MagicMock:
    """Create a mock CloudSnapshotVM object."""
    vm = MagicMock()
    vm.key = 900
    vm.name = "web-server"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 900,
            "name": "web-server",
            "status": "idle",
        }
        return data.get(key, default)

    vm.get = mock_get
    return vm


@pytest.fixture
def mock_snapshot_tenant() -> MagicMock:
    """Create a mock CloudSnapshotTenant object."""
    tenant = MagicMock()
    tenant.key = 950
    tenant.name = "acme-tenant"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 950,
            "name": "acme-tenant",
            "status": "idle",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


def test_snapshot_list(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot list should list cloud snapshots."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]

    result = cli_runner.invoke(app, ["snapshot", "list"])

    assert result.exit_code == 0
    assert "daily-2026-02-08" in result.output
    mock_client.cloud_snapshots.list.assert_called_once_with(include_expired=False)


def test_snapshot_list_include_expired(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot list --include-expired should pass flag to SDK."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]

    result = cli_runner.invoke(app, ["snapshot", "list", "--include-expired"])

    assert result.exit_code == 0
    mock_client.cloud_snapshots.list.assert_called_once_with(include_expired=True)


def test_snapshot_list_empty(cli_runner, mock_client):
    """vrg snapshot list should handle empty list."""
    mock_client.cloud_snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "list"])

    assert result.exit_code == 0


def test_snapshot_get(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot get should resolve by name."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]
    mock_client.cloud_snapshots.get.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(app, ["snapshot", "get", "daily-2026-02-08"])

    assert result.exit_code == 0
    assert "daily-2026-02-08" in result.output


def test_snapshot_get_by_key(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot get should accept numeric key."""
    mock_client.cloud_snapshots.get.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(app, ["snapshot", "get", "800"])

    assert result.exit_code == 0
    assert "daily-2026-02-08" in result.output
    mock_client.cloud_snapshots.get.assert_called_once_with(800)


def test_snapshot_create(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot create should create a snapshot with defaults."""
    mock_client.cloud_snapshots.create.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(app, ["snapshot", "create"])

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.cloud_snapshots.create.assert_called_once_with(
        name=None,
        immutable=False,
        private=False,
        wait=False,
    )


def test_snapshot_create_with_options(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot create should accept --name, --retention, --immutable, --private."""
    mock_client.cloud_snapshots.create.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "create",
            "--name",
            "pre-upgrade",
            "--retention",
            "604800",
            "--immutable",
            "--private",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.cloud_snapshots.create.assert_called_once_with(
        name="pre-upgrade",
        retention_seconds=604800,
        immutable=True,
        private=True,
        wait=False,
    )


def test_snapshot_create_never_expire(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot create --never-expire should pass never_expire to SDK."""
    mock_client.cloud_snapshots.create.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(app, ["snapshot", "create", "--never-expire"])

    assert result.exit_code == 0
    mock_client.cloud_snapshots.create.assert_called_once_with(
        name=None,
        never_expire=True,
        immutable=False,
        private=False,
        wait=False,
    )


def test_snapshot_create_wait(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot create --wait should pass wait=True to SDK."""
    mock_client.cloud_snapshots.create.return_value = mock_cloud_snapshot

    result = cli_runner.invoke(app, ["snapshot", "create", "--wait"])

    assert result.exit_code == 0
    mock_client.cloud_snapshots.create.assert_called_once_with(
        name=None,
        immutable=False,
        private=False,
        wait=True,
    )


def test_snapshot_delete(cli_runner, mock_client, mock_cloud_snapshot):
    """vrg snapshot delete should remove a snapshot with --yes."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]

    result = cli_runner.invoke(app, ["snapshot", "delete", "daily-2026-02-08", "--yes"])

    assert result.exit_code == 0
    mock_client.cloud_snapshots.delete.assert_called_once_with(800)
    assert "Deleted" in result.output


def test_snapshot_vms(cli_runner, mock_client, mock_cloud_snapshot, mock_snapshot_vm):
    """vrg snapshot vms should list VMs in a snapshot."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]
    mock_client.cloud_snapshots.vms.return_value.list.return_value = [mock_snapshot_vm]

    result = cli_runner.invoke(app, ["snapshot", "vms", "daily-2026-02-08"])

    assert result.exit_code == 0
    assert "web-server" in result.output
    mock_client.cloud_snapshots.vms.assert_called_once_with(800)


def test_snapshot_tenants(cli_runner, mock_client, mock_cloud_snapshot, mock_snapshot_tenant):
    """vrg snapshot tenants should list tenants in a snapshot."""
    mock_client.cloud_snapshots.list.return_value = [mock_cloud_snapshot]
    mock_client.cloud_snapshots.tenants.return_value.list.return_value = [mock_snapshot_tenant]

    result = cli_runner.invoke(app, ["snapshot", "tenants", "daily-2026-02-08"])

    assert result.exit_code == 0
    assert "acme-tenant" in result.output
    mock_client.cloud_snapshots.tenants.assert_called_once_with(800)


def test_snapshot_not_found(cli_runner, mock_client):
    """vrg snapshot get with unknown name should exit 6."""
    mock_client.cloud_snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()


def test_snapshot_create_retention_and_never_expire_error(cli_runner, mock_client):
    """vrg snapshot create with --retention and --never-expire should fail."""
    result = cli_runner.invoke(
        app,
        ["snapshot", "create", "--retention", "604800", "--never-expire"],
    )

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output
