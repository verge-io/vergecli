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
- **Network Management** — create and manage internal/external networks with DHCP
- **Firewall Rules** — create, enable, disable, and delete network firewall rules
- **DNS** — manage DNS views, zones, and records (A, CNAME, MX, TXT, etc.)
- **DHCP Host Overrides** — assign static IPs via hostname-based overrides
- **IP Aliases** — add secondary IP addresses to networks
- **Network Diagnostics** — ping, traceroute, DNS lookup from within networks
- **Configuration Profiles** — multiple environments with named profiles
- **Multiple Auth Methods** — bearer token, API key, or username/password
- **Flexible Output** — table or JSON format with `--query` field extraction

## Command Overview

| Command | Subcommands |
|---------|-------------|
| `vrg vm` | `list`, `get`, `create`, `update`, `delete`, `start`, `stop`, `restart`, `reset`, `status` |
| `vrg network` | `list`, `get`, `create`, `update`, `delete`, `start`, `stop`, `restart`, `status`, `apply-rules`, `apply-dns` |
| `vrg network rule` | `list`, `get`, `create`, `update`, `delete`, `enable`, `disable` |
| `vrg network dns zone` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network dns record` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network dns view` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network host` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network alias` | `list`, `get`, `create`, `update`, `delete` |
| `vrg network diag` | `ping`, `traceroute`, `dns`, `resolve` |
| `vrg system` | `info`, `version` |
| `vrg configure` | `setup`, `show`, `list`, `remove` |

Run `vrg <command> --help` for detailed usage of any command.

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
| `VERGE_OUTPUT` | Default output format (table/json) |

## Output Formats

### Table (default)

```bash
vrg vm list
```

### JSON

```bash
vrg vm list -o json
```

### Field Extraction

Extract specific fields using dot notation:

```bash
# Get just the status
vrg vm get web-server --query status

# Get nested field
vrg vm get web-server --query config.ram
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--profile` | `-p` | Configuration profile to use |
| `--host` | `-H` | VergeOS host URL (override) |
| `--output` | `-o` | Output format (table, json) |
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

- [Cookbook](docs/cookbook.md) — Task-oriented recipes for common workflows
- [Changelog](CHANGELOG.md) — Version history
- [Known Issues](docs/KNOWN_ISSUES.md) — Current limitations and workarounds

## License

MIT License — see [LICENSE](LICENSE) for details.
