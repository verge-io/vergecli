# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Breaking:** JSON output key field renamed from `"key"` to `"$key"` across all resources. CSV header displays as `"Key"`.
- `"Key"` column is now visible by default in table output (previously wide-only).
- `vrg vm reset` and `vrg tenant reset` now require `--yes` to skip confirmation prompt.

### Fixed
- Added `"maintenance"` status style (renders yellow) for node maintenance state.
- Consolidated duplicate percent-threshold style helpers into single `style_percent_threshold` function.
- Removed duplicate `mock_tenant` test fixtures; consolidated to shared conftest fixture.
- Guarded optional `hostname` kwarg in `ext_ip_create` to avoid passing `None` to SDK.

## [0.1.0] - 2026-02-04

### Added

- Initial release of Verge CLI
- Configuration management with profiles and environment variable overrides
- VM commands: list, get, create, update, delete, start, stop, restart, reset
- Network commands: list, get, create, update, delete, start, stop
- System commands: info, version
- Multiple authentication methods: Bearer token, API key, Basic auth
- Output formats: table (default) and JSON
- Field extraction with `--query` option (dot notation)
- Resource name resolution with disambiguation for duplicate names
- Wait functionality with exponential backoff for async operations
- Configurable verbosity levels (-v, -vv, -vvv)
- Consistent exit codes for different error types
- Shell completion support (bash, zsh, fish)

### Configuration

- Config file location: `~/.vrg/config.toml`
- Support for multiple profiles
- Environment variable overrides (VERGE_HOST, VERGE_TOKEN, etc.)

### Dependencies

- pyvergeos >= 1.0.0
- typer >= 0.9.0
- rich >= 13.0.0
