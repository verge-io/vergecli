"""Tests for tenant shared object sub-resource commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_share_list(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share list should list shared objects for a tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["tenant", "share", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "shared-web-server" in result.output
    mock_client.shared_objects.list.assert_called_once_with(tenant_key=5, inbox_only=False)


def test_share_list_inbox(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share list --inbox should filter inbox items."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.list.return_value = [mock_shared_object]

    result = cli_runner.invoke(app, ["tenant", "share", "list", "acme-corp", "--inbox"])

    assert result.exit_code == 0
    mock_client.shared_objects.list.assert_called_once_with(tenant_key=5, inbox_only=True)


def test_share_get_by_key(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share get should accept a numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.get.return_value = mock_shared_object

    result = cli_runner.invoke(app, ["tenant", "share", "get", "acme-corp", "15"])

    assert result.exit_code == 0
    assert "shared-web-server" in result.output
    mock_client.shared_objects.get.assert_called_once_with(15)


def test_share_get_by_name(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share get should accept a name with tenant context."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.get.return_value = mock_shared_object

    result = cli_runner.invoke(app, ["tenant", "share", "get", "acme-corp", "shared-web-server"])

    assert result.exit_code == 0
    assert "shared-web-server" in result.output
    mock_client.shared_objects.get.assert_called_once_with(tenant_key=5, name="shared-web-server")


def test_share_create(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share create should create a shared object."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_vm = MagicMock()
    mock_vm.key = 42
    mock_vm.name = "web-server"
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.shared_objects.create.return_value = mock_shared_object

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "share",
            "create",
            "acme-corp",
            "--vm",
            "web-server",
            "--name",
            "shared-web-server",
            "--description",
            "Web server VM shared to dev tenant",
        ],
    )

    assert result.exit_code == 0
    assert "shared-web-server" in result.output
    mock_client.shared_objects.create.assert_called_once_with(
        tenant_key=5,
        vm_key=42,
        name="shared-web-server",
        description="Web server VM shared to dev tenant",
    )


def test_share_create_with_snapshot(cli_runner, mock_client, mock_tenant, mock_shared_object):
    """vrg tenant share create --snapshot should pass snapshot_name."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.vms.list.return_value = []
    # Use numeric VM key to avoid name resolution
    mock_client.shared_objects.create.return_value = mock_shared_object

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "share",
            "create",
            "acme-corp",
            "--vm",
            "42",
            "--snapshot",
            "pre-upgrade",
        ],
    )

    assert result.exit_code == 0
    mock_client.shared_objects.create.assert_called_once_with(
        tenant_key=5,
        vm_key=42,
        snapshot_name="pre-upgrade",
    )


def test_share_import(cli_runner, mock_client, mock_tenant):
    """vrg tenant share import should import a shared object."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.import_object.return_value = {"status": "ok"}

    result = cli_runner.invoke(app, ["tenant", "share", "import", "acme-corp", "15"])

    assert result.exit_code == 0
    assert "Import initiated" in result.output
    mock_client.shared_objects.import_object.assert_called_once_with(key=15)


def test_share_refresh(cli_runner, mock_client, mock_tenant):
    """vrg tenant share refresh should refresh a shared object."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.shared_objects.refresh_object.return_value = None

    result = cli_runner.invoke(app, ["tenant", "share", "refresh", "acme-corp", "15"])

    assert result.exit_code == 0
    assert "Refresh initiated" in result.output
    mock_client.shared_objects.refresh_object.assert_called_once_with(key=15)


def test_share_delete_confirm(cli_runner, mock_client, mock_tenant):
    """vrg tenant share delete --yes should delete without prompting."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "share", "delete", "acme-corp", "15", "--yes"])

    assert result.exit_code == 0
    assert "Deleted" in result.output
    mock_client.shared_objects.delete.assert_called_once_with(key=15)


def test_share_delete_no_confirm(cli_runner, mock_client, mock_tenant):
    """vrg tenant share delete without --yes should abort."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "share", "delete", "acme-corp", "15"], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_client.shared_objects.delete.assert_not_called()


def test_share_tenant_not_found(cli_runner, mock_client):
    """vrg tenant share list should exit 6 when tenant not found."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "share", "list", "nonexistent"])

    assert result.exit_code == 6
