"""Tests for alarm commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_alarm_list(cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock) -> None:
    """Test listing active alarms."""
    mock_client.alarms.list.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list"])

    assert result.exit_code == 0
    assert "42" in result.output
    assert "warning" in result.output
    mock_client.alarms.list.assert_called_once_with(
        filter=None, level=None, include_snoozed=False, limit=None
    )


def test_alarm_list_critical(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test listing critical alarms uses list_critical()."""
    mock_client.alarms.list_critical.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list", "--level", "critical"])

    assert result.exit_code == 0
    mock_client.alarms.list_critical.assert_called_once_with(include_snoozed=False, limit=None)


def test_alarm_list_errors(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test listing error alarms uses list_errors()."""
    mock_client.alarms.list_errors.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list", "--level", "error"])

    assert result.exit_code == 0
    mock_client.alarms.list_errors.assert_called_once_with(include_snoozed=False, limit=None)


def test_alarm_list_warnings(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test listing warning alarms uses list_warnings()."""
    mock_client.alarms.list_warnings.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list", "--level", "warning"])

    assert result.exit_code == 0
    mock_client.alarms.list_warnings.assert_called_once_with(include_snoozed=False, limit=None)


def test_alarm_list_by_owner_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test listing alarms filtered by owner type."""
    mock_client.alarms.list_by_owner_type.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list", "--owner-type", "VM"])

    assert result.exit_code == 0
    mock_client.alarms.list_by_owner_type.assert_called_once_with(
        owner_type="VM", include_snoozed=False, limit=None
    )


def test_alarm_list_include_snoozed(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test listing alarms with snoozed included."""
    mock_client.alarms.list.return_value = [mock_alarm]

    result = cli_runner.invoke(app, ["alarm", "list", "--include-snoozed"])

    assert result.exit_code == 0
    mock_client.alarms.list.assert_called_once_with(
        filter=None, level=None, include_snoozed=True, limit=None
    )


def test_alarm_get(cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock) -> None:
    """Test getting an alarm by key."""
    mock_client.alarms.get.return_value = mock_alarm

    result = cli_runner.invoke(app, ["alarm", "get", "42"])

    assert result.exit_code == 0
    assert "High CPU Usage" in result.output
    mock_client.alarms.get.assert_called_once_with(key=42)


def test_alarm_snooze_default(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test snoozing an alarm with default 24 hours."""
    mock_client.alarms.snooze.return_value = mock_alarm

    result = cli_runner.invoke(app, ["alarm", "snooze", "42"])

    assert result.exit_code == 0
    assert "snoozed" in result.output.lower()
    assert "24" in result.output
    mock_client.alarms.snooze.assert_called_once_with(42, hours=24)


def test_alarm_snooze_custom(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test snoozing an alarm with custom hours."""
    mock_client.alarms.snooze.return_value = mock_alarm

    result = cli_runner.invoke(app, ["alarm", "snooze", "42", "--hours", "48"])

    assert result.exit_code == 0
    assert "snoozed" in result.output.lower()
    assert "48" in result.output
    mock_client.alarms.snooze.assert_called_once_with(42, hours=48)


def test_alarm_unsnooze(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test unsnoozing an alarm."""
    mock_client.alarms.unsnooze.return_value = mock_alarm

    result = cli_runner.invoke(app, ["alarm", "unsnooze", "42"])

    assert result.exit_code == 0
    assert "unsnoozed" in result.output.lower()
    mock_client.alarms.unsnooze.assert_called_once_with(42)


def test_alarm_resolve(
    cli_runner: CliRunner, mock_client: MagicMock, mock_alarm: MagicMock
) -> None:
    """Test resolving an alarm."""
    mock_client.alarms.resolve.return_value = None

    result = cli_runner.invoke(app, ["alarm", "resolve", "42"])

    assert result.exit_code == 0
    assert "resolved" in result.output.lower()
    mock_client.alarms.resolve.assert_called_once_with(42)


def test_alarm_summary(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test alarm summary display."""
    mock_client.alarms.get_summary.return_value = {
        "total": 5,
        "active": 4,
        "snoozed": 1,
        "critical": 1,
        "error": 1,
        "warning": 2,
        "message": 0,
        "resolvable": 2,
    }

    result = cli_runner.invoke(app, ["alarm", "summary"])

    assert result.exit_code == 0
    assert "critical" in result.output
    assert "error" in result.output
    assert "warning" in result.output
    mock_client.alarms.get_summary.assert_called_once()
