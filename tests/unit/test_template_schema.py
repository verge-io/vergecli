"""Tests for template schema validation and unit conversion."""

import pytest

from verge_cli.template.schema import (
    ValidationError,
    convert_units,
    merge_vm_set_defaults,
    validate_template,
)


class TestValidateTemplate:
    """Tests for schema validation."""

    def test_valid_minimal(self):
        data = {
            "apiVersion": "v4",
            "kind": "VirtualMachine",
            "vm": {"name": "test", "os_family": "linux"},
        }
        validate_template(data)  # Should not raise

    def test_missing_api_version(self):
        data = {"kind": "VirtualMachine", "vm": {"name": "test", "os_family": "linux"}}
        with pytest.raises(ValidationError):
            validate_template(data)

    def test_invalid_kind(self):
        data = {
            "apiVersion": "v4",
            "kind": "InvalidKind",
            "vm": {"name": "test", "os_family": "linux"},
        }
        with pytest.raises(ValidationError):
            validate_template(data)

    def test_missing_vm_for_virtual_machine(self):
        data = {"apiVersion": "v4", "kind": "VirtualMachine"}
        with pytest.raises(ValidationError):
            validate_template(data)

    def test_valid_vm_set(self):
        data = {
            "apiVersion": "v4",
            "kind": "VirtualMachineSet",
            "vms": [
                {"name": "vm-01", "os_family": "linux"},
                {"name": "vm-02", "os_family": "linux"},
            ],
        }
        validate_template(data)

    def test_invalid_os_family(self):
        data = {
            "apiVersion": "v4",
            "kind": "VirtualMachine",
            "vm": {"name": "test", "os_family": "invalid"},
        }
        with pytest.raises(ValidationError):
            validate_template(data)

    def test_ram_as_string(self):
        data = {
            "apiVersion": "v4",
            "kind": "VirtualMachine",
            "vm": {"name": "test", "os_family": "linux", "ram": "4GB"},
        }
        validate_template(data)  # Should accept string

    def test_ram_as_int(self):
        data = {
            "apiVersion": "v4",
            "kind": "VirtualMachine",
            "vm": {"name": "test", "os_family": "linux", "ram": 4096},
        }
        validate_template(data)  # Should accept int


class TestConvertUnits:
    """Tests for post-validation unit conversion."""

    def test_ram_string_to_mb(self):
        vm = {"name": "test", "os_family": "linux", "ram": "4GB"}
        convert_units(vm)
        assert vm["ram"] == 4096

    def test_ram_int_passthrough(self):
        vm = {"name": "test", "os_family": "linux", "ram": 2048}
        convert_units(vm)
        assert vm["ram"] == 2048

    def test_drive_size_to_gb(self):
        vm = {
            "name": "test",
            "os_family": "linux",
            "drives": [{"name": "OS", "size": "50GB", "media": "disk"}],
        }
        convert_units(vm)
        assert vm["drives"][0]["size"] == 50

    def test_no_ram_key(self):
        vm = {"name": "test", "os_family": "linux"}
        convert_units(vm)  # Should not raise


class TestMergeVmSetDefaults:
    """Tests for VirtualMachineSet default merging."""

    def test_basic_merge(self):
        defaults = {"os_family": "linux", "ram": "4GB", "cpu_cores": 2}
        vms = [
            {"name": "vm-01", "os_family": "linux"},
            {"name": "vm-02", "os_family": "linux", "ram": "8GB"},
        ]
        result = merge_vm_set_defaults(defaults, vms)
        assert result[0]["ram"] == "4GB"
        assert result[0]["cpu_cores"] == 2
        assert result[1]["ram"] == "8GB"  # Override
        assert result[1]["cpu_cores"] == 2  # Inherited

    def test_drives_override_not_merge(self):
        defaults = {
            "os_family": "linux",
            "drives": [{"name": "Default Disk", "size": "30GB"}],
        }
        vms = [
            {"name": "vm-01", "os_family": "linux"},
            {
                "name": "vm-02",
                "os_family": "linux",
                "drives": [{"name": "Custom Disk", "size": "100GB"}],
            },
        ]
        result = merge_vm_set_defaults(defaults, vms)
        assert len(result[0]["drives"]) == 1
        assert result[0]["drives"][0]["name"] == "Default Disk"
        assert result[1]["drives"][0]["name"] == "Custom Disk"

    def test_empty_defaults(self):
        result = merge_vm_set_defaults({}, [{"name": "vm-01", "os_family": "linux"}])
        assert result[0]["name"] == "vm-01"
