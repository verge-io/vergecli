"""Tests for VM commands (clone, migrate, hibernate, tag, favorite, console)."""

from __future__ import annotations

from unittest.mock import MagicMock

from verge_cli.cli import app

# --- Clone ---


def test_vm_clone(cli_runner, mock_client, mock_vm):
    """vrg vm clone should clone a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.clone.return_value = {"name": "clone-vm", "$key": 2}

    result = cli_runner.invoke(app, ["vm", "clone", "test-vm", "--name", "clone-vm"])

    assert result.exit_code == 0
    mock_vm.clone.assert_called_once_with(name="clone-vm", preserve_macs=False)


def test_vm_clone_with_preserve_macs(cli_runner, mock_client, mock_vm):
    """vrg vm clone --preserve-macs should pass flag to SDK."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.clone.return_value = {"name": "clone-vm", "$key": 2}

    result = cli_runner.invoke(
        app, ["vm", "clone", "test-vm", "--name", "clone-vm", "--preserve-macs"]
    )

    assert result.exit_code == 0
    mock_vm.clone.assert_called_once_with(name="clone-vm", preserve_macs=True)


def test_vm_clone_by_key(cli_runner, mock_client, mock_vm):
    """vrg vm clone with numeric key should work."""
    mock_client.vms.list.return_value = []
    mock_client.vms.get.return_value = mock_vm
    mock_vm.clone.return_value = {"name": "clone-vm", "$key": 2}

    result = cli_runner.invoke(app, ["vm", "clone", "1"])

    assert result.exit_code == 0
    mock_vm.clone.assert_called_once()


# --- Migrate ---


def test_vm_migrate(cli_runner, mock_client, mock_vm):
    """vrg vm migrate should migrate a running VM."""
    mock_vm.is_running = True
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "migrate", "test-vm"])

    assert result.exit_code == 0
    mock_vm.migrate.assert_called_once_with(preferred_node=None)


def test_vm_migrate_with_node(cli_runner, mock_client, mock_vm):
    """vrg vm migrate --node should resolve and pass node key."""
    mock_vm.is_running = True
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    mock_node = MagicMock()
    mock_node.name = "node2"
    mock_node.key = 20
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["vm", "migrate", "test-vm", "--node", "node2"])

    assert result.exit_code == 0
    mock_vm.migrate.assert_called_once_with(preferred_node=20)


def test_vm_migrate_not_running(cli_runner, mock_client, mock_vm):
    """vrg vm migrate on stopped VM should fail."""
    mock_vm.is_running = False
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "migrate", "test-vm"])

    assert result.exit_code == 1
    mock_vm.migrate.assert_not_called()


# --- Hibernate ---


def test_vm_hibernate(cli_runner, mock_client, mock_vm):
    """vrg vm hibernate should hibernate a running VM."""
    mock_vm.is_running = True
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "hibernate", "test-vm"])

    assert result.exit_code == 0
    mock_vm.hibernate.assert_called_once()


def test_vm_hibernate_not_running(cli_runner, mock_client, mock_vm):
    """vrg vm hibernate on stopped VM should fail."""
    mock_vm.is_running = False
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "hibernate", "test-vm"])

    assert result.exit_code == 1
    mock_vm.hibernate.assert_not_called()


# --- Tag ---


def test_vm_tag(cli_runner, mock_client, mock_vm, mock_tag):
    """vrg vm tag should add a tag to a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_client.tags.list.return_value = [mock_tag]

    result = cli_runner.invoke(app, ["vm", "tag", "test-vm", "production"])

    assert result.exit_code == 0
    mock_vm.tag.assert_called_once_with(5)


def test_vm_tag_by_key(cli_runner, mock_client, mock_vm):
    """vrg vm tag with numeric tag key should work."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_client.tags.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "tag", "test-vm", "5"])

    assert result.exit_code == 0
    mock_vm.tag.assert_called_once_with(5)


# --- Untag ---


def test_vm_untag(cli_runner, mock_client, mock_vm, mock_tag):
    """vrg vm untag should remove a tag from a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_client.tags.list.return_value = [mock_tag]

    result = cli_runner.invoke(app, ["vm", "untag", "test-vm", "production"])

    assert result.exit_code == 0
    mock_vm.untag.assert_called_once_with(5)


def test_vm_untag_by_key(cli_runner, mock_client, mock_vm):
    """vrg vm untag with numeric tag key should work."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_client.tags.list.return_value = []

    result = cli_runner.invoke(app, ["vm", "untag", "test-vm", "5"])

    assert result.exit_code == 0
    mock_vm.untag.assert_called_once_with(5)


# --- Favorite ---


def test_vm_favorite(cli_runner, mock_client, mock_vm):
    """vrg vm favorite should mark VM as favorite."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "favorite", "test-vm"])

    assert result.exit_code == 0
    mock_vm.favorite.assert_called_once()


def test_vm_favorite_by_key(cli_runner, mock_client, mock_vm):
    """vrg vm favorite with numeric key should work."""
    mock_client.vms.list.return_value = []
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "favorite", "1"])

    assert result.exit_code == 0
    mock_vm.favorite.assert_called_once()


# --- Unfavorite ---


def test_vm_unfavorite(cli_runner, mock_client, mock_vm):
    """vrg vm unfavorite should remove VM from favorites."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "unfavorite", "test-vm"])

    assert result.exit_code == 0
    mock_vm.unfavorite.assert_called_once()


# --- Console ---


def test_vm_console(cli_runner, mock_client, mock_vm):
    """vrg vm console should display console info."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.get_console_info.return_value = {
        "console_type": "vnc",
        "host": "192.168.1.10",
        "port": 5900,
        "url": "vnc://192.168.1.10:5900",
        "web_url": "https://verge.example.com/vnc/?vm=1",
        "is_available": True,
    }

    result = cli_runner.invoke(app, ["vm", "console", "test-vm"])

    assert result.exit_code == 0
    mock_vm.get_console_info.assert_called_once()


def test_vm_console_json_output(cli_runner, mock_client, mock_vm):
    """vrg vm console with JSON output should include all fields."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.get_console_info.return_value = {
        "console_type": "vnc",
        "host": "192.168.1.10",
        "port": 5900,
        "url": "vnc://192.168.1.10:5900",
        "web_url": "https://verge.example.com/vnc/?vm=1",
        "is_available": True,
    }

    result = cli_runner.invoke(app, ["--output", "json", "vm", "console", "test-vm"])

    assert result.exit_code == 0
    assert "vnc" in result.output
    assert "5900" in result.output
