# Testing

Test strategy, fixtures, and commands for the Verge CLI test suite.

## Strategy

- **Unit tests** — Mock pyvergeos client via `conftest.py`, test command logic and output
- **Integration tests** — Mark with `@pytest.mark.integration`, require real API credentials
- **Coverage target** — 90% on critical paths (auth, CRUD, name resolution)

## Running Tests

```bash
# All tests
uv run pytest

# Unit tests only (fast, no API needed)
uv run pytest tests/unit/

# Integration tests (requires VERGE_HOST + auth env vars)
uv run pytest -m integration

# Skip integration tests
uv run pytest -m "not integration"

# Single test file
uv run pytest tests/unit/test_vm.py -v

# Tests matching a pattern
uv run pytest -k "test_list"

# With coverage report
uv run pytest --cov=verge_cli --cov-report=term-missing
```

## Linting & Type Checking

```bash
# Lint (check for issues)
uv run ruff check

# Lint (auto-fix)
uv run ruff check --fix

# Format check (CI enforces this)
uv run ruff format --check .

# Auto-format
uv run ruff format .

# Type check (strict mode)
uv run mypy src/verge_cli
```

## Test Organization

```
tests/
├── conftest.py         # Shared fixtures (mock client, mock resources)
├── unit/               # Unit tests — one file per command module
│   ├── test_vm.py
│   ├── test_vm_drive.py
│   ├── test_network.py
│   ├── test_tenant.py
│   └── ...             # ~50+ test files
├── integration/        # Integration tests (real API)
└── shakedown/          # End-to-end shakedown scripts
```

## Available Fixtures

From `tests/conftest.py`:

### Core Fixtures

| Fixture | Purpose |
|---------|---------|
| `cli_runner` | Typer's `CliRunner` for invoking CLI commands |
| `mock_client` | Mocked pyvergeos client (patches `verge_cli.auth.get_client`) |
| `temp_config_dir` | Temporary `~/.vrg` directory |
| `sample_config_file` | Pre-populated test config file |

### Resource Fixtures

| Fixture | Purpose |
|---------|---------|
| `mock_vm` | Mock VM object with standard attributes |
| `mock_network` | Mock Network object |
| `mock_dns_view` | Mock DNS View object |
| `mock_drive` | Mock VM Drive object |
| `mock_nic` | Mock VM NIC object |
| `mock_device` | Mock VM Device/TPM object |
| `mock_tenant` | Mock Tenant object with sub-managers |
| `mock_cluster` | Mock Cluster object |
| `mock_node` | Mock Node object |
| `mock_storage_tier` | Mock Storage Tier object |
| `mock_nas_service` | Mock NAS Service object |
| `mock_nas_volume` | Mock NAS Volume object |
| `mock_nas_volume_snapshot` | Mock NAS Volume Snapshot object |
| `mock_cifs_share` | Mock CIFS Share object |
| `mock_nfs_share` | Mock NFS Share object |
| `mock_nas_user` | Mock NAS User object |
| `mock_nas_sync` | Mock NAS Sync Job object |
| `mock_nas_file` | Mock NAS file entry (dict) |
| `mock_nas_dir` | Mock NAS directory entry (dict) |
| `mock_recipe` | Mock VM Recipe object |
| `mock_recipe_section` | Mock Recipe Section object |
| `mock_recipe_question` | Mock Recipe Question object |
| `mock_recipe_instance` | Mock Recipe Instance object |
| `mock_recipe_log` | Mock Recipe Log entry |
| `mock_user` | Mock User object |
| `mock_group` | Mock Group object |
| `mock_group_member` | Mock Group Member object |
| `mock_permission` | Mock Permission object |
| `mock_api_key` | Mock API Key object |
| `mock_api_key_created` | Mock API Key creation response |
| `mock_auth_source` | Mock Auth Source object |
| `mock_task` | Mock Task object |
| `mock_task_schedule` | Mock Task Schedule object |
| `mock_task_trigger` | Mock Task Trigger object |
| `mock_task_event` | Mock Task Event object |
| `mock_task_script` | Mock Task Script object |
| `mock_certificate` | Mock Certificate object |
| `mock_oidc_app` | Mock OIDC Application object |
| `mock_oidc_user_entry` | Mock OIDC User ACL entry |
| `mock_oidc_group_entry` | Mock OIDC Group ACL entry |
| `mock_oidc_log` | Mock OIDC Log entry |
| `mock_catalog` | Mock Catalog object |
| `mock_catalog_log` | Mock Catalog Log entry |
| `mock_catalog_repo` | Mock Catalog Repository object |
| `mock_catalog_repo_status` | Mock Repository Status object |
| `mock_catalog_repo_log` | Mock Repository Log entry |
| `mock_update_settings` | Mock Update Settings object |
| `mock_update_source` | Mock Update Source object |
| `mock_update_source_status` | Mock Update Source Status object |
| `mock_update_branch` | Mock Update Branch object |
| `mock_update_package` | Mock Update Package object |
| `mock_update_source_package` | Mock Source Package object |
| `mock_update_log` | Mock Update Log entry |
| `mock_update_dashboard` | Mock Update Dashboard object |
| `mock_alarm` | Mock Alarm object |
| `mock_alarm_history` | Mock Alarm History entry |
| `mock_log_entry` | Mock System Log entry |
| `mock_tag` | Mock Tag object |
| `mock_tag_category` | Mock Tag Category object |
| `mock_tag_member` | Mock Tag Member object |
| `mock_resource_group` | Mock Resource Group object |
| `mock_shared_object` | Mock Tenant Shared Object |

## Example Test Pattern

The standard mock-invoke-assert pattern:

```python
from verge_cli.cli import app

def test_vm_list(cli_runner, mock_client, mock_vm):
    # Arrange: set up mock return values
    mock_client.vms.list.return_value = [mock_vm]

    # Act: invoke the CLI command
    result = cli_runner.invoke(app, ["vm", "list"])

    # Assert: check output and mock calls
    assert result.exit_code == 0
    assert "test-vm" in result.output
    mock_client.vms.list.assert_called_once()
```

### Testing Error Handling

```python
from pyvergeos.exceptions import NotFoundError

def test_vm_get_not_found(cli_runner, mock_client):
    mock_client.vms.get.side_effect = NotFoundError("VM not found")

    result = cli_runner.invoke(app, ["vm", "get", "999"])

    assert result.exit_code == 6  # NOT_FOUND_ERROR
```

### Testing Sub-Resource Commands

```python
def test_vm_drive_list(cli_runner, mock_client, mock_vm, mock_drive):
    mock_client.vms.get.return_value = mock_vm
    mock_vm.drives.list.return_value = [mock_drive]

    result = cli_runner.invoke(app, ["vm", "drive", "list", "test-vm"])

    assert result.exit_code == 0
    assert "OS Disk" in result.output
```

## Tips

- Always run `uv run ruff check` on test files — unused imports sneak in from template code
- The `mock_client` fixture patches `verge_cli.auth.get_client`, so commands get the mock automatically
- Use `mock_client.<resource>.list.return_value = [mock_obj]` to set up list responses
- Use `.side_effect` for error testing
- SDK attribute access returns `Any` — wrap `.key` with `int()` in code under test
