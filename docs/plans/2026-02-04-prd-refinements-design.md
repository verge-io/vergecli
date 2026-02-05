# Verge CLI - PRD Refinements Design

**Date:** 2026-02-04
**Status:** Approved

This document captures design decisions made during brainstorming to refine the original PRD.

---

## CLI Framework

**Decision:** Use **Typer** (built on Click)

**Rationale:**
- Less boilerplate for the ~30 resource types with similar CRUD patterns
- Type hints reduce repetition and improve IDE support
- Built on Click, so we can drop down to Click's API when finer control is needed
- Cross-platform (pure Python)
- Achieves the same end-user experience as AWS/Azure CLI patterns

---

## Authentication & Configuration

### Config File

**Location:** `~/.vrg/config.toml` (single file)

**Structure:**
```toml
[default]
host = "https://verge.example.com"
token = "eyJhbGciOiJIUzI1..."  # Bearer token (highest priority)
verify_ssl = true
output = "table"
timeout = 30

[profile.production]
host = "https://verge-prod.example.com"
api_key = "vk_xxxxxxxxxxxx"  # API key (second priority)

[profile.dev]
host = "https://192.168.1.100"
username = "admin"           # Basic auth (third priority)
password = "secret123"
verify_ssl = false
```

### Auth Methods

Supported methods (auto-detected from fields present):
1. **Bearer token** - `token` field (highest priority)
2. **API key** - `api_key` field
3. **Basic auth** - `username` + `password` fields (lowest priority)

### Credential Resolution Order

1. Command-line arguments (`--token`, `--api-key`, `--username/--password`)
2. Environment variables (`VERGE_TOKEN`, `VERGE_API_KEY`, `VERGE_USERNAME/VERGE_PASSWORD`)
3. Profile in config file (via `--profile` or `VERGE_PROFILE`)
4. Default profile
5. Interactive prompt (if TTY)

### Secure Storage

Deferred to post-MVP. v1.0 uses plaintext config file only.

---

## Output Formatting

### Default Format

**Table** - Human-friendly for interactive use. Users add `-o json` for scripting.

### Supported Formats (v1.0)

- **Table** (default)
- **JSON**

Additional formats (YAML, CSV) deferred to later versions.

### Query Filtering

Simple dot notation for extracting specific fields:

```bash
vrg vm get web-server-01 --query status
# Returns: running
```

JMESPath deferred to later versions.

### Field Selection

Pass directly to VergeOS API:

```bash
vrg vm list                      # SDK default fields
vrg vm list --fields most        # API returns "most" fields
vrg vm list --fields all         # API returns all fields
vrg vm list --fields name,status # Specific fields only
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

### Error Messages

Simple format without suggestions:

```
Error: VM 'nonexistent' not found.
```

### Verbosity Levels

Stackable flags:
- `-v` - Info level
- `-vv` - Debug level
- `-vvv` - Trace level (full API request/response)

### Quiet Mode

`--quiet` / `-q` - Suppress all output except errors and requested data.

---

## Testing Strategy

### Approach

**Integration-heavy** - Most tests run against real VergeOS test systems.

### Test Environments

| System | URL | Purpose |
|--------|-----|---------|
| DEV System 1 | https://192.168.10.75 | Primary testing |
| DEV System 2 | https://192.168.10.85 | VPN and Sites testing |

### CI/CD

- **Unit tests** - Run in CI (no live system access required)
- **Linting** - Run in CI
- **Integration tests** - Run locally only against dev systems

### Tools

| Tool | Purpose |
|------|---------|
| pytest | Test framework |
| ruff | Linting and formatting |
| mypy | Type checking |
| uv | Package management (local and CI) |

---

## Development Tooling

### Package Manager

**uv** - Used for all local development and CI.

```bash
# Local development
uv sync              # Install dependencies
uv run pytest        # Run tests
uv run ruff check    # Run linter
uv run mypy .        # Run type checker

# CI
uv sync --frozen
uv run pytest tests/unit
uv run ruff check
uv run mypy .
```

---

## Summary of Changes from Original PRD

| Area | Original | Refined |
|------|----------|---------|
| CLI Framework | "Click or Typer" (undecided) | Typer |
| Config files | Two files possible | Single `~/.vrg/config.toml` |
| Auth method selection | Not specified | Auto-detect by field presence |
| Auth priority | Not specified | Bearer → API key → Basic |
| Default output | Table | Table (confirmed) |
| Output formats (v1.0) | Table, JSON, YAML, CSV | Table, JSON only |
| Query filtering | JMESPath mentioned | Simple dot notation |
| Field selection | Not detailed | Pass to API (`most`, `all`, specific) |
| Secure storage | Keyring integration | Deferred to post-MVP |
| Testing strategy | General coverage targets | Integration-heavy, local only |
| Package manager | pip/pipx | uv |
