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


def test_tenant_create(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should create a tenant."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "create", "--name", "acme-corp", "--description", "ACME Corp"],
    )

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.create.assert_called_once()
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["description"] == "ACME Corp"


def test_tenant_create_with_password(cli_runner, mock_client, mock_tenant):
    """vrg tenant create with --password should pass password to SDK."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--password",
            "s3cret!",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["password"] == "s3cret!"


def test_tenant_create_all_options(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should accept all optional flags."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--description",
            "ACME Corp",
            "--password",
            "pass123",
            "--url",
            "acme.verge.local",
            "--note",
            "Production",
            "--expose-cloud-snapshots",
            "--allow-branding",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["url"] == "acme.verge.local"
    assert call_kwargs["note"] == "Production"
    assert call_kwargs["expose_cloud_snapshots"] is True
    assert call_kwargs["allow_branding"] is True


def test_tenant_create_no_name(cli_runner, mock_client):
    """vrg tenant create without --name should fail."""
    result = cli_runner.invoke(app, ["tenant", "create"])

    assert result.exit_code == 2


def test_tenant_update(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should update tenant properties."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "update", "acme-corp", "--description", "Updated ACME"],
    )

    assert result.exit_code == 0
    mock_client.tenants.update.assert_called_once()
    call_args = mock_client.tenants.update.call_args
    assert call_args[0][0] == 5  # key
    assert call_args[1]["description"] == "Updated ACME"


def test_tenant_update_no_changes(cli_runner, mock_client, mock_tenant):
    """vrg tenant update with no options should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "update", "acme-corp"])

    assert result.exit_code == 2
    assert "No updates" in result.output


def test_tenant_update_multiple_fields(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should accept multiple fields."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "update",
            "acme-corp",
            "--name",
            "acme-new",
            "--url",
            "new.verge.local",
            "--no-expose-cloud-snapshots",
        ],
    )

    assert result.exit_code == 0
    call_args = mock_client.tenants.update.call_args
    assert call_args[1]["name"] == "acme-new"
    assert call_args[1]["url"] == "new.verge.local"
    assert call_args[1]["expose_cloud_snapshots"] is False


def test_tenant_delete(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete should delete a tenant."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_cancelled(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete without --yes should prompt and cancel."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp"], input="n\n")

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_not_called()


def test_tenant_delete_force_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete --force should delete running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes", "--force"])

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_running_no_force(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete of running tenant without --force should fail."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 7
    mock_client.tenants.delete.assert_not_called()


def test_tenant_start(cli_runner, mock_client, mock_tenant):
    """vrg tenant start should power on a tenant."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_on.assert_called_once_with(5)


def test_tenant_start_already_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant start on running tenant should show message."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    assert "already running" in result.output
    mock_client.tenants.power_on.assert_not_called()


def test_tenant_stop(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop should power off a tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_off.assert_called_once_with(5)


def test_tenant_stop_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop on stopped tenant should show message."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    assert "not running" in result.output
    mock_client.tenants.power_off.assert_not_called()


def test_tenant_restart(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart should restart a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.restart.assert_called_once_with(5)


def test_tenant_restart_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.restart.assert_not_called()


def test_tenant_reset(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset should hard reset a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.reset.assert_called_once_with(5)


def test_tenant_reset_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.reset.assert_not_called()
