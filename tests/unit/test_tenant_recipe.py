"""Tests for tenant recipe, instance, and log commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_tenant_recipe_list(cli_runner, mock_client, mock_tenant_recipe):
    """vrg tenant-recipe list should list all tenant recipes."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]

    result = cli_runner.invoke(app, ["tenant-recipe", "list"])

    assert result.exit_code == 0
    assert "Standard Tenant" in result.output
    mock_client.tenant_recipes.list.assert_called_once_with()


def test_tenant_recipe_get(cli_runner, mock_client, mock_tenant_recipe):
    """vrg tenant-recipe get should get a recipe by name."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]
    mock_client.tenant_recipes.get.return_value = mock_tenant_recipe

    result = cli_runner.invoke(app, ["tenant-recipe", "get", "Standard Tenant"])

    assert result.exit_code == 0
    assert "Standard Tenant" in result.output


def test_tenant_recipe_update(cli_runner, mock_client, mock_tenant_recipe):
    """vrg tenant-recipe update should update a recipe."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]
    mock_client.tenant_recipes.update.return_value = mock_tenant_recipe

    result = cli_runner.invoke(
        app,
        [
            "tenant-recipe",
            "update",
            "Standard Tenant",
            "--description",
            "Updated desc",
        ],
    )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_tenant_recipe_delete(cli_runner, mock_client, mock_tenant_recipe):
    """vrg tenant-recipe delete --yes should delete a recipe."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]

    result = cli_runner.invoke(app, ["tenant-recipe", "delete", "Standard Tenant", "--yes"])

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.tenant_recipes.delete.assert_called_once_with(
        "cc11dd22ee33ff44cc11dd22ee33ff44cc11dd22"
    )


def test_tenant_recipe_download(cli_runner, mock_client, mock_tenant_recipe):
    """vrg tenant-recipe download should download a recipe."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]

    result = cli_runner.invoke(app, ["tenant-recipe", "download", "Standard Tenant"])

    assert result.exit_code == 0
    assert "downloaded" in result.output.lower()
    mock_client.tenant_recipes.download.assert_called_once_with(
        "cc11dd22ee33ff44cc11dd22ee33ff44cc11dd22"
    )


def test_tenant_recipe_deploy(
    cli_runner, mock_client, mock_tenant_recipe, mock_tenant_recipe_instance
):
    """vrg tenant-recipe deploy should deploy with --name and --set."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]
    mock_client.tenant_recipes.deploy.return_value = mock_tenant_recipe_instance

    result = cli_runner.invoke(
        app,
        [
            "tenant-recipe",
            "deploy",
            "Standard Tenant",
            "--name",
            "acme-tenant",
            "--set",
            "ADMIN_USER=admin",
            "--set",
            "ADMIN_PASS=secret123",
        ],
    )

    assert result.exit_code == 0
    assert "deployed" in result.output.lower()
    mock_client.tenant_recipes.deploy.assert_called_once_with(
        "cc11dd22ee33ff44cc11dd22ee33ff44cc11dd22",
        "acme-tenant",
        answers={"ADMIN_USER": "admin", "ADMIN_PASS": "secret123"},
    )


def test_tenant_recipe_not_found(cli_runner, mock_client):
    """vrg tenant-recipe get nonexistent should exit 6."""
    mock_client.tenant_recipes.list.return_value = []

    result = cli_runner.invoke(app, ["tenant-recipe", "get", "nonexistent"])

    assert result.exit_code == 6


def test_tenant_recipe_instance_list(cli_runner, mock_client, mock_tenant_recipe_instance):
    """vrg tenant-recipe instance list should list instances."""
    mock_client.tenant_recipe_instances.list.return_value = [mock_tenant_recipe_instance]

    result = cli_runner.invoke(app, ["tenant-recipe", "instance", "list"])

    assert result.exit_code == 0
    assert "acme-tenant" in result.output
    mock_client.tenant_recipe_instances.list.assert_called_once_with()


def test_tenant_recipe_instance_list_filtered(
    cli_runner, mock_client, mock_tenant_recipe, mock_tenant_recipe_instance
):
    """vrg tenant-recipe instance list --recipe should filter by recipe."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]
    mock_client.tenant_recipe_instances.list.return_value = [mock_tenant_recipe_instance]

    result = cli_runner.invoke(
        app, ["tenant-recipe", "instance", "list", "--recipe", "Standard Tenant"]
    )

    assert result.exit_code == 0
    mock_client.tenant_recipe_instances.list.assert_called_once_with(
        recipe="cc11dd22ee33ff44cc11dd22ee33ff44cc11dd22"
    )


def test_tenant_recipe_instance_get(cli_runner, mock_client, mock_tenant_recipe_instance):
    """vrg tenant-recipe instance get should get an instance by name."""
    mock_client.tenant_recipe_instances.list.return_value = [mock_tenant_recipe_instance]
    mock_client.tenant_recipe_instances.get.return_value = mock_tenant_recipe_instance

    result = cli_runner.invoke(app, ["tenant-recipe", "instance", "get", "acme-tenant"])

    assert result.exit_code == 0
    assert "acme-tenant" in result.output


def test_tenant_recipe_instance_delete(cli_runner, mock_client, mock_tenant_recipe_instance):
    """vrg tenant-recipe instance delete --yes should delete an instance."""
    mock_client.tenant_recipe_instances.list.return_value = [mock_tenant_recipe_instance]

    result = cli_runner.invoke(app, ["tenant-recipe", "instance", "delete", "acme-tenant", "--yes"])

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()


def test_tenant_recipe_log_list(cli_runner, mock_client, mock_tenant_recipe_log):
    """vrg tenant-recipe log list should list logs."""
    mock_client.tenant_recipe_logs.list.return_value = [mock_tenant_recipe_log]

    result = cli_runner.invoke(app, ["tenant-recipe", "log", "list"])

    assert result.exit_code == 0
    assert "Tenant recipe deployed successfully" in result.output
    mock_client.tenant_recipe_logs.list.assert_called_once_with()


def test_tenant_recipe_log_list_filtered(
    cli_runner, mock_client, mock_tenant_recipe, mock_tenant_recipe_log
):
    """vrg tenant-recipe log list --recipe should filter by recipe."""
    mock_client.tenant_recipes.list.return_value = [mock_tenant_recipe]
    mock_client.tenant_recipe_logs.list.return_value = [mock_tenant_recipe_log]

    result = cli_runner.invoke(app, ["tenant-recipe", "log", "list", "--recipe", "Standard Tenant"])

    assert result.exit_code == 0
    mock_client.tenant_recipe_logs.list.assert_called_once_with(
        tenant_recipe="cc11dd22ee33ff44cc11dd22ee33ff44cc11dd22"
    )


def test_tenant_recipe_log_get(cli_runner, mock_client, mock_tenant_recipe_log):
    """vrg tenant-recipe log get should get a log entry by key."""
    mock_client.tenant_recipe_logs.get.return_value = mock_tenant_recipe_log

    result = cli_runner.invoke(app, ["tenant-recipe", "log", "get", "600"])

    assert result.exit_code == 0
    assert "Tenant recipe deployed successfully" in result.output
    mock_client.tenant_recipe_logs.get.assert_called_once_with(key=600)
