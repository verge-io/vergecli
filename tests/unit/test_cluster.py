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


def test_cluster_create(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should create a new cluster."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "create", "--name", "Cluster1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.create.assert_called_once()


def test_cluster_create_with_options(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should accept all options."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        [
            "cluster",
            "create",
            "--name",
            "Cluster1",
            "--description",
            "Primary",
            "--enabled",
            "--compute",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.create.call_args[1]
    assert call_kwargs["name"] == "Cluster1"
    assert call_kwargs["description"] == "Primary"
    assert call_kwargs["enabled"] is True
    assert call_kwargs["compute"] is True


def test_cluster_create_no_name(cli_runner, mock_client):
    """vrg cluster create without --name should fail."""
    result = cli_runner.invoke(app, ["cluster", "create"])

    assert result.exit_code == 2


def test_cluster_update(cli_runner, mock_client, mock_cluster):
    """vrg cluster update should update a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.update.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        ["cluster", "update", "Cluster1", "--description", "Updated"],
    )

    assert result.exit_code == 0
    mock_client.clusters.update.assert_called_once()
    call_args = mock_client.clusters.update.call_args
    assert call_args[0][0] == 1  # key
    assert call_args[1]["description"] == "Updated"


def test_cluster_update_no_changes(cli_runner, mock_client, mock_cluster):
    """vrg cluster update with no options should fail."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "update", "Cluster1"])

    assert result.exit_code == 2


def test_cluster_delete(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete should delete a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "delete", "Cluster1", "--yes"])

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_called_once_with(1)


def test_cluster_delete_without_yes(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete without --yes should prompt and abort on 'n'."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "delete", "Cluster1"], input="n\n")

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_not_called()
