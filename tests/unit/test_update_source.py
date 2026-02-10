"""Tests for update source management commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_source_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test listing update sources."""
    mock_client.update_sources.list.return_value = [mock_update_source]

    result = cli_runner.invoke(app, ["update", "source", "list"])

    assert result.exit_code == 0
    assert "test-source" in result.output
    mock_client.update_sources.list.assert_called_once()


def test_source_list_enabled(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test listing with --enabled filter."""
    mock_client.update_sources.list.return_value = [mock_update_source]

    result = cli_runner.invoke(app, ["update", "source", "list", "--enabled"])

    assert result.exit_code == 0
    mock_client.update_sources.list.assert_called_once_with(enabled=True)


def test_source_get_by_key(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test get source by numeric key."""
    mock_client.update_sources.get.return_value = mock_update_source

    result = cli_runner.invoke(app, ["update", "source", "get", "1"])

    assert result.exit_code == 0
    assert "test-source" in result.output


def test_source_get_by_name(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test get source by name (resolve)."""
    mock_client.update_sources.list.return_value = [mock_update_source]
    mock_client.update_sources.get.return_value = mock_update_source

    result = cli_runner.invoke(app, ["update", "source", "get", "test-source"])

    assert result.exit_code == 0
    assert "test-source" in result.output


def test_source_create(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test creating a source with name + url."""
    mock_client.update_sources.create.return_value = mock_update_source

    result = cli_runner.invoke(
        app,
        [
            "update",
            "source",
            "create",
            "--name",
            "new-source",
            "--url",
            "https://updates.example.com",
        ],
    )

    assert result.exit_code == 0
    mock_client.update_sources.create.assert_called_once_with(
        name="new-source",
        url="https://updates.example.com",
        enabled=True,
    )


def test_source_create_with_auth(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test creating a source with user + password."""
    mock_client.update_sources.create.return_value = mock_update_source

    result = cli_runner.invoke(
        app,
        [
            "update",
            "source",
            "create",
            "--name",
            "auth-source",
            "--url",
            "https://updates.example.com",
            "--user",
            "admin",
            "--password",
            "secret",
        ],
    )

    assert result.exit_code == 0
    mock_client.update_sources.create.assert_called_once_with(
        name="auth-source",
        url="https://updates.example.com",
        enabled=True,
        user="admin",
        password="secret",
    )


def test_source_update(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test updating a source URL."""
    mock_client.update_sources.get.return_value = mock_update_source
    mock_client.update_sources.update.return_value = mock_update_source

    result = cli_runner.invoke(
        app,
        [
            "update",
            "source",
            "update",
            "1",
            "--url",
            "https://new-url.example.com",
        ],
    )

    assert result.exit_code == 0
    mock_client.update_sources.update.assert_called_once_with(
        1,
        url="https://new-url.example.com",
    )


def test_source_delete_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source: MagicMock,
) -> None:
    """Test delete with --yes confirmation."""
    mock_client.update_sources.get.return_value = mock_update_source

    result = cli_runner.invoke(app, ["update", "source", "delete", "1", "--yes"])

    assert result.exit_code == 0
    mock_client.update_sources.delete.assert_called_once_with(1)


def test_source_delete_no_confirm(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test delete without --yes aborts."""
    result = cli_runner.invoke(app, ["update", "source", "delete", "1"], input="n\n")

    assert result.exit_code != 0
    mock_client.update_sources.delete.assert_not_called()


def test_source_status(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_update_source_status: MagicMock,
) -> None:
    """Test showing source status."""
    mock_client.update_sources.get_status.return_value = mock_update_source_status

    result = cli_runner.invoke(app, ["update", "source", "status", "1"])

    assert result.exit_code == 0
    assert "idle" in result.output
    mock_client.update_sources.get_status.assert_called_once_with(1)


def test_source_not_found(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Test name resolution error (exit 6)."""
    mock_client.update_sources.list.return_value = []

    result = cli_runner.invoke(app, ["update", "source", "get", "nonexistent"])

    assert result.exit_code == 6
