# Verge CLI

> Command-line interface for VergeOS, wrapping the pyvergeos SDK to provide scriptable infrastructure management.

A Python CLI for managing VergeOS virtual machines, networks, tenants, storage, and more. Targets system administrators, DevOps engineers, and MSPs who need terminal-based automation.

## Tech Stack

- **Language**: Python 3.9+
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
│   ├── output.py           # Table/JSON formatters with Rich
│   ├── errors.py           # Exception classes and exit code mapping
│   ├── utils.py            # Resolver (name→key) and waiter utilities
│   └── commands/
│       ├── configure.py    # `vrg configure` command
│       └── ...             # Future: vm.py, network.py, tenant.py, etc.
├── tests/
│   ├── conftest.py         # Shared fixtures (cli_runner, mock_client)
│   ├── unit/               # Unit tests (mock SDK)
│   └── integration/        # Integration tests (real API, marked)
├── docs/plans/             # Implementation plans
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

# Type checking
uv run mypy .

# Build package
uv build
```

## Reference Documentation

| Document | When to Read |
|----------|--------------|
| `.claude/PRD.md` | Full requirements, command reference, API mapping |
| `docs/plans/2026-02-04-phase1-mvp-implementation.md` | Current implementation plan with task checklist |
| `README.md` | Installation and quick start |

## Architecture

### Context Pattern

Global options (`--profile`, `--host`, `--output`, etc.) are parsed in `cli.py`'s main callback and stored in `ctx.obj`. Commands call `get_context(ctx)` to get a `VergeContext` with a lazily-created pyvergeos client.

```python
# In a command:
from verge_cli.cli import get_context

@app.command()
def list(ctx: typer.Context):
    vctx = get_context(ctx)  # Gets authenticated client
    vms = vctx.client.vms.list()
    output_result(vctx, vms)
```

### Name Resolution

Commands accept `<ID|NAME>` arguments. Use `resolve_resource_id()` from `utils.py`:
- Numeric strings → treated as Key, returned as int
- Text strings → search by name via SDK
- 0 matches → `NotFoundError` (exit 6)
- 1 match → return Key
- Multiple matches → `MultipleMatchesError` (exit 7), list matches

### Credential Resolution Order

1. CLI arguments (`--token`, `--api-key`, `--username/--password`)
2. Environment variables (`VERGE_HOST`, `VERGE_TOKEN`, etc.)
3. Profile in config file
4. Default profile
5. Interactive prompt (future)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Configuration error |
| 4 | Authentication error |
| 5 | Authorization error |
| 6 | Resource not found |
| 7 | Multiple matches (ambiguous name) |
| 8 | Validation error |
| 9 | Timeout error |
| 10 | Connection error |

## Code Conventions

### Output Formatting

Use `rich.box.SIMPLE` for tables (copy-paste friendly). Check `sys.stdout.isatty()` to disable fancy formatting when piping. For JSON, use `json.dumps(data, default=str)` to handle datetime serialization.

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
from verge_cli.cli import get_context
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(help="Manage <resources>.")

@app.command("list")
def list_resources(ctx: typer.Context):
    """List all <resources>."""
    vctx = get_context(ctx)
    items = vctx.client.<resources>.list()
    output_result(vctx, items)

@app.command()
def get(ctx: typer.Context, identifier: str):
    """Get <resource> by ID or name."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.<resources>, identifier)
    item = vctx.client.<resources>.get(key)
    output_result(vctx, item)
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

```python
# tests/conftest.py pattern
@pytest.fixture
def mock_client(mocker):
    mock = MagicMock()
    mocker.patch("verge_cli.auth.get_client", return_value=mock)
    return mock
```
