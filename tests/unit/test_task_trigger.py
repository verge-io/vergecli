"""Tests for task schedule trigger management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_trigger_list(cli_runner, mock_client, mock_task, mock_task_trigger):
    """Test listing triggers for a task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.task_schedule_triggers.list.return_value = [mock_task_trigger]
    result = cli_runner.invoke(app, ["task", "trigger", "list", "nightly-backup"])
    assert result.exit_code == 0
    assert "nightly-backup" in result.output
    assert "nightly-window" in result.output
    mock_client.task_schedule_triggers.list.assert_called_once_with(task=100)


def test_trigger_create(cli_runner, mock_client, mock_task, mock_task_schedule, mock_task_trigger):
    """Test creating a trigger linking a task to a schedule."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.task_schedules.list.return_value = [mock_task_schedule]
    mock_client.task_schedule_triggers.create.return_value = mock_task_trigger
    result = cli_runner.invoke(
        app,
        ["task", "trigger", "create", "nightly-backup", "--schedule", "nightly-window"],
    )
    assert result.exit_code == 0
    assert "created" in result.output
    mock_client.task_schedule_triggers.create.assert_called_once_with(task=100, schedule=200)


def test_trigger_delete(cli_runner, mock_client):
    """Test deleting a trigger with --yes."""
    result = cli_runner.invoke(app, ["task", "trigger", "delete", "300", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output
    mock_client.task_schedule_triggers.delete.assert_called_once_with(300)


def test_trigger_run(cli_runner, mock_client):
    """Test manually firing a trigger."""
    mock_client.task_schedule_triggers.trigger.return_value = None
    result = cli_runner.invoke(app, ["task", "trigger", "run", "300"])
    assert result.exit_code == 0
    assert "fired" in result.output
    mock_client.task_schedule_triggers.trigger.assert_called_once_with(300)
