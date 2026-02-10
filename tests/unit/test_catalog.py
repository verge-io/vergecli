"""Tests for catalog management commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from verge_cli.cli import app

if TYPE_CHECKING:
    from typer.testing import CliRunner


def test_catalog_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_catalog: MagicMock
) -> None:
    """Test listing catalogs."""
    mock_client.catalogs.list.return_value = [mock_catalog]

    result = cli_runner.invoke(app, ["catalog", "list"])

    assert result.exit_code == 0
    assert "test-catalog" in result.output
    mock_client.catalogs.list.assert_called_once()


def test_catalog_list_by_repo(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
    mock_catalog_repo: MagicMock,
) -> None:
    """Test listing catalogs filtered by repository."""
    mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]
    mock_client.catalogs.list.return_value = [mock_catalog]

    result = cli_runner.invoke(app, ["catalog", "list", "--repo", "test-repo"])

    assert result.exit_code == 0
    assert "test-catalog" in result.output
    mock_client.catalogs.list.assert_called_once_with(repository=1)


def test_catalog_list_enabled(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test listing only enabled catalogs."""
    mock_client.catalogs.list.return_value = [mock_catalog]

    result = cli_runner.invoke(app, ["catalog", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.catalogs.list.assert_called_once_with(enabled=True)


def test_catalog_get_by_key(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test getting a catalog by hex key."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    mock_client.catalogs.get.return_value = mock_catalog

    result = cli_runner.invoke(app, ["catalog", "get", hex_key])

    assert result.exit_code == 0
    assert "test-catalog" in result.output
    mock_client.catalogs.get.assert_called_once_with(hex_key)


def test_catalog_get_by_name(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test getting a catalog by name (resolves to hex key)."""
    mock_client.catalogs.list.return_value = [mock_catalog]
    mock_client.catalogs.get.return_value = mock_catalog

    result = cli_runner.invoke(app, ["catalog", "get", "test-catalog"])

    assert result.exit_code == 0
    assert "test-catalog" in result.output


def test_catalog_create(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
    mock_catalog_repo: MagicMock,
) -> None:
    """Test creating a catalog."""
    mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]
    mock_client.catalogs.create.return_value = mock_catalog

    result = cli_runner.invoke(
        app,
        ["catalog", "create", "--name", "test-catalog", "--repo", "test-repo"],
    )

    assert result.exit_code == 0
    mock_client.catalogs.create.assert_called_once_with(
        name="test-catalog",
        repository=1,
        publishing_scope="private",
        enabled=True,
    )


def test_catalog_create_with_scope(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
    mock_catalog_repo: MagicMock,
) -> None:
    """Test creating a catalog with a publishing scope."""
    mock_client.catalog_repositories.list.return_value = [mock_catalog_repo]
    mock_client.catalogs.create.return_value = mock_catalog

    result = cli_runner.invoke(
        app,
        [
            "catalog",
            "create",
            "--name",
            "test-catalog",
            "--repo",
            "test-repo",
            "--publishing-scope",
            "global",
        ],
    )

    assert result.exit_code == 0
    mock_client.catalogs.create.assert_called_once_with(
        name="test-catalog",
        repository=1,
        publishing_scope="global",
        enabled=True,
    )


def test_catalog_update(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test updating a catalog."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    mock_client.catalogs.update.return_value = mock_catalog

    result = cli_runner.invoke(
        app,
        ["catalog", "update", hex_key, "--description", "Updated description"],
    )

    assert result.exit_code == 0
    mock_client.catalogs.update.assert_called_once_with(hex_key, description="Updated description")


def test_catalog_delete_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test deleting a catalog with --yes."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    result = cli_runner.invoke(
        app,
        ["catalog", "delete", hex_key, "--yes"],
    )

    assert result.exit_code == 0
    mock_client.catalogs.delete.assert_called_once_with(hex_key)


def test_catalog_delete_no_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test deleting a catalog without --yes aborts."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

    result = cli_runner.invoke(
        app,
        ["catalog", "delete", hex_key],
        input="n\n",
    )

    assert result.exit_code != 0
    mock_client.catalogs.delete.assert_not_called()


def test_catalog_enable(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test enabling a catalog."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    mock_client.catalogs.update.return_value = mock_catalog

    result = cli_runner.invoke(app, ["catalog", "enable", hex_key])

    assert result.exit_code == 0
    mock_client.catalogs.update.assert_called_once_with(hex_key, enabled=True)


def test_catalog_disable(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_catalog: MagicMock,
) -> None:
    """Test disabling a catalog."""
    hex_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    mock_client.catalogs.update.return_value = mock_catalog

    result = cli_runner.invoke(app, ["catalog", "disable", hex_key])

    assert result.exit_code == 0
    mock_client.catalogs.update.assert_called_once_with(hex_key, enabled=False)


def test_catalog_not_found(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test name resolution error when catalog not found."""
    mock_client.catalogs.list.return_value = []

    result = cli_runner.invoke(app, ["catalog", "get", "nonexistent"])

    assert result.exit_code == 6
