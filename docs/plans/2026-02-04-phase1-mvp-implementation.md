# Phase 1 MVP Implementation Plan

**Date:** 2026-02-04
**Target:** v0.1.0 MVP
**Status:** Planning

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

### 3. Authentication

**Goal:** Connect to VergeOS using configured credentials.

**Files:**
- `src/verge_cli/auth.py`

**Tasks:**
- [ ] Implement credential resolution order (CLI → env → config → prompt)
- [ ] Implement auth method auto-detection (bearer → api_key → basic)
- [ ] Create `get_client()` function that returns authenticated pyvergeos client
- [ ] Handle authentication errors with proper exit codes

**Acceptance:** `vrg system info` connects and returns system info.

---

### 4. Output Formatting

**Goal:** Display results as table or JSON.

**Files:**
- `src/verge_cli/output.py`

**Tasks:**
- [ ] Implement table formatter using Rich
- [ ] Implement JSON formatter
- [ ] Add `--output` / `-o` global option (table, json)
- [ ] Add `--query` option for simple dot notation extraction
- [ ] Add `--fields` option to pass to API
- [ ] Add `--quiet` / `-q` for minimal output
- [ ] Handle empty results gracefully

**Acceptance:** `vrg vm list -o json` returns valid JSON.

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

### 6. VM Commands

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

**Tasks:**
- [ ] Create `vm` command group
- [ ] Implement `vm list` with filtering
- [ ] Implement `vm get` (by key or name)
- [ ] Implement `vm create`
- [ ] Implement `vm update`
- [ ] Implement `vm delete` with confirmation
- [ ] Implement power operations (start, stop, restart, reset)
- [ ] Add `--wait` option for async operations
- [ ] Add `--yes` to skip confirmation

**Acceptance:** Can create, list, start, stop, and delete a VM.

---

### 7. Network Commands

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
- [ ] Implement `network get`
- [ ] Implement `network create`
- [ ] Implement `network update`
- [ ] Implement `network delete`
- [ ] Implement power operations

**Acceptance:** Can create, list, and manage networks.

---

### 8. System Commands

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

### 9. Global Options & Polish

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

### 10. Testing & CI

**Goal:** Basic test coverage and CI pipeline.

**Tasks:**
- [ ] Set up pytest with unit test structure
- [ ] Add unit tests for config loading
- [ ] Add unit tests for output formatting
- [ ] Add integration tests for VM commands (local only)
- [ ] Set up GitHub Actions for CI (uv, ruff, mypy, pytest unit)
- [ ] Add pre-commit hooks for ruff/mypy

**Acceptance:** CI passes on push.

---

### 11. Documentation & Release

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
6. Error handling returns correct exit codes
7. CI passes (unit tests, ruff, mypy)
8. Package installs via `pip install verge-cli`
