"""Tests for NAS volume sync management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_sync_list(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync list should list all sync jobs."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "list"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_client.volume_syncs.list.assert_called_once_with()


def test_sync_list_by_service(cli_runner, mock_client, mock_nas_sync, mock_nas_service):
    """vrg nas sync list --service should filter by service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "list", "--service", "nas01"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_client.volume_syncs.list.assert_called_once_with(service=1)


def test_sync_get(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync get should resolve by name."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]
    mock_client.volume_syncs.get.return_value = mock_nas_sync

    result = cli_runner.invoke(app, ["nas", "sync", "get", "daily-backup"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output


def test_sync_get_by_hex_key(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync get should accept 40-char hex key directly."""
    mock_client.volume_syncs.get.return_value = mock_nas_sync
    hex_key = "aabb001122334455667788990011223344556677"

    result = cli_runner.invoke(app, ["nas", "sync", "get", hex_key])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_client.volume_syncs.get.assert_called_once_with(key=hex_key)


def test_sync_create(cli_runner, mock_client, mock_nas_sync, mock_nas_service, mock_nas_volume):
    """vrg nas sync create should create with required args."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.volume_syncs.create.return_value = mock_nas_sync

    src_vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    dst_vol_key = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5"

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "sync",
            "create",
            "--name",
            "daily-backup",
            "--service",
            "nas01",
            "--source-volume",
            src_vol_key,
            "--dest-volume",
            dst_vol_key,
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.volume_syncs.create.assert_called_once_with(
        name="daily-backup",
        service=1,
        source_volume=src_vol_key,
        destination_volume=dst_vol_key,
        sync_method="ysync",
        destination_delete="never",
        workers=4,
        preserve_acls=True,
        preserve_permissions=True,
        preserve_owner=True,
        preserve_groups=True,
        preserve_mod_time=True,
        preserve_xattrs=True,
        copy_symlinks=True,
        freeze_filesystem=False,
    )


def test_sync_create_with_options(
    cli_runner, mock_client, mock_nas_sync, mock_nas_service, mock_nas_volume
):
    """vrg nas sync create with --sync-method, --workers, --include, --exclude."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.volume_syncs.create.return_value = mock_nas_sync

    src_vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    dst_vol_key = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5"

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "sync",
            "create",
            "--name",
            "daily-backup",
            "--service",
            "nas01",
            "--source-volume",
            src_vol_key,
            "--dest-volume",
            dst_vol_key,
            "--sync-method",
            "rsync",
            "--workers",
            "8",
            "--include",
            "*.docx,*.xlsx",
            "--exclude",
            "temp/*",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.volume_syncs.create.assert_called_once_with(
        name="daily-backup",
        service=1,
        source_volume=src_vol_key,
        destination_volume=dst_vol_key,
        sync_method="rsync",
        destination_delete="never",
        workers=8,
        preserve_acls=True,
        preserve_permissions=True,
        preserve_owner=True,
        preserve_groups=True,
        preserve_mod_time=True,
        preserve_xattrs=True,
        copy_symlinks=True,
        freeze_filesystem=False,
        include=["*.docx", "*.xlsx"],
        exclude=["temp/*"],
    )


def test_sync_create_with_preserve_flags(
    cli_runner, mock_client, mock_nas_sync, mock_nas_service, mock_nas_volume
):
    """vrg nas sync create with --no-preserve-acls, --no-copy-symlinks."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.volume_syncs.create.return_value = mock_nas_sync

    src_vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    dst_vol_key = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5"

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "sync",
            "create",
            "--name",
            "daily-backup",
            "--service",
            "nas01",
            "--source-volume",
            src_vol_key,
            "--dest-volume",
            dst_vol_key,
            "--no-preserve-acls",
            "--no-copy-symlinks",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.volume_syncs.create.assert_called_once_with(
        name="daily-backup",
        service=1,
        source_volume=src_vol_key,
        destination_volume=dst_vol_key,
        sync_method="ysync",
        destination_delete="never",
        workers=4,
        preserve_acls=False,
        preserve_permissions=True,
        preserve_owner=True,
        preserve_groups=True,
        preserve_mod_time=True,
        preserve_xattrs=True,
        copy_symlinks=False,
        freeze_filesystem=False,
    )


def test_sync_update(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync update should update workers and dest-delete."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "sync",
            "update",
            "daily-backup",
            "--workers",
            "8",
            "--dest-delete",
            "delete-after",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.volume_syncs.update.assert_called_once_with(
        "aabb001122334455667788990011223344556677",
        workers=8,
        destination_delete="delete-after",
    )


def test_sync_delete(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync delete should delete with --yes."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "delete", "daily-backup", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.volume_syncs.delete.assert_called_once_with(
        "aabb001122334455667788990011223344556677"
    )


def test_sync_enable(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync enable should enable a sync job."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "enable", "daily-backup"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.volume_syncs.enable.assert_called_once_with(
        "aabb001122334455667788990011223344556677"
    )


def test_sync_disable(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync disable should disable a sync job."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "disable", "daily-backup"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.volume_syncs.disable.assert_called_once_with(
        "aabb001122334455667788990011223344556677"
    )


def test_sync_start(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync start should start a sync job."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "start", "daily-backup"])

    assert result.exit_code == 0
    assert "Started" in result.output
    mock_client.volume_syncs.start.assert_called_once_with(
        "aabb001122334455667788990011223344556677"
    )


def test_sync_stop(cli_runner, mock_client, mock_nas_sync):
    """vrg nas sync stop should stop a running sync job."""
    mock_client.volume_syncs.list.return_value = [mock_nas_sync]

    result = cli_runner.invoke(app, ["nas", "sync", "stop", "daily-backup"])

    assert result.exit_code == 0
    assert "Stopped" in result.output
    mock_client.volume_syncs.stop.assert_called_once_with(
        "aabb001122334455667788990011223344556677"
    )


def test_sync_not_found(cli_runner, mock_client):
    """vrg nas sync get should exit 6 for unknown sync."""
    mock_client.volume_syncs.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "sync", "get", "nonexistent"])

    assert result.exit_code == 6
