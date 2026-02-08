"""Tests for tenant snapshot sub-resource commands."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_snapshot() -> MagicMock:
    """Create a mock Tenant Snapshot object."""
    snap = MagicMock()
    snap.key = 600
    snap.name = "daily-backup"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 600,
            "name": "daily-backup",
            "created": 1707300000,
            "expires": 0,
            "profile": "default",
        }
        return data.get(key, default)

    snap.get = mock_get
    return snap


def test_snapshot_list(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot list should list snapshots."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(app, ["tenant", "snapshot", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_tenant.snapshots.list.assert_called_once()


def test_snapshot_get(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot get should show snapshot details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]
    mock_tenant.snapshots.get.return_value = mock_snapshot

    result = cli_runner.invoke(app, ["tenant", "snapshot", "get", "acme-corp", "daily-backup"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output


def test_snapshot_get_by_key(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot get should accept numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.get.return_value = mock_snapshot

    result = cli_runner.invoke(app, ["tenant", "snapshot", "get", "acme-corp", "600"])

    assert result.exit_code == 0


def test_snapshot_create(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot create should create a snapshot."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.create.return_value = mock_snapshot

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "snapshot",
            "create",
            "acme-corp",
            "--name",
            "daily-backup",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.snapshots.create.assert_called_once()


def test_snapshot_create_with_expires(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot create should accept --expires-in-days."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.create.return_value = mock_snapshot

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "snapshot",
            "create",
            "acme-corp",
            "--name",
            "daily-backup",
            "--expires-in-days",
            "30",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.snapshots.create.call_args[1]
    assert call_kwargs["expires_in_days"] == 30


def test_snapshot_delete(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot delete should remove a snapshot with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(
        app, ["tenant", "snapshot", "delete", "acme-corp", "daily-backup", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.snapshots.delete.assert_called_once_with(600)


def test_snapshot_restore(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot restore should restore a snapshot."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(app, ["tenant", "snapshot", "restore", "acme-corp", "daily-backup"])

    assert result.exit_code == 0
    mock_tenant.snapshots.restore.assert_called_once_with(600)


def test_snapshot_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant snapshot list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "snapshot", "list", "acme-corp"])

    assert result.exit_code == 0
