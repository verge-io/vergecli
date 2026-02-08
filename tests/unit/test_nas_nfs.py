"""Tests for NAS NFS share management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_nfs_list(cli_runner, mock_client, mock_nfs_share):
    """vrg nas nfs list should list all NFS shares."""
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]

    result = cli_runner.invoke(app, ["nas", "nfs", "list"])

    assert result.exit_code == 0
    assert "linuxapps" in result.output
    mock_client.nfs_shares.list.assert_called_once_with()


def test_nfs_list_by_volume(cli_runner, mock_client, mock_nfs_share, mock_nas_volume):
    """vrg nas nfs list --volume should filter by volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]

    result = cli_runner.invoke(app, ["nas", "nfs", "list", "--volume", "data-vol"])

    assert result.exit_code == 0
    assert "linuxapps" in result.output
    mock_client.nfs_shares.list.assert_called_once_with(
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_nfs_get(cli_runner, mock_client, mock_nfs_share):
    """vrg nas nfs get should resolve by name."""
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]
    mock_client.nfs_shares.get.return_value = mock_nfs_share

    result = cli_runner.invoke(app, ["nas", "nfs", "get", "linuxapps"])

    assert result.exit_code == 0
    assert "linuxapps" in result.output


def test_nfs_create(cli_runner, mock_client, mock_nfs_share, mock_nas_volume):
    """vrg nas nfs create with --allowed-hosts."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.nfs_shares.create.return_value = mock_nfs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "nfs",
            "create",
            "--name",
            "linuxapps",
            "--volume",
            "data-vol",
            "--allowed-hosts",
            "10.0.0.0/24,192.168.1.0/24",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nfs_shares.create.assert_called_once_with(
        name="linuxapps",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        allowed_hosts="10.0.0.0/24,192.168.1.0/24",
    )


def test_nfs_create_allow_all(cli_runner, mock_client, mock_nfs_share, mock_nas_volume):
    """vrg nas nfs create with --allow-all."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.nfs_shares.create.return_value = mock_nfs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "nfs",
            "create",
            "--name",
            "linuxapps",
            "--volume",
            "data-vol",
            "--allow-all",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nfs_shares.create.assert_called_once_with(
        name="linuxapps",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        allow_all=True,
    )


def test_nfs_create_with_squash(cli_runner, mock_client, mock_nfs_share, mock_nas_volume):
    """vrg nas nfs create with --squash and --data-access options."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.nfs_shares.create.return_value = mock_nfs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "nfs",
            "create",
            "--name",
            "linuxapps",
            "--volume",
            "data-vol",
            "--allow-all",
            "--squash",
            "no_root_squash",
            "--data-access",
            "rw",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nfs_shares.create.assert_called_once_with(
        name="linuxapps",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        allow_all=True,
        squash="no_root_squash",
        data_access="rw",
    )


def test_nfs_create_requires_hosts_or_allow_all(cli_runner, mock_client, mock_nas_volume):
    """vrg nas nfs create without --allowed-hosts or --allow-all should fail."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "nfs",
            "create",
            "--name",
            "linuxapps",
            "--volume",
            "data-vol",
        ],
    )

    assert result.exit_code == 2
    mock_client.nfs_shares.create.assert_not_called()


def test_nfs_update(cli_runner, mock_client, mock_nfs_share):
    """vrg nas nfs update should update data-access and squash."""
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "nfs",
            "update",
            "linuxapps",
            "--data-access",
            "ro",
            "--squash",
            "all_squash",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.nfs_shares.update.assert_called_once_with(
        "def456abc123def456abc123def456abc123def4",
        data_access="ro",
        squash="all_squash",
    )


def test_nfs_delete(cli_runner, mock_client, mock_nfs_share):
    """vrg nas nfs delete should delete with --yes."""
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]

    result = cli_runner.invoke(app, ["nas", "nfs", "delete", "linuxapps", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.nfs_shares.delete.assert_called_once_with(
        "def456abc123def456abc123def456abc123def4"
    )


def test_nfs_enable(cli_runner, mock_client, mock_nfs_share):
    """vrg nas nfs enable should enable a share."""
    mock_client.nfs_shares.list.return_value = [mock_nfs_share]

    result = cli_runner.invoke(app, ["nas", "nfs", "enable", "linuxapps"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.nfs_shares.enable.assert_called_once_with(
        "def456abc123def456abc123def456abc123def4"
    )


def test_nfs_not_found(cli_runner, mock_client):
    """vrg nas nfs get with unknown name should exit 6."""
    mock_client.nfs_shares.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "nfs", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
