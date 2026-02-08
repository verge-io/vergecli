# Phase 2: Infrastructure & Tenants — Design Document

**Date:** 2026-02-07
**Status:** Approved
**Scope:** Clusters, Nodes, Storage Tiers, Tenants (full lifecycle + sub-resources), Tab Completion

---

## Overview

Phase 2 adds 4 new top-level command groups and 5 tenant sub-resource groups to the CLI, covering infrastructure management (clusters, nodes, storage tiers) and full tenant lifecycle management including compute/storage allocation, networking, snapshots, and monitoring.

### Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tenant sub-resource depth | Full coverage | SDK support is solid; MSPs need complete tenant provisioning |
| Cluster create/update params | Essential only | `name`, `description`, `enabled`, `compute` — keeps `--help` clean |
| Node sub-resources (PCI/GPU/USB) | Deferred | Core + maintenance only; hardware discovery in a later phase |
| Node maintenance UX | Single command with `--enable`/`--disable` | Cleaner than two separate commands |
| Tenant isolation UX | Single command with `--enable`/`--disable` | Consistent with node maintenance pattern |
| Tenant sub-command hierarchy | Nested under `vrg tenant` | Matches existing `vrg vm drive/nic/device` pattern |
| Tab completion | Static only (Typer built-in) | Dynamic resource name completion deferred |
| Docker image | Deferred | Focus Phase 2 on commands + completion |

---

## Command Inventory

### `vrg cluster` — Cluster Management

**File:** `src/verge_cli/commands/cluster.py`
**SDK:** `client.clusters` → `ClusterManager`

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `name` | Name | |
| `status` | Status | style_map: online→green, degraded→yellow, error→red, offline→red |
| `total_nodes` | Nodes | |
| `online_nodes` | Online | |
| `total_ram_gb` | RAM GB | |
| `ram_used_percent` | RAM % | style_fn: >80→red, >60→yellow |
| `total_cores` | Cores | |
| `running_machines` | Running VMs | wide_only |
| `is_compute` | Compute | wide_only, format Yes/No |
| `is_storage` | Storage | wide_only, format Yes/No |

**Commands:**

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg cluster list` | `client.clusters.list()` | |
| `vrg cluster get <ID\|NAME>` | `client.clusters.get(key)` | Full detail: compute flags, default CPU, RAM/core per unit, max RAM/cores per VM |
| `vrg cluster create --name NAME [--description] [--enabled] [--compute]` | `client.clusters.create(...)` | Essential params only |
| `vrg cluster update <ID\|NAME> [--name] [--description] [--enabled] [--compute]` | `client.clusters.update(key, ...)` | Essential params only |
| `vrg cluster delete <ID\|NAME> [--yes]` | `client.clusters.delete(key)` | Confirm destructive |
| `vrg cluster vsan-status [--name NAME] [--include-tiers]` | `client.clusters.vsan_status(...)` | Cluster-wide vSAN health |

---

### `vrg node` — Node Management

**File:** `src/verge_cli/commands/node.py`
**SDK:** `client.nodes` → `NodeManager`

Nodes are physical/virtual servers in the infrastructure. No create/update/delete — managed at infrastructure level.

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `name` | Name | |
| `status` | Status | style_map: online→green, maintenance→yellow, offline→red, error→bold red |
| `cluster_name` | Cluster | |
| `ram_gb` | RAM GB | |
| `cores` | Cores | |
| `cpu_usage` | CPU % | style_fn: >80→red, >60→yellow |
| `is_physical` | Physical | wide_only, format Yes/No |
| `model` | Model | wide_only |
| `cpu` | CPU | wide_only |
| `core_temp` | Temp °C | wide_only, style_fn: >80→red, >60→yellow |
| `vergeos_version` | Version | wide_only |

**Commands:**

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg node list [--cluster NAME]` | `client.nodes.list(cluster=...)` | Optional cluster filter |
| `vrg node get <ID\|NAME>` | `client.nodes.get(key)` | Full detail: CPU speed, IPMI, IOMMU, vSAN, kernel/QEMU versions |
| `vrg node maintenance <ID\|NAME> --enable` | `client.nodes.enable_maintenance(key)` | Migrates VMs off node |
| `vrg node maintenance <ID\|NAME> --disable` | `client.nodes.disable_maintenance(key)` | |
| `vrg node restart <ID\|NAME> [--yes]` | `client.nodes.restart(key)` | Maintenance reboot, confirm destructive |

---

### `vrg storage` — Storage Tier Management

**File:** `src/verge_cli/commands/storage.py`
**SDK:** `client.storage_tiers` → `StorageTierManager`

Read-only — tiers are defined by physical disk configuration.

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `tier` | Tier # | |
| `description` | Description | |
| `capacity_gb` | Capacity GB | |
| `used_gb` | Used GB | |
| `free_gb` | Free GB | |
| `used_percent` | Used % | style_fn: >80→red, >60→yellow |
| `dedupe_ratio` | Dedupe | wide_only |
| `dedupe_savings_percent` | Savings % | wide_only |
| `read_ops` | Read IOPS | wide_only |
| `write_ops` | Write IOPS | wide_only |

**Commands:**

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg storage list` | `client.storage_tiers.list()` | All tiers with capacity/usage |
| `vrg storage get <TIER#\|KEY>` | `client.storage_tiers.get(key)` | Full detail including I/O stats |
| `vrg storage summary` | `client.storage_tiers.get_summary()` | Aggregate totals across all tiers |

---

### `vrg tenant` — Tenant Management

**File:** `src/verge_cli/commands/tenant.py`
**SDK:** `client.tenants` → `TenantManager`

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `name` | Name | |
| `status` | Status | style_map: online→green, running→green, offline→red, stopped→red, error→bold red, starting→yellow, stopping→yellow, migrating→yellow |
| `state` | State | |
| `is_isolated` | Isolated | format Yes/No |
| `description` | Description | wide_only |
| `network_name` | Network | wide_only |
| `ui_address_ip` | UI IP | wide_only |
| `uuid` | UUID | wide_only |

**Core CRUD:**

| Command | SDK Call |
|---------|---------|
| `vrg tenant list` | `client.tenants.list()` |
| `vrg tenant get <ID\|NAME>` | `client.tenants.get(key)` |
| `vrg tenant create --name NAME [--description] [--password] [--url] [--note] [--expose-cloud-snapshots] [--allow-branding]` | `client.tenants.create(...)` |
| `vrg tenant update <ID\|NAME> [--name] [--description] [--url] [--note] [--expose-cloud-snapshots] [--allow-branding]` | `client.tenants.update(key, ...)` |
| `vrg tenant delete <ID\|NAME> [--yes]` | `client.tenants.delete(key)` |

**Power Operations:**

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg tenant start <ID\|NAME> [--wait] [--timeout]` | `client.tenants.power_on(key)` | |
| `vrg tenant stop <ID\|NAME> [--wait] [--timeout]` | `client.tenants.power_off(key)` | |
| `vrg tenant restart <ID\|NAME> [--wait] [--timeout]` | `client.tenants.restart(key)` | |
| `vrg tenant reset <ID\|NAME> [--yes]` | `client.tenants.reset(key)` | Hard reboot, confirm |

**Tenant-Specific Actions:**

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg tenant clone <ID\|NAME> [--name] [--no-network] [--no-storage] [--no-nodes]` | `client.tenants.clone(key, ...)` | |
| `vrg tenant isolate <ID\|NAME> --enable / --disable` | `enable_isolation(key)` / `disable_isolation(key)` | Mutually exclusive flags |
| `vrg tenant crash-cart create <ID\|NAME> [--name]` | `client.tenants.create_crash_cart(key, ...)` | Sub-Typer group |
| `vrg tenant crash-cart delete <ID\|NAME> [--name] [--yes]` | `client.tenants.delete_crash_cart(key, ...)` | |
| `vrg tenant send-file <TENANT> <FILE>` | `client.tenants.send_file(key, file_key)` | Resolve both args |

---

### Tenant Sub-Resources

All sub-resources follow the `vrg vm drive/nic/device` pattern: the parent tenant is always the first positional argument.

#### `vrg tenant node` — Compute Allocation

**File:** `src/verge_cli/commands/tenant_node.py`
**SDK:** `tenant_obj.nodes` → `TenantNodeManager`

Tenant nodes are compute resource allocations (CPU/RAM from a cluster), NOT physical infrastructure nodes.

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `name` | Name | |
| `cpu_cores` | CPU | |
| `ram_gb` | RAM GB | |
| `status` | Status | style_map: running→green, stopped→red |
| `is_enabled` | Enabled | format Yes/No |
| `cluster_name` | Cluster | wide_only |
| `host_node` | Host Node | wide_only |

**Commands:**

| Command | SDK Call |
|---------|---------|
| `vrg tenant node list <TENANT>` | `tenant_obj.nodes.list()` |
| `vrg tenant node get <TENANT> <NODE>` | `tenant_obj.nodes.get(key)` |
| `vrg tenant node create <TENANT> --cpu-cores N --ram-gb N [--cluster KEY] [--name] [--preferred-node KEY]` | `tenant_obj.nodes.create(...)` |
| `vrg tenant node update <TENANT> <NODE> [--cpu-cores] [--ram-gb] [--name] [--enabled/--disabled]` | `tenant_obj.nodes.update(...)` |
| `vrg tenant node delete <TENANT> <NODE> [--yes]` | `tenant_obj.nodes.delete(key)` |

#### `vrg tenant storage` — Storage Allocation

**File:** `src/verge_cli/commands/tenant_storage.py`
**SDK:** `tenant_obj.storage` → `TenantStorageManager`

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `tier_name` | Tier | |
| `provisioned_gb` | Provisioned GB | |
| `used_gb` | Used GB | wide_only |
| `used_percent` | Used % | wide_only, style_fn: >80→red, >60→yellow |

**Commands:**

| Command | SDK Call |
|---------|---------|
| `vrg tenant storage list <TENANT>` | `tenant_obj.storage.list()` |
| `vrg tenant storage get <TENANT> <STORAGE>` | `tenant_obj.storage.get(key)` |
| `vrg tenant storage create <TENANT> --tier N --provisioned-gb N` | `tenant_obj.storage.create(...)` |
| `vrg tenant storage update <TENANT> <STORAGE> [--provisioned-gb]` | `tenant_obj.storage.update(...)` |
| `vrg tenant storage delete <TENANT> <STORAGE> [--yes]` | `tenant_obj.storage.delete(key)` |

#### `vrg tenant net-block` / `ext-ip` / `l2` — Networking

**File:** `src/verge_cli/commands/tenant_net.py` (three sub-Typer apps in one file)

**Network Blocks** (`vrg tenant net-block`):
- Columns: `$key` (Key), `cidr`, `network_name` (Network), `description` (wide_only)
- Commands: `list <TENANT>`, `create <TENANT> --cidr CIDR --network KEY`, `delete <TENANT> <BLOCK> [--yes]`
- SDK: `tenant_obj.network_blocks`

**External IPs** (`vrg tenant ext-ip`):
- Columns: `$key` (Key), `ip_address` (IP), `network_name` (Network), `hostname` (wide_only)
- Commands: `list <TENANT>`, `create <TENANT> --ip IP --network KEY [--hostname]`, `delete <TENANT> <IP> [--yes]`
- SDK: `tenant_obj.external_ips`

**Layer 2 Networks** (`vrg tenant l2`):
- Columns: `$key` (Key), `network_name` (Network), `network_type` (Type), `is_enabled` (Enabled, Yes/No)
- Commands: `list <TENANT>`, `create <TENANT> --network-name NAME`, `delete <TENANT> <L2> [--yes]`
- SDK: `tenant_obj.l2_networks`

#### `vrg tenant snapshot` — Tenant Snapshots

**File:** `src/verge_cli/commands/tenant_snapshot.py`
**SDK:** `tenant_obj.snapshots` → `TenantSnapshotManager`

**Columns:**

| Key | Header | Notes |
|-----|--------|-------|
| `$key` | Key | |
| `name` | Name | |
| `created` | Created | format_fn: epoch→datetime |
| `expires` | Expires | format_fn: 0→"Never", else datetime |
| `profile` | Profile | wide_only |

**Commands:**

| Command | SDK Call |
|---------|---------|
| `vrg tenant snapshot list <TENANT>` | `tenant_obj.snapshots.list()` |
| `vrg tenant snapshot get <TENANT> <SNAPSHOT>` | `tenant_obj.snapshots.get(key)` |
| `vrg tenant snapshot create <TENANT> [--name] [--retention SECS]` | `tenant_obj.snapshots.create(...)` |
| `vrg tenant snapshot delete <TENANT> <SNAPSHOT> [--yes]` | `tenant_obj.snapshots.delete(key)` |
| `vrg tenant snapshot restore <TENANT> <SNAPSHOT>` | `tenant_obj.snapshots.restore(key)` |

#### `vrg tenant stats` / `logs` — Monitoring

**File:** `src/verge_cli/commands/tenant_stats.py` (two sub-Typer apps)

**Stats** (`vrg tenant stats`):

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg tenant stats current <TENANT>` | `tenant_obj.stats.get()` | ram_used_mb, total_cpu_percent, per-tier usage |
| `vrg tenant stats history <TENANT> [--limit 20]` | `tenant_obj.stats.history_short(limit=N)` | Time series as table |

**Logs** (`vrg tenant logs`):

| Command | SDK Call | Notes |
|---------|---------|-------|
| `vrg tenant logs list <TENANT> [--limit 50] [--errors-only]` | `tenant_obj.logs.list(...)` | Activity logs |

---

## Registration

### In `cli.py`:

```python
from verge_cli.commands import cluster, node, storage, tenant
app.add_typer(cluster.app, name="cluster")
app.add_typer(node.app, name="node")
app.add_typer(storage.app, name="storage")
app.add_typer(tenant.app, name="tenant")
```

### In `tenant.py`:

```python
from verge_cli.commands import (
    tenant_node, tenant_storage, tenant_net,
    tenant_snapshot, tenant_stats,
)
app.add_typer(tenant_node.app, name="node")
app.add_typer(tenant_storage.app, name="storage")
app.add_typer(tenant_net.net_block_app, name="net-block")
app.add_typer(tenant_net.ext_ip_app, name="ext-ip")
app.add_typer(tenant_net.l2_app, name="l2")
app.add_typer(tenant_snapshot.app, name="snapshot")
app.add_typer(tenant_stats.stats_app, name="stats")
app.add_typer(tenant_stats.logs_app, name="logs")
# crash-cart is a sub-Typer defined within tenant.py itself
```

---

## Tab Completion

Typer provides shell completion out of the box:

- `vrg --install-completion [bash|zsh|fish|powershell]`
- `vrg --show-completion [bash|zsh|fish|powershell]`

Static completion only (commands, subcommands, flags). Dynamic resource name completion deferred.

Verify completion works and document in README.

---

## New Files

| File | Purpose |
|------|---------|
| `src/verge_cli/commands/cluster.py` | Cluster CRUD + vsan-status |
| `src/verge_cli/commands/node.py` | Node list/get/maintenance/restart |
| `src/verge_cli/commands/storage.py` | Storage tier list/get/summary |
| `src/verge_cli/commands/tenant.py` | Tenant CRUD + power + clone + isolate + crash-cart + send-file |
| `src/verge_cli/commands/tenant_node.py` | Tenant compute allocation |
| `src/verge_cli/commands/tenant_storage.py` | Tenant storage allocation |
| `src/verge_cli/commands/tenant_net.py` | Tenant net-block, ext-ip, l2 |
| `src/verge_cli/commands/tenant_snapshot.py` | Tenant snapshots |
| `src/verge_cli/commands/tenant_stats.py` | Tenant stats + logs |
| `tests/unit/test_cluster.py` | Cluster tests |
| `tests/unit/test_node.py` | Node tests |
| `tests/unit/test_storage.py` | Storage tier tests |
| `tests/unit/test_tenant.py` | Tenant core tests |
| `tests/unit/test_tenant_node.py` | Tenant node tests |
| `tests/unit/test_tenant_storage.py` | Tenant storage tests |
| `tests/unit/test_tenant_net.py` | Tenant networking tests |
| `tests/unit/test_tenant_snapshot.py` | Tenant snapshot tests |
| `tests/unit/test_tenant_stats.py` | Tenant stats/logs tests |

---

## Testing Strategy

- **New conftest fixtures:** `mock_tenant`, `mock_cluster`, `mock_node`, `mock_storage_tier`
- **Tenant sub-resource mocks:** Created per test file (not in conftest — too many)
- **Pattern:** Mock SDK → invoke CLI → assert exit code + output content
- **Validation:** `ruff check`, `ruff format --check`, `mypy`, `pytest` on each module
- **Regression:** Full `pytest tests/unit/` after each command module is complete

---

## Implementation Order

1. **Cluster** — straightforward CRUD, good warmup
2. **Node** — simple (no create/update/delete)
3. **Storage** — read-only, smallest scope
4. **Tenant core** — CRUD + power + actions (largest single file)
5. **Tenant node** — compute allocation sub-resource
6. **Tenant storage** — storage allocation sub-resource
7. **Tenant net** — three networking sub-groups
8. **Tenant snapshot** — snapshot sub-resource
9. **Tenant stats** — stats + logs (last, depends on tenant core)
10. **Tab completion** — verify + document
