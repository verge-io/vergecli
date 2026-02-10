"""Tests for update package commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestUpdatePackageList:
    """Tests for vrg update package list."""

    def test_package_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_package: MagicMock,
    ) -> None:
        """List installed packages."""
        mock_client.update_packages.list.return_value = [mock_update_package]

        result = cli_runner.invoke(app, ["update", "package", "list"])

        assert result.exit_code == 0
        assert "yb-core" in result.output
        mock_client.update_packages.list.assert_called_once()

    def test_package_list_by_branch(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_package: MagicMock,
    ) -> None:
        """List packages filtered by branch."""
        mock_client.update_packages.list.return_value = [mock_update_package]

        result = cli_runner.invoke(
            app,
            ["update", "package", "list", "--branch", "1"],
        )

        assert result.exit_code == 0
        mock_client.update_packages.list.assert_called_once_with(branch=1)


class TestUpdatePackageGet:
    """Tests for vrg update package get."""

    def test_package_get(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_package: MagicMock,
    ) -> None:
        """Get a package by name."""
        mock_client.update_packages.get.return_value = mock_update_package

        result = cli_runner.invoke(app, ["update", "package", "get", "yb-core"])

        assert result.exit_code == 0
        assert "yb-core" in result.output
        mock_client.update_packages.get.assert_called_once_with(key="yb-core")
