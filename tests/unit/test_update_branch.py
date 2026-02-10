"""Tests for update branch commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestUpdateBranchList:
    """Tests for vrg update branch list."""

    def test_branch_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_branch: MagicMock,
    ) -> None:
        """List update branches."""
        mock_client.update_branches.list.return_value = [mock_update_branch]

        result = cli_runner.invoke(app, ["update", "branch", "list"])

        assert result.exit_code == 0
        assert "stable-4.13" in result.output
        mock_client.update_branches.list.assert_called_once()


class TestUpdateBranchGet:
    """Tests for vrg update branch get."""

    def test_branch_get_by_key(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_branch: MagicMock,
    ) -> None:
        """Get a branch by key."""
        mock_client.update_branches.get.return_value = mock_update_branch

        result = cli_runner.invoke(app, ["update", "branch", "get", "1"])

        assert result.exit_code == 0
        assert "stable-4.13" in result.output
        mock_client.update_branches.get.assert_called_once_with(key=1)

    def test_branch_get_by_name(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_branch: MagicMock,
    ) -> None:
        """Get a branch by name (resolve via list)."""
        mock_client.update_branches.list.return_value = [mock_update_branch]
        mock_client.update_branches.get.return_value = mock_update_branch

        result = cli_runner.invoke(app, ["update", "branch", "get", "stable-4.13"])

        assert result.exit_code == 0
        assert "stable-4.13" in result.output
