# VM Sub-Resources & Template System Design

> Phase 2 feature: NICs, Drives, Devices (TPM) as sub-resource commands + declarative YAML template system for VM provisioning.

**Date:** 2026-02-05
**Status:** Design approved
**Scope:** Full spec — sub-resource CRUD, template create/validate/export, dry-run, --set overrides, batch VirtualMachineSet, variable substitution, JSON schema

---

## Overview

Phase 1 delivered VM lifecycle commands (CRUD + power ops). A VM is an empty shell without storage, networking, and devices. This phase adds:

1. **Sub-resource CRUD** — `vrg vm drive`, `vrg vm nic`, `vrg vm device` commands
2. **Template system** — declarative YAML format (`.vrg.yaml`) for provisioning complete VMs with all sub-resources in a single command
3. **Export** — reverse-engineer running VMs into portable templates ("ClickOps to GitOps")

Node (physical host) commands are deferred to a future phase.

---

## Design Principles

- **SDK-first** — every layer talks to pyvergeos objects, never raw API calls. Leverage SDK pagination, filtering, and typed resource objects.
- **YAML over JSON** — human-readable, supports comments, widely tooled.
- **Human-friendly units** — `4GB` instead of `4294967296` bytes. The CLI translates.
- **Sensible defaults** — only `name` and `os_family` are truly required.
- **1:1 API mapping** — every template field maps directly to a pyvergeos method argument.
- **Composable** — drives, NICs, devices, and cloud-init are inline sections; the CLI orchestrates multi-step SDK calls.

---

## Part 1: Sub-Resource Commands

Three new command groups nested under `vrg vm`:

```
vrg vm drive  <command> <vm> [options]
vrg vm nic    <command> <vm> [options]
vrg vm device <command> <vm> [options]
```

### `vrg vm drive` Commands

| Command | Description |
|---------|-------------|
| `list <vm>` | List drives attached to a VM |
| `get <vm> <drive>` | Get details of a specific drive (by ID or name) |
| `create <vm>` | Add a drive (`--size 50GB --interface virtio-scsi --media disk --tier 3 --name "OS Disk"`) |
| `update <vm> <drive>` | Update drive properties (`--name`, `--size`, `--tier`, `--enabled`) |
| `delete <vm> <drive>` | Remove a drive (with confirmation prompt) |
| `import <vm>` | Import a drive from file (`--file-name disk.vmdk --interface virtio-scsi`) |

### `vrg vm nic` Commands

| Command | Description |
|---------|-------------|
| `list <vm>` | List NICs on a VM |
| `get <vm> <nic>` | Get NIC details |
| `create <vm>` | Add a NIC (`--network External --interface virtio --name "eth0"`) |
| `update <vm> <nic>` | Update NIC (`--name`, `--enabled`, `--network`) |
| `delete <vm> <nic>` | Remove a NIC |

### `vrg vm device` Commands (TPM Only)

| Command | Description |
|---------|-------------|
| `list <vm>` | List devices on a VM |
| `get <vm> <device>` | Get device details |
| `create <vm>` | Add TPM (`--model crb --version 2.0`) |
| `delete <vm> <device>` | Remove a device |

TPM payload: `{"machine": "<machine_key>", "type": "tpm", "settings_args": {"model": "crb", "version": "2"}}`

Model options: `tis`, `crb`. Version options: `1.2`, `2.0`. No resource groups needed.

### Command Patterns

- `<vm>` is always the first positional arg — resolved via `resolve_resource_id` (name or ID)
- `<drive>`, `<nic>`, `<device>` are the second positional arg for get/update/delete
- VM fetched first to get `machine_key`, then sub-resources accessed via `vm.drives`, `vm.nics`, `vm.devices`
- Commands are thin wrappers: `vrg vm drive create <vm>` → `client.vms.get(id).drives.create(...)`
- Unit parsing for `--size`: accepts `50GB`, `1TB`, `512MB` — converted appropriately

---

## Part 2: Template System

### File Format

Extension: `.vrg.yaml` (also accepts `.yaml` / `.yml`).

Spec document: `docs/VergeOS-vm-tempalte-spec.md`
JSON Schema: `.claude/reference/specs/vm-schema.json` (starting point — needs refinements)
Example templates: `.claude/reference/*.vrg.yml`

### CLI Commands

```bash
# Create VM from template
vrg vm create -f web-server.vrg.yaml

# Create with field overrides
vrg vm create -f web-server.vrg.yaml --set vm.name=web-03 --set vm.ram=16GB

# Dry-run: show planned actions without creating anything
vrg vm create -f web-server.vrg.yaml --dry-run

# Batch create from VirtualMachineSet template
vrg vm create -f fleet.vrg.yaml

# Validate template syntax and references
vrg vm validate -f template.vrg.yaml

# Export existing VM to template
vrg vm export my-web-server -o exported.vrg.yaml
vrg vm export my-web-server              # stdout
vrg vm export 42 -o exported.vrg.yaml    # by ID
```

The `-f` flag switches `vrg vm create` to template mode. Mutually exclusive with inline flags (`--name`, `--ram`, etc.). Overrides go through `--set`.

### Variable Substitution

**Two-pass processing:**

```
Pass 1: Quick-parse YAML to extract `vars:` block only
Pass 2: Merge vars with environment variables (env takes precedence)
Pass 3: String substitution on raw YAML text using combined variables
Pass 4: Full YAML parse
```

**Syntax:**

| Pattern | Meaning |
|---------|---------|
| `${VAR}` | Required — error if unset |
| `${VAR:-default}` | Use `default` if VAR is unset |

**Example:**
```yaml
vars:
  env: production
  team: platform

vm:
  name: "${env}-web-${team}-01"
  ram: ${VM_RAM:-4GB}
  cluster: ${CLUSTER_ID}
```

```bash
CLUSTER_ID=1 vrg vm create -f template.vrg.yaml
```

### `--set` Overrides

Applied after variable substitution and YAML parsing, before validation.

**Syntax:** dot-path notation into the parsed structure.

```bash
vrg vm create -f template.vrg.yaml --set vm.name=web-03 --set vm.ram=16GB
```

**Rules:**
- Upsert behavior — creates the key if it doesn't exist, updates if it does
- Final structure must still pass schema validation (invalid keys caught)
- List items cannot be targeted individually — no `--set vm.drives[0].size=100GB`
- Values are strings — same unit parser / type coercion applies
- For `VirtualMachineSet`, `--set` applies to all VMs (overrides defaults)

### Processing Pipeline

```
Raw YAML text
  → Extract vars: block (pass 1)
  → Merge with env vars (env wins)
  → String substitution (pass 2)
  → Full YAML parse (pass 3)
  → --set overrides (dot-path upsert)
  → Schema validation
  → Unit conversion (4GB → 4096 MB, 50GB → bytes)
  → Name resolution via SDK (networks, clusters, media files)
  → API calls via pyvergeos (or dry-run output)
```

### Creation Orchestration

For each VM definition:

```
1. Translate YAML keys to pyvergeos method kwargs
2. client.vms.create(**args) → get vm object (has machine_key)
3. For each drive: vm.drives.create(**drive_args)
4. For each NIC: vm.nics.create(**nic_args)
5. For each device: vm.devices.create_tpm(**device_args)
6. Set cloud-init files if specified
7. Power on if power_on_after_create: true
8. Print summary
```

**VirtualMachineSet handling:** Merge `defaults` into each `vms[]` entry (entry values override defaults), then process each VM through the same pipeline.

**Error handling:** If drive/NIC creation fails mid-way, the VM still exists (partially provisioned). Print what succeeded and what failed. Exit with error code but leave the VM for the user to fix or delete. No silent rollback.

### Dry-Run Output

```
Dry run — no resources will be created.

VM: web-server-01 (linux, 4 cores, 8GB RAM, q35)
  Drive 1: "OS Disk" — disk, virtio-scsi, 50GB, tier 3
  Drive 2: "Ubuntu ISO" — cdrom, ahci, media: ubuntu-24.04-server.iso
  NIC 1: "External Network" — virtio, network: DMZ Internal (key: 3)
  Cloud-init: nocloud (2 files: user-data, meta-data)
  Power on after create: no

5 API calls would be made.
```

---

## Part 3: Export

### Purpose

Reverse-engineer a running VM into a portable `.vrg.yaml` template. Enables "ClickOps to GitOps" migration.

### Behavior

1. Fetch VM by name/ID via `client.vms.get()`
2. Iterate `vm.drives`, `vm.nics`, `vm.devices` as pyvergeos resource objects
3. Map SDK object attributes back to template field names
4. Convert units to human-friendly: `ram: 4096` → `ram: 4GB`, drive bytes → `50GB`
5. Emit clean YAML with `apiVersion: v4`, `kind: VirtualMachine`

### What it omits

- `machine_key`, internal IDs, timestamps — implementation details
- Cloud-init file contents (not retrievable after creation — emit comment noting this)
- Auto-generated MACs (omit `mac:` so re-creation gets fresh ones)

### What it preserves by reference

- Network names (resolved back from keys via SDK)
- Media source names for CD-ROMs (resolved back from file keys where possible)
- Cluster/node names

### Image detection

If the boot drive matches a known Library Image (by parent/hash), emit `image: <name>` rather than a raw drive configuration. Only list extra data drives explicitly.

### Hydration header

Exported files are static snapshots with variables resolved:

```yaml
# Exported from VM: my-web-server (key: 42)
# Date: 2026-02-05
# Note: This is a static snapshot. Variables have been resolved.
apiVersion: v4
kind: VirtualMachine
...
```

### Name resolution fallback

If a network/cluster name can't be resolved (permissions, deleted resource), fall back to the numeric ID with a warning comment:

```yaml
network: 7  # Warning: could not resolve name for network key 7
```

---

## Part 4: JSON Schema

### Location

`schemas/vrg-vm-template.schema.json` — shipped with the package.

### The Type Trap: Loose Input, Strict Output

Fields like `ram` and `drive.size` accept human-friendly strings (`4GB`) in templates. The schema must be permissive for editor validation:

- `ram`: `oneOf: [integer, string matching ^\\d+(\\.\\d+)?\\s*(MB|GB|TB)$]`
- `drive.size`: same pattern
- `cluster`, `network`, `media_source`: `oneOf: [integer, string]`

This gives VS Code real-time validation (catches `4GGB`) while allowing flexible input.

### Schema Refinements Needed

Starting from `.claude/reference/specs/vm-schema.json`:

1. **`deviceSpec`** — update for TPM-only scope: require `type: tpm`, add `model` (enum: tis/crb) and `version` (enum: "1.2"/"2.0"), remove `resource_group` requirement
2. **`ram`** — change from string-only to `oneOf: [integer, string-with-pattern]`
3. **`os_family`** — add to `vmSpec.required` array alongside `name`
4. **`name` pattern** — allow `${VAR}` syntax for variable substitution: update regex

### Editor Integration

```json
// .vscode/settings.json
{
  "yaml.schemas": {
    "./schemas/vrg-vm-template.schema.json": "*.vrg.yaml"
  }
}
```

The `vrg vm validate` command uses this same schema programmatically.

---

## File Organization

### New Source Files

```
src/verge_cli/
├── commands/
│   ├── vm.py              # Modified — add -f, --set, --dry-run to create; add validate, export
│   ├── vm_drive.py        # NEW — vrg vm drive list/get/create/update/delete/import
│   ├── vm_nic.py          # NEW — vrg vm nic list/get/create/update/delete
│   └── vm_device.py       # NEW — vrg vm device list/get/create/delete (TPM only)
├── template/
│   ├── __init__.py
│   ├── loader.py          # YAML loading, two-pass variable substitution, --set application
│   ├── schema.py          # Schema validation (wraps JSON schema), unit parsing
│   ├── resolver.py        # Name → ID resolution via pyvergeos SDK (networks, clusters, media)
│   ├── builder.py         # Orchestrator: validated dict → pyvergeos method calls
│   ├── exporter.py        # Reverse: pyvergeos objects → template YAML (image detection, hydration)
│   └── units.py           # Unit parser: "4GB" → 4096 (MB), "50GB" → bytes
├── schemas/
│   └── vrg-vm-template.schema.json
```

### New Test Files

```
tests/unit/
├── test_vm_drive.py
├── test_vm_nic.py
├── test_vm_device.py
├── test_template_loader.py
├── test_template_schema.py
├── test_template_resolver.py
├── test_template_builder.py
├── test_template_exporter.py
└── test_template_units.py
```

### Registration

```python
# In cli.py
from verge_cli.commands import vm_drive, vm_nic, vm_device

vm.app.add_typer(vm_drive.app, name="drive")
vm.app.add_typer(vm_nic.app, name="nic")
vm.app.add_typer(vm_device.app, name="device")
```

### Shared Utilities

- `units.py` — used by template `schema.py` AND CLI `--size` option callbacks on `vm_drive.py`
- `resolver.py` — used by template `builder.py` AND `vm_nic.py` (`--network` name resolution)
- Existing `utils.resolve_resource_id()` — handles VM name→key; `resolver.py` handles template-specific batch resolution

---

## Implementation Order

### Milestone 1: Foundation — `units.py` + `resolver.py`

**Why first:** Everything else depends on these.

- `template/units.py` — parse `4GB` → 4096 MB, `50GB` → bytes, with validation and error messages
- `template/resolver.py` — batch name→ID resolution using pyvergeos SDK list/search methods (`client.networks.list()`, etc.). Leverages SDK pagination and filtering.
- Full unit tests for both modules

### Milestone 2: Sub-Resource CRUD Commands

**Why second:** Useful standalone and exercises SDK sub-resource APIs. Can be worked in parallel with M3 after M1 is done.

- `commands/vm_drive.py` — thin wrapper: `vm.drives.create(...)`, uses `units.py` for `--size`
- `commands/vm_nic.py` — thin wrapper: `vm.nics.create(...)`, uses `resolver.py` for `--network`
- `commands/vm_device.py` — thin wrapper: TPM only (`--model`, `--version`)
- Register all three on `vm.app` in `cli.py`
- Unit tests for each command module

### Milestone 3: Template Loading & Validation

**Why third:** Template parsing is the core; everything else builds on it. Can be worked in parallel with M2 after M1 is done.

- `template/loader.py` — two-pass variable substitution, `--set` override application, YAML loading
- `template/schema.py` — JSON schema validation, integrate with `units.py` for post-parse conversion
- Finalize `schemas/vrg-vm-template.schema.json` (fix deviceSpec for TPM, `oneOf` for ram, os_family required)
- `vrg vm validate -f` command
- Unit tests for loader, schema, variable substitution, `--set` mechanics

### Milestone 4: Template Create & Dry-Run

**Why fourth:** Orchestration ties loader + resolver + SDK calls together. Depends on M1 + M3.

- `template/builder.py` — translation layer: validated dict → pyvergeos method kwargs → SDK calls
- `--dry-run` mode — same pipeline but prints plan instead of calling APIs
- `-f` flag on `vrg vm create` — template mode branch
- `VirtualMachineSet` support — merge defaults, iterate VMs
- Error handling — partial provisioning reporting
- Unit tests (mocked SDK)

### Milestone 5: Export + JSON Schema Packaging

**Why last:** Export is read-only and depends on understanding the full template structure. Depends on M3.

- `template/exporter.py` — iterate pyvergeos resource objects → template YAML (unit conversion back, name resolution fallback, image detection, hydration header)
- `vrg vm export` command
- Package `schemas/vrg-vm-template.schema.json` into distribution
- Unit tests for export (round-trip: create from template → export → compare structure)

### Dependency Graph

```
M1 (units + resolver)
├── M2 (CRUD commands)     ← can parallel with M3
├── M3 (loader + validation) ← can parallel with M2
│   └── M4 (builder + create -f)
│   └── M5 (export + schema packaging)
```

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/VergeOS-vm-tempalte-spec.md` | Full template YAML specification |
| `.claude/reference/specs/vm-schema.json` | Draft JSON schema (needs refinements) |
| `.claude/reference/web-server.vrg.yml` | Example: Linux web server template |
| `.claude/reference/windows-server.vrg.yml` | Example: Windows Server template |
| `.claude/reference/k8s-cluster.vrg.yml` | Example: VirtualMachineSet batch template |
