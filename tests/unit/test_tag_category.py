"""Tests for tag category commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_category_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test listing tag categories."""
    mock_client.tag_categories.list.return_value = [mock_tag_category]
    result = cli_runner.invoke(app, ["tag", "category", "list"])
    assert result.exit_code == 0
    assert "Environment" in result.output
    mock_client.tag_categories.list.assert_called_once()


def test_category_get(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test getting a tag category by name."""
    mock_client.tag_categories.list.return_value = [mock_tag_category]
    mock_client.tag_categories.get.return_value = mock_tag_category
    result = cli_runner.invoke(app, ["tag", "category", "get", "1"])
    assert result.exit_code == 0
    assert "Environment" in result.output
    mock_client.tag_categories.get.assert_called_once_with(1)


def test_category_create(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test creating a tag category with taggable flags."""
    mock_client.tag_categories.create.return_value = mock_tag_category
    result = cli_runner.invoke(
        app,
        [
            "tag",
            "category",
            "create",
            "--name",
            "Environment",
            "--description",
            "Env classification",
            "--taggable-vms",
            "--taggable-networks",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower() or "Environment" in result.output
    mock_client.tag_categories.create.assert_called_once_with(
        name="Environment",
        description="Env classification",
        taggable_vms=True,
        taggable_networks=True,
    )


def test_category_create_single_selection(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test creating a tag category with --single-selection."""
    mock_client.tag_categories.create.return_value = mock_tag_category
    result = cli_runner.invoke(
        app,
        [
            "tag",
            "category",
            "create",
            "--name",
            "Environment",
            "--single-selection",
            "--taggable-vms",
        ],
    )
    assert result.exit_code == 0
    mock_client.tag_categories.create.assert_called_once_with(
        name="Environment",
        single_tag_selection=True,
        taggable_vms=True,
    )


def test_category_update(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test updating a tag category."""
    mock_client.tag_categories.list.return_value = [mock_tag_category]
    mock_client.tag_categories.get.return_value = mock_tag_category
    mock_client.tag_categories.update.return_value = mock_tag_category
    result = cli_runner.invoke(
        app,
        ["tag", "category", "update", "1", "--description", "Updated desc"],
    )
    assert result.exit_code == 0
    mock_client.tag_categories.update.assert_called_once_with(1, description="Updated desc")


def test_category_delete_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag_category: MagicMock
) -> None:
    """Test deleting a tag category with --yes."""
    mock_client.tag_categories.list.return_value = [mock_tag_category]
    mock_client.tag_categories.get.return_value = mock_tag_category
    result = cli_runner.invoke(app, ["tag", "category", "delete", "1", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.tag_categories.delete.assert_called_once_with(1)


def test_category_not_found(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test resolution error when category not found (exit 6)."""
    mock_client.tag_categories.list.return_value = []
    result = cli_runner.invoke(app, ["tag", "category", "get", "nonexistent"])
    assert result.exit_code == 6
