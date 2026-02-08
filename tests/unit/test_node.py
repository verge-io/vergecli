"""Tests for node commands."""

from verge_cli.cli import app


def test_node_list(cli_runner, mock_client, mock_node):
    """vrg node list should list all nodes."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "node1" in result.output
    mock_client.nodes.list.assert_called_once()


def test_node_list_empty(cli_runner, mock_client):
    """vrg node list should handle empty results."""
    mock_client.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_node_list_with_cluster_filter(cli_runner, mock_client, mock_node):
    """vrg node list --cluster should filter by cluster name."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list", "--cluster", "Cluster1"])

    assert result.exit_code == 0
    assert "node1" in result.output
    call_kwargs = mock_client.nodes.list.call_args[1]
    assert call_kwargs["cluster"] == "Cluster1"


def test_node_list_json(cli_runner, mock_client, mock_node):
    """vrg node list --output json should output JSON."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["--output", "json", "node", "list"])

    assert result.exit_code == 0
    assert '"name": "node1"' in result.output


def test_node_get(cli_runner, mock_client, mock_node):
    """vrg node get should show node details."""
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "node1"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_get_by_key(cli_runner, mock_client, mock_node):
    """vrg node get by numeric key should work."""
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "10"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_maintenance_enable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --enable should enable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--enable"])

    assert result.exit_code == 0
    mock_client.nodes.enable_maintenance.assert_called_once_with(10)


def test_node_maintenance_disable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --disable should disable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--disable"])

    assert result.exit_code == 0
    mock_client.nodes.disable_maintenance.assert_called_once_with(10)


def test_node_maintenance_no_flag(cli_runner, mock_client, mock_node):
    """vrg node maintenance without --enable or --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1"])

    assert result.exit_code == 2


def test_node_maintenance_both_flags(cli_runner, mock_client, mock_node):
    """vrg node maintenance with both --enable and --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1", "--enable", "--disable"])

    assert result.exit_code == 2


def test_node_restart(cli_runner, mock_client, mock_node):
    """vrg node restart --yes should restart the node."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "restart", "node1", "--yes"])

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_called_once_with(10)


def test_node_restart_without_yes(cli_runner, mock_client, mock_node):
    """vrg node restart without --yes should prompt and abort on 'n'."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "restart", "node1"], input="n\n")

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_not_called()
