"""Tests for VM import and import log commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_vm_import_list(cli_runner, mock_client, mock_vm_import):
    """vrg vm import list should list all VM imports."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]

    result = cli_runner.invoke(app, ["vm", "import", "list"])

    assert result.exit_code == 0
    assert "ubuntu-import" in result.output
    mock_client.vm_imports.list.assert_called_once_with()


def test_vm_import_get(cli_runner, mock_client, mock_vm_import):
    """vrg vm import get should get an import by name."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]
    mock_client.vm_imports.get.return_value = mock_vm_import

    result = cli_runner.invoke(app, ["vm", "import", "get", "ubuntu-import"])

    assert result.exit_code == 0
    assert "ubuntu-import" in result.output


def test_vm_import_create(cli_runner, mock_client, mock_vm_import):
    """vrg vm import create should create an import job."""
    mock_client.vm_imports.create.return_value = mock_vm_import

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "import",
            "create",
            "--name",
            "ubuntu-import",
            "--file",
            "5",
            "--no-preserve-macs",
        ],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    call_kwargs = mock_client.vm_imports.create.call_args[1]
    assert call_kwargs["name"] == "ubuntu-import"
    assert call_kwargs["file"] == 5
    assert call_kwargs["preserve_macs"] is False


def test_vm_import_start(cli_runner, mock_client, mock_vm_import):
    """vrg vm import start should start an import."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]

    result = cli_runner.invoke(app, ["vm", "import", "start", "ubuntu-import"])

    assert result.exit_code == 0
    assert "started" in result.output.lower()
    mock_client.vm_imports.start_import.assert_called_once_with(
        "ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12"
    )


def test_vm_import_cancel(cli_runner, mock_client, mock_vm_import):
    """vrg vm import cancel should cancel an import."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]

    result = cli_runner.invoke(app, ["vm", "import", "cancel", "ubuntu-import"])

    assert result.exit_code == 0
    assert "cancelled" in result.output.lower()
    mock_client.vm_imports.abort_import.assert_called_once_with(
        "ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12"
    )


def test_vm_import_delete(cli_runner, mock_client, mock_vm_import):
    """vrg vm import delete --yes should delete an import."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]

    result = cli_runner.invoke(app, ["vm", "import", "delete", "ubuntu-import", "--yes"])

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.vm_imports.delete.assert_called_once_with(
        "ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12"
    )


def test_vm_import_not_found(cli_runner, mock_client):
    """vrg vm import get nonexistent should exit 6."""
    mock_client.vm_imports.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "import", "get", "nonexistent"])

    assert result.exit_code == 6


def test_vm_import_log_list(cli_runner, mock_client, mock_vm_import_log):
    """vrg vm import log list should list import logs."""
    mock_client.vm_import_logs.list.return_value = [mock_vm_import_log]

    result = cli_runner.invoke(app, ["vm", "import", "log", "list"])

    assert result.exit_code == 0
    assert "Import started" in result.output
    mock_client.vm_import_logs.list.assert_called_once_with()


def test_vm_import_log_list_filtered(cli_runner, mock_client, mock_vm_import, mock_vm_import_log):
    """vrg vm import log list --import should filter by import."""
    mock_client.vm_imports.list.return_value = [mock_vm_import]
    mock_client.vm_import_logs.list.return_value = [mock_vm_import_log]

    result = cli_runner.invoke(app, ["vm", "import", "log", "list", "--import", "ubuntu-import"])

    assert result.exit_code == 0
    mock_client.vm_import_logs.list.assert_called_once_with(
        vm_import="ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12"
    )


def test_vm_import_log_get(cli_runner, mock_client, mock_vm_import_log):
    """vrg vm import log get should get a log entry by key."""
    mock_client.vm_import_logs.get.return_value = mock_vm_import_log

    result = cli_runner.invoke(app, ["vm", "import", "log", "get", "500"])

    assert result.exit_code == 0
    assert "Import started" in result.output
    mock_client.vm_import_logs.get.assert_called_once_with(key=500)
