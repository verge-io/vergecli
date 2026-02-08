"""Tests for snapshot profile commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_snapshot_profile() -> MagicMock:
    """Create a mock SnapshotProfile object."""
    profile = MagicMock()
    profile.key = 800
    profile.name = "daily-backup"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 800,
            "name": "daily-backup",
            "description": "Daily backup profile",
        }
        return data.get(key, default)

    profile.get = mock_get
    return profile


def test_profile_list(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile list should list all profiles."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]

    result = cli_runner.invoke(app, ["snapshot", "profile", "list"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_client.snapshot_profiles.list.assert_called_once()


def test_profile_list_empty(cli_runner, mock_client):
    """vrg snapshot profile list should handle empty list."""
    mock_client.snapshot_profiles.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "profile", "list"])

    assert result.exit_code == 0


def test_profile_get(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile get should resolve by name."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    mock_client.snapshot_profiles.get.return_value = mock_snapshot_profile

    result = cli_runner.invoke(app, ["snapshot", "profile", "get", "daily-backup"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output


def test_profile_get_by_key(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile get should accept numeric key."""
    mock_client.snapshot_profiles.get.return_value = mock_snapshot_profile

    result = cli_runner.invoke(app, ["snapshot", "profile", "get", "800"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_client.snapshot_profiles.get.assert_called_once_with(800)


def test_profile_create(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile create should create with name."""
    mock_client.snapshot_profiles.create.return_value = mock_snapshot_profile

    result = cli_runner.invoke(
        app,
        ["snapshot", "profile", "create", "--name", "daily-backup"],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.snapshot_profiles.create.assert_called_once_with(name="daily-backup")


def test_profile_create_with_description(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile create should accept --description."""
    mock_client.snapshot_profiles.create.return_value = mock_snapshot_profile

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "create",
            "--name",
            "daily-backup",
            "--description",
            "Daily backup profile",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.snapshot_profiles.create.assert_called_once_with(
        name="daily-backup", description="Daily backup profile"
    )


def test_profile_update(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile update should update name and description."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "update",
            "daily-backup",
            "--name",
            "weekly-backup",
            "--description",
            "Weekly backup profile",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    mock_client.snapshot_profiles.update.assert_called_once_with(
        800, name="weekly-backup", description="Weekly backup profile"
    )


def test_profile_delete(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile delete should delete with --yes."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]

    result = cli_runner.invoke(app, ["snapshot", "profile", "delete", "daily-backup", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.snapshot_profiles.delete.assert_called_once_with(800)


def test_profile_not_found(cli_runner, mock_client):
    """vrg snapshot profile get with unknown name should exit 6."""
    mock_client.snapshot_profiles.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "profile", "get", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
