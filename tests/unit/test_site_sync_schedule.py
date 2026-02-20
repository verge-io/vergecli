"""Tests for site sync schedule management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from verge_cli.cli import app


def _mock_schedule() -> MagicMock:
    """Create a mock SiteSyncSchedule object."""
    schedule = MagicMock()
    schedule.key = 500
    schedule.name = "daily-sync"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 500,
            "sync_key": 800,
            "sync_name": "prod-to-backup",
            "profile_period_key": 10,
            "profile_period_name": "daily",
            "retention": 604800,
            "priority": 1,
            "do_not_expire": False,
            "destination_prefix": "remote",
        }
        return data.get(key, default)

    schedule.get = mock_get
    return schedule


def test_schedule_list(cli_runner, mock_client):
    """vrg site sync schedule list should list all schedules."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.list.return_value = [mock]

    result = cli_runner.invoke(app, ["site", "sync", "schedule", "list"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output
    mock_client.site_sync_schedules.list.assert_called_once_with()


def test_schedule_list_by_sync(cli_runner, mock_client):
    """vrg site sync schedule list --sync should filter by sync key."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.list.return_value = [mock]

    result = cli_runner.invoke(app, ["site", "sync", "schedule", "list", "--sync", "800"])

    assert result.exit_code == 0
    mock_client.site_sync_schedules.list.assert_called_once_with(sync_key=800)


def test_schedule_list_by_sync_name(cli_runner, mock_client):
    """vrg site sync schedule list --sync should accept sync name."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.list.return_value = [mock]

    result = cli_runner.invoke(
        app, ["site", "sync", "schedule", "list", "--sync", "prod-to-backup"]
    )

    assert result.exit_code == 0
    mock_client.site_sync_schedules.list.assert_called_once_with(sync_name="prod-to-backup")


def test_schedule_get(cli_runner, mock_client):
    """vrg site sync schedule get should get schedule details."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.get.return_value = mock

    result = cli_runner.invoke(app, ["site", "sync", "schedule", "get", "500"])

    assert result.exit_code == 0
    assert "prod-to-backup" in result.output
    mock_client.site_sync_schedules.get.assert_called_once_with(500)


def test_schedule_create(cli_runner, mock_client):
    """vrg site sync schedule create should create a schedule."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.create.return_value = mock

    result = cli_runner.invoke(
        app,
        [
            "site",
            "sync",
            "schedule",
            "create",
            "--sync-key",
            "800",
            "--profile-period-key",
            "10",
            "--retention",
            "604800",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.site_sync_schedules.create.assert_called_once_with(
        sync_key=800,
        profile_period_key=10,
        retention=604800,
        do_not_expire=False,
        destination_prefix="remote",
    )


def test_schedule_create_with_priority(cli_runner, mock_client):
    """vrg site sync schedule create --priority should set priority."""
    mock = _mock_schedule()
    mock_client.site_sync_schedules.create.return_value = mock

    result = cli_runner.invoke(
        app,
        [
            "site",
            "sync",
            "schedule",
            "create",
            "--sync-key",
            "800",
            "--profile-period-key",
            "10",
            "--retention",
            "604800",
            "--priority",
            "5",
        ],
    )

    assert result.exit_code == 0
    mock_client.site_sync_schedules.create.assert_called_once_with(
        sync_key=800,
        profile_period_key=10,
        retention=604800,
        do_not_expire=False,
        destination_prefix="remote",
        priority=5,
    )


def test_schedule_delete(cli_runner, mock_client):
    """vrg site sync schedule delete --yes should delete a schedule."""
    result = cli_runner.invoke(app, ["site", "sync", "schedule", "delete", "500", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.site_sync_schedules.delete.assert_called_once_with(500)


def test_schedule_delete_cancel(cli_runner, mock_client):
    """vrg site sync schedule delete should cancel without --yes."""
    result = cli_runner.invoke(app, ["site", "sync", "schedule", "delete", "500"], input="n\n")

    assert result.exit_code == 0
    mock_client.site_sync_schedules.delete.assert_not_called()
