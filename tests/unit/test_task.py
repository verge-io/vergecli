"""Tests for task management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_task_list(cli_runner, mock_client, mock_task):
    """Test listing tasks."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "list"])
    assert result.exit_code == 0
    assert "nightly-backup" in result.output
    mock_client.tasks.list.assert_called_once()


def test_task_list_running(cli_runner, mock_client, mock_task):
    """Test listing running tasks."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "list", "--running"])
    assert result.exit_code == 0
    mock_client.tasks.list.assert_called_once_with(running=True)


def test_task_list_enabled(cli_runner, mock_client, mock_task):
    """Test listing enabled tasks."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "list", "--enabled"])
    assert result.exit_code == 0
    mock_client.tasks.list.assert_called_once_with(enabled=True)


def test_task_list_disabled(cli_runner, mock_client, mock_task):
    """Test listing disabled tasks."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "list", "--disabled"])
    assert result.exit_code == 0
    mock_client.tasks.list.assert_called_once_with(enabled=False)


def test_task_get(cli_runner, mock_client, mock_task):
    """Test getting a task by name."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.get.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "get", "nightly-backup"])
    assert result.exit_code == 0
    assert "nightly-backup" in result.output


def test_task_get_by_key(cli_runner, mock_client, mock_task):
    """Test getting a task by numeric key."""
    mock_client.tasks.list.return_value = []
    mock_client.tasks.get.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "get", "100"])
    assert result.exit_code == 0
    assert "nightly-backup" in result.output
    mock_client.tasks.get.assert_called_once_with(100)


def test_task_create(cli_runner, mock_client, mock_task):
    """Test creating a task with required fields."""
    mock_client.tasks.create.return_value = mock_task
    result = cli_runner.invoke(
        app,
        [
            "task",
            "create",
            "--name",
            "nightly-backup",
            "--owner",
            "1",
            "--action",
            "snapshot",
            "--table",
            "vms",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower()
    mock_client.tasks.create.assert_called_once_with(
        name="nightly-backup",
        owner=1,
        action="snapshot",
        table="vms",
        enabled=True,
        delete_after_run=False,
    )


def test_task_create_with_options(cli_runner, mock_client, mock_task):
    """Test creating a task with all optional flags."""
    mock_client.tasks.create.return_value = mock_task
    result = cli_runner.invoke(
        app,
        [
            "task",
            "create",
            "--name",
            "backup",
            "--owner",
            "1",
            "--action",
            "snapshot",
            "--table",
            "vms",
            "--description",
            "Test task",
            "--disabled",
            "--delete-after-run",
            "--settings-json",
            '{"key": "value"}',
        ],
    )
    assert result.exit_code == 0
    mock_client.tasks.create.assert_called_once_with(
        name="backup",
        owner=1,
        action="snapshot",
        enabled=False,
        delete_after_run=True,
        table="vms",
        description="Test task",
        settings_args={"key": "value"},
    )


def test_task_update(cli_runner, mock_client, mock_task):
    """Test updating a task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.update.return_value = mock_task
    result = cli_runner.invoke(
        app,
        ["task", "update", "nightly-backup", "--name", "new-name", "--description", "Updated"],
    )
    assert result.exit_code == 0
    assert "updated" in result.output.lower()
    mock_client.tasks.update.assert_called_once_with(100, name="new-name", description="Updated")


def test_task_delete(cli_runner, mock_client, mock_task):
    """Test deleting a task with --yes."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "delete", "nightly-backup", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.tasks.delete.assert_called_once_with(100)


def test_task_delete_no_confirm(cli_runner, mock_client, mock_task):
    """Test deleting a task without --yes aborts."""
    mock_client.tasks.list.return_value = [mock_task]
    result = cli_runner.invoke(app, ["task", "delete", "nightly-backup"], input="n\n")
    assert result.exit_code == 0
    mock_client.tasks.delete.assert_not_called()


def test_task_enable(cli_runner, mock_client, mock_task):
    """Test enabling a task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.enable.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "enable", "nightly-backup"])
    assert result.exit_code == 0
    assert "enabled" in result.output.lower()
    mock_client.tasks.enable.assert_called_once_with(100)


def test_task_disable(cli_runner, mock_client, mock_task):
    """Test disabling a task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.disable.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "disable", "nightly-backup"])
    assert result.exit_code == 0
    assert "disabled" in result.output.lower()
    mock_client.tasks.disable.assert_called_once_with(100)


def test_task_run(cli_runner, mock_client, mock_task):
    """Test executing a task (no wait)."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.execute.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "run", "nightly-backup"])
    assert result.exit_code == 0
    assert "started" in result.output.lower()
    mock_client.tasks.execute.assert_called_once_with(100)


def test_task_run_with_wait(cli_runner, mock_client, mock_task):
    """Test executing a task with --wait."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.execute.return_value = mock_task
    mock_client.tasks.wait.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "run", "nightly-backup", "--wait"])
    assert result.exit_code == 0
    assert "completed" in result.output.lower()
    mock_client.tasks.execute.assert_called_once_with(100)
    mock_client.tasks.wait.assert_called_once_with(100, timeout=300, raise_on_error=True)


def test_task_run_with_params(cli_runner, mock_client, mock_task):
    """Test executing a task with --params-json."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.execute.return_value = mock_task
    result = cli_runner.invoke(
        app,
        ["task", "run", "nightly-backup", "--params-json", '{"snapshot_name": "manual"}'],
    )
    assert result.exit_code == 0
    mock_client.tasks.execute.assert_called_once_with(100, snapshot_name="manual")


def test_task_cancel(cli_runner, mock_client, mock_task):
    """Test cancelling a running task."""
    mock_client.tasks.list.return_value = [mock_task]
    mock_client.tasks.cancel.return_value = mock_task
    result = cli_runner.invoke(app, ["task", "cancel", "nightly-backup"])
    assert result.exit_code == 0
    assert "cancelled" in result.output.lower()
    mock_client.tasks.cancel.assert_called_once_with(100)


def test_task_not_found(cli_runner, mock_client):
    """Test task not found error."""
    mock_client.tasks.list.return_value = []
    result = cli_runner.invoke(app, ["task", "get", "nonexistent"])
    assert result.exit_code == 6
