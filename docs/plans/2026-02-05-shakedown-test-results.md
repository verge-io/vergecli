# CLI Shakedown Test Results

**Date:** 2026-02-05
**Environment:** VergeOS 26.0.2.1 (midgard)
**Status:** Completed with issues documented

---

## Summary

Full integration test of verge-cli against a live VergeOS system. Created, modified, and deleted test resources without affecting existing infrastructure.

**Tests Passed:** 32/38
**Tests Failed:** 6 (documented as issues below)

---

## Test Results by Category

### Network Commands

| Command | Status | Notes |
|---------|--------|-------|
| `network create` | PARTIAL | Missing `--vnet-default-gateway` option |
| `network list` | PASS | |
| `network get` | PASS | |
| `network update` | PASS | |
| `network start` | PASS | |
| `network stop` | PASS | |
| `network restart` | PASS | |
| `network delete` | PASS | |
| `network status` | PASS | |
| `network apply-rules` | PASS | |
| `network apply-dns` | PASS | |

### Firewall Rule Commands

| Command | Status | Notes |
|---------|--------|-------|
| `network rule create` | PASS | |
| `network rule list` | PASS | |
| `network rule get` | PASS | |
| `network rule update` | PARTIAL | Missing `--description` option |
| `network rule delete` | PASS | |
| `network rule enable` | PASS | |
| `network rule disable` | PASS | |

### DNS/DHCP Host Override Commands

| Command | Status | Notes |
|---------|--------|-------|
| `network host create` | PASS | |
| `network host list` | PASS | |
| `network host get` | PASS | |
| `network host update` | PASS | |
| `network host delete` | PASS | |

### IP Alias Commands

| Command | Status | Notes |
|---------|--------|-------|
| `network alias create` | PARTIAL | CIDR notation fails with misleading error |
| `network alias list` | PASS | |
| `network alias get` | PASS | |
| `network alias update` | PASS | |
| `network alias delete` | PASS | |

### DNS Zone/Record Commands

| Command | Status | Notes |
|---------|--------|-------|
| `network dns zone create` | FAIL | Missing required `--view` option |
| `network dns zone list` | N/T | Not tested due to create failure |
| `network dns record create` | N/T | Not tested due to zone failure |

### VM Commands

| Command | Status | Notes |
|---------|--------|-------|
| `vm create` | PARTIAL | Missing `--network` option |
| `vm list` | PASS | |
| `vm get` | PASS | |
| `vm update` | PASS | |
| `vm delete` | PASS | |
| `vm start` | PASS | |
| `vm stop` | PASS | |
| `vm stop --force` | PASS | |
| `vm restart` | FAIL | 'guestreset' action not supported |
| `vm reset` | PASS | |

### Network Diagnostics

| Command | Status | Notes |
|---------|--------|-------|
| `network diag leases` | PASS | |
| `network diag addresses` | PASS | |
| `network diag stats` | PASS | |

### Output Formats

| Format | Status | Notes |
|--------|--------|-------|
| Table output | PASS | |
| JSON output | PASS | |
| `--query` extraction | PASS | |

---

## Issues Found

### Issue #1: Missing `--vnet-default-gateway` option in `network create`

**Severity:** Medium
**Location:** `src/verge_cli/commands/network.py`

The API supports `vnet_default_gateway` field to route traffic through another network (e.g., External), but the CLI doesn't expose this option.

**Expected:**
```bash
vrg network create --name "mynet" --cidr "10.0.0.0/24" --vnet-default-gateway 3
```

**Fix:** Add `--vnet-default-gateway` option that accepts network key or name.

---

### Issue #2: Missing `--description` option in `network rule update`

**Severity:** Low
**Location:** `src/verge_cli/commands/network_rule.py`

The `rule create` command has `--description` but `rule update` does not, so descriptions cannot be modified after creation.

**Fix:** Add `--description` option to `rule update` command.

---

### Issue #3: CIDR alias creation fails with misleading error

**Severity:** Medium
**Location:** `src/verge_cli/commands/network_alias.py` or SDK

Creating an IP alias with CIDR notation (e.g., `10.99.99.0/24`) fails with:
```
Error: Unable to create IP '10.99.99.1': This IP already exists
```

The error references the network's interface IP, not the CIDR being created.

**Workaround:** Use single IP addresses instead of CIDR ranges.

**Investigation needed:** May be SDK or API limitation.

---

### Issue #4: Missing `--view` option in `network dns zone create`

**Severity:** High
**Location:** `src/verge_cli/commands/network_dns.py`

The API requires a `view` field for DNS zone creation, but the CLI doesn't provide this option:
```
Error: field 'vnet_dns_zones.view' is required
```

**Fix:** Add `--view` option (required) to `dns zone create` command.

---

### Issue #5: Missing `--network` option in `vm create`

**Severity:** Medium
**Location:** `src/verge_cli/commands/vm.py`

Cannot attach a VM to a network during creation. Users must use the web UI or separate commands.

**Fix:** Add `--network` option that accepts network key or name to attach a NIC.

---

### Issue #6: `vm restart` fails with invalid action error

**Severity:** Medium
**Location:** `src/verge_cli/commands/vm.py` or SDK

The restart command sends 'guestreset' action which the API doesn't accept:
```
Error: Error sending action to node: value 'guestreset' is not in list for field 'action'
```

**Workaround:** Use `vm reset` for hard reset, or `vm stop` + `vm start` for graceful restart.

**Investigation needed:** Check correct action name in SDK/API documentation.

---

## Recommendations

1. **High Priority:** Fix Issue #4 (DNS zone create) - blocks all DNS zone functionality
2. **Medium Priority:** Fix Issues #1, #5, #6 - important for common workflows
3. **Low Priority:** Fix Issues #2, #3 - minor usability improvements

---

## Test Environment Cleanup

All test resources were successfully deleted:
- Network: cli-test-net (key: 15)
- VM: cli-test-vm (key: 45)
- 3 firewall rules
- 1 host override
- 1 IP alias

No orphaned resources remain.
