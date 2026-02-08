"""Tests for NAS local user management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_user_list(cli_runner, mock_client, mock_nas_user):
    """vrg nas user list should list all NAS users."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "list"])

    assert result.exit_code == 0
    assert "nasadmin" in result.output
    mock_client.nas_users.list.assert_called_once_with()


def test_user_list_by_service(cli_runner, mock_client, mock_nas_user, mock_nas_service):
    """vrg nas user list --service should filter by service."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "list", "--service", "nas01"])

    assert result.exit_code == 0
    assert "nasadmin" in result.output
    mock_client.nas_users.list.assert_called_once_with(service=1)


def test_user_list_enabled(cli_runner, mock_client, mock_nas_user):
    """vrg nas user list --enabled should filter by enabled state."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "list", "--enabled"])

    assert result.exit_code == 0
    assert "nasadmin" in result.output
    mock_client.nas_users.list.assert_called_once_with(enabled=True)


def test_user_get(cli_runner, mock_client, mock_nas_user):
    """vrg nas user get should resolve by name."""
    mock_client.nas_users.list.return_value = [mock_nas_user]
    mock_client.nas_users.get.return_value = mock_nas_user

    result = cli_runner.invoke(app, ["nas", "user", "get", "nasadmin"])

    assert result.exit_code == 0
    assert "nasadmin" in result.output


def test_user_get_by_hex_key(cli_runner, mock_client, mock_nas_user):
    """vrg nas user get should accept 40-char hex key directly."""
    mock_client.nas_users.get.return_value = mock_nas_user
    hex_key = "aabbccdd11223344556677889900aabbccdd1122"

    result = cli_runner.invoke(app, ["nas", "user", "get", hex_key])

    assert result.exit_code == 0
    assert "nasadmin" in result.output
    mock_client.nas_users.get.assert_called_once_with(key=hex_key)


def test_user_create(cli_runner, mock_client, mock_nas_user, mock_nas_service):
    """vrg nas user create should create with required args."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_users.create.return_value = mock_nas_user

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "user",
            "create",
            "--service",
            "nas01",
            "--name",
            "nasadmin",
            "--password",
            "SecurePass123!",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_users.create.assert_called_once_with(
        service=1,
        name="nasadmin",
        password="SecurePass123!",
    )


def test_user_create_with_options(cli_runner, mock_client, mock_nas_user, mock_nas_service):
    """vrg nas user create with --displayname, --home-share, --home-drive."""
    mock_client.nas_services.list.return_value = [mock_nas_service]
    mock_client.nas_users.create.return_value = mock_nas_user

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "user",
            "create",
            "--service",
            "nas01",
            "--name",
            "nasadmin",
            "--password",
            "SecurePass123!",
            "--displayname",
            "NAS Admin",
            "--home-share",
            "AdminDocs",
            "--home-drive",
            "H",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.nas_users.create.assert_called_once_with(
        service=1,
        name="nasadmin",
        password="SecurePass123!",
        displayname="NAS Admin",
        home_share="AdminDocs",
        home_drive="H",
    )


def test_user_update(cli_runner, mock_client, mock_nas_user):
    """vrg nas user update should update password and displayname."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(
        app,
        [
            "nas",
            "user",
            "update",
            "nasadmin",
            "--password",
            "NewPass456!",
            "--displayname",
            "Updated Admin",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.nas_users.update.assert_called_once_with(
        "aabbccdd11223344556677889900aabbccdd1122",
        password="NewPass456!",
        displayname="Updated Admin",
    )


def test_user_delete(cli_runner, mock_client, mock_nas_user):
    """vrg nas user delete should delete with --yes."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "delete", "nasadmin", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.nas_users.delete.assert_called_once_with("aabbccdd11223344556677889900aabbccdd1122")


def test_user_enable(cli_runner, mock_client, mock_nas_user):
    """vrg nas user enable should enable a user."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "enable", "nasadmin"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_client.nas_users.enable.assert_called_once_with("aabbccdd11223344556677889900aabbccdd1122")


def test_user_disable(cli_runner, mock_client, mock_nas_user):
    """vrg nas user disable should disable a user."""
    mock_client.nas_users.list.return_value = [mock_nas_user]

    result = cli_runner.invoke(app, ["nas", "user", "disable", "nasadmin"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_client.nas_users.disable.assert_called_once_with(
        "aabbccdd11223344556677889900aabbccdd1122"
    )


def test_user_not_found(cli_runner, mock_client):
    """vrg nas user get should exit 6 for unknown user."""
    mock_client.nas_users.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "user", "get", "nonexistent"])

    assert result.exit_code == 6
