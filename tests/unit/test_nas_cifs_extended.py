"""Extended tests for NAS CIFS share management commands (create/update options)."""

from __future__ import annotations

from verge_cli.cli import app


def test_cifs_create_with_all_options(cli_runner, mock_client, mock_cifs_share, mock_nas_volume):
    """vrg nas cifs create with all options should pass them through."""
    mock_client.nas_volumes.list.return_value = [mock_nas_volume]
    mock_client.cifs_shares.create.return_value = mock_cifs_share

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "create",
            "--name",
            "shared",
            "--volume",
            "data-vol",
            "--share-path",
            "/exports/shared",
            "--description",
            "Shared folder",
            "--comment",
            "Public share",
            "--browseable",
            "--read-only",
            "--guest-ok",
            "--guest-only",
            "--force-user",
            "nobody",
            "--force-group",
            "nogroup",
            "--valid-users",
            "alice,bob",
            "--valid-groups",
            "devs,ops",
            "--admin-users",
            "admin",
            "--admin-groups",
            "admins",
            "--allowed-hosts",
            "10.0.0.0/24,192.168.1.0/24",
            "--denied-hosts",
            "10.0.0.99",
            "--shadow-copy",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    call_kwargs = mock_client.cifs_shares.create.call_args[1]
    assert call_kwargs["name"] == "shared"
    assert call_kwargs["share_path"] == "/exports/shared"
    assert call_kwargs["description"] == "Shared folder"
    assert call_kwargs["comment"] == "Public share"
    assert call_kwargs["browseable"] is True
    assert call_kwargs["read_only"] is True
    assert call_kwargs["guest_ok"] is True
    assert call_kwargs["guest_only"] is True
    assert call_kwargs["force_user"] == "nobody"
    assert call_kwargs["force_group"] == "nogroup"
    assert call_kwargs["valid_users"] == ["alice", "bob"]
    assert call_kwargs["valid_groups"] == ["devs", "ops"]
    assert call_kwargs["admin_users"] == ["admin"]
    assert call_kwargs["admin_groups"] == ["admins"]
    assert call_kwargs["allowed_hosts"] == ["10.0.0.0/24", "192.168.1.0/24"]
    assert call_kwargs["denied_hosts"] == ["10.0.0.99"]
    assert call_kwargs["shadow_copy"] is True


def test_cifs_update_boolean_flags(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs update with boolean flags should pass them."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "update",
            "users",
            "--browseable",
            "--guest-ok",
            "--no-read-only",
            "--shadow-copy",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.cifs_shares.update.call_args[1]
    assert call_kwargs["browseable"] is True
    assert call_kwargs["guest_ok"] is True
    assert call_kwargs["read_only"] is False
    assert call_kwargs["shadow_copy"] is True


def test_cifs_update_list_fields(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs update with comma-separated lists should split them."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "update",
            "users",
            "--valid-users",
            "alice,bob,charlie",
            "--admin-groups",
            "admins",
            "--allowed-hosts",
            "10.0.0.0/24",
            "--denied-hosts",
            "10.0.0.99,10.0.0.100",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.cifs_shares.update.call_args[1]
    assert call_kwargs["valid_users"] == ["alice", "bob", "charlie"]
    assert call_kwargs["admin_groups"] == ["admins"]
    assert call_kwargs["allowed_hosts"] == ["10.0.0.0/24"]
    assert call_kwargs["denied_hosts"] == ["10.0.0.99", "10.0.0.100"]


def test_cifs_update_force_user_group(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs update with force user/group should pass them."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "cifs",
            "update",
            "users",
            "--force-user",
            "www-data",
            "--force-group",
            "www-data",
            "--comment",
            "Updated comment",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.cifs_shares.update.call_args[1]
    assert call_kwargs["force_user"] == "www-data"
    assert call_kwargs["force_group"] == "www-data"
    assert call_kwargs["comment"] == "Updated comment"


def test_cifs_disable(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs disable should disable a share."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "disable", "users"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.cifs_shares.disable.assert_called_once_with(
        "abc123def456abc123def456abc123def456abc1"
    )


def test_cifs_delete_cancelled(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs delete without --yes should prompt and cancel on 'n'."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "delete", "users"], input="n\n")

    assert result.exit_code == 0
    mock_client.cifs_shares.delete.assert_not_called()


def test_cifs_list_with_enabled_filter(cli_runner, mock_client, mock_cifs_share):
    """vrg nas cifs list --enabled should filter by enabled state."""
    mock_client.cifs_shares.list.return_value = [mock_cifs_share]

    result = cli_runner.invoke(app, ["nas", "cifs", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.cifs_shares.list.assert_called_once_with(enabled=True)
