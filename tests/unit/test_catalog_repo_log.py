"""Tests for catalog repository log commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestCatalogRepoLogList:
    """Tests for vrg catalog repo log list."""

    def test_repo_log_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo_log: MagicMock,
    ) -> None:
        """List catalog repository logs."""
        mock_client.catalog_repository_logs.list.return_value = [mock_catalog_repo_log]

        result = cli_runner.invoke(app, ["catalog", "repo", "log", "list"])

        assert result.exit_code == 0
        assert "Repository refreshed successfully" in result.output
        mock_client.catalog_repository_logs.list.assert_called_once()

    def test_repo_log_list_by_repo(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo: MagicMock,
        mock_catalog_repo_log: MagicMock,
    ) -> None:
        """List logs filtered by repository."""
        mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]
        mock_client.catalog_repository_logs.list.return_value = [mock_catalog_repo_log]

        result = cli_runner.invoke(
            app,
            ["catalog", "repo", "log", "list", "--repo", "test-repo"],
        )

        assert result.exit_code == 0
        mock_client.catalog_repository_logs.list.assert_called_once_with(
            catalog_repository=1,
        )

    def test_repo_log_list_by_level(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo_log: MagicMock,
    ) -> None:
        """List logs filtered by level."""
        mock_client.catalog_repository_logs.list.return_value = [mock_catalog_repo_log]

        result = cli_runner.invoke(
            app,
            ["catalog", "repo", "log", "list", "--level", "error"],
        )

        assert result.exit_code == 0
        mock_client.catalog_repository_logs.list.assert_called_once_with(level="error")


class TestCatalogRepoLogGet:
    """Tests for vrg catalog repo log get."""

    def test_repo_log_get(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_catalog_repo_log: MagicMock,
    ) -> None:
        """Get a single log entry."""
        mock_client.catalog_repository_logs.get.return_value = mock_catalog_repo_log

        result = cli_runner.invoke(app, ["catalog", "repo", "log", "get", "100"])

        assert result.exit_code == 0
        assert "Repository refreshed successfully" in result.output
        mock_client.catalog_repository_logs.get.assert_called_once_with(key=100)
