"""Tests for VM drive sub-resource commands."""

from verge_cli.cli import app


def test_drive_list(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive list should list drives on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]

    result = cli_runner.invoke(app, ["vm", "drive", "list", "test-vm"])

    assert result.exit_code == 0
    assert "OS Disk" in result.output
    mock_vm.drives.list.assert_called_once()


def test_drive_get(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive get should show drive details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]
    mock_vm.drives.get.return_value = mock_drive

    result = cli_runner.invoke(app, ["vm", "drive", "get", "test-vm", "OS Disk"])

    assert result.exit_code == 0
    assert "OS Disk" in result.output


def test_drive_create(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive create should add a drive to a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.create.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        ["vm", "drive", "create", "test-vm", "--size", "50GB", "--name", "OS Disk"],
    )

    assert result.exit_code == 0
    mock_vm.drives.create.assert_called_once()
    call_kwargs = mock_vm.drives.create.call_args[1]
    assert call_kwargs["size_gb"] == 50
    assert call_kwargs["name"] == "OS Disk"


def test_drive_create_with_interface(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive create should accept --interface flag."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.create.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        [
            "vm",
            "drive",
            "create",
            "test-vm",
            "--size",
            "100GB",
            "--interface",
            "ide",
            "--media",
            "disk",
            "--tier",
            "2",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_vm.drives.create.call_args[1]
    assert call_kwargs["interface"] == "ide"
    assert call_kwargs["media"] == "disk"
    assert call_kwargs["tier"] == 2


def test_drive_delete(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive delete should remove a drive."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]

    result = cli_runner.invoke(app, ["vm", "drive", "delete", "test-vm", "OS Disk", "--yes"])

    assert result.exit_code == 0
    mock_vm.drives.delete.assert_called_once_with(10)


def test_drive_update(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive update should update drive properties."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]
    mock_vm.drives.update.return_value = mock_drive

    result = cli_runner.invoke(
        app, ["vm", "drive", "update", "test-vm", "OS Disk", "--name", "Boot Disk"]
    )

    assert result.exit_code == 0
    mock_vm.drives.update.assert_called_once()


def test_drive_import(cli_runner, mock_client, mock_vm, mock_drive):
    """vrg vm drive import should import a drive from file."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.import_drive.return_value = mock_drive

    result = cli_runner.invoke(
        app,
        ["vm", "drive", "import", "test-vm", "--file-name", "disk.vmdk"],
    )

    assert result.exit_code == 0
    mock_vm.drives.import_drive.assert_called_once()
