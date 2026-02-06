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
    schema: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    return schema


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
        msg = "Template validation failed:\n" + "\n".join(messages)
        raise ValidationError(msg, errors=[str(e.message) for e in errors])


def convert_units(vm_config: dict[str, Any]) -> None:
    """Convert human-friendly units to API values in-place.

    - ram: '4GB' -> 4096 (MB int)
    - drives[].size: '50GB' -> 50 (GB int)

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
