"""Tests for storage tier commands."""

from verge_cli.cli import app


def test_storage_list(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list should list all storage tiers."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.list.assert_called_once()


def test_storage_list_empty(cli_runner, mock_client):
    """vrg storage list should handle empty results."""
    mock_client.storage_tiers.list.return_value = []

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_storage_list_json(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list --output json should output JSON."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["--output", "json", "storage", "list"])

    assert result.exit_code == 0
    assert '"description": "SSD Storage"' in result.output


def test_storage_get(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get should show tier details."""
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "1"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.get.assert_called_once_with(tier=1)


def test_storage_get_by_name(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get by name should resolve and show details."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "Tier 1 - SSD"])

    assert result.exit_code == 0
    assert "SSD" in result.output


def test_storage_summary(cli_runner, mock_client):
    """vrg storage summary should show aggregate storage data."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
        "tier_count": 2,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(app, ["storage", "summary"])

    assert result.exit_code == 0
    assert "20480" in result.output
    mock_client.storage_tiers.get_summary.assert_called_once()


def test_storage_summary_json(cli_runner, mock_client):
    """vrg storage summary with JSON output."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(app, ["--output", "json", "storage", "summary"])

    assert result.exit_code == 0
    assert '"total_capacity_gb": 20480' in result.output
