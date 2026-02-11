"""Tests for template YAML loader with variable substitution."""

import pytest

from verge_cli.template.loader import (
    apply_set_overrides,
    load_template,
    substitute_variables,
)


class TestSubstituteVariables:
    """Tests for variable substitution."""

    def test_simple_var(self):
        text = "name: ${VM_NAME}"
        result = substitute_variables(text, {"VM_NAME": "web-01"})
        assert result == "name: web-01"

    def test_var_with_default(self):
        text = "ram: ${VM_RAM:-4GB}"
        result = substitute_variables(text, {})
        assert result == "ram: 4GB"

    def test_var_with_default_overridden(self):
        text = "ram: ${VM_RAM:-4GB}"
        result = substitute_variables(text, {"VM_RAM": "8GB"})
        assert result == "ram: 8GB"

    def test_multiple_vars(self):
        text = "name: ${ENV}-${ROLE}-01"
        result = substitute_variables(text, {"ENV": "prod", "ROLE": "web"})
        assert result == "name: prod-web-01"

    def test_missing_required_var(self):
        text = "cluster: ${CLUSTER_ID}"
        with pytest.raises(ValueError, match="CLUSTER_ID"):
            substitute_variables(text, {})

    def test_no_vars(self):
        text = "name: my-vm"
        result = substitute_variables(text, {})
        assert result == "name: my-vm"

    def test_empty_default(self):
        text = "desc: ${DESC:-}"
        result = substitute_variables(text, {})
        assert result == "desc: "


class TestApplySetOverrides:
    """Tests for --set dot-path overrides."""

    def test_simple_set(self):
        data = {"vm": {"name": "old"}}
        apply_set_overrides(data, ["vm.name=new"])
        assert data["vm"]["name"] == "new"

    def test_nested_set(self):
        data = {"vm": {"nested": {"key": "old"}}}
        apply_set_overrides(data, ["vm.nested.key=new"])
        assert data["vm"]["nested"]["key"] == "new"

    def test_upsert_new_key(self):
        data = {"vm": {"name": "test"}}
        apply_set_overrides(data, ["vm.cpu_cores=4"])
        assert data["vm"]["cpu_cores"] == 4

    def test_multiple_overrides(self):
        data = {"vm": {"name": "old", "ram": "4GB"}}
        apply_set_overrides(data, ["vm.name=new", "vm.ram=8GB"])
        assert data["vm"]["name"] == "new"
        assert data["vm"]["ram"] == "8GB"

    def test_invalid_format(self):
        data = {"vm": {}}
        with pytest.raises(ValueError, match="Invalid --set"):
            apply_set_overrides(data, ["invalid"])


class TestLoadTemplate:
    """Tests for full template loading pipeline."""

    def test_minimal_template(self, tmp_path):
        template = tmp_path / "test.vrg.yaml"
        template.write_text(
            "apiVersion: v4\nkind: VirtualMachine\nvm:\n  name: my-vm\n  os_family: linux\n"
        )
        result = load_template(str(template))
        assert result["vm"]["name"] == "my-vm"
        assert result["kind"] == "VirtualMachine"

    def test_with_vars_block(self, tmp_path):
        template = tmp_path / "test.vrg.yaml"
        template.write_text(
            "apiVersion: v4\n"
            "kind: VirtualMachine\n"
            "vars:\n"
            "  env: staging\n"
            "vm:\n"
            '  name: "${env}-web"\n'
            "  os_family: linux\n"
        )
        result = load_template(str(template))
        assert result["vm"]["name"] == "staging-web"

    def test_env_overrides_vars(self, tmp_path, monkeypatch):
        template = tmp_path / "test.vrg.yaml"
        template.write_text(
            "apiVersion: v4\n"
            "kind: VirtualMachine\n"
            "vars:\n"
            "  env: staging\n"
            "vm:\n"
            '  name: "${env}-web"\n'
            "  os_family: linux\n"
        )
        monkeypatch.setenv("env", "production")
        result = load_template(str(template))
        assert result["vm"]["name"] == "production-web"

    def test_with_set_overrides(self, tmp_path):
        template = tmp_path / "test.vrg.yaml"
        template.write_text(
            "apiVersion: v4\n"
            "kind: VirtualMachine\n"
            "vm:\n"
            "  name: my-vm\n"
            "  os_family: linux\n"
            "  ram: 4GB\n"
        )
        result = load_template(str(template), set_overrides=["vm.ram=8GB"])
        assert result["vm"]["ram"] == "8GB"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_template("/nonexistent/file.vrg.yaml")

    def test_virtual_machine_set(self, tmp_path):
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
            "    ram: 8GB\n"
        )
        result = load_template(str(template))
        assert result["kind"] == "VirtualMachineSet"
        assert len(result["vms"]) == 2
