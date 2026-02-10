"""Tests for group commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_group_list(cli_runner, mock_client, mock_group):
    """List groups."""
    mock_client.groups.list.return_value = [mock_group]

    result = cli_runner.invoke(app, ["group", "list"])

    assert result.exit_code == 0
    assert "admins" in result.output
    mock_client.groups.list.assert_called_once()


def test_group_list_enabled(cli_runner, mock_client, mock_group):
    """--enabled filter."""
    mock_client.groups.list.return_value = [mock_group]

    result = cli_runner.invoke(app, ["group", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.groups.list.assert_called_once_with(enabled=True)


def test_group_get(cli_runner, mock_client, mock_group):
    """Get group by name."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.groups.get.return_value = mock_group

    result = cli_runner.invoke(app, ["group", "get", "admins"])

    assert result.exit_code == 0
    assert "admins" in result.output


def test_group_create(cli_runner, mock_client, mock_group):
    """Basic create."""
    mock_client.groups.create.return_value = mock_group

    result = cli_runner.invoke(app, ["group", "create", "--name", "admins"])

    assert result.exit_code == 0
    assert "Created group" in result.output
    mock_client.groups.create.assert_called_once()
    call_kwargs = mock_client.groups.create.call_args[1]
    assert call_kwargs["name"] == "admins"
    assert call_kwargs["enabled"] is True


def test_group_create_with_options(cli_runner, mock_client, mock_group):
    """Create with all optional flags."""
    mock_client.groups.create.return_value = mock_group

    result = cli_runner.invoke(
        app,
        [
            "group",
            "create",
            "--name",
            "admins",
            "--description",
            "Admin group",
            "--email",
            "admins@example.com",
            "--disabled",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.groups.create.call_args[1]
    assert call_kwargs["name"] == "admins"
    assert call_kwargs["description"] == "Admin group"
    assert call_kwargs["email"] == "admins@example.com"
    assert call_kwargs["enabled"] is False


def test_group_update(cli_runner, mock_client, mock_group):
    """Update name, description."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.groups.update.return_value = mock_group

    result = cli_runner.invoke(
        app,
        [
            "group",
            "update",
            "admins",
            "--name",
            "super-admins",
            "--description",
            "Super admin group",
        ],
    )

    assert result.exit_code == 0
    assert "Updated group" in result.output
    mock_client.groups.update.assert_called_once()
    call_kwargs = mock_client.groups.update.call_args
    assert call_kwargs[0][0] == 20  # key
    assert call_kwargs[1]["name"] == "super-admins"
    assert call_kwargs[1]["description"] == "Super admin group"


def test_group_delete(cli_runner, mock_client, mock_group):
    """Delete with --yes."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.groups.get.return_value = mock_group

    result = cli_runner.invoke(app, ["group", "delete", "admins", "--yes"])

    assert result.exit_code == 0
    assert "Deleted group" in result.output
    mock_client.groups.delete.assert_called_once_with(20)


def test_group_enable(cli_runner, mock_client, mock_group):
    """Enable group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.groups.enable.return_value = mock_group

    result = cli_runner.invoke(app, ["group", "enable", "admins"])

    assert result.exit_code == 0
    assert "Enabled group" in result.output
    mock_client.groups.enable.assert_called_once_with(20)


def test_group_disable(cli_runner, mock_client, mock_group):
    """Disable group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.groups.disable.return_value = mock_group

    result = cli_runner.invoke(app, ["group", "disable", "admins"])

    assert result.exit_code == 0
    assert "Disabled group" in result.output
    mock_client.groups.disable.assert_called_once_with(20)


def test_group_member_list(cli_runner, mock_client, mock_group, mock_group_member):
    """List members of a group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_member_mgr = MagicMock()
    mock_member_mgr.list.return_value = [mock_group_member]
    mock_client.groups.members.return_value = mock_member_mgr

    result = cli_runner.invoke(app, ["group", "member", "list", "admins"])

    assert result.exit_code == 0
    assert "admin" in result.output
    mock_client.groups.members.assert_called_once_with(20)


def test_group_member_add_user(cli_runner, mock_client, mock_group, mock_user, mock_group_member):
    """Add user to group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.users.list.return_value = [mock_user]
    mock_member_mgr = MagicMock()
    mock_member_mgr.add_user.return_value = mock_group_member
    mock_client.groups.members.return_value = mock_member_mgr

    result = cli_runner.invoke(app, ["group", "member", "add", "admins", "--user", "admin"])

    assert result.exit_code == 0
    assert "Added user" in result.output
    mock_member_mgr.add_user.assert_called_once_with(10)


def test_group_member_add_group(cli_runner, mock_client, mock_group, mock_group_member):
    """Add nested group."""
    # We need two groups: parent and member
    child_group = MagicMock()
    child_group.key = 21
    child_group.name = "developers"
    child_group.is_enabled = True

    def child_get(key, default=None):
        data = {
            "description": "Dev group",
            "email": "devs@example.com",
            "member_count": 5,
            "created": 1707000000,
        }
        return data.get(key, default)

    child_group.get = child_get

    mock_client.groups.list.return_value = [mock_group, child_group]
    mock_member_mgr = MagicMock()
    member_obj = MagicMock()
    member_obj.member_name = "developers"
    member_obj.member_type = "Group"
    member_obj.member_key = 21
    mock_member_mgr.add_group.return_value = member_obj
    mock_client.groups.members.return_value = mock_member_mgr

    result = cli_runner.invoke(app, ["group", "member", "add", "admins", "--group", "developers"])

    assert result.exit_code == 0
    assert "Added group" in result.output
    mock_member_mgr.add_group.assert_called_once_with(21)


def test_group_member_remove_user(cli_runner, mock_client, mock_group, mock_user):
    """Remove user from group."""
    mock_client.groups.list.return_value = [mock_group]
    mock_client.users.list.return_value = [mock_user]
    mock_member_mgr = MagicMock()
    mock_client.groups.members.return_value = mock_member_mgr

    result = cli_runner.invoke(app, ["group", "member", "remove", "admins", "--user", "admin"])

    assert result.exit_code == 0
    assert "Removed user" in result.output
    mock_member_mgr.remove_user.assert_called_once_with(10)


def test_group_member_remove_group(cli_runner, mock_client, mock_group):
    """Remove nested group."""
    child_group = MagicMock()
    child_group.key = 21
    child_group.name = "developers"
    child_group.is_enabled = True

    def child_get(key, default=None):
        return {"description": "Dev", "email": "", "member_count": 0, "created": 0}.get(
            key, default
        )

    child_group.get = child_get

    mock_client.groups.list.return_value = [mock_group, child_group]
    mock_member_mgr = MagicMock()
    mock_client.groups.members.return_value = mock_member_mgr

    result = cli_runner.invoke(
        app, ["group", "member", "remove", "admins", "--group", "developers"]
    )

    assert result.exit_code == 0
    assert "Removed group" in result.output
    mock_member_mgr.remove_group.assert_called_once_with(21)


def test_group_not_found(cli_runner, mock_client):
    """Name resolution error (exit 6)."""
    mock_client.groups.list.return_value = []

    result = cli_runner.invoke(app, ["group", "get", "nonexistent"])

    assert result.exit_code == 6
