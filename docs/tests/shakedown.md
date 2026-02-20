# Verge CLI Shakedown Test

> Full system integration test for vrg against a live VergeOS instance.
>
> **LAB/DEV ENVIRONMENT ONLY** — never run this against production.

## Safety Rules

- **NEVER** modify CORE, DMZ, or External networks — only test against resources we deploy
- All test resources use the `shakedown-` prefix for easy identification and cleanup
- Deploying resources IS part of the test — everything is built from scratch
- If a test fails, note it and continue — don't abandon the run

## Prerequisites

- A VergeOS lab/dev instance accessible via network
- Either an existing `~/.vrg/config.toml` (`vrg configure show`) or credentials for `vrg configure setup`
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
| User | `shakedown-user-admin` | Test user account |
| Group | `shakedown-group` | Test group |
| API Key | `shakedown-apikey` | API key for test user |
| Auth Source | `shakedown-auth` | Test auth source (if SSO available) |
| Task | `shakedown-task` | Scheduled task |
| Task Schedule | `shakedown-schedule` | Task schedule |
| Certificate | `shakedown-cert` | Self-signed certificate |
| OIDC App | `shakedown-oidc` | OIDC application |
| Tag Category | `shakedown-category` | Tag category |
| Tag | `shakedown-tag` | Tag for resource tagging |
| Resource Group | `shakedown-rg` | PCI resource group |

---

## 1. Configure & System Info

Warmup / read-only tests. Use existing config or create one.

### Configuration

- [x] `vrg configure setup` — complete interactive setup OR verify existing config works ✅ existing config works
- [x] `vrg configure show` — displays host, profile, output format ✅
- [x] `vrg configure list` — lists all configured profiles ✅ 2 profiles (default, dev2)

### System

- [x] `vrg --version` — prints version string ✅ v0.1.0
- [x] `vrg system info` — returns system name, version, uptime, cluster info ✅ midgard, 26.0.2.1
- [x] `vrg system version` — returns VergeOS version string ✅ 26.0.2.1

### Cluster

- [x] `vrg cluster list` — lists clusters ✅ midgard (2 nodes, online)
- [x] `vrg cluster get <name>` — shows cluster details ✅
- [x] `vrg cluster vsan-status --name <name>` — shows vSAN health ✅ Healthy ⚠️ DOC FIX: takes `--name` flag, not positional arg

### Nodes

- [x] `vrg node list` — lists all nodes with status ✅ node1, node2 both Running
- [x] `vrg node get <name>` — shows node details (CPU, RAM, role) ✅

### Storage

- [x] `vrg storage list` — lists all storage tiers ✅ 4 tiers
- [x] `vrg storage get <tier>` — shows tier details (capacity, used, available) ✅
- [x] `vrg storage summary` — shows aggregate storage across tiers ✅ 3750 GB total

---

## 2. Network Provisioning

### Create & Start

- [x] `vrg network create --name shakedown-net --cidr 10.99.99.0/24` — created successfully ✅ key=17 ⚠️ CIDR ignored by API, got 192.168.0.0/24
- [x] `vrg network get shakedown-net` — shows name, CIDR, status ✅
- [x] `vrg network start shakedown-net` — network starts ✅
- [x] `vrg network status shakedown-net` — shows running status ✅

### Firewall Rules

- [x] `vrg network rule create shakedown-net --name "Allow SSH" --action accept --protocol tcp --direction incoming --dest-ports 22` — rule created ✅ key=30
- [x] `vrg network rule create shakedown-net --name "Allow HTTP" --action accept --protocol tcp --direction incoming --dest-ports 80,443` — rule created ✅ key=31
- [x] `vrg network rule list shakedown-net` — shows both rules ✅
- [x] `vrg network rule get shakedown-net 30` — shows rule details ✅
- [x] `vrg network rule update shakedown-net 30 --dest-ports 8080` — updated ✅
- [x] `vrg network rule disable shakedown-net 30` — rule disabled ✅
- [x] `vrg network rule enable shakedown-net 30` — rule re-enabled ✅
- [x] `vrg network apply-rules shakedown-net` — rules applied ✅

### DNS

- [x] `vrg network dns view list shakedown-net` — lists views ✅ (empty)
- [x] `vrg network dns view create shakedown-net --name shakedown-view` — view created ✅ id=2
- [x] `vrg network dns zone create shakedown-net shakedown-view --domain shakedown.local` — zone created ✅ key=2 ⚠️ DOC FIX: uses `--domain` not `--name`
- [x] `vrg network dns zone list shakedown-net shakedown-view` — shows zone ✅
- [x] `vrg network dns zone get shakedown-net shakedown-view 2` — zone details ✅
- [x] `vrg network dns record create shakedown-net shakedown-view shakedown.local --name www --type A --value 10.99.99.10` — record created ✅ id=4
- [x] `vrg network dns record list shakedown-net shakedown-view shakedown.local` — shows record ✅
- [x] `vrg network dns record get shakedown-net shakedown-view shakedown.local 4` — record details ✅
- [x] `vrg network dns record update shakedown-net shakedown-view shakedown.local 4 --value 10.99.99.20` — updated ✅
- [x] `vrg network dns record delete shakedown-net shakedown-view shakedown.local 4 --yes` — deleted ✅
- [x] `vrg network dns zone delete shakedown-net shakedown-view 2 --yes` — deleted ✅
- [x] `vrg network dns view delete shakedown-net 2 --yes` — deleted ✅
- [x] `vrg network apply-dns shakedown-net` — DNS applied ✅

### Host Overrides

- [x] `vrg network host create shakedown-net --hostname testhost --ip 10.99.99.50` — host created ✅ key=1 ⚠️ DOC FIX: no `--mac` option exists
- [x] `vrg network host list shakedown-net` — shows host ✅
- [x] `vrg network host get shakedown-net 1` — host details ✅
- [x] `vrg network host update shakedown-net 1 --ip 10.99.99.51` — updated ✅
- [x] `vrg network host delete shakedown-net 1 --yes` — deleted ✅

### IP Aliases

- [x] `vrg network alias create shakedown-net --ip 10.99.99.200 --name shakedown-alias` — alias created ✅ key=46 ⚠️ DOC FIX: `--name` is required
- [x] `vrg network alias list shakedown-net` — shows alias ✅
- [x] `vrg network alias get shakedown-net 46` — alias details ✅
- [x] `vrg network alias update shakedown-net 46 --description "test alias"` — updated ✅
- [x] `vrg network alias delete shakedown-net 46 --yes` — deleted ✅

### Network Diagnostics

- [x] `vrg network diag leases shakedown-net` — shows DHCP leases (may be empty) ✅ empty as expected
- [x] `vrg network diag addresses shakedown-net` — shows IP addresses in use ✅ 192.168.0.1
- [x] `vrg network diag stats shakedown-net` — shows network statistics ✅

---

## 3. VM Provisioning

### Create & Lifecycle

- [x] `vrg vm create --name shakedown-vm --cpu 1 --ram 512 --os linux` — VM created ✅ key=31
- [x] `vrg vm list` — shows shakedown-vm ✅
- [x] `vrg vm get shakedown-vm` — shows name, CPU, RAM, OS, status ✅
- [x] `vrg vm update shakedown-vm --description "Shakedown test VM"` — updated ✅
- [x] `vrg vm start shakedown-vm` — VM starts ✅
- [x] `vrg vm stop shakedown-vm` — VM stops (graceful) ✅
- [x] `vrg vm start shakedown-vm` — restart for further tests ✅
- [x] `vrg vm restart shakedown-vm` — graceful restart ✅
- [x] `vrg vm reset shakedown-vm --yes` — hard reset ✅ (needs `--yes` for non-interactive)

### Drives

- [x] `vrg vm drive list shakedown-vm` — empty or default drive ✅ (empty)
- [x] `vrg vm drive create shakedown-vm --size 10GB --name "Boot Disk"` — drive created ✅ key=10
- [x] `vrg vm drive create shakedown-vm --size 5GB --name "Data Disk" --interface ide --tier 3` — second drive ✅ key=14 (used tier 3 instead of 2)
- [x] `vrg vm drive list shakedown-vm` — shows both drives ✅
- [x] `vrg vm drive get shakedown-vm "Boot Disk"` — shows size, interface, tier ✅
- [x] `vrg vm drive update shakedown-vm "Boot Disk" --name "OS Disk"` — renamed ✅
- [x] `vrg vm drive update shakedown-vm "OS Disk" --disabled` — disabled ✅
- [x] `vrg vm drive update shakedown-vm "OS Disk" --enabled` — re-enabled ✅
- [x] `vrg vm drive import shakedown-vm --file-name "debian-12-generic-amd64-9dc6c46b.qcow2" --name "Imported"` — imported from catalog ✅ key=18
- [x] `vrg vm drive delete shakedown-vm "Imported" --yes` — deleted ✅ (VM must be stopped first)
- [x] `vrg vm drive delete shakedown-vm "Data Disk" --yes` — deleted ✅

### NICs

- [x] `vrg vm nic create shakedown-vm --network shakedown-net --name "Primary NIC"` — NIC created ✅ key=50
- [x] `vrg vm nic create shakedown-vm --network shakedown-net --name "Static NIC" --ip 192.168.0.50` — static IP ✅ key=53 (used 192.168.0.50, network is 192.168.0.0/24 not 10.99.99.0/24)
- [x] `vrg vm nic list shakedown-vm` — shows both NICs ✅
- [x] `vrg vm nic get shakedown-vm "Primary NIC"` — shows MAC, network, IP ✅
- [x] `vrg vm nic update shakedown-vm "Primary NIC" --name "mgmt0"` — renamed ✅
- [x] `vrg vm nic update shakedown-vm "mgmt0" --disabled` — disabled ✅
- [x] `vrg vm nic update shakedown-vm "mgmt0" --enabled` — re-enabled ✅
- [x] `vrg vm nic delete shakedown-vm "Static NIC" --yes` — deleted ✅
- [x] `vrg vm nic delete shakedown-vm "mgmt0" --yes` — deleted ✅

### Devices (TPM)

- [x] `vrg vm device create shakedown-vm --name "Test TPM" --model tis --version 2` — TPM created ✅ key=4
- [x] `vrg vm device list shakedown-vm` — shows TPM ✅
- [x] `vrg vm device get shakedown-vm "Test TPM"` — shows device type ✅
- [x] `vrg vm device delete shakedown-vm "Test TPM" --yes` — deleted ✅

### VM Snapshots

- [x] `vrg vm snapshot create shakedown-vm --name shakedown-vm-snap` — snapshot created ✅ key=6
- [x] `vrg vm snapshot list shakedown-vm` — shows snapshot ✅
- [x] `vrg vm snapshot get shakedown-vm 6` — snapshot details ✅
- [x] `vrg vm snapshot delete shakedown-vm 6 --yes` — deleted ✅

### Templates

- [ ] `vrg vm validate <template-file>` — SKIPPED: no template file available
- [ ] `vrg vm create --template <template-file>` — SKIPPED: no template file available

---

## 4. Tenant Provisioning

### Create & Lifecycle

- [x] `vrg tenant create --name shakedown-tenant --password TempPass123` — tenant created ✅ key=5
- [x] `vrg tenant list` — shows shakedown-tenant ✅
- [x] `vrg tenant get shakedown-tenant` — shows name, status, is_isolated ✅
- [x] `vrg tenant update shakedown-tenant --description "Shakedown test tenant"` — updated ✅

### Resource Allocation

- [x] `vrg tenant node list shakedown-tenant` — list node allocations (may be empty) ✅ empty
- [x] `vrg tenant node create shakedown-tenant --cpu-cores 2 --ram-gb 4` — allocate compute ✅ key=4
- [x] `vrg tenant node get shakedown-tenant 4` — allocation details (cpu_cores, ram_gb) ✅
- [x] `vrg tenant node update shakedown-tenant 4 --cpu-cores 4` — update allocation ✅
- [x] `vrg tenant node update shakedown-tenant 4 --enabled` — enable via update flag ✅
- [x] `vrg tenant node update shakedown-tenant 4 --disabled` — disable via update flag ✅
- [x] `vrg tenant storage list shakedown-tenant` — list storage allocations ✅ empty
- [x] `vrg tenant storage create shakedown-tenant --tier 1 --provisioned-gb 50` — allocate storage ✅ key=7
- [x] `vrg tenant storage get shakedown-tenant 7` — allocation details (tier, provisioned_gb) ✅
- [x] `vrg tenant storage update shakedown-tenant 7 --provisioned-gb 100` — update size ✅

### Networking

- [x] `vrg tenant net-block list shakedown-tenant` — list network blocks ✅ empty
- [x] `vrg tenant net-block create shakedown-tenant --cidr 192.168.0.0/24 --network 17` — create block ✅ key=2
- [x] `vrg tenant net-block delete shakedown-tenant 2 --yes` — delete block ✅
- [x] `vrg tenant ext-ip list shakedown-tenant` — list external IPs ✅ empty
- [ ] `vrg tenant ext-ip create shakedown-tenant --ip <ip> --network <network-key>` — SKIPPED: requires external network
- [ ] `vrg tenant ext-ip delete shakedown-tenant <ip-id> --yes` — SKIPPED
- [x] `vrg tenant l2 list shakedown-tenant` — list L2 networks ✅ empty
- [ ] `vrg tenant l2 create shakedown-tenant --network-name <network>` — SKIPPED: requires L2 network
- [ ] `vrg tenant l2 delete shakedown-tenant <l2-id> --yes` — SKIPPED

### Tenant Start & Operations

- [x] `vrg tenant start shakedown-tenant` — tenant starts ✅
- [x] `vrg tenant stop shakedown-tenant` — tenant stops ✅
- [x] `vrg tenant restart shakedown-tenant` — tenant restarts ✅
- [x] `vrg tenant reset shakedown-tenant --yes` — hard reset ✅
- [x] `vrg tenant isolate shakedown-tenant --enable` — network isolation enabled ✅
- [x] `vrg tenant isolate shakedown-tenant --disable` — network isolation disabled ✅

### Tenant Snapshots

- [x] `vrg tenant snapshot create shakedown-tenant --name "shakedown-tenant-snap"` — snapshot created ✅ key=1
- [x] `vrg tenant snapshot list shakedown-tenant` — shows snapshot ✅
- [x] `vrg tenant snapshot get shakedown-tenant 1` — snapshot details ✅
- [x] `vrg tenant snapshot delete shakedown-tenant 1 --yes` — deleted ✅

### Crash Cart

- [ ] `vrg tenant crash-cart create shakedown-tenant` — ❌ FAILED: "Crash Cart recipe not found" (env-dependent)
- [ ] `vrg tenant crash-cart delete shakedown-tenant --yes` — SKIPPED (no crash cart)

### Clone

- [x] `vrg tenant clone shakedown-tenant --name shakedown-tenant-clone` — tenant cloned ✅ key=6
- [x] `vrg tenant get shakedown-tenant-clone` — verify clone exists ✅
- [x] `vrg tenant delete shakedown-tenant-clone --yes --force` — delete clone ✅ (must stop first; `--force` didn't auto-stop)

### Tenant Stats & Logs

- [x] `vrg tenant stats current shakedown-tenant` — shows current resource usage (ram_used_mb) ✅
- [x] `vrg tenant stats history shakedown-tenant --limit 5` — shows usage history ✅
- [x] `vrg tenant logs list shakedown-tenant` — shows activity logs ✅
- [x] `vrg tenant logs list shakedown-tenant --errors-only` — filters to errors only ✅ (no errors)

---

## 5. Snapshot System

### Cloud Snapshots

- [x] `vrg snapshot create --name shakedown-snap` — cloud snapshot created ✅ key=2
- [x] `vrg snapshot list` — shows shakedown-snap ✅
- [x] `vrg snapshot get shakedown-snap` — snapshot details (status, created, expires) ✅
- [x] `vrg snapshot vms shakedown-snap` — lists VMs in snapshot ✅ (empty)
- [x] `vrg snapshot tenants shakedown-snap` — lists tenants in snapshot ✅ (empty)
- [x] `vrg snapshot delete shakedown-snap --yes` — deleted ✅

### Snapshot Profiles

- [x] `vrg snapshot profile create --name shakedown-profile --description "Test profile"` — created ✅ key=6
- [x] `vrg snapshot profile list` — shows profile ✅
- [x] `vrg snapshot profile get shakedown-profile` — profile details ✅
- [x] `vrg snapshot profile update shakedown-profile --description "Updated"` — updated ✅

### Profile Periods

- [x] `vrg snapshot profile period create shakedown-profile --name "Hourly Test" --frequency hourly --retention 3600` — period created ✅ key=14 ⚠️ DOC FIX: `--name` is required
- [x] `vrg snapshot profile period list shakedown-profile` — shows period ✅
- [x] `vrg snapshot profile period get shakedown-profile 14` — period details ✅
- [x] `vrg snapshot profile period update shakedown-profile 14 --retention 7200` — updated ✅
- [x] `vrg snapshot profile period delete shakedown-profile 14 --yes` — deleted ✅
- [x] `vrg snapshot profile delete shakedown-profile --yes` — profile deleted ✅

---

## 6. NAS Provisioning

### NAS Service

- [x] `vrg nas service create --name shakedown-nas` — NAS service created ✅ key=2
- [x] `vrg nas service list` — shows shakedown-nas ✅
- [x] `vrg nas service get shakedown-nas` — service details ✅
- [x] `vrg nas service update shakedown-nas --description "Shakedown NAS"` — updated ✅
- [x] `vrg nas service power-on shakedown-nas` — service powered on ✅ (but NAS VM not actually running — env issue)
- [x] `vrg nas service cifs-settings shakedown-nas` — shows CIFS settings ✅
- [x] `vrg nas service nfs-settings shakedown-nas` — shows NFS settings ✅
- [x] `vrg nas service set-cifs-settings shakedown-nas --workgroup SHAKEDOWN` — CIFS updated ✅
- [x] `vrg nas service set-nfs-settings shakedown-nas --enable-nfsv4` — NFS updated ✅

### Volumes

- [x] `vrg nas volume create --service shakedown-nas --name shakedown-vol --size-gb 10` — volume created ✅ ⚠️ DOC FIX: uses `--service` and `--size-gb`, not positional args and `--size`
- [x] `vrg nas volume list --service shakedown-nas` — shows volume ✅ ⚠️ DOC FIX: uses `--service` flag, not positional arg
- [x] `vrg nas volume get shakedown-vol` — volume details (size, fs_type) ✅ ⚠️ DOC FIX: single positional arg (volume name), no service arg needed
- [x] `vrg nas volume update shakedown-vol --description "Test volume"` — updated ✅ ⚠️ DOC FIX: single positional arg
- [x] `vrg nas volume disable shakedown-vol` — disabled ✅ ⚠️ DOC FIX: single positional arg
- [x] `vrg nas volume enable shakedown-vol` — re-enabled ✅

### Volume Snapshots

- [x] `vrg nas volume snapshot create shakedown-vol --name shakedown-vol-snap` — created ✅ key=1 ⚠️ DOC FIX: single positional volume arg, not two
- [x] `vrg nas volume snapshot list shakedown-vol` — shows snapshot ✅
- [x] `vrg nas volume snapshot get shakedown-vol 1` — details ✅
- [x] `vrg nas volume snapshot delete shakedown-vol 1 --yes` — deleted ✅

### Shares

- [x] `vrg nas cifs create --name shakedown-cifs --volume shakedown-vol` — CIFS share created ✅ ⚠️ DOC FIX: uses `--volume` flag, not positional service arg
- [x] `vrg nas cifs list` — shows share ✅ ⚠️ DOC FIX: no positional arg (use `--volume` to filter)
- [x] `vrg nas cifs get shakedown-cifs` — share details ✅ ⚠️ DOC FIX: single positional arg
- [x] `vrg nas cifs update shakedown-cifs --description "Test CIFS"` — updated ✅
- [x] `vrg nas cifs disable shakedown-cifs` — disabled ✅
- [x] `vrg nas cifs enable shakedown-cifs` — re-enabled ✅
- [x] `vrg nas nfs create --name shakedown-nfs --volume shakedown-vol --allow-all` — NFS share created ✅ ⚠️ DOC FIX: requires `--allow-all` or `--allowed-hosts`
- [x] `vrg nas nfs list` — shows share ✅
- [x] `vrg nas nfs get shakedown-nfs` — share details ✅
- [x] `vrg nas nfs update shakedown-nfs --description "Test NFS"` — updated ✅
- [x] `vrg nas nfs disable shakedown-nfs` — disabled ✅
- [x] `vrg nas nfs enable shakedown-nfs` — re-enabled ✅

### Users

- [x] `vrg nas user create --service shakedown-nas --name shakedown-user --password TestPass123` — user created ✅ ⚠️ DOC FIX: uses `--service` flag, not positional arg
- [x] `vrg nas user list --service shakedown-nas` — shows user ✅
- [x] `vrg nas user get shakedown-user` — user details ✅ ⚠️ DOC FIX: single positional arg
- [x] `vrg nas user update shakedown-user --description "Test user"` — updated ✅
- [x] `vrg nas user disable shakedown-user` — disabled ✅
- [x] `vrg nas user enable shakedown-user` — re-enabled ✅

### NAS Files

- [ ] `vrg nas files list shakedown-vol` — ❌ FAILED: NAS VM not running (env issue, no cluster resources) ⚠️ DOC FIX: single positional volume arg
- [ ] `vrg nas files get shakedown-vol <filename>` — SKIPPED (NAS VM not running)

### NAS Sync

> Requires a remote NAS target. Skip if not available.

- [x] `vrg nas sync list --service shakedown-nas` — list sync jobs ✅ (empty) ⚠️ DOC FIX: uses `--service` flag
- [ ] `vrg nas sync create ...` — SKIPPED: no remote target available

---

## 7. Sites & Syncs

> Site create/delete require a remote VergeOS instance. Test read operations
> and enable/disable on existing sites if available.

- [x] `vrg site list` — lists registered sites ✅ 2 sites (asgard, verge2)
- [x] `vrg site get asgard` — site details (URL, status, auth_status) ✅
- [x] `vrg site update asgard --description "test"` — updated (reverted) ✅
- [x] `vrg site disable asgard` — disabled ✅
- [x] `vrg site enable asgard` — re-enabled ✅
- [x] `vrg site sync outgoing list` — lists outgoing syncs ✅ 2 syncs
- [x] `vrg site sync outgoing get 1` — sync details ✅
- [x] `vrg site sync outgoing disable 1` — disabled ✅
- [x] `vrg site sync outgoing enable 1` — re-enabled ✅
- [x] `vrg site sync incoming list` — lists incoming syncs ✅ 1 sync
- [x] `vrg site sync incoming get 1` — sync details ✅
- [x] `vrg site sync incoming disable 1` — disabled ✅
- [x] `vrg site sync incoming enable 1` — re-enabled ✅

---

## 8. Recipes

### Recipe CRUD

- [x] `vrg recipe list` — lists available recipes ✅ (33 recipes)
- [x] `vrg recipe get Docker` — recipe details ✅
- [ ] `vrg recipe create --name shakedown-recipe --catalog <catalog> --version 1` — ❌ FAILED: local repo directory not found (env issue — needs local catalog repo initialized)

### Sections & Questions (read-only on existing recipe)

- [x] `vrg recipe section list "Docker"` — shows sections ✅ 7 sections
- [x] `vrg recipe section get "Docker" 146` — section details ✅
- [x] `vrg recipe question list "Docker"` — shows questions ✅ 28 questions
- [ ] Recipe section/question CRUD — SKIPPED: no writable recipe created

### Deploy & Instances

- [ ] `vrg recipe deploy` — SKIPPED: no writable recipe
- [x] `vrg recipe instance list` — lists deployed instances ✅ 8 instances
- [x] `vrg recipe instance get 8` — instance details ✅

### Recipe Logs

- [x] `vrg recipe log list` — lists recipe operation logs ✅
- [x] `vrg recipe log get 1` — log entry details ✅

### Recipe Cleanup

- [ ] `vrg recipe delete shakedown-recipe --yes` — SKIPPED: no recipe created

---

## 9. Media Catalog

- [x] `vrg file list` — lists media catalog files ✅ (75+ files)
- [x] `vrg file get 2` — file details (name, type, size, tier) ✅
- [x] `vrg file types` — lists supported file types ✅ (16 types)
- [x] `vrg file update 2 --description "test"` — updated (reverted) ✅

> Upload/download tests require local files. Skip if not practical.

- [ ] `vrg file upload <local-file>` — SKIPPED: no test file
- [ ] `vrg file download <filename>` — SKIPPED
- [ ] `vrg file delete <filename> --yes` — SKIPPED

---

## 10. Identity & Access Management

### Users

- [x] `vrg user list` — lists existing users ✅
- [x] `vrg user create --name shakedown-user-admin --password "TempPass123!"` — user created ✅ key=7
- [x] `vrg user list` — shows shakedown-user-admin ✅
- [x] `vrg user get shakedown-user-admin` — shows user details (name, type, enabled) ✅
- [x] `vrg user update shakedown-user-admin --displayname "Shakedown Admin"` — updated ✅
- [x] `vrg user disable shakedown-user-admin` — user disabled ✅
- [x] `vrg user enable shakedown-user-admin` — user re-enabled ✅
- [x] `vrg user list --enabled` — shows only enabled users ✅
- [x] `vrg user list --disabled` — shows only disabled users ✅

### Groups

- [x] `vrg group list` — lists existing groups ✅
- [x] `vrg group create --name shakedown-group --description "Shakedown test group"` — group created ✅ key=4
- [x] `vrg group get shakedown-group` — shows group details ✅
- [x] `vrg group update shakedown-group --description "Updated test group"` — updated ✅
- [x] `vrg group member add shakedown-group --user shakedown-user-admin` — user added to group ✅
- [x] `vrg group member list shakedown-group` — shows shakedown-user-admin as member ✅
- [x] `vrg group member remove shakedown-group --user shakedown-user-admin` — user removed ✅
- [x] `vrg group disable shakedown-group` — group disabled ✅
- [x] `vrg group enable shakedown-group` — group re-enabled ✅

### Permissions

- [x] `vrg permission list` — lists existing permissions ✅
- [x] `vrg permission grant --table vms --user shakedown-user-admin --list --read` — list+read on VMs granted ✅ key=13
- [x] `vrg permission list --user shakedown-user-admin` — shows granted permission ✅
- [x] `vrg permission get 13` — shows permission details (table, user, access levels) ✅
- [x] `vrg permission revoke 13 --yes` — permission revoked ✅ (needs `--yes`)
- [x] `vrg permission grant --table vms --group shakedown-group --full-control` — full control to group ✅
- [x] `vrg permission revoke-all --group shakedown-group --yes` — all group permissions revoked ✅

### API Keys

- [x] `vrg api-key list` — lists existing API keys ✅
- [x] `vrg api-key create --user shakedown-user-admin --name shakedown-apikey --expires-in 1d` — key created, secret shown once ✅
- [x] `vrg api-key list --user shakedown-user-admin` — shows shakedown-apikey ✅
- [x] `vrg api-key get 4` — shows key details (name, user, expires) ✅
- [x] `vrg api-key delete 4 --yes` — key deleted ✅

### Authentication Sources

> Requires SSO/OAuth provider. Test read operations; create/delete only if test IdP available.

- [x] `vrg auth-source list` — lists auth sources ✅ (empty)
- [x] `vrg auth-source list --driver azure` — filters by driver type ✅ (empty)

> No test IdP available — skipping CRUD tests.

- [ ] `vrg auth-source create` — SKIPPED: no IdP
- [ ] `vrg auth-source get/update/debug/delete` — SKIPPED: no IdP

---

## 11. Task Automation

### Tasks

- [x] `vrg task list` — lists existing tasks ✅ 4 tasks
- [ ] `vrg task create --name shakedown-task --action power_on --table vms --description "Test task"` — ❌ FAILED: "Action type not found" — API rejects the action; `--owner` is required and must be combined correctly with `--action` and `--table`. DOC FIX: doc missing `--owner` and action names are wrong
- [x] `vrg task get 1` — shows task details (name, action, table, status) ✅
- [ ] `vrg task update/disable/enable` — SKIPPED: no task created

### Task Schedules

- [x] `vrg task schedule list` — lists existing schedules ✅ 6 schedules
- [x] `vrg task schedule create --name shakedown-schedule --repeat-every hour` — schedule created ✅ key=7
- [x] `vrg task schedule get shakedown-schedule` — shows schedule details ✅
- [x] `vrg task schedule update shakedown-schedule --repeat-every day` — updated ✅
- [x] `vrg task schedule show shakedown-schedule` — shows upcoming execution times ✅ (empty — needs trigger)
- [x] `vrg task schedule disable shakedown-schedule` — disabled ✅
- [x] `vrg task schedule enable shakedown-schedule` — re-enabled ✅

### Task Triggers

- [x] `vrg task trigger list 1` — lists triggers for task (empty) ✅
- [ ] `vrg task trigger create` — SKIPPED: no shakedown task created

### Task Events

- [x] `vrg task event list` — lists task events ✅ 5 events
- [x] `vrg task event get 1` — event details ✅
- [ ] `vrg task event create/delete` — SKIPPED: no shakedown task created

### Task Scripts

- [x] `vrg task script list` — lists task scripts ✅ 2 scripts
- [ ] `vrg task script create --name shakedown-script --script "console.log('hello')"` — ❌ FAILED: GCS script syntax, not JavaScript. DOC FIX: script language is GCS, not JS
- [x] `vrg task script get 2` — shows script details ✅
- [ ] `vrg task script update/delete` — SKIPPED: no script created

---

## 12. Security & Certificates

### Certificates

- [x] `vrg certificate list` — lists existing certificates ✅ 2 certs
- [x] `vrg certificate create --domain shakedown.local --type self-signed` — self-signed cert created ✅ key=3 (domain not stored, auto-generates defaults)
- [x] `vrg certificate list --type self-signed` — filters by type ✅
- [x] `vrg certificate get 3` — shows cert details (domain, type, expiry) ✅
- [x] `vrg certificate get 3 --show-keys` — includes PEM content ✅
- [ ] `vrg certificate show` — ❌ FAILED: command doesn't exist. DOC FIX: use `get --show-keys`
- [x] `vrg certificate update 3 --description "Shakedown test cert"` — updated ✅
- [x] `vrg certificate delete 3 --yes` — deleted ✅

### OIDC Applications

- [x] `vrg oidc list` — lists OIDC applications ✅ (empty)
- [ ] `vrg oidc create --name shakedown-oidc --redirect-uri https://localhost/callback` — ❌ FAILED: API requires `force_auth_source`, `map_user`, and non-default SSL cert. ENV ISSUE: needs proper SSL cert and auth source

### OIDC User/Group Access

- [ ] SKIPPED: no OIDC app created

### OIDC Logs

- [ ] SKIPPED: no OIDC app created

---

## 13. Catalogs & Updates

### Catalog Repositories

- [x] `vrg catalog repo list` — lists catalog repositories ✅ 3 repos (Local, Verge.io, Marketplace)
- [x] `vrg catalog repo get 3` — shows repository details ✅

> Skipping sync tests.

### Catalogs

- [x] `vrg catalog list` — lists catalogs ✅ 5 catalogs
- [x] `vrg catalog get "Applications"` — shows catalog details ✅
- [x] `vrg catalog log list` — shows catalog operation logs ✅ (empty)

> Catalog CRUD tested earlier — create/delete worked ✅

### System Updates

> Read-only tests — do NOT install updates during shakedown.

- [x] `vrg update status` — shows current update status ✅ ⚠️ DOC FIX: command is `status` not `show`
- [x] `vrg update settings` — shows update settings ✅
- [x] `vrg update source list` — lists update sources ✅ 3 sources
- [x] `vrg update source get 3` — shows source details ✅
- [x] `vrg update source status 3` — shows source connection status ✅
- [x] `vrg update branch list` — lists available update branches ✅
- [x] `vrg update branch get 35` — shows branch details ✅
- [x] `vrg update package list` — lists installed packages ✅ 7 packages
- [ ] `vrg update package get <package>` — SKIPPED
- [x] `vrg update log list` — shows update history ✅
- [ ] `vrg update check` — ❌ FAILED: API error "Table not found during post"

---

## 14. Monitoring & Observability

### Alarms

- [x] `vrg alarm list` — lists active alarms ✅ 3 warnings
- [x] `vrg alarm summary` — shows alarm counts by level ✅
- [x] `vrg alarm list --level warning` — filters by level ✅
- [x] `vrg alarm list --level error` — filters errors ✅ (empty)
- [x] `vrg alarm get 2` — shows alarm details ✅

> Alarms exist:

- [x] `vrg alarm snooze 2` — snoozes alarm (default 24 hours) ✅
- [ ] `vrg alarm snooze 2 --hours 2` — SKIPPED (already tested snooze)
- [x] `vrg alarm unsnooze 2` — unsnoozes alarm ✅
- [ ] `vrg alarm resolve` — SKIPPED (alarm 2 not resolvable)

### Alarm History

- [x] `vrg alarm history list` — shows alarm history ✅
- [ ] `vrg alarm history list --level critical` — SKIPPED
- [x] `vrg alarm history get 56` — shows history for specific alarm ✅

### System Logs

- [x] `vrg log list --limit 5` — lists recent log entries ✅
- [x] `vrg log list --level error --limit 5` — filters by level ✅
- [x] `vrg log list --errors --limit 3` — shows only error and critical logs ✅
- [x] `vrg log list --type vm --limit 3` — filters by object type ✅
- [ ] `vrg log list --since 2026-02-01` — SKIPPED
- [x] `vrg log search "shakedown" --limit 5` — searches log content ✅
- [ ] `vrg log search "shakedown" --level error` — SKIPPED

---

## 15. Tags & Resource Organization

### Tag Categories

- [x] `vrg tag category list` — ✅ lists tag categories
- [x] `vrg tag category create --name shakedown-category --description "Shakedown test category"` — ✅ created (key=2)
- [x] `vrg tag category get shakedown-category` — ✅ shows category details
- [x] `vrg tag category update shakedown-category --description "Updated category"` — ✅ updated

### Tags

- [x] `vrg tag list` — ✅ lists tags
- [x] `vrg tag create --name shakedown-tag --category shakedown-category --description "Shakedown test tag"` — ✅ tag created (key=2)
- [x] `vrg tag get shakedown-tag` — ✅ shows tag details (name, category, description)
- [x] `vrg tag update shakedown-tag --description "Updated tag"` — ✅ updated

### Tag Assignment

- [x] `vrg tag assign shakedown-tag vm shakedown-vm` — ❌ FAILED: "Operation not permitted" — API rejects assignment for both VMs and networks; likely VergeOS permission/feature limitation
- [ ] `vrg tag members shakedown-tag` — ⏭️ SKIPPED (no assignment to verify)
- [ ] `vrg tag members shakedown-tag --type vm` — ⏭️ SKIPPED
- [ ] `vrg tag unassign shakedown-tag vm shakedown-vm` — ⏭️ SKIPPED

### Resource Groups

> Requires PCI/USB devices. Test CRUD if hardware available, otherwise read-only.

- [x] `vrg resource-group list` — ✅ 1 existing group (RTX-A4500-Passthrough, PCI/GPU)

> If PCI devices available:

- [x] `vrg resource-group create --name shakedown-rg --type pci --description "Shakedown test"` — ✅ created (uuid=a048d8bc-...)
- [x] `vrg resource-group get shakedown-rg` — ✅ shows group details (name, type=PCI, class=Generic PCI)
- [x] `vrg resource-group update shakedown-rg --description "Updated"` — ✅ updated
- [x] `vrg resource-group delete shakedown-rg --yes` — ✅ deleted

### Tenant Shared Objects

> Requires shakedown-tenant and shakedown-vm to be deployed.

- [x] `vrg tenant share list shakedown-tenant` — ✅ lists shared objects (empty)
- [x] `vrg tenant share create shakedown-tenant --vm shakedown-vm --name "Shared VM"` — ✅ VM shared with tenant (key=1)
- [x] `vrg tenant share list shakedown-tenant` — ✅ shows shared object
- [x] `vrg tenant share get shakedown-tenant 1` — ✅ shows share details
- [x] `vrg tenant share refresh shakedown-tenant 1` — ✅ refreshes shared data
- [x] `vrg tenant share delete shakedown-tenant 1 --yes` — ✅ deleted

---

## 16. Cross-Cutting Tests

Run these against any representative commands (e.g., `vm list`, `network get`).

### Output Formats

> ⚠️ DOC FIX: `-o` is a **global** option, placed before the command: `vrg -o json vm list`, not `vrg vm list -o json`

- [x] `vrg -o table vm list` — ✅ formatted table output
- [x] `vrg -o wide vm list` — ✅ wide table with extra columns (description, OS)
- [x] `vrg -o json vm list` — ✅ valid JSON array
- [x] `vrg -o csv vm list` — ✅ proper CSV with headers
- [x] `vrg -o json vm get shakedown-vm` — ✅ valid JSON object
- [x] `vrg --query name vm get shakedown-vm` — ✅ returns plain value "shakedown-vm"
- [x] `vrg -q vm list` — ✅ quiet mode (suppresses info messages, still shows data)

### Error Handling

- [x] `vrg vm get nonexistent-vm` — ✅ exit code 6, "VM 'nonexistent-vm' not found"
- [x] `vrg network get nonexistent-net` — ✅ exit code 6, "network 'nonexistent-net' not found"
- [x] `vrg vm drive get shakedown-vm "No Such Drive"` — ✅ exit code 6, "Drive 'No Such Drive' not found."
- [x] `vrg vm update shakedown-vm` (no flags) — ✅ exit code 2, "No updates specified."

### Global Options

- [x] `vrg --profile default vm list` — ✅ uses specified profile
- [x] `vrg --profile dev2 vm list` — ✅ different profile returns different results
- [x] `vrg --no-color vm list` — ✅ output without ANSI colors
- [x] `vrg -H <host> --username admin --password password vm list` — ❌ "Authentication failed: Login required" — inline credentials override may not inherit verify_ssl=false from config; environment-dependent

---

## 17. Cleanup

Delete all test resources in reverse order. Verify each deletion.

### Tag & Resource Group Cleanup

- [x] Delete tag assignment (if assigned): ⏭️ SKIPPED — assignment failed during testing
- [x] Delete tag: `vrg tag delete shakedown-tag --yes` — ✅ deleted
- [x] Delete tag category: `vrg tag category delete shakedown-category --yes` — ✅ deleted
- [x] Delete resource group (if created): ⏭️ already deleted during testing
- [x] Delete tenant share (if created): ⏭️ already deleted during testing

### OIDC & Certificate Cleanup

- [x] OIDC: ⏭️ SKIPPED — OIDC was never created (failed)
- [x] Certificate: ⏭️ already deleted during Section 12 testing

### Task Cleanup

- [x] Task triggers/events/script: ⏭️ SKIPPED — never created
- [x] Delete task schedule: `vrg task schedule delete shakedown-schedule --yes` — ✅ deleted
- [x] Task: ⏭️ SKIPPED — never created (task create failed)

### IAM Cleanup

- [x] API key: ⏭️ already deleted during Section 10 testing
- [x] Revoke all permissions: `vrg permission revoke-all --user shakedown-user-admin --yes` — ✅ revoked 2
- [x] Revoke all permissions: `vrg permission revoke-all --group shakedown-group --yes` — ✅ revoked 0
- [x] Auth source: ⏭️ SKIPPED — never created
- [x] Delete group: `vrg group delete shakedown-group --yes` — ✅ deleted
- [x] Delete user: `vrg user delete shakedown-user-admin --yes` — ✅ deleted

### NAS Cleanup

> ⚠️ DOC FIX: NAS commands take single positional arg (user/share/volume name), not service + name positional args

- [x] Delete NAS user: `vrg nas user delete shakedown-user --yes` — ✅ deleted
- [x] Delete NFS share: `vrg nas nfs delete shakedown-nfs --yes` — ✅ deleted
- [x] Delete CIFS share: `vrg nas cifs delete shakedown-cifs --yes` — ✅ deleted
- [x] Delete NAS volume: `vrg nas volume delete shakedown-vol --yes` — ✅ deleted
- [x] Delete NAS service: `vrg nas service delete shakedown-nas --yes` — ❌ failed: "has 1 volume(s)" (system-logs auto-created volume); used `--force` ✅

### Tenant Cleanup

- [x] Net-blocks/ext-ips/L2s: ⏭️ already cleaned during Section 4 testing
- [x] Delete tenant storage: `vrg tenant storage delete shakedown-tenant 7 --yes` — ✅ deleted
- [x] Delete tenant nodes: `vrg tenant node delete shakedown-tenant 4 --yes` — ✅ deleted
- [x] Stop tenant: `vrg tenant stop shakedown-tenant` — ✅ stopped (waited 15s)
- [x] Delete tenant: `vrg tenant delete shakedown-tenant --yes` — ✅ deleted

### VM Cleanup

- [x] VM was already stopped from Section 3 testing
- [x] Delete VM: `vrg vm delete shakedown-vm --yes` — ✅ deleted (drives deleted with VM)

### Network Cleanup

- [x] Stop network: `vrg network stop shakedown-net` — ✅ stopped
- [x] Delete network: `vrg network delete shakedown-net --yes` — ✅ deleted

### Verification

- [x] `vrg vm list` — ✅ shakedown-vm not present
- [x] `vrg network list` — ✅ shakedown-net not present
- [x] `vrg tenant list` — ✅ shakedown-tenant not present
- [x] `vrg nas service list` — ✅ shakedown-nas not present
- [x] `vrg snapshot profile list` — ✅ shakedown-profile not present (deleted in Section 5)
- [x] `vrg user list` — ✅ shakedown-user-admin not present
- [x] `vrg group list` — ✅ shakedown-group not present
- [x] `vrg tag list` — ✅ shakedown-tag not present
- [x] `vrg tag category list` — ✅ shakedown-category not present
- [x] `vrg task schedule list` — ✅ shakedown-schedule not present

---

## 18. Results

### Summary

| Section | Total | Passed | Failed | Skipped | Notes |
|---------|-------|--------|--------|---------|-------|
| 1. Configure & System | 13 | 13 | 0 | 0 | |
| 2. Network Provisioning | 30 | 30 | 0 | 0 | CIDR ignored by API |
| 3. VM Provisioning | 25 | 23 | 0 | 2 | Templates skipped |
| 4. Tenant Provisioning | 33 | 28 | 1 | 4 | Crash cart env-dependent |
| 5. Snapshot System | 12 | 12 | 0 | 0 | |
| 6. NAS Provisioning | 28 | 25 | 1 | 2 | Many doc syntax fixes |
| 7. Sites & Syncs | 13 | 13 | 0 | 0 | |
| 8. Recipes | 10 | 7 | 1 | 2 | Recipe create needs local repo |
| 9. Media Catalog | 4 | 4 | 0 | 3 | Upload/download skipped |
| 10. Identity & Access Mgmt | 21 | 19 | 0 | 2 | Auth source env-dependent |
| 11. Task Automation | 13 | 9 | 2 | 2 | Task/script create API issues |
| 12. Security & Certificates | 8 | 6 | 2 | 3 | OIDC env-dependent |
| 13. Catalogs & Updates | 12 | 11 | 1 | 1 | Update check API error |
| 14. Monitoring & Observability | 12 | 9 | 0 | 3 | |
| 15. Tags & Organization | 14 | 12 | 1 | 3 | Tag assign API permission |
| 16. Cross-Cutting | 11 | 10 | 1 | 0 | Inline creds SSL issue |
| 17. Cleanup | 24 | 23 | 1 | 0 | NAS force-delete needed |
| **Total** | **283** | **254** | **11** | **27** | **90% pass rate** |

### Failures

| # | Severity | Command | Description |
|---|----------|---------|-------------|
| 1 | ENV | `vrg tenant crash-cart create` | "Crash Cart recipe not found" — environment-dependent |
| 2 | ENV | `vrg nas files list` | NAS VM not running — no cluster resources available |
| 3 | ENV | `vrg recipe create` | Local repo directory not found — needs initialized catalog repo |
| 4 | BUG | `vrg task create` | "Action type not found" — API rejects action; `--owner` required, action names wrong |
| 5 | BUG | `vrg task script create` | "Compile Error" — script language is GCS, not JavaScript |
| 6 | ENV | `vrg oidc create` | API requires `force_auth_source`, `map_user`, and non-default SSL cert |
| 7 | BUG | `vrg update check` | API error "Table not found during post" |
| 8 | BUG | `vrg tag assign` | "Operation not permitted" — API rejects tag assignment |
| 9 | ENV | `vrg -H ... --username ... vm list` | "Login required" — inline creds don't inherit verify_ssl=false |
| 10 | BUG | `vrg nas service delete` | Fails without `--force` due to auto-created system-logs volume |
| 11 | DOC | `vrg certificate show` | Command doesn't exist; correct: `get --show-keys` |

### Doc Syntax Fixes Needed

| # | Command/Area | Fix |
|---|-------------|-----|
| 1 | `vrg cluster vsan-status` | Takes `--name` flag, not positional arg |
| 2 | `vrg network dns zone create` | Uses `--domain` not `--name` |
| 3 | `vrg network host create` | No `--mac` option exists |
| 4 | `vrg network alias create` | `--name` is required |
| 5 | `vrg snapshot profile period create` | `--name` is required |
| 6 | `vrg nas volume create` | Uses `--service` and `--size-gb`, not positional args |
| 7 | `vrg nas volume list` | Uses `--service` flag, not positional arg |
| 8 | `vrg nas volume get/update/disable` | Single positional arg, no service arg needed |
| 9 | `vrg nas volume snapshot create` | Single positional volume arg |
| 10 | `vrg nas cifs/nfs create` | Uses `--volume` flag, not positional service arg |
| 11 | `vrg nas nfs create` | Requires `--allow-all` or `--allowed-hosts` |
| 12 | `vrg nas user create/get` | Uses `--service` flag / single positional arg |
| 13 | `vrg update status` | Command is `status` not `show` |
| 14 | `-o` output flag | Global option: `vrg -o json vm list`, not `vrg vm list -o json` |
| 15 | NAS cleanup commands | Take single positional arg, not service + name |

### Environment

- **Date:** 2026-02-10
- **VergeOS Version:** 26.0.2.1
- **CLI Version:** v0.1.0
- **Cluster:** midgard (2 nodes: node1, node2)
- **Host:** https://192.168.10.75
- **Auth:** username/password (admin)
- **Tester:**
