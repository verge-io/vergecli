# vrg vm Template Specification (`.vrg.yaml`)

A declarative, human-readable YAML format for defining VergeOS virtual machines.
Inspired by Terraform HCL, Azure ARM templates, and cloud-init — but designed specifically
for the VergeOS API and CLI workflow.

---

## Design Principles

1. **YAML over JSON** — easier to read/write by hand, supports comments, widely tooled.
2. **Human-friendly units** — `4GB` instead of `4294967296` bytes. The CLI translates.
3. **Sensible defaults** — only `name` and `os_family` are truly required; everything else falls back to sane defaults.
4. **1:1 API mapping** — every field maps directly to a VergeOS API parameter. No magic.
5. **Composable** — drives, NICs, devices, and cloud-init are inline sections, but the CLI orchestrates the multi-step API calls (create VM → get machine key → add drives → add NICs → add devices).

---

## File Extension

`.vrg.yaml` (VergeOS Template) — or just `.yaml` / `.yml`. The CLI should accept any.

---

## Minimal Example

```yaml
# The simplest possible VM definition
apiVersion: v4
kind: VirtualMachine

vm:
  name: my-web-server
  os_family: linux
```

Everything else gets defaults: 1 core, 1GB RAM, q35 machine type, no drives, no NICs.

---

## Full Example — Linux Web Server

```yaml
apiVersion: v4
kind: VirtualMachine

vm:
  name: web-server-01
  description: "Production web server"
  enabled: true
  os_family: linux               # linux | windows | freebsd | other
  os_description: "Ubuntu 24.04 LTS"

  # Compute
  cpu_cores: 4
  cpu_type: auto                 # auto | Broadwell | Cascadelake-Server | etc.
  ram: 8GB                       # Accepts: 512MB, 4GB, 16GB — CLI converts to MB

  # Machine
  machine_type: q35              # q35 | pc
  boot_order: cd                 # d | cd | cdn | c | dc | n | nd | do
  allow_hotplug: true
  uefi: true
  secure_boot: false

  # Display / Console
  console: vnc                   # vnc | spice
  video: virtio                  # std | cirrus | vmware | qxl | virtio | none

  # Agent & Clock
  guest_agent: true
  rtc_base: utc                  # utc | localtime

  # Scheduling & HA
  cluster: 1                     # Cluster ID or name (CLI resolves names → IDs)
  failover_cluster: ~            # null = none
  preferred_node: ~
  ha_group: "web"                # Anti-affinity group (no + prefix)
  # ha_group: "+web"             # Affinity group (+ prefix = same node)

  # Power
  power_on_after_create: false   # Maps to API `powerstate` field

  # Snapshot
  snapshot_profile: ~            # Snapshot profile name or ID; null = inherit system

  # Cloud-Init
  cloudinit:
    datasource: nocloud          # nocloud | config_drive_v2 | ~ (none)
    files:
      - name: user-data
        content: |
          #cloud-config
          hostname: web-server-01
          users:
            - name: admin
              sudo: ALL=(ALL) NOPASSWD:ALL
              ssh_authorized_keys:
                - ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...
          packages:
            - nginx
            - certbot
      - name: meta-data
        content: |
          instance-id: web-server-01
          local-hostname: web-server-01

  # Advanced Options (passed as-is to the VM advanced options field)
  # Each line becomes one entry. See: docs.verge.io/knowledge-base/vm-advanced-options/
  advanced_options: |
    nic1.txqueuelen=5000
    nic1.numtxqueues=4
    nic1.numrxqueues=4

  # ---------- Hardware ----------

  drives:
    - name: "OS Disk"
      description: "Operating System Disk"
      media: disk                # disk | cdrom | import | clone | efidisk
      interface: virtio-scsi     # virtio-scsi | virtio | ide | ahci | lsi53c895a
      size: 50GB                 # CLI converts to bytes for the API
      preferred_tier: 3          # Storage tier 1-5
      # order: 0                 # Optional explicit ordering

    - name: "Data Disk"
      media: disk
      interface: virtio-scsi
      size: 200GB
      preferred_tier: 4

    - name: "Ubuntu ISO"
      media: cdrom
      interface: ahci
      media_source: 7            # Media file ID from the vSAN
                                 # (CLI could also accept name: "ubuntu-24.04-server.iso")

    - name: "Cloned from template"
      media: import              # or 'clone'
      interface: virtio-scsi
      media_source: 123          # Source drive/image ID
      preferred_tier: 3

  nics:
    - name: "Primary Network"
      description: "LAN connection"
      interface: virtio          # virtio | e1000 | rtl8139 | pcnet
      enabled: true
      network: 3                 # Network ID (vnet key)
                                 # CLI could also resolve names: "DMZ Internal"
      # mac: "52:54:00:xx:xx:xx" # Optional — auto-generated if omitted

    - name: "Management"
      interface: virtio
      network: 5

  devices:
    - name: "GPU Passthrough"
      resource_group: "1f67f07e-f653-db95-c475-01b8a2ea0ff1"  # UUID from resource_groups API
      settings: {}               # Device-specific settings
```

---

## Full Example — Windows Server

```yaml
apiVersion: v4
kind: VirtualMachine

vm:
  name: dc-01
  description: "Active Directory Domain Controller"
  enabled: true
  os_family: windows
  os_description: "Windows Server 2025 Standard"

  cpu_cores: 4
  ram: 16GB
  machine_type: q35
  boot_order: cd
  uefi: true
  secure_boot: true
  console: vnc
  video: std
  guest_agent: true
  rtc_base: localtime
  cluster: 1
  ha_group: "domain-controllers"
  power_on_after_create: false

  advanced_options: |
    smbios.type1.manufacturer=Dell Inc.
    smbios.type1.product=PowerEdge R740

  drives:
    - name: "OS Disk"
      media: disk
      interface: virtio-scsi
      size: 100GB
      preferred_tier: 2

    - name: "Windows ISO"
      media: cdrom
      interface: ahci
      media_source: windows-2025-eval   # CLI resolves ISO name → ID

    - name: "VirtIO Drivers"
      media: cdrom
      interface: ahci
      media_source: virtio-win          # CLI resolves ISO name → ID

  nics:
    - name: "Corporate LAN"
      interface: virtio
      network: internal-lan             # CLI resolves network name → ID
```

---

## Multi-VM Example (Batch Provisioning)

```yaml
apiVersion: v4
kind: VirtualMachineSet

# Shared defaults — applied to every VM unless overridden
defaults:
  os_family: linux
  cpu_cores: 2
  ram: 4GB
  machine_type: q35
  guest_agent: true
  uefi: true
  console: vnc
  video: virtio
  drives:
    - name: "OS Disk"
      media: disk
      interface: virtio-scsi
      size: 30GB
      preferred_tier: 3
  nics:
    - name: "Primary"
      interface: virtio
      network: internal-lan

vms:
  - name: app-server-01
    description: "Application server"
    ram: 8GB                     # Overrides default
    cpu_cores: 4                 # Overrides default
    ha_group: "app-servers"
    drives:                      # Overrides default drives entirely
      - name: "OS Disk"
        media: disk
        interface: virtio-scsi
        size: 50GB
        preferred_tier: 2

  - name: app-server-02
    description: "Application server (replica)"
    ram: 8GB
    cpu_cores: 4
    ha_group: "app-servers"

  - name: monitoring-01
    description: "Prometheus + Grafana"
    # Inherits all defaults (2 cores, 4GB, 30GB disk)
```

---

## Schema Reference

### Top-Level Fields

| Field        | Required | Values                                  | Description                        |
|--------------|----------|-----------------------------------------|------------------------------------|
| `apiVersion` | Yes      | `v1`                                    | Schema version for forward compat  |
| `kind`       | Yes      | `VirtualMachine` \| `VirtualMachineSet` | Single VM or batch                 |

### `vm` Fields

| Field                  | Required | Default          | API Field               | Notes                                          |
|------------------------|----------|------------------|-------------------------|-------------------------------------------------|
| `name`                 | **Yes**  | —                | `name`                  | Must be unique                                  |
| `description`          | No       | `""`             | `description`           |                                                 |
| `enabled`              | No       | `true`           | `enabled`               |                                                 |
| `os_family`            | **Yes**  | —                | `os_family`             | `linux` \| `windows` \| `freebsd` \| `other`   |
| `os_description`       | No       | `""`             | `os_description`        | Freeform text                                   |
| `cpu_cores`            | No       | `1`              | `cpu_cores`             |                                                 |
| `cpu_type`             | No       | `auto`           | `cpu_type`              | `auto` lets VergeOS pick optimal for host       |
| `ram`                  | No       | `1GB`            | `ram`                   | CLI parses `512MB`/`4GB` → integer MB           |
| `machine_type`         | No       | `q35`            | `machine_type`          | `q35` \| `pc`                                   |
| `boot_order`           | No       | `cd`             | `boot_order`            | `d` `cd` `cdn` `c` `dc` `n` `nd` `do`          |
| `allow_hotplug`        | No       | `true`           | `allow_hotplug`         |                                                 |
| `uefi`                 | No       | `false`          | `uefi`                  |                                                 |
| `secure_boot`          | No       | `false`          | `secure_boot`           | Requires `uefi: true`                           |
| `console`              | No       | `vnc`            | `console`               | `vnc` \| `spice`                                |
| `video`                | No       | `std`            | `video`                 | `std` `cirrus` `vmware` `qxl` `virtio` `none`  |
| `guest_agent`          | No       | `false`          | `guest_agent`           |                                                 |
| `rtc_base`             | No       | `utc`            | `rtc_base`              | `utc` \| `localtime`                            |
| `cluster`              | No       | `~`              | `cluster`               | ID or name                                      |
| `failover_cluster`     | No       | `~`              | `failover_cluster`      | ID or name                                      |
| `preferred_node`       | No       | `~`              | `preferred_node`        | ID or name                                      |
| `ha_group`             | No       | `~`              | `ha_group`              | `+group` = affinity, `group` = anti-affinity    |
| `snapshot_profile`     | No       | `~`              | `snapshot_profile`      | Name or ID                                      |
| `power_on_after_create`| No       | `false`          | `powerstate`            |                                                 |
| `advanced_options`     | No       | `~`              | (advanced options field) | Multi-line string, one option per line          |

### `cloudinit` Fields

| Field        | Required | Default | API Field               | Notes                                  |
|--------------|----------|---------|-------------------------|----------------------------------------|
| `datasource` | No       | `~`     | `cloudinit_datasource`  | `nocloud` \| `config_drive_v2` \| `~`  |
| `files`      | No       | `[]`    | `cloudinit_files`       | List of `{name, content}` objects      |

### `drives[]` Fields

| Field            | Required         | Default        | API Field        | Notes                                              |
|------------------|------------------|----------------|------------------|----------------------------------------------------|
| `name`           | No               | auto-generated | `name`           |                                                    |
| `description`    | No               | `""`           | `description`    |                                                    |
| `media`          | No               | `disk`         | `media`          | `disk` `cdrom` `import` `clone` `efidisk`          |
| `interface`      | No               | `virtio-scsi`  | `interface`      | `virtio-scsi` `virtio` `ide` `ahci` `lsi53c895a`  |
| `size`           | When media=disk  | —              | `disksize`       | CLI converts `50GB` → bytes                        |
| `preferred_tier` | No               | `3`            | `preferred_tier` | `1`-`5`                                            |
| `media_source`   | When media≠disk  | —              | `media_source`   | ID or filename (CLI resolves)                      |
| `enabled`        | No               | `true`         | `enabled`        |                                                    |
| `order`          | No               | list index     | `orderid`        |                                                    |
| `asset`          | No               | `~`            | `asset`          | Freeform asset tag for recipe use                  |

### `nics[]` Fields

| Field         | Required | Default   | API Field   | Notes                               |
|---------------|----------|-----------|-------------|--------------------------------------|
| `name`        | No       | auto-gen  | `name`      |                                      |
| `description` | No       | `""`      | `description`|                                     |
| `interface`   | No       | `virtio`  | `interface` | `virtio` `e1000` `rtl8139` `pcnet`  |
| `enabled`     | No       | `true`    | `enabled`   |                                      |
| `network`     | **Yes**  | —         | `vnet`      | Network ID or name (CLI resolves)    |
| `mac`         | No       | auto-gen  | `mac`       | Optional specific MAC address        |
| `asset`       | No       | `~`       | `asset`     | Freeform asset tag for recipe use    |

### `devices[]` Fields

| Field            | Required | Default | API Field        | Notes                            |
|------------------|----------|---------|------------------|-----------------------------------|
| `name`           | No       | `""`    | —                | For human reference only          |
| `resource_group` | **Yes**  | —       | `resource_group` | UUID from `/api/v4/resource_groups` |
| `settings`       | No       | `{}`    | `settings_args`  | Device-specific key-value pairs   |

---

## Unit Parsing Rules (for CLI implementation)

The CLI should parse human-friendly units and convert to API values:

| Input       | Parsed As          | API Value              |
|-------------|--------------------|-----------------------|
| `512MB`     | 512 megabytes      | `ram: 512` (MB int)   |
| `4GB`       | 4 gigabytes        | `ram: 4096` (MB int)  |
| `50GB` (disk) | 50 gigabytes     | `disksize: 53687091200` (bytes) |
| `1TB` (disk)  | 1 terabyte       | `disksize: 1099511627776` (bytes) |

Regex: `/^(\d+(?:\.\d+)?)\s*(MB|GB|TB)$/i`

---

## CLI Workflow (How the template gets applied)

```
vrg vm create -f web-server.vrg.yaml
```

Under the hood:

```
1. Parse & validate YAML against schema
2. Resolve names → IDs (cluster, network, media_source, etc.)
3. POST /api/v4/vms              → get vm_key + machine_key
4. For each drive:
     POST /api/v4/machine_drives   (using machine_key)
5. For each NIC:
     POST /api/v4/machine_nics     (using machine_key)
6. For each device:
     POST /api/v4/machine_devices  (using machine_key)
7. If power_on_after_create:
     POST /api/v4/vm_actions       { vm: vm_key, action: "poweron" }
8. Print summary
```

---

## CLI Commands

```bash
# Create VM from template
vrg vm create -f my-vm.vrg.yaml

# Validate template without creating anything
vrg vm validate -f my-vm.vrg.yaml

# Generate a template from an existing VM (reverse-engineer)
vrg vm export --id 42 -o exported-vm.vrg.yaml

# Dry-run: show what API calls would be made
vrg vm create -f my-vm.vrg.yaml --dry-run

# Create from template with overrides
vrg vm create -f my-vm.vrg.yaml --set vm.name=web-server-03 --set vm.ram=16GB

# Create batch from VirtualMachineSet template
vrg vm create -f fleet.vrg.yaml
```

---

## Variable Substitution (Optional Enhancement)

For more advanced use, support `${VAR}` substitution from environment or a vars file:

```yaml
apiVersion: v4
kind: VirtualMachine

vars:
  env: production
  team: platform

vm:
  name: "${env}-web-${team}-01"
  description: "Web server for ${team} (${env})"
  ram: ${VM_RAM:-4GB}            # Env var with default
  cluster: ${CLUSTER_ID}

  nics:
    - name: "Primary"
      network: ${NETWORK_ID}
```

```bash
CLUSTER_ID=1 NETWORK_ID=3 VM_RAM=8GB vrg vm create -f my-vm.vrg.yaml
```

---

## JSON Schema (for validation / editor autocompletion)

The CLI should ship a JSON Schema file that editors like VS Code can use for
autocompletion and inline validation. Register it via:

```json
// .vscode/settings.json
{
  "yaml.schemas": {
    "./vergeos-vm-schema.json": "*.vrg.yaml"
  }
}
```

---

## Notes on Name Resolution

Several fields accept either an **ID** (integer) or a **name** (string). The CLI should:

1. If the value is an integer, use it directly as the API ID.
2. If the value is a string, query the appropriate API endpoint to resolve it:
   - `cluster` → `GET /api/v4/clusters?filter=name eq '...'`
   - `network` → `GET /api/v4/networks?filter=name eq '...'`
   - `media_source` (string) → `GET /api/v4/media_files?filter=name contains '...'`
3. If resolution fails or is ambiguous, error with suggestions.

This makes templates portable between environments where IDs differ but names are consistent.