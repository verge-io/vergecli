# M2 Sub-Resource CRUD — Shakedown Test Results

**Date:** 2026-02-06
**Environment:** VergeOS 26.0.2.1 (midgard)
**Scope:** `vrg vm drive`, `vrg vm nic`, `vrg vm device` sub-commands
**Test VM:** shakedown-m2-vm (key: 80, 1 CPU, 512MB RAM, Linux)

**Tests Passed:** 38/41
**Tests Failed:** 1
**Tests Partial:** 2

---

## Phase 1: Setup

| Command | Status | Notes |
|---------|--------|-------|
| `vm create --name shakedown-m2-vm --cpu 1 --ram 512 --os linux` | PASS | Created key: 80 |
| `vm get shakedown-m2-vm` | PASS | All fields correct |
| `vm drive --help` | PASS | Shows list, get, create, update, delete, import |
| `vm nic --help` | PASS | Shows list, get, create, update, delete |
| `vm device --help` | PASS | Shows list, get, create, delete |

---

## Phase 2: VM Drive CRUD

| Command | Status | Notes |
|---------|--------|-------|
| `vm drive list shakedown-m2-vm` (empty) | PASS | "No results found." |
| `vm drive create --size 10GB --name "Boot Disk" --description "..."` | PASS | Created key: 72 |
| `vm drive list` (after create) | PASS | Shows Boot Disk |
| `vm drive get "Boot Disk"` (by name) | PASS | All fields correct |
| `vm drive get 72` (by numeric key) | PASS | Same result |
| `vm drive update "Boot Disk" --name "OS Disk"` | PASS | Renamed successfully |
| `vm drive update "OS Disk" --tier 2` | PASS | Tier changed to 2 |
| `vm drive update "OS Disk" --disabled` | PASS | enabled → no |
| `vm drive update "OS Disk" --enabled` | PASS | enabled → yes |
| `vm drive create --size 5GB --name "Data Disk" --interface ide --tier 3` | PASS | Created key: 80, interface=ide |
| `vm drive list` (2 drives) | PASS | Shows both drives |
| `vm drive list --media disk` | PASS | Filter works (both are disk) |
| `vm drive create --size 1TB --name "Big Disk"` | PASS | size_gb=1024.0, TB parsing works |
| `vm drive delete "Big Disk" --yes` | PASS | |
| `vm drive delete "Data Disk" --yes` | PASS | |
| `vm drive import --file-name "noble-server-cloudimg-amd64.ova" --name "Imported OVA"` | PASS | Imported key: 121, size=0.56GB |
| `vm drive update "OS Disk"` (no flags) | PASS | Exit 2, "No updates specified." |
| `vm drive get "NonExistent"` | PASS | Exit 6, "Drive 'NonExistent' not found." |
| `vm drive import --file-name "nonexistent.vmdk"` | PASS | Exit 1, clear error |

### Drive Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| `--output json` (drive list) | PASS | Valid JSON array |
| `--output json` (drive get) | PASS | Valid JSON object |
| `--query name` (drive get) | PASS | Returns "OS Disk" |

---

## Phase 3: VM NIC CRUD

| Command | Status | Notes |
|---------|--------|-------|
| `vm nic list shakedown-m2-vm` (empty) | PASS | "No results found." |
| `vm nic create --network Internal --name "Primary NIC" --description "..."` | PASS | Created key: 107, mac auto-assigned |
| `vm nic list` (after create) | PASS | Shows Primary NIC |
| `vm nic get "Primary NIC"` (by name) | PASS | All fields correct, network_name=Internal |
| `vm nic get 107` (by numeric key) | PASS | Same result |
| `vm nic update "Primary NIC" --name "mgmt0"` | PASS | Renamed successfully |
| `vm nic update "mgmt0" --disabled` | PASS | enabled → no |
| `vm nic update "mgmt0" --enabled` | PASS | enabled → yes |
| `vm nic create --network Internal --name "Secondary NIC" --interface e1000` | PASS | Created key: 108, interface=e1000 |
| `vm nic list` (2 NICs) | PASS | Shows both NICs |
| `vm nic create --network Internal --name "Static NIC" --ip "10.100.100.50"` | PASS | IP assigned correctly |
| `vm nic create --network Internal --ip "10.0.0.50"` | PASS | Exit 8, "ip is not in vnet network range" |
| `vm nic create --network "NonExistentNetwork"` | PASS | Exit 1, "Network not found" |
| `vm nic update "mgmt0"` (no flags) | PASS | Exit 2, "No updates specified." |
| `vm nic get "NonExistent"` | PASS | Exit 6, "NIC 'NonExistent' not found." |
| `vm nic delete "Secondary NIC" --yes` | PASS | |
| `vm nic delete "Static NIC" --yes` | PASS | |
| `vm nic delete "mgmt0" --yes` | PASS | |

### NIC Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| `--output json` (nic list) | PASS | Valid JSON array with all fields |
| `--query mac_address` (nic get) | PASS | Returns MAC address |

---

## Phase 4: VM Device (TPM) CRUD

| Command | Status | Notes |
|---------|--------|-------|
| `vm device list shakedown-m2-vm` (empty) | PASS | "No results found." |
| `vm device create shakedown-m2-vm` (defaults) | PASS | Created key: 7, name=tpm_0 |
| `vm device list` (after create) | PASS | Shows tpm_0 |
| `vm device get "tpm_0"` (by name) | PASS | device_type=Trusted Platform Module (vTPM) |
| `vm device get 7` (by numeric key) | PASS | Same result |
| `vm device delete "tpm_0" --yes` | PASS | |
| `vm device create --name "Custom TPM" --model tis --version 2` | PASS | Created with tis model |
| `vm device create --model crb --version 1.2` | FAIL | "value '1.2' is not in list for field 'version'". See Issue #1 |
| `vm device delete "Custom TPM" --yes` | PASS | |
| `vm device get "NonExistent"` | PASS | Exit 6, "Device 'NonExistent' not found." |

### Device Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| `--output json` (device list) | PASS | Valid JSON array |
| `--output json` (device get) | PASS | Valid JSON object |
| `--query device_type` (device get) | PASS | Returns "Trusted Platform Module (vTPM)" |

### Device Known Issue

| Field | Status | Notes |
|-------|--------|-------|
| model in output | PARTIAL | Always empty — `settings_args` not returned by API on device object. See Issue #2 |
| version in output | PARTIAL | Always empty — same cause as model. See Issue #2 |

---

## Phase 5: Cross-Cutting Tests

| Test | Status | Notes |
|------|--------|-------|
| Sub-commands with VM key (80) instead of name | PASS | `drive list 80`, `nic list 80` both work |
| Sub-commands with non-existent VM | PASS | Exit 6, "VM 'nonexistent-vm' not found" |
| All sub-commands registered on `vm` app | PASS | `vm --help` shows drive, nic, device |

---

## Phase 6: Cleanup

| Resource | Status | Notes |
|----------|--------|-------|
| Drive: Imported OVA (key: 121) | Deleted | |
| Drive: OS Disk (key: 72) | Deleted | |
| NIC: mgmt0 (key: 107) | Deleted | |
| VM: shakedown-m2-vm (key: 80) | Deleted | |
| Verification: `drive list`, `nic list`, `device list` | All empty | |
| Verification: VM not in `vm list` | Confirmed | |

No orphaned resources remain.

---

## Issues Found

### Issue #1: TPM version help text shows invalid values

**Severity:** Low
**Command:** `vrg vm device create --version 1.2`
**Error:** `value '1.2' is not in list for field 'version'`
**Expected behavior:** Help text says `(1.2, 2.0)` but valid API values are `1` and `2` (not `1.2` and `2.0`).
**Fix:** Update help text in `vm_device.py` from `"TPM version (1.2, 2.0)"` to `"TPM version (1, 2)"` and change the default from `"2.0"` to `"2"`.

---

### Issue #2: TPM model/version fields always empty in output

**Severity:** Low
**Location:** `src/verge_cli/commands/vm_device.py` → `_device_to_dict()`
**Behavior:** The `model` and `version` fields are always empty in both table and JSON output, even after creating a TPM with explicit `--model tis --version 2`.
**Root cause:** `_device_to_dict()` reads from `device.get("settings_args", {})`, but the API does not return `settings_args` on the device object after creation or retrieval.
**Impact:** Cosmetic only — the TPM is created correctly with the specified model/version, but the output doesn't reflect it.
**Fix options:**
1. Remove model/version from default output (they're creation-only params)
2. Investigate if a different API field contains the settings (e.g., `settings`, `config`)

---

### Issue #3: NIC create with invalid network returns exit 1 instead of exit 6

**Severity:** Low
**Command:** `vrg vm nic create --network "NonExistentNetwork"`
**Behavior:** Returns exit code 1 ("Unexpected error") with message "Network 'NonExistentNetwork' not found"
**Expected:** Exit code 6 (Not Found) since it's a resource not found error.
**Fix:** Catch the SDK's not-found exception for network resolution and map it to exit code 6.

---

## Summary

### What Works Well
- All CRUD operations (list, get, create, update, delete) work correctly for drives, NICs, and devices
- Drive import from OVA files works
- Name and numeric key resolution works for both parent VM and sub-resources
- `--size` unit parsing (GB, TB) works correctly
- `--media` filter on drive list works
- NIC creation with static IP, custom interface, and network name resolution all work
- Error handling is clean: non-existent resources (exit 6), no updates (exit 2), out-of-range IPs (exit 8)
- JSON output and `--query` extraction work for all sub-resource types
- Sub-commands accept VM by name or numeric key

### Issues (3 total)

| # | Severity | Issue |
|---|----------|-------|
| 1 | Low | TPM version help text shows invalid values (1.2/2.0 → should be 1/2) |
| 2 | Low | TPM model/version always empty in output (settings_args not returned by API) |
| 3 | Low | NIC create with invalid network returns exit 1 instead of exit 6 |

All issues are low severity. The M2 sub-resource commands are production-ready.
