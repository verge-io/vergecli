"""Tests for recipe section management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_section_list(cli_runner, mock_client, mock_recipe, mock_recipe_section):
    """vrg recipe section list should list sections for a recipe."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]

    result = cli_runner.invoke(app, ["recipe", "section", "list", "Ubuntu Server 22.04"])

    assert result.exit_code == 0
    assert "Virtual Machine" in result.output
    mock_client.recipe_sections.list.assert_called_once_with(
        recipe_ref="vm_recipes/8f73f8bcc9c9f1aaba32f733bfc295acaf548554"
    )


def test_section_get(cli_runner, mock_client, mock_recipe, mock_recipe_section):
    """vrg recipe section get should get a section by name."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]
    mock_client.recipe_sections.get.return_value = mock_recipe_section

    result = cli_runner.invoke(
        app,
        ["recipe", "section", "get", "Ubuntu Server 22.04", "Virtual Machine"],
    )

    assert result.exit_code == 0
    assert "Virtual Machine" in result.output


def test_section_create(cli_runner, mock_client, mock_recipe, mock_recipe_section):
    """vrg recipe section create should create a section."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.create.return_value = mock_recipe_section

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "section",
            "create",
            "Ubuntu Server 22.04",
            "--name",
            "Virtual Machine",
            "--description",
            "Core VM settings",
        ],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    mock_client.recipe_sections.create.assert_called_once_with(
        name="Virtual Machine",
        recipe_ref="vm_recipes/8f73f8bcc9c9f1aaba32f733bfc295acaf548554",
        description="Core VM settings",
    )


def test_section_update(cli_runner, mock_client, mock_recipe, mock_recipe_section):
    """vrg recipe section update should update section order."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]
    mock_client.recipe_sections.update.return_value = mock_recipe_section

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "section",
            "update",
            "Ubuntu Server 22.04",
            "Virtual Machine",
            "--order",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_section_delete(cli_runner, mock_client, mock_recipe, mock_recipe_section):
    """vrg recipe section delete should delete section (cascades to questions)."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "section",
            "delete",
            "Ubuntu Server 22.04",
            "Virtual Machine",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.recipe_sections.delete.assert_called_once_with(100)
