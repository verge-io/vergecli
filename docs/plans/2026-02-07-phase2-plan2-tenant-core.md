# Phase 2 Plan 2: Tenant Core Commands

**Goal:** Add full tenant lifecycle management to the CLI — CRUD, power operations, clone, isolate, crash-cart, and send-file.

**Architecture:** Single command module `tenant.py` following vm.py pattern for CRUD and power ops. Crash-cart uses a sub-Typer within the same file. Tenant sub-resources (node, storage, net, snapshot, stats) are deferred to Plan 3.

**Tech Stack:** Python 3.10+, Typer, Rich, pyvergeos SDK, pytest

**Prerequisite:** Plan 1 (Infrastructure) should be completed first — it establishes conftest fixture patterns.

---

## Task 1: Update TENANT_COLUMNS + add mock_tenant fixture

### Step 1.1: Update TENANT_COLUMNS in columns.py

**File:** `src/verge_cli/columns.py`

The existing `TENANT_COLUMNS` (lines 268-285) needs to be updated to match the design doc:

1. Add `$key` column (not wide_only) at the top
2. Change `isolate` to `is_isolated`, move it OUT of `wide_only`, add it after `state`
3. Remove the standalone `key` column (replaced by `$key`)

**Edit** the existing `TENANT_COLUMNS` definition at lines 268-285 to:

```python
TENANT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("state"),
    ColumnDef(
        "is_isolated",
        header="Isolated",
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    # wide-only
    ColumnDef("description", wide_only=True),
    ColumnDef("network_name", header="Network", wide_only=True),
    ColumnDef("ui_address_ip", header="UI IP", wide_only=True),
    ColumnDef("uuid", wide_only=True),
]
```

**Verify:**

```bash
uv run ruff check src/verge_cli/columns.py
uv run mypy src/verge_cli/columns.py
```

### Step 1.2: Add mock_tenant fixture to conftest.py

**File:** `tests/conftest.py`

Add the following fixture after the `mock_device` fixture (after line 228):

```python
@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"
    tenant.status = "running"
    tenant.is_running = True

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "ACME Corporation tenant",
            "state": "active",
            "is_isolated": False,
            "network_name": "Tenant Internal",
            "ui_address_ip": "10.10.0.100",
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "url": "acme.verge.local",
            "note": "Production tenant",
            "expose_cloud_snapshots": True,
            "allow_branding": False,
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant
```

**Verify:**

```bash
uv run ruff check tests/conftest.py
uv run pytest tests/unit/test_cli.py -v --tb=short
```

### Step 1.3: Commit

```bash
uv run ruff check src/verge_cli/columns.py tests/conftest.py
uv run mypy src/verge_cli
git add src/verge_cli/columns.py tests/conftest.py
git commit -m "$(cat <<'EOF'
✨ feat: update TENANT_COLUMNS and add mock_tenant fixture

Update TENANT_COLUMNS to match design doc: add $key column, change
isolate to is_isolated (not wide_only), remove standalone key column.
Add mock_tenant fixture to conftest for upcoming tenant commands.
EOF
)"
```

---

## Task 2: tenant.py — scaffolding + list + get

### Step 2.1: Write tests for tenant list and get

**File:** `tests/unit/test_tenant.py`

```python
"""Tests for tenant commands."""

from verge_cli.cli import app


def test_tenant_list(cli_runner, mock_client, mock_tenant):
    """vrg tenant list should list tenants."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.list.assert_called_once()


def test_tenant_list_empty(cli_runner, mock_client):
    """vrg tenant list with no tenants should show empty message."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_tenant_list_json(cli_runner, mock_client, mock_tenant):
    """vrg tenant list --output json should produce valid JSON."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["--output", "json", "tenant", "list"])

    assert result.exit_code == 0
    assert '"name": "acme-corp"' in result.output
    assert '"$key": 5' in result.output
    assert '"is_isolated": false' in result.output


def test_tenant_get(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should show tenant details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "acme-corp"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_by_key(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should accept numeric key."""
    mock_client.tenants.list.return_value = []
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "5"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_not_found(cli_runner, mock_client):
    """vrg tenant get with unknown name should exit 6."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "get", "nonexistent"])

    assert result.exit_code == 6
```

**Run tests to verify they fail:**

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All tests should fail because `tenant.py` does not exist yet and `tenant` is not registered in cli.py.

### Step 2.2: Create tenant.py with scaffolding, list, and get

**File:** `src/verge_cli/commands/tenant.py`

```python
"""Tenant management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id, wait_for_state

app = typer.Typer(
    name="tenant",
    help="Manage tenants.",
    no_args_is_help=True,
)


def _tenant_to_dict(tenant: Any) -> dict[str, Any]:
    """Convert a Tenant object to a dictionary for output."""
    return {
        "$key": tenant.key,
        "name": tenant.name,
        "status": tenant.status,
        "state": tenant.get("state", ""),
        "is_isolated": tenant.get("is_isolated", False),
        "description": tenant.get("description", ""),
        "network_name": tenant.get("network_name", ""),
        "ui_address_ip": tenant.get("ui_address_ip", ""),
        "uuid": tenant.get("uuid", ""),
        "url": tenant.get("url", ""),
        "note": tenant.get("note", ""),
        "expose_cloud_snapshots": tenant.get("expose_cloud_snapshots", False),
        "allow_branding": tenant.get("allow_branding", False),
    }


@app.command("list")
@handle_errors()
def tenant_list(ctx: typer.Context) -> None:
    """List tenants."""
    vctx = get_context(ctx)
    tenants = vctx.client.tenants.list()
    data = [_tenant_to_dict(t) for t in tenants]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Get details of a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 2.3: Register tenant in cli.py

**File:** `src/verge_cli/cli.py`

Update the import line (line 11):

```python
from verge_cli.commands import configure, network, system, tenant, vm
```

Add the registration line after the existing `app.add_typer` calls (after line 24):

```python
app.add_typer(tenant.app, name="tenant")
```

### Step 2.4: Run tests

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All 7 tests should pass.

### Step 2.5: Lint and type check

```bash
uv run ruff check src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
uv run mypy src/verge_cli
```

### Step 2.6: Commit

```bash
git add src/verge_cli/commands/tenant.py tests/unit/test_tenant.py src/verge_cli/cli.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant list and get commands

Create tenant.py with scaffolding, _tenant_to_dict converter, list
and get commands. Register tenant app in cli.py.
EOF
)"
```

---

## Task 3: tenant.py — create + update

### Step 3.1: Write tests for create and update

**File:** `tests/unit/test_tenant.py` — append the following tests:

```python
def test_tenant_create(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should create a tenant."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "create", "--name", "acme-corp", "--description", "ACME Corp"],
    )

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.create.assert_called_once()
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["description"] == "ACME Corp"


def test_tenant_create_with_password(cli_runner, mock_client, mock_tenant):
    """vrg tenant create with --password should pass password to SDK."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--password",
            "s3cret!",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["password"] == "s3cret!"


def test_tenant_create_all_options(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should accept all optional flags."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--description",
            "ACME Corp",
            "--password",
            "pass123",
            "--url",
            "acme.verge.local",
            "--note",
            "Production",
            "--expose-cloud-snapshots",
            "--allow-branding",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["url"] == "acme.verge.local"
    assert call_kwargs["note"] == "Production"
    assert call_kwargs["expose_cloud_snapshots"] is True
    assert call_kwargs["allow_branding"] is True


def test_tenant_create_no_name(cli_runner, mock_client):
    """vrg tenant create without --name should fail."""
    result = cli_runner.invoke(app, ["tenant", "create"])

    assert result.exit_code == 2


def test_tenant_update(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should update tenant properties."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "update", "acme-corp", "--description", "Updated ACME"],
    )

    assert result.exit_code == 0
    mock_client.tenants.update.assert_called_once()
    call_args = mock_client.tenants.update.call_args
    assert call_args[0][0] == 5  # key
    assert call_args[1]["description"] == "Updated ACME"


def test_tenant_update_no_changes(cli_runner, mock_client, mock_tenant):
    """vrg tenant update with no options should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "update", "acme-corp"])

    assert result.exit_code == 2
    assert "No updates" in result.output


def test_tenant_update_multiple_fields(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should accept multiple fields."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "update",
            "acme-corp",
            "--name",
            "acme-new",
            "--url",
            "new.verge.local",
            "--no-expose-cloud-snapshots",
        ],
    )

    assert result.exit_code == 0
    call_args = mock_client.tenants.update.call_args
    assert call_args[1]["name"] == "acme-new"
    assert call_args[1]["url"] == "new.verge.local"
    assert call_args[1]["expose_cloud_snapshots"] is False
```

**Run tests (should fail — create/update not implemented yet):**

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short -k "create or update"
```

### Step 3.2: Implement create and update in tenant.py

Add the following commands after the `tenant_get` function in `src/verge_cli/commands/tenant.py`:

```python
@app.command("create")
@handle_errors()
def tenant_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Tenant name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Tenant description")
    ] = "",
    password: Annotated[
        str | None, typer.Option("--password", help="Admin password for tenant")
    ] = None,
    url: Annotated[
        str | None, typer.Option("--url", help="Tenant URL slug")
    ] = None,
    note: Annotated[
        str | None, typer.Option("--note", help="Internal note")
    ] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Create a new tenant."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {"name": name, "description": description}
    if password is not None:
        kwargs["password"] = password
    if url is not None:
        kwargs["url"] = url
    if note is not None:
        kwargs["note"] = note
    if expose_cloud_snapshots is not None:
        kwargs["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        kwargs["allow_branding"] = allow_branding

    tenant_obj = vctx.client.tenants.create(**kwargs)

    output_success(
        f"Created tenant '{tenant_obj.name}' (key: {tenant_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def tenant_update(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New tenant name")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Tenant description")
    ] = None,
    url: Annotated[
        str | None, typer.Option("--url", help="Tenant URL slug")
    ] = None,
    note: Annotated[
        str | None, typer.Option("--note", help="Internal note")
    ] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Update a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if url is not None:
        updates["url"] = url
    if note is not None:
        updates["note"] = note
    if expose_cloud_snapshots is not None:
        updates["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        updates["allow_branding"] = allow_branding

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    tenant_obj = vctx.client.tenants.update(key, **updates)

    output_success(f"Updated tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 3.3: Run tests

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All tests (previous + new) should pass.

### Step 3.4: Lint and type check

```bash
uv run ruff check src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
uv run mypy src/verge_cli
```

### Step 3.5: Commit

```bash
git add src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant create and update commands

Tenant create accepts --name, --description, --password, --url, --note,
--expose-cloud-snapshots, and --allow-branding. Update resolves by
name/key and accepts the same optional flags.
EOF
)"
```

---

## Task 4: tenant.py — delete + power operations

### Step 4.1: Write tests for delete and power ops

**File:** `tests/unit/test_tenant.py` — append the following tests:

```python
def test_tenant_delete(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete should delete a tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_cancelled(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete without --yes should prompt and cancel."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp"], input="n\n")

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_not_called()


def test_tenant_delete_force_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete --force should delete running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(
        app, ["tenant", "delete", "acme-corp", "--yes", "--force"]
    )

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_running_no_force(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete of running tenant without --force should fail."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 7
    mock_client.tenants.delete.assert_not_called()


def test_tenant_start(cli_runner, mock_client, mock_tenant):
    """vrg tenant start should power on a tenant."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_on.assert_called_once_with(5)


def test_tenant_start_already_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant start on running tenant should show message."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    assert "already running" in result.output
    mock_client.tenants.power_on.assert_not_called()


def test_tenant_stop(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop should power off a tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_off.assert_called_once_with(5)


def test_tenant_stop_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop on stopped tenant should show message."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    assert "not running" in result.output
    mock_client.tenants.power_off.assert_not_called()


def test_tenant_restart(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart should restart a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.restart.assert_called_once_with(5)


def test_tenant_restart_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.restart.assert_not_called()


def test_tenant_reset(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset should hard reset a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.reset.assert_called_once_with(5)


def test_tenant_reset_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.reset.assert_not_called()
```

**Run tests (should fail):**

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short -k "delete or start or stop or restart or reset"
```

### Step 4.2: Implement delete in tenant.py

Add after the `tenant_update` function:

```python
@app.command("delete")
@handle_errors()
def tenant_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force delete running tenant")
    ] = False,
) -> None:
    """Delete a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running and not force:
        typer.echo(
            f"Error: Tenant '{tenant_obj.name}' is running. Use --force to delete anyway.",
            err=True,
        )
        raise typer.Exit(7)

    if not confirm_action(f"Delete tenant '{tenant_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.tenants.delete(key)
    output_success(f"Deleted tenant '{tenant_obj.name}'", quiet=vctx.quiet)
```

### Step 4.3: Implement power operations in tenant.py

Add after the `tenant_delete` function:

```python
@app.command("start")
@handle_errors()
def tenant_start(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to start")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Start a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is already running.")
        return

    vctx.client.tenants.power_on(key)
    output_success(f"Starting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' is now running", quiet=vctx.quiet
        )


@app.command("stop")
@handle_errors()
def tenant_stop(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to stop")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Stop a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        return

    vctx.client.tenants.power_off(key)
    output_success(f"Stopping tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state=["stopped", "offline"],
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' is now stopped", quiet=vctx.quiet
        )


@app.command("restart")
@handle_errors()
def tenant_restart(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to restart")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Restart a tenant.

    This sends a restart command to the tenant. For a hard reset
    (like pressing the reset button), use 'vrg tenant reset' instead.
    """
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(
            f"Tenant '{tenant_obj.name}' is not running. Use 'vrg tenant start' instead."
        )
        raise typer.Exit(1)

    vctx.client.tenants.restart(key)
    output_success(f"Restarting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' has restarted", quiet=vctx.quiet
        )


@app.command("reset")
@handle_errors()
def tenant_reset(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Hard reset a tenant (like pressing the reset button)."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        raise typer.Exit(1)

    vctx.client.tenants.reset(key)
    output_success(f"Reset tenant '{tenant_obj.name}'", quiet=vctx.quiet)
```

### Step 4.4: Run tests

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All tests should pass.

### Step 4.5: Lint and type check

```bash
uv run ruff check src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
uv run mypy src/verge_cli
```

### Step 4.6: Commit

```bash
git add src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant delete and power operation commands

Add delete (with --force for running tenants), start, stop, restart,
and reset commands. Power ops use client.tenants.power_on/power_off/
restart/reset pattern with --wait and --timeout support.
EOF
)"
```

---

## Task 5: tenant.py — clone + isolate

### Step 5.1: Write tests for clone and isolate

**File:** `tests/unit/test_tenant.py` — append the following tests:

```python
from unittest.mock import MagicMock


def test_tenant_clone(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone should clone a tenant."""
    cloned = MagicMock()
    cloned.key = 10
    cloned.name = "acme-corp-clone"
    cloned.status = "stopped"
    cloned.is_running = False

    def cloned_get(key: str, default=None):
        data = {
            "description": "ACME Corporation tenant",
            "state": "inactive",
            "is_isolated": False,
            "network_name": "Tenant Internal",
            "ui_address_ip": "",
            "uuid": "660e8400-e29b-41d4-a716-446655440001",
            "url": "",
            "note": "",
            "expose_cloud_snapshots": True,
            "allow_branding": False,
        }
        return data.get(key, default)

    cloned.get = cloned_get
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(app, ["tenant", "clone", "acme-corp"])

    assert result.exit_code == 0
    assert "acme-corp-clone" in result.output
    mock_client.tenants.clone.assert_called_once()
    call_args = mock_client.tenants.clone.call_args
    assert call_args[0][0] == 5  # key


def test_tenant_clone_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone --name should pass new name to SDK."""
    cloned = MagicMock()
    cloned.key = 10
    cloned.name = "new-tenant"
    cloned.status = "stopped"
    cloned.is_running = False

    def cloned_get(key: str, default=None):
        return {
            "description": "",
            "state": "inactive",
            "is_isolated": False,
            "network_name": "",
            "ui_address_ip": "",
            "uuid": "aaa",
            "url": "",
            "note": "",
            "expose_cloud_snapshots": False,
            "allow_branding": False,
        }.get(key, default)

    cloned.get = cloned_get
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(
        app, ["tenant", "clone", "acme-corp", "--name", "new-tenant"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.clone.call_args[1]
    assert call_kwargs["name"] == "new-tenant"


def test_tenant_clone_skip_flags(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone should pass --no-network, --no-storage, --no-nodes."""
    cloned = MagicMock()
    cloned.key = 10
    cloned.name = "clone"
    cloned.status = "stopped"
    cloned.is_running = False

    def cloned_get(key: str, default=None):
        return {
            "description": "",
            "state": "inactive",
            "is_isolated": False,
            "network_name": "",
            "ui_address_ip": "",
            "uuid": "bbb",
            "url": "",
            "note": "",
            "expose_cloud_snapshots": False,
            "allow_branding": False,
        }.get(key, default)

    cloned.get = cloned_get
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "clone",
            "acme-corp",
            "--no-network",
            "--no-storage",
            "--no-nodes",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.clone.call_args[1]
    assert call_kwargs["no_network"] is True
    assert call_kwargs["no_storage"] is True
    assert call_kwargs["no_nodes"] is True


def test_tenant_isolate_enable(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate --enable should enable isolation."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--enable"]
    )

    assert result.exit_code == 0
    mock_client.tenants.enable_isolation.assert_called_once_with(5)


def test_tenant_isolate_disable(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate --disable should disable isolation."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--disable"]
    )

    assert result.exit_code == 0
    mock_client.tenants.disable_isolation.assert_called_once_with(5)


def test_tenant_isolate_no_flag(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate without --enable or --disable should fail."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "isolate", "acme-corp"])

    assert result.exit_code == 2


def test_tenant_isolate_both_flags(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate with both --enable and --disable should fail."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--enable", "--disable"]
    )

    assert result.exit_code == 2
```

**Run tests (should fail):**

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short -k "clone or isolate"
```

### Step 5.2: Implement clone and isolate in tenant.py

Add after the `tenant_reset` function:

```python
@app.command("clone")
@handle_errors()
def tenant_clone(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key to clone")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Name for the cloned tenant"),
    ] = None,
    no_network: Annotated[
        bool,
        typer.Option("--no-network", help="Skip cloning network configuration"),
    ] = False,
    no_storage: Annotated[
        bool,
        typer.Option("--no-storage", help="Skip cloning storage allocations"),
    ] = False,
    no_nodes: Annotated[
        bool,
        typer.Option("--no-nodes", help="Skip cloning node allocations"),
    ] = False,
) -> None:
    """Clone a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if no_network:
        kwargs["no_network"] = True
    if no_storage:
        kwargs["no_storage"] = True
    if no_nodes:
        kwargs["no_nodes"] = True

    cloned_obj = vctx.client.tenants.clone(key, **kwargs)

    output_success(
        f"Cloned tenant to '{cloned_obj.name}' (key: {cloned_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _tenant_to_dict(cloned_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("isolate")
@handle_errors()
def tenant_isolate(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    enable: Annotated[
        bool,
        typer.Option("--enable", help="Enable network isolation"),
    ] = False,
    disable: Annotated[
        bool,
        typer.Option("--disable", help="Disable network isolation"),
    ] = False,
) -> None:
    """Enable or disable network isolation for a tenant."""
    if enable == disable:
        typer.echo(
            "Error: Specify either --enable or --disable.", err=True
        )
        raise typer.Exit(2)

    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if enable:
        vctx.client.tenants.enable_isolation(key)
        output_success("Isolation enabled", quiet=vctx.quiet)
    else:
        vctx.client.tenants.disable_isolation(key)
        output_success("Isolation disabled", quiet=vctx.quiet)
```

### Step 5.3: Run tests

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All tests should pass.

### Step 5.4: Lint and type check

```bash
uv run ruff check src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
uv run mypy src/verge_cli
```

### Step 5.5: Commit

```bash
git add src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant clone and isolate commands

Clone supports --name, --no-network, --no-storage, --no-nodes.
Isolate uses mutually exclusive --enable/--disable flags matching
the node maintenance UX pattern.
EOF
)"
```

---

## Task 6: tenant.py — crash-cart sub-Typer + send-file

### Step 6.1: Write tests for crash-cart and send-file

**File:** `tests/unit/test_tenant.py` — append the following tests:

```python
def test_tenant_crash_cart_create(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart create should create a crash cart."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "create", "acme-corp"]
    )

    assert result.exit_code == 0
    mock_client.tenants.create_crash_cart.assert_called_once_with(5)


def test_tenant_crash_cart_create_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart create --name should pass name to SDK."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app,
        ["tenant", "crash-cart", "create", "acme-corp", "--name", "debug-cart"],
    )

    assert result.exit_code == 0
    mock_client.tenants.create_crash_cart.assert_called_once_with(
        5, name="debug-cart"
    )


def test_tenant_crash_cart_delete(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete should delete a crash cart."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "delete", "acme-corp", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_called_once_with(5)


def test_tenant_crash_cart_delete_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete --name should pass name to SDK."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "crash-cart",
            "delete",
            "acme-corp",
            "--name",
            "debug-cart",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_called_once_with(
        5, name="debug-cart"
    )


def test_tenant_crash_cart_delete_cancelled(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete without --yes should prompt."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "delete", "acme-corp"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_not_called()


def test_tenant_send_file(cli_runner, mock_client, mock_tenant):
    """vrg tenant send-file should send a file to the tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "send-file", "acme-corp", "42"]
    )

    assert result.exit_code == 0
    mock_client.tenants.send_file.assert_called_once_with(5, file_key=42)
```

**Run tests (should fail):**

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short -k "crash_cart or send_file"
```

### Step 6.2: Implement crash-cart sub-Typer and send-file

Add the crash-cart sub-Typer and send-file command at the end of `src/verge_cli/commands/tenant.py`, after the `tenant_isolate` function:

```python
# ---------------------------------------------------------------------------
# Crash-cart sub-Typer
# ---------------------------------------------------------------------------

crash_cart_app = typer.Typer(
    name="crash-cart",
    help="Manage tenant crash carts.",
    no_args_is_help=True,
)
app.add_typer(crash_cart_app, name="crash-cart")


@crash_cart_app.command("create")
@handle_errors()
def crash_cart_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Crash cart name")
    ] = None,
) -> None:
    """Create a crash cart for a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if name is not None:
        vctx.client.tenants.create_crash_cart(key, name=name)
    else:
        vctx.client.tenants.create_crash_cart(key)

    output_success(f"Created crash cart for tenant (key: {key})", quiet=vctx.quiet)


@crash_cart_app.command("delete")
@handle_errors()
def crash_cart_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Crash cart name")
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Delete a crash cart from a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if not confirm_action("Delete crash cart?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    if name is not None:
        vctx.client.tenants.delete_crash_cart(key, name=name)
    else:
        vctx.client.tenants.delete_crash_cart(key)

    output_success(f"Deleted crash cart for tenant (key: {key})", quiet=vctx.quiet)


# ---------------------------------------------------------------------------
# Send-file command
# ---------------------------------------------------------------------------


@app.command("send-file")
@handle_errors()
def tenant_send_file(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    file_key: Annotated[str, typer.Argument(help="File key (numeric ID)")],
) -> None:
    """Send a file to a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    vctx.client.tenants.send_file(key, file_key=int(file_key))

    output_success(
        f"Sent file {file_key} to tenant (key: {key})", quiet=vctx.quiet
    )
```

### Step 6.3: Run tests

```bash
uv run pytest tests/unit/test_tenant.py -v --tb=short
```

All tests should pass.

### Step 6.4: Lint and type check

```bash
uv run ruff check src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
uv run mypy src/verge_cli
```

### Step 6.5: Commit

```bash
git add src/verge_cli/commands/tenant.py tests/unit/test_tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant crash-cart and send-file commands

Add crash-cart sub-Typer with create and delete commands. Add send-file
command that forwards a system file to a tenant by key. Crash-cart
delete requires --yes confirmation.
EOF
)"
```

---

## Task 7: Register in cli.py + regression test

### Step 7.1: Verify registration

The tenant app was already registered in cli.py in Task 2, Step 2.3. Verify it is present:

**File:** `src/verge_cli/cli.py` should contain:

```python
from verge_cli.commands import configure, network, system, tenant, vm
```

And:

```python
app.add_typer(tenant.app, name="tenant")
```

### Step 7.2: Add CLI help test for tenant commands

**File:** `tests/unit/test_cli.py` — add the following test class at the end:

```python
class TestTenantCommands:
    """Tests for tenant commands."""

    def test_tenant_help(self, cli_runner: CliRunner) -> None:
        """Test tenant --help."""
        result = cli_runner.invoke(app, ["tenant", "--help"])

        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "create" in result.stdout
        assert "update" in result.stdout
        assert "delete" in result.stdout
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "restart" in result.stdout
        assert "reset" in result.stdout
        assert "clone" in result.stdout
        assert "isolate" in result.stdout
        assert "crash-cart" in result.stdout
        assert "send-file" in result.stdout
```

Also update the `test_help_flag` test to include "tenant" in the assertions (line 28 area):

Verify the line `assert "vm" in result.stdout` exists, and add:

```python
assert "tenant" in result.stdout
```

### Step 7.3: Run full test suite

```bash
uv run pytest tests/unit/ -v --tb=short
```

All tests should pass (including existing VM, network, and system tests).

### Step 7.4: Run linting and type checking

```bash
uv run ruff check
uv run ruff format --check .
uv run mypy src/verge_cli
```

Fix any issues that come up. Common issues:

- **Unused imports in test file**: Remove `MagicMock` import if not at the top level (it is only needed in the clone tests where it is used inline). If ruff complains about duplicate import, move the `from unittest.mock import MagicMock` to the top of the test file and remove the inline import.
- **mypy Any returns**: Ensure `int(file_key)` is used in `send_file`, and `resolve_resource_id` returns are used directly as `int`.

### Step 7.5: Commit

```bash
git add tests/unit/test_cli.py
git commit -m "$(cat <<'EOF'
✅ test: add tenant CLI help regression tests

Verify tenant command group appears in main help and that all
subcommands (list, get, create, update, delete, start, stop, restart,
reset, clone, isolate, crash-cart, send-file) are listed.
EOF
)"
```

---

## Appendix A: Complete tenant.py Reference

Below is the final complete file for reference. This should be the state of `src/verge_cli/commands/tenant.py` after all tasks:

```python
"""Tenant management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id, wait_for_state

app = typer.Typer(
    name="tenant",
    help="Manage tenants.",
    no_args_is_help=True,
)


def _tenant_to_dict(tenant: Any) -> dict[str, Any]:
    """Convert a Tenant object to a dictionary for output."""
    return {
        "$key": tenant.key,
        "name": tenant.name,
        "status": tenant.status,
        "state": tenant.get("state", ""),
        "is_isolated": tenant.get("is_isolated", False),
        "description": tenant.get("description", ""),
        "network_name": tenant.get("network_name", ""),
        "ui_address_ip": tenant.get("ui_address_ip", ""),
        "uuid": tenant.get("uuid", ""),
        "url": tenant.get("url", ""),
        "note": tenant.get("note", ""),
        "expose_cloud_snapshots": tenant.get("expose_cloud_snapshots", False),
        "allow_branding": tenant.get("allow_branding", False),
    }


@app.command("list")
@handle_errors()
def tenant_list(ctx: typer.Context) -> None:
    """List tenants."""
    vctx = get_context(ctx)
    tenants = vctx.client.tenants.list()
    data = [_tenant_to_dict(t) for t in tenants]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Get details of a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def tenant_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Tenant name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Tenant description")
    ] = "",
    password: Annotated[
        str | None, typer.Option("--password", help="Admin password for tenant")
    ] = None,
    url: Annotated[
        str | None, typer.Option("--url", help="Tenant URL slug")
    ] = None,
    note: Annotated[
        str | None, typer.Option("--note", help="Internal note")
    ] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Create a new tenant."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {"name": name, "description": description}
    if password is not None:
        kwargs["password"] = password
    if url is not None:
        kwargs["url"] = url
    if note is not None:
        kwargs["note"] = note
    if expose_cloud_snapshots is not None:
        kwargs["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        kwargs["allow_branding"] = allow_branding

    tenant_obj = vctx.client.tenants.create(**kwargs)

    output_success(
        f"Created tenant '{tenant_obj.name}' (key: {tenant_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def tenant_update(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New tenant name")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="Tenant description")
    ] = None,
    url: Annotated[
        str | None, typer.Option("--url", help="Tenant URL slug")
    ] = None,
    note: Annotated[
        str | None, typer.Option("--note", help="Internal note")
    ] = None,
    expose_cloud_snapshots: Annotated[
        bool | None,
        typer.Option(
            "--expose-cloud-snapshots/--no-expose-cloud-snapshots",
            help="Expose cloud snapshots to tenant",
        ),
    ] = None,
    allow_branding: Annotated[
        bool | None,
        typer.Option(
            "--allow-branding/--no-allow-branding",
            help="Allow tenant to customize branding",
        ),
    ] = None,
) -> None:
    """Update a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if url is not None:
        updates["url"] = url
    if note is not None:
        updates["note"] = note
    if expose_cloud_snapshots is not None:
        updates["expose_cloud_snapshots"] = expose_cloud_snapshots
    if allow_branding is not None:
        updates["allow_branding"] = allow_branding

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    tenant_obj = vctx.client.tenants.update(key, **updates)

    output_success(f"Updated tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    output_result(
        _tenant_to_dict(tenant_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def tenant_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Force delete running tenant")
    ] = False,
) -> None:
    """Delete a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running and not force:
        typer.echo(
            f"Error: Tenant '{tenant_obj.name}' is running. Use --force to delete anyway.",
            err=True,
        )
        raise typer.Exit(7)

    if not confirm_action(f"Delete tenant '{tenant_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.tenants.delete(key)
    output_success(f"Deleted tenant '{tenant_obj.name}'", quiet=vctx.quiet)


@app.command("start")
@handle_errors()
def tenant_start(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to start")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Start a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is already running.")
        return

    vctx.client.tenants.power_on(key)
    output_success(f"Starting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' is now running", quiet=vctx.quiet
        )


@app.command("stop")
@handle_errors()
def tenant_stop(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to stop")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Stop a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        return

    vctx.client.tenants.power_off(key)
    output_success(f"Stopping tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state=["stopped", "offline"],
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' is now stopped", quiet=vctx.quiet
        )


@app.command("restart")
@handle_errors()
def tenant_restart(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    wait: Annotated[
        bool, typer.Option("--wait", "-w", help="Wait for tenant to restart")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Wait timeout in seconds")
    ] = 300,
) -> None:
    """Restart a tenant.

    This sends a restart command to the tenant. For a hard reset
    (like pressing the reset button), use 'vrg tenant reset' instead.
    """
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(
            f"Tenant '{tenant_obj.name}' is not running. Use 'vrg tenant start' instead."
        )
        raise typer.Exit(1)

    vctx.client.tenants.restart(key)
    output_success(f"Restarting tenant '{tenant_obj.name}'", quiet=vctx.quiet)

    if wait:
        tenant_obj = wait_for_state(
            get_resource=vctx.client.tenants.get,
            resource_key=key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="Tenant",
            quiet=vctx.quiet,
        )
        output_success(
            f"Tenant '{tenant_obj.name}' has restarted", quiet=vctx.quiet
        )


@app.command("reset")
@handle_errors()
def tenant_reset(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Hard reset a tenant (like pressing the reset button)."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)

    if not tenant_obj.is_running:
        typer.echo(f"Tenant '{tenant_obj.name}' is not running.")
        raise typer.Exit(1)

    vctx.client.tenants.reset(key)
    output_success(f"Reset tenant '{tenant_obj.name}'", quiet=vctx.quiet)


@app.command("clone")
@handle_errors()
def tenant_clone(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key to clone")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Name for the cloned tenant"),
    ] = None,
    no_network: Annotated[
        bool,
        typer.Option("--no-network", help="Skip cloning network configuration"),
    ] = False,
    no_storage: Annotated[
        bool,
        typer.Option("--no-storage", help="Skip cloning storage allocations"),
    ] = False,
    no_nodes: Annotated[
        bool,
        typer.Option("--no-nodes", help="Skip cloning node allocations"),
    ] = False,
) -> None:
    """Clone a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["name"] = name
    if no_network:
        kwargs["no_network"] = True
    if no_storage:
        kwargs["no_storage"] = True
    if no_nodes:
        kwargs["no_nodes"] = True

    cloned_obj = vctx.client.tenants.clone(key, **kwargs)

    output_success(
        f"Cloned tenant to '{cloned_obj.name}' (key: {cloned_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _tenant_to_dict(cloned_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("isolate")
@handle_errors()
def tenant_isolate(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    enable: Annotated[
        bool,
        typer.Option("--enable", help="Enable network isolation"),
    ] = False,
    disable: Annotated[
        bool,
        typer.Option("--disable", help="Disable network isolation"),
    ] = False,
) -> None:
    """Enable or disable network isolation for a tenant."""
    if enable == disable:
        typer.echo(
            "Error: Specify either --enable or --disable.", err=True
        )
        raise typer.Exit(2)

    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if enable:
        vctx.client.tenants.enable_isolation(key)
        output_success("Isolation enabled", quiet=vctx.quiet)
    else:
        vctx.client.tenants.disable_isolation(key)
        output_success("Isolation disabled", quiet=vctx.quiet)


# ---------------------------------------------------------------------------
# Crash-cart sub-Typer
# ---------------------------------------------------------------------------

crash_cart_app = typer.Typer(
    name="crash-cart",
    help="Manage tenant crash carts.",
    no_args_is_help=True,
)
app.add_typer(crash_cart_app, name="crash-cart")


@crash_cart_app.command("create")
@handle_errors()
def crash_cart_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Crash cart name")
    ] = None,
) -> None:
    """Create a crash cart for a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if name is not None:
        vctx.client.tenants.create_crash_cart(key, name=name)
    else:
        vctx.client.tenants.create_crash_cart(key)

    output_success(f"Created crash cart for tenant (key: {key})", quiet=vctx.quiet)


@crash_cart_app.command("delete")
@handle_errors()
def crash_cart_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="Crash cart name")
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Delete a crash cart from a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    if not confirm_action("Delete crash cart?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    if name is not None:
        vctx.client.tenants.delete_crash_cart(key, name=name)
    else:
        vctx.client.tenants.delete_crash_cart(key)

    output_success(f"Deleted crash cart for tenant (key: {key})", quiet=vctx.quiet)


# ---------------------------------------------------------------------------
# Send-file command
# ---------------------------------------------------------------------------


@app.command("send-file")
@handle_errors()
def tenant_send_file(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    file_key: Annotated[str, typer.Argument(help="File key (numeric ID)")],
) -> None:
    """Send a file to a tenant."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant, "Tenant")

    vctx.client.tenants.send_file(key, file_key=int(file_key))

    output_success(
        f"Sent file {file_key} to tenant (key: {key})", quiet=vctx.quiet
    )
```

---

## Appendix B: Complete test_tenant.py Reference

Below is the final complete test file for reference. This should be the state of `tests/unit/test_tenant.py` after all tasks:

```python
"""Tests for tenant commands."""

from unittest.mock import MagicMock

from verge_cli.cli import app


# ---------------------------------------------------------------------------
# list / get
# ---------------------------------------------------------------------------


def test_tenant_list(cli_runner, mock_client, mock_tenant):
    """vrg tenant list should list tenants."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.list.assert_called_once()


def test_tenant_list_empty(cli_runner, mock_client):
    """vrg tenant list with no tenants should show empty message."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_tenant_list_json(cli_runner, mock_client, mock_tenant):
    """vrg tenant list --output json should produce valid JSON."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["--output", "json", "tenant", "list"])

    assert result.exit_code == 0
    assert '"name": "acme-corp"' in result.output
    assert '"$key": 5' in result.output
    assert '"is_isolated": false' in result.output


def test_tenant_get(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should show tenant details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "acme-corp"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_by_key(cli_runner, mock_client, mock_tenant):
    """vrg tenant get should accept numeric key."""
    mock_client.tenants.list.return_value = []
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "get", "5"])

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.get.assert_called_once_with(5)


def test_tenant_get_not_found(cli_runner, mock_client):
    """vrg tenant get with unknown name should exit 6."""
    mock_client.tenants.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "get", "nonexistent"])

    assert result.exit_code == 6


# ---------------------------------------------------------------------------
# create / update
# ---------------------------------------------------------------------------


def test_tenant_create(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should create a tenant."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "create", "--name", "acme-corp", "--description", "ACME Corp"],
    )

    assert result.exit_code == 0
    assert "acme-corp" in result.output
    mock_client.tenants.create.assert_called_once()
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["description"] == "ACME Corp"


def test_tenant_create_with_password(cli_runner, mock_client, mock_tenant):
    """vrg tenant create with --password should pass password to SDK."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--password",
            "s3cret!",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["password"] == "s3cret!"


def test_tenant_create_all_options(cli_runner, mock_client, mock_tenant):
    """vrg tenant create should accept all optional flags."""
    mock_client.tenants.create.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "create",
            "--name",
            "acme-corp",
            "--description",
            "ACME Corp",
            "--password",
            "pass123",
            "--url",
            "acme.verge.local",
            "--note",
            "Production",
            "--expose-cloud-snapshots",
            "--allow-branding",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.create.call_args[1]
    assert call_kwargs["name"] == "acme-corp"
    assert call_kwargs["url"] == "acme.verge.local"
    assert call_kwargs["note"] == "Production"
    assert call_kwargs["expose_cloud_snapshots"] is True
    assert call_kwargs["allow_branding"] is True


def test_tenant_create_no_name(cli_runner, mock_client):
    """vrg tenant create without --name should fail."""
    result = cli_runner.invoke(app, ["tenant", "create"])

    assert result.exit_code == 2


def test_tenant_update(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should update tenant properties."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        ["tenant", "update", "acme-corp", "--description", "Updated ACME"],
    )

    assert result.exit_code == 0
    mock_client.tenants.update.assert_called_once()
    call_args = mock_client.tenants.update.call_args
    assert call_args[0][0] == 5  # key
    assert call_args[1]["description"] == "Updated ACME"


def test_tenant_update_no_changes(cli_runner, mock_client, mock_tenant):
    """vrg tenant update with no options should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "update", "acme-corp"])

    assert result.exit_code == 2
    assert "No updates" in result.output


def test_tenant_update_multiple_fields(cli_runner, mock_client, mock_tenant):
    """vrg tenant update should accept multiple fields."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.update.return_value = mock_tenant

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "update",
            "acme-corp",
            "--name",
            "acme-new",
            "--url",
            "new.verge.local",
            "--no-expose-cloud-snapshots",
        ],
    )

    assert result.exit_code == 0
    call_args = mock_client.tenants.update.call_args
    assert call_args[1]["name"] == "acme-new"
    assert call_args[1]["url"] == "new.verge.local"
    assert call_args[1]["expose_cloud_snapshots"] is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_tenant_delete(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete should delete a tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_cancelled(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete without --yes should prompt and cancel."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp"], input="n\n")

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_not_called()


def test_tenant_delete_force_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete --force should delete running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(
        app, ["tenant", "delete", "acme-corp", "--yes", "--force"]
    )

    assert result.exit_code == 0
    mock_client.tenants.delete.assert_called_once_with(5)


def test_tenant_delete_running_no_force(cli_runner, mock_client, mock_tenant):
    """vrg tenant delete of running tenant without --force should fail."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "delete", "acme-corp", "--yes"])

    assert result.exit_code == 7
    mock_client.tenants.delete.assert_not_called()


# ---------------------------------------------------------------------------
# power operations
# ---------------------------------------------------------------------------


def test_tenant_start(cli_runner, mock_client, mock_tenant):
    """vrg tenant start should power on a tenant."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_on.assert_called_once_with(5)


def test_tenant_start_already_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant start on running tenant should show message."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "start", "acme-corp"])

    assert result.exit_code == 0
    assert "already running" in result.output
    mock_client.tenants.power_on.assert_not_called()


def test_tenant_stop(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop should power off a tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.power_off.assert_called_once_with(5)


def test_tenant_stop_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant stop on stopped tenant should show message."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "stop", "acme-corp"])

    assert result.exit_code == 0
    assert "not running" in result.output
    mock_client.tenants.power_off.assert_not_called()


def test_tenant_restart(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart should restart a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.restart.assert_called_once_with(5)


def test_tenant_restart_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant restart on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "restart", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.restart.assert_not_called()


def test_tenant_reset(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset should hard reset a running tenant."""
    mock_tenant.is_running = True
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 0
    mock_client.tenants.reset.assert_called_once_with(5)


def test_tenant_reset_not_running(cli_runner, mock_client, mock_tenant):
    """vrg tenant reset on stopped tenant should fail."""
    mock_tenant.is_running = False
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(app, ["tenant", "reset", "acme-corp"])

    assert result.exit_code == 1
    mock_client.tenants.reset.assert_not_called()


# ---------------------------------------------------------------------------
# clone / isolate
# ---------------------------------------------------------------------------


def _make_cloned_tenant(key: int = 10, name: str = "acme-corp-clone") -> MagicMock:
    """Helper to create a cloned tenant mock."""
    cloned = MagicMock()
    cloned.key = key
    cloned.name = name
    cloned.status = "stopped"
    cloned.is_running = False

    def cloned_get(k: str, default=None):
        data = {
            "description": "",
            "state": "inactive",
            "is_isolated": False,
            "network_name": "",
            "ui_address_ip": "",
            "uuid": "660e8400-e29b-41d4-a716-446655440001",
            "url": "",
            "note": "",
            "expose_cloud_snapshots": False,
            "allow_branding": False,
        }
        return data.get(k, default)

    cloned.get = cloned_get
    return cloned


def test_tenant_clone(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone should clone a tenant."""
    cloned = _make_cloned_tenant()
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(app, ["tenant", "clone", "acme-corp"])

    assert result.exit_code == 0
    assert "acme-corp-clone" in result.output
    mock_client.tenants.clone.assert_called_once()
    call_args = mock_client.tenants.clone.call_args
    assert call_args[0][0] == 5  # key


def test_tenant_clone_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone --name should pass new name to SDK."""
    cloned = _make_cloned_tenant(name="new-tenant")
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(
        app, ["tenant", "clone", "acme-corp", "--name", "new-tenant"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.clone.call_args[1]
    assert call_kwargs["name"] == "new-tenant"


def test_tenant_clone_skip_flags(cli_runner, mock_client, mock_tenant):
    """vrg tenant clone should pass --no-network, --no-storage, --no-nodes."""
    cloned = _make_cloned_tenant(name="clone")
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.clone.return_value = cloned

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "clone",
            "acme-corp",
            "--no-network",
            "--no-storage",
            "--no-nodes",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.tenants.clone.call_args[1]
    assert call_kwargs["no_network"] is True
    assert call_kwargs["no_storage"] is True
    assert call_kwargs["no_nodes"] is True


def test_tenant_isolate_enable(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate --enable should enable isolation."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--enable"]
    )

    assert result.exit_code == 0
    mock_client.tenants.enable_isolation.assert_called_once_with(5)


def test_tenant_isolate_disable(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate --disable should disable isolation."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--disable"]
    )

    assert result.exit_code == 0
    mock_client.tenants.disable_isolation.assert_called_once_with(5)


def test_tenant_isolate_no_flag(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate without --enable or --disable should fail."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(app, ["tenant", "isolate", "acme-corp"])

    assert result.exit_code == 2


def test_tenant_isolate_both_flags(cli_runner, mock_client, mock_tenant):
    """vrg tenant isolate with both --enable and --disable should fail."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "isolate", "acme-corp", "--enable", "--disable"]
    )

    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# crash-cart / send-file
# ---------------------------------------------------------------------------


def test_tenant_crash_cart_create(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart create should create a crash cart."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "create", "acme-corp"]
    )

    assert result.exit_code == 0
    mock_client.tenants.create_crash_cart.assert_called_once_with(5)


def test_tenant_crash_cart_create_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart create --name should pass name to SDK."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app,
        ["tenant", "crash-cart", "create", "acme-corp", "--name", "debug-cart"],
    )

    assert result.exit_code == 0
    mock_client.tenants.create_crash_cart.assert_called_once_with(
        5, name="debug-cart"
    )


def test_tenant_crash_cart_delete(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete should delete a crash cart."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "delete", "acme-corp", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_called_once_with(5)


def test_tenant_crash_cart_delete_with_name(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete --name should pass name to SDK."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "crash-cart",
            "delete",
            "acme-corp",
            "--name",
            "debug-cart",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_called_once_with(
        5, name="debug-cart"
    )


def test_tenant_crash_cart_delete_cancelled(cli_runner, mock_client, mock_tenant):
    """vrg tenant crash-cart delete without --yes should prompt."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "crash-cart", "delete", "acme-corp"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.tenants.delete_crash_cart.assert_not_called()


def test_tenant_send_file(cli_runner, mock_client, mock_tenant):
    """vrg tenant send-file should send a file to the tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]

    result = cli_runner.invoke(
        app, ["tenant", "send-file", "acme-corp", "42"]
    )

    assert result.exit_code == 0
    mock_client.tenants.send_file.assert_called_once_with(5, file_key=42)
```

---

## Appendix C: Files Modified/Created Summary

| File | Action | Task |
|------|--------|------|
| `src/verge_cli/columns.py` | Modified (update TENANT_COLUMNS) | 1 |
| `tests/conftest.py` | Modified (add mock_tenant) | 1 |
| `src/verge_cli/commands/tenant.py` | Created | 2-6 |
| `src/verge_cli/cli.py` | Modified (import + register tenant) | 2 |
| `tests/unit/test_tenant.py` | Created | 2-6 |
| `tests/unit/test_cli.py` | Modified (add tenant help tests) | 7 |

---

## Appendix D: Key Differences from vm.py

| Aspect | VM | Tenant | Reason |
|--------|-----|--------|--------|
| Power ops | `vm_obj.power_on()` (on object) | `client.tenants.power_on(key)` (on manager) | SDK design difference per design doc |
| Restart | Graceful stop + wait + start (two-phase) | Single `client.tenants.restart(key)` call | SDK provides atomic restart for tenants |
| Reset | No `--yes` confirmation | No `--yes` confirmation | Matches vm.py pattern |
| Delete | `--force` for running | `--force` for running | Same pattern |
| Clone | N/A | `client.tenants.clone(key, ...)` | Tenant-specific feature |
| Isolate | N/A | `enable_isolation(key)` / `disable_isolation(key)` | Tenant-specific feature |
| Sub-Typer | vm_drive, vm_nic, vm_device (separate files) | crash-cart (inline in tenant.py) | Crash-cart is small enough for inline |
| `_to_dict` | Uses `vm.key` (no $key prefix) | Uses `$key: tenant.key` | Design doc specifies $key for tenants |

---

## Appendix E: Potential Pitfalls

1. **`MagicMock` import in test file**: The `from unittest.mock import MagicMock` import is needed in `test_tenant.py` for the `_make_cloned_tenant` helper. Place it at the top of the file to avoid ruff F811 warnings.

2. **`mock_tenant.is_running` mutation**: Several tests override `mock_tenant.is_running`. Since `MagicMock` attributes are mutable, tests that set `is_running = False` will affect subsequent tests using the same fixture. Pytest creates a fresh fixture per test function, so this is safe. But if tests are converted to a class sharing a fixture, this could cause ordering issues.

3. **`--expose-cloud-snapshots` / `--no-expose-cloud-snapshots`**: Typer handles `bool | None` with the `--flag/--no-flag` syntax. The default must be `None` (not `False`) for the "no updates specified" check to work correctly. When neither flag is passed, the value is `None`; when `--expose-cloud-snapshots` is passed, it is `True`; when `--no-expose-cloud-snapshots` is passed, it is `False`.

4. **`isolate --enable --disable`**: When both flags are passed, Typer sets both to `True`. The check `if enable == disable` catches both the "both True" and "both False" cases, exiting with code 2.

5. **`file_key` as string argument**: The `send-file` command takes `file_key` as a `str` Typer argument and converts with `int(file_key)`. This is intentional because Typer does not support `int` arguments as cleanly for positional args, and the `int()` conversion provides mypy type safety for the SDK call.

---

## Task Checklist

- [x] Task 1: Update TENANT_COLUMNS + add mock_tenant fixture
- [x] Task 2: tenant.py — scaffolding + list + get
- [x] Task 3: tenant.py — create + update
- [x] Task 4: tenant.py — delete + power operations
- [x] Task 5: tenant.py — clone + isolate
- [x] Task 6: tenant.py — crash-cart sub-Typer + send-file
- [ ] Task 7: Register in cli.py + regression test
