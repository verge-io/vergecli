"""Tests for cluster commands."""

from unittest.mock import MagicMock

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


# --- vsan-status tests ---


def _make_mock_vsan_status(
    cluster_name: str = "Cluster1",
    health_status: str = "Healthy",
    total_nodes: int = 4,
    online_nodes: int = 4,
    used_ram_gb: float = 115.2,
    online_ram_gb: float = 256.0,
    ram_used_percent: float = 45.0,
    total_cores: int = 64,
    online_cores: int = 64,
    used_cores: int = 20,
    core_used_percent: float = 31.3,
    running_machines: int = 20,
    tiers: list | None = None,
) -> MagicMock:
    """Create a mock VSANStatus object."""
    status = MagicMock()
    status.key = 1
    status.cluster_name = cluster_name
    status.health_status = health_status
    status.total_nodes = total_nodes
    status.online_nodes = online_nodes
    status.used_ram_gb = used_ram_gb
    status.online_ram_gb = online_ram_gb
    status.ram_used_percent = ram_used_percent
    status.total_cores = total_cores
    status.online_cores = online_cores
    status.used_cores = used_cores
    status.core_used_percent = core_used_percent
    status.running_machines = running_machines
    status.tiers = tiers or []
    return status


def test_cluster_vsan_status(cli_runner, mock_client):
    """vrg cluster vsan-status should show vSAN health."""
    mock_status = _make_mock_vsan_status()
    mock_client.clusters.vsan_status.return_value = [mock_status]

    result = cli_runner.invoke(app, ["cluster", "vsan-status"])

    assert result.exit_code == 0
    assert "Healthy" in result.output
    assert "Cluster1" in result.output
    mock_client.clusters.vsan_status.assert_called_once()


def test_cluster_vsan_status_with_name(cli_runner, mock_client):
    """vrg cluster vsan-status --name should pass cluster name."""
    mock_status = _make_mock_vsan_status()
    mock_client.clusters.vsan_status.return_value = [mock_status]

    result = cli_runner.invoke(app, ["cluster", "vsan-status", "--name", "Cluster1"])

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["cluster_name"] == "Cluster1"


def test_cluster_vsan_status_with_tiers(cli_runner, mock_client):
    """vrg cluster vsan-status --include-tiers should pass flag."""
    mock_status = _make_mock_vsan_status(
        tiers=[{"tier": 1, "status": "online", "used_percent": 60.0}],
    )
    mock_client.clusters.vsan_status.return_value = [mock_status]

    result = cli_runner.invoke(app, ["cluster", "vsan-status", "--include-tiers"])

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["include_tiers"] is True


def test_cluster_vsan_status_json(cli_runner, mock_client):
    """vrg cluster vsan-status with JSON output."""
    mock_status = _make_mock_vsan_status()
    mock_client.clusters.vsan_status.return_value = [mock_status]

    result = cli_runner.invoke(app, ["--output", "json", "cluster", "vsan-status"])

    assert result.exit_code == 0
    assert '"health_status": "Healthy"' in result.output


def test_cluster_vsan_status_empty(cli_runner, mock_client):
    """vrg cluster vsan-status should handle empty results."""
    mock_client.clusters.vsan_status.return_value = []

    result = cli_runner.invoke(app, ["cluster", "vsan-status"])

    assert result.exit_code == 0
    assert "No results" in result.output
