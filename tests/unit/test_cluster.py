"""Tests for cluster commands."""

from verge_cli.cli import app


def test_cluster_list(cli_runner, mock_client, mock_cluster):
    """vrg cluster list should list all clusters."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.list.assert_called_once()


def test_cluster_list_empty(cli_runner, mock_client):
    """vrg cluster list should handle empty results."""
    mock_client.clusters.list.return_value = []

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_cluster_list_json(cli_runner, mock_client, mock_cluster):
    """vrg cluster list --output json should output JSON."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["--output", "json", "cluster", "list"])

    assert result.exit_code == 0
    assert '"name": "Cluster1"' in result.output


def test_cluster_get(cli_runner, mock_client, mock_cluster):
    """vrg cluster get should show cluster details."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "Cluster1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output


def test_cluster_get_by_key(cli_runner, mock_client, mock_cluster):
    """vrg cluster get by numeric key should work."""
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
