"""Tests for OIDC application group ACL commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_oidc_group_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_group_entry: MagicMock,
) -> None:
    """List allowed groups for an OIDC application."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_groups_mgr = MagicMock()
    mock_groups_mgr.list.return_value = [mock_oidc_group_entry]
    mock_client.oidc_applications.allowed_groups.return_value = mock_groups_mgr

    result = cli_runner.invoke(app, ["oidc", "group", "list", "grafana"])

    assert result.exit_code == 0
    assert "admins" in result.output
    mock_client.oidc_applications.allowed_groups.assert_called_once_with(80)


def test_oidc_group_add(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_group: MagicMock,
) -> None:
    """Add group to allowed list by key."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_groups_mgr = MagicMock()
    mock_client.oidc_applications.allowed_groups.return_value = mock_groups_mgr

    result = cli_runner.invoke(app, ["oidc", "group", "add", "grafana", "20"])

    assert result.exit_code == 0
    assert "Added group" in result.output
    mock_groups_mgr.add.assert_called_once_with(group_key=20)


def test_oidc_group_add_by_name(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_group: MagicMock,
) -> None:
    """Add group to allowed list by name."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_groups_mgr = MagicMock()
    mock_client.oidc_applications.allowed_groups.return_value = mock_groups_mgr
    mock_client.groups.list.return_value = [mock_group]

    result = cli_runner.invoke(app, ["oidc", "group", "add", "grafana", "admins"])

    assert result.exit_code == 0
    assert "Added group" in result.output
    mock_groups_mgr.add.assert_called_once_with(group_key=20)


def test_oidc_group_remove(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_group: MagicMock,
    mock_oidc_group_entry: MagicMock,
) -> None:
    """Remove group from allowed list."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_groups_mgr = MagicMock()
    mock_groups_mgr.list.return_value = [mock_oidc_group_entry]
    mock_client.oidc_applications.allowed_groups.return_value = mock_groups_mgr
    mock_client.groups.list.return_value = [mock_group]

    result = cli_runner.invoke(app, ["oidc", "group", "remove", "grafana", "admins", "--yes"])

    assert result.exit_code == 0
    assert "Removed group" in result.output
    mock_groups_mgr.delete.assert_called_once_with(91)


def test_oidc_group_remove_no_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_group: MagicMock,
    mock_oidc_group_entry: MagicMock,
) -> None:
    """Remove without --yes aborts."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_groups_mgr = MagicMock()
    mock_groups_mgr.list.return_value = [mock_oidc_group_entry]
    mock_client.oidc_applications.allowed_groups.return_value = mock_groups_mgr
    mock_client.groups.list.return_value = [mock_group]

    result = cli_runner.invoke(app, ["oidc", "group", "remove", "grafana", "admins"], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_groups_mgr.delete.assert_not_called()
