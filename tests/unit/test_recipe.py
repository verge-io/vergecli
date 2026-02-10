"""Tests for VM recipe management commands."""

from __future__ import annotations

from verge_cli.cli import app
from verge_cli.commands.recipe import _parse_set_args


def test_recipe_list(cli_runner, mock_client, mock_recipe):
    """vrg recipe list should list all recipes."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]

    result = cli_runner.invoke(app, ["recipe", "list"])

    assert result.exit_code == 0
    assert "Ubuntu Server 22.04" in result.output
    mock_client.vm_recipes.list.assert_called_once_with()


def test_recipe_list_downloaded(cli_runner, mock_client, mock_recipe):
    """vrg recipe list --downloaded should filter downloaded recipes."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]

    result = cli_runner.invoke(app, ["recipe", "list", "--downloaded"])

    assert result.exit_code == 0
    assert "Ubuntu Server 22.04" in result.output
    mock_client.vm_recipes.list.assert_called_once_with(downloaded=True)


def test_recipe_get(cli_runner, mock_client, mock_recipe):
    """vrg recipe get should get a recipe by name."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipes.get.return_value = mock_recipe

    result = cli_runner.invoke(app, ["recipe", "get", "Ubuntu Server 22.04"])

    assert result.exit_code == 0
    assert "Ubuntu Server 22.04" in result.output


def test_recipe_create(cli_runner, mock_client, mock_recipe):
    """vrg recipe create should create a new recipe with --version."""
    mock_client.vm_recipes.create.return_value = mock_recipe

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "create",
            "--name",
            "Ubuntu Server 22.04",
            "--catalog",
            "default",
            "--version",
            "1.0",
        ],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    call_kwargs = mock_client.vm_recipes.create.call_args[1]
    assert call_kwargs["version"] == "1.0"


def test_recipe_create_missing_version(cli_runner, mock_client):
    """vrg recipe create without --version should fail."""
    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "create",
            "--name",
            "Test Recipe",
            "--catalog",
            "default",
        ],
    )

    assert result.exit_code != 0


def test_recipe_update(cli_runner, mock_client, mock_recipe):
    """vrg recipe update should update description and notes."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipes.update.return_value = mock_recipe

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "update",
            "Ubuntu Server 22.04",
            "--description",
            "Updated desc",
        ],
    )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_recipe_delete(cli_runner, mock_client, mock_recipe):
    """vrg recipe delete --yes should delete the recipe."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]

    result = cli_runner.invoke(
        app,
        ["recipe", "delete", "Ubuntu Server 22.04", "--yes"],
    )

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.vm_recipes.delete.assert_called_once_with(
        "8f73f8bcc9c9f1aaba32f733bfc295acaf548554"
    )


def test_recipe_deploy(cli_runner, mock_client, mock_recipe, mock_recipe_instance):
    """vrg recipe deploy should deploy with --name and --set KEY=VALUE."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipes.deploy.return_value = mock_recipe_instance

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "deploy",
            "Ubuntu Server 22.04",
            "--name",
            "my-ubuntu",
            "--set",
            "YB_CPU_CORES=4",
            "--set",
            "YB_RAM=8192",
        ],
    )

    assert result.exit_code == 0
    assert "deployed" in result.output.lower()
    mock_client.vm_recipes.deploy.assert_called_once_with(
        "8f73f8bcc9c9f1aaba32f733bfc295acaf548554",
        "my-ubuntu",
        answers={"YB_CPU_CORES": "4", "YB_RAM": "8192"},
        auto_update=False,
    )


def test_recipe_deploy_with_auto_update(cli_runner, mock_client, mock_recipe, mock_recipe_instance):
    """vrg recipe deploy --auto-update should pass auto_update=True."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipes.deploy.return_value = mock_recipe_instance

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "deploy",
            "Ubuntu Server 22.04",
            "--name",
            "my-ubuntu",
            "--auto-update",
        ],
    )

    assert result.exit_code == 0
    mock_client.vm_recipes.deploy.assert_called_once_with(
        "8f73f8bcc9c9f1aaba32f733bfc295acaf548554",
        "my-ubuntu",
        answers=None,
        auto_update=True,
    )


def test_recipe_not_found(cli_runner, mock_client):
    """vrg recipe get nonexistent should exit 6."""
    mock_client.vm_recipes.list.return_value = []

    result = cli_runner.invoke(app, ["recipe", "get", "nonexistent"])

    assert result.exit_code == 6


def test_parse_set_args():
    """_parse_set_args should parse KEY=VALUE pairs."""
    result = _parse_set_args(["KEY=VALUE", "FOO=bar=baz"])
    assert result == {"KEY": "VALUE", "FOO": "bar=baz"}
