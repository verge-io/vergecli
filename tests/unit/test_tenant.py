"""Tests for tenant commands."""

from verge_cli.cli import app


def test_tenant_list(cli_runner, mock_client, mock_tenant):
    """vrg tenant list should list tenants."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.list.assert_called_once()


def test_tenant_list_empty(cli_runner, mock_client):
    """vrg tenant list with no tenants should show empty message."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_tenant_list_json(cli_runner, mock_client, mock_tenant):
    """vrg tenant list --output json should produce valid JSON."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["--output", "json", "tenant", "list"])

    assert result.exit_code == 0
    assert '"name": "acme-corp"' in result.output
    assert '"$key": 5' in result.output
    assert '"is_isolated": false' in result.output


def test_tenant_get(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should show tenant details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "acme-corp"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_by_key(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should accept numeric key."""
    mock_client.tenants.list.return_value = []
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "5"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_not_found(cli_runner, mock_client):
    """vrg tenant get with unknown name should exit 6."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "get", "nonexistent"])

    assert result.exit_code == 6
