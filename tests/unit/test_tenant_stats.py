"""Tests for tenant stats and logs sub-resource commands."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_stats_current() -> MagicMock:
    """Create mock current stats data (TenantStats object)."""
    stats = MagicMock()
    stats.ram_used_mb = 4096
    stats.last_update = None
    stats.tenant_key = 5
    return stats


@pytest.fixture
def mock_stats_history_entry() -> MagicMock:
    """Create a mock TenantStatsHistory entry."""
    entry = MagicMock()
    entry.timestamp = MagicMock()
    entry.total_cpu = 45
    entry.ram_used_mb = 4096
    entry.ram_allocated_mb = 8192
    entry.core_count = 8
    entry.ram_pct = 50
    entry.vram_used_mb = 3500
    entry.ip_count = 10

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "timestamp": 1707300000,
            "total_cpu": 45,
            "ram_used_mb": 4096,
            "ram_allocated_mb": 8192,
            "core_count": 8,
            "ram_pct": 50,
        }
        return data.get(key, default)

    entry.get = mock_get
    return entry


@pytest.fixture
def mock_log_entry() -> MagicMock:
    """Create a mock log entry (TenantLog object)."""
    entry = MagicMock()
    entry.key = 100
    entry.level = "Message"
    entry.level_raw = "message"
    entry.text = "Tenant started successfully"
    entry.user = "admin"
    entry.timestamp = MagicMock()
    entry.timestamp.__str__ = lambda self: "2024-02-07 12:00:00"
    entry.is_error = False
    entry.is_warning = False

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "timestamp": "2024-02-07 12:00:00",
            "type": "message",
            "level": "Message",
            "text": "Tenant started successfully",
            "user": "admin",
            "message": "Tenant started successfully",
        }
        return data.get(key, default)

    entry.get = mock_get
    return entry


# ===== Stats Tests =====


def test_stats_current(cli_runner, mock_client, mock_tenant, mock_stats_current):
    """vrg tenant stats current should show current stats."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.get.return_value = mock_stats_current

    result = cli_runner.invoke(app, ["tenant", "stats", "current", "acme-corp"])

    assert result.exit_code == 0
    assert "ram_used_mb" in result.output or "4096" in result.output
    mock_tenant.stats.get.assert_called_once()


def test_stats_history(cli_runner, mock_client, mock_tenant, mock_stats_history_entry):
    """vrg tenant stats history should show stats history."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.history_short.return_value = [mock_stats_history_entry]

    result = cli_runner.invoke(app, ["tenant", "stats", "history", "acme-corp"])

    assert result.exit_code == 0
    mock_tenant.stats.history_short.assert_called_once()


def test_stats_history_with_limit(cli_runner, mock_client, mock_tenant, mock_stats_history_entry):
    """vrg tenant stats history should accept --limit."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.history_short.return_value = [mock_stats_history_entry]

    result = cli_runner.invoke(app, ["tenant", "stats", "history", "acme-corp", "--limit", "10"])

    assert result.exit_code == 0
    mock_tenant.stats.history_short.assert_called_once_with(limit=10)


# ===== Logs Tests =====


def test_logs_list(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should list log entries."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["tenant", "logs", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "Tenant started" in result.output
    mock_tenant.logs.list.assert_called_once()


def test_logs_list_with_limit(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should accept --limit."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["tenant", "logs", "list", "acme-corp", "--limit", "10"])

    assert result.exit_code == 0
    call_kwargs = mock_tenant.logs.list.call_args[1]
    assert call_kwargs["limit"] == 10


def test_logs_list_errors_only(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should accept --errors-only."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["tenant", "logs", "list", "acme-corp", "--errors-only"])

    assert result.exit_code == 0
    call_kwargs = mock_tenant.logs.list.call_args[1]
    assert call_kwargs["errors_only"] is True
