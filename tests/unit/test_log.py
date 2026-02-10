"""Tests for system log commands."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app
from verge_cli.commands.log import _parse_datetime


def test_log_list(cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock) -> None:
    """Test listing logs with default limit."""
    mock_client.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list"])

    assert result.exit_code == 0
    assert "1000" in result.output
    assert "audit" in result.output
    mock_client.logs.list.assert_called_once_with(
        filter=None,
        level=None,
        object_type=None,
        user=None,
        since=None,
        before=None,
        limit=100,
    )


def test_log_list_with_limit(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs with custom limit."""
    mock_client.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--limit", "50"])

    assert result.exit_code == 0
    mock_client.logs.list.assert_called_once_with(
        filter=None,
        level=None,
        object_type=None,
        user=None,
        since=None,
        before=None,
        limit=50,
    )


def test_log_list_by_level(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs filtered by level uses list_by_level()."""
    mock_client.logs.list_by_level.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--level", "error"])

    assert result.exit_code == 0
    mock_client.logs.list_by_level.assert_called_once_with(level="error", limit=100, since=None)


def test_log_list_errors(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test --errors shortcut uses list_errors()."""
    mock_client.logs.list_errors.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--errors"])

    assert result.exit_code == 0
    mock_client.logs.list_errors.assert_called_once_with(limit=100, since=None)


def test_log_list_by_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs filtered by object type uses list_by_object_type()."""
    mock_client.logs.list_by_object_type.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--type", "vm"])

    assert result.exit_code == 0
    mock_client.logs.list_by_object_type.assert_called_once_with(
        object_type="vm", limit=100, since=None
    )


def test_log_list_by_user(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs filtered by user uses list_by_user()."""
    mock_client.logs.list_by_user.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--user", "admin"])

    assert result.exit_code == 0
    mock_client.logs.list_by_user.assert_called_once_with(user="admin", limit=100, since=None)


def test_log_list_since(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs with --since filter."""
    mock_client.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--since", "2026-02-10"])

    assert result.exit_code == 0
    mock_client.logs.list.assert_called_once_with(
        filter=None,
        level=None,
        object_type=None,
        user=None,
        since=datetime(2026, 2, 10),
        before=None,
        limit=100,
    )


def test_log_list_before(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test listing logs with --before filter."""
    mock_client.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "list", "--before", "2026-02-10T12:00:00"])

    assert result.exit_code == 0
    mock_client.logs.list.assert_called_once_with(
        filter=None,
        level=None,
        object_type=None,
        user=None,
        since=None,
        before=datetime(2026, 2, 10, 12, 0, 0),
        limit=100,
    )


def test_log_get(cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock) -> None:
    """Test getting a log entry by key."""
    mock_client.logs.get.return_value = mock_log_entry

    result = cli_runner.invoke(app, ["log", "get", "1000"])

    assert result.exit_code == 0
    assert "web-server-01" in result.output
    mock_client.logs.get.assert_called_once_with(key=1000)


def test_log_search(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test searching logs by text."""
    mock_client.logs.search.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "search", "started"])

    assert result.exit_code == 0
    assert "web-server-01" in result.output
    mock_client.logs.search.assert_called_once_with(
        text="started",
        level=None,
        object_type=None,
        since=None,
        limit=100,
    )


def test_log_search_with_level(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test searching logs with level filter."""
    mock_client.logs.search.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "search", "warning text", "--level", "warning"])

    assert result.exit_code == 0
    mock_client.logs.search.assert_called_once_with(
        text="warning text",
        level="warning",
        object_type=None,
        since=None,
        limit=100,
    )


def test_log_search_with_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test searching logs with object type filter."""
    mock_client.logs.search.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "search", "snapshot", "--type", "vm"])

    assert result.exit_code == 0
    mock_client.logs.search.assert_called_once_with(
        text="snapshot",
        level=None,
        object_type="vm",
        since=None,
        limit=100,
    )


def test_log_search_with_since(
    cli_runner: CliRunner, mock_client: MagicMock, mock_log_entry: MagicMock
) -> None:
    """Test searching logs with since filter."""
    mock_client.logs.search.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["log", "search", "power", "--since", "2026-02-10"])

    assert result.exit_code == 0
    mock_client.logs.search.assert_called_once_with(
        text="power",
        level=None,
        object_type=None,
        since=datetime(2026, 2, 10),
        limit=100,
    )


def test_parse_datetime_iso() -> None:
    """Test parsing ISO 8601 datetime string."""
    result = _parse_datetime("2026-02-10T12:00:00")
    assert result == datetime(2026, 2, 10, 12, 0, 0)


def test_parse_datetime_date_only() -> None:
    """Test parsing date-only string."""
    result = _parse_datetime("2026-02-10")
    assert result == datetime(2026, 2, 10, 0, 0, 0)


def test_parse_datetime_invalid() -> None:
    """Test invalid datetime format raises BadParameter."""
    with pytest.raises(Exception, match="Invalid datetime format"):
        _parse_datetime("not-a-date")
