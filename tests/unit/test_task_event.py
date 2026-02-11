"""Tests for task event management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_event_list(cli_runner, mock_client, mock_task_event):
    """Test listing all task events."""
    mock_client.task_events.list.return_value = [mock_task_event]
    result = cli_runner.invoke(app, ["task", "event", "list"])
    assert result.exit_code == 0
    assert "poweron" in result.output
    mock_client.task_events.list.assert_called_once()


def test_event_list_by_task(cli_runner, mock_client, mock_task, mock_task_event):
    """Test listing events filtered by task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.task_events.list.return_value = [mock_task_event]
    result = cli_runner.invoke(app, ["task", "event", "list", "--task", "nightly-backup"])
    assert result.exit_code == 0
    mock_client.task_events.list.assert_called_once_with(task=100)


def test_event_list_by_table(cli_runner, mock_client, mock_task_event):
    """Test listing events filtered by table."""
    mock_client.task_events.list.return_value = [mock_task_event]
    result = cli_runner.invoke(app, ["task", "event", "list", "--table", "vms"])
    assert result.exit_code == 0
    mock_client.task_events.list.assert_called_once_with(table="vms")


def test_event_list_by_event(cli_runner, mock_client, mock_task_event):
    """Test listing events filtered by event type."""
    mock_client.task_events.list.return_value = [mock_task_event]
    result = cli_runner.invoke(app, ["task", "event", "list", "--event", "poweron"])
    assert result.exit_code == 0
    mock_client.task_events.list.assert_called_once_with(event="poweron")


def test_event_get(cli_runner, mock_client, mock_task_event):
    """Test getting an event by numeric key."""
    mock_client.task_events.get.return_value = mock_task_event
    result = cli_runner.invoke(app, ["task", "event", "get", "400"])
    assert result.exit_code == 0
    assert "poweron" in result.output
    mock_client.task_events.get.assert_called_once_with(400)


def test_event_create(cli_runner, mock_client, mock_task, mock_task_event):
    """Test creating an event with required fields."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.task_events.create.return_value = mock_task_event
    result = cli_runner.invoke(
        app,
        [
            "task",
            "event",
            "create",
            "--task",
            "nightly-backup",
            "--event",
            "poweron",
            "--table",
            "vms",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output
    mock_client.task_events.create.assert_called_once_with(task=100, event="poweron", table="vms")


def test_event_create_with_options(cli_runner, mock_client, mock_task, mock_task_event):
    """Test creating an event with all optional fields."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.task_events.create.return_value = mock_task_event
    result = cli_runner.invoke(
        app,
        [
            "task",
            "event",
            "create",
            "--task",
            "nightly-backup",
            "--event",
            "poweron",
            "--table",
            "vms",
            "--event-name",
            "Power On",
            "--filters-json",
            '{"severity": "high"}',
            "--context-json",
            '{"notify": true}',
        ],
    )
    assert result.exit_code == 0
    mock_client.task_events.create.assert_called_once_with(
        task=100,
        event="poweron",
        table="vms",
        event_name="Power On",
        table_event_filters={"severity": "high"},
        context={"notify": True},
    )


def test_event_update(cli_runner, mock_client):
    """Test updating event filters and context."""
    result = cli_runner.invoke(
        app,
        [
            "task",
            "event",
            "update",
            "400",
            "--filters-json",
            '{"severity": "critical"}',
            "--context-json",
            '{"escalate": true}',
        ],
    )
    assert result.exit_code == 0
    assert "updated" in result.output
    mock_client.task_events.update.assert_called_once_with(
        400,
        table_event_filters={"severity": "critical"},
        context={"escalate": True},
    )


def test_event_delete(cli_runner, mock_client):
    """Test deleting an event with --yes."""
    result = cli_runner.invoke(app, ["task", "event", "delete", "400", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output
    mock_client.task_events.delete.assert_called_once_with(400)


def test_event_delete_no_confirm(cli_runner, mock_client):
    """Test deleting an event without --yes aborts."""
    result = cli_runner.invoke(app, ["task", "event", "delete", "400"], input="n\n")
    assert result.exit_code == 0
    mock_client.task_events.delete.assert_not_called()


def test_event_trigger(cli_runner, mock_client):
    """Test manually triggering an event."""
    result = cli_runner.invoke(app, ["task", "event", "trigger", "400"])
    assert result.exit_code == 0
    assert "triggered" in result.output
    mock_client.task_events.trigger.assert_called_once_with(400, context=None)


def test_event_trigger_with_context(cli_runner, mock_client):
    """Test triggering an event with context data."""
    result = cli_runner.invoke(
        app,
        ["task", "event", "trigger", "400", "--context-json", '{"custom": "data"}'],
    )
    assert result.exit_code == 0
    mock_client.task_events.trigger.assert_called_once_with(400, context={"custom": "data"})
