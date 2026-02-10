"""Tests for task schedule management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_schedule_list(cli_runner, mock_client, mock_task_schedule):
    """Test listing schedules."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    result = cli_runner.invoke(app, ["task", "schedule", "list"])
    assert result.exit_code == 0
    assert "nightly-window" in result.output
    mock_client.task_schedules.list.assert_called_once()


def test_schedule_list_enabled(cli_runner, mock_client, mock_task_schedule):
    """Test listing enabled schedules."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    result = cli_runner.invoke(app, ["task", "schedule", "list", "--enabled"])
    assert result.exit_code == 0
    mock_client.task_schedules.list.assert_called_once_with(enabled=True)


def test_schedule_list_by_repeat(cli_runner, mock_client, mock_task_schedule):
    """Test listing schedules by repeat interval."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    result = cli_runner.invoke(app, ["task", "schedule", "list", "--repeat-every", "day"])
    assert result.exit_code == 0
    mock_client.task_schedules.list.assert_called_once_with(repeat_every="day")


def test_schedule_get(cli_runner, mock_client, mock_task_schedule):
    """Test getting a schedule by name."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.get.return_value = mock_task_schedule
    result = cli_runner.invoke(app, ["task", "schedule", "get", "nightly-window"])
    assert result.exit_code == 0
    assert "nightly-window" in result.output


def test_schedule_create_basic(cli_runner, mock_client, mock_task_schedule):
    """Test creating a schedule with defaults."""
    mock_client.task_schedules.create.return_value = mock_task_schedule
    result = cli_runner.invoke(
        app,
        ["task", "schedule", "create", "--name", "test-schedule"],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower()
    mock_client.task_schedules.create.assert_called_once()
    call_kwargs = mock_client.task_schedules.create.call_args
    assert (
        call_kwargs.kwargs["name"] == "test-schedule" or call_kwargs[1]["name"] == "test-schedule"
    )


def test_schedule_create_daily(cli_runner, mock_client, mock_task_schedule):
    """Test creating a daily schedule with time window."""
    mock_client.task_schedules.create.return_value = mock_task_schedule
    result = cli_runner.invoke(
        app,
        [
            "task",
            "schedule",
            "create",
            "--name",
            "daily-backup",
            "--repeat-every",
            "day",
            "--start-time",
            "7200",
            "--end-time",
            "14400",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower()


def test_schedule_create_weekly(cli_runner, mock_client, mock_task_schedule):
    """Test creating a weekly schedule with specific days."""
    mock_client.task_schedules.create.return_value = mock_task_schedule
    result = cli_runner.invoke(
        app,
        [
            "task",
            "schedule",
            "create",
            "--name",
            "weekday-only",
            "--repeat-every",
            "week",
            "--no-saturday",
            "--no-sunday",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower()
    call_kwargs = mock_client.task_schedules.create.call_args
    # Saturday and Sunday should be False
    if call_kwargs.kwargs:
        assert call_kwargs.kwargs["saturday"] is False
        assert call_kwargs.kwargs["sunday"] is False
    else:
        assert call_kwargs[1]["saturday"] is False
        assert call_kwargs[1]["sunday"] is False


def test_schedule_update(cli_runner, mock_client, mock_task_schedule):
    """Test updating a schedule."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.update.return_value = mock_task_schedule
    result = cli_runner.invoke(
        app,
        [
            "task",
            "schedule",
            "update",
            "nightly-window",
            "--repeat-every",
            "week",
            "--no-saturday",
        ],
    )
    assert result.exit_code == 0
    assert "updated" in result.output.lower()
    mock_client.task_schedules.update.assert_called_once_with(
        200, repeat_every="week", saturday=False
    )


def test_schedule_delete(cli_runner, mock_client, mock_task_schedule):
    """Test deleting a schedule with --yes."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    result = cli_runner.invoke(app, ["task", "schedule", "delete", "nightly-window", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.task_schedules.delete.assert_called_once_with(200)


def test_schedule_enable(cli_runner, mock_client, mock_task_schedule):
    """Test enabling a schedule."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.enable.return_value = mock_task_schedule
    result = cli_runner.invoke(app, ["task", "schedule", "enable", "nightly-window"])
    assert result.exit_code == 0
    assert "enabled" in result.output.lower()
    mock_client.task_schedules.enable.assert_called_once_with(200)


def test_schedule_disable(cli_runner, mock_client, mock_task_schedule):
    """Test disabling a schedule."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.disable.return_value = mock_task_schedule
    result = cli_runner.invoke(app, ["task", "schedule", "disable", "nightly-window"])
    assert result.exit_code == 0
    assert "disabled" in result.output.lower()
    mock_client.task_schedules.disable.assert_called_once_with(200)


def test_schedule_show(cli_runner, mock_client, mock_task_schedule):
    """Test showing upcoming executions."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.get_schedule.return_value = [
        {"time": "2026-02-11 02:00:00"},
        {"time": "2026-02-12 02:00:00"},
    ]
    result = cli_runner.invoke(app, ["task", "schedule", "show", "nightly-window"])
    assert result.exit_code == 0
    mock_client.task_schedules.get_schedule.assert_called_once_with(200, max_results=20)


def test_schedule_show_max_results(cli_runner, mock_client, mock_task_schedule):
    """Test --max-results option for schedule show."""
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedules.get_schedule.return_value = []
    result = cli_runner.invoke(
        app,
        ["task", "schedule", "show", "nightly-window", "--max-results", "5"],
    )
    assert result.exit_code == 0
    mock_client.task_schedules.get_schedule.assert_called_once_with(200, max_results=5)
