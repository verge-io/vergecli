"""Tests for shared object management commands."""

from __future__ import annotations

from verge_cli.cli import app


def test_shared_object_list(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object list should list shared objects."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "list"])

    assert result.exit_code == 0
    assert "shared-web-server" in result.output
    mock_client.shared_objects.list.assert_called_once_with()


def test_shared_object_list_by_tenant(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object list --tenant should filter by tenant key."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "list", "--tenant", "3"])

    assert result.exit_code == 0
    mock_client.shared_objects.list.assert_called_once_with(tenant_key=3)


def test_shared_object_list_inbox(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object list --inbox should filter inbox objects."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "list", "--inbox"])

    assert result.exit_code == 0
    mock_client.shared_objects.list.assert_called_once_with(inbox_only=True)


def test_shared_object_get(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object get should get shared object details."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]
    mock_client.shared_objects.get.return_value = mock_shared_object

    result = cli_runner.invoke(app, ["shared-object", "get", "shared-web-server"])

    assert result.exit_code == 0
    assert "shared-web-server" in result.output


def test_shared_object_get_by_key(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object get should accept numeric key."""
    mock_client.shared_objects.get.return_value = mock_shared_object

    result = cli_runner.invoke(app, ["shared-object", "get", "15"])

    assert result.exit_code == 0
    mock_client.shared_objects.get.assert_called_once_with(15)


def test_shared_object_create(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object create should create a shared object."""
    mock_client.shared_objects.create.return_value = mock_shared_object

    result = cli_runner.invoke(
        app,
        [
            "shared-object",
            "create",
            "--tenant-key",
            "3",
            "--vm-name",
            "web-server",
            "--name",
            "shared-web-server",
        ],
    )

    assert result.exit_code == 0
    assert "Created" in result.output
    mock_client.shared_objects.create.assert_called_once_with(
        tenant_key=3, vm_name="web-server", name="shared-web-server"
    )


def test_shared_object_import(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object import should import a shared object."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "import", "shared-web-server"])

    assert result.exit_code == 0
    assert "Imported" in result.output
    mock_client.shared_objects.import_object.assert_called_once_with(15)


def test_shared_object_refresh(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object refresh should refresh a shared object."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "refresh", "shared-web-server"])

    assert result.exit_code == 0
    assert "Refreshed" in result.output
    mock_client.shared_objects.refresh_object.assert_called_once_with(15)


def test_shared_object_delete(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object delete --yes should delete a shared object."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "delete", "shared-web-server", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.shared_objects.delete.assert_called_once_with(15)


def test_shared_object_delete_cancel(cli_runner, mock_client, mock_shared_object):
    """vrg shared-object delete should cancel without --yes."""
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["shared-object", "delete", "shared-web-server"], input="n\n")

    assert result.exit_code == 0
    mock_client.shared_objects.delete.assert_not_called()
