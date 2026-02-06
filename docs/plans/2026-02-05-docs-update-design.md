# Documentation Update Design

> Post-MVP documentation refresh: README rewrite, cookbook, CLAUDE.md audit.

**Date:** 2026-02-05
**Status:** Approved

## Deliverables

### 1. README.md Rewrite

**Audience:** MSPs, sysadmins, DevOps engineers evaluating the tool.

**Structure:**

1. **Hero** — One-liner, badges (version, Python 3.10+, license), short description of what verge-cli does (wraps pyvergeos SDK for terminal-based VergeOS management).

2. **Installation** — `pip install verge-cli` and `uv tool install verge-cli`, verify with `vrg --version`.

3. **Quick Start** — 3 steps: install → `vrg configure setup` → `vrg vm list`.

4. **Features** — Bulleted list of implemented capabilities:
   - VM lifecycle (create, start, stop, restart, reset, delete)
   - Network management (create, start, stop, restart)
   - Firewall rules (create, enable, disable, delete)
   - DNS management (views, zones, records)
   - DHCP host overrides
   - IP aliases
   - Network diagnostics (ping, traceroute, DNS lookup)
   - Configuration profiles with multiple auth methods
   - Table and JSON output with `--query` field extraction

5. **Command Overview** — Compact table: command group → subcommands.

6. **Configuration** — Auth methods (token, API key, basic auth), env vars, profile management.

7. **Output Formats** — Table vs JSON vs `--query` examples.

8. **Exit Codes** — Table matching actual `errors.py` implementation.

9. **Global Options** — Table of `--profile`, `--host`, `--output`, etc.

10. **Development** — Clone, `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run mypy`, `uv build`.

11. **Links** — Cookbook, CHANGELOG, known issues, license.

**Changes from current README:**
- Add Features section (missing)
- Add full Command Overview table (current version only shows examples for some commands)
- Fix Python badge from 3.9+ to 3.10+
- Remove network commands section duplication with Command Overview
- Keep Development section but ensure all commands use `uv run`
- Add link to cookbook docs

### 2. docs/cookbook.md

**Format:** 4 task-oriented recipes, each following:
- **Goal** — one sentence
- **Steps** — numbered commands with explanation
- **Verify** — confirmation command
- **Cleanup** — teardown (optional)

**Recipes:**

1. **Getting Started** — Install, `vrg configure setup`, verify with `vrg system info`, mention env vars as alternative.

2. **Managing Virtual Machines** — `vrg vm create`, `vrg vm get`, `vrg vm start --wait`, `vrg vm list --status running`, `vrg vm update`, `vrg vm stop`, `vrg vm delete --force --yes`.

3. **Setting Up a Network** — `vrg network create`, `vrg network rule create` (allow SSH), `vrg network host create` (static lease), verify with `vrg network diag ping`.

4. **Configuring DNS** — `vrg network dns view create`, `vrg network dns zone create`, `vrg network dns record create` (A record, CNAME), `vrg network apply-dns`, verify with `vrg network diag dns`.

**Size:** ~30-50 lines per recipe, ~150-200 lines total.

### 3. CLAUDE.md Audit (root only, do NOT touch .claude/CLAUDE.md)

**Specific fixes:**

| Section | Current | Corrected |
|---------|---------|-----------|
| Tech Stack | Python 3.9+ | Python 3.10+ |
| Exit code 5 | Authorization error | Permission denied |
| Exit code 7 | Multiple matches (ambiguous name) | Conflict (duplicate name) |
| Name Resolution bullet 4 | `MultipleMatchesError` (exit 7), list matches | `MultipleMatchesError` (exit 7, conflict), list matches |
| Project structure commands/ | Only shows `configure.py` and `...` | Lists all 9 command files |
| Test fixtures table | Missing `mock_dns_view` | Add `mock_dns_view` fixture |
| Status line | "Phase 1 MVP in progress" | "Phase 1 MVP complete" |

**Ensure all examples use `uv run`:** Audit every bash code block — currently they already use `uv run` but verify nothing was missed.

## Files Modified

- `README.md` — full rewrite
- `docs/cookbook.md` — new file
- `CLAUDE.md` — targeted corrections

## Files NOT Modified

- `.claude/CLAUDE.md` — shared company file, do not touch
