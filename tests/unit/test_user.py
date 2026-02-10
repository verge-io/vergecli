"""Tests for user commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_user_list(cli_runner, mock_client, mock_user):
    """List users, default output."""
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["user", "list"])

    assert result.exit_code == 0
    assert "admin" in result.output
    mock_client.users.list.assert_called_once()


def test_user_list_enabled(cli_runner, mock_client, mock_user):
    """--enabled flag filters."""
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["user", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.users.list.assert_called_once_with(enabled=True)


def test_user_list_disabled(cli_runner, mock_client, mock_user):
    """--disabled flag filters."""
    mock_client.users.list.return_value = []

    result = cli_runner.invoke(app, ["user", "list", "--disabled"])

    assert result.exit_code == 0
    mock_client.users.list.assert_called_once_with(enabled=False)


def test_user_list_by_type(cli_runner, mock_client, mock_user):
    """--type api filter."""
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["user", "list", "--type", "api"])

    assert result.exit_code == 0
    mock_client.users.list.assert_called_once_with(user_type="api")


def test_user_get(cli_runner, mock_client, mock_user):
    """Get user by name resolution."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.get.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "get", "admin"])

    assert result.exit_code == 0
    assert "admin" in result.output


def test_user_get_by_key(cli_runner, mock_client, mock_user):
    """Get user by numeric key."""
    mock_client.users.list.return_value = []
    mock_client.users.get.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "get", "10"])

    assert result.exit_code == 0
    assert "admin" in result.output
    mock_client.users.get.assert_called_with(10)


def test_user_create(cli_runner, mock_client, mock_user):
    """Basic create with name + password."""
    mock_client.users.create.return_value = mock_user

    result = cli_runner.invoke(
        app, ["user", "create", "--name", "admin", "--password", "secret123"]
    )

    assert result.exit_code == 0
    assert "Created user" in result.output
    mock_client.users.create.assert_called_once()
    call_kwargs = mock_client.users.create.call_args[1]
    assert call_kwargs["name"] == "admin"
    assert call_kwargs["password"] == "secret123"


def test_user_create_with_options(cli_runner, mock_client, mock_user):
    """Create with all optional flags."""
    mock_client.users.create.return_value = mock_user

    result = cli_runner.invoke(
        app,
        [
            "user",
            "create",
            "--name",
            "admin",
            "--password",
            "secret123",
            "--displayname",
            "Administrator",
            "--email",
            "admin@example.com",
            "--type",
            "normal",
            "--change-password",
            "--physical-access",
            "--two-factor",
            "--two-factor-type",
            "email",
            "--ssh-keys",
            "ssh-rsa AAAA...",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.users.create.call_args[1]
    assert call_kwargs["displayname"] == "Administrator"
    assert call_kwargs["email"] == "admin@example.com"
    assert call_kwargs["user_type"] == "normal"
    assert call_kwargs["change_password"] is True
    assert call_kwargs["physical_access"] is True
    assert call_kwargs["two_factor_enabled"] is True
    assert call_kwargs["two_factor_type"] == "email"
    assert call_kwargs["ssh_keys"] == "ssh-rsa AAAA..."


def test_user_update(cli_runner, mock_client, mock_user):
    """Update displayname, email."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.update.return_value = mock_user

    result = cli_runner.invoke(
        app,
        [
            "user",
            "update",
            "admin",
            "--displayname",
            "New Name",
            "--email",
            "new@example.com",
        ],
    )

    assert result.exit_code == 0
    assert "Updated user" in result.output
    mock_client.users.update.assert_called_once()
    call_kwargs = mock_client.users.update.call_args
    assert call_kwargs[0][0] == 10  # key
    assert call_kwargs[1]["displayname"] == "New Name"
    assert call_kwargs[1]["email"] == "new@example.com"


def test_user_delete(cli_runner, mock_client, mock_user):
    """Delete with --yes."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.get.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "delete", "admin", "--yes"])

    assert result.exit_code == 0
    assert "Deleted user" in result.output
    mock_client.users.delete.assert_called_once_with(10)


def test_user_delete_no_confirm(cli_runner, mock_client, mock_user):
    """Delete without --yes aborts."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.get.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "delete", "admin"], input="n\n")

    assert result.exit_code == 0
    mock_client.users.delete.assert_not_called()


def test_user_enable(cli_runner, mock_client, mock_user):
    """Enable a disabled user."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.enable.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "enable", "admin"])

    assert result.exit_code == 0
    assert "Enabled user" in result.output
    mock_client.users.enable.assert_called_once_with(10)


def test_user_disable(cli_runner, mock_client, mock_user):
    """Disable an enabled user."""
    mock_client.users.list.return_value = [mock_user]
    mock_client.users.disable.return_value = mock_user

    result = cli_runner.invoke(app, ["user", "disable", "admin"])

    assert result.exit_code == 0
    assert "Disabled user" in result.output
    mock_client.users.disable.assert_called_once_with(10)


def test_user_not_found(cli_runner, mock_client):
    """Name resolution error (exit 6)."""
    mock_client.users.list.return_value = []

    result = cli_runner.invoke(app, ["user", "get", "nonexistent"])

    assert result.exit_code == 6
