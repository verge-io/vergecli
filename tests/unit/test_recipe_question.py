"""Tests for recipe question management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_question_list(cli_runner, mock_client, mock_recipe, mock_recipe_question):
    """vrg recipe question list should list questions for a recipe."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_questions.list.return_value = [mock_recipe_question]

    result = cli_runner.invoke(app, ["recipe", "question", "list", "Ubuntu Server 22.04"])

    assert result.exit_code == 0
    assert "YB_CPU_CORES" in result.output
    mock_client.recipe_questions.list.assert_called_once_with(
        recipe_ref="vm_recipes/8f73f8bcc9c9f1aaba32f733bfc295acaf548554"
    )


def test_question_list_by_section(
    cli_runner, mock_client, mock_recipe, mock_recipe_section, mock_recipe_question
):
    """vrg recipe question list --section should filter by section."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]
    mock_client.recipe_questions.list.return_value = [mock_recipe_question]

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "question",
            "list",
            "Ubuntu Server 22.04",
            "--section",
            "Virtual Machine",
        ],
    )

    assert result.exit_code == 0
    assert "YB_CPU_CORES" in result.output
    mock_client.recipe_questions.list.assert_called_once_with(
        recipe_ref="vm_recipes/8f73f8bcc9c9f1aaba32f733bfc295acaf548554",
        section=100,
    )


def test_question_get(cli_runner, mock_client, mock_recipe, mock_recipe_question):
    """vrg recipe question get should get a question by name."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_questions.list.return_value = [mock_recipe_question]
    mock_client.recipe_questions.get.return_value = mock_recipe_question

    result = cli_runner.invoke(
        app,
        ["recipe", "question", "get", "Ubuntu Server 22.04", "YB_CPU_CORES"],
    )

    assert result.exit_code == 0
    assert "YB_CPU_CORES" in result.output


def test_question_create(
    cli_runner, mock_client, mock_recipe, mock_recipe_section, mock_recipe_question
):
    """vrg recipe question create should create with name, section, type."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]
    mock_client.recipe_questions.create.return_value = mock_recipe_question

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "question",
            "create",
            "Ubuntu Server 22.04",
            "--name",
            "YB_CPU_CORES",
            "--section",
            "Virtual Machine",
            "--type",
            "num",
            "--display",
            "CPU Cores",
            "--default",
            "2",
        ],
    )

    assert result.exit_code == 0
    assert "created" in result.output.lower()
    mock_client.recipe_questions.create.assert_called_once()


def test_question_create_with_list_options(
    cli_runner, mock_client, mock_recipe, mock_recipe_section, mock_recipe_question
):
    """vrg recipe question create --list-options should parse options."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_sections.list.return_value = [mock_recipe_section]
    mock_client.recipe_questions.create.return_value = mock_recipe_question

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "question",
            "create",
            "Ubuntu Server 22.04",
            "--name",
            "YB_SIZE",
            "--section",
            "Virtual Machine",
            "--type",
            "list",
            "--list-options",
            "small=Small,medium=Medium,large=Large",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.recipe_questions.create.call_args
    assert call_kwargs.kwargs["list_options"] == {
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
    }


def test_question_update(cli_runner, mock_client, mock_recipe, mock_recipe_question):
    """vrg recipe question update should update display and default."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_questions.list.return_value = [mock_recipe_question]
    mock_client.recipe_questions.update.return_value = mock_recipe_question

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "question",
            "update",
            "Ubuntu Server 22.04",
            "YB_CPU_CORES",
            "--display",
            "Number of Cores",
            "--default",
            "4",
        ],
    )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_question_delete(cli_runner, mock_client, mock_recipe, mock_recipe_question):
    """vrg recipe question delete should delete the question."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.recipe_questions.list.return_value = [mock_recipe_question]

    result = cli_runner.invoke(
        app,
        [
            "recipe",
            "question",
            "delete",
            "Ubuntu Server 22.04",
            "YB_CPU_CORES",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.recipe_questions.delete.assert_called_once_with(200)
