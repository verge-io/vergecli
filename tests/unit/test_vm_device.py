"""Tests for VM device sub-resource commands (TPM only)."""

from verge_cli.cli import app


def test_device_list(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device list should list devices on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]

    result = cli_runner.invoke(app, ["vm", "device", "list", "test-vm"])

    assert result.exit_code == 0
    assert "TPM" in result.output


def test_device_get(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device get should show device details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]
    mock_vm.devices.get.return_value = mock_device

    result = cli_runner.invoke(app, ["vm", "device", "get", "test-vm", "TPM"])

    assert result.exit_code == 0
    assert "TPM" in result.output


def test_device_create_tpm(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device create should add a TPM device."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.create.return_value = mock_device

    result = cli_runner.invoke(
        app,
        ["vm", "device", "create", "test-vm", "--model", "crb", "--version", "2"],
    )

    assert result.exit_code == 0
    mock_vm.devices.create.assert_called_once()
    call_kwargs = mock_vm.devices.create.call_args[1]
    assert call_kwargs["device_type"] == "tpm"
    assert call_kwargs["settings"]["model"] == "crb"
    assert call_kwargs["settings"]["version"] == "2"


def test_device_create_tpm_defaults(cli_runner, mock_client, mock_vm, mock_device):
    """TPM defaults to model=crb, version=2.0."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.create.return_value = mock_device

    result = cli_runner.invoke(app, ["vm", "device", "create", "test-vm"])

    assert result.exit_code == 0
    call_kwargs = mock_vm.devices.create.call_args[1]
    assert call_kwargs["settings"]["model"] == "crb"
    assert call_kwargs["settings"]["version"] == "2"


def test_device_delete(cli_runner, mock_client, mock_vm, mock_device):
    """vrg vm device delete should remove a device."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.devices.list.return_value = [mock_device]

    result = cli_runner.invoke(app, ["vm", "device", "delete", "test-vm", "TPM", "--yes"])

    assert result.exit_code == 0
    mock_vm.devices.delete.assert_called_once_with(30)
