# DNS Views and Shakedown Fixes Design

**Date:** 2026-02-05
**Status:** Approved

---

## Overview

Implement DNS view support following the pyvergeos v1.0.1 hierarchical model (Network → View → Zone → Record) and fix issues discovered during shakedown testing.

---

## DNS Command Hierarchy

### DNS View Commands

New command group under `vrg network dns view`:

```
vrg network dns view list <network>
vrg network dns view get <network> <view>
vrg network dns view create <network> --name <name> [options]
vrg network dns view update <network> <view> [options]
vrg network dns view delete <network> <view>
```

**Create/Update options:**

| Option | Description |
|--------|-------------|
| `--name` | View name (required for create) |
| `--recursion/--no-recursion` | Enable recursive DNS queries |
| `--match-clients` | Client networks to match (comma-separated CIDRs) |
| `--match-destinations` | Destination networks to match (comma-separated CIDRs) |
| `--max-cache-size` | Max RAM for DNS cache in bytes (default: 32MB) |

**List output columns:** `id`, `name`, `recursion`, `match_clients`

**Implementation notes:**
- Comma-separated input for `--match-clients` and `--match-destinations` transformed to semicolon-delimited format for SDK
- View identifier accepts name or numeric ID

### DNS Zone Commands

Refactored to require view as positional argument:

```
vrg network dns zone list <network> <view>
vrg network dns zone get <network> <view> <zone>
vrg network dns zone create <network> <view> --domain <domain> [options]
vrg network dns zone update <network> <view> <zone> [options]
vrg network dns zone delete <network> <view> <zone>
```

**Create/Update options:**

| Option | Description |
|--------|-------------|
| `--domain` | Zone domain name (required for create) |
| `--type` | Zone type: master, slave, forward, stub (default: master) |
| `--nameserver` | Primary nameserver FQDN |
| `--email` | Zone administrator email |
| `--default-ttl` | Default TTL for records (default: 1h) |
| `--masters` | Master servers for secondary zones (comma-separated) |
| `--forwarders` | Forwarder servers for forward zones (comma-separated) |

**List output columns:** `id`, `domain`, `type`, `view_name`, `serial`

**Implementation notes:**
- Zone identifier accepts domain name or numeric ID
- Comma-separated input for `--masters` and `--forwarders` transformed to semicolon-delimited format for SDK

### DNS Record Commands

Refactored to require view as positional argument, use ID-based identification:

```
vrg network dns record list <network> <view> <zone>
vrg network dns record get <network> <view> <zone> <id>
vrg network dns record create <network> <view> <zone> --name <name> --type <type> --value <value> [options]
vrg network dns record update <network> <view> <zone> <id> [options]
vrg network dns record delete <network> <view> <zone> <id>
```

**Create/Update options:**

| Option | Description |
|--------|-------------|
| `--name` | Record hostname (use `@` for root domain) |
| `--type` | Record type: A, AAAA, CNAME, MX, NS, PTR, SRV, TXT, CAA |
| `--value` | Record value (IP, hostname, or text) |
| `--ttl` | Time-to-live (e.g., 1h, 30m, 1d) |
| `--priority` | MX/SRV priority |
| `--weight` | SRV weight |
| `--port` | SRV port |
| `--description` | Record description |

**List output columns:** `id`, `host`, `type`, `value`, `ttl`, `priority`

**Implementation notes:**
- Record operations use numeric ID (not hostname) for get/update/delete
- Renamed `--address` to `--value` for clarity with non-A record types

---

## Example Workflows

### Split-Horizon DNS Setup

```bash
# Create views for internal and external resolution
vrg network dns view create mynet --name internal --recursion --match-clients "10.0.0.0/8,192.168.0.0/16"
vrg network dns view create mynet --name external --match-clients "any"

# Create same zone in both views
vrg network dns zone create mynet internal --domain example.com
vrg network dns zone create mynet external --domain example.com

# Internal view: private IPs
vrg network dns record create mynet internal example.com --name www --type A --value 10.0.0.100
vrg network dns record create mynet internal example.com --name db --type A --value 10.0.0.50

# External view: public IPs
vrg network dns record create mynet external example.com --name www --type A --value 203.0.113.50

# Apply DNS changes
vrg network apply-dns mynet
```

### Record Management by ID

```bash
# List records to see IDs
vrg network dns record list mynet internal example.com
# id  host  type  value       ttl  priority
# 42  www   A     10.0.0.100  1h
# 43  db    A     10.0.0.50   1h

# Update by ID
vrg network dns record update mynet internal example.com 42 --ttl 30m

# Delete by ID
vrg network dns record delete mynet internal example.com 43
```

---

## Shakedown Fixes

### Issue #1: Missing `--vnet-default-gateway` in `network create`

**File:** `src/verge_cli/commands/network.py`

Add option to route traffic through another network:

```bash
vrg network create --name mynet --cidr 10.0.0.0/24 --vnet-default-gateway External
```

- Accepts network name or key
- Resolved via `resolve_resource_id()`
- Maps to SDK's `interface_network` parameter

### Issue #2: Missing `--description` in `network rule update`

**File:** `src/verge_cli/commands/network_rule.py`

Add `--description` option to `rule_update()` function, matching the create command.

### Issue #6: `vm restart` fails with 'guestreset' action

**File:** `src/verge_cli/commands/vm.py`

The SDK's `guest_reboot()` method sends action `guestreset` which the API rejects.

**Investigation needed:** Check API documentation for correct action name. Possible solutions:
1. Different action name exists
2. Use `guestshutdown` + wait + `poweron` sequence
3. SDK bug requiring upstream fix

### Issue #3: CIDR alias creation fails (Deferred)

This appears to be an API/SDK limitation. Document workaround in CLI help text:
> "Use single IP addresses. CIDR notation may fail with misleading errors."

Defer SDK investigation to separate effort.

### Issue #5: Missing `--network` in `vm create` (Deferred)

Requires NIC/drive infrastructure implementation. Will be addressed when `vm nic` and `vm drive` command groups are added.

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/verge_cli/commands/network_dns.py` | Major refactor: add view commands, update zone/record commands for view hierarchy |
| `src/verge_cli/commands/network.py` | Add `--vnet-default-gateway` option to create command |
| `src/verge_cli/commands/network_rule.py` | Add `--description` option to update command |
| `src/verge_cli/commands/vm.py` | Fix restart action |
| `pyproject.toml` | Update pyvergeos dependency to v1.0.1 |

---

## Dependencies

- pyvergeos v1.0.1 (provides `dns_views` and updated `dns` modules)

---

## Testing Strategy

1. **Unit tests:** Mock SDK responses for all new view commands
2. **Integration tests:** Test full workflow against live VergeOS system
3. **Regression tests:** Verify existing zone/record tests still pass (with updated signatures)
