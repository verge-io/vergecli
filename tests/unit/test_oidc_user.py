"""Tests for OIDC application user ACL commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from pyvergeos.exceptions import NotFoundError
from typer.testing import CliRunner

from verge_cli.cli import app


def test_oidc_user_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_user_entry: MagicMock,
) -> None:
    """List allowed users for an OIDC application."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_users_mgr.list.return_value = [mock_oidc_user_entry]
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr

    result = cli_runner.invoke(app, ["oidc", "user", "list", "grafana"])

    assert result.exit_code == 0
    assert "admin" in result.output
    mock_client.oidc_applications.allowed_users.assert_called_once_with(80)


def test_oidc_user_list_empty(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
) -> None:
    """List allowed users when ACL is empty."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_users_mgr.list.return_value = []
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr

    result = cli_runner.invoke(app, ["oidc", "user", "list", "80"])

    assert result.exit_code == 0


def test_oidc_user_add(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_user: MagicMock,
) -> None:
    """Add user to allowed list by key."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr

    # resolve_resource_id with numeric key
    result = cli_runner.invoke(app, ["oidc", "user", "add", "grafana", "10"])

    assert result.exit_code == 0
    assert "Added user" in result.output
    mock_users_mgr.add.assert_called_once_with(user_key=10)


def test_oidc_user_add_by_name(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_user: MagicMock,
) -> None:
    """Add user to allowed list by name."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr

    # resolve_resource_id for name resolution
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["oidc", "user", "add", "grafana", "admin"])

    assert result.exit_code == 0
    assert "Added user" in result.output
    mock_users_mgr.add.assert_called_once_with(user_key=10)


def test_oidc_user_remove(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_user: MagicMock,
    mock_oidc_user_entry: MagicMock,
) -> None:
    """Remove user from allowed list by name."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_users_mgr.list.return_value = [mock_oidc_user_entry]
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["oidc", "user", "remove", "grafana", "admin", "--yes"])

    assert result.exit_code == 0
    assert "Removed user" in result.output
    mock_users_mgr.delete.assert_called_once_with(90)


def test_oidc_user_remove_by_entry_key(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_user_entry: MagicMock,
) -> None:
    """Remove user from allowed list by numeric key (user key match)."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    # Entry has user=10, so passing "10" should find it
    mock_users_mgr.list.return_value = [mock_oidc_user_entry]
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr

    result = cli_runner.invoke(app, ["oidc", "user", "remove", "grafana", "10", "--yes"])

    assert result.exit_code == 0
    assert "Removed user" in result.output
    mock_users_mgr.delete.assert_called_once_with(90)


def test_oidc_user_remove_no_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_user: MagicMock,
    mock_oidc_user_entry: MagicMock,
) -> None:
    """Remove without --yes aborts."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_users_mgr = MagicMock()
    mock_users_mgr.list.return_value = [mock_oidc_user_entry]
    mock_client.oidc_applications.allowed_users.return_value = mock_users_mgr
    mock_client.users.list.return_value = [mock_user]

    result = cli_runner.invoke(app, ["oidc", "user", "remove", "grafana", "admin"], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_users_mgr.delete.assert_not_called()


def test_oidc_user_app_not_found(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Parent app resolution error (exit 6)."""
    mock_client.oidc_applications.get.side_effect = NotFoundError("not found")

    result = cli_runner.invoke(app, ["oidc", "user", "list", "nonexistent"])

    assert result.exit_code == 6
