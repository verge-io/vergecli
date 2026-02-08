"""Tests for recipe log management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_log_list(cli_runner, mock_client, mock_recipe_log):
    """vrg recipe log list should list recipe logs."""
    mock_client.vm_recipe_logs.list.return_value = [mock_recipe_log]

    result = cli_runner.invoke(app, ["recipe", "log", "list"])

    assert result.exit_code == 0
    assert "Recipe deployed successfully" in result.output
    mock_client.vm_recipe_logs.list.assert_called_once_with()


def test_log_list_by_recipe(cli_runner, mock_client, mock_recipe, mock_recipe_log):
    """vrg recipe log list --recipe should filter by recipe."""
    mock_client.vm_recipes.list.return_value = [mock_recipe]
    mock_client.vm_recipe_logs.list.return_value = [mock_recipe_log]

    result = cli_runner.invoke(
        app,
        ["recipe", "log", "list", "--recipe", "Ubuntu Server 22.04"],
    )

    assert result.exit_code == 0
    assert "Recipe deployed successfully" in result.output
    mock_client.vm_recipe_logs.list.assert_called_once_with(
        vm_recipe="8f73f8bcc9c9f1aaba32f733bfc295acaf548554"
    )


def test_log_get(cli_runner, mock_client, mock_recipe_log):
    """vrg recipe log get should get log details."""
    mock_client.vm_recipe_logs.get.return_value = mock_recipe_log

    result = cli_runner.invoke(app, ["recipe", "log", "get", "300"])

    assert result.exit_code == 0
    assert "Recipe deployed successfully" in result.output
    mock_client.vm_recipe_logs.get.assert_called_once_with(key=300)
