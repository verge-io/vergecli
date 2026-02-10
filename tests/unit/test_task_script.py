"""Tests for task script management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_script_list(cli_runner, mock_client, mock_task_script):
    """Test listing task scripts."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(app, ["task", "script", "list"])
    assert result.exit_code == 0
    assert "cleanup-logs" in result.output
    mock_client.task_scripts.list.assert_called_once()


def test_script_get(cli_runner, mock_client, mock_task_script):
    """Test getting a script by name."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    mock_client.task_scripts.get.return_value = mock_task_script
    result = cli_runner.invoke(app, ["task", "script", "get", "cleanup-logs"])
    assert result.exit_code == 0
    assert "cleanup-logs" in result.output


def test_script_get_by_key(cli_runner, mock_client, mock_task_script):
    """Test getting a script by numeric key."""
    mock_client.task_scripts.list.return_value = []
    mock_client.task_scripts.get.return_value = mock_task_script
    result = cli_runner.invoke(app, ["task", "script", "get", "500"])
    assert result.exit_code == 0
    assert "cleanup-logs" in result.output
    mock_client.task_scripts.get.assert_called_once_with(500)


def test_script_create_inline(cli_runner, mock_client, mock_task_script):
    """Test creating a script with inline code."""
    mock_client.task_scripts.create.return_value = mock_task_script
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "create",
            "--name",
            "test-script",
            "--script",
            'log("Hello")',
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output
    mock_client.task_scripts.create.assert_called_once_with(
        name="test-script", script='log("Hello")'
    )


def test_script_create_from_file(cli_runner, mock_client, mock_task_script, tmp_path):
    """Test creating a script from @file path."""
    script_file = tmp_path / "test.gcs"
    script_file.write_text('log("From file")')
    mock_client.task_scripts.create.return_value = mock_task_script
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "create",
            "--name",
            "file-script",
            "--script",
            f"@{script_file}",
        ],
    )
    assert result.exit_code == 0
    mock_client.task_scripts.create.assert_called_once_with(
        name="file-script", script='log("From file")'
    )


def test_script_create_file_not_found(cli_runner, mock_client):
    """Test error when @file does not exist."""
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "create",
            "--name",
            "bad-file",
            "--script",
            "@/nonexistent/path.gcs",
        ],
    )
    assert result.exit_code != 0


def test_script_create_with_options(cli_runner, mock_client, mock_task_script):
    """Test creating a script with all optional fields."""
    mock_client.task_scripts.create.return_value = mock_task_script
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "create",
            "--name",
            "full-script",
            "--script",
            'log("test")',
            "--description",
            "A test script",
            "--settings-json",
            '{"questions": []}',
        ],
    )
    assert result.exit_code == 0
    mock_client.task_scripts.create.assert_called_once_with(
        name="full-script",
        script='log("test")',
        description="A test script",
        task_settings={"questions": []},
    )


def test_script_update(cli_runner, mock_client, mock_task_script):
    """Test updating a script name and code."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "update",
            "cleanup-logs",
            "--name",
            "cleanup-logs-v2",
            "--script",
            'log("Updated")',
        ],
    )
    assert result.exit_code == 0
    assert "updated" in result.output
    mock_client.task_scripts.update.assert_called_once_with(
        500, name="cleanup-logs-v2", script='log("Updated")'
    )


def test_script_update_from_file(cli_runner, mock_client, mock_task_script, tmp_path):
    """Test updating a script from @file path."""
    script_file = tmp_path / "updated.gcs"
    script_file.write_text('log("Updated from file")')
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "update",
            "cleanup-logs",
            "--script",
            f"@{script_file}",
        ],
    )
    assert result.exit_code == 0
    mock_client.task_scripts.update.assert_called_once_with(500, script='log("Updated from file")')


def test_script_delete(cli_runner, mock_client, mock_task_script):
    """Test deleting a script with --yes."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(
        app,
        ["task", "script", "delete", "cleanup-logs", "--yes"],
    )
    assert result.exit_code == 0
    assert "deleted" in result.output
    mock_client.task_scripts.delete.assert_called_once_with(500)


def test_script_delete_no_confirm(cli_runner, mock_client, mock_task_script):
    """Test deleting a script without --yes aborts."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(
        app,
        ["task", "script", "delete", "cleanup-logs"],
        input="n\n",
    )
    assert result.exit_code == 0
    mock_client.task_scripts.delete.assert_not_called()


def test_script_run(cli_runner, mock_client, mock_task_script):
    """Test running a script."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(app, ["task", "script", "run", "cleanup-logs"])
    assert result.exit_code == 0
    assert "started" in result.output
    mock_client.task_scripts.run.assert_called_once_with(500)


def test_script_run_with_params(cli_runner, mock_client, mock_task_script):
    """Test running a script with parameters."""
    mock_client.task_scripts.list.return_value = [mock_task_script]
    result = cli_runner.invoke(
        app,
        [
            "task",
            "script",
            "run",
            "cleanup-logs",
            "--params-json",
            '{"target_vm": 123}',
        ],
    )
    assert result.exit_code == 0
    mock_client.task_scripts.run.assert_called_once_with(500, target_vm=123)


def test_script_not_found(cli_runner, mock_client):
    """Test name resolution error for nonexistent script."""
    mock_client.task_scripts.list.return_value = []
    result = cli_runner.invoke(app, ["task", "script", "get", "nonexistent"])
    assert result.exit_code == 6
