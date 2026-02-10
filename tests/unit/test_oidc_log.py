"""Tests for OIDC application log commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_oidc_log_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """List logs for an OIDC application."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.list.return_value = [mock_oidc_log]
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "list", "grafana"])

    assert result.exit_code == 0
    assert "authenticated" in result.output
    mock_client.oidc_applications.logs.assert_called_once_with(80)
    mock_logs_mgr.list.assert_called_once_with(limit=50)


def test_oidc_log_list_errors(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """List error logs with --errors flag."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.list_errors.return_value = [mock_oidc_log]
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "list", "grafana", "--errors"])

    assert result.exit_code == 0
    mock_logs_mgr.list_errors.assert_called_once_with(limit=50)


def test_oidc_log_list_warnings(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """List warning logs with --warnings flag."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.list_warnings.return_value = [mock_oidc_log]
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "list", "grafana", "--warnings"])

    assert result.exit_code == 0
    mock_logs_mgr.list_warnings.assert_called_once_with(limit=50)


def test_oidc_log_list_by_level(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """List logs filtered by --level audit."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.list_audits.return_value = [mock_oidc_log]
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "list", "grafana", "--level", "audit"])

    assert result.exit_code == 0
    mock_logs_mgr.list_audits.assert_called_once_with(limit=50)


def test_oidc_log_list_limit(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """List logs with --limit."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.list.return_value = [mock_oidc_log]
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "list", "grafana", "--limit", "10"])

    assert result.exit_code == 0
    mock_logs_mgr.list.assert_called_once_with(limit=10)


def test_oidc_log_get(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_oidc_app: MagicMock,
    mock_oidc_log: MagicMock,
) -> None:
    """Get a specific log entry."""
    mock_client.oidc_applications.get.return_value = mock_oidc_app
    mock_logs_mgr = MagicMock()
    mock_logs_mgr.get.return_value = mock_oidc_log
    mock_client.oidc_applications.logs.return_value = mock_logs_mgr

    result = cli_runner.invoke(app, ["oidc", "log", "get", "grafana", "1000"])

    assert result.exit_code == 0
    assert "authenticated" in result.output
    mock_logs_mgr.get.assert_called_once_with(key=1000)
