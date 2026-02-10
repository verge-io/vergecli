"""Tests for OIDC application management commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from pyvergeos.exceptions import NotFoundError
from typer.testing import CliRunner

from verge_cli.cli import app


def test_oidc_list(cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock) -> None:
    """List OIDC applications."""
    mock_client.oidc_applications.list.return_value = [mock_oidc_app]

    result = cli_runner.invoke(app, ["oidc", "list"])

    assert result.exit_code == 0
    assert "grafana" in result.output
    mock_client.oidc_applications.list.assert_called_once()


def test_oidc_list_enabled(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """List enabled OIDC applications."""
    mock_client.oidc_applications.list.return_value = [mock_oidc_app]

    result = cli_runner.invoke(app, ["oidc", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.oidc_applications.list.assert_called_once_with(enabled=True)


def test_oidc_list_disabled(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """List disabled OIDC applications."""
    mock_client.oidc_applications.list.return_value = [mock_oidc_app]

    result = cli_runner.invoke(app, ["oidc", "list", "--disabled"])

    assert result.exit_code == 0
    mock_client.oidc_applications.list.assert_called_once_with(enabled=False)


def test_oidc_list_enabled_disabled_exclusive(
    cli_runner: CliRunner, mock_client: MagicMock
) -> None:
    """--enabled and --disabled are mutually exclusive."""
    result = cli_runner.invoke(app, ["oidc", "list", "--enabled", "--disabled"])

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_oidc_get(cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock) -> None:
    """Get OIDC application by name."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "get", "grafana"])

    assert result.exit_code == 0
    assert "grafana" in result.output
    mock_client.oidc_applications.get.assert_called_once_with(
        name="grafana", include_secret=False, include_well_known=False
    )


def test_oidc_get_by_key(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Get OIDC application by numeric key."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "get", "80"])

    assert result.exit_code == 0
    assert "grafana" in result.output
    mock_client.oidc_applications.get.assert_called_once_with(
        key=80, include_secret=False, include_well_known=False
    )


def test_oidc_get_show_secret(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """--show-secret includes client_secret in output."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "get", "grafana", "--show-secret"])

    assert result.exit_code == 0
    assert "oidc_secret_xyz789" in result.output
    mock_client.oidc_applications.get.assert_called_once_with(
        name="grafana", include_secret=True, include_well_known=False
    )


def test_oidc_get_show_well_known(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """--show-well-known includes well-known configuration URL."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "get", "grafana", "--show-well-known"])

    assert result.exit_code == 0
    assert ".well-known" in result.output
    mock_client.oidc_applications.get.assert_called_once_with(
        name="grafana", include_secret=False, include_well_known=True
    )


def test_oidc_create(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Basic OIDC application create, verify client_id/secret in output."""
    mock_client.oidc_applications.create.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "create", "--name", "grafana"])

    assert result.exit_code == 0
    assert "Created OIDC application" in result.output
    assert "oidc_abc123" in result.output  # client_id
    assert "oidc_secret_xyz789" in result.output  # client_secret shown on create
    mock_client.oidc_applications.create.assert_called_once_with(name="grafana", enabled=True)


def test_oidc_create_with_options(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Create with all optional flags."""
    mock_client.oidc_applications.create.return_value = mock_oidc_app

    result = cli_runner.invoke(
        app,
        [
            "oidc",
            "create",
            "--name",
            "my-app",
            "--description",
            "Test app",
            "--disabled",
            "--restrict-access",
        ],
    )

    assert result.exit_code == 0
    mock_client.oidc_applications.create.assert_called_once_with(
        name="my-app",
        enabled=False,
        description="Test app",
        restrict_access=True,
    )


def test_oidc_create_redirect_uris(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Comma-separated redirect URIs."""
    mock_client.oidc_applications.create.return_value = mock_oidc_app

    result = cli_runner.invoke(
        app,
        [
            "oidc",
            "create",
            "--name",
            "my-app",
            "--redirect-uri",
            "https://a.example.com/cb,https://b.example.com/cb",
        ],
    )

    assert result.exit_code == 0
    mock_client.oidc_applications.create.assert_called_once_with(
        name="my-app",
        enabled=True,
        redirect_uri=["https://a.example.com/cb", "https://b.example.com/cb"],
    )


def test_oidc_create_scopes(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Custom scope flags."""
    mock_client.oidc_applications.create.return_value = mock_oidc_app

    result = cli_runner.invoke(
        app,
        [
            "oidc",
            "create",
            "--name",
            "my-app",
            "--no-scope-groups",
            "--scope-profile",
        ],
    )

    assert result.exit_code == 0
    mock_client.oidc_applications.create.assert_called_once_with(
        name="my-app",
        enabled=True,
        scope_groups=False,
        scope_profile=True,
    )


def test_oidc_update(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Update name and description."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_client.oidc_applications.update.return_value = mock_oidc_app

    result = cli_runner.invoke(
        app,
        ["oidc", "update", "80", "--name", "grafana-v2", "--description", "Updated"],
    )

    assert result.exit_code == 0
    assert "Updated OIDC application" in result.output
    mock_client.oidc_applications.update.assert_called_once_with(
        80, name="grafana-v2", description="Updated"
    )


def test_oidc_update_scopes(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Update scope flags."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_client.oidc_applications.update.return_value = mock_oidc_app

    result = cli_runner.invoke(
        app,
        ["oidc", "update", "80", "--no-scope-groups", "--scope-email"],
    )

    assert result.exit_code == 0
    mock_client.oidc_applications.update.assert_called_once_with(
        80, scope_groups=False, scope_email=True
    )


def test_oidc_delete(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Delete with --yes."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "delete", "80", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.oidc_applications.delete.assert_called_once_with(80)


def test_oidc_delete_no_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Delete without --yes aborts."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "delete", "80"], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_client.oidc_applications.delete.assert_not_called()


def test_oidc_enable(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Enable an OIDC application."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "enable", "80"])

    assert result.exit_code == 0
    assert "Enabled" in result.output
    mock_oidc_app.enable.assert_called_once()


def test_oidc_disable(
    cli_runner: CliRunner, mock_client: MagicMock, mock_oidc_app: MagicMock
) -> None:
    """Disable an OIDC application."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app

    result = cli_runner.invoke(app, ["oidc", "disable", "80"])

    assert result.exit_code == 0
    assert "Disabled" in result.output
    mock_oidc_app.disable.assert_called_once()


def test_oidc_not_found(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Name resolution error (exit 6)."""
    mock_client.oidc_applications.get.side_effect = NotFoundError("Not found")

    result = cli_runner.invoke(app, ["oidc", "get", "nonexistent"])

    assert result.exit_code == 6
