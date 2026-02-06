"""Tests for template builder (VM provisioning orchestrator)."""

from unittest.mock import MagicMock

import pytest

from verge_cli.template.builder import (
    ProvisionError,
    ProvisionResult,
    build_dry_run,
    provision_vm,
)


@pytest.fixture
def mock_ctx():
    """Create a mock context with a pyvergeos client."""
    ctx = MagicMock()
    mock_vm = MagicMock()
    mock_vm.key = 1
    mock_vm.name = "test-vm"
    mock_vm.machine_key = 38
    ctx.client.vms.create.return_value = mock_vm

    mock_drive = MagicMock()
    mock_drive.key = 10
    mock_drive.name = "OS Disk"
    mock_vm.drives.create.return_value = mock_drive

    mock_nic = MagicMock()
    mock_nic.key = 20
    mock_nic.name = "eth0"
    mock_vm.nics.create.return_value = mock_nic

    mock_device = MagicMock()
    mock_device.key = 30
    mock_device.name = "TPM"
    mock_vm.devices.create.return_value = mock_device

    return ctx


class TestProvisionVm:
    """Tests for single VM provisioning."""

    def test_minimal_vm(self, mock_ctx):
        config = {"name": "test-vm", "os_family": "linux"}
        result = provision_vm(mock_ctx.client, config)

        assert isinstance(result, ProvisionResult)
        assert result.vm_key == 1
        assert result.vm_name == "test-vm"
        mock_ctx.client.vms.create.assert_called_once()

    def test_vm_with_ram_and_cpu(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "ram": 4096,
            "cpu_cores": 4,
        }
        provision_vm(mock_ctx.client, config)

        call_kwargs = mock_ctx.client.vms.create.call_args[1]
        assert call_kwargs["ram"] == 4096
        assert call_kwargs["cpu_cores"] == 4

    def test_vm_with_drives(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "drives": [
                {
                    "name": "OS Disk",
                    "size": 50,
                    "interface": "virtio-scsi",
                    "media": "disk",
                    "preferred_tier": 3,
                },
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.drives.create.assert_called_once()
        assert result.drives_created == 1

    def test_vm_with_nics(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "nics": [
                {"name": "eth0", "network": 3, "interface": "virtio"},
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.nics.create.assert_called_once()
        assert result.nics_created == 1

    def test_vm_with_tpm(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "devices": [
                {"type": "tpm", "model": "crb", "version": "2.0"},
            ],
        }
        result = provision_vm(mock_ctx.client, config)

        vm = mock_ctx.client.vms.create.return_value
        vm.devices.create.assert_called_once()
        call_kwargs = vm.devices.create.call_args[1]
        assert call_kwargs["device_type"] == "tpm"
        assert call_kwargs["settings"]["model"] == "crb"
        assert result.devices_created == 1

    def test_vm_with_cloudinit(self, mock_ctx):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "cloudinit": {
                "datasource": "nocloud",
                "files": [
                    {"name": "user-data", "content": "#cloud-config\nhostname: test"},
                ],
            },
        }
        provision_vm(mock_ctx.client, config)

        call_kwargs = mock_ctx.client.vms.create.call_args[1]
        assert call_kwargs["cloudinit_datasource"] == "NoCloud"

    def test_drive_failure_partial_provision(self, mock_ctx):
        vm = mock_ctx.client.vms.create.return_value
        vm.drives.create.side_effect = Exception("API error")

        config = {
            "name": "test-vm",
            "os_family": "linux",
            "drives": [{"name": "OS", "size": 50, "media": "disk"}],
        }

        with pytest.raises(ProvisionError) as exc_info:
            provision_vm(mock_ctx.client, config)

        assert exc_info.value.result.vm_key == 1
        assert len(exc_info.value.result.errors) > 0


class TestBuildDryRun:
    """Tests for dry-run output."""

    def test_dry_run_single_vm(self):
        config = {
            "name": "test-vm",
            "os_family": "linux",
            "ram": 4096,
            "cpu_cores": 2,
            "drives": [{"name": "OS Disk", "size": 50, "media": "disk"}],
            "nics": [{"name": "eth0", "network": "DMZ Internal", "interface": "virtio"}],
        }
        output = build_dry_run(config)

        assert "test-vm" in output
        assert "OS Disk" in output
        assert "DMZ Internal" in output
