# Milestone 3: Template Loading & Validation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** YAML template loading with variable substitution, `--set` overrides, JSON schema validation, and `vrg vm validate` command.

**Architecture:** `template/loader.py` handles two-pass variable substitution and `--set` application. `template/schema.py` validates against a JSON schema and converts units. The `vrg vm validate -f` command wires them together.

**Tech Stack:** Python 3.10+, PyYAML, jsonschema, pytest

**Depends on:** M1 (units.py for unit conversion)

---

### Task 1: Finalize JSON Schema

**Files:**
- Create: `src/verge_cli/schemas/vrg-vm-template.schema.json`

**Context:** Starting from `.claude/reference/specs/vm-schema.json`. Refinements needed:
1. `deviceSpec` — TPM-only: require `type`, add `model`/`version` enums, remove `resource_group` requirement
2. `ram` — `oneOf: [integer, string-with-pattern]` (not string-only)
3. `os_family` — add to `vmSpec.required`
4. `name` pattern — allow `${VAR}` syntax

**Step 1: Create the schemas directory and final schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://verge.io/schemas/vrg/v4.json",
  "title": "VergeOS VM Template",
  "description": "Declarative VM definition for the VergeOS CLI (.vrg.yaml)",
  "type": "object",
  "required": ["apiVersion", "kind"],
  "properties": {
    "apiVersion": {
      "type": "string",
      "enum": ["v4"]
    },
    "kind": {
      "type": "string",
      "enum": ["VirtualMachine", "VirtualMachineSet"]
    },
    "vars": {
      "type": "object",
      "description": "Variable definitions for ${VAR} substitution",
      "additionalProperties": { "type": "string" }
    },
    "vm": { "$ref": "#/definitions/vmSpec" },
    "defaults": { "$ref": "#/definitions/vmSpec" },
    "vms": {
      "type": "array",
      "items": { "$ref": "#/definitions/vmSpec" }
    }
  },
  "oneOf": [
    {
      "properties": { "kind": { "const": "VirtualMachine" } },
      "required": ["vm"]
    },
    {
      "properties": { "kind": { "const": "VirtualMachineSet" } },
      "required": ["vms"]
    }
  ],
  "definitions": {
    "sizeValue": {
      "description": "Human-friendly size (e.g., '4GB') or integer",
      "oneOf": [
        { "type": "integer", "minimum": 1 },
        { "type": "string", "pattern": "^\\d+(\\.\\d+)?\\s*(MB|GB|TB)$" }
      ]
    },
    "nameOrId": {
      "description": "Resource name (string) or numeric ID",
      "oneOf": [
        { "type": "integer" },
        { "type": "string" }
      ]
    },
    "vmSpec": {
      "type": "object",
      "required": ["name", "os_family"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "enabled": { "type": "boolean", "default": true },
        "os_family": {
          "type": "string",
          "enum": ["linux", "windows", "freebsd", "other"]
        },
        "os_description": { "type": "string" },
        "cpu_cores": { "type": "integer", "minimum": 1, "default": 1 },
        "cpu_type": { "type": "string", "default": "auto" },
        "ram": { "$ref": "#/definitions/sizeValue" },
        "machine_type": {
          "type": "string",
          "enum": ["q35", "pc"],
          "default": "q35"
        },
        "boot_order": {
          "type": "string",
          "enum": ["d", "cd", "cdn", "c", "dc", "n", "nd", "do"],
          "default": "cd"
        },
        "allow_hotplug": { "type": "boolean", "default": true },
        "uefi": { "type": "boolean", "default": false },
        "secure_boot": { "type": "boolean", "default": false },
        "console": {
          "type": "string",
          "enum": ["vnc", "spice"],
          "default": "vnc"
        },
        "video": {
          "type": "string",
          "enum": ["std", "cirrus", "vmware", "qxl", "virtio", "none"],
          "default": "std"
        },
        "guest_agent": { "type": "boolean", "default": false },
        "rtc_base": {
          "type": "string",
          "enum": ["utc", "localtime"],
          "default": "utc"
        },
        "cluster": { "$ref": "#/definitions/nameOrId" },
        "failover_cluster": { "$ref": "#/definitions/nameOrId" },
        "preferred_node": { "$ref": "#/definitions/nameOrId" },
        "ha_group": { "type": "string" },
        "snapshot_profile": { "$ref": "#/definitions/nameOrId" },
        "power_on_after_create": { "type": "boolean", "default": false },
        "advanced_options": { "type": "string" },
        "cloudinit": { "$ref": "#/definitions/cloudinitSpec" },
        "drives": {
          "type": "array",
          "items": { "$ref": "#/definitions/driveSpec" }
        },
        "nics": {
          "type": "array",
          "items": { "$ref": "#/definitions/nicSpec" }
        },
        "devices": {
          "type": "array",
          "items": { "$ref": "#/definitions/deviceSpec" }
        }
      }
    },
    "cloudinitSpec": {
      "type": "object",
      "properties": {
        "datasource": {
          "type": "string",
          "enum": ["nocloud", "config_drive_v2"]
        },
        "files": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "content"],
            "properties": {
              "name": {
                "type": "string",
                "enum": ["user-data", "meta-data", "vendor-data", "network-data"]
              },
              "content": { "type": "string" }
            }
          }
        }
      }
    },
    "driveSpec": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "media": {
          "type": "string",
          "enum": ["disk", "cdrom", "import", "clone", "efidisk"],
          "default": "disk"
        },
        "interface": {
          "type": "string",
          "enum": ["virtio-scsi", "virtio", "ide", "ahci", "lsi53c895a", "nvme"],
          "default": "virtio-scsi"
        },
        "size": { "$ref": "#/definitions/sizeValue" },
        "preferred_tier": {
          "type": "integer",
          "minimum": 1,
          "maximum": 5,
          "default": 3
        },
        "media_source": { "$ref": "#/definitions/nameOrId" },
        "enabled": { "type": "boolean", "default": true },
        "order": { "type": "integer" },
        "asset": { "type": "string" }
      }
    },
    "nicSpec": {
      "type": "object",
      "required": ["network"],
      "properties": {
        "name": { "type": "string" },
        "description": { "type": "string" },
        "interface": {
          "type": "string",
          "enum": ["virtio", "e1000", "e1000e", "rtl8139", "pcnet", "igb", "vmxnet3"],
          "default": "virtio"
        },
        "enabled": { "type": "boolean", "default": true },
        "network": { "$ref": "#/definitions/nameOrId" },
        "mac": {
          "type": "string",
          "pattern": "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
        },
        "asset": { "type": "string" }
      }
    },
    "deviceSpec": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "name": { "type": "string" },
        "type": {
          "type": "string",
          "enum": ["tpm"]
        },
        "model": {
          "type": "string",
          "enum": ["tis", "crb"],
          "default": "crb"
        },
        "version": {
          "type": "string",
          "enum": ["1.2", "2.0"],
          "default": "2.0"
        }
      }
    }
  }
}
```

**Step 2: Verify schema is valid JSON**

Run: `uv run python -c "import json; json.load(open('src/verge_cli/schemas/vrg-vm-template.schema.json'))"`
Expected: No error

**Step 3: Commit**

```bash
git add src/verge_cli/schemas/vrg-vm-template.schema.json
git commit -m "feat: add JSON schema for .vrg.yaml template validation"
```

---

### Task 2: Create template/loader.py

**Files:**
- Create: `src/verge_cli/template/loader.py`
- Create: `tests/unit/test_template_loader.py`

**Context:**
- Two-pass processing: extract `vars:` block → merge with env → substitute → parse
- `--set` overrides: dot-path upsert after YAML parse
- Variable syntax: `${VAR}` (required), `${VAR:-default}` (with fallback)

**Step 1: Write failing tests**

```python
# tests/unit/test_template_loader.py
"""Tests for template YAML loader with variable substitution."""

import os

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
        assert data["vm"]["cpu_cores"] == "4"

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
            "apiVersion: v4\n"
            "kind: VirtualMachine\n"
            "vm:\n"
            "  name: my-vm\n"
            "  os_family: linux\n"
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
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_loader.py -v`
Expected: FAIL

**Step 3: Implement loader.py**

```python
# src/verge_cli/template/loader.py
"""YAML template loading with variable substitution and --set overrides."""

from __future__ import annotations

import os
import re

import yaml


# Match ${VAR} or ${VAR:-default}
_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-(.*?))?\}")


def substitute_variables(text: str, variables: dict[str, str]) -> str:
    """Substitute ${VAR} and ${VAR:-default} in text.

    Args:
        text: Raw text with variable references.
        variables: Variable name→value mapping.

    Returns:
        Text with variables substituted.

    Raises:
        ValueError: If a required variable (no default) is missing.
    """
    missing: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)

        if var_name in variables:
            return variables[var_name]
        if default is not None:
            return default

        missing.append(var_name)
        return match.group(0)

    result = _VAR_PATTERN.sub(replacer, text)

    if missing:
        msg = f"Unresolved template variables: {', '.join(missing)}"
        raise ValueError(msg)

    return result


def apply_set_overrides(data: dict, overrides: list[str]) -> None:
    """Apply --set dot-path overrides to parsed data (in-place).

    Args:
        data: Parsed template dict.
        overrides: List of 'dot.path=value' strings.

    Raises:
        ValueError: If override format is invalid.
    """
    for override in overrides:
        if "=" not in override:
            msg = f"Invalid --set format: '{override}'. Expected 'key.path=value'."
            raise ValueError(msg)

        path, value = override.split("=", 1)
        parts = path.split(".")

        # Navigate to parent, creating intermediate dicts as needed
        target = data
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value


def _extract_vars_block(text: str) -> dict[str, str]:
    """Quick-parse YAML to extract just the vars: block.

    Args:
        text: Raw YAML text.

    Returns:
        Dict of variable definitions.
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}

    if isinstance(data, dict) and "vars" in data:
        vars_block = data["vars"]
        if isinstance(vars_block, dict):
            return {k: str(v) for k, v in vars_block.items()}

    return {}


def load_template(
    path: str,
    set_overrides: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
) -> dict:
    """Load a .vrg.yaml template with variable substitution and overrides.

    Processing pipeline:
    1. Read raw YAML text
    2. Extract vars: block (pass 1)
    3. Merge with environment variables (env wins)
    4. Substitute ${VAR} references (pass 2)
    5. Full YAML parse (pass 3)
    6. Apply --set overrides
    7. Return parsed dict

    Args:
        path: Path to .vrg.yaml file.
        set_overrides: List of 'key.path=value' overrides.
        env_vars: Environment variable overrides (defaults to os.environ).

    Returns:
        Parsed and processed template dict.

    Raises:
        FileNotFoundError: If template file doesn't exist.
        ValueError: If variables can't be resolved.
        yaml.YAMLError: If YAML is malformed.
    """
    with open(path) as f:
        raw_text = f.read()

    # Pass 1: extract vars block
    template_vars = _extract_vars_block(raw_text)

    # Merge with env vars (env takes precedence)
    effective_env = env_vars if env_vars is not None else dict(os.environ)
    combined_vars = {**template_vars, **effective_env}

    # Pass 2: substitute variables
    substituted_text = substitute_variables(raw_text, combined_vars)

    # Pass 3: full YAML parse
    data = yaml.safe_load(substituted_text)

    if not isinstance(data, dict):
        msg = "Template must be a YAML mapping at the top level."
        raise ValueError(msg)

    # Remove vars block from output (consumed)
    data.pop("vars", None)

    # Apply --set overrides
    if set_overrides:
        apply_set_overrides(data, set_overrides)

    return data
```

**Step 4: Run tests**

Run: `uv run pytest tests/unit/test_template_loader.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/verge_cli/template/loader.py tests/unit/test_template_loader.py
git commit -m "feat: add template loader with variable substitution and --set overrides"
```

---

### Task 3: Create template/schema.py

**Files:**
- Create: `src/verge_cli/template/schema.py`
- Create: `tests/unit/test_template_schema.py`

**Context:**
- Validates parsed template dict against the JSON schema
- After validation, converts human-friendly units to API values (RAM → MB, disk size → GB)
- For `VirtualMachineSet`, merges `defaults` into each `vms[]` entry

**Step 1: Write failing tests**

```python
# tests/unit/test_template_schema.py
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
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_template_schema.py -v`
Expected: FAIL

**Step 3: Implement schema.py**

```python
# src/verge_cli/template/schema.py
"""Template schema validation and unit conversion."""

from __future__ import annotations

import importlib.resources
import json
from typing import Any

import jsonschema

from verge_cli.template.units import parse_disk_size, parse_ram


class ValidationError(Exception):
    """Template validation error with details."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        self.errors = errors or []
        super().__init__(message)


def _load_schema() -> dict[str, Any]:
    """Load the JSON schema from package resources."""
    schema_path = importlib.resources.files("verge_cli.schemas").joinpath(
        "vrg-vm-template.schema.json"
    )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_template(data: dict[str, Any]) -> None:
    """Validate a parsed template against the JSON schema.

    Args:
        data: Parsed template dict.

    Raises:
        ValidationError: If validation fails.
    """
    schema = _load_schema()

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

    if errors:
        messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            messages.append(f"  {path}: {error.message}")
        msg = f"Template validation failed:\n" + "\n".join(messages)
        raise ValidationError(msg, errors=[str(e.message) for e in errors])


def convert_units(vm_config: dict[str, Any]) -> None:
    """Convert human-friendly units to API values in-place.

    - ram: '4GB' → 4096 (MB int)
    - drives[].size: '50GB' → 50 (GB int)

    Args:
        vm_config: Single VM configuration dict.
    """
    if "ram" in vm_config and isinstance(vm_config["ram"], str):
        vm_config["ram"] = parse_ram(vm_config["ram"])

    for drive in vm_config.get("drives", []):
        if "size" in drive and isinstance(drive["size"], str):
            drive["size"] = parse_disk_size(drive["size"])


def merge_vm_set_defaults(
    defaults: dict[str, Any],
    vms: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge VirtualMachineSet defaults into each VM config.

    VM values override defaults. List fields (drives, nics, devices)
    are replaced entirely, not merged.

    Args:
        defaults: Default configuration.
        vms: List of individual VM configurations.

    Returns:
        List of merged VM configurations.
    """
    result = []
    for vm in vms:
        merged = {**defaults, **vm}
        result.append(merged)
    return result
```

**Step 4: Create `__init__.py` for schemas package**

```python
# src/verge_cli/schemas/__init__.py
"""JSON schemas for template validation."""
```

**Step 5: Run tests**

Run: `uv run pytest tests/unit/test_template_schema.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/verge_cli/template/schema.py src/verge_cli/schemas/__init__.py tests/unit/test_template_schema.py
git commit -m "feat: add template schema validation and unit conversion"
```

---

### Task 4: Add `vrg vm validate` command

**Files:**
- Modify: `src/verge_cli/commands/vm.py`

**Step 1: Add the validate command**

Add to `vm.py`:

```python
@app.command("validate")
@handle_errors()
def vm_validate(
    ctx: typer.Context,
    file: Annotated[
        str,
        typer.Option("--file", "-f", help="Path to .vrg.yaml template file"),
    ],
    set_overrides: Annotated[
        list[str] | None,
        typer.Option("--set", help="Override template values (key.path=value)"),
    ] = None,
) -> None:
    """Validate a VM template file."""
    from verge_cli.template.loader import load_template
    from verge_cli.template.schema import ValidationError, validate_template

    try:
        data = load_template(file, set_overrides=set_overrides or [])
        validate_template(data)
    except (ValueError, ValidationError) as e:
        typer.echo(f"Validation failed: {e}", err=True)
        raise typer.Exit(8)

    output_success(f"Template '{file}' is valid.", quiet=get_context(ctx).quiet if ctx.obj else False)
```

Note: The `validate` command doesn't need an API connection — it only parses and validates locally. But we still use `handle_errors()` for consistent error formatting. Don't call `get_context()` for the client — just use `ctx.obj` directly for quiet flag if available.

Actually, simpler approach — just use typer.echo directly since validate doesn't need the API:

```python
@app.command("validate")
@handle_errors()
def vm_validate(
    ctx: typer.Context,
    file: Annotated[
        str,
        typer.Option("--file", "-f", help="Path to .vrg.yaml template file"),
    ],
    set_overrides: Annotated[
        list[str] | None,
        typer.Option("--set", help="Override template values (key.path=value)"),
    ] = None,
) -> None:
    """Validate a VM template file without creating anything."""
    from verge_cli.template.loader import load_template
    from verge_cli.template.schema import ValidationError, validate_template

    try:
        data = load_template(file, set_overrides=set_overrides or [])
        validate_template(data)
    except (ValueError, ValidationError) as e:
        typer.echo(f"Validation failed: {e}", err=True)
        raise typer.Exit(8)

    typer.echo(f"✓ Template '{file}' is valid.")
```

**Step 2: Write test**

Add to a new test file or inline:

```python
# tests/unit/test_vm_validate.py
"""Tests for vrg vm validate command."""

from verge_cli.cli import app


def test_validate_valid_template(cli_runner, tmp_path):
    """vrg vm validate should accept a valid template."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: test-vm\n"
        "  os_family: linux\n"
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid_template(cli_runner, tmp_path):
    """vrg vm validate should reject an invalid template."""
    template = tmp_path / "bad.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vm:\n"
        "  name: test-vm\n"
        '  os_family: "invalid"\n'
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code != 0


def test_validate_missing_file(cli_runner):
    """vrg vm validate should error on missing file."""
    result = cli_runner.invoke(app, ["vm", "validate", "-f", "/nonexistent.vrg.yaml"])
    assert result.exit_code != 0


def test_validate_with_variables(cli_runner, tmp_path, monkeypatch):
    """vrg vm validate should resolve variables."""
    template = tmp_path / "test.vrg.yaml"
    template.write_text(
        "apiVersion: v4\n"
        "kind: VirtualMachine\n"
        "vars:\n"
        "  env: test\n"
        "vm:\n"
        '  name: "${env}-vm"\n'
        "  os_family: linux\n"
    )

    result = cli_runner.invoke(app, ["vm", "validate", "-f", str(template)])
    assert result.exit_code == 0
```

**Step 3: Run tests**

Run: `uv run pytest tests/unit/test_vm_validate.py -v`
Expected: All PASS

**Step 4: Run full suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/verge_cli/commands/vm.py tests/unit/test_vm_validate.py
git commit -m "feat: add vrg vm validate command for template validation"
```

---

## Milestone 3 Complete

After M3 you should have:
- `src/verge_cli/schemas/vrg-vm-template.schema.json` — finalized JSON schema
- `src/verge_cli/template/loader.py` — two-pass variable substitution + --set overrides
- `src/verge_cli/template/schema.py` — JSON schema validation + unit conversion + VirtualMachineSet merge
- `vrg vm validate -f template.vrg.yaml` — working command
- Full test coverage for loader, schema, and validate command
