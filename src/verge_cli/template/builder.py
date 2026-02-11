"""Template builder — orchestrates VM provisioning via pyvergeos SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Mapping from template cloudinit datasource names to SDK values
_CLOUDINIT_DATASOURCE_MAP = {
    "nocloud": "NoCloud",
    "config_drive_v2": "ConfigDrive",
}

# VM fields that map directly to client.vms.create() kwargs
_VM_CREATE_FIELDS = {
    "name",
    "ram",
    "cpu_cores",
    "description",
    "os_family",
    "machine_type",
    "boot_order",
    "allow_hotplug",
    "uefi",
    "secure_boot",
    "console",
    "video",
    "guest_agent",
    "rtc_base",
    "cluster",
    "failover_cluster",
    "preferred_node",
    "ha_group",
    "snapshot_profile",
    "cpu_type",
    "enabled",
}


@dataclass
class ProvisionResult:
    """Result of provisioning a single VM."""

    vm_key: int
    vm_name: str
    drives_created: int = 0
    nics_created: int = 0
    devices_created: int = 0
    powered_on: bool = False
    errors: list[str] = field(default_factory=list)


class ProvisionError(Exception):
    """Provisioning failed (VM may be partially created)."""

    def __init__(self, message: str, result: ProvisionResult) -> None:
        self.result = result
        super().__init__(message)


def provision_vm(client: Any, vm_config: dict[str, Any]) -> ProvisionResult:
    """Provision a single VM from a validated, unit-converted config dict.

    Orchestration:
    1. Create VM via client.vms.create()
    2. Update cloud-init files if datasource configured
    3. Create drives via vm.drives.create()
    4. Create NICs via vm.nics.create()
    5. Create devices via vm.devices.create()
    6. Power on if requested

    Args:
        client: pyvergeos VergeClient.
        vm_config: Validated VM configuration dict (units already converted).

    Returns:
        ProvisionResult with creation details.

    Raises:
        ProvisionError: If any sub-resource creation fails (VM still exists).
    """
    # 1. Build VM create kwargs
    vm_kwargs: dict[str, Any] = {}
    for key in _VM_CREATE_FIELDS:
        if key in vm_config:
            vm_kwargs[key] = vm_config[key]

    # Handle machine_type — template uses 'q35', SDK expects 'pc-q35-10.0'
    if "machine_type" in vm_kwargs:
        mt = vm_kwargs["machine_type"]
        if mt == "q35":
            vm_kwargs["machine_type"] = "pc-q35-10.0"

    # Handle cloud-init datasource (API auto-creates /user-data and /meta-data)
    cloudinit = vm_config.get("cloudinit")
    if cloudinit:
        ds = cloudinit.get("datasource", "")
        vm_kwargs["cloudinit_datasource"] = _CLOUDINIT_DATASOURCE_MAP.get(ds, ds)

    # Handle advanced_options as kwargs pass-through
    if "advanced_options" in vm_config:
        vm_kwargs["advanced_options"] = vm_config["advanced_options"]

    # 2. Create VM
    vm = client.vms.create(**vm_kwargs)
    result = ProvisionResult(vm_key=int(vm.key), vm_name=str(vm.name))

    # 3. Update cloud-init files with template contents
    # The API auto-creates /user-data and /meta-data when datasource is set,
    # so we update them rather than creating new ones.
    if cloudinit:
        _update_cloudinit_files(client, int(vm.key), cloudinit, result)

    # 4. Create drives
    for drive_config in vm_config.get("drives", []):
        try:
            drive_kwargs = _build_drive_kwargs(drive_config)
            vm.drives.create(**drive_kwargs)
            result.drives_created += 1
        except Exception as e:
            result.errors.append(f"Drive '{drive_config.get('name', '?')}': {e}")

    # 5. Create NICs
    for nic_config in vm_config.get("nics", []):
        try:
            nic_kwargs = _build_nic_kwargs(nic_config)
            vm.nics.create(**nic_kwargs)
            result.nics_created += 1
        except Exception as e:
            result.errors.append(f"NIC '{nic_config.get('name', '?')}': {e}")

    # 6. Create devices (TPM only for now)
    for device_config in vm_config.get("devices", []):
        try:
            device_kwargs = _build_device_kwargs(device_config)
            vm.devices.create(**device_kwargs)
            result.devices_created += 1
        except Exception as e:
            result.errors.append(f"Device '{device_config.get('name', '?')}': {e}")

    # 7. Power on if requested
    if vm_config.get("power_on_after_create", False):
        try:
            vm.power_on()
            result.powered_on = True
        except Exception as e:
            result.errors.append(f"Power on: {e}")

    # If there were errors, raise with the partial result
    if result.errors:
        msg = f"VM '{result.vm_name}' created (key: {result.vm_key}) but with errors:\n"
        msg += "\n".join(f"  - {e}" for e in result.errors)
        raise ProvisionError(msg, result)

    return result


def _update_cloudinit_files(
    client: Any,
    vm_key: int,
    cloudinit: dict[str, Any],
    result: ProvisionResult,
) -> None:
    """Update auto-created cloud-init files with template contents.

    When cloudinit_datasource is set, the API auto-creates /user-data and
    /meta-data files. This function updates those files with template content.
    """
    from pyvergeos.resources.cloudinit_files import CloudInitFileManager

    ci_mgr = CloudInitFileManager(client)
    existing = ci_mgr.list_for_vm(vm_key)
    # Build lookup: name -> key
    existing_map = {f.name: int(f.key) for f in existing}

    for file_spec in cloudinit.get("files", []):
        name = file_spec["name"]
        if not name.startswith("/"):
            name = f"/{name}"
        content = file_spec.get("content", "")
        try:
            if name in existing_map:
                ci_mgr.update(existing_map[name], contents=content)
            else:
                ci_mgr.create(vm_key=vm_key, name=name, contents=content)
        except Exception as e:
            result.errors.append(f"Cloud-init file '{name}': {e}")


def _build_drive_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate drive template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {}
    if "name" in config:
        kwargs["name"] = config["name"]
    if "size" in config:
        kwargs["size_gb"] = config["size"]  # Already converted to GB by convert_units
    if "interface" in config:
        kwargs["interface"] = config["interface"]
    if "media" in config:
        kwargs["media"] = config["media"]
    if "preferred_tier" in config:
        kwargs["tier"] = config["preferred_tier"]
    if "description" in config:
        kwargs["description"] = config["description"]
    if "media_source" in config:
        kwargs["media_source"] = config["media_source"]
    if "enabled" in config:
        kwargs["enabled"] = config["enabled"]
    return kwargs


def _build_nic_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate NIC template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {}
    if "network" in config:
        kwargs["network"] = config["network"]
    if "name" in config:
        kwargs["name"] = config["name"]
    if "interface" in config:
        kwargs["interface"] = config["interface"]
    if "mac" in config:
        kwargs["mac_address"] = config["mac"]
    if "description" in config:
        kwargs["description"] = config["description"]
    if "enabled" in config:
        kwargs["enabled"] = config["enabled"]
    return kwargs


def _build_device_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    """Translate device template config to SDK create kwargs."""
    kwargs: dict[str, Any] = {
        "device_type": config.get("type", "tpm"),
    }
    settings: dict[str, str] = {}
    if "model" in config:
        settings["model"] = config["model"]
    if "version" in config:
        # API expects "1" or "2", not "1.0" or "2.0"
        ver = str(config["version"])
        if ver.endswith(".0"):
            ver = ver[:-2]
        settings["version"] = ver
    if settings:
        kwargs["settings"] = settings
    if "name" in config:
        kwargs["name"] = config["name"]
    return kwargs


def build_dry_run(vm_config: dict[str, Any]) -> str:
    """Build a human-readable dry-run summary for a VM config.

    Args:
        vm_config: Validated VM configuration dict.

    Returns:
        Multi-line string describing what would be created.
    """
    lines: list[str] = []
    name = vm_config.get("name", "unnamed")
    os_fam = vm_config.get("os_family", "?")
    cores = vm_config.get("cpu_cores", 1)
    ram = vm_config.get("ram", "1GB")
    mt = vm_config.get("machine_type", "q35")

    lines.append(f"VM: {name} ({os_fam}, {cores} cores, {ram} RAM, {mt})")

    api_calls = 1  # VM create

    for i, drive in enumerate(vm_config.get("drives", []), 1):
        d_name = drive.get("name", f"Drive {i}")
        d_media = drive.get("media", "disk")
        d_iface = drive.get("interface", "virtio-scsi")
        d_size = drive.get("size", "")
        d_tier = drive.get("preferred_tier", "")
        d_src = drive.get("media_source", "")
        parts = [d_media, d_iface]
        if d_size:
            parts.append(f"{d_size}GB")
        if d_tier:
            parts.append(f"tier {d_tier}")
        if d_src:
            parts.append(f"media: {d_src}")
        lines.append(f'  Drive {i}: "{d_name}" — {", ".join(parts)}')
        api_calls += 1

    for i, nic in enumerate(vm_config.get("nics", []), 1):
        n_name = nic.get("name", f"NIC {i}")
        n_iface = nic.get("interface", "virtio")
        n_net = nic.get("network", "?")
        lines.append(f'  NIC {i}: "{n_name}" — {n_iface}, network: {n_net}')
        api_calls += 1

    for i, dev in enumerate(vm_config.get("devices", []), 1):
        d_name = dev.get("name", f"Device {i}")
        d_type = dev.get("type", "?")
        d_model = dev.get("model", "")
        d_ver = dev.get("version", "")
        lines.append(f'  Device {i}: "{d_name}" — {d_type} ({d_model} v{d_ver})')
        api_calls += 1

    cloudinit = vm_config.get("cloudinit")
    if cloudinit:
        ds = cloudinit.get("datasource", "?")
        files = cloudinit.get("files", [])
        file_names = ", ".join(f["name"] for f in files)
        lines.append(f"  Cloud-init: {ds} ({len(files)} files: {file_names})")

    power = vm_config.get("power_on_after_create", False)
    lines.append(f"  Power on after create: {'yes' if power else 'no'}")
    if power:
        api_calls += 1

    lines.append(f"\n{api_calls} API calls would be made.")
    return "\n".join(lines)
