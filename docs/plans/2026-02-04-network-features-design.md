# Network Features Design

> Expanding network commands to include firewall rules, DNS, diagnostics, and apply operations.

**Status:** Design complete, ready for implementation
**Date:** 2026-02-04
**SDK Issue:** [#24 - DNS View management](https://github.com/verge-io/pyVergeOS/issues/24)

## Overview

The current `vrg network` commands only support basic CRUD and power operations. This design adds the network management features required for MVP:

- Firewall rules and IP aliases
- DNS/DHCP host overrides
- DNS zones and records (BIND networks)
- Network diagnostics (DHCP leases, addresses, stats)
- Apply operations for pending changes
- Status visibility for pending restart/apply flags

## Command Structure

### New Subcommand Groups

```
vrg network rule ...       # Firewall rules
vrg network alias ...      # IP aliases for rules
vrg network host ...       # DNS/DHCP host overrides
vrg network dns zone ...   # DNS zones (BIND required)
vrg network dns record ... # DNS records (BIND required)
vrg network diag ...       # Diagnostics
```

### New Network Commands

```
vrg network apply-rules <network>   # Apply firewall changes
vrg network apply-dns <network>     # Apply DNS changes
vrg network restart <network>       # Restart network
vrg network status <network>        # Detailed status with pending changes
```

### Updated Existing Commands

- `vrg network list` - Add needs_restart, needs_rule_apply, needs_dns_apply columns
- `vrg network get` - Add status flags to output
- `vrg vm list` - Add needs_restart column
- `vrg vm get` - Add needs_restart to output

## Firewall Rules

### Commands

```bash
vrg network rule list <network>
vrg network rule get <network> <rule>
vrg network rule create <network> [options]
vrg network rule update <network> <rule> [options]
vrg network rule delete <network> <rule>
vrg network rule enable <network> <rule>
vrg network rule disable <network> <rule>
```

### Create/Update Options

| Option | Description |
|--------|-------------|
| `--name` | Rule name |
| `--direction` | incoming, outgoing |
| `--action` | accept, drop, reject, translate, route |
| `--protocol` | tcp, udp, tcpudp, icmp, any |
| `--interface` | auto, router, dmz, wireguard, any |
| `--source-ip` | Source IP/CIDR or "alias:\<name\>" |
| `--source-ports` | Source port(s) |
| `--dest-ip` | Destination IP/CIDR or "alias:\<name\>" |
| `--dest-ports` | Destination port(s) |
| `--target-ip` | NAT target IP (for translate action) |
| `--target-ports` | NAT target ports (for translate action) |
| `--enabled/--disabled` | Rule state (default: enabled) |
| `--log/--no-log` | Enable logging |
| `--stats/--no-stats` | Enable statistics |
| `--order` | Rule order/position |

### List Filters

```bash
vrg network rule list <network> --direction incoming
vrg network rule list <network> --action accept
vrg network rule list <network> --enabled
vrg network rule list <network> --disabled
```

### Notes

- `<rule>` accepts ID or name for lookup
- Changes require `vrg network apply-rules` to take effect
- System rules cannot be deleted

## IP Aliases

### Commands

```bash
vrg network alias list <network>
vrg network alias get <network> <alias>
vrg network alias create <network> --ip <ip> --name <name> [--description <desc>]
vrg network alias update <network> <alias> [--ip <ip>] [--name <name>] [--description <desc>]
vrg network alias delete <network> <alias>
```

### Notes

- `<alias>` accepts ID, IP, or hostname for lookup
- Used in rules as `--source-ip "alias:webserver"` or `--dest-ip "alias:database"`
- Update implemented as delete+create (SDK doesn't expose PUT, but UI does)

## Host Overrides

### Commands

```bash
vrg network host list <network>
vrg network host get <network> <host>
vrg network host create <network> --hostname <name> --ip <ip> [--type host|domain]
vrg network host update <network> <host> [--hostname <name>] [--ip <ip>] [--type host|domain]
vrg network host delete <network> <host>
```

### Options

| Option | Description |
|--------|-------------|
| `--hostname` | Hostname for the mapping |
| `--ip` | IP address to map to |
| `--type` | `host` (single hostname) or `domain` (domain-wide) |

### Notes

- `<host>` accepts ID, hostname, or IP for lookup
- Available on all networks (doesn't require BIND)
- Changes require `vrg network apply-dns` to take effect

## DNS Zones

### Commands

```bash
vrg network dns zone list <network>
vrg network dns zone get <network> <zone>
vrg network dns zone create <network> --domain <domain> --view <view> [options]
vrg network dns zone update <network> <zone> [options]
vrg network dns zone delete <network> <zone>
```

### Create/Update Options

| Option | Description |
|--------|-------------|
| `--domain` | Domain name (e.g., example.com) |
| `--view` | DNS view name or ID (required for create) |
| `--type` | master, slave, redirect, forward, stub, static-stub |
| `--nameserver` | Primary nameserver |
| `--email` | Admin email |
| `--default-ttl` | Default TTL for records |

### Notes

- `<zone>` accepts ID or domain name for lookup
- Requires BIND enabled on the network
- **DNS View management blocked** until SDK issue #24 resolved
- Users must create views in UI, then manage zones/records via CLI

## DNS Records

### Commands

```bash
vrg network dns record list <network> <zone>
vrg network dns record get <network> <zone> <record>
vrg network dns record create <network> <zone> --type <type> --value <value> [options]
vrg network dns record update <network> <zone> <record> [options]
vrg network dns record delete <network> <zone> <record>
```

### Create/Update Options

| Option | Description |
|--------|-------------|
| `--host` | Hostname (empty for root domain) |
| `--type` | A, AAAA, CNAME, MX, NS, PTR, SRV, TXT, CAA |
| `--value` | Record value (IP, hostname, or text) |
| `--ttl` | Time-to-live (e.g., "1h", "30m", "1d") |
| `--mx-preference` | MX priority (lower = higher priority) |
| `--weight` | SRV weight |
| `--port` | SRV port |
| `--description` | Optional description |

### Notes

- `<record>` accepts ID or host name for lookup
- Changes require `vrg network apply-dns` to take effect

## Diagnostics

### Commands

```bash
vrg network diag leases <network>      # DHCP leases
vrg network diag addresses <network>   # All network addresses
vrg network diag stats <network>       # Traffic/quality statistics
```

### Leases Output

| Field | Description |
|-------|-------------|
| IP | Leased IP address |
| MAC | Client MAC address |
| Hostname | Client hostname |
| Vendor | Client vendor |
| Expiration | Lease expiration time |

### Addresses Output

| Field | Description |
|-------|-------------|
| IP | IP address |
| MAC | MAC address |
| Hostname | Hostname |
| Type | dynamic, static, ipalias, proxy, virtual |
| Expiration | Expiration time (if applicable) |

### Stats Output

| Field | Description |
|-------|-------------|
| TX/RX Bytes | Bytes per second and total |
| TX/RX Packets | Packets per second |
| Quality | Quality percentage (0-100) |
| Latency | Average latency |
| Packet Loss | Loss percentage |

## Status and Apply Operations

### Status Command

```bash
vrg network status <network>
```

**Output includes:**
- Running state
- `needs_restart` - Config changes pending restart
- `needs_rule_apply` - Firewall rules pending
- `needs_dns_apply` - DNS changes pending
- `needs_proxy_apply` - Proxy changes pending

### Apply Commands

```bash
vrg network apply-rules <network>   # Apply pending firewall rules
vrg network apply-dns <network>     # Apply pending DNS/host changes
```

**Notes:**
- Network must be running to apply rules/dns
- Returns success message or error

### Restart Command

```bash
vrg network restart <network> [--apply-rules] [--wait] [--timeout <seconds>]
```

| Option | Description |
|--------|-------------|
| `--apply-rules/--no-apply-rules` | Apply firewall rules after restart (default: true) |
| `--wait` | Wait for network to be running before returning |
| `--timeout` | Timeout for wait in seconds (default: 300) |

## Updated List/Get Output

### Network List

Add columns for pending changes:

| Column | Shows |
|--------|-------|
| RESTART | ✓ if needs_restart |
| RULES | ✓ if needs_rule_apply |
| DNS | ✓ if needs_dns_apply |

### Network Get

Add status section showing all pending flags.

### VM List/Get

Add `RESTART` column/field showing ✓ if needs_restart.

## Deferred Features

The following features are deferred to separate top-level commands:

| Feature | Future Command | Reason |
|---------|----------------|--------|
| WireGuard VPN | `vrg wireguard` | Complex enough for dedicated command |
| IPSec VPN | `vrg ipsec` | Complex enough for dedicated command |
| Routing (BGP/OSPF/EIGRP) | `vrg routing` | Enterprise feature, specialized |
| DNS Views | Blocked | Waiting on SDK issue #24 |

## Implementation Notes

### File Structure

```
src/verge_cli/commands/
├── network.py          # Update existing, add apply/restart/status
├── network_rule.py     # New: firewall rules
├── network_alias.py    # New: IP aliases
├── network_host.py     # New: host overrides
├── network_dns.py      # New: zones and records
├── network_diag.py     # New: diagnostics
└── vm.py               # Update: add needs_restart to output
```

### Registration Pattern

```python
# In network.py
from verge_cli.commands import network_rule, network_alias, network_host, network_dns, network_diag

app.add_typer(network_rule.app, name="rule")
app.add_typer(network_alias.app, name="alias")
app.add_typer(network_host.app, name="host")
app.add_typer(network_dns.app, name="dns")
app.add_typer(network_diag.app, name="diag")
```

### Alias Update Pattern

Since SDK doesn't expose alias update, implement as delete+create:

```python
def update(ctx, alias_id, ip, name, description):
    vctx = get_context(ctx)
    network = resolve_network(vctx, network_id)

    # Get existing alias
    existing = network.aliases.get(alias_id)

    # Merge updates
    new_ip = ip or existing.ip
    new_name = name or existing.hostname
    new_desc = description or existing.description

    # Delete and recreate
    network.aliases.delete(existing.key)
    return network.aliases.create(ip=new_ip, name=new_name, description=new_desc)
```

### DNS Hierarchy

Records are accessed through zones:

```python
# Get network
network = client.networks.get(name="internal")

# Get zone
zone = network.dns_zones.get(domain="example.com")

# List records in zone
records = zone.records.list()

# Create record
record = zone.records.create(
    host="www",
    record_type="A",
    value="10.0.0.100"
)
```

## Testing Strategy

### Unit Tests

- Mock pyvergeos client responses
- Test each command's argument parsing
- Test output formatting for each resource type
- Test error handling (not found, multiple matches)

### Integration Tests

- Mark with `@pytest.mark.integration`
- **Test environment:** See `.claude/TESTENV.md` for live system credentials and resources
- Use DEV System 1 (192.168.10.75) for primary testing
- Create test networks with naming convention `clitest-<feature>` (e.g., `clitest-rules`)
- Require test network with BIND enabled for DNS tests
- Test full CRUD cycles for rules, aliases, hosts, zones, records
- Test apply operations and status flags
- Clean up test resources after each test run
