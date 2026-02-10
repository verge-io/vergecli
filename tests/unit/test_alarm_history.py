"""Tests for alarm history commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_alarm_history_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm_history: MagicMock
) -> None:
    """Test listing alarm history."""
    mock_client.alarms.list_history.return_value = [mock_alarm_history]

    result = cli_runner.invoke(app, ["alarm", "history", "list"])

    assert result.exit_code == 0
    assert "100" in result.output
    assert "error" in result.output
    mock_client.alarms.list_history.assert_called_once_with(filter=None, level=None, limit=None)


def test_alarm_history_list_by_level(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm_history: MagicMock
) -> None:
    """Test listing alarm history filtered by level."""
    mock_client.alarms.list_history.return_value = [mock_alarm_history]

    result = cli_runner.invoke(app, ["alarm", "history", "list", "--level", "error"])

    assert result.exit_code == 0
    mock_client.alarms.list_history.assert_called_once_with(filter=None, level="error", limit=None)


def test_alarm_history_get(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm_history: MagicMock
) -> None:
    """Test getting an alarm history entry by key."""
    mock_client.alarms.get_history.return_value = mock_alarm_history

    result = cli_runner.invoke(app, ["alarm", "history", "get", "100"])

    assert result.exit_code == 0
    assert "Disk Failure" in result.output
    mock_client.alarms.get_history.assert_called_once_with(100)
