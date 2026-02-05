# Verge CLI

Command-line interface for VergeOS.

[![PyPI version](https://img.shields.io/pypi/v/verge-cli)](https://pypi.org/project/verge-cli/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install verge-cli
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install verge-cli
```

## Quick Start

```bash
# Configure credentials interactively
vrg configure setup

# List VMs
vrg vm list

# Get system info
vrg system info

# Start a VM and wait for it to be running
vrg vm start web-server --wait
```

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

### Authentication Methods

The CLI supports three authentication methods (in priority order):

1. **Bearer Token** - `--token` or `VERGE_TOKEN`
2. **API Key** - `--api-key` or `VERGE_API_KEY`
3. **Basic Auth** - `--username`/`--password` or `VERGE_USERNAME`/`VERGE_PASSWORD`

## Commands

### VM Management

```bash
# List all VMs
vrg vm list

# List running VMs only
vrg vm list --status running

# Get VM details
vrg vm get web-server

# Create a VM
vrg vm create --name my-vm --ram 2048 --cpu 2

# Update a VM
vrg vm update my-vm --ram 4096

# Start/stop/restart VMs
vrg vm start my-vm --wait
vrg vm stop my-vm --wait
vrg vm restart my-vm

# Delete a VM (with confirmation)
vrg vm delete my-vm

# Force delete a running VM
vrg vm delete my-vm --force --yes
```

### Network Management

```bash
# List networks
vrg network list

# Create a network with DHCP
vrg network create --name dev-net --cidr 10.0.0.0/24 --ip 10.0.0.1 --dhcp

# Start/stop networks
vrg network start dev-net
vrg network stop dev-net
```

### System Information

```bash
# Get system info and statistics
vrg system info

# Get VergeOS version
vrg system version
```

### Configuration Management

```bash
# Interactive configuration setup
vrg configure setup

# Show current configuration
vrg configure show

# List all profiles
vrg configure list
```

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

## License

MIT License - see [LICENSE](LICENSE) for details.
