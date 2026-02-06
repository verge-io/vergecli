# Verge CLI

> Command-line interface for VergeOS, wrapping the pyvergeos SDK to provide scriptable infrastructure management.

A Python CLI for managing VergeOS virtual machines, networks, tenants, storage, and more. Targets system administrators, DevOps engineers, and MSPs who need terminal-based automation.

**Status:** Phase 1 MVP complete — see `docs/plans/2026-02-04-phase1-mvp-implementation.md` for task checklist.

## Tech Stack

- **Language**: Python 3.10+
- **Package Manager**: uv (with pip/pipx for installation)
- **CLI Framework**: Typer with Rich for output formatting
- **SDK**: pyvergeos (full API wrapper)
- **Config Format**: TOML (`~/.vrg/config.toml`)
- **Testing**: pytest with pytest-mock, pytest-cov
- **Linting**: ruff (replaces flake8, isort, pyupgrade)
- **Type Checking**: mypy (strict mode)

## Project Structure

```text
verge-cli/
├── src/verge_cli/
│   ├── __init__.py         # Version string
│   ├── __main__.py         # Entry point for `python -m verge_cli`
│   ├── cli.py              # Main Typer app, global options, context setup
│   ├── config.py           # TOML config loading/saving, env var handling
│   ├── auth.py             # pyvergeos client creation with credentials
│   ├── context.py          # VergeContext dataclass passed to commands
│   ├── columns.py          # ColumnDef system for table column definitions
│   ├── output.py           # Table/JSON/CSV formatters with Rich
│   ├── errors.py           # Exception classes and exit code mapping
│   ├── utils.py            # Resolver (name→key) and waiter utilities
│   ├── template/           # VM template subsystem
│   │   ├── builder.py      # Builds VM + sub-resources from parsed template
│   │   ├── loader.py       # YAML loading, variable substitution, --set merging
│   │   ├── resolver.py     # Name→key resolution for template references
│   │   ├── schema.py       # JSON schema validation for .vrg.yaml files
│   │   └── units.py        # Unit conversion (e.g., "4GB" → 4096 MB)
│   ├── schemas/
│   │   └── vrg-vm-template.schema.json  # JSON schema for .vrg.yaml
│   └── commands/
│       ├── configure.py    # `vrg configure` command
│       ├── system.py       # `vrg system` commands
│       ├── vm.py           # `vrg vm` commands (CRUD + power + template create)
│       ├── vm_drive.py     # `vrg vm drive` sub-resource commands
│       ├── vm_nic.py       # `vrg vm nic` sub-resource commands
│       ├── vm_device.py    # `vrg vm device` sub-resource commands
│       ├── network.py      # `vrg network` commands
│       ├── network_rule.py # `vrg network rule` commands
│       ├── network_dns.py  # `vrg network dns` commands
│       ├── network_host.py # `vrg network host` commands
│       ├── network_alias.py # `vrg network alias` commands
│       └── network_diag.py # `vrg network diag` commands
├── tests/
│   ├── conftest.py         # Shared fixtures (cli_runner, mock_client, etc.)
│   ├── unit/               # Unit tests (mock SDK, ~28 test files)
│   └── integration/        # Integration tests (real API, marked)
├── docs/
│   ├── cookbook.md          # Task-oriented recipes
│   ├── templates.md        # Template language reference
│   ├── KNOWN_ISSUES.md     # Current limitations and workarounds
│   └── plans/              # Implementation plans
├── .claude/
│   ├── PRD.md              # Full product requirements
│   └── skills/             # Claude Code skills
└── pyproject.toml          # Project metadata, dependencies, tool config
```

## Commands

```bash
# Install dependencies
uv sync

# Run CLI during development
uv run vrg --help
uv run vrg configure
uv run vrg vm list

# Run all tests
uv run pytest

# Run unit tests only (fast, no API)
uv run pytest tests/unit/

# Run integration tests (requires VERGE_HOST, VERGE_TOKEN)
uv run pytest -m integration

# Run single test file
uv run pytest tests/unit/test_config.py -v

# Linting
uv run ruff check
uv run ruff check --fix

# Format checking (CI enforces this)
uv run ruff format --check .
uv run ruff format .          # auto-format

# Type checking
uv run mypy src/verge_cli

# Build package
uv build
```

## Reference Documentation

| Document | When to Read |
|----------|--------------|
| `.claude/PRD.md` | Full requirements, command reference, API mapping |
| `README.md` | Installation, quick start, command overview |
| `docs/templates.md` | Template language reference (.vrg.yaml format) |
| `docs/cookbook.md` | Task-oriented recipes for common workflows |
| `docs/KNOWN_ISSUES.md` | Current limitations and workarounds |

## Architecture

### Context Pattern

Global options (`--profile`, `--host`, `--output`, etc.) are parsed in `cli.py`'s main callback and stored in `ctx.obj`. Commands call `get_context(ctx)` to get a `VergeContext` with a lazily-created pyvergeos client.

```python
# In a command:
from verge_cli.context import get_context
from verge_cli.output import output_result

@app.command()
def list(ctx: typer.Context):
    vctx = get_context(ctx)  # Gets authenticated client
    vms = vctx.client.vms.list()
    output_result(
        [_vm_to_dict(v) for v in vms],  # Convert SDK objects to dicts
        columns=COLUMNS,                 # ColumnDef list for table/csv
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Name Resolution

Commands accept `<ID|NAME>` arguments. Use `resolve_resource_id()` from `utils.py`:
- Numeric strings → treated as Key, returned as int
- Text strings → search by name via SDK
- 0 matches → `NotFoundError` (exit 6)
- 1 match → return Key
- Multiple matches → `MultipleMatchesError` (exit 7, conflict), list matches

### Credential Resolution Order

1. CLI arguments (`--token`, `--api-key`, `--username/--password`)
2. Environment variables (`VERGE_HOST`, `VERGE_TOKEN`, etc.)
3. Profile in config file
4. Default profile
5. Interactive prompt (future)

### Template System

The `verge_cli.template` package handles `.vrg.yaml` template-based VM creation:

| Module | Responsibility |
|--------|----------------|
| `units.py` | Parses human-friendly sizes like `"4GB"` → `4096` MB |
| `resolver.py` | Resolves template name references (network, tier) to API keys |
| `loader.py` | YAML loading, `${VAR}` substitution, `--set` override merging |
| `schema.py` | Validates templates against `schemas/vrg-vm-template.schema.json` |
| `builder.py` | Orchestrates VM + drives + NICs + devices + cloud-init creation |

Template flow: `loader.py` → `schema.py` → `resolver.py` → `builder.py`

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |
| 4 | Authentication error |
| 5 | Permission denied |
| 6 | Resource not found |
| 7 | Conflict (duplicate name) |
| 8 | Validation error |
| 9 | Timeout error |
| 10 | Connection error |

## Code Conventions

### ColumnDef System

All command output uses `ColumnDef` from `verge_cli.columns` to define table columns. Each command module defines a `COLUMNS` list:

```python
from verge_cli.columns import ColumnDef

COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map={"running": "green", "stopped": "red"}),
    ColumnDef("description", wide_only=True),  # Only shown in -o wide
]
```

`ColumnDef` supports:
- `header` — Custom display header (defaults to title-cased key)
- `wide_only` — Only shown in `wide` output format
- `style_map` — Dict mapping values to Rich styles
- `style_fn` — Callable `(value, row) -> style` for dynamic styling
- `format_fn` — Callable `(value, for_csv=False) -> str` for custom formatting
- `normalize_fn` — Callable to normalize values before style lookup

### Output Formatting

Use `rich.box.SIMPLE` for tables (copy-paste friendly). Check `sys.stdout.isatty()` to disable fancy formatting when piping.

Output helpers in `verge_cli.output`:
- `output_result(data, ...)` — Main output dispatcher (table/wide/json/csv)
- `output_success(message, ...)` — Green checkmark success message
- `output_error(message, ...)` — Red error message to stderr
- `output_warning(message, ...)` — Yellow warning message

### Waiting on Async Operations

Use `wait_for_state()` from `utils.py` with exponential backoff:
```python
wait_for_state(vm, target_state="running", timeout=300, interval=2.0, backoff=1.5)
```

### Update Operations

Use read-patch-write pattern when API doesn't support partial updates:
```python
current = client.vms.get(key)
updates = {k: v for k, v in cli_args.items() if v is not None}
client.vms.update(key, **{**current, **updates})
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `VERGE_HOST` | VergeOS host URL |
| `VERGE_TOKEN` | Bearer token |
| `VERGE_API_KEY` | API key |
| `VERGE_USERNAME` | Username for basic auth |
| `VERGE_PASSWORD` | Password for basic auth |
| `VERGE_PROFILE` | Default profile name |
| `VERGE_OUTPUT` | Default output format |
| `VERGE_VERIFY_SSL` | SSL verification (true/false) |
| `VERGE_TIMEOUT` | Request timeout in seconds |

## Adding a New Command Group

### Step 1: Create Command Module

Create `src/verge_cli/commands/<resource>.py`:

```python
"""<Resource> management commands."""
import typer
from verge_cli.columns import ColumnDef
from verge_cli.context import get_context
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(help="Manage <resources>.")

# Define columns for table/wide/csv output
COLUMNS: list[ColumnDef] = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map={"running": "green", "stopped": "red"}),
    ColumnDef("description", wide_only=True),
]

def _to_dict(obj: object) -> dict:
    """Convert SDK object to dict for output."""
    return {
        "$key": obj.key,
        "name": obj.name,
        "status": obj.get("status"),
        "description": obj.get("description"),
    }

@app.command("list")
def list_resources(ctx: typer.Context):
    """List all <resources>."""
    vctx = get_context(ctx)
    items = vctx.client.<resources>.list()
    output_result(
        [_to_dict(i) for i in items],
        columns=COLUMNS,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )

@app.command()
def get(ctx: typer.Context, identifier: str):
    """Get <resource> by ID or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.<resources>, identifier)
    item = vctx.client.<resources>.get(key)
    output_result(
        _to_dict(item),
        columns=COLUMNS,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 2: Register in cli.py

```python
from verge_cli.commands import <resource>
app.add_typer(<resource>.app, name="<resource>")
```

### Step 3: Add Tests

Create `tests/unit/test_<resource>.py` with mocked SDK responses.

## Testing Strategy

- **Unit tests**: Mock pyvergeos client in `conftest.py`, test command logic
- **Integration tests**: Mark with `@pytest.mark.integration`, require env vars
- **Coverage target**: 90% on critical paths (auth, CRUD)

### Test Commands

```bash
uv run pytest                           # All tests
uv run pytest tests/unit/               # Unit tests only
uv run pytest -m integration            # Integration tests (needs VERGE_HOST, VERGE_TOKEN)
uv run pytest -m "not integration"      # Skip integration tests
uv run pytest tests/unit/test_vm.py -v  # Single file with verbose
uv run pytest -k "test_list"            # Tests matching pattern
```

### Available Test Fixtures

From `tests/conftest.py`:

| Fixture | Purpose |
|---------|---------|
| `cli_runner` | Typer's `CliRunner` for invoking CLI commands |
| `mock_client` | Mocked pyvergeos client (patches `verge_cli.auth.get_client`) |
| `mock_vm` | Mock VM object with standard attributes |
| `mock_network` | Mock Network object with standard attributes |
| `mock_dns_view` | Mock DNS View object with standard attributes |
| `mock_drive` | Mock Drive object (VM sub-resource) |
| `mock_nic` | Mock NIC object (VM sub-resource) |
| `mock_device` | Mock Device/TPM object (VM sub-resource) |
| `temp_config_dir` | Temporary `~/.vrg` directory |
| `sample_config_file` | Pre-populated test config file |

### Example Test Pattern

```python
def test_vm_list(cli_runner, mock_client, mock_vm):
    mock_client.vms.list.return_value = [mock_vm]

    result = cli_runner.invoke(app, ["vm", "list"])

    assert result.exit_code == 0
    assert "test-vm" in result.output
    mock_client.vms.list.assert_called_once()
```
