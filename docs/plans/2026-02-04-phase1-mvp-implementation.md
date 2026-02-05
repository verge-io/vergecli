# Phase 1 MVP Implementation Plan

**Date:** 2026-02-04
**Target:** v0.1.0 MVP
**Status:** Planning (Revised)

---

## Overview

Phase 1 delivers a functional CLI for VM and Network management with proper authentication, configuration, and output formatting.

---

## Implementation Order

### 1. Project Skeleton

**Goal:** Set up the project structure with uv and Typer.

```
verge-cli/
├── src/
│   └── verge_cli/
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── README.md
```

**Tasks:**
- [ ] Create `pyproject.toml` with uv, Typer, pyvergeos dependencies
- [ ] Create `src/verge_cli/__init__.py` with version
- [ ] Create `src/verge_cli/__main__.py` entry point
- [ ] Create `src/verge_cli/cli.py` with main Typer app
- [ ] Add `vrg` console script entry point
- [ ] Verify `uv run vrg --help` works

**Acceptance:** `uv run vrg --help` displays help text.

---

### 2. Configuration Management

**Goal:** Load/save config from `~/.vrg/config.toml`.

**Files:**
- `src/verge_cli/config.py`

**Tasks:**
- [ ] Define config schema (host, credentials, output, timeout, verify_ssl)
- [ ] Implement `load_config()` - read from file
- [ ] Implement `get_profile(name)` - get specific profile
- [ ] Implement `save_config()` - write to file
- [ ] Support environment variable overrides (VERGE_HOST, VERGE_TOKEN, etc.)
- [ ] Create `vrg configure` command for interactive setup
- [ ] Create `vrg configure show` to display current config

**Acceptance:** Can create config file and read it back.

---

### 3. Authentication & Context

**Goal:** Connect to VergeOS using configured credentials. Pass context to sub-commands.

**Files:**
- `src/verge_cli/auth.py`
- `src/verge_cli/context.py`

**Design Pattern:**
Use Typer's `ctx.obj` to share state across commands:

```python
@dataclass
class VergeContext:
    config: Config
    client: VergeClient
    output_format: str
    verbosity: int
    quiet: bool

@app.callback()
def main(ctx: typer.Context, profile: str = "default", ...):
    config = load_config(profile)
    client = get_client(config)
    ctx.obj = VergeContext(config=config, client=client, ...)
```

**Tasks:**
- [ ] Create `VergeContext` dataclass to hold config, client, and options
- [ ] Implement credential resolution order (CLI → env → config → prompt)
- [ ] Implement auth method auto-detection (bearer → api_key → basic)
- [ ] Create `get_client()` function that returns authenticated pyvergeos client
- [ ] Wire up `ctx.obj` in main callback
- [ ] Handle authentication errors with proper exit codes

**Acceptance:** `vrg system info` connects and returns system info.

---

### 4. Output Formatting

**Goal:** Display results as table or JSON.

**Files:**
- `src/verge_cli/output.py`

**Design Notes:**
- Use `rich.box.SIMPLE` for tables (copy-paste friendly)
- Check `sys.stdout.isatty()` to disable fancy formatting when piping
- Handle datetime serialization: `json.dumps(data, default=str)`

**Tasks:**
- [ ] Implement table formatter using Rich with `box.SIMPLE`
- [ ] Implement JSON formatter with `default=str` for datetime handling
- [ ] Add `--output` / `-o` global option (table, json)
- [ ] Add `--query` option for simple dot notation extraction
- [ ] Add `--fields` option to pass to API
- [ ] Add `--quiet` / `-q` for minimal output
- [ ] Detect TTY and adjust output (no colors when piping)
- [ ] Handle empty results gracefully

**Acceptance:** `vrg vm list -o json` returns valid JSON, including datetime fields.

---

### 5. Error Handling

**Goal:** Consistent error messages and exit codes.

**Files:**
- `src/verge_cli/errors.py`

**Tasks:**
- [ ] Define exception classes for each exit code
- [ ] Implement error handler that catches exceptions and exits cleanly
- [ ] Add `-v` / `-vv` / `-vvv` verbosity levels
- [ ] Map pyvergeos exceptions to CLI exit codes

**Acceptance:** Invalid commands exit with code 2, not found with code 6.

---

### 6. Utilities (Resolver & Waiter)

**Goal:** Shared utilities for name resolution and async operation waiting.

**Files:**
- `src/verge_cli/utils.py`

#### Name Resolver

**The Problem:** Commands accept `<ID|NAME>` but APIs operate on Keys. Names may not be unique.

**Solution:**
```python
def resolve_resource_id(
    manager: ResourceManager,
    identifier: str,
) -> int:
    """Resolve a name or ID to a resource key.

    Args:
        manager: pyvergeos resource manager (e.g., client.vms)
        identifier: Either a numeric key or a resource name

    Returns:
        Resource key (int)

    Raises:
        NotFoundError: No resource matches
        MultipleMatchesError: Multiple resources match name (exit code 7)
    """
```

**Behavior:**
- If identifier is numeric → assume it's a Key, return as int
- If identifier is a string → search by name
  - 0 matches → raise NotFoundError (exit 6)
  - 1 match → return the Key
  - >1 matches → raise MultipleMatchesError (exit 7), list the matches

#### Waiter Utility

**The Problem:** `--wait` flags need consistent polling with proper timeouts.

**Solution:**
```python
def wait_for_state(
    resource: ResourceObject,
    target_state: str,
    timeout: int = 300,
    interval: float = 2.0,
    backoff: float = 1.5,
    max_interval: float = 10.0,
) -> ResourceObject:
    """Wait for a resource to reach a target state.

    Uses exponential backoff to reduce API load.
    Shows spinner via rich.status.Status.
    """

def wait_for_task(
    client: VergeClient,
    task_key: int,
    timeout: int = 300,
) -> dict:
    """Wait for a task to complete."""
```

**Tasks:**
- [ ] Implement `resolve_resource_id()` with uniqueness check
- [ ] Create `MultipleMatchesError` exception
- [ ] Implement `wait_for_state()` with exponential backoff
- [ ] Implement `wait_for_task()` for async operations
- [ ] Use `rich.status.Status` for spinner feedback during wait

**Acceptance:** Resolving an ambiguous name fails with clear error listing matches.

---

### 7. VM Commands

**Goal:** Full VM lifecycle management.

**Files:**
- `src/verge_cli/commands/vm.py`

**Commands:**
```
vrg vm list [--filter] [--status] [--fields]
vrg vm get <VM>
vrg vm create --name NAME [--cluster] [--ram] [--cpu]
vrg vm update <VM> [--name] [--ram] [--cpu]
vrg vm delete <VM> [--force] [--yes]
vrg vm start <VM> [--wait]
vrg vm stop <VM> [--force] [--wait]
vrg vm restart <VM> [--wait]
vrg vm reset <VM>
```

**Design Notes:**
- Use `resolve_resource_id()` for all `<VM>` arguments
- Use `wait_for_state()` for `--wait` operations
- For `update`: Use Read-Patch-Write pattern if API doesn't support partial updates
  ```python
  # Read current state
  vm = client.vms.get(key)
  # Overlay CLI arguments (only non-None values)
  updates = {k: v for k, v in cli_args.items() if v is not None}
  # Write merged state
  client.vms.update(key, **{**vm, **updates})
  ```

**Tasks:**
- [ ] Create `vm` command group
- [ ] Implement `vm list` with filtering
- [ ] Implement `vm get` using resolver
- [ ] Implement `vm create`
- [ ] Implement `vm update` with read-patch-write pattern
- [ ] Implement `vm delete` with confirmation, using resolver
- [ ] Implement power operations using resolver and waiter
- [ ] Add `--wait` option using `wait_for_state()`
- [ ] Add `--yes` to skip confirmation

**Acceptance:** Can create, list, start, stop, and delete a VM. Ambiguous names fail safely.

---

### 8. Network Commands

**Goal:** Virtual network management.

**Files:**
- `src/verge_cli/commands/network.py`

**Commands:**
```
vrg network list [--type] [--status] [--fields]
vrg network get <NETWORK>
vrg network create --name NAME --type TYPE [--cidr] [--gateway]
vrg network update <NETWORK> [OPTIONS]
vrg network delete <NETWORK> [--yes]
vrg network start <NETWORK>
vrg network stop <NETWORK>
```

**Tasks:**
- [ ] Create `network` command group
- [ ] Implement `network list` with type filtering
- [ ] Implement `network get` using resolver
- [ ] Implement `network create`
- [ ] Implement `network update` with read-patch-write
- [ ] Implement `network delete` using resolver
- [ ] Implement power operations

**Acceptance:** Can create, list, and manage networks.

---

### 9. System Commands

**Goal:** Basic system info for testing connectivity.

**Files:**
- `src/verge_cli/commands/system.py`

**Commands:**
```
vrg system info
vrg system version
```

**Tasks:**
- [ ] Implement `system info`
- [ ] Implement `system version`

**Acceptance:** `vrg system info` returns system details.

---

### 10. Global Options & Polish

**Goal:** Consistent global options across all commands.

**Tasks:**
- [ ] Add `--profile` / `-p` to select config profile
- [ ] Add `--host` / `-H` to override host
- [ ] Add `--no-color` to disable colors
- [ ] Add `--version` to show CLI version
- [ ] Add `--help` to all commands
- [ ] Ensure consistent option naming across commands

**Acceptance:** All global options work on any command.

---

### 11. Testing & CI

**Goal:** Basic test coverage and CI pipeline.

**Mocking Strategy:**
Mock pyvergeos in unit tests so they don't hit real APIs:

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_client(mocker):
    """Mock the SDK client for unit tests."""
    mock = MagicMock()
    mocker.patch("verge_cli.auth.get_client", return_value=mock)
    return mock

@pytest.fixture
def cli_runner():
    """Typer test runner."""
    from typer.testing import CliRunner
    return CliRunner()
```

**Tasks:**
- [ ] Set up pytest with unit test structure
- [ ] Create `conftest.py` with mock fixtures
- [ ] Add unit tests for config loading
- [ ] Add unit tests for output formatting
- [ ] Add unit tests for resolver (mock SDK responses)
- [ ] Add integration tests for VM commands (local only, marked `@pytest.mark.integration`)
- [ ] Set up GitHub Actions for CI (uv, ruff, mypy, pytest unit)
- [ ] Add pre-commit hooks for ruff/mypy

**Acceptance:** CI passes on push. Integration tests run locally with `pytest -m integration`.

---

### 12. Documentation & Release

**Goal:** Package ready for PyPI.

**Tasks:**
- [ ] Write README with installation and quick start
- [ ] Add LICENSE file
- [ ] Configure PyPI metadata in pyproject.toml
- [ ] Test `uv build` produces valid wheel
- [ ] Document environment variables
- [ ] Add CHANGELOG.md

**Acceptance:** `pip install verge-cli` works from test PyPI.

---

## Dependencies

```toml
[project]
dependencies = [
    "pyvergeos>=1.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "tomli>=2.0; python_version<'3.11'",
    "tomli-w>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.0",
    "mypy>=1.0",
    "ruff>=0.1",
]
```

---

## Definition of Done

MVP is complete when:
1. `vrg configure` creates valid config file
2. `vrg vm list/get/create/update/delete/start/stop` all work
3. `vrg network list/get/create/update/delete` all work
4. `vrg system info` shows system details
5. `-o json` and `-o table` work on all list/get commands
6. Ambiguous name resolution fails safely with helpful error
7. `--wait` uses exponential backoff, shows spinner
8. Error handling returns correct exit codes
9. CI passes (unit tests, ruff, mypy)
10. Package installs via `pip install verge-cli`

---

## Risk Mitigations Summary

| Risk | Mitigation |
|------|------------|
| Name vs Key ambiguity | Resolver utility fails on multiple matches |
| Ad-hoc wait loops | Waiter utility with exponential backoff |
| Partial update overwrites | Read-Patch-Write pattern |
| Datetime JSON serialization | `json.dumps(data, default=str)` |
| State passing in Typer | `ctx.obj` with VergeContext dataclass |
| Unit tests hitting real API | Mock pyvergeos in conftest.py |
