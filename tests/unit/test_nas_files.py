"""Tests for NAS volume file browser commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app
from verge_cli.commands.nas_files import _format_size


def test_files_list(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_nas_file: dict[str, Any],
    mock_nas_dir: dict[str, Any],
) -> None:
    """List files in root directory."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.list.return_value = [mock_nas_file, mock_nas_dir]
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    # Resolve volume by name
    mock_vol = MagicMock()
    mock_vol.key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    mock_vol.name = "data-vol"
    mock_client.nas_volumes.list.return_value = [mock_vol]

    result = cli_runner.invoke(app, ["nas", "files", "list", "data-vol"])
    assert result.exit_code == 0
    assert "report.txt" in result.output
    assert "documents" in result.output
    mock_client.nas_volumes.files.assert_called_once_with(
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )
    mock_file_mgr.list.assert_called_once_with(path="/")


def test_files_list_subdir(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_nas_file: dict[str, Any],
) -> None:
    """List files with --path /subdir."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.list.return_value = [mock_nas_file]
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    # Use hex key directly (no name resolution needed)
    vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    result = cli_runner.invoke(app, ["nas", "files", "list", vol_key, "--path", "/subdir"])
    assert result.exit_code == 0
    assert "report.txt" in result.output
    mock_file_mgr.list.assert_called_once_with(path="/subdir")


def test_files_list_with_extensions(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_nas_file: dict[str, Any],
) -> None:
    """Filter by --extensions txt,log."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.list.return_value = [mock_nas_file]
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    result = cli_runner.invoke(app, ["nas", "files", "list", vol_key, "--extensions", "txt,log"])
    assert result.exit_code == 0
    assert "report.txt" in result.output
    mock_file_mgr.list.assert_called_once_with(path="/", extensions="txt,log")


def test_files_list_empty(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Handles empty directory."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.list.return_value = []
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    result = cli_runner.invoke(app, ["nas", "files", "list", vol_key])
    assert result.exit_code == 0


def test_files_get_file(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_nas_file: dict[str, Any],
) -> None:
    """Get details of a specific file."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.get.return_value = mock_nas_file
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    result = cli_runner.invoke(app, ["nas", "files", "get", vol_key, "/report.txt"])
    assert result.exit_code == 0
    assert "report.txt" in result.output
    mock_file_mgr.get.assert_called_once_with(path="/report.txt")


def test_files_get_directory(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_nas_dir: dict[str, Any],
) -> None:
    """Get details of a directory."""
    mock_file_mgr = MagicMock()
    mock_file_mgr.get.return_value = mock_nas_dir
    mock_client.nas_volumes.files.return_value = mock_file_mgr

    vol_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    result = cli_runner.invoke(app, ["nas", "files", "get", vol_key, "/documents"])
    assert result.exit_code == 0
    assert "documents" in result.output
    mock_file_mgr.get.assert_called_once_with(path="/documents")


def test_files_volume_not_found(
    cli_runner: CliRunner,
    mock_client: MagicMock,
) -> None:
    """Volume resolution error (exit 6)."""
    mock_client.nas_volumes.list.return_value = []

    result = cli_runner.invoke(app, ["nas", "files", "list", "nonexistent"])
    assert result.exit_code == 6


def test_format_size() -> None:
    """Size formatting helper (B, KB, MB, GB, TB)."""
    assert _format_size(0) == "0 B"
    assert _format_size(512) == "512 B"
    assert _format_size(1024) == "1.0 KB"
    assert _format_size(1048576) == "1.0 MB"
    assert _format_size(1073741824) == "1.0 GB"
    assert _format_size(1099511627776) == "1.0 TB"
