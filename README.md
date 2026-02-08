# Verge CLI

Command-line interface for [VergeOS](https://www.verge.io) — manage virtual machines, networks, DNS, firewall rules, and more from your terminal.

[![PyPI version](https://img.shields.io/pypi/v/verge-cli)](https://pypi.org/project/verge-cli/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install verge-cli
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install verge-cli
```

Verify the installation:

```bash
vrg --version
```

## Quick Start

```bash
# 1. Configure credentials
vrg configure setup

# 2. Verify connection
vrg system info

# 3. List your VMs
vrg vm list
```

## Features

- **VM Lifecycle** — create, start, stop, restart, reset, update, and delete virtual machines
- **VM Sub-Resources** — manage drives, NICs, and TPM devices on VMs
- **Network Management** — create and manage internal/external networks with DHCP
- **Firewall Rules** — create, enable, disable, and delete network firewall rules
- **DNS** — manage DNS views, zones, and records (A, CNAME, MX, TXT, etc.)
- **DHCP Host Overrides** — assign static IPs via hostname-based overrides
- **IP Aliases** — add secondary IP addresses to networks
- **Network Diagnostics** — DHCP leases, address tables, and traffic statistics
- **Tenant Management** — full tenant lifecycle with nodes, storage, network blocks, snapshots, and stats
- **Clusters & Nodes** — view cluster and node inventory
- **Storage Tiers** — inspect storage tier capacity and usage
- **Configuration Profiles** — multiple environments with named profiles
- **Multiple Auth Methods** — bearer token, API key, or username/password
- **VM Templates** — declarative YAML templates with variables, dry-run, and batch provisioning
- **Shell Completion** — tab completion for bash, zsh, fish, and PowerShell
- **Flexible Output** — table, wide, JSON, or CSV format with `--query` field extraction

## Command Overview

| Command | Subcommands |
|---------|-------------|
| `vrg vm` | `list`, `get`, `create`, `update`, `delete`, `start`, `stop`, `restart`, `reset`, `validate` |
| `vrg vm drive` | `list`, `get`, `create`, `update`, `delete`, `import` |
| `vrg vm nic` | `list`, `get`, `create`, `update`, `delete` |
| `vrg vm device` | `list`, `get`, `create`, `delete` |
| `vrg network` | `list`, `get`, `create`, `update`, `delete`, `start`, `stop`, `restart`, `status`, `apply-rules`, `apply-dns` |
| `vrg network rule` | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable` |
| `vrg network dns view` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network dns zone` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network dns record` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network host` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network alias` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network diag` | `leases`, `addresses`, `stats` |
| `vrg tenant` | `list`, `get`, `create`, `update`, `delete`, `start`, `stop`, `restart`, `reset`, `clone`, `isolate` |
| `vrg tenant node` | `list`, `get`, `create`, `update`, `delete` |
| `vrg tenant storage` | `list`, `get`, `create`, `update`, `delete` |
| `vrg tenant net-block` | `list`, `get`, `create`, `delete` |
| `vrg tenant ext-ip` | `list`, `get`, `create`, `delete` |
| `vrg tenant l2` | `list`, `get`, `create`, `delete` |
| `vrg tenant snapshot` | `list`, `get`, `create`, `delete`, `restore` |
| `vrg tenant stats` | `current`, `history` |
| `vrg tenant logs` | `list` |
| `vrg cluster` | `list`, `get` |
| `vrg node` | `list`, `get` |
| `vrg storage` | `list`, `get` |
| `vrg system` | `info`, `version` |
| `vrg configure` | `setup`, `show`, `list` |
| `vrg completion` | `show` |

Run `vrg <command> --help` for detailed usage of any command.

> **Destructive operations** (`delete`, `reset`) require `--yes` to skip the confirmation prompt.

## Shell Completion

Tab completion is available for bash, zsh, fish, and PowerShell.

### Bash

```bash
vrg completion show bash >> ~/.bashrc
```

### Zsh

```bash
vrg completion show zsh > "${fpath[1]}/_vrg"
```

### Fish

```bash
vrg completion show fish > ~/.config/fish/completions/vrg.fish
```

### PowerShell

```powershell
vrg completion show powershell >> $PROFILE
```

Restart your shell (or `source` the file) to activate completion.

Alternatively, Typer's built-in flags work for quick setup:

```bash
vrg --install-completion   # auto-detect shell and install
vrg --show-completion      # print script without installing
```

> Dynamic resource name completion (e.g., completing VM names) is not yet available.

## Configuration

### Config File

Configuration is stored in `~/.vrg/config.toml`:

```toml
[default]
host = "https://verge.example.com"
token = "your-api-token"
verify_ssl = true
output = "table"
timeout = 30

[profile.production]
host = "https://verge-prod.example.com"
api_key = "vk_xxxxxxxxxxxx"

[profile.dev]
host = "https://192.168.1.100"
username = "admin"
password = "secret123"
verify_ssl = false
```

### Authentication Methods

The CLI supports three authentication methods (in priority order):

1. **Bearer Token** — `--token` or `VERGE_TOKEN`
2. **API Key** — `--api-key` or `VERGE_API_KEY`
3. **Basic Auth** — `--username`/`--password` or `VERGE_USERNAME`/`VERGE_PASSWORD`

### Environment Variables

All settings can be overridden with environment variables:

| Variable | Description |
|----------|-------------|
| `VERGE_HOST` | VergeOS host URL |
| `VERGE_TOKEN` | Bearer token for authentication |
| `VERGE_API_KEY` | API key for authentication |
| `VERGE_USERNAME` | Username for basic auth |
| `VERGE_PASSWORD` | Password for basic auth |
| `VERGE_PROFILE` | Default profile to use |
| `VERGE_VERIFY_SSL` | Verify SSL certificates (true/false) |
| `VERGE_TIMEOUT` | Request timeout in seconds |
| `VERGE_OUTPUT` | Default output format (table/wide/json/csv) |

## Output Formats

### Table (default)

```bash
vrg vm list
```

### Wide

Shows all columns including those hidden in the default table view:

```bash
vrg -o wide vm list
```

### JSON

```bash
vrg -o json vm list
```

### CSV

Machine-readable output for piping to other tools:

```bash
vrg -o csv vm list
```

### Field Extraction

Extract specific fields using dot notation:

```bash
# Get just the status
vrg --query status vm get web-server

# Get nested field
vrg --query config.ram vm get web-server
```

## VM Templates

Create VMs from declarative `.vrg.yaml` files instead of long command lines.

### Template Structure

```yaml
apiVersion: v4
kind: VirtualMachine

vm:
  name: web-server-01
  os_family: linux
  cpu_cores: 4
  ram: 8GB
  machine_type: q35
  uefi: true

  drives:
    - name: "OS Disk"
      media: disk
      interface: virtio-scsi
      size: 50GB

  nics:
    - name: "Primary"
      interface: virtio
      network: External

  devices:
    - type: tpm
      model: crb
      version: "2.0"

  cloudinit:
    datasource: nocloud
    files:
      - name: user-data
        content: |
          #cloud-config
          hostname: web-server-01
          packages: [nginx]
```

### Usage

```bash
# Validate a template
vrg vm validate -f web-server.vrg.yaml

# Preview without creating
vrg vm create -f web-server.vrg.yaml --dry-run

# Create from template
vrg vm create -f web-server.vrg.yaml

# Override values at create time
vrg vm create -f web-server.vrg.yaml --set vm.name=web-02 --set vm.ram=16GB
```

### Variables

Templates support `${VAR}` substitution from environment variables or a `vars:` block. Use `${VAR:-default}` for optional variables with defaults.

```yaml
vars:
  env: staging
vm:
  name: "${env}-web-01"
  ram: "${VM_RAM:-4GB}"
```

### Batch Provisioning

Use `kind: VirtualMachineSet` to create multiple VMs from shared defaults. Each VM in `vms:` inherits from `defaults:` and can override any field.

```bash
vrg vm create -f k8s-cluster.vrg.yaml --dry-run
```

See the [Template Guide](docs/templates.md) for the full field reference, cloud-init, variables, and more examples.

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--profile` | `-p` | Configuration profile to use |
| `--host` | `-H` | VergeOS host URL (override) |
| `--output` | `-o` | Output format (table, wide, json, csv) |
| `--query` | | Extract field using dot notation |
| `--verbose` | `-v` | Increase verbosity (-v, -vv, -vvv) |
| `--quiet` | `-q` | Suppress non-essential output |
| `--no-color` | | Disable colored output |
| `--version` | `-V` | Show version |
| `--help` | | Show help |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |
| 4 | Authentication error |
| 5 | Permission denied |
| 6 | Resource not found |
| 7 | Conflict (e.g., duplicate name) |
| 8 | Validation error |
| 9 | Timeout |
| 10 | Connection error |

## Development

```bash
# Clone the repository
git clone https://github.com/verge-io/verge-cli.git
cd verge-cli

# Install with development dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Run type checker
uv run mypy src/verge_cli

# Build package
uv build
```

## Documentation

- [Template Guide](docs/templates.md) — Full template language reference
- [Cookbook](docs/cookbook.md) — Task-oriented recipes for common workflows
- [Changelog](CHANGELOG.md) — Version history
- [Known Issues](docs/KNOWN_ISSUES.md) — Current limitations and workarounds

## License

MIT License — see [LICENSE](LICENSE) for details.
