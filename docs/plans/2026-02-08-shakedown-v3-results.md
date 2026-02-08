# CLI Shakedown Test v3 — Phase 3 & 4 Commands

**Date:** 2026-02-08
**Environment:** VergeOS 26.0.2.1 (midgard)
**Scope:** Phase 3 (Data Protection) and Phase 4 (Storage & NAS) commands
**Previous Shakedown:** v2 — 56/61 passed

**Tests Passed:** 82/84
**Tests Failed:** 1
**Tests Partial:** 1

---

## Test Resources Created & Cleaned Up

| Resource | Name | Details |
|----------|------|---------|
| VM Snapshot | shakedown-snap (key: 63) | On VM 30 (test), retention 86400s |
| Cloud Snapshot | shakedown-cloud-snap (key: 4) | Default retention |
| NAS Volume Snapshot | shakedown-vol-snap (key: 1) | On test-volumes, 3-day retention |
| Snapshot Profile | shakedown-profile (key: 6) | With 1 period |
| Snapshot Profile Period | shakedown-period (key: 14) | Hourly, 3600s retention |
| NAS User | shakedown-user | On service test23 |

All test resources successfully deleted. No orphaned resources remain.

---

## Phase 1: Cloud Snapshots

| Command | Status | Notes |
|---------|--------|-------|
| `snapshot list` | PASS | 7 snapshots visible |
| `snapshot get` | PASS | Returns all fields (key, name, status, created, expires, immutable, private) |
| `snapshot create` | PASS | Created shakedown-cloud-snap |
| `snapshot delete` | PASS | Deleted cleanly with --yes |
| `snapshot vms` | PASS | Returns empty (no VMs in this snapshot) |
| `snapshot tenants` | PASS | Returns empty |

---

## Phase 2: Snapshot Profiles & Periods

| Command | Status | Notes |
|---------|--------|-------|
| `snapshot profile list` | PASS | 5 profiles visible |
| `snapshot profile get` | PASS | Returns name, description |
| `snapshot profile create` | PASS | Created shakedown-profile |
| `snapshot profile update` | PASS | Updated description |
| `snapshot profile delete` | PASS | Deleted cleanly |
| `snapshot profile period list` | PASS | Shows frequency, retention, min_snaps, max_tier |
| `snapshot profile period get` | PASS | Full period details |
| `snapshot profile period create` | PASS | Created hourly period |
| `snapshot profile period update` | PASS | Updated retention from 3600 to 7200 |
| `snapshot profile period delete` | PASS | Deleted cleanly |

---

## Phase 3: VM Snapshots

| Command | Status | Notes |
|---------|--------|-------|
| `vm snapshot list` | PASS | Lists all snapshots for VM 30 |
| `vm snapshot get` | PASS | Returns key, name, created, expires, quiesced |
| `vm snapshot create` | PASS | Created shakedown-snap on running VM |
| `vm snapshot delete` | PASS | Deleted cleanly |
| `vm snapshot restore` | N/T | Not tested (would disrupt running VM) |

---

## Phase 4: Sites

| Command | Status | Notes |
|---------|--------|-------|
| `site list` | PASS | 2 sites visible |
| `site get` | PASS | All fields (url, status, enabled, auth_status, city, country) |
| `site update` | PASS | Updated description, verified, reverted |
| `site disable` | PASS | |
| `site enable` | PASS | |
| `site create` | N/T | Would require additional remote site |
| `site delete` | N/T | Would remove production site |
| `site reauth` | N/T | Would require credentials |
| `site refresh` | N/T | Would trigger network traffic |

---

## Phase 5: Site Syncs

| Command | Status | Notes |
|---------|--------|-------|
| `site sync outgoing list` | PASS | 2 outgoing syncs |
| `site sync outgoing get` | PASS | Full sync details (encryption, compression, threads) |
| `site sync outgoing disable` | PASS | |
| `site sync outgoing enable` | PASS | |
| `site sync incoming list` | PASS | 1 incoming sync |
| `site sync incoming get` | PASS | Full sync details |
| `site sync incoming disable` | PASS | |
| `site sync incoming enable` | PASS | |

---

## Phase 6: NAS Services

| Command | Status | Notes |
|---------|--------|-------|
| `nas service list` | PASS | 2 services visible |
| `nas service get` | PASS | Returns vm_running, volume_count, max_imports, max_syncs |
| `nas service update` | PASS | Updated max_imports 4→6, verified, reverted |
| `nas service cifs-settings` | PASS | Shows workgroup, server_type, protocol, ad_status |
| `nas service nfs-settings` | PASS | Shows enable_nfsv4, squash, data_access |
| `nas service create` | N/T | Would create new NAS service VM |
| `nas service delete` | N/T | Would remove existing service |
| `nas service power-on` | N/T | Service already running |
| `nas service power-off` | N/T | Would disrupt running service |
| `nas service restart` | N/T | Would disrupt running service |
| `nas service set-cifs-settings` | N/T | Would change production settings |
| `nas service set-nfs-settings` | N/T | Would change production settings |

---

## Phase 7: NAS Volumes

| Command | Status | Notes |
|---------|--------|-------|
| `nas volume list` | PASS | 4 volumes visible |
| `nas volume get` | PASS | Returns size_gb, used_gb, fs_type, preferred_tier |
| `nas volume update` | PASS | Updated description, verified, reverted |
| `nas volume disable` | PASS | |
| `nas volume enable` | PASS | |
| `nas volume create` | N/T | Would allocate storage |
| `nas volume delete` | N/T | Would destroy data |
| `nas volume reset` | N/T | Would disrupt volume |
| `nas volume snapshot list` | PASS | Empty (expected after cleanup) |
| `nas volume snapshot get` | PASS | Verified during create/get/delete cycle |
| `nas volume snapshot create` | PASS | Created shakedown-vol-snap |
| `nas volume snapshot delete` | PASS | Deleted cleanly |

---

## Phase 8: NAS Shares

### CIFS Shares

| Command | Status | Notes |
|---------|--------|-------|
| `nas cifs list` | PASS | 1 share visible |
| `nas cifs get` | PASS | Returns volume_name, browseable, read_only, guest_ok |
| `nas cifs update` | PASS | Updated description, verified, reverted |
| `nas cifs disable` | PASS | |
| `nas cifs enable` | PASS | |
| `nas cifs create` | N/T | Would need volume setup |
| `nas cifs delete` | N/T | Would remove share |

### NFS Shares

| Command | Status | Notes |
|---------|--------|-------|
| `nas nfs list` | PASS | 1 share visible |
| `nas nfs get` | PASS | Returns volume_name, data_access, squash |
| `nas nfs update` | PASS | Updated description, verified, reverted |
| `nas nfs disable` | PASS | |
| `nas nfs enable` | PASS | |
| `nas nfs create` | N/T | Would need volume setup |
| `nas nfs delete` | N/T | Would remove share |

---

## Phase 9: NAS Users

| Command | Status | Notes |
|---------|--------|-------|
| `nas user list` | PASS | Empty initially (expected) |
| `nas user create` | PASS | Created shakedown-user |
| `nas user get` | PASS | Returns name, enabled, service_name |
| `nas user update` | PASS | Updated description |
| `nas user disable` | PASS | |
| `nas user enable` | PASS | |
| `nas user delete` | PASS | Deleted cleanly |

---

## Phase 10: NAS Sync Jobs

| Command | Status | Notes |
|---------|--------|-------|
| `nas sync list` | PASS | Empty (no sync jobs configured) |
| `nas sync create` | N/T | Would require remote NAS target |
| `nas sync get/update/delete/enable/disable/start/stop` | N/T | No sync jobs to test |

---

## Phase 11: NAS Files

| Command | Status | Notes |
|---------|--------|-------|
| `nas files list` | PASS | Shows .snapshots and lost+found on test-cifs |
| `nas files list -p <path>` | PASS | Lists subdirectory contents |
| `nas files get` | PASS | Returns name, type, size, size_display, modified |

---

## Phase 12: Media Catalog Files

| Command | Status | Notes |
|---------|--------|-------|
| `file list` | PASS | 92 files visible |
| `file get` | PASS | Returns name, type, size_gb, tier, creator, modified |
| `file types` | PASS | 16 supported types (iso, qcow2, raw, ova, etc.) |
| `file update` | N/T | Would modify production files |
| `file upload` | N/T | Would require local file |
| `file download` | N/T | Would download large files |
| `file delete` | N/T | Would destroy production data |

---

## Phase 13: VM Recipes

| Command | Status | Notes |
|---------|--------|-------|
| `recipe list` | PASS | 32 recipes visible |
| `recipe get` | PASS | Returns name, description, enabled |
| `recipe create` | FAIL | Missing `--version` option — API requires `vm_recipes.version` field. See Issue #12 |
| `recipe update` | PARTIAL | CLI works but existing recipes are from remote catalog → "Changes are not allowed on non-local repositories". Would work on locally-created recipes. |
| `recipe delete` | N/T | No locally-created recipes to test |
| `recipe deploy` | N/T | Would create VM resources |
| `recipe instance list` | PASS | 8 instances visible |
| `recipe instance get` | PASS | Returns name, recipe_name, auto_update |
| `recipe instance delete` | N/T | Would remove instance tracking |
| `recipe log list` | PASS | 18 log entries visible |
| `recipe log get` | PASS | Returns level, text, timestamp, user |
| `recipe section list` | PASS | Shows sections with name, description, orderid |
| `recipe section get` | PASS | Full section details |
| `recipe section create` | N/T | Existing recipes are read-only (remote catalog) |
| `recipe section update` | N/T | Read-only (remote catalog) |
| `recipe section delete` | N/T | Read-only (remote catalog) |
| `recipe question list` | PASS | Shows all questions with type, label, required |
| `recipe question get` | PASS | Full question details (name, display, type, default, hint) |
| `recipe question create` | N/T | Existing recipes are read-only (remote catalog) |
| `recipe question update` | N/T | Read-only (remote catalog) |
| `recipe question delete` | N/T | Read-only (remote catalog) |

---

## Phase 14: Output Formats

| Format | Commands Tested | Status |
|--------|----------------|--------|
| Table | All list/get commands | PASS |
| Wide | snapshot, site, nas service, file | PASS |
| JSON | snapshot, site, nas service, recipe, file, nas volume | PASS (all valid JSON) |
| CSV | snapshot, site, nas service, recipe | PASS (proper headers and data) |
| `--query` | snapshot, site, nas volume, file, recipe | PASS (returns plain values) |

---

## Phase 15: Error Handling

| Test | Status | Exit Code | Notes |
|------|--------|-----------|-------|
| `vm snapshot get` non-existent | PASS | 6 | Clear error message |
| `nas volume get` non-existent | PASS | 6 | Clear error message |
| `recipe get` non-existent | PASS | 6 | Clear error message |
| `site get` non-existent | PASS | 6 | Clear error message |
| `snapshot get` non-existent | PASS | 6 | Clear error message |

---

## New Issues Found

### Issue #12: `recipe create` missing `--version` option

**Severity:** Medium
**Command:** `vrg recipe create --name "test" --catalog "New VM"`
**Error:** `field 'vm_recipes.version' is required`
**Fix:** Add `--version` option to `recipe create` command. The API requires a version string.

---

## Summary

### Results by Category

| Category | Tested | Passed | Failed | Partial | N/T |
|----------|--------|--------|--------|---------|-----|
| Cloud Snapshots | 6 | 6 | 0 | 0 | 0 |
| Snapshot Profiles/Periods | 10 | 10 | 0 | 0 | 0 |
| VM Snapshots | 4+1 N/T | 4 | 0 | 0 | 1 |
| Sites | 5+4 N/T | 5 | 0 | 0 | 4 |
| Site Syncs | 8 | 8 | 0 | 0 | 0 |
| NAS Services | 5+7 N/T | 5 | 0 | 0 | 7 |
| NAS Volumes | 8+3 N/T | 8 | 0 | 0 | 3 |
| NAS Shares (CIFS) | 5+2 N/T | 5 | 0 | 0 | 2 |
| NAS Shares (NFS) | 5+2 N/T | 5 | 0 | 0 | 2 |
| NAS Users | 7 | 7 | 0 | 0 | 0 |
| NAS Sync | 1+7 N/T | 1 | 0 | 0 | 7 |
| NAS Files | 3 | 3 | 0 | 0 | 0 |
| Media Catalog Files | 3+4 N/T | 3 | 0 | 0 | 4 |
| VM Recipes | 7+10 N/T | 5 | 1 | 1 | 10 |
| Output Formats | 6 | 6 | 0 | 0 | 0 |
| Error Handling | 5 | 5 | 0 | 0 | 0 |
| **Total** | **84 tested** | **82** | **1** | **1** | **40** |

### Notes on N/T (Not Tested)
Commands marked N/T were skipped because:
- They would create/destroy production resources (NAS volumes, services, files)
- They would disrupt running services (power-off, restart)
- They require external setup (site create, NAS sync, file upload)
- Existing recipes are from a remote catalog (read-only for section/question CRUD)

### Issues
| # | Issue | Severity | Notes |
|---|-------|----------|-------|
| 12 | `recipe create` missing `--version` option | Medium | API requires `vm_recipes.version` field but CLI doesn't expose it |

### Test Environment Cleanup

All test resources successfully deleted:
- VM Snapshot: shakedown-snap (key: 63)
- Cloud Snapshot: shakedown-cloud-snap (key: 4)
- NAS Volume Snapshot: shakedown-vol-snap (key: 1)
- Snapshot Profile: shakedown-profile (key: 6) with period (key: 14)
- NAS User: shakedown-user

No orphaned resources remain.
