"""Tests for update available package commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


class TestUpdateAvailableList:
    """Tests for vrg update available list."""

    def test_available_list(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_source_package: MagicMock,
    ) -> None:
        """List available packages."""
        mock_client.update_source_packages.list.return_value = [mock_update_source_package]

        result = cli_runner.invoke(app, ["update", "available", "list"])

        assert result.exit_code == 0
        assert "yb-core" in result.output
        mock_client.update_source_packages.list.assert_called_once()

    def test_available_list_by_source(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_source_package: MagicMock,
    ) -> None:
        """List available packages filtered by source."""
        mock_client.update_source_packages.list.return_value = [mock_update_source_package]

        result = cli_runner.invoke(
            app,
            ["update", "available", "list", "--source", "1"],
        )

        assert result.exit_code == 0
        mock_client.update_source_packages.list.assert_called_once_with(source=1)

    def test_available_list_downloaded(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_source_package: MagicMock,
    ) -> None:
        """List only downloaded packages."""
        mock_client.update_source_packages.list_downloaded.return_value = [
            mock_update_source_package
        ]

        result = cli_runner.invoke(
            app,
            ["update", "available", "list", "--downloaded"],
        )

        assert result.exit_code == 0
        mock_client.update_source_packages.list_downloaded.assert_called_once()

    def test_available_list_pending(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_source_package: MagicMock,
    ) -> None:
        """List only pending packages."""
        mock_client.update_source_packages.list_pending.return_value = [mock_update_source_package]

        result = cli_runner.invoke(
            app,
            ["update", "available", "list", "--pending"],
        )

        assert result.exit_code == 0
        mock_client.update_source_packages.list_pending.assert_called_once()


class TestUpdateAvailableGet:
    """Tests for vrg update available get."""

    def test_available_get(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_update_source_package: MagicMock,
    ) -> None:
        """Get an available package by key."""
        mock_client.update_source_packages.get.return_value = mock_update_source_package

        result = cli_runner.invoke(app, ["update", "available", "get", "10"])

        assert result.exit_code == 0
        assert "yb-core" in result.output
        mock_client.update_source_packages.get.assert_called_once_with(key=10)
