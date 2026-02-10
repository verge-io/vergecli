"""Tests for update log commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestUpdateLogList:
    """Tests for vrg update log list."""

    def test_update_log_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_log: MagicMock,
    ) -> None:
        """List update logs."""
        mock_client.update_logs.list.return_value = [mock_update_log]

        result = cli_runner.invoke(app, ["update", "log", "list"])

        assert result.exit_code == 0
        assert "Update check completed" in result.output
        mock_client.update_logs.list.assert_called_once()

    def test_update_log_list_by_level(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_log: MagicMock,
    ) -> None:
        """List logs filtered by level."""
        mock_client.update_logs.list.return_value = [mock_update_log]

        result = cli_runner.invoke(
            app,
            ["update", "log", "list", "--level", "error"],
        )

        assert result.exit_code == 0
        mock_client.update_logs.list.assert_called_once_with(level="error")


class TestUpdateLogGet:
    """Tests for vrg update log get."""

    def test_update_log_get(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_log: MagicMock,
    ) -> None:
        """Get a single log entry."""
        mock_client.update_logs.get.return_value = mock_update_log

        result = cli_runner.invoke(app, ["update", "log", "get", "500"])

        assert result.exit_code == 0
        assert "Update check completed" in result.output
        mock_client.update_logs.get.assert_called_once_with(key=500)
