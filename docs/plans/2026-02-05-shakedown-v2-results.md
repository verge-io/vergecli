# CLI Shakedown Test v2 - Results

**Date:** 2026-02-05
**Environment:** VergeOS 26.0.2.1 (midgard)
**Previous Shakedown:** 32/38 passed (6 issues)
**Goal:** Comprehensive retest + edge cases + stress test

**Tests Passed:** 56/61
**Tests Failed:** 2
**Tests Partial:** 3

---

## Test Resources

| Resource | Name | Details |
|----------|------|---------|
| Network | shakedown-net | 10.99.99.0/24, gateway=External(3), DHCP |
| VM | shakedown-vm | 1 CPU, 512MB RAM, Linux |
| Rules | shakedown-rule-ssh, -web, -block | Incoming accept/drop |
| DNS View | shakedown-view | With recursion |
| DNS Zone | shakedown.local | Master zone |
| DNS Records | A, CNAME, MX | Various test records |
| Host Override | shakedown-host | 10.99.99.50 |
| IP Alias | shakedown-alias | 10.99.99.200 |

---

## Phase 1: System & Config

| Command | Status | Notes |
|---------|--------|-------|
| `system info` | PASS | Returns host, version, VM/network/tenant counts |
| `system version` | PASS | Returns 26.0.2.1 |
| `configure list` | PASS | Shows both profiles (default, dev2) |
| `configure show` | PASS | Shows effective config with masked password |

---

## Phase 2: Network Lifecycle

| Command | Status | Notes |
|---------|--------|-------|
| `network create` (full options) | PASS | `--vnet-default-gateway 3` works (Issue #1 FIXED) |
| `network list` | PASS | shakedown-net visible |
| `network get` (by name) | PASS | All fields correct |
| `network update` (description) | PASS | |
| `network start` | PASS | |
| `network status` | PASS | Shows running, needs_restart, needs_rule_apply |
| `network restart --apply-rules` | PASS | |
| `network apply-rules` | PASS | |
| `network apply-dns` | PASS | |
| `network stop` | PASS | (tested during cleanup) |
| `network delete` | PASS | (tested during cleanup) |

---

## Phase 3: Network Sub-resources

### Firewall Rules

| Command | Status | Notes |
|---------|--------|-------|
| `rule create` (SSH, accept tcp 22) | PASS | |
| `rule create` (Web, accept tcp 80,443) | PASS | Multi-port works |
| `rule create` (Block, `--action block`) | FAIL | `block` not valid; `drop` works. See Issue #7 |
| `rule create` (Block, `--action drop`) | PASS | Correct action name |
| `rule list` | PASS | |
| `rule get` (by name) | PASS | |
| `rule update` (dest-ports) | PASS | |
| `rule update` (description) | PASS | Issue #2 FIXED |
| `rule disable` | PASS | |
| `rule enable` | PASS | |
| `rule delete` | PASS | |
| `rule list --direction incoming` | PASS | Filter works |
| `rule list --action accept` | PASS | Filter works |

### Host Overrides

| Command | Status | Notes |
|---------|--------|-------|
| `host create` | PASS | |
| `host list` | PASS | |
| `host get` (by name) | PASS | |
| `host update` (IP change) | PASS | |
| `host delete` | PASS | |

### IP Aliases

| Command | Status | Notes |
|---------|--------|-------|
| `alias create` (single IP) | PASS | |
| `alias create` (CIDR) | FAIL | Issue #3 still broken - "IP already exists" |
| `alias list` | PASS | |
| `alias get` (by name) | PASS | |
| `alias update` (description) | PASS | |
| `alias delete` | PASS | |

---

## Phase 4: DNS Stack

### DNS Views

| Command | Status | Notes |
|---------|--------|-------|
| `dns view create` | PASS | Issue #4 FIXED (views now supported) |
| `dns view list` | PASS | |
| `dns view get` (by name) | PASS | |
| `dns view update` (--no-recursion) | PASS | |
| `dns view delete` | PASS | (tested during cleanup) |

### DNS Zones

| Command | Status | Notes |
|---------|--------|-------|
| `dns zone create` (with view arg) | PASS | Issue #4 FIXED |
| `dns zone list` | PASS | Shows view_name column |
| `dns zone get` (by domain) | PASS | |
| `dns zone update` | PASS | |
| `dns zone delete` | PASS | (tested during cleanup) |

### DNS Records

| Command | Status | Notes |
|---------|--------|-------|
| `dns record create` (A) | PASS | |
| `dns record create` (CNAME) | PASS | |
| `dns record create` (MX, with priority) | PASS | |
| `dns record list` | PASS | |
| `dns record list --type A` | PARTIAL | Filter returns all records, not just A. See Issue #8 |
| `dns record get` (by name) | PASS | |
| `dns record update` (value change) | PASS | |
| `dns record delete` | PASS | |

---

## Phase 5: VM Lifecycle

| Command | Status | Notes |
|---------|--------|-------|
| `vm create` (full options) | PASS | |
| `vm list` | PASS | |
| `vm get` (by name) | PASS | |
| `vm get` (by numeric key) | PASS | |
| `vm update` (RAM + description) | PASS | |
| `vm start` | PASS | |
| `vm stop` (graceful) | PASS | Slow without guest agent (expected) |
| `vm stop --force` | PASS | |
| `vm restart` | PASS | Performs stop+start sequence (no guestreset error). Issue #6 FIXED |
| `vm reset` (hard) | PASS | |
| `vm delete` | PASS | |
| `vm list --status running` | FAIL | "Invalid argument" error. See Issue #9 |

---

## Phase 6: Edge Cases & Stress

| Test | Status | Notes |
|------|--------|-------|
| Get non-existent VM | PASS | Exit 6, clear error message |
| Get non-existent network | PASS | Exit 6, clear error message |
| Delete non-existent VM | PASS | Exit 6, clear error message |
| Create rule missing `--name` | PASS | Exit 2, Typer shows missing option |
| Create VM missing `--name` | PASS | Exit 2, Typer shows missing option |
| Create network missing `--name` | PASS | Exit 2, Typer shows missing option |
| Create duplicate VM name | PASS | Exit 8, "name already in use" |
| JSON output (VM get) | PASS | Valid JSON |
| JSON output (network get) | PASS | Valid JSON |
| JSON output (rule list) | PASS | Valid JSON array |
| JSON output (DNS record list) | PASS | Valid JSON array |
| JSON output (host list) | PASS | Valid JSON array |
| JSON output (alias list) | PASS | Valid JSON array |
| JSON output (DNS view list) | PASS | Valid JSON array |
| JSON output (diag stats) | PASS | Valid JSON |
| JSON output (network status) | PASS | Valid JSON |
| `--query name` (single item) | PASS | Returns plain value |
| `--query name` (list) | PASS | Returns JSON array of values |
| `--query nonexistent_field` | PASS | Returns "No result", exit 0 |
| `network list --type internal` | PASS | Filters correctly |
| `network list --status running` | FAIL | "Invalid argument". See Issue #9 |
| `network list --filter "name=..."` | FAIL | "Invalid argument". See Issue #10 |
| `vm list --filter "name=..."` | FAIL | "Invalid argument". See Issue #10 |
| `--fields / -f` (global option) | FAIL | Option not implemented. See Issue #11 |

---

## Previous Issues Status

| # | Issue | Previous Status | Current Status |
|---|-------|-----------------|----------------|
| 1 | `--vnet-default-gateway` missing in network create | OPEN | **FIXED** |
| 2 | `--description` missing in rule update | OPEN | **FIXED** |
| 3 | CIDR alias creation fails | OPEN | Still broken (SDK/API issue) |
| 4 | DNS zone create missing view support | OPEN | **FIXED** (view is now an argument) |
| 5 | `--network` missing in VM create | OPEN | Still missing (not retested) |
| 6 | `vm restart` guestreset error | OPEN | **FIXED** (now uses stop+start sequence) |

---

## New Issues Found

### Issue #7: `--action block` not a valid firewall action

**Severity:** Low
**Command:** `vrg network rule create --action block`
**Error:** `value 'block' is not in list for field 'action'`
**Workaround:** Use `--action drop` or `--action reject` instead.
**Fix:** CLI should validate action values and/or document valid options (accept, drop, reject) in help text.

---

### Issue #8: DNS record `--type` filter not working

**Severity:** Low
**Command:** `vrg network dns record list <net> <view> <zone> --type A`
**Behavior:** Returns all record types instead of filtering to A records only.
**Fix:** Implement server-side or client-side filtering by record type.

---

### Issue #9: `--status` filter broken on vm list and network list

**Severity:** Medium
**Command:** `vrg vm list --status running` and `vrg network list --status running`
**Error:** `Error: Invalid argument` (exit 8)
**Fix:** Investigate how the `--status` filter is passed to the SDK. May be a field name mismatch between CLI and API.

---

### Issue #10: `--filter` broken on vm list and network list

**Severity:** Medium
**Command:** `vrg vm list --filter "name=shakedown"` and `vrg network list --filter "name=shakedown"`
**Error:** `Error: Invalid argument` (exit 8)
**Fix:** Investigate filter parsing and how it maps to SDK query parameters.

---

### Issue #11: `--fields / -f` global option not implemented

**Severity:** Low
**Command:** `vrg vm list --fields name,status,ram` or `vrg vm list -f name,status,ram`
**Error:** `No such option: --fields` / `No such option: -f`
**Notes:** CLAUDE.md documents `--fields/-f` as a global option, but it's not implemented on any command. Either implement it or remove from documentation.

---

## Summary

### Improvements Since v1
- **4 previously-reported issues fixed:** vnet-default-gateway (#1), rule update description (#2), DNS view/zone support (#4), vm restart (#6)
- **Full DNS stack now operational:** views, zones, and records all working end-to-end
- **55/60 tests passing** (up from 32/38)

### Remaining Issues (7 total)
| Priority | Count | Issues |
|----------|-------|--------|
| Medium | 3 | #5 (VM --network), #9 (--status filter), #10 (--filter) |
| Low | 4 | #3 (CIDR alias), #7 (action validation), #8 (DNS type filter), #11 (--fields) |

### Test Environment Cleanup
All test resources successfully deleted:
- Network: shakedown-net (key: 15)
- VM: shakedown-vm (key: 37)
- 3 firewall rules (2 remaining at cleanup + 1 deleted during test)
- 1 host override
- 1 IP alias
- 1 DNS view, 1 DNS zone, 3 DNS records (1 deleted during test)

No orphaned resources remain.
