"""Tests for VM NIC sub-resource commands."""

from verge_cli.cli import app


def test_nic_list(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic list should list NICs on a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]

    result = cli_runner.invoke(app, ["vm", "nic", "list", "test-vm"])

    assert result.exit_code == 0
    assert "Primary" in result.output
    assert "DMZ" in result.output  # Network name may be truncated in table


def test_nic_get(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic get should show NIC details."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]
    mock_vm.nics.get.return_value = mock_nic

    result = cli_runner.invoke(app, ["vm", "nic", "get", "test-vm", "Primary Network"])

    assert result.exit_code == 0
    assert "Primary Network" in result.output


def test_nic_create(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic create should add a NIC to a VM."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.create.return_value = mock_nic

    result = cli_runner.invoke(
        app,
        ["vm", "nic", "create", "test-vm", "--network", "DMZ Internal", "--name", "eth0"],
    )

    assert result.exit_code == 0
    mock_vm.nics.create.assert_called_once()
    call_kwargs = mock_vm.nics.create.call_args[1]
    assert call_kwargs["network"] == "DMZ Internal"


def test_nic_delete(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic delete should remove a NIC."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]

    result = cli_runner.invoke(app, ["vm", "nic", "delete", "test-vm", "Primary Network", "--yes"])

    assert result.exit_code == 0
    mock_vm.nics.delete.assert_called_once_with(20)


def test_nic_update(cli_runner, mock_client, mock_vm, mock_nic):
    """vrg vm nic update should update NIC properties."""
    mock_client.vms.list.return_value = [mock_vm]
    mock_client.vms.get.return_value = mock_vm
    mock_vm.nics.list.return_value = [mock_nic]
    mock_vm.nics.update.return_value = mock_nic

    result = cli_runner.invoke(
        app, ["vm", "nic", "update", "test-vm", "Primary Network", "--name", "mgmt0"]
    )

    assert result.exit_code == 0
    mock_vm.nics.update.assert_called_once()
