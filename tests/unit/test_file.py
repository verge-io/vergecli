"""Tests for media catalog file commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app


@pytest.fixture
def mock_file() -> MagicMock:
    """Create a mock File object."""
    f = MagicMock()
    f.key = 1
    f.name = "ubuntu-22.04.iso"
    f.file_type = "iso"
    f.description = "Ubuntu 22.04 LTS"
    f.size_gb = 4.7
    f.allocated_gb = 5.0
    f.used_gb = 4.7
    f.preferred_tier = 1
    f.creator = "admin"
    f.modified = None
    f.size_bytes = 5046586573

    def mock_get(key: str, default: Any = None) -> Any:
        data: dict[str, Any] = {
            "$key": 1,
            "name": "ubuntu-22.04.iso",
            "type": "iso",
            "description": "Ubuntu 22.04 LTS",
            "filesize": 5046586573,
            "allocated_bytes": 5368709120,
            "used_bytes": 5046586573,
            "preferred_tier": 1,
            "creator": "admin",
            "modified": None,
        }
        return data.get(key, default)

    f.get = mock_get
    return f


class TestFileList:
    """Tests for the file list command."""

    def test_file_list(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """List all files, verify table output."""
        mock_client.files.list.return_value = [mock_file]

        result = cli_runner.invoke(app, ["file", "list"])

        assert result.exit_code == 0
        assert "ubuntu-22.04.iso" in result.output
        mock_client.files.list.assert_called_once()

    def test_file_list_type_filter(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """--type iso passes file_type to SDK."""
        mock_client.files.list.return_value = [mock_file]

        result = cli_runner.invoke(app, ["file", "list", "--type", "iso"])

        assert result.exit_code == 0
        mock_client.files.list.assert_called_once_with(file_type="iso")

    def test_file_list_empty(self, cli_runner: CliRunner, mock_client: MagicMock) -> None:
        """No files returns empty table."""
        mock_client.files.list.return_value = []

        result = cli_runner.invoke(app, ["file", "list"])

        assert result.exit_code == 0
        mock_client.files.list.assert_called_once()


class TestFileGet:
    """Tests for the file get command."""

    def test_file_get_by_name(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """Get file by name resolution."""
        mock_client.files.list.return_value = [mock_file]
        mock_client.files.get.return_value = mock_file

        result = cli_runner.invoke(app, ["file", "get", "ubuntu-22.04.iso"])

        assert result.exit_code == 0
        assert "ubuntu-22.04.iso" in result.output

    def test_file_get_by_key(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """Get file by numeric key."""
        mock_client.files.get.return_value = mock_file

        result = cli_runner.invoke(app, ["file", "get", "1"])

        assert result.exit_code == 0
        assert "ubuntu-22.04.iso" in result.output
        mock_client.files.get.assert_called_once_with(
            1,
            fields=[
                "$key",
                "name",
                "type",
                "description",
                "filesize",
                "allocated_bytes",
                "used_bytes",
                "preferred_tier",
                "modified",
                "creator",
            ],
        )

    def test_file_get_not_found(self, cli_runner: CliRunner, mock_client: MagicMock) -> None:
        """Nonexistent file returns exit code 6."""
        mock_client.files.list.return_value = []

        result = cli_runner.invoke(app, ["file", "get", "nonexistent"])

        assert result.exit_code == 6


class TestFileUpload:
    """Tests for the file upload command."""

    def test_file_upload(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock, tmp_path: Any
    ) -> None:
        """Upload file, verify SDK call with path."""
        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"fake iso content")
        mock_client.files.upload.return_value = mock_file

        result = cli_runner.invoke(app, ["file", "upload", str(test_file)])

        assert result.exit_code == 0
        mock_client.files.upload.assert_called_once()
        call_kwargs = mock_client.files.upload.call_args
        assert call_kwargs.kwargs.get("path") == str(test_file) or call_kwargs[1].get(
            "path"
        ) == str(test_file)

    def test_file_upload_with_options(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock, tmp_path: Any
    ) -> None:
        """Upload with --name, --description, --tier."""
        test_file = tmp_path / "test.iso"
        test_file.write_bytes(b"fake iso content")
        mock_client.files.upload.return_value = mock_file

        result = cli_runner.invoke(
            app,
            [
                "file",
                "upload",
                str(test_file),
                "--name",
                "custom-name.iso",
                "--description",
                "My ISO",
                "--tier",
                "2",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client.files.upload.call_args[1]
        assert call_kwargs["path"] == str(test_file)
        assert call_kwargs["name"] == "custom-name.iso"
        assert call_kwargs["description"] == "My ISO"
        assert call_kwargs["tier"] == 2

    def test_file_upload_file_not_found(
        self, cli_runner: CliRunner, mock_client: MagicMock
    ) -> None:
        """Local file doesn't exist, error before SDK call."""
        result = cli_runner.invoke(app, ["file", "upload", "/nonexistent/file.iso"])

        assert result.exit_code == 1
        mock_client.files.upload.assert_not_called()


class TestFileDownload:
    """Tests for the file download command."""

    def test_file_download(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_file: MagicMock,
        tmp_path: Any,
    ) -> None:
        """Download file, verify SDK call with key."""
        mock_client.files.get.return_value = mock_file
        mock_client.files.download.return_value = tmp_path / "ubuntu-22.04.iso"

        result = cli_runner.invoke(app, ["file", "download", "1"])

        assert result.exit_code == 0
        mock_client.files.download.assert_called_once()
        call_kwargs = mock_client.files.download.call_args[1]
        assert call_kwargs["key"] == 1

    def test_file_download_with_options(
        self,
        cli_runner: CliRunner,
        mock_client: MagicMock,
        mock_file: MagicMock,
        tmp_path: Any,
    ) -> None:
        """Download with --destination, --filename, --overwrite."""
        mock_client.files.get.return_value = mock_file
        mock_client.files.download.return_value = tmp_path / "custom.iso"

        result = cli_runner.invoke(
            app,
            [
                "file",
                "download",
                "1",
                "--destination",
                str(tmp_path),
                "--filename",
                "custom.iso",
                "--overwrite",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client.files.download.call_args[1]
        assert call_kwargs["key"] == 1
        assert call_kwargs["destination"] == str(tmp_path)
        assert call_kwargs["filename"] == "custom.iso"
        assert call_kwargs["overwrite"] is True


class TestFileDelete:
    """Tests for the file delete command."""

    def test_file_delete_confirmed(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """Delete with --yes skips confirmation."""
        mock_client.files.get.return_value = mock_file

        result = cli_runner.invoke(app, ["file", "delete", "1", "--yes"])

        assert result.exit_code == 0
        mock_client.files.delete.assert_called_once_with(1)


class TestFileUpdate:
    """Tests for the file update command."""

    def test_file_update(
        self, cli_runner: CliRunner, mock_client: MagicMock, mock_file: MagicMock
    ) -> None:
        """Update metadata (name, description, tier)."""
        mock_client.files.list.return_value = [mock_file]
        mock_client.files.update.return_value = mock_file

        result = cli_runner.invoke(
            app,
            [
                "file",
                "update",
                "ubuntu-22.04.iso",
                "--name",
                "ubuntu-22.04-updated.iso",
                "--description",
                "Updated description",
                "--tier",
                "3",
            ],
        )

        assert result.exit_code == 0
        mock_client.files.update.assert_called_once_with(
            1,
            name="ubuntu-22.04-updated.iso",
            description="Updated description",
            preferred_tier=3,
        )


class TestFileTypes:
    """Tests for the file types command."""

    def test_file_types(self, cli_runner: CliRunner, mock_client: MagicMock) -> None:
        """List supported file types, verify all 16 types in output."""
        result = cli_runner.invoke(app, ["file", "types"])

        assert result.exit_code == 0
        # Verify all 16 file types appear in output
        for type_key in [
            "iso",
            "img",
            "qcow",
            "qcow2",
            "qed",
            "raw",
            "vdi",
            "vhd",
            "vhdx",
            "vmdk",
            "ova",
            "ovf",
            "vmx",
            "ybvm",
            "nvram",
            "zip",
        ]:
            assert type_key in result.output
