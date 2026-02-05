# Verge CLI - Product Requirements Document

## Executive Summary

**Product Name:** verge-cli
**Command Name:** `vrg`
**Version:** 1.0.0
**Status:** Planning
**Date:** February 2026

Verge CLI is a command-line interface for managing VergeOS infrastructure. It provides a unified tool for interacting with VergeOS APIs, enabling administrators and developers to manage virtual machines, networks, storage, tenants, backups, and more from the terminal. The CLI follows patterns established by AWS CLI and Azure CLI for familiarity and ease of adoption.

---

## Problem Statement

VergeOS administrators currently manage infrastructure through:
1. **Web UI** - Feature-rich but not scriptable
2. **REST API** - Powerful but requires custom tooling
3. **SDKs** (Python, Go, PowerShell) - Require programming knowledge

There is no unified command-line tool for:
- Quick administrative tasks
- Shell scripting and automation
- CI/CD pipeline integration
- SSH-based remote management
- Batch operations across resources

---

## Goals & Objectives

### Primary Goals
1. **Provide full API coverage** - All VergeOS operations accessible via CLI
2. **Enable automation** - Scriptable commands with machine-readable output
3. **Ensure consistency** - Uniform command structure across all resource types
4. **Support enterprise workflows** - Multi-environment, profiles, and secure credential management

### Success Metrics
- 100% coverage of pyvergeos SDK functionality
- Sub-second response time for simple operations
- Adoption by 50% of VergeOS administrators within 6 months
- Integration into 3+ CI/CD platforms

---

## Target Users

### Primary Users
1. **System Administrators** - Day-to-day infrastructure management
2. **DevOps Engineers** - Automation and CI/CD integration
3. **MSPs/Service Providers** - Multi-tenant management at scale

### Secondary Users
1. **Developers** - Testing and development environment management
2. **Support Engineers** - Troubleshooting and diagnostics

### User Personas

**Alex - Infrastructure Administrator**
- Manages 50+ VMs across 5 clusters
- Prefers terminal over GUI for repetitive tasks
- Needs quick status checks and bulk operations
- Values tab completion and consistent syntax

**Sam - DevOps Engineer**
- Builds CI/CD pipelines for infrastructure provisioning
- Requires JSON output for parsing and automation
- Needs non-interactive authentication
- Values idempotent operations and clear exit codes

**Jordan - MSP Technician**
- Manages multiple customer tenants
- Switches between environments frequently
- Needs secure credential management
- Values profile-based configuration

---

## Scope

### In Scope (v1.0)

#### Core Infrastructure
- [x] Virtual Machines (full lifecycle)
- [x] Virtual Networks (internal, external, rules)
- [x] Clusters and Nodes
- [x] Storage Tiers
- [x] Drives and NICs

#### Multi-Tenancy
- [x] Tenant management (CRUD, power operations)
- [x] Tenant resource allocation
- [x] Tenant snapshots

#### Data Protection
- [x] VM snapshots
- [x] Cloud snapshots
- [x] Site syncs (outgoing/incoming)
- [x] Snapshot profiles

#### Storage & NAS
- [x] NAS volumes
- [x] CIFS/NFS shares
- [x] Volume syncs
- [x] File management (media catalog)

#### Networking
- [x] Firewall rules
- [x] DHCP configuration
- [x] DNS zones and records
- [x] Aliases and routing
- [x] WireGuard VPN
- [x] IPSec VPN

#### Administration
- [x] Users and groups
- [x] Permissions
- [x] API keys
- [x] Certificates
- [x] System settings

#### Automation
- [x] Tasks and schedules
- [x] Webhooks
- [x] VM recipes
- [x] Tenant recipes

#### Monitoring
- [x] Alarms
- [x] Logs
- [x] Statistics/dashboards

### Out of Scope (Future Versions)
- [ ] Private AI / LLM management (v1.1)
- [ ] Interactive TUI mode (v1.2)
- [ ] Plugin system for extensions (v1.2)
- [ ] Terraform state import/export (v1.1)
- [ ] Real-time log streaming (v1.1)
- [ ] Standalone binaries via PyInstaller (v1.1)
- [ ] Native installers (MSI, PKG, DEB, RPM) (v1.2)

---

## Technical Architecture

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.9+ | Matches pyvergeos SDK, broad adoption |
| CLI Framework | Click or Typer | Modern, supports nested commands, auto-help |
| SDK | pyvergeos | Existing SDK with full API coverage |
| Config | TOML/YAML | Human-readable, standard formats |
| Output | Rich | Table formatting, colors, progress bars |
| Packaging | PyPI + pipx | Standard Python distribution |

### Project Structure

```
verge-cli/
├── src/
│   └── verge_cli/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── cli.py               # Main CLI group
│       ├── config.py            # Configuration management
│       ├── auth.py              # Authentication handling
│       ├── output.py            # Output formatting
│       ├── utils.py             # Shared utilities
│       └── commands/
│           ├── __init__.py
│           ├── vm.py            # VM commands
│           ├── network.py       # Network commands
│           ├── tenant.py        # Tenant commands
│           ├── snapshot.py      # Snapshot commands
│           ├── storage.py       # Storage commands
│           ├── nas.py           # NAS commands
│           ├── user.py          # User commands
│           ├── task.py          # Task commands
│           ├── system.py        # System commands
│           └── ...
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

### SDK Integration

The CLI will wrap the pyvergeos SDK:

```python
# Example: vm.py command implementation
from pyvergeos import VergeClient
from verge_cli.config import get_client

@vm.command()
@click.option('--name', required=True)
@click.option('--cluster', default=None)
@click.option('--ram', default=1024, type=int)
@click.option('--cpu', default=1, type=int)
def create(name, cluster, ram, cpu):
    """Create a new virtual machine."""
    client = get_client()
    vm = client.vms.create(
        name=name,
        cluster=cluster,
        ram=ram,
        cpu_cores=cpu
    )
    output(vm)
```

---

## Command Structure

### Command Hierarchy

```
vrg
├── configure          # Setup and profile management
├── vm                 # Virtual machine operations
├── network            # Virtual network operations
├── cluster            # Cluster management
├── node               # Node management
├── tenant             # Tenant operations
├── snapshot           # Snapshot management
├── storage            # Storage tier operations
├── nas                # NAS service operations
├── user               # User management
├── group              # Group management
├── permission         # Permission management
├── apikey             # API key management
├── task               # Task and schedule management
├── recipe             # Recipe operations
├── webhook            # Webhook management
├── certificate        # Certificate management
├── alarm              # Alarm management
├── log                # Log viewing
├── system             # System settings and info
└── site-sync          # Site synchronization
```

### Command Pattern

All resource commands follow a consistent CRUD+ pattern:

```
vrg <resource> list [OPTIONS]      # List resources with filtering
vrg <resource> get <ID|NAME>       # Get single resource details
vrg <resource> create [OPTIONS]    # Create new resource
vrg <resource> update <ID> [OPTS]  # Update existing resource
vrg <resource> delete <ID|NAME>    # Delete resource
vrg <resource> <action> <ID>       # Resource-specific actions
```

### Global Options

```
--profile, -p       # Named profile to use
--host, -H          # Override host URL
--output, -o        # Output format (table|json|yaml|csv)
--quiet, -q         # Suppress non-essential output
--verbose, -v       # Increase verbosity (stackable: -vvv)
--no-color          # Disable colored output
--dry-run           # Show what would happen without executing
--help, -h          # Show help message
--version           # Show version information
```

### Resource-Specific Options

#### VM Commands
```
vrg vm list [--filter EXPR] [--status STATUS] [--cluster NAME] [--tag TAG]
vrg vm get <VM>
vrg vm create --name NAME [--cluster NAME] [--ram MB] [--cpu CORES] [--recipe NAME]
vrg vm update <VM> [--name NAME] [--ram MB] [--cpu CORES]
vrg vm delete <VM> [--force]

# Power operations
vrg vm start <VM>
vrg vm stop <VM> [--force]
vrg vm restart <VM>
vrg vm reset <VM>

# VM actions
vrg vm snapshot <VM> --name NAME [--retention HOURS]
vrg vm clone <VM> --name NAME [--cluster NAME]
vrg vm migrate <VM> [--node NODE]
vrg vm console <VM>

# Hardware management
vrg vm drive list <VM>
vrg vm drive add <VM> --size GB [--tier TIER]
vrg vm drive resize <VM> <DRIVE> --size GB
vrg vm drive remove <VM> <DRIVE>

vrg vm nic list <VM>
vrg vm nic add <VM> --network NET
vrg vm nic remove <VM> <NIC>

vrg vm device list <VM>
vrg vm device add <VM> --resource-group UUID
vrg vm device remove <VM> <DEVICE>
```

#### Network Commands
```
vrg network list [--type internal|external] [--status STATUS]
vrg network get <NETWORK>
vrg network create --name NAME --type TYPE [--cidr CIDR] [--gateway IP]
vrg network update <NETWORK> [OPTIONS]
vrg network delete <NETWORK>

vrg network start <NETWORK>
vrg network stop <NETWORK>
vrg network apply-rules <NETWORK>
vrg network apply-dns <NETWORK>
vrg network diagnostics <NETWORK>

# Sub-resources
vrg network rule list <NETWORK>
vrg network rule add <NETWORK> [OPTIONS]
vrg network rule remove <NETWORK> <RULE>

vrg network alias list <NETWORK>
vrg network dhcp list <NETWORK>
vrg network dns list <NETWORK>
```

#### Tenant Commands
```
vrg tenant list [--filter EXPR]
vrg tenant get <TENANT>
vrg tenant create --name NAME [--recipe NAME] [--cpu CORES] [--ram GB] [--storage GB]
vrg tenant update <TENANT> [OPTIONS]
vrg tenant delete <TENANT> [--force]

vrg tenant start <TENANT>
vrg tenant stop <TENANT> [--force]
vrg tenant restart <TENANT>
vrg tenant snapshot <TENANT> --name NAME
vrg tenant connect <TENANT>
```

#### Snapshot Commands
```
vrg snapshot list [--type vm|tenant|cloud|volume] [--filter EXPR]
vrg snapshot get <SNAPSHOT>
vrg snapshot create --type TYPE --target ID --name NAME [--retention HOURS]
vrg snapshot restore <SNAPSHOT> [--name NAME]
vrg snapshot delete <SNAPSHOT>

vrg snapshot profile list
vrg snapshot profile create --name NAME --schedule CRON [--retention HOURS]
```

#### Storage Commands
```
vrg storage tier list
vrg storage tier get <TIER>
vrg storage stats

vrg storage file list [--filter EXPR]
vrg storage file upload <LOCAL_PATH> [--name NAME]
vrg storage file download <FILE> <LOCAL_PATH>
vrg storage file delete <FILE>
```

#### NAS Commands
```
vrg nas volume list
vrg nas volume get <VOLUME>
vrg nas volume create --name NAME --size GB [--tier TIER]
vrg nas volume delete <VOLUME>
vrg nas volume snapshot <VOLUME> --name NAME

vrg nas share list [--type cifs|nfs]
vrg nas share create --volume VOLUME --name NAME --type TYPE [OPTIONS]
vrg nas share delete <SHARE>

vrg nas service list
vrg nas service start <SERVICE>
vrg nas service stop <SERVICE>
```

#### Site Sync Commands
```
vrg site-sync list [--direction outgoing|incoming]
vrg site-sync get <SYNC>
vrg site-sync create --site SITE --source SOURCE [OPTIONS]
vrg site-sync delete <SYNC>

vrg site-sync start <SYNC>
vrg site-sync stop <SYNC>
vrg site-sync enable <SYNC>
vrg site-sync disable <SYNC>
vrg site-sync status <SYNC>
```

#### User/Group Commands
```
vrg user list [--type normal|api|vdi]
vrg user get <USER>
vrg user create --name NAME --email EMAIL [--type TYPE]
vrg user update <USER> [OPTIONS]
vrg user delete <USER>
vrg user enable <USER>
vrg user disable <USER>

vrg group list
vrg group get <GROUP>
vrg group create --name NAME
vrg group member add <GROUP> --user USER
vrg group member remove <GROUP> --user USER

vrg permission list [--user USER] [--group GROUP]
vrg permission grant --user USER --resource RESOURCE --level LEVEL
vrg permission revoke <PERMISSION>
```

#### Task Commands
```
vrg task list [--status STATUS]
vrg task get <TASK>
vrg task create --name NAME [--script SCRIPT]
vrg task execute <TASK> [--wait]
vrg task cancel <TASK>
vrg task enable <TASK>
vrg task disable <TASK>
vrg task wait <TASK> [--timeout SECONDS]

vrg task schedule list
vrg task schedule create --task TASK --cron CRON
```

#### System Commands
```
vrg system info
vrg system version
vrg system settings list
vrg system settings get <KEY>
vrg system settings set <KEY> <VALUE>
vrg system license show
vrg system stats
```

---

## Configuration Management

### Configuration File

**Location:** `~/.vrg/config.toml` (or `~/.config/verge/config.toml`)

```toml
[default]
host = "https://verge.example.com"
verify_ssl = true
output = "table"
timeout = 30

[profile.production]
host = "https://verge-prod.example.com"
api_key = "vk_xxxxxxxxxxxx"

[profile.staging]
host = "https://verge-staging.example.com"
username = "admin"
# Password stored in keyring or prompted

[profile.dev]
host = "https://192.168.1.100"
verify_ssl = false
```

### Credentials Management

**Priority Order (highest to lowest):**
1. Command-line arguments (`--api-key`, `--username/--password`)
2. Environment variables (`VERGE_HOST`, `VERGE_API_KEY`, `VERGE_USERNAME`, `VERGE_PASSWORD`)
3. Profile in config file
4. Default profile
5. Interactive prompt

**Environment Variables:**
```bash
VERGE_HOST           # VergeOS host URL
VERGE_API_KEY        # API key for authentication
VERGE_USERNAME       # Username for basic auth
VERGE_PASSWORD       # Password for basic auth
VERGE_PROFILE        # Default profile name
VERGE_OUTPUT         # Default output format
VERGE_VERIFY_SSL     # SSL verification (true/false)
VERGE_TIMEOUT        # Request timeout in seconds
```

### Configure Command

```bash
# Interactive configuration
vrg configure

# Configure specific profile
vrg configure --profile production

# Set individual values
vrg configure set host https://verge.example.com
vrg configure set output json
vrg configure set verify_ssl false

# List configuration
vrg configure list

# Show current effective configuration
vrg configure show
```

---

## Output Formats

### Table Format (Default)

```
$ vrg vm list
┌─────┬───────────────┬──────────┬────────┬───────┬─────────────────────┐
│ Key │ Name          │ Status   │ CPU    │ RAM   │ Cluster             │
├─────┼───────────────┼──────────┼────────┼───────┼─────────────────────┤
│ 1   │ web-server-01 │ running  │ 4      │ 8 GB  │ production          │
│ 2   │ web-server-02 │ running  │ 4      │ 8 GB  │ production          │
│ 3   │ db-primary    │ running  │ 8      │ 32 GB │ production          │
│ 4   │ dev-test      │ stopped  │ 2      │ 4 GB  │ development         │
└─────┴───────────────┴──────────┴────────┴───────┴─────────────────────┘
```

### JSON Format

```json
$ vrg vm list -o json
[
  {
    "$key": 1,
    "name": "web-server-01",
    "status": "running",
    "cpu_cores": 4,
    "ram": 8192,
    "cluster": "production"
  }
]
```

### YAML Format

```yaml
$ vrg vm list -o yaml
- $key: 1
  name: web-server-01
  status: running
  cpu_cores: 4
  ram: 8192
  cluster: production
```

### CSV Format

```csv
$ vrg vm list -o csv
$key,name,status,cpu_cores,ram,cluster
1,web-server-01,running,4,8192,production
2,web-server-02,running,4,8192,production
```

### Single Value Output

```bash
# Get specific field
$ vrg vm get web-server-01 -o json | jq -r '.status'
running

# Query mode for scripting
$ vrg vm get web-server-01 --query status
running
```

---

## Error Handling

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments / usage error |
| 3 | Configuration error |
| 4 | Authentication error |
| 5 | Authorization error (forbidden) |
| 6 | Resource not found |
| 7 | Conflict error |
| 8 | Validation error |
| 9 | Timeout error |
| 10 | Connection error |

### Error Output

```
$ vrg vm delete nonexistent
Error: VM 'nonexistent' not found.

Use 'vrg vm list' to see available VMs.

Exit code: 6
```

### Verbose Error Mode

```
$ vrg vm delete nonexistent -vvv
DEBUG: Loading profile 'default'
DEBUG: Connecting to https://verge.example.com
DEBUG: DELETE /api/v4/vms/nonexistent
DEBUG: Response: 404 Not Found
ERROR: VM 'nonexistent' not found.
DEBUG: API response: {"error": "Resource not found", "code": 404}

Exit code: 6
```

---

## Interactive Features

### Tab Completion

Support for bash, zsh, and fish shells:

```bash
# Install completion
vrg completion bash >> ~/.bashrc
vrg completion zsh >> ~/.zshrc
vrg completion fish > ~/.config/fish/completions/vrg.fish

# Usage
$ vrg vm st<TAB>
start  stop  stats

$ vrg vm get web<TAB>
web-server-01  web-server-02
```

### Progress Indicators

Long-running operations show progress:

```
$ vrg vm clone db-primary --name db-replica
Cloning VM 'db-primary' to 'db-replica'...
[████████████████████████████████████████] 100% Complete

VM 'db-replica' created successfully.
Key: 15
```

### Confirmation Prompts

Destructive operations require confirmation:

```
$ vrg vm delete web-server-01
Are you sure you want to delete VM 'web-server-01'? [y/N]: y
Deleting VM 'web-server-01'...
VM deleted successfully.

# Skip confirmation
$ vrg vm delete web-server-01 --yes
```

### Wait Mode

Wait for async operations to complete:

```
$ vrg vm start db-primary --wait
Starting VM 'db-primary'...
Waiting for VM to be running... done (12s)
VM 'db-primary' is now running.

# With timeout
$ vrg vm snapshot db-primary --name backup --wait --timeout 300
```

---

## Filtering and Queries

### OData-Style Filters

```bash
# Simple equality
vrg vm list --filter "status eq 'running'"

# Multiple conditions
vrg vm list --filter "status eq 'running' and cpu_cores ge 4"

# Pattern matching
vrg vm list --filter "name bw 'web-'"

# Complex queries
vrg vm list --filter "(status eq 'running' or status eq 'stopped') and ram gt 4096"
```

### Shorthand Filters

```bash
# Direct field filters
vrg vm list --status running
vrg vm list --cluster production --status running
vrg network list --type internal
```

### Sorting and Limiting

```bash
# Sort ascending
vrg vm list --sort name

# Sort descending
vrg vm list --sort -created

# Limit results
vrg vm list --limit 10

# Pagination
vrg vm list --limit 10 --offset 20
```

### Field Selection

```bash
# Select specific fields
vrg vm list --fields name,status,ram

# Common field sets
vrg vm list --fields summary
vrg vm list --fields all
```

---

## Batch Operations

### Multiple Resource Operations

```bash
# Delete multiple VMs
vrg vm delete vm1 vm2 vm3

# Start all VMs matching filter
vrg vm start --filter "cluster eq 'dev'"

# Apply to all from file
vrg vm stop $(cat vms-to-stop.txt)
```

### Input from Stdin

```bash
# Pipe list to delete
vrg vm list --filter "name bw 'temp-'" -o json | jq -r '.[].name' | xargs vrg vm delete

# Create from JSON file
cat vm-config.json | vrg vm create --from-json -
```

### Dry Run Mode

```bash
$ vrg vm delete --filter "status eq 'stopped'" --dry-run
Would delete the following VMs:
  - dev-test (key: 4)
  - staging-old (key: 7)
  - temp-build (key: 12)

Total: 3 VMs
Run without --dry-run to execute.
```

---

## Security Considerations

### Credential Storage

1. **Keyring Integration** - Store passwords in system keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
2. **API Keys** - Prefer API keys over username/password
3. **Environment Variables** - Support for CI/CD pipelines
4. **No Plaintext Passwords** - Never store passwords in config files

### SSL/TLS

```bash
# Skip verification (development only)
vrg --verify-ssl=false vm list

# Custom CA certificate
vrg --ca-cert /path/to/ca.pem vm list

# Environment variable
export VERGE_CA_CERT=/path/to/ca.pem
```

### Audit Logging

```bash
# Log all commands to file
export VERGE_AUDIT_LOG=~/.vrg/audit.log

# Log format
# 2026-02-01T10:30:00Z user=admin profile=production cmd="vm delete web-server-01" exit=0
```

---

## Cross-Platform Support

### Supported Platforms

| Platform | Versions | Architecture |
|----------|----------|--------------|
| **Linux** | Ubuntu 20.04+, RHEL 8+, Debian 11+ | x64, arm64 |
| **macOS** | 12 (Monterey)+ | x64 (Intel), arm64 (Apple Silicon) |
| **Windows** | 10, 11, Server 2019+ | x64 |

### Platform-Specific Considerations

#### Configuration Paths

The CLI uses platform-appropriate directories via `platformdirs`:

| OS | Config Directory | Data Directory |
|----|------------------|----------------|
| Linux | `~/.config/verge/` | `~/.local/share/verge/` |
| macOS | `~/Library/Application Support/verge/` | Same |
| Windows | `%APPDATA%\verge\` | `%LOCALAPPDATA%\verge\` |

**Fallback:** `~/.vrg/` is supported on all platforms for simplicity.

#### Credential Storage

Secure credential storage via `keyring` library:

| OS | Backend | Notes |
|----|---------|-------|
| macOS | Keychain | Native integration |
| Windows | Windows Credential Manager | Native integration |
| Linux | Secret Service API | GNOME Keyring, KWallet |
| Fallback | Encrypted file | When no keyring available |

```python
# Implementation
import keyring
from keyring.errors import NoKeyringError

def store_credential(service, key, value):
    try:
        keyring.set_password(service, key, value)
    except NoKeyringError:
        # Fall back to encrypted file storage
        store_encrypted_file(key, value)
```

#### Shell Completion

Support for all major shells:

| Shell | OS | Installation |
|-------|-----|--------------|
| bash | Linux, macOS, Windows (Git Bash) | `vrg completion bash >> ~/.bashrc` |
| zsh | macOS (default), Linux | `vrg completion zsh >> ~/.zshrc` |
| fish | Linux, macOS | `vrg completion fish > ~/.config/fish/completions/vrg.fish` |
| PowerShell | Windows, macOS, Linux | `vrg completion powershell >> $PROFILE` |

#### Terminal Handling

The `rich` library handles cross-platform terminal differences:

- **Colors:** Auto-detects ANSI support, falls back gracefully
- **Unicode:** Uses ASCII alternatives on limited terminals
- **Width:** Adapts table output to terminal size
- **Windows Terminal:** Full support for modern Windows Terminal
- **Legacy cmd.exe:** Graceful degradation with `colorama`

```python
from rich.console import Console

console = Console()  # Auto-detects capabilities
console.print("[green]Success[/green]")  # Works everywhere
```

#### Path Handling

All file operations use `pathlib` for cross-platform compatibility:

```python
from pathlib import Path

# Always works regardless of OS
config_file = Path.home() / ".verge" / "config.toml"
```

#### Line Endings

- Config files use platform-native line endings when written
- Config files accept both LF and CRLF when read
- JSON/YAML output always uses LF for consistency

#### SSL Certificates

| OS | System CA Bundle Location |
|----|---------------------------|
| Linux | `/etc/ssl/certs/ca-certificates.crt` |
| macOS | System Keychain |
| Windows | Windows Certificate Store |

The `requests` library (via `certifi`) handles this automatically.

### Cross-Platform Dependencies

```toml
[project]
dependencies = [
    "pyvergeos>=0.1.1",
    "click>=8.0",           # CLI framework
    "rich>=13.0",           # Terminal output (handles Windows automatically)
    "platformdirs>=3.0",    # Platform-specific paths
    "keyring>=24.0",        # Secure credential storage
    "tomli>=2.0; python_version<'3.11'",  # TOML parsing (stdlib in 3.11+)
    "tomli-w>=1.0",         # TOML writing
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "mypy>=1.0",
    "ruff>=0.1",
]
```

### Testing Matrix

CI/CD runs tests on:

```yaml
# GitHub Actions matrix
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]
```

---

## Distribution & Installation

### v1.0 Distribution (PyPI Only)

The initial release targets Python users via PyPI. This keeps the release process simple and aligns with our target audience of technical administrators and DevOps engineers.

**Requirements:** Python 3.9 or later

```bash
# Install from PyPI (standard)
pip install verge-cli

# Install with pipx (recommended - isolated environment)
pipx install verge-cli

# Install specific version
pip install verge-cli==1.0.0

# Upgrade
pip install --upgrade verge-cli

# Verify installation
vrg --version
```

### Container Image

For CI/CD pipelines and users who prefer containers:

```bash
# Docker
docker run -it --rm \
  -e VERGE_HOST=https://verge.example.com \
  -e VERGE_API_KEY=vk_xxx \
  vrg/cli vm list

# With config mount
docker run -it --rm \
  -v ~/.verge:/root/.verge:ro \
  vrg/cli vm list
```

### Build from Source

```bash
git clone https://github.com/verge/verge-cli.git
cd verge-cli
pip install -e ".[dev]"
```

### Future Distribution (v1.1+)

The following distribution methods will be added based on user demand:

| Method | Target Version | Notes |
|--------|----------------|-------|
| PyInstaller binaries | v1.1 | Standalone executables for users without Python |
| Homebrew | v1.1 | `brew install verge-cli` |
| Docker Hub | v1.0 | Available at launch |
| Windows MSI | v1.2 | Native Windows installer |
| Linux DEB/RPM | v1.2 | Native Linux packages |

---

## Testing Strategy

### Unit Tests
- Command parsing and validation
- Output formatting
- Configuration management
- Filter expression building

### Integration Tests
- Mock SDK responses
- End-to-end command execution
- Error handling scenarios

### Acceptance Tests
- Real VergeOS environment
- Full workflow testing
- Performance benchmarks

### Test Coverage Target
- 90% line coverage
- 100% coverage for critical paths (auth, CRUD operations)

---

## Documentation

### Built-in Help

```bash
vrg --help
vrg vm --help
vrg vm create --help
```

### Man Pages

```bash
man vrg
man vrg-vm
man vrg-network
```

### Online Documentation
- Quick start guide
- Command reference
- Configuration guide
- Scripting examples
- Troubleshooting guide

---

## Release Plan

### Phase 1: Core (v0.1.0) - MVP
- [ ] Project setup and CLI framework (Click or Typer)
- [ ] Configuration management (~/.vrg/config.toml)
- [ ] Authentication (API key, basic auth, environment variables)
- [ ] VM commands (full CRUD + power operations)
- [ ] Network commands (full CRUD + rules)
- [ ] Output formatting (table, JSON)
- [ ] Basic error handling and exit codes

### Phase 2: Infrastructure (v0.2.0)
- [ ] Cluster and node commands
- [ ] Tenant commands (full lifecycle)
- [ ] Storage tier commands
- [ ] Drive and NIC management (VM sub-commands)
- [ ] Tab completion (bash, zsh, fish, PowerShell)
- [ ] Docker image release

### Phase 3: Data Protection (v0.3.0)
- [ ] VM snapshots
- [ ] Tenant snapshots
- [ ] Cloud snapshots
- [ ] Snapshot profiles
- [ ] Site syncs (outgoing/incoming)

### Phase 4: Storage & NAS (v0.4.0)
- [ ] NAS volumes
- [ ] CIFS/NFS shares
- [ ] Volume syncs
- [ ] File management (media catalog)

### Phase 5: Administration (v0.5.0)
- [ ] Users and groups
- [ ] Permissions (grant/revoke)
- [ ] API keys
- [ ] Certificates

### Phase 6: Automation (v0.6.0)
- [ ] Tasks and schedules
- [ ] Webhooks
- [ ] VM recipes
- [ ] Tenant recipes

### Phase 7: Polish (v1.0.0)
- [ ] Full documentation (man pages, online docs)
- [ ] Performance optimization
- [ ] Comprehensive test coverage (90%+)
- [ ] Stable API (command structure locked)

### Phase 8: Extended Distribution (v1.1.0)
- [ ] PyInstaller standalone binaries
- [ ] Homebrew formula
- [ ] Private AI / LLM commands

---

## Appendix A: Full Command Reference

### VM Commands
| Command | Description |
|---------|-------------|
| `vm list` | List all VMs |
| `vm get` | Get VM details |
| `vm create` | Create new VM |
| `vm update` | Update VM settings |
| `vm delete` | Delete VM |
| `vm start` | Power on VM |
| `vm stop` | Power off VM |
| `vm restart` | Restart VM |
| `vm reset` | Hard reset VM |
| `vm snapshot` | Create VM snapshot |
| `vm clone` | Clone VM |
| `vm migrate` | Migrate VM to node |
| `vm console` | Open VM console |
| `vm drive list` | List VM drives |
| `vm drive add` | Add drive to VM |
| `vm drive resize` | Resize VM drive |
| `vm drive remove` | Remove drive from VM |
| `vm nic list` | List VM NICs |
| `vm nic add` | Add NIC to VM |
| `vm nic remove` | Remove NIC from VM |
| `vm device list` | List VM devices |
| `vm device add` | Add device to VM |
| `vm device remove` | Remove device from VM |

### Network Commands
| Command | Description |
|---------|-------------|
| `network list` | List all networks |
| `network get` | Get network details |
| `network create` | Create new network |
| `network update` | Update network settings |
| `network delete` | Delete network |
| `network start` | Power on network |
| `network stop` | Power off network |
| `network apply-rules` | Apply firewall rules |
| `network apply-dns` | Apply DNS changes |
| `network diagnostics` | Run network diagnostics |
| `network rule list` | List network rules |
| `network rule add` | Add firewall rule |
| `network rule remove` | Remove firewall rule |
| `network alias list` | List network aliases |
| `network dhcp list` | List DHCP leases |
| `network dns list` | List DNS records |

### Tenant Commands
| Command | Description |
|---------|-------------|
| `tenant list` | List all tenants |
| `tenant get` | Get tenant details |
| `tenant create` | Create new tenant |
| `tenant update` | Update tenant settings |
| `tenant delete` | Delete tenant |
| `tenant start` | Power on tenant |
| `tenant stop` | Power off tenant |
| `tenant restart` | Restart tenant |
| `tenant snapshot` | Create tenant snapshot |
| `tenant connect` | Open tenant UI |

### Snapshot Commands
| Command | Description |
|---------|-------------|
| `snapshot list` | List snapshots |
| `snapshot get` | Get snapshot details |
| `snapshot create` | Create snapshot |
| `snapshot restore` | Restore from snapshot |
| `snapshot delete` | Delete snapshot |
| `snapshot profile list` | List snapshot profiles |
| `snapshot profile create` | Create snapshot profile |
| `snapshot profile delete` | Delete snapshot profile |

### Storage Commands
| Command | Description |
|---------|-------------|
| `storage tier list` | List storage tiers |
| `storage tier get` | Get tier details |
| `storage stats` | Show storage statistics |
| `storage file list` | List media files |
| `storage file upload` | Upload file |
| `storage file download` | Download file |
| `storage file delete` | Delete file |

### NAS Commands
| Command | Description |
|---------|-------------|
| `nas volume list` | List NAS volumes |
| `nas volume get` | Get volume details |
| `nas volume create` | Create NAS volume |
| `nas volume delete` | Delete NAS volume |
| `nas volume snapshot` | Snapshot volume |
| `nas share list` | List shares |
| `nas share create` | Create CIFS/NFS share |
| `nas share delete` | Delete share |
| `nas service list` | List NAS services |
| `nas service start` | Start NAS service |
| `nas service stop` | Stop NAS service |

### Site Sync Commands
| Command | Description |
|---------|-------------|
| `site-sync list` | List site syncs |
| `site-sync get` | Get sync details |
| `site-sync create` | Create site sync |
| `site-sync delete` | Delete site sync |
| `site-sync start` | Start sync |
| `site-sync stop` | Stop sync |
| `site-sync enable` | Enable sync |
| `site-sync disable` | Disable sync |
| `site-sync status` | Check sync status |

### User Commands
| Command | Description |
|---------|-------------|
| `user list` | List users |
| `user get` | Get user details |
| `user create` | Create user |
| `user update` | Update user |
| `user delete` | Delete user |
| `user enable` | Enable user |
| `user disable` | Disable user |

### Group Commands
| Command | Description |
|---------|-------------|
| `group list` | List groups |
| `group get` | Get group details |
| `group create` | Create group |
| `group delete` | Delete group |
| `group member add` | Add member to group |
| `group member remove` | Remove member from group |

### Task Commands
| Command | Description |
|---------|-------------|
| `task list` | List tasks |
| `task get` | Get task details |
| `task create` | Create task |
| `task execute` | Run task |
| `task cancel` | Cancel running task |
| `task enable` | Enable task |
| `task disable` | Disable task |
| `task wait` | Wait for task completion |
| `task schedule list` | List schedules |
| `task schedule create` | Create schedule |

### System Commands
| Command | Description |
|---------|-------------|
| `system info` | Show system information |
| `system version` | Show version |
| `system settings list` | List settings |
| `system settings get` | Get setting value |
| `system settings set` | Set setting value |
| `system license show` | Show license info |
| `system stats` | Show system stats |

---

## Appendix B: pyvergeos SDK Resource Mapping

| CLI Command Group | SDK Manager | Notes |
|-------------------|-------------|-------|
| `vm` | `client.vms` | Full lifecycle management |
| `network` | `client.networks` | Internal and external |
| `cluster` | `client.clusters` | With tier sub-manager |
| `node` | `client.nodes` | Physical and virtual |
| `tenant` | `client.tenants` | Full tenant management |
| `snapshot` | `client.vm_snapshots`, `client.cloud_snapshots` | Multiple snapshot types |
| `storage tier` | `client.storage_tiers` | Read-only properties |
| `storage file` | `client.files` | Media catalog |
| `nas volume` | `client.nas_volumes` | Volume management |
| `nas share` | `client.nas_cifs_shares`, `client.nas_nfs_shares` | Share types |
| `nas service` | `client.nas_services` | Service control |
| `site-sync` | `client.site_syncs`, `client.site_syncs_incoming` | Both directions |
| `user` | `client.users` | User types: normal, API, VDI |
| `group` | `client.groups` | With member management |
| `permission` | `client.permissions` | Grant/revoke |
| `apikey` | `client.api_keys` | API key management |
| `task` | `client.tasks` | With schedule sub-manager |
| `recipe` | `client.vm_recipes`, `client.tenant_recipes` | Both types |
| `webhook` | `client.webhooks` | Event notifications |
| `certificate` | `client.certificates` | SSL/TLS certs |
| `alarm` | `client.alarms` | System alarms |
| `log` | `client.logs` | System logs |
| `system` | `client.system` | Settings, licenses |

---

## Appendix C: Competitive Analysis

### AWS CLI
**Strengths:**
- Comprehensive coverage
- Excellent documentation
- Wide adoption
- Tab completion

**Patterns to Adopt:**
- `aws <service> <action>` structure
- `--output` format flag
- `--query` for JMESPath filtering
- Profile-based configuration

### Azure CLI
**Strengths:**
- Consistent command structure
- Interactive mode
- Rich help system

**Patterns to Adopt:**
- `az <group> <subgroup> <action>` hierarchy
- `--yes` for confirmation skip
- `--no-wait` for async operations

### kubectl
**Strengths:**
- Declarative and imperative modes
- Namespace context
- Output customization

**Patterns to Adopt:**
- `-o wide` for additional columns
- `get`, `describe`, `delete` verbs
- Context switching

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-02-01 | Claude | Initial draft |
