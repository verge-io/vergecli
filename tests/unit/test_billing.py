"""Tests for billing commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_billing_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_billing_record: MagicMock
) -> None:
    """Test listing billing records."""
    mock_client.billing.list.return_value = [mock_billing_record]

    result = cli_runner.invoke(app, ["billing", "list"])

    assert result.exit_code == 0
    assert "1" in result.output  # key
    assert "8" in result.output  # used_cores
    mock_client.billing.list.assert_called_once_with()


def test_billing_list_with_since_until(
    cli_runner: CliRunner, mock_client: MagicMock, mock_billing_record: MagicMock
) -> None:
    """Test listing billing records with date filters."""
    mock_client.billing.list.return_value = [mock_billing_record]

    result = cli_runner.invoke(
        app, ["billing", "list", "--since", "2026-01-01", "--until", "2026-02-01"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.billing.list.call_args[1]
    assert "since" in call_kwargs
    assert "until" in call_kwargs


def test_billing_list_with_limit(
    cli_runner: CliRunner, mock_client: MagicMock, mock_billing_record: MagicMock
) -> None:
    """Test listing billing records with limit."""
    mock_client.billing.list.return_value = [mock_billing_record]

    result = cli_runner.invoke(app, ["billing", "list", "--limit", "10"])

    assert result.exit_code == 0
    mock_client.billing.list.assert_called_once_with(limit=10)


def test_billing_get(
    cli_runner: CliRunner, mock_client: MagicMock, mock_billing_record: MagicMock
) -> None:
    """Test getting a billing record by key."""
    mock_client.billing.get.return_value = mock_billing_record

    result = cli_runner.invoke(app, ["billing", "get", "1"])

    assert result.exit_code == 0
    assert "Billing record" in result.output
    mock_client.billing.get.assert_called_once_with(1)


def test_billing_generate(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test generating a billing record with --yes."""
    mock_client.billing.generate.return_value = None

    result = cli_runner.invoke(app, ["billing", "generate", "--yes"])

    assert result.exit_code == 0
    assert "generated" in result.output.lower()
    mock_client.billing.generate.assert_called_once()


def test_billing_generate_no_confirm(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test generating a billing record without --yes aborts."""
    result = cli_runner.invoke(app, ["billing", "generate"], input="n\n")

    assert result.exit_code == 0
    mock_client.billing.generate.assert_not_called()


def test_billing_latest(
    cli_runner: CliRunner, mock_client: MagicMock, mock_billing_record: MagicMock
) -> None:
    """Test getting the latest billing record."""
    mock_client.billing.get_latest.return_value = mock_billing_record

    result = cli_runner.invoke(app, ["billing", "latest"])

    assert result.exit_code == 0
    assert "16" in result.output  # used_ram_gb or total_cores
    mock_client.billing.get_latest.assert_called_once()


def test_billing_summary(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test billing summary."""
    mock_summary = MagicMock()
    mock_summary.record_count = 30
    mock_summary.avg_cpu_utilization = 45.5
    mock_summary.peak_cpu_cores = 12
    mock_summary.avg_ram_utilization = 62.3
    mock_summary.peak_ram_gb = 28.0
    mock_summary.avg_storage_used_gb = 450.0
    mock_summary.peak_storage_used_gb = 520.0
    mock_client.billing.get_summary.return_value = mock_summary

    result = cli_runner.invoke(app, ["billing", "summary"])

    assert result.exit_code == 0
    assert "30" in result.output  # record_count
    mock_client.billing.get_summary.assert_called_once_with()


def test_billing_summary_with_dates(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test billing summary with date filters."""
    mock_summary = MagicMock()
    mock_summary.record_count = 10
    mock_summary.avg_cpu_utilization = 50.0
    mock_summary.peak_cpu_cores = 8
    mock_summary.avg_ram_utilization = 60.0
    mock_summary.peak_ram_gb = 24.0
    mock_summary.avg_storage_used_gb = 400.0
    mock_summary.peak_storage_used_gb = 480.0
    mock_client.billing.get_summary.return_value = mock_summary

    result = cli_runner.invoke(
        app, ["billing", "summary", "--since", "2026-01-01", "--until", "2026-02-01"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.billing.get_summary.call_args[1]
    assert "since" in call_kwargs
    assert "until" in call_kwargs
