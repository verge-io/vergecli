"""Tests for recipe instance management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_instance_list(cli_runner, mock_client, mock_recipe_instance):
    """vrg recipe instance list should list deployed instances."""
    mock_client.vm_recipe_instances.list.return_value = [mock_recipe_instance]

    result = cli_runner.invoke(app, ["recipe", "instance", "list"])

    assert result.exit_code == 0
    assert "my-ubuntu" in result.output
    mock_client.vm_recipe_instances.list.assert_called_once_with()


def test_instance_list_by_recipe(cli_runner, mock_client, mock_recipe, mock_recipe_instance):
    """vrg recipe instance list --recipe should filter by recipe."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipe_instances.list.return_value = [mock_recipe_instance]

    result = cli_runner.invoke(
        app,
        ["recipe", "instance", "list", "--recipe", "Ubuntu Server 22.04"],
    )

    assert result.exit_code == 0
    assert "my-ubuntu" in result.output
    mock_client.vm_recipe_instances.list.assert_called_once_with(
        recipe="8f73f8bcc9c9f1aaba32f733bfc295acaf548554"
    )


def test_instance_get(cli_runner, mock_client, mock_recipe_instance):
    """vrg recipe instance get should get instance details."""
    mock_client.vm_recipe_instances.list.return_value = [mock_recipe_instance]
    mock_client.vm_recipe_instances.get.return_value = mock_recipe_instance

    result = cli_runner.invoke(app, ["recipe", "instance", "get", "my-ubuntu"])

    assert result.exit_code == 0
    assert "my-ubuntu" in result.output


def test_instance_delete(cli_runner, mock_client, mock_recipe_instance):
    """vrg recipe instance delete should delete instance tracking."""
    mock_client.vm_recipe_instances.list.return_value = [mock_recipe_instance]

    result = cli_runner.invoke(
        app,
        ["recipe", "instance", "delete", "my-ubuntu", "--yes"],
    )

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.vm_recipe_instances.delete.assert_called_once_with(50)
