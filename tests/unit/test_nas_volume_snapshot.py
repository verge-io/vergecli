"""Tests for NAS volume snapshot commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_snapshot_list(cli_runner, mock_client, mock_nas_volume, mock_nas_volume_snapshot):
    """vrg nas volume snapshot list should list snapshots for a volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.list.return_value = [mock_nas_volume_snapshot]

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "snapshot", "list", "data-vol"],
    )

    assert result.exit_code == 0
    assert "snap-001" in result.output
    mock_client.nas_volumes.snapshots.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_snapshot_get(cli_runner, mock_client, mock_nas_volume, mock_nas_volume_snapshot):
    """vrg nas volume snapshot get should get snapshot by name."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.list.return_value = [mock_nas_volume_snapshot]
    mock_snap_mgr.get.return_value = mock_nas_volume_snapshot

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "snapshot", "get", "data-vol", "snap-001"],
    )

    assert result.exit_code == 0
    assert "snap-001" in result.output
    mock_snap_mgr.get.assert_called_once_with(42)


def test_snapshot_create(cli_runner, mock_client, mock_nas_volume, mock_nas_volume_snapshot):
    """vrg nas volume snapshot create should create with --name and --expires-days."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.create.return_value = mock_nas_volume_snapshot

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "volume",
            "snapshot",
            "create",
            "data-vol",
            "--name",
            "snap-001",
            "--expires-days",
            "7",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_snap_mgr.create.assert_called_once_with(
        name="snap-001",
        expires_days=7,
    )


def test_snapshot_create_never_expires(
    cli_runner, mock_client, mock_nas_volume, mock_nas_volume_snapshot
):
    """vrg nas volume snapshot create --never-expires should pass never_expires flag."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.create.return_value = mock_nas_volume_snapshot

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "volume",
            "snapshot",
            "create",
            "data-vol",
            "--name",
            "snap-permanent",
            "--never-expires",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_snap_mgr.create.assert_called_once_with(
        name="snap-permanent",
        never_expires=True,
    )


def test_snapshot_delete(cli_runner, mock_client, mock_nas_volume, mock_nas_volume_snapshot):
    """vrg nas volume snapshot delete should delete with --yes."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.list.return_value = [mock_nas_volume_snapshot]

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "snapshot", "delete", "data-vol", "snap-001", "--yes"],
    )

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_snap_mgr.delete.assert_called_once_with(42)


def test_snapshot_not_found(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume snapshot get with unknown name should exit 6."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_snap_mgr = mock_client.nas_volumes.snapshots.return_value
    mock_snap_mgr.list.return_value = []

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "snapshot", "get", "data-vol", "nonexistent"],
    )

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
