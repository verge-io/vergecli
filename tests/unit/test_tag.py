"""Tests for tag commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from typer.testing import CliRunner

from verge_cli.cli import app


def test_tag_list(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test listing tags."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "list"])
    assert result.exit_code == 0
    assert "production" in result.output
    assert "Environment" in result.output
    mock_client.tags.list.assert_called_once()


def test_tag_list_by_category(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test listing tags filtered by category name."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "list", "--category", "Environment"])
    assert result.exit_code == 0
    assert "production" in result.output
    mock_client.tags.list.assert_called_once_with(category_name="Environment")


def test_tag_list_by_category_key(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test listing tags filtered by numeric category key."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "list", "--category", "1"])
    assert result.exit_code == 0
    mock_client.tags.list.assert_called_once_with(category_key=1)


def test_tag_get_by_key(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test getting a tag by numeric key."""
    mock_client.tags.get.return_value = mock_tag
    result = cli_runner.invoke(app, ["tag", "get", "5"])
    assert result.exit_code == 0
    assert "production" in result.output
    mock_client.tags.get.assert_called_once_with(5)


def test_tag_get_by_name(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test getting a tag by name with category."""
    mock_client.tags.get.return_value = mock_tag
    result = cli_runner.invoke(app, ["tag", "get", "production", "--category", "Environment"])
    assert result.exit_code == 0
    assert "production" in result.output
    mock_client.tags.get.assert_called_once_with(name="production", category_name="Environment")


def test_tag_create(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test creating a tag."""
    mock_cat = MagicMock()
    mock_cat.key = 1
    mock_cat.name = "Environment"
    mock_client.tag_categories.list.return_value = [mock_cat]
    mock_client.tags.create.return_value = mock_tag
    result = cli_runner.invoke(
        app,
        [
            "tag",
            "create",
            "--name",
            "production",
            "--category",
            "Environment",
            "--description",
            "Prod env",
        ],
    )
    assert result.exit_code == 0
    assert "created" in result.output.lower() or "production" in result.output
    mock_client.tags.create.assert_called_once_with(
        name="production", category_key=1, description="Prod env"
    )


def test_tag_update(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test updating a tag."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_client.tags.update.return_value = mock_tag
    result = cli_runner.invoke(app, ["tag", "update", "5", "--description", "Updated description"])
    assert result.exit_code == 0
    mock_client.tags.update.assert_called_once_with(5, description="Updated description")


def test_tag_delete_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test deleting a tag with --yes confirmation."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "delete", "5", "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output.lower()
    mock_client.tags.delete.assert_called_once_with(5)


def test_tag_delete_no_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test deleting a tag without --yes aborts."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "delete", "5"], input="n\n")
    assert result.exit_code != 0
    mock_client.tags.delete.assert_not_called()


def test_tag_assign_vm(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test assigning a tag to a VM."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_member_mgr = MagicMock()
    mock_client.tags.members.return_value = mock_member_mgr
    result = cli_runner.invoke(app, ["tag", "assign", "5", "vm", "42"])
    assert result.exit_code == 0
    assert "assigned" in result.output.lower()
    mock_client.tags.members.assert_called_once_with(5)
    mock_member_mgr.add.assert_called_once_with("vms", 42)


def test_tag_assign_network(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test assigning a tag to a network."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_member_mgr = MagicMock()
    mock_client.tags.members.return_value = mock_member_mgr
    result = cli_runner.invoke(app, ["tag", "assign", "5", "network", "10"])
    assert result.exit_code == 0
    assert "assigned" in result.output.lower()
    mock_client.tags.members.assert_called_once_with(5)
    mock_member_mgr.add.assert_called_once_with("vnets", 10)


def test_tag_unassign(cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock) -> None:
    """Test unassigning a tag from a resource."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_member_mgr = MagicMock()
    mock_client.tags.members.return_value = mock_member_mgr
    result = cli_runner.invoke(app, ["tag", "unassign", "5", "vm", "42"])
    assert result.exit_code == 0
    assert "unassigned" in result.output.lower()
    mock_client.tags.members.assert_called_once_with(5)
    mock_member_mgr.remove_resource.assert_called_once_with("vms", 42)


def test_tag_members(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_tag: MagicMock,
    mock_tag_member: MagicMock,
) -> None:
    """Test listing tagged resources."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_member_mgr = MagicMock()
    mock_member_mgr.list.return_value = [mock_tag_member]
    mock_client.tags.members.return_value = mock_member_mgr
    result = cli_runner.invoke(app, ["tag", "members", "5"])
    assert result.exit_code == 0
    assert "vm" in result.output.lower()
    mock_client.tags.members.assert_called_once_with(5)
    mock_member_mgr.list.assert_called_once()


def test_tag_members_by_type(
    cli_runner: CliRunner,
    mock_client: MagicMock,
    mock_tag: MagicMock,
    mock_tag_member: MagicMock,
) -> None:
    """Test listing tagged resources filtered by type."""
    mock_client.tags.list.return_value = [mock_tag]
    mock_member_mgr = MagicMock()
    mock_member_mgr.list.return_value = [mock_tag_member]
    mock_client.tags.members.return_value = mock_member_mgr
    result = cli_runner.invoke(app, ["tag", "members", "5", "--type", "vm"])
    assert result.exit_code == 0
    mock_member_mgr.list.assert_called_once_with(resource_type="vms")


def test_tag_assign_invalid_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_tag: MagicMock
) -> None:
    """Test assigning with an invalid resource type."""
    mock_client.tags.list.return_value = [mock_tag]
    result = cli_runner.invoke(app, ["tag", "assign", "5", "invalid_type", "42"])
    assert result.exit_code != 0
