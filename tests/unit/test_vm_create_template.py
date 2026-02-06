"""Tests for vrg vm create -f (template mode)."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_create_from_template(cli_runner, mock_client, tmp_path):
    """vrg vm create -f should create VM from template."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: template-vm\n"
        "  os_family: linux\n"
        "  ram: 4GB\n"
        "  cpu_cores: 2\n"
    )

    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "template-vm"
    mock_vm.machine_key = 38
    mock_vm.drives = MagicMock()
    mock_vm.nics = MagicMock()
    mock_vm.devices = MagicMock()
    mock_client.vms.create.return_value = mock_vm

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template)])

    assert result.exit_code == 0
    mock_client.vms.create.assert_called_once()
    call_kwargs = mock_client.vms.create.call_args[1]
    assert call_kwargs["name"] == "template-vm"
    assert call_kwargs["ram"] == 4096


def test_create_dry_run(cli_runner, tmp_path):
    """vrg vm create -f --dry-run should print plan without creating."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: dry-run-vm\n"
        "  os_family: linux\n"
        "  drives:\n"
        "    - name: OS Disk\n"
        "      size: 50GB\n"
        "      media: disk\n"
    )

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template), "--dry-run"])

    assert result.exit_code == 0
    assert "dry-run-vm" in result.output
    assert "OS Disk" in result.output
    assert "Dry run" in result.output


def test_create_with_set_override(cli_runner, mock_client, tmp_path):
    """vrg vm create -f --set should apply overrides."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\nkind: VirtualMachine\nvm:\n  name: original-name\n  os_family: linux\n"
    )

    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "overridden-name"
    mock_vm.machine_key = 38
    mock_vm.drives = MagicMock()
    mock_vm.nics = MagicMock()
    mock_vm.devices = MagicMock()
    mock_client.vms.create.return_value = mock_vm

    result = cli_runner.invoke(
        app, ["vm", "create", "-f", str(template), "--set", "vm.name=overridden-name"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.vms.create.call_args[1]
    assert call_kwargs["name"] == "overridden-name"


def test_create_vm_set(cli_runner, mock_client, tmp_path):
    """vrg vm create -f with VirtualMachineSet should create multiple VMs."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachineSet\n"
        "defaults:\n"
        "  os_family: linux\n"
        "  ram: 4GB\n"
        "vms:\n"
        "  - name: vm-01\n"
        "    os_family: linux\n"
        "  - name: vm-02\n"
        "    os_family: linux\n"
    )

    mock_vm1 = MagicMock()
    mock_vm1.key = 1
    mock_vm1.name = "vm-01"
    mock_vm1.machine_key = 38
    mock_vm1.drives = MagicMock()
    mock_vm1.nics = MagicMock()
    mock_vm1.devices = MagicMock()

    mock_vm2 = MagicMock()
    mock_vm2.key = 2
    mock_vm2.name = "vm-02"
    mock_vm2.machine_key = 39
    mock_vm2.drives = MagicMock()
    mock_vm2.nics = MagicMock()
    mock_vm2.devices = MagicMock()

    mock_client.vms.create.side_effect = [mock_vm1, mock_vm2]

    result = cli_runner.invoke(app, ["vm", "create", "-f", str(template)])

    assert result.exit_code == 0
    assert mock_client.vms.create.call_count == 2
