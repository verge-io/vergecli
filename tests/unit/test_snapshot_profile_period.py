"""Tests for snapshot profile period commands."""

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


@pytest.fixture
def mock_snapshot_profile_period() -> MagicMock:
    """Create a mock SnapshotProfilePeriod object."""
    period = MagicMock()
    period.key = 900
    period.name = "daily-midnight"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 900,
            "name": "daily-midnight",
            "frequency": "daily",
            "retention": 604800,
            "min_snapshots": 1,
            "max_tier": 1,
            "minute": 0,
            "hour": 0,
            "day_of_week": "any",
            "quiesce": False,
            "immutable": False,
            "skip_missed": False,
        }
        return data.get(key, default)

    period.get = mock_get
    return period


def test_period_list(cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period):
    """vrg snapshot profile period list should list periods for a profile."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    mock_client.snapshot_profiles.periods.return_value.list.return_value = [
        mock_snapshot_profile_period
    ]

    result = cli_runner.invoke(app, ["snapshot", "profile", "period", "list", "daily-backup"])

    assert result.exit_code == 0
    assert "daily-midnight" in result.output
    mock_client.snapshot_profiles.periods.assert_called_once_with(800)


def test_period_list_empty(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile period list should handle empty list."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    mock_client.snapshot_profiles.periods.return_value.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "profile", "period", "list", "daily-backup"])

    assert result.exit_code == 0


def test_period_get(cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period):
    """vrg snapshot profile period get should resolve period by name."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.list.return_value = [mock_snapshot_profile_period]
    period_mgr.get.return_value = mock_snapshot_profile_period

    result = cli_runner.invoke(
        app, ["snapshot", "profile", "period", "get", "daily-backup", "daily-midnight"]
    )

    assert result.exit_code == 0
    assert "daily-midnight" in result.output


def test_period_get_by_key(
    cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period
):
    """vrg snapshot profile period get should accept numeric key."""
    mock_client.snapshot_profiles.get.return_value = mock_snapshot_profile
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.get.return_value = mock_snapshot_profile_period

    result = cli_runner.invoke(app, ["snapshot", "profile", "period", "get", "800", "900"])

    assert result.exit_code == 0
    assert "daily-midnight" in result.output
    period_mgr.get.assert_called_once_with(900)


def test_period_create_daily(
    cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period
):
    """vrg snapshot profile period create should create a daily period."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.create.return_value = mock_snapshot_profile_period

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "period",
            "create",
            "daily-backup",
            "--name",
            "daily-midnight",
            "--frequency",
            "daily",
            "--retention",
            "604800",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    period_mgr.create.assert_called_once_with(
        name="daily-midnight",
        frequency="daily",
        retention=604800,
        minute=0,
        hour=0,
        day_of_week="any",
        day_of_month=0,
        quiesce=False,
        immutable=False,
        min_snapshots=1,
        max_tier=1,
        skip_missed=False,
    )


def test_period_create_hourly_with_options(
    cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period
):
    """vrg snapshot profile period create should accept schedule options."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.create.return_value = mock_snapshot_profile_period

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "period",
            "create",
            "daily-backup",
            "--name",
            "hourly-30",
            "--frequency",
            "hourly",
            "--retention",
            "86400",
            "--minute",
            "30",
            "--quiesce",
            "--immutable",
            "--min-snapshots",
            "2",
            "--max-tier",
            "3",
            "--skip-missed",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    period_mgr.create.assert_called_once_with(
        name="hourly-30",
        frequency="hourly",
        retention=86400,
        minute=30,
        hour=0,
        day_of_week="any",
        day_of_month=0,
        quiesce=True,
        immutable=True,
        min_snapshots=2,
        max_tier=3,
        skip_missed=True,
    )


def test_period_update(
    cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period
):
    """vrg snapshot profile period update should update period options."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.list.return_value = [mock_snapshot_profile_period]

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "period",
            "update",
            "daily-backup",
            "daily-midnight",
            "--retention",
            "1209600",
            "--hour",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "Updated" in result.output
    period_mgr.update.assert_called_once_with(900, retention=1209600, hour=3)


def test_period_delete(
    cli_runner, mock_client, mock_snapshot_profile, mock_snapshot_profile_period
):
    """vrg snapshot profile period delete should delete with --yes."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.list.return_value = [mock_snapshot_profile_period]

    result = cli_runner.invoke(
        app,
        [
            "snapshot",
            "profile",
            "period",
            "delete",
            "daily-backup",
            "daily-midnight",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert "Deleted" in result.output
    period_mgr.delete.assert_called_once_with(900)


def test_period_not_found(cli_runner, mock_client, mock_snapshot_profile):
    """vrg snapshot profile period get with unknown period should exit 6."""
    mock_client.snapshot_profiles.list.return_value = [mock_snapshot_profile]
    period_mgr = mock_client.snapshot_profiles.periods.return_value
    period_mgr.list.return_value = []

    result = cli_runner.invoke(
        app,
        ["snapshot", "profile", "period", "get", "daily-backup", "nonexistent"],
    )

    assert result.exit_code == 6
    assert "not found" in result.output.lower()


def test_period_profile_not_found(cli_runner, mock_client):
    """vrg snapshot profile period list with unknown profile should exit 6."""
    mock_client.snapshot_profiles.list.return_value = []

    result = cli_runner.invoke(app, ["snapshot", "profile", "period", "list", "nonexistent"])

    assert result.exit_code == 6
    assert "not found" in result.output.lower()
