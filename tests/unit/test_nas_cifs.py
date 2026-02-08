"""Tests for NAS CIFS share management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_cifs_list(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs list should list all CIFS shares."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "list"])

    assert result.exit_code == 0
    assert "users" in result.output
    mock_client.cifs_shares.list.assert_called_once_with()


def test_cifs_list_by_volume(cli_runner, mock_client, mock_cifs_share, mock_nas_volume):
    """vrg nas cifs list --volume should filter by volume."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "list", "--volume", "data-vol"])

    assert result.exit_code == 0
    assert "users" in result.output
    mock_client.cifs_shares.list.assert_called_once_with(
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )


def test_cifs_get(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs get should resolve by name."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]
    mock_client.cifs_shares.get.return_value = mock_cifs_share

    result = cli_runner.invoke(app, ["nas", "cifs", "get", "users"])

    assert result.exit_code == 0
    assert "users" in result.output


def test_cifs_get_by_hex_key(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs get should accept 40-char hex key directly."""
    mock_client.cifs_shares.get.return_value = mock_cifs_share
    hex_key = "abc123def456abc123def456abc123def456abc1"

    result = cli_runner.invoke(app, ["nas", "cifs", "get", hex_key])

    assert result.exit_code == 0
    assert "users" in result.output
    mock_client.cifs_shares.get.assert_called_once_with(key=hex_key)


def test_cifs_create(cli_runner, mock_client, mock_cifs_share, mock_nas_volume):
    """vrg nas cifs create should create with required args."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.cifs_shares.create.return_value = mock_cifs_share

    result = cli_runner.invoke(
        app,
        ["nas", "cifs", "create", "--name", "users", "--volume", "data-vol"],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.cifs_shares.create.assert_called_once_with(
        name="users",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    )


def test_cifs_create_with_users(cli_runner, mock_client, mock_cifs_share, mock_nas_volume):
    """vrg nas cifs create with --valid-users, --admin-users comma-separated."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.cifs_shares.create.return_value = mock_cifs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "create",
            "--name",
            "users",
            "--volume",
            "data-vol",
            "--valid-users",
            "alice,bob",
            "--admin-users",
            "admin",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.cifs_shares.create.assert_called_once_with(
        name="users",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        valid_users=["alice", "bob"],
        admin_users=["admin"],
    )


def test_cifs_create_with_shadow_copy(cli_runner, mock_client, mock_cifs_share, mock_nas_volume):
    """vrg nas cifs create with --shadow-copy."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.cifs_shares.create.return_value = mock_cifs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "create",
            "--name",
            "users",
            "--volume",
            "data-vol",
            "--shadow-copy",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.cifs_shares.create.assert_called_once_with(
        name="users",
        volume="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        shadow_copy=True,
    )


def test_cifs_update(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs update should update description and read-only."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "update",
            "users",
            "--description",
            "Updated desc",
            "--read-only",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.cifs_shares.update.assert_called_once_with(
        "abc123def456abc123def456abc123def456abc1",
        description="Updated desc",
        read_only=True,
    )


def test_cifs_delete(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs delete should delete with --yes."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "delete", "users", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.cifs_shares.delete.assert_called_once_with(
        "abc123def456abc123def456abc123def456abc1"
    )


def test_cifs_enable(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs enable should enable a share."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "enable", "users"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.cifs_shares.enable.assert_called_once_with(
        "abc123def456abc123def456abc123def456abc1"
    )
