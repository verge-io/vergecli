# Verge CLI Shakedown Test

> Full system integration test for verge-cli against a live VergeOS instance.
>
> **LAB/DEV ENVIRONMENT ONLY** — never run this against production.

## Safety Rules

- **NEVER** modify CORE, DMZ, or External networks — only test against resources we deploy
- All test resources use the `shakedown-` prefix for easy identification and cleanup
- Deploying resources IS part of the test — everything is built from scratch
- If a test fails, note it and continue — don't abandon the run

## Prerequisites

- A VergeOS lab/dev instance accessible via network
- Either an existing `~/.vrg/config.toml` or credentials for `vrg configure setup`
- At least one ISO or OVA in the media catalog (for drive import tests)
- An available network range that doesn't conflict with existing infrastructure

## Test Resource Names

| Resource | Name | Notes |
|----------|------|-------|
| Network | `shakedown-net` | Internal network, e.g. 10.99.99.0/24 |
| VM | `shakedown-vm` | Minimal: 1 CPU, 512MB RAM, Linux |
| Tenant | `shakedown-tenant` | Minimal tenant deployment |
| NAS Service | `shakedown-nas` | NAS service VM |
| NAS Volume | `shakedown-vol` | Small test volume |
| Snapshot Profile | `shakedown-profile` | With test period |
| NAS User | `shakedown-user` | Local NAS user |
| Cloud Snapshot | `shakedown-snap` | System-level snapshot |
| VM Snapshot | `shakedown-vm-snap` | Per-VM snapshot |
| Recipe | `shakedown-recipe` | Local recipe for testing |

---

## 1. Configure & System Info

Warmup / read-only tests. Use existing config or create one.

### Configuration

- [ ] `vrg configure setup` — complete interactive setup OR verify existing config works
- [ ] `vrg configure show` — displays host, profile, output format
- [ ] `vrg configure list` — lists all configured profiles

### System

- [ ] `vrg --version` — prints version string
- [ ] `vrg system info` — returns system name, version, uptime, cluster info
- [ ] `vrg system version` — returns VergeOS version string

### Cluster

- [ ] `vrg cluster list` — lists clusters
- [ ] `vrg cluster get <name>` — shows cluster details
- [ ] `vrg cluster vsan-status <name>` — shows vSAN health

### Nodes

- [ ] `vrg node list` — lists all nodes with status
- [ ] `vrg node get <name>` — shows node details (CPU, RAM, role)

### Storage

- [ ] `vrg storage list` — lists all storage tiers
- [ ] `vrg storage get <tier>` — shows tier details (capacity, used, available)
- [ ] `vrg storage summary` — shows aggregate storage across tiers

---

## 2. Network Provisioning

### Create & Start

- [ ] `vrg network create --name shakedown-net --cidr 10.99.99.0/24` — created successfully
- [ ] `vrg network get shakedown-net` — shows name, CIDR, status
- [ ] `vrg network start shakedown-net` — network starts
- [ ] `vrg network status shakedown-net` — shows running status

### Firewall Rules

- [ ] `vrg network rule create shakedown-net --name "Allow SSH" --action accept --protocol tcp --direction incoming --dest-ports 22` — rule created
- [ ] `vrg network rule create shakedown-net --name "Allow HTTP" --action accept --protocol tcp --direction incoming --dest-ports 80,443` — rule created
- [ ] `vrg network rule list shakedown-net` — shows both rules
- [ ] `vrg network rule get shakedown-net <rule-id>` — shows rule details
- [ ] `vrg network rule update shakedown-net <rule-id> --dest-ports 8080` — updated
- [ ] `vrg network rule disable shakedown-net <rule-id>` — rule disabled
- [ ] `vrg network rule enable shakedown-net <rule-id>` — rule re-enabled
- [ ] `vrg network apply-rules shakedown-net` — rules applied

### DNS

- [ ] `vrg network dns view list shakedown-net` — lists views
- [ ] `vrg network dns view create shakedown-net --name shakedown-view` — view created
- [ ] `vrg network dns zone create shakedown-net shakedown-view --name shakedown.local` — zone created
- [ ] `vrg network dns zone list shakedown-net shakedown-view` — shows zone
- [ ] `vrg network dns zone get shakedown-net shakedown-view <zone-id>` — zone details
- [ ] `vrg network dns record create shakedown-net shakedown-view shakedown.local --name www --type A --value 10.99.99.10` — record created
- [ ] `vrg network dns record list shakedown-net shakedown-view shakedown.local` — shows record
- [ ] `vrg network dns record get shakedown-net shakedown-view shakedown.local <record-id>` — record details
- [ ] `vrg network dns record update shakedown-net shakedown-view shakedown.local <record-id> --value 10.99.99.20` — updated
- [ ] `vrg network dns record delete shakedown-net shakedown-view shakedown.local <record-id> --yes` — deleted
- [ ] `vrg network dns zone delete shakedown-net shakedown-view <zone-id> --yes` — deleted
- [ ] `vrg network dns view delete shakedown-net <view-id> --yes` — deleted
- [ ] `vrg network apply-dns shakedown-net` — DNS applied

### Host Overrides

- [ ] `vrg network host create shakedown-net --hostname testhost --ip 10.99.99.50 --mac 00:11:22:33:44:55` — host created
- [ ] `vrg network host list shakedown-net` — shows host
- [ ] `vrg network host get shakedown-net <host-id>` — host details
- [ ] `vrg network host update shakedown-net <host-id> --ip 10.99.99.51` — updated
- [ ] `vrg network host delete shakedown-net <host-id> --yes` — deleted

### IP Aliases

- [ ] `vrg network alias create shakedown-net --ip 10.99.99.200` — alias created
- [ ] `vrg network alias list shakedown-net` — shows alias
- [ ] `vrg network alias get shakedown-net <alias-id>` — alias details
- [ ] `vrg network alias update shakedown-net <alias-id> --description "test alias"` — updated
- [ ] `vrg network alias delete shakedown-net <alias-id> --yes` — deleted

### Network Diagnostics

- [ ] `vrg network diag leases shakedown-net` — shows DHCP leases (may be empty)
- [ ] `vrg network diag addresses shakedown-net` — shows IP addresses in use
- [ ] `vrg network diag stats shakedown-net` — shows network statistics

---

## 3. VM Provisioning

### Create & Lifecycle

- [ ] `vrg vm create --name shakedown-vm --cpu 1 --ram 512 --os linux` — VM created
- [ ] `vrg vm list` — shows shakedown-vm
- [ ] `vrg vm get shakedown-vm` — shows name, CPU, RAM, OS, status
- [ ] `vrg vm update shakedown-vm --description "Shakedown test VM"` — updated
- [ ] `vrg vm start shakedown-vm` — VM starts
- [ ] `vrg vm stop shakedown-vm` — VM stops (graceful)
- [ ] `vrg vm start shakedown-vm` — restart for further tests
- [ ] `vrg vm restart shakedown-vm` — graceful restart
- [ ] `vrg vm reset shakedown-vm` — hard reset

### Drives

- [ ] `vrg vm drive list shakedown-vm` — empty or default drive
- [ ] `vrg vm drive create shakedown-vm --size 10GB --name "Boot Disk"` — drive created
- [ ] `vrg vm drive create shakedown-vm --size 5GB --name "Data Disk" --interface ide --tier 2` — second drive
- [ ] `vrg vm drive list shakedown-vm` — shows both drives
- [ ] `vrg vm drive get shakedown-vm "Boot Disk"` — shows size, interface, tier
- [ ] `vrg vm drive update shakedown-vm "Boot Disk" --name "OS Disk"` — renamed
- [ ] `vrg vm drive update shakedown-vm "OS Disk" --disabled` — disabled
- [ ] `vrg vm drive update shakedown-vm "OS Disk" --enabled` — re-enabled
- [ ] `vrg vm drive import shakedown-vm --file-name <ova-or-iso> --name "Imported"` — imported from catalog
- [ ] `vrg vm drive delete shakedown-vm "Imported" --yes` — deleted
- [ ] `vrg vm drive delete shakedown-vm "Data Disk" --yes` — deleted

### NICs

- [ ] `vrg vm nic create shakedown-vm --network shakedown-net --name "Primary NIC"` — NIC created
- [ ] `vrg vm nic create shakedown-vm --network shakedown-net --name "Static NIC" --ip 10.99.99.50` — static IP
- [ ] `vrg vm nic list shakedown-vm` — shows both NICs
- [ ] `vrg vm nic get shakedown-vm "Primary NIC"` — shows MAC, network, IP
- [ ] `vrg vm nic update shakedown-vm "Primary NIC" --name "mgmt0"` — renamed
- [ ] `vrg vm nic update shakedown-vm "mgmt0" --disabled` — disabled
- [ ] `vrg vm nic update shakedown-vm "mgmt0" --enabled` — re-enabled
- [ ] `vrg vm nic delete shakedown-vm "Static NIC" --yes` — deleted
- [ ] `vrg vm nic delete shakedown-vm "mgmt0" --yes` — deleted

### Devices (TPM)

- [ ] `vrg vm device create shakedown-vm --name "Test TPM" --model tis --version 2` — TPM created
- [ ] `vrg vm device list shakedown-vm` — shows TPM
- [ ] `vrg vm device get shakedown-vm "Test TPM"` — shows device type
- [ ] `vrg vm device delete shakedown-vm "Test TPM" --yes` — deleted

### VM Snapshots

- [ ] `vrg vm snapshot create shakedown-vm --name shakedown-vm-snap` — snapshot created
- [ ] `vrg vm snapshot list shakedown-vm` — shows snapshot
- [ ] `vrg vm snapshot get shakedown-vm <snap-id>` — snapshot details
- [ ] `vrg vm snapshot delete shakedown-vm <snap-id> --yes` — deleted

### Templates

- [ ] `vrg vm validate <template-file>` — validates a .vrg.yaml template without creating
- [ ] `vrg vm create --template <template-file>` — creates VM from template (if template available)

---

## 4. Tenant Provisioning

### Create & Lifecycle

- [ ] `vrg tenant create --name shakedown-tenant --password <admin-pass>` — tenant created
- [ ] `vrg tenant list` — shows shakedown-tenant
- [ ] `vrg tenant get shakedown-tenant` — shows name, status, is_isolated
- [ ] `vrg tenant update shakedown-tenant --description "Shakedown test tenant"` — updated

### Resource Allocation

- [ ] `vrg tenant node list shakedown-tenant` — list node allocations (may be empty)
- [ ] `vrg tenant node create shakedown-tenant --cpu-cores 2 --ram-gb 4` — allocate compute
- [ ] `vrg tenant node get shakedown-tenant <alloc-id>` — allocation details (cpu_cores, ram_gb)
- [ ] `vrg tenant node update shakedown-tenant <alloc-id> --cpu-cores 4` — update allocation
- [ ] `vrg tenant node update shakedown-tenant <alloc-id> --enabled` — enable via update flag
- [ ] `vrg tenant node update shakedown-tenant <alloc-id> --disabled` — disable via update flag
- [ ] `vrg tenant storage list shakedown-tenant` — list storage allocations
- [ ] `vrg tenant storage create shakedown-tenant --tier 1 --provisioned-gb 50` — allocate storage
- [ ] `vrg tenant storage get shakedown-tenant <alloc-id>` — allocation details (tier, provisioned_gb)
- [ ] `vrg tenant storage update shakedown-tenant <alloc-id> --provisioned-gb 100` — update size

### Networking

- [ ] `vrg tenant net-block list shakedown-tenant` — list network blocks
- [ ] `vrg tenant net-block create shakedown-tenant --cidr 10.99.99.0/24 --network <network-key>` — create block
- [ ] `vrg tenant net-block delete shakedown-tenant <block-id> --yes` — delete block
- [ ] `vrg tenant ext-ip list shakedown-tenant` — list external IPs
- [ ] `vrg tenant ext-ip create shakedown-tenant --ip <ip> --network <network-key>` — allocate IP
- [ ] `vrg tenant ext-ip delete shakedown-tenant <ip-id> --yes` — delete IP
- [ ] `vrg tenant l2 list shakedown-tenant` — list L2 networks
- [ ] `vrg tenant l2 create shakedown-tenant --network-name <network>` — create L2 pass-through
- [ ] `vrg tenant l2 delete shakedown-tenant <l2-id> --yes` — delete L2

### Tenant Start & Operations

- [ ] `vrg tenant start shakedown-tenant` — tenant starts
- [ ] `vrg tenant stop shakedown-tenant` — tenant stops
- [ ] `vrg tenant restart shakedown-tenant` — tenant restarts
- [ ] `vrg tenant reset shakedown-tenant --yes` — hard reset
- [ ] `vrg tenant isolate shakedown-tenant --enable` — network isolation enabled
- [ ] `vrg tenant isolate shakedown-tenant --disable` — network isolation disabled

### Tenant Snapshots

- [ ] `vrg tenant snapshot create shakedown-tenant --name "shakedown-tenant-snap"` — snapshot created
- [ ] `vrg tenant snapshot list shakedown-tenant` — shows snapshot
- [ ] `vrg tenant snapshot get shakedown-tenant <snap-id>` — snapshot details
- [ ] `vrg tenant snapshot delete shakedown-tenant <snap-id> --yes` — deleted

### Crash Cart

- [ ] `vrg tenant crash-cart create shakedown-tenant` — crash cart created
- [ ] `vrg tenant crash-cart delete shakedown-tenant --yes` — crash cart deleted

### Clone

- [ ] `vrg tenant clone shakedown-tenant --name shakedown-tenant-clone` — tenant cloned
- [ ] `vrg tenant get shakedown-tenant-clone` — verify clone exists
- [ ] `vrg tenant delete shakedown-tenant-clone --yes --force` — delete clone

### Tenant Stats & Logs

- [ ] `vrg tenant stats current shakedown-tenant` — shows current resource usage (ram_used_mb)
- [ ] `vrg tenant stats history shakedown-tenant --limit 5` — shows usage history
- [ ] `vrg tenant logs list shakedown-tenant` — shows activity logs
- [ ] `vrg tenant logs list shakedown-tenant --errors-only` — filters to errors only

---

## 5. Snapshot System

### Cloud Snapshots

- [ ] `vrg snapshot create --name shakedown-snap` — cloud snapshot created
- [ ] `vrg snapshot list` — shows shakedown-snap
- [ ] `vrg snapshot get shakedown-snap` — snapshot details (status, created, expires)
- [ ] `vrg snapshot vms shakedown-snap` — lists VMs in snapshot
- [ ] `vrg snapshot tenants shakedown-snap` — lists tenants in snapshot
- [ ] `vrg snapshot delete shakedown-snap --yes` — deleted

### Snapshot Profiles

- [ ] `vrg snapshot profile create --name shakedown-profile --description "Test profile"` — created
- [ ] `vrg snapshot profile list` — shows profile
- [ ] `vrg snapshot profile get shakedown-profile` — profile details
- [ ] `vrg snapshot profile update shakedown-profile --description "Updated"` — updated

### Profile Periods

- [ ] `vrg snapshot profile period create shakedown-profile --frequency hourly --retention 3600` — period created
- [ ] `vrg snapshot profile period list shakedown-profile` — shows period
- [ ] `vrg snapshot profile period get shakedown-profile <period-id>` — period details
- [ ] `vrg snapshot profile period update shakedown-profile <period-id> --retention 7200` — updated
- [ ] `vrg snapshot profile period delete shakedown-profile <period-id> --yes` — deleted
- [ ] `vrg snapshot profile delete shakedown-profile --yes` — profile deleted

---

## 6. NAS Provisioning

### NAS Service

- [ ] `vrg nas service create --name shakedown-nas` — NAS service created
- [ ] `vrg nas service list` — shows shakedown-nas
- [ ] `vrg nas service get shakedown-nas` — service details
- [ ] `vrg nas service update shakedown-nas --description "Shakedown NAS"` — updated
- [ ] `vrg nas service power-on shakedown-nas` — service powered on
- [ ] `vrg nas service cifs-settings shakedown-nas` — shows CIFS settings
- [ ] `vrg nas service nfs-settings shakedown-nas` — shows NFS settings
- [ ] `vrg nas service set-cifs-settings shakedown-nas --workgroup SHAKEDOWN` — CIFS updated
- [ ] `vrg nas service set-nfs-settings shakedown-nas --enable-nfsv4` — NFS updated

### Volumes

- [ ] `vrg nas volume create shakedown-nas --name shakedown-vol --size 10` — volume created
- [ ] `vrg nas volume list shakedown-nas` — shows volume
- [ ] `vrg nas volume get shakedown-nas shakedown-vol` — volume details (size, fs_type)
- [ ] `vrg nas volume update shakedown-nas shakedown-vol --description "Test volume"` — updated
- [ ] `vrg nas volume disable shakedown-nas shakedown-vol` — disabled
- [ ] `vrg nas volume enable shakedown-nas shakedown-vol` — re-enabled

### Volume Snapshots

- [ ] `vrg nas volume snapshot create shakedown-nas shakedown-vol --name shakedown-vol-snap` — created
- [ ] `vrg nas volume snapshot list shakedown-nas shakedown-vol` — shows snapshot
- [ ] `vrg nas volume snapshot get shakedown-nas shakedown-vol <snap-id>` — details
- [ ] `vrg nas volume snapshot delete shakedown-nas shakedown-vol <snap-id> --yes` — deleted

### Shares

- [ ] `vrg nas cifs create shakedown-nas --volume shakedown-vol --name shakedown-cifs` — CIFS share created
- [ ] `vrg nas cifs list shakedown-nas` — shows share
- [ ] `vrg nas cifs get shakedown-nas shakedown-cifs` — share details
- [ ] `vrg nas cifs update shakedown-nas shakedown-cifs --description "Test CIFS"` — updated
- [ ] `vrg nas cifs disable shakedown-nas shakedown-cifs` — disabled
- [ ] `vrg nas cifs enable shakedown-nas shakedown-cifs` — re-enabled
- [ ] `vrg nas nfs create shakedown-nas --volume shakedown-vol --name shakedown-nfs` — NFS share created
- [ ] `vrg nas nfs list shakedown-nas` — shows share
- [ ] `vrg nas nfs get shakedown-nas shakedown-nfs` — share details
- [ ] `vrg nas nfs update shakedown-nas shakedown-nfs --description "Test NFS"` — updated
- [ ] `vrg nas nfs disable shakedown-nas shakedown-nfs` — disabled
- [ ] `vrg nas nfs enable shakedown-nas shakedown-nfs` — re-enabled

### Users

- [ ] `vrg nas user create shakedown-nas --name shakedown-user --password TestPass123` — user created
- [ ] `vrg nas user list shakedown-nas` — shows user
- [ ] `vrg nas user get shakedown-nas shakedown-user` — user details
- [ ] `vrg nas user update shakedown-nas shakedown-user --description "Test user"` — updated
- [ ] `vrg nas user disable shakedown-nas shakedown-user` — disabled
- [ ] `vrg nas user enable shakedown-nas shakedown-user` — re-enabled

### NAS Files

- [ ] `vrg nas files list shakedown-nas shakedown-vol` — lists files (may show .snapshots, lost+found)
- [ ] `vrg nas files get shakedown-nas shakedown-vol <filename>` — file details

### NAS Sync

> Requires a remote NAS target. Skip if not available.

- [ ] `vrg nas sync list shakedown-nas` — list sync jobs (may be empty)
- [ ] `vrg nas sync create shakedown-nas ...` — create sync job (if remote target available)

---

## 7. Sites & Syncs

> Site create/delete require a remote VergeOS instance. Test read operations
> and enable/disable on existing sites if available.

- [ ] `vrg site list` — lists registered sites
- [ ] `vrg site get <site>` — site details (URL, status, auth_status)
- [ ] `vrg site update <site> --description "test"` — updated (revert after)
- [ ] `vrg site disable <site>` — disabled
- [ ] `vrg site enable <site>` — re-enabled
- [ ] `vrg site sync outgoing list` — lists outgoing syncs
- [ ] `vrg site sync outgoing get <sync-id>` — sync details
- [ ] `vrg site sync outgoing disable <sync-id>` — disabled
- [ ] `vrg site sync outgoing enable <sync-id>` — re-enabled
- [ ] `vrg site sync incoming list` — lists incoming syncs
- [ ] `vrg site sync incoming get <sync-id>` — sync details
- [ ] `vrg site sync incoming disable <sync-id>` — disabled
- [ ] `vrg site sync incoming enable <sync-id>` — re-enabled

---

## 8. Recipes

### Recipe CRUD

- [ ] `vrg recipe list` — lists available recipes
- [ ] `vrg recipe get <recipe>` — recipe details
- [ ] `vrg recipe create --name shakedown-recipe --catalog "Test" --version 1` — local recipe created

### Sections & Questions

- [ ] `vrg recipe section create shakedown-recipe --name "General" --description "General settings"` — section created
- [ ] `vrg recipe section list shakedown-recipe` — shows section
- [ ] `vrg recipe section get shakedown-recipe <section-id>` — section details
- [ ] `vrg recipe section update shakedown-recipe <section-id> --description "Updated"` — updated
- [ ] `vrg recipe question create shakedown-recipe --name "vm_name" --type string --section <section-id> --display "VM Name"` — question created
- [ ] `vrg recipe question list shakedown-recipe` — shows question
- [ ] `vrg recipe question get shakedown-recipe <question-id>` — question details
- [ ] `vrg recipe question update shakedown-recipe <question-id> --display "Server Name"` — updated
- [ ] `vrg recipe question delete shakedown-recipe <question-id> --yes` — deleted
- [ ] `vrg recipe section delete shakedown-recipe <section-id> --yes` — deleted

### Deploy & Instances

- [ ] `vrg recipe deploy shakedown-recipe --name "shakedown-deployed"` — deploys recipe as VM
- [ ] `vrg recipe instance list` — lists deployed instances, shows shakedown-deployed
- [ ] `vrg recipe instance get <instance-id>` — instance details
- [ ] `vrg recipe instance delete <instance-id> --yes` — instance deleted

### Recipe Logs

- [ ] `vrg recipe log list` — lists recipe operation logs
- [ ] `vrg recipe log get <log-id>` — log entry details

### Recipe Cleanup

- [ ] `vrg recipe delete shakedown-recipe --yes` — deleted

---

## 9. Media Catalog

- [ ] `vrg file list` — lists media catalog files
- [ ] `vrg file get <filename>` — file details (name, type, size, tier)
- [ ] `vrg file types` — lists supported file types
- [ ] `vrg file update <filename> --description "test"` — updated (revert after)

> Upload/download tests require local files. Skip if not practical.

- [ ] `vrg file upload <local-file>` — file uploaded to catalog
- [ ] `vrg file download <filename>` — file downloaded
- [ ] `vrg file delete <filename> --yes` — uploaded file deleted

---

## 10. Cross-Cutting Tests

Run these against any representative commands (e.g., `vm list`, `network get`).

### Output Formats

- [ ] `vrg vm list -o table` — formatted table output
- [ ] `vrg vm list -o wide` — wide table with extra columns
- [ ] `vrg vm list -o json` — valid JSON array
- [ ] `vrg vm list -o csv` — proper CSV with headers
- [ ] `vrg vm get shakedown-vm -o json` — valid JSON object
- [ ] `vrg vm get shakedown-vm --query name` — returns plain value "shakedown-vm"
- [ ] `vrg vm list -q` — quiet mode, minimal output

### Error Handling

- [ ] `vrg vm get nonexistent-vm` — exit code 6, "not found" message
- [ ] `vrg network get nonexistent-net` — exit code 6
- [ ] `vrg vm drive get shakedown-vm "No Such Drive"` — exit code 6
- [ ] `vrg vm update shakedown-vm` (no flags) — exit code 2, "no updates specified"

### Global Options

- [ ] `vrg --profile <name> vm list` — uses specified profile
- [ ] `vrg --no-color vm list` — output without ANSI colors
- [ ] `vrg -H <host> --token <token> vm list` — inline credentials work

---

## 11. Cleanup

Delete all test resources in reverse order. Verify each deletion.

### NAS Cleanup

- [ ] Delete NAS user: `vrg nas user delete shakedown-nas shakedown-user --yes`
- [ ] Delete NFS share: `vrg nas nfs delete shakedown-nas shakedown-nfs --yes`
- [ ] Delete CIFS share: `vrg nas cifs delete shakedown-nas shakedown-cifs --yes`
- [ ] Delete NAS volume: `vrg nas volume delete shakedown-nas shakedown-vol --yes`
- [ ] Power off NAS: `vrg nas service power-off shakedown-nas`
- [ ] Delete NAS service: `vrg nas service delete shakedown-nas --yes`

### Tenant Cleanup

- [ ] Delete tenant net-blocks: `vrg tenant net-block delete shakedown-tenant <block-id> --yes`
- [ ] Delete tenant ext-ips: `vrg tenant ext-ip delete shakedown-tenant <ip-id> --yes`
- [ ] Delete tenant L2s: `vrg tenant l2 delete shakedown-tenant <l2-id> --yes`
- [ ] Delete tenant storage: `vrg tenant storage delete shakedown-tenant <alloc-id> --yes`
- [ ] Delete tenant nodes: `vrg tenant node delete shakedown-tenant <alloc-id> --yes`
- [ ] Stop tenant: `vrg tenant stop shakedown-tenant`
- [ ] Delete tenant: `vrg tenant delete shakedown-tenant --yes --force`

### VM Cleanup

- [ ] Delete remaining drives: `vrg vm drive delete shakedown-vm "OS Disk" --yes`
- [ ] Stop VM: `vrg vm stop shakedown-vm --force`
- [ ] Delete VM: `vrg vm delete shakedown-vm --yes`

### Network Cleanup

- [ ] Stop network: `vrg network stop shakedown-net`
- [ ] Delete network: `vrg network delete shakedown-net --yes`

### Verification

- [ ] `vrg vm list` — shakedown-vm not present
- [ ] `vrg network list` — shakedown-net not present
- [ ] `vrg tenant list` — shakedown-tenant not present
- [ ] `vrg nas service list` — shakedown-nas not present
- [ ] `vrg snapshot profile list` — shakedown-profile not present

---

## 12. Results

### Summary

| Section | Tests | Passed | Failed | Notes |
|---------|-------|--------|--------|-------|
| 1. Configure & System | | | | |
| 2. Network Provisioning | | | | |
| 3. VM Provisioning | | | | |
| 4. Tenant Provisioning | | | | |
| 5. Snapshot System | | | | |
| 6. NAS Provisioning | | | | |
| 7. Sites & Syncs | | | | |
| 8. Recipes | | | | |
| 9. Media Catalog | | | | |
| 10. Cross-Cutting | | | | |
| 11. Cleanup | | | | |
| **Total** | | | | |

### Issues Found

| # | Severity | Command | Description |
|---|----------|---------|-------------|
| | | | |

### Environment

- **Date:** YYYY-MM-DD
- **VergeOS Version:**
- **CLI Version:** `vrg --version`
- **Tester:**
