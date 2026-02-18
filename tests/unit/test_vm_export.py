"""Tests for VM export and export stats commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_vm_export_list(cli_runner, mock_client, mock_vm_export):
    """vrg vm export list should list all VM exports."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(app, ["vm", "export", "list"])

    assert result.exit_code == 0
    assert "vm-exports" in result.output
    mock_client.volume_vm_exports.list.assert_called_once_with()


def test_vm_export_get(cli_runner, mock_client, mock_vm_export):
    """vrg vm export get should get an export by integer key."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]
    mock_client.volume_vm_exports.get.return_value = mock_vm_export

    result = cli_runner.invoke(app, ["vm", "export", "get", "10"])

    assert result.exit_code == 0
    assert "vm-exports" in result.output


def test_vm_export_create(cli_runner, mock_client, mock_vm_export):
    """vrg vm export create should create an export config."""
    mock_client.volume_vm_exports.create.return_value = mock_vm_export

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "export",
            "create",
            "--volume",
            "1",
            "--quiesced",
            "--max-exports",
            "5",
        ],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    call_kwargs = mock_client.volume_vm_exports.create.call_args[1]
    assert call_kwargs["volume"] == 1
    assert call_kwargs["quiesced"] is True
    assert call_kwargs["max_exports"] == 5


def test_vm_export_start(cli_runner, mock_client, mock_vm_export):
    """vrg vm export start should start an export by key."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(app, ["vm", "export", "start", "10"])

    assert result.exit_code == 0
    assert "started" in result.output.lower()
    mock_client.volume_vm_exports.start_export.assert_called_once_with(10)


def test_vm_export_start_with_name_and_vms(cli_runner, mock_client, mock_vm_export):
    """vrg vm export start --name --vms should pass name and VM list."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "export",
            "start",
            "10",
            "--name",
            "manual-run",
            "--vms",
            "1,2,3",
        ],
    )

    assert result.exit_code == 0
    mock_client.volume_vm_exports.start_export.assert_called_once_with(
        10, name="manual-run", vms=[1, 2, 3]
    )


def test_vm_export_stop(cli_runner, mock_client, mock_vm_export):
    """vrg vm export stop should stop an export."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(app, ["vm", "export", "stop", "10"])

    assert result.exit_code == 0
    assert "stopped" in result.output.lower()
    mock_client.volume_vm_exports.stop_export.assert_called_once_with(10)


def test_vm_export_delete(cli_runner, mock_client, mock_vm_export):
    """vrg vm export delete --yes should delete an export."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(app, ["vm", "export", "delete", "10", "--yes"])

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()


def test_vm_export_cleanup(cli_runner, mock_client, mock_vm_export):
    """vrg vm export cleanup should clean up exported files."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]

    result = cli_runner.invoke(app, ["vm", "export", "cleanup", "10"])

    assert result.exit_code == 0
    assert "cleaned up" in result.output.lower()
    mock_client.volume_vm_exports.cleanup_exports.assert_called_once_with(10)


def test_vm_export_not_found(cli_runner, mock_client):
    """vrg vm export get nonexistent should exit 6."""
    mock_client.volume_vm_exports.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "export", "get", "nonexistent"])

    assert result.exit_code == 6


def test_vm_export_stats_list(cli_runner, mock_client, mock_vm_export_stat):
    """vrg vm export stats list should list export stats."""
    mock_client.volume_vm_export_stats.list.return_value = [mock_vm_export_stat]

    result = cli_runner.invoke(app, ["vm", "export", "stats", "list"])

    assert result.exit_code == 0
    assert "backup-2026-02-18" in result.output
    mock_client.volume_vm_export_stats.list.assert_called_once_with()


def test_vm_export_stats_list_filtered(
    cli_runner, mock_client, mock_vm_export, mock_vm_export_stat
):
    """vrg vm export stats list --export should filter by export key."""
    mock_client.volume_vm_exports.list.return_value = [mock_vm_export]
    mock_client.volume_vm_export_stats.list.return_value = [mock_vm_export_stat]

    result = cli_runner.invoke(app, ["vm", "export", "stats", "list", "--export", "10"])

    assert result.exit_code == 0
    mock_client.volume_vm_export_stats.list.assert_called_once_with(volume_vm_exports=10)


def test_vm_export_stats_get(cli_runner, mock_client, mock_vm_export_stat):
    """vrg vm export stats get should get a stat entry by key."""
    mock_client.volume_vm_export_stats.get.return_value = mock_vm_export_stat

    result = cli_runner.invoke(app, ["vm", "export", "stats", "get", "100"])

    assert result.exit_code == 0
    assert "backup-2026-02-18" in result.output
    mock_client.volume_vm_export_stats.get.assert_called_once_with(key=100)
