"""Tests for NAS service management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_cifs_settings() -> MagicMock:
    """Create a mock CIFS settings object."""
    settings = MagicMock()
    settings.key = 10

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "workgroup": "WORKGROUP",
            "server_type": "default",
            "server_min_protocol": "SMB2",
            "map_to_guest": "never",
            "extended_acl_support": False,
            "ad_status": "not joined",
        }
        return data.get(key, default)

    settings.get = mock_get
    return settings


@pytest.fixture
def mock_nfs_settings() -> MagicMock:
    """Create a mock NFS settings object."""
    settings = MagicMock()
    settings.key = 20

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "enable_nfsv4": False,
            "allow_all": True,
            "allowed_hosts": "*",
            "squash": "root_squash",
            "data_access": "rw",
            "anonuid": 65534,
            "anongid": 65534,
        }
        return data.get(key, default)

    settings.get = mock_get
    return settings


def test_service_list(cli_runner, mock_client, mock_nas_service):
    """vrg nas service list should list all NAS services."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "list"])

    assert result.exit_code == 0
    assert "nas01" in result.output
    mock_client.nas_services.list.assert_called_once()


def test_service_list_running(cli_runner, mock_client, mock_nas_service):
    """vrg nas service list --status running should filter running services."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "list", "--status", "running"])

    assert result.exit_code == 0
    assert "nas01" in result.output
    mock_client.nas_services.list.assert_called_once_with(status="running")


def test_service_get(cli_runner, mock_client, mock_nas_service):
    """vrg nas service get should resolve by name."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_services.get.return_value = mock_nas_service

    result = cli_runner.invoke(app, ["nas", "service", "get", "nas01"])

    assert result.exit_code == 0
    assert "nas01" in result.output


def test_service_get_by_key(cli_runner, mock_client, mock_nas_service):
    """vrg nas service get should accept numeric key."""
    mock_client.nas_services.get.return_value = mock_nas_service

    result = cli_runner.invoke(app, ["nas", "service", "get", "1"])

    assert result.exit_code == 0
    assert "nas01" in result.output
    mock_client.nas_services.get.assert_called_once_with(1)


def test_service_create(cli_runner, mock_client, mock_nas_service):
    """vrg nas service create should create with defaults."""
    mock_client.nas_services.create.return_value = mock_nas_service

    result = cli_runner.invoke(app, ["nas", "service", "create", "--name", "nas01"])

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_services.create.assert_called_once_with(
        name="nas01",
        cores=4,
        memory_gb=8,
    )


def test_service_create_with_options(cli_runner, mock_client, mock_nas_service):
    """vrg nas service create should accept --cores, --memory-gb, --network, --hostname."""
    mock_client.nas_services.create.return_value = mock_nas_service

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "service",
            "create",
            "--name",
            "nas01",
            "--cores",
            "8",
            "--memory-gb",
            "16",
            "--network",
            "Internal",
            "--hostname",
            "mynas",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_services.create.assert_called_once_with(
        name="nas01",
        cores=8,
        memory_gb=16,
        network="Internal",
        hostname="mynas",
    )


def test_service_update(cli_runner, mock_client, mock_nas_service):
    """vrg nas service update should update max-imports, max-syncs, read-ahead-kb."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "service",
            "update",
            "nas01",
            "--max-imports",
            "5",
            "--max-syncs",
            "3",
            "--read-ahead-kb",
            "1024",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.nas_services.update.assert_called_once_with(
        1,
        max_imports=5,
        max_syncs=3,
        read_ahead_kb=1024,
    )


def test_service_delete(cli_runner, mock_client, mock_nas_service):
    """vrg nas service delete should remove a service with --yes."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "delete", "nas01", "--yes"])

    assert result.exit_code == 0
    mock_client.nas_services.delete.assert_called_once_with(1, force=False)
    assert "Deleted" in result.output


def test_service_delete_force(cli_runner, mock_client, mock_nas_service):
    """vrg nas service delete --force should force delete."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "delete", "nas01", "--force", "--yes"])

    assert result.exit_code == 0
    mock_client.nas_services.delete.assert_called_once_with(1, force=True)
    assert "Deleted" in result.output


def test_service_power_on(cli_runner, mock_client, mock_nas_service):
    """vrg nas service power-on should power on a service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "power-on", "nas01"])

    assert result.exit_code == 0
    assert "Powered on" in result.output
    mock_client.nas_services.power_on.assert_called_once_with(1)


def test_service_power_off(cli_runner, mock_client, mock_nas_service):
    """vrg nas service power-off should power off a service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "power-off", "nas01"])

    assert result.exit_code == 0
    assert "Powered off" in result.output
    mock_client.nas_services.power_off.assert_called_once_with(1, force=False)


def test_service_power_off_force(cli_runner, mock_client, mock_nas_service):
    """vrg nas service power-off --force should hard power off."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "power-off", "nas01", "--force"])

    assert result.exit_code == 0
    assert "Powered off" in result.output
    mock_client.nas_services.power_off.assert_called_once_with(1, force=True)


def test_service_restart(cli_runner, mock_client, mock_nas_service):
    """vrg nas service restart should restart a service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]

    result = cli_runner.invoke(app, ["nas", "service", "restart", "nas01"])

    assert result.exit_code == 0
    assert "Restarted" in result.output
    mock_client.nas_services.restart.assert_called_once_with(1)


def test_cifs_settings(cli_runner, mock_client, mock_nas_service, mock_cifs_settings):
    """vrg nas service cifs-settings should display CIFS settings."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_services.get_cifs_settings.return_value = mock_cifs_settings

    result = cli_runner.invoke(app, ["nas", "service", "cifs-settings", "nas01"])

    assert result.exit_code == 0
    assert "WORKGROUP" in result.output
    mock_client.nas_services.get_cifs_settings.assert_called_once_with(1)


def test_set_cifs_settings(cli_runner, mock_client, mock_nas_service, mock_cifs_settings):
    """vrg nas service set-cifs-settings should update workgroup and min-protocol."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_services.set_cifs_settings.return_value = mock_cifs_settings

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "service",
            "set-cifs-settings",
            "nas01",
            "--workgroup",
            "MYGROUP",
            "--min-protocol",
            "SMB3",
        ],
    )

    assert result.exit_code == 0
    assert "Updated CIFS" in result.output
    mock_client.nas_services.set_cifs_settings.assert_called_once_with(
        1,
        workgroup="MYGROUP",
        min_protocol="SMB3",
    )


def test_nfs_settings(cli_runner, mock_client, mock_nas_service, mock_nfs_settings):
    """vrg nas service nfs-settings should display NFS settings."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_services.get_nfs_settings.return_value = mock_nfs_settings

    result = cli_runner.invoke(app, ["nas", "service", "nfs-settings", "nas01"])

    assert result.exit_code == 0
    assert "root_squash" in result.output
    mock_client.nas_services.get_nfs_settings.assert_called_once_with(1)


def test_set_nfs_settings(cli_runner, mock_client, mock_nas_service, mock_nfs_settings):
    """vrg nas service set-nfs-settings should update squash, data-access, allowed-hosts."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_services.set_nfs_settings.return_value = mock_nfs_settings

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "service",
            "set-nfs-settings",
            "nas01",
            "--squash",
            "all_squash",
            "--data-access",
            "ro",
            "--allowed-hosts",
            "192.168.1.0/24",
        ],
    )

    assert result.exit_code == 0
    assert "Updated NFS" in result.output
    mock_client.nas_services.set_nfs_settings.assert_called_once_with(
        1,
        squash="all_squash",
        data_access="ro",
        allowed_hosts="192.168.1.0/24",
    )


def test_service_not_found(cli_runner, mock_client):
    """vrg nas service get with unknown name should exit 6."""
    mock_client.nas_services.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "service", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
