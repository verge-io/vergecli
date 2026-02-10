"""Tests for catalog log management commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_catalog_log_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog_log: MagicMock,
) -> None:
    """Test listing catalog logs."""
    mock_client.catalog_logs.list.return_value = [mock_catalog_log]

    result = cli_runner.invoke(app, ["catalog", "log", "list"])

    assert result.exit_code == 0
    assert "Catalog synced successfully" in result.output
    mock_client.catalog_logs.list.assert_called_once()


def test_catalog_log_list_by_catalog(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
    mock_catalog_log: MagicMock,
) -> None:
    """Test listing catalog logs filtered by catalog."""
    mock_client.catalogs.list.return_value = [mock_catalog]
    mock_client.catalog_logs.list.return_value = [mock_catalog_log]

    result = cli_runner.invoke(app, ["catalog", "log", "list", "--catalog", "test-catalog"])

    assert result.exit_code == 0
    assert "Catalog synced successfully" in result.output
    mock_client.catalog_logs.list.assert_called_once_with(
        catalog="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
    )


def test_catalog_log_get(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog_log: MagicMock,
) -> None:
    """Test getting a single catalog log entry."""
    mock_client.catalog_logs.get.return_value = mock_catalog_log

    result = cli_runner.invoke(app, ["catalog", "log", "get", "200"])

    assert result.exit_code == 0
    assert "Catalog synced successfully" in result.output
    mock_client.catalog_logs.get.assert_called_once_with(key=200)
