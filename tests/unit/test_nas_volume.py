"""Tests for NAS volume management commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from verge_cli.cli import app
from verge_cli.utils import resolve_nas_resource


def test_volume_list(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume list should list all volumes."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "list"])

    assert result.exit_code == 0
    assert "data-vol" in result.output
    mock_client.nas_volumes.list.assert_called_once_with()


def test_volume_list_by_service(cli_runner, mock_client, mock_nas_volume, mock_nas_service):
    """vrg nas volume list --service should filter by NAS service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "list", "--service", "nas01"])

    assert result.exit_code == 0
    assert "data-vol" in result.output
    mock_client.nas_volumes.list.assert_called_once_with(service=1)


def test_volume_list_by_fs_type(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume list --fs-type should filter by filesystem type."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "list", "--fs-type", "ext4"])

    assert result.exit_code == 0
    assert "data-vol" in result.output
    mock_client.nas_volumes.list.assert_called_once_with(fs_type="ext4")


def test_volume_get(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume get should resolve by name."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.nas_volumes.get.return_value = mock_nas_volume

    result = cli_runner.invoke(app, ["nas", "volume", "get", "data-vol"])

    assert result.exit_code == 0
    assert "data-vol" in result.output


def test_volume_get_by_hex_key(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume get should accept 40-char hex key directly."""
    mock_client.nas_volumes.get.return_value = mock_nas_volume
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    result = cli_runner.invoke(app, ["nas", "volume", "get", hex_key])

    assert result.exit_code == 0
    assert "data-vol" in result.output
    mock_client.nas_volumes.get.assert_called_once_with(hex_key)


def test_volume_create(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume create should create with required args."""
    mock_client.nas_volumes.create.return_value = mock_nas_volume

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "create", "--name", "data-vol", "--service", "1", "--size-gb", "50"],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_volumes.create.assert_called_once_with(
        name="data-vol",
        service=1,
        size_gb=50,
    )


def test_volume_create_with_options(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume create should accept --tier, --owner-user, --snapshot-profile."""
    mock_client.nas_volumes.create.return_value = mock_nas_volume

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "volume",
            "create",
            "--name",
            "data-vol",
            "--service",
            "1",
            "--size-gb",
            "100",
            "--tier",
            "2",
            "--owner-user",
            "admin",
            "--snapshot-profile",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_volumes.create.assert_called_once_with(
        name="data-vol",
        service=1,
        size_gb=100,
        tier=2,
        owner_user="admin",
        snapshot_profile=5,
    )


def test_volume_update(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume update should update size-gb and tier."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(
        app,
        ["nas", "volume", "update", "data-vol", "--size-gb", "100", "--tier", "3"],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.nas_volumes.update.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        size_gb=100,
        tier=3,
    )


def test_volume_delete(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume delete should remove a volume with --yes."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "delete", "data-vol", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.nas_volumes.delete.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_volume_enable(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume enable should enable a volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "enable", "data-vol"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.nas_volumes.enable.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_volume_disable(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume disable should disable a volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "disable", "data-vol"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.nas_volumes.disable.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_volume_reset(cli_runner, mock_client, mock_nas_volume):
    """vrg nas volume reset should reset an errored volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(app, ["nas", "volume", "reset", "data-vol"])

    assert result.exit_code == 0
    assert "Reset" in result.output
    mock_client.nas_volumes.reset.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_volume_not_found(cli_runner, mock_client):
    """vrg nas volume get with unknown name should exit 6."""
    mock_client.nas_volumes.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "volume", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()


def test_resolve_nas_resource_hex_key():
    """resolve_nas_resource should pass through 40-char hex keys directly."""
    mock_manager = MagicMock()
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    result = resolve_nas_resource(mock_manager, hex_key, "NAS volume")

    assert result == hex_key
    # Should NOT call list() when hex key is provided
    mock_manager.list.assert_not_called()
