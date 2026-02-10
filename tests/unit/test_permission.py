"""Tests for permission commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_permission_list(cli_runner, mock_client, mock_permission):
    """List all permissions."""
    mock_client.permissions.list.return_value = [mock_permission]

    result = cli_runner.invoke(app, ["permission", "list"])

    assert result.exit_code == 0
    assert "admin" in result.output
    assert "vms" in result.output
    mock_client.permissions.list.assert_called_once()


def test_permission_list_by_user(cli_runner, mock_client, mock_permission, mock_user):
    """--user filter resolves and passes user key."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.list.return_value = [mock_permission]

    result = cli_runner.invoke(app, ["permission", "list", "--user", "admin"])

    assert result.exit_code == 0
    mock_client.permissions.list.assert_called_once_with(user=10)


def test_permission_list_by_group(cli_runner, mock_client, mock_permission, mock_group):
    """--group filter resolves and passes group key."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.permissions.list.return_value = [mock_permission]

    result = cli_runner.invoke(app, ["permission", "list", "--group", "admins"])

    assert result.exit_code == 0
    mock_client.permissions.list.assert_called_once_with(group=20)


def test_permission_list_by_table(cli_runner, mock_client, mock_permission):
    """--table vms filter."""
    mock_client.permissions.list.return_value = [mock_permission]

    result = cli_runner.invoke(app, ["permission", "list", "--table", "vms"])

    assert result.exit_code == 0
    mock_client.permissions.list.assert_called_once_with(table="vms")


def test_permission_get(cli_runner, mock_client, mock_permission):
    """Get permission by numeric key."""
    mock_client.permissions.get.return_value = mock_permission

    result = cli_runner.invoke(app, ["permission", "get", "50"])

    assert result.exit_code == 0
    assert "admin" in result.output
    mock_client.permissions.get.assert_called_once_with(50)


def test_permission_grant_user(cli_runner, mock_client, mock_permission, mock_user):
    """Grant to user with specific flags."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.grant.return_value = mock_permission

    result = cli_runner.invoke(
        app,
        [
            "permission",
            "grant",
            "--table",
            "vms",
            "--user",
            "admin",
            "--list",
            "--read",
        ],
    )

    assert result.exit_code == 0
    assert "Granted permission" in result.output
    mock_client.permissions.grant.assert_called_once_with(
        table="vms",
        row_key=0,
        can_list=True,
        can_read=True,
        can_create=False,
        can_modify=False,
        can_delete=False,
        full_control=False,
        user=10,
    )


def test_permission_grant_group(cli_runner, mock_client, mock_permission, mock_group):
    """Grant to group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.permissions.grant.return_value = mock_permission

    result = cli_runner.invoke(
        app,
        [
            "permission",
            "grant",
            "--table",
            "vnets",
            "--group",
            "admins",
            "--list",
        ],
    )

    assert result.exit_code == 0
    mock_client.permissions.grant.assert_called_once_with(
        table="vnets",
        row_key=0,
        can_list=True,
        can_read=False,
        can_create=False,
        can_modify=False,
        can_delete=False,
        full_control=False,
        group=20,
    )


def test_permission_grant_full_control(cli_runner, mock_client, mock_permission, mock_user):
    """--full-control flag."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.grant.return_value = mock_permission

    result = cli_runner.invoke(
        app,
        [
            "permission",
            "grant",
            "--table",
            "vms",
            "--user",
            "admin",
            "--full-control",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.permissions.grant.call_args[1]
    assert call_kwargs["full_control"] is True


def test_permission_grant_specific_row(cli_runner, mock_client, mock_permission, mock_user):
    """--row 42 for specific resource."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.grant.return_value = mock_permission

    result = cli_runner.invoke(
        app,
        [
            "permission",
            "grant",
            "--table",
            "vms",
            "--user",
            "admin",
            "--row",
            "42",
            "--list",
            "--read",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.permissions.grant.call_args[1]
    assert call_kwargs["row_key"] == 42


def test_permission_grant_default_list_only(cli_runner, mock_client, mock_permission, mock_user):
    """No flags → defaults to --list only."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.grant.return_value = mock_permission

    result = cli_runner.invoke(
        app,
        [
            "permission",
            "grant",
            "--table",
            "vms",
            "--user",
            "admin",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.permissions.grant.call_args[1]
    assert call_kwargs["can_list"] is True
    assert call_kwargs["can_read"] is False


def test_permission_revoke(cli_runner, mock_client):
    """Revoke single permission with --yes."""
    result = cli_runner.invoke(app, ["permission", "revoke", "50", "--yes"])

    assert result.exit_code == 0
    assert "Revoked permission" in result.output
    mock_client.permissions.revoke.assert_called_once_with(50)


def test_permission_revoke_no_confirm(cli_runner, mock_client):
    """Revoke without --yes aborts."""
    result = cli_runner.invoke(app, ["permission", "revoke", "50"], input="n\n")

    assert result.exit_code == 0
    mock_client.permissions.revoke.assert_not_called()


def test_permission_revoke_all_user(cli_runner, mock_client, mock_user):
    """Revoke all for a user."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.permissions.revoke_for_user.return_value = 3

    result = cli_runner.invoke(app, ["permission", "revoke-all", "--user", "admin", "--yes"])

    assert result.exit_code == 0
    assert "Revoked 3 permission(s)" in result.output
    mock_client.permissions.revoke_for_user.assert_called_once_with(10, table=None)


def test_permission_revoke_all_group_table(cli_runner, mock_client, mock_group):
    """Revoke all for group on specific table."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.permissions.revoke_for_group.return_value = 2

    result = cli_runner.invoke(
        app,
        ["permission", "revoke-all", "--group", "admins", "--table", "vms", "--yes"],
    )

    assert result.exit_code == 0
    assert "Revoked 2 permission(s)" in result.output
    mock_client.permissions.revoke_for_group.assert_called_once_with(20, table="vms")
