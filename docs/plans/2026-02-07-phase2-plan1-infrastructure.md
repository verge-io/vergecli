# Phase 2 Plan 1: Infrastructure Commands

**Goal:** Add cluster, node, and storage tier management commands to the CLI.

**Architecture:** Three new top-level command modules following the existing vm.py CRUD pattern. Each gets its own ColumnDef list, test file, and conftest fixtures.

**Tech Stack:** Python 3.10+, Typer, Rich, pyvergeos SDK, pytest

---

## Task 1: Add conftest fixtures + column definitions

**Files to modify:**
- `tests/conftest.py` — add `mock_cluster`, `mock_node`, `mock_storage_tier` fixtures
- `src/verge_cli/columns.py` — add `CLUSTER_COLUMNS`, `NODE_COLUMNS`, `STORAGE_COLUMNS`

### Step 1.1: Add `mock_cluster` fixture to `tests/conftest.py`

Add this fixture after the existing `mock_device` fixture (after line 228):

```python
@pytest.fixture
def mock_cluster() -> MagicMock:
    """Create a mock Cluster object."""
    cluster = MagicMock()
    cluster.key = 1
    cluster.name = "Cluster1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 1,
            "name": "Cluster1",
            "description": "Primary Cluster",
            "status": "online",
            "total_nodes": 4,
            "online_nodes": 4,
            "total_ram_gb": 256,
            "ram_used_percent": 45.2,
            "total_cores": 64,
            "running_machines": 20,
            "is_compute": True,
            "is_storage": True,
            "enabled": True,
        }
        return data.get(key, default)

    cluster.get = mock_get
    return cluster
```

### Step 1.2: Add `mock_node` fixture to `tests/conftest.py`

Add this fixture after `mock_cluster`:

```python
@pytest.fixture
def mock_node() -> MagicMock:
    """Create a mock Node object."""
    node = MagicMock()
    node.key = 10
    node.name = "node1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 10,
            "name": "node1",
            "status": "online",
            "cluster_name": "Cluster1",
            "ram_gb": 64,
            "cores": 16,
            "cpu_usage": 35.0,
            "is_physical": True,
            "model": "PowerEdge R740",
            "cpu": "Intel Xeon Gold 6248",
            "core_temp": 52,
            "vergeos_version": "6.0.1",
        }
        return data.get(key, default)

    node.get = mock_get
    return node
```

### Step 1.3: Add `mock_storage_tier` fixture to `tests/conftest.py`

Add this fixture after `mock_node`:

```python
@pytest.fixture
def mock_storage_tier() -> MagicMock:
    """Create a mock Storage Tier object."""
    tier = MagicMock()
    tier.key = 1
    tier.name = "Tier 1 - SSD"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 1,
            "tier": 1,
            "description": "SSD Storage",
            "capacity_gb": 10240,
            "used_gb": 6144,
            "free_gb": 4096,
            "used_percent": 60.0,
            "dedupe_ratio": 1.5,
            "dedupe_savings_percent": 33.3,
            "read_ops": 15000,
            "write_ops": 8000,
        }
        return data.get(key, default)

    tier.get = mock_get
    return tier
```

### Step 1.4: Add `_percent_style` helper and column definitions to `src/verge_cli/columns.py`

Add the `_percent_style` helper function after the existing `default_format` function (after line 113), before the "Resource column definitions" section:

```python
def _percent_style(value: Any, row: dict[str, Any]) -> str | None:
    """Style for percentage columns: >80 red bold, >60 yellow."""
    if isinstance(value, (int, float)):
        if value > 80:
            return "red bold"
        if value > 60:
            return "yellow"
    return None


def _temp_style(value: Any, row: dict[str, Any]) -> str | None:
    """Style for temperature columns: >80 red bold, >60 yellow."""
    if isinstance(value, (int, float)):
        if value > 80:
            return "red bold"
        if value > 60:
            return "yellow"
    return None
```

Add the three column definitions at the end of the file, after `TENANT_COLUMNS` (after line 285):

```python
CLUSTER_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("total_nodes", header="Nodes"),
    ColumnDef("online_nodes", header="Online"),
    ColumnDef("total_ram_gb", header="RAM GB"),
    ColumnDef("ram_used_percent", header="RAM %", style_fn=_percent_style),
    ColumnDef("total_cores", header="Cores"),
    # wide-only
    ColumnDef("running_machines", header="Running VMs", wide_only=True),
    ColumnDef(
        "is_compute",
        header="Compute",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    ColumnDef(
        "is_storage",
        header="Storage",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    ColumnDef("key", wide_only=True),
]

NODE_COLUMNS = [
    ColumnDef("name"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("cluster_name", header="Cluster"),
    ColumnDef("ram_gb", header="RAM GB"),
    ColumnDef("cores"),
    ColumnDef("cpu_usage", header="CPU %", style_fn=_percent_style),
    # wide-only
    ColumnDef(
        "is_physical",
        header="Physical",
        wide_only=True,
        format_fn=format_bool_yn,
        style_map=BOOL_STYLES,
    ),
    ColumnDef("model", wide_only=True),
    ColumnDef("cpu", header="CPU", wide_only=True),
    ColumnDef("core_temp", header="Temp \u00b0C", wide_only=True, style_fn=_temp_style),
    ColumnDef("vergeos_version", header="Version", wide_only=True),
    ColumnDef("key", wide_only=True),
]

STORAGE_COLUMNS = [
    ColumnDef("tier", header="Tier #"),
    ColumnDef("description"),
    ColumnDef("capacity_gb", header="Capacity GB"),
    ColumnDef("used_gb", header="Used GB"),
    ColumnDef("free_gb", header="Free GB"),
    ColumnDef("used_percent", header="Used %", style_fn=_percent_style),
    # wide-only
    ColumnDef("dedupe_ratio", header="Dedupe", wide_only=True),
    ColumnDef("dedupe_savings_percent", header="Savings %", wide_only=True),
    ColumnDef("read_ops", header="Read IOPS", wide_only=True),
    ColumnDef("write_ops", header="Write IOPS", wide_only=True),
    ColumnDef("key", wide_only=True),
]
```

### Step 1.5: Verify

```bash
uv run ruff check src/verge_cli/columns.py
uv run mypy src/verge_cli/columns.py
uv run pytest tests/unit/ -v --co -q  # Verify fixtures are discoverable (dry run)
```

### Step 1.6: Commit

```
git add tests/conftest.py src/verge_cli/columns.py
```

Commit message:
```
feat: add infrastructure fixtures and column definitions

Add mock_cluster, mock_node, mock_storage_tier fixtures to conftest.
Add CLUSTER_COLUMNS, NODE_COLUMNS, STORAGE_COLUMNS to columns.py
with percent/temperature style functions.
```

---

## Task 2: cluster.py — list + get commands (TDD)

**Files to create:**
- `tests/unit/test_cluster.py`
- `src/verge_cli/commands/cluster.py`

### Step 2.1: Write failing tests for cluster list + get

Create `tests/unit/test_cluster.py`:

```python
"""Tests for cluster commands."""

from verge_cli.cli import app


def test_cluster_list(cli_runner, mock_client, mock_cluster):
    """vrg cluster list should list all clusters."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.list.assert_called_once()


def test_cluster_list_empty(cli_runner, mock_client):
    """vrg cluster list should handle empty results."""
    mock_client.clusters.list.return_value = []

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_cluster_list_json(cli_runner, mock_client, mock_cluster):
    """vrg cluster list --output json should output JSON."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["--output", "json", "cluster", "list"])

    assert result.exit_code == 0
    assert '"name": "Cluster1"' in result.output


def test_cluster_get(cli_runner, mock_client, mock_cluster):
    """vrg cluster get should show cluster details."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "Cluster1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output


def test_cluster_get_by_key(cli_runner, mock_client, mock_cluster):
    """vrg cluster get by numeric key should work."""
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
```

### Step 2.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_cluster.py -v
```

Expected: failures (cluster commands don't exist yet).

### Step 2.3: Create `src/verge_cli/commands/cluster.py` with list + get

```python
"""Cluster management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import CLUSTER_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="cluster",
    help="Manage clusters.",
    no_args_is_help=True,
)


def _cluster_to_dict(cluster: Any) -> dict[str, Any]:
    """Convert a Cluster object to a dict for output."""
    return {
        "key": cluster.key,
        "name": cluster.name,
        "status": cluster.get("status", ""),
        "total_nodes": cluster.get("total_nodes"),
        "online_nodes": cluster.get("online_nodes"),
        "total_ram_gb": cluster.get("total_ram_gb"),
        "ram_used_percent": cluster.get("ram_used_percent"),
        "total_cores": cluster.get("total_cores"),
        "running_machines": cluster.get("running_machines"),
        "is_compute": cluster.get("is_compute"),
        "is_storage": cluster.get("is_storage"),
    }


@app.command("list")
@handle_errors()
def cluster_list(
    ctx: typer.Context,
) -> None:
    """List all clusters."""
    vctx = get_context(ctx)

    clusters = vctx.client.clusters.list()
    data = [_cluster_to_dict(c) for c in clusters]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=CLUSTER_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def cluster_get(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
) -> None:
    """Get details of a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")
    cluster_obj = vctx.client.clusters.get(key)

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 2.4: Register cluster in `src/verge_cli/cli.py`

Add to imports (line 11):
```python
from verge_cli.commands import configure, network, system, vm
```
becomes:
```python
from verge_cli.commands import cluster, configure, network, system, vm
```

Add registration after line 24 (after `app.add_typer(vm.app, name="vm")`):
```python
app.add_typer(cluster.app, name="cluster")
```

### Step 2.5: Run tests to verify they pass

```bash
uv run pytest tests/unit/test_cluster.py -v
```

### Step 2.6: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/cluster.py tests/unit/test_cluster.py
uv run mypy src/verge_cli/commands/cluster.py
```

### Step 2.7: Commit

```
git add src/verge_cli/commands/cluster.py tests/unit/test_cluster.py src/verge_cli/cli.py
```

Commit message:
```
feat: add cluster list and get commands

Implement vrg cluster list and vrg cluster get with TDD.
Register cluster command group in cli.py.
```

---

## Task 3: cluster.py — create, update, delete (TDD)

**Files to modify:**
- `tests/unit/test_cluster.py` — add tests
- `src/verge_cli/commands/cluster.py` — add commands

### Step 3.1: Write failing tests for create, update, delete

Append to `tests/unit/test_cluster.py`:

```python
def test_cluster_create(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should create a new cluster."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "create", "--name", "Cluster1"]
    )

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.create.assert_called_once()


def test_cluster_create_with_options(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should accept all options."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        [
            "cluster",
            "create",
            "--name",
            "Cluster1",
            "--description",
            "Primary",
            "--enabled",
            "--compute",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.create.call_args[1]
    assert call_kwargs["name"] == "Cluster1"
    assert call_kwargs["description"] == "Primary"
    assert call_kwargs["enabled"] is True
    assert call_kwargs["is_compute"] is True


def test_cluster_create_no_name(cli_runner, mock_client):
    """vrg cluster create without --name should fail."""
    result = cli_runner.invoke(app, ["cluster", "create"])

    assert result.exit_code == 2


def test_cluster_update(cli_runner, mock_client, mock_cluster):
    """vrg cluster update should update a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.update.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        ["cluster", "update", "Cluster1", "--description", "Updated"],
    )

    assert result.exit_code == 0
    mock_client.clusters.update.assert_called_once()
    call_args = mock_client.clusters.update.call_args
    assert call_args[0][0] == 1  # key
    assert call_args[1]["description"] == "Updated"


def test_cluster_update_no_changes(cli_runner, mock_client, mock_cluster):
    """vrg cluster update with no options should fail."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "update", "Cluster1"])

    assert result.exit_code == 2


def test_cluster_delete(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete should delete a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "delete", "Cluster1", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_called_once_with(1)


def test_cluster_delete_without_yes(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete without --yes should prompt and abort on 'n'."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "delete", "Cluster1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_not_called()
```

### Step 3.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_cluster.py -v -k "create or update or delete"
```

### Step 3.3: Add create, update, delete to `src/verge_cli/commands/cluster.py`

Add this import to the existing imports:

```python
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id
```

(Change the existing `output_result` import to also include `output_success`, and add `confirm_action` to the `utils` import.)

Add these commands after `cluster_get`:

```python
@app.command("create")
@handle_errors()
def cluster_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Cluster name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Cluster description")
    ] = "",
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--no-enabled", help="Enable the cluster"),
    ] = None,
    compute: Annotated[
        bool | None,
        typer.Option("--compute/--no-compute", help="Mark as compute cluster"),
    ] = None,
) -> None:
    """Create a new cluster."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {
        "name": name,
        "description": description,
    }
    if enabled is not None:
        kwargs["enabled"] = enabled
    if compute is not None:
        kwargs["is_compute"] = compute

    cluster_obj = vctx.client.clusters.create(**kwargs)

    output_success(
        f"Created cluster '{cluster_obj.name}' (key: {cluster_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def cluster_update(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New cluster name")
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Cluster description"),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--no-enabled", help="Enable/disable the cluster"),
    ] = None,
    compute: Annotated[
        bool | None,
        typer.Option("--compute/--no-compute", help="Mark as compute cluster"),
    ] = None,
) -> None:
    """Update a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if enabled is not None:
        updates["enabled"] = enabled
    if compute is not None:
        updates["is_compute"] = compute

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    cluster_obj = vctx.client.clusters.update(key, **updates)

    output_success(f"Updated cluster '{cluster_obj.name}'", quiet=vctx.quiet)

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def cluster_delete(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Delete a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")
    cluster_obj = vctx.client.clusters.get(key)

    if not confirm_action(f"Delete cluster '{cluster_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.clusters.delete(key)
    output_success(f"Deleted cluster '{cluster_obj.name}'", quiet=vctx.quiet)
```

### Step 3.4: Run tests

```bash
uv run pytest tests/unit/test_cluster.py -v
```

### Step 3.5: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/cluster.py tests/unit/test_cluster.py
uv run mypy src/verge_cli/commands/cluster.py
```

### Step 3.6: Commit

```
git add src/verge_cli/commands/cluster.py tests/unit/test_cluster.py
```

Commit message:
```
feat: add cluster create, update, and delete commands

Implement vrg cluster create/update/delete with TDD.
Create accepts --name, --description, --enabled/--no-enabled, --compute/--no-compute.
Delete requires --yes or interactive confirmation.
```

---

## Task 4: cluster.py — vsan-status command (TDD)

**Files to modify:**
- `tests/unit/test_cluster.py` — add tests
- `src/verge_cli/commands/cluster.py` — add command

### Step 4.1: Write failing tests for vsan-status

Append to `tests/unit/test_cluster.py`:

```python
from unittest.mock import MagicMock


def test_cluster_vsan_status(cli_runner, mock_client):
    """vrg cluster vsan-status should show vSAN health."""
    mock_status = {
        "status": "healthy",
        "total_drives": 24,
        "online_drives": 24,
        "rebuilding": False,
    }
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(app, ["cluster", "vsan-status"])

    assert result.exit_code == 0
    assert "healthy" in result.output
    mock_client.clusters.vsan_status.assert_called_once()


def test_cluster_vsan_status_with_name(cli_runner, mock_client):
    """vrg cluster vsan-status --name should pass cluster name."""
    mock_status = {"status": "healthy", "total_drives": 8}
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["cluster", "vsan-status", "--name", "Cluster1"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["cluster_name"] == "Cluster1"


def test_cluster_vsan_status_with_tiers(cli_runner, mock_client):
    """vrg cluster vsan-status --include-tiers should pass flag."""
    mock_status = {
        "status": "healthy",
        "tiers": [{"tier": 1, "status": "online"}],
    }
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["cluster", "vsan-status", "--include-tiers"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["include_tiers"] is True


def test_cluster_vsan_status_json(cli_runner, mock_client):
    """vrg cluster vsan-status with JSON output."""
    mock_status = {"status": "healthy", "total_drives": 24}
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["--output", "json", "cluster", "vsan-status"]
    )

    assert result.exit_code == 0
    assert '"status": "healthy"' in result.output
```

### Step 4.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_cluster.py -v -k "vsan"
```

### Step 4.3: Add vsan-status to `src/verge_cli/commands/cluster.py`

Add this command after `cluster_delete`:

```python
@app.command("vsan-status")
@handle_errors()
def cluster_vsan_status(
    ctx: typer.Context,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Cluster name to query"),
    ] = None,
    include_tiers: Annotated[
        bool,
        typer.Option("--include-tiers", help="Include per-tier status"),
    ] = False,
) -> None:
    """Show vSAN status for a cluster."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["cluster_name"] = name
    if include_tiers:
        kwargs["include_tiers"] = True

    status = vctx.client.clusters.vsan_status(**kwargs)

    # vsan_status returns a dict or dict-like object — output directly
    if isinstance(status, dict):
        data = status
    else:
        data = dict(status) if hasattr(status, "__iter__") else {"result": str(status)}

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 4.4: Run tests

```bash
uv run pytest tests/unit/test_cluster.py -v
```

### Step 4.5: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/cluster.py tests/unit/test_cluster.py
uv run mypy src/verge_cli/commands/cluster.py
```

### Step 4.6: Commit

```
git add src/verge_cli/commands/cluster.py tests/unit/test_cluster.py
```

Commit message:
```
feat: add cluster vsan-status command

Implement vrg cluster vsan-status with optional --name and --include-tiers flags.
Outputs vSAN health data as table or JSON.
```

---

## Task 5: node.py — list + get commands (TDD)

**Files to create:**
- `tests/unit/test_node.py`
- `src/verge_cli/commands/node.py`

### Step 5.1: Write failing tests for node list + get

Create `tests/unit/test_node.py`:

```python
"""Tests for node commands."""

from verge_cli.cli import app


def test_node_list(cli_runner, mock_client, mock_node):
    """vrg node list should list all nodes."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "node1" in result.output
    mock_client.nodes.list.assert_called_once()


def test_node_list_empty(cli_runner, mock_client):
    """vrg node list should handle empty results."""
    mock_client.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_node_list_with_cluster_filter(cli_runner, mock_client, mock_node):
    """vrg node list --cluster should filter by cluster name."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list", "--cluster", "Cluster1"])

    assert result.exit_code == 0
    assert "node1" in result.output
    call_kwargs = mock_client.nodes.list.call_args[1]
    assert call_kwargs["cluster"] == "Cluster1"


def test_node_list_json(cli_runner, mock_client, mock_node):
    """vrg node list --output json should output JSON."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["--output", "json", "node", "list"])

    assert result.exit_code == 0
    assert '"name": "node1"' in result.output


def test_node_get(cli_runner, mock_client, mock_node):
    """vrg node get should show node details."""
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "node1"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_get_by_key(cli_runner, mock_client, mock_node):
    """vrg node get by numeric key should work."""
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "10"])

    assert result.exit_code == 0
    assert "node1" in result.output
```

### Step 5.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_node.py -v
```

### Step 5.3: Create `src/verge_cli/commands/node.py` with list + get

```python
"""Node management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import NODE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="node",
    help="Manage nodes.",
    no_args_is_help=True,
)


def _node_to_dict(node: Any) -> dict[str, Any]:
    """Convert a Node object to a dict for output."""
    return {
        "key": node.key,
        "name": node.name,
        "status": node.get("status", ""),
        "cluster_name": node.get("cluster_name", ""),
        "ram_gb": node.get("ram_gb"),
        "cores": node.get("cores"),
        "cpu_usage": node.get("cpu_usage"),
        "is_physical": node.get("is_physical"),
        "model": node.get("model", ""),
        "cpu": node.get("cpu", ""),
        "core_temp": node.get("core_temp"),
        "vergeos_version": node.get("vergeos_version", ""),
    }


@app.command("list")
@handle_errors()
def node_list(
    ctx: typer.Context,
    cluster: Annotated[
        str | None,
        typer.Option("--cluster", "-c", help="Filter by cluster name"),
    ] = None,
) -> None:
    """List all nodes."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {}
    if cluster is not None:
        kwargs["cluster"] = cluster

    nodes = vctx.client.nodes.list(**kwargs)
    data = [_node_to_dict(n) for n in nodes]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NODE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def node_get(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
) -> None:
    """Get details of a node."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.nodes, node, "Node")
    node_obj = vctx.client.nodes.get(key)

    output_result(
        _node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 5.4: Register node in `src/verge_cli/cli.py`

Add `node` to imports:
```python
from verge_cli.commands import cluster, configure, network, node, system, vm
```

Add registration:
```python
app.add_typer(node.app, name="node")
```

### Step 5.5: Run tests

```bash
uv run pytest tests/unit/test_node.py -v
```

### Step 5.6: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/node.py tests/unit/test_node.py
uv run mypy src/verge_cli/commands/node.py
```

### Step 5.7: Commit

```
git add src/verge_cli/commands/node.py tests/unit/test_node.py src/verge_cli/cli.py
```

Commit message:
```
feat: add node list and get commands

Implement vrg node list (with --cluster filter) and vrg node get with TDD.
Register node command group in cli.py.
```

---

## Task 6: node.py — maintenance + restart (TDD)

**Files to modify:**
- `tests/unit/test_node.py` — add tests
- `src/verge_cli/commands/node.py` — add commands

### Step 6.1: Write failing tests for maintenance + restart

Append to `tests/unit/test_node.py`:

```python
def test_node_maintenance_enable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --enable should enable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--enable"]
    )

    assert result.exit_code == 0
    mock_client.nodes.enable_maintenance.assert_called_once_with(10)


def test_node_maintenance_disable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --disable should disable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--disable"]
    )

    assert result.exit_code == 0
    mock_client.nodes.disable_maintenance.assert_called_once_with(10)


def test_node_maintenance_no_flag(cli_runner, mock_client, mock_node):
    """vrg node maintenance without --enable or --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1"])

    assert result.exit_code == 2


def test_node_maintenance_both_flags(cli_runner, mock_client, mock_node):
    """vrg node maintenance with both --enable and --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--enable", "--disable"]
    )

    assert result.exit_code == 2


def test_node_restart(cli_runner, mock_client, mock_node):
    """vrg node restart --yes should restart the node."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "restart", "node1", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_called_once_with(10)


def test_node_restart_without_yes(cli_runner, mock_client, mock_node):
    """vrg node restart without --yes should prompt and abort on 'n'."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "restart", "node1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_not_called()
```

### Step 6.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_node.py -v -k "maintenance or restart"
```

### Step 6.3: Add maintenance + restart to `src/verge_cli/commands/node.py`

Add these commands after `node_get`:

```python
@app.command("maintenance")
@handle_errors()
def node_maintenance(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
    enable: Annotated[
        bool,
        typer.Option("--enable", help="Enable maintenance mode"),
    ] = False,
    disable: Annotated[
        bool,
        typer.Option("--disable", help="Disable maintenance mode"),
    ] = False,
) -> None:
    """Enable or disable maintenance mode on a node."""
    if enable == disable:
        # Both True (impossible via CLI, but defensive) or both False
        typer.echo("Error: Specify exactly one of --enable or --disable.", err=True)
        raise typer.Exit(2)

    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.nodes, node, "Node")

    if enable:
        vctx.client.nodes.enable_maintenance(key)
        output_success(f"Enabled maintenance mode on node '{node}'", quiet=vctx.quiet)
    else:
        vctx.client.nodes.disable_maintenance(key)
        output_success(f"Disabled maintenance mode on node '{node}'", quiet=vctx.quiet)


@app.command("restart")
@handle_errors()
def node_restart(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Restart a node."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.nodes, node, "Node")

    if not confirm_action(f"Restart node '{node}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.nodes.restart(key)
    output_success(f"Restarting node '{node}'", quiet=vctx.quiet)
```

### Step 6.4: Run tests

```bash
uv run pytest tests/unit/test_node.py -v
```

### Step 6.5: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/node.py tests/unit/test_node.py
uv run mypy src/verge_cli/commands/node.py
```

### Step 6.6: Commit

```
git add src/verge_cli/commands/node.py tests/unit/test_node.py
```

Commit message:
```
feat: add node maintenance and restart commands

Implement vrg node maintenance (--enable/--disable) and vrg node restart (--yes).
Maintenance uses mutually exclusive flags consistent with design doc.
```

---

## Task 7: storage.py — list, get, summary (TDD)

**Files to create:**
- `tests/unit/test_storage.py`
- `src/verge_cli/commands/storage.py`

### Step 7.1: Write failing tests for storage list, get, summary

Create `tests/unit/test_storage.py`:

```python
"""Tests for storage tier commands."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_storage_list(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list should list all storage tiers."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.list.assert_called_once()


def test_storage_list_empty(cli_runner, mock_client):
    """vrg storage list should handle empty results."""
    mock_client.storage_tiers.list.return_value = []

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_storage_list_json(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list --output json should output JSON."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["--output", "json", "storage", "list"])

    assert result.exit_code == 0
    assert '"description": "SSD Storage"' in result.output


def test_storage_get(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get should show tier details."""
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "1"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.get.assert_called_once_with(1)


def test_storage_get_by_name(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get by name should resolve and show details."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "Tier 1 - SSD"])

    assert result.exit_code == 0
    assert "SSD" in result.output


def test_storage_summary(cli_runner, mock_client):
    """vrg storage summary should show aggregate storage data."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
        "tier_count": 2,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(app, ["storage", "summary"])

    assert result.exit_code == 0
    assert "20480" in result.output
    mock_client.storage_tiers.get_summary.assert_called_once()


def test_storage_summary_json(cli_runner, mock_client):
    """vrg storage summary with JSON output."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(
        app, ["--output", "json", "storage", "summary"]
    )

    assert result.exit_code == 0
    assert '"total_capacity_gb": 20480' in result.output
```

### Step 7.2: Run tests to verify they fail

```bash
uv run pytest tests/unit/test_storage.py -v
```

### Step 7.3: Create `src/verge_cli/commands/storage.py`

```python
"""Storage tier management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import STORAGE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="storage",
    help="Manage storage tiers.",
    no_args_is_help=True,
)


def _tier_to_dict(tier: Any) -> dict[str, Any]:
    """Convert a StorageTier object to a dict for output."""
    return {
        "key": tier.key,
        "tier": tier.get("tier"),
        "description": tier.get("description", ""),
        "capacity_gb": tier.get("capacity_gb"),
        "used_gb": tier.get("used_gb"),
        "free_gb": tier.get("free_gb"),
        "used_percent": tier.get("used_percent"),
        "dedupe_ratio": tier.get("dedupe_ratio"),
        "dedupe_savings_percent": tier.get("dedupe_savings_percent"),
        "read_ops": tier.get("read_ops"),
        "write_ops": tier.get("write_ops"),
    }


@app.command("list")
@handle_errors()
def storage_list(
    ctx: typer.Context,
) -> None:
    """List all storage tiers."""
    vctx = get_context(ctx)

    tiers = vctx.client.storage_tiers.list()
    data = [_tier_to_dict(t) for t in tiers]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=STORAGE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def storage_get(
    ctx: typer.Context,
    tier: Annotated[str, typer.Argument(help="Storage tier number or key")],
) -> None:
    """Get details of a storage tier."""
    vctx = get_context(ctx)

    # Storage tiers are typically accessed by numeric tier number or key.
    # If the identifier is numeric, try using it directly as a key.
    if tier.isdigit():
        tier_obj = vctx.client.storage_tiers.get(int(tier))
    else:
        key = resolve_resource_id(
            vctx.client.storage_tiers, tier, "Storage tier"
        )
        tier_obj = vctx.client.storage_tiers.get(key)

    output_result(
        _tier_to_dict(tier_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("summary")
@handle_errors()
def storage_summary(
    ctx: typer.Context,
) -> None:
    """Show aggregate storage summary across all tiers."""
    vctx = get_context(ctx)

    summary = vctx.client.storage_tiers.get_summary()

    # Summary returns a dict or dict-like object
    if isinstance(summary, dict):
        data = summary
    else:
        data = dict(summary) if hasattr(summary, "__iter__") else {"result": str(summary)}

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### Step 7.4: Register storage in `src/verge_cli/cli.py`

Add `storage` to imports:
```python
from verge_cli.commands import cluster, configure, network, node, storage, system, vm
```

Add registration:
```python
app.add_typer(storage.app, name="storage")
```

### Step 7.5: Run tests

```bash
uv run pytest tests/unit/test_storage.py -v
```

### Step 7.6: Run linting + type checking

```bash
uv run ruff check src/verge_cli/commands/storage.py tests/unit/test_storage.py
uv run mypy src/verge_cli/commands/storage.py
```

### Step 7.7: Commit

```
git add src/verge_cli/commands/storage.py tests/unit/test_storage.py src/verge_cli/cli.py
```

Commit message:
```
feat: add storage list, get, and summary commands

Implement vrg storage list, vrg storage get, and vrg storage summary with TDD.
Storage get accepts tier number or key. Summary shows aggregate data.
Register storage command group in cli.py.
```

---

## Task 8: Registration + full regression

**Files to verify:**
- `src/verge_cli/cli.py` — all three command groups registered

### Step 8.1: Verify final `src/verge_cli/cli.py` state

The file should have these imports and registrations:

```python
from verge_cli.commands import cluster, configure, network, node, storage, system, vm

# Register sub-commands
app.add_typer(cluster.app, name="cluster")
app.add_typer(configure.app, name="configure")
app.add_typer(network.app, name="network")
app.add_typer(node.app, name="node")
app.add_typer(storage.app, name="storage")
app.add_typer(system.app, name="system")
app.add_typer(vm.app, name="vm")
```

Note: Keep alphabetical order for imports and registrations for consistency.

### Step 8.2: Run full unit test suite

```bash
uv run pytest tests/unit/ -v
```

All existing tests MUST still pass. No regressions.

### Step 8.3: Run full linting

```bash
uv run ruff check
```

### Step 8.4: Run full type checking

```bash
uv run mypy src/verge_cli
```

### Step 8.5: Verify help output

```bash
uv run vrg --help
uv run vrg cluster --help
uv run vrg node --help
uv run vrg storage --help
```

Verify:
- `cluster`, `node`, `storage` appear in `vrg --help`
- Each sub-help shows the correct commands
- `vrg cluster --help` shows: list, get, create, update, delete, vsan-status
- `vrg node --help` shows: list, get, maintenance, restart
- `vrg storage --help` shows: list, get, summary

### Step 8.6: Commit

```
git add src/verge_cli/cli.py
```

Commit message:
```
feat: register cluster, node, storage commands and verify regression

All infrastructure commands registered in cli.py.
Full test suite passes. Linting and type checking clean.
```

---

## Complete File Listings

### `src/verge_cli/commands/cluster.py` (final)

```python
"""Cluster management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import CLUSTER_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="cluster",
    help="Manage clusters.",
    no_args_is_help=True,
)


def _cluster_to_dict(cluster: Any) -> dict[str, Any]:
    """Convert a Cluster object to a dict for output."""
    return {
        "key": cluster.key,
        "name": cluster.name,
        "status": cluster.get("status", ""),
        "total_nodes": cluster.get("total_nodes"),
        "online_nodes": cluster.get("online_nodes"),
        "total_ram_gb": cluster.get("total_ram_gb"),
        "ram_used_percent": cluster.get("ram_used_percent"),
        "total_cores": cluster.get("total_cores"),
        "running_machines": cluster.get("running_machines"),
        "is_compute": cluster.get("is_compute"),
        "is_storage": cluster.get("is_storage"),
    }


@app.command("list")
@handle_errors()
def cluster_list(
    ctx: typer.Context,
) -> None:
    """List all clusters."""
    vctx = get_context(ctx)

    clusters = vctx.client.clusters.list()
    data = [_cluster_to_dict(c) for c in clusters]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=CLUSTER_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def cluster_get(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
) -> None:
    """Get details of a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")
    cluster_obj = vctx.client.clusters.get(key)

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def cluster_create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Cluster name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Cluster description")
    ] = "",
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--no-enabled", help="Enable the cluster"),
    ] = None,
    compute: Annotated[
        bool | None,
        typer.Option("--compute/--no-compute", help="Mark as compute cluster"),
    ] = None,
) -> None:
    """Create a new cluster."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {
        "name": name,
        "description": description,
    }
    if enabled is not None:
        kwargs["enabled"] = enabled
    if compute is not None:
        kwargs["is_compute"] = compute

    cluster_obj = vctx.client.clusters.create(**kwargs)

    output_success(
        f"Created cluster '{cluster_obj.name}' (key: {cluster_obj.key})",
        quiet=vctx.quiet,
    )

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def cluster_update(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
    name: Annotated[
        str | None, typer.Option("--name", "-n", help="New cluster name")
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="Cluster description"),
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--no-enabled", help="Enable/disable the cluster"),
    ] = None,
    compute: Annotated[
        bool | None,
        typer.Option("--compute/--no-compute", help="Mark as compute cluster"),
    ] = None,
) -> None:
    """Update a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")

    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if enabled is not None:
        updates["enabled"] = enabled
    if compute is not None:
        updates["is_compute"] = compute

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    cluster_obj = vctx.client.clusters.update(key, **updates)

    output_success(f"Updated cluster '{cluster_obj.name}'", quiet=vctx.quiet)

    output_result(
        _cluster_to_dict(cluster_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def cluster_delete(
    ctx: typer.Context,
    cluster: Annotated[str, typer.Argument(help="Cluster name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Delete a cluster."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.clusters, cluster, "Cluster")
    cluster_obj = vctx.client.clusters.get(key)

    if not confirm_action(f"Delete cluster '{cluster_obj.name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.clusters.delete(key)
    output_success(f"Deleted cluster '{cluster_obj.name}'", quiet=vctx.quiet)


@app.command("vsan-status")
@handle_errors()
def cluster_vsan_status(
    ctx: typer.Context,
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Cluster name to query"),
    ] = None,
    include_tiers: Annotated[
        bool,
        typer.Option("--include-tiers", help="Include per-tier status"),
    ] = False,
) -> None:
    """Show vSAN status for a cluster."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {}
    if name is not None:
        kwargs["cluster_name"] = name
    if include_tiers:
        kwargs["include_tiers"] = True

    status = vctx.client.clusters.vsan_status(**kwargs)

    # vsan_status returns a dict or dict-like object
    if isinstance(status, dict):
        data = status
    else:
        data = dict(status) if hasattr(status, "__iter__") else {"result": str(status)}

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### `src/verge_cli/commands/node.py` (final)

```python
"""Node management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import NODE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="node",
    help="Manage nodes.",
    no_args_is_help=True,
)


def _node_to_dict(node: Any) -> dict[str, Any]:
    """Convert a Node object to a dict for output."""
    return {
        "key": node.key,
        "name": node.name,
        "status": node.get("status", ""),
        "cluster_name": node.get("cluster_name", ""),
        "ram_gb": node.get("ram_gb"),
        "cores": node.get("cores"),
        "cpu_usage": node.get("cpu_usage"),
        "is_physical": node.get("is_physical"),
        "model": node.get("model", ""),
        "cpu": node.get("cpu", ""),
        "core_temp": node.get("core_temp"),
        "vergeos_version": node.get("vergeos_version", ""),
    }


@app.command("list")
@handle_errors()
def node_list(
    ctx: typer.Context,
    cluster: Annotated[
        str | None,
        typer.Option("--cluster", "-c", help="Filter by cluster name"),
    ] = None,
) -> None:
    """List all nodes."""
    vctx = get_context(ctx)

    kwargs: dict[str, Any] = {}
    if cluster is not None:
        kwargs["cluster"] = cluster

    nodes = vctx.client.nodes.list(**kwargs)
    data = [_node_to_dict(n) for n in nodes]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=NODE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def node_get(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
) -> None:
    """Get details of a node."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.nodes, node, "Node")
    node_obj = vctx.client.nodes.get(key)

    output_result(
        _node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("maintenance")
@handle_errors()
def node_maintenance(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
    enable: Annotated[
        bool,
        typer.Option("--enable", help="Enable maintenance mode"),
    ] = False,
    disable: Annotated[
        bool,
        typer.Option("--disable", help="Disable maintenance mode"),
    ] = False,
) -> None:
    """Enable or disable maintenance mode on a node."""
    if enable == disable:
        typer.echo("Error: Specify exactly one of --enable or --disable.", err=True)
        raise typer.Exit(2)

    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.nodes, node, "Node")

    if enable:
        vctx.client.nodes.enable_maintenance(key)
        output_success(f"Enabled maintenance mode on node '{node}'", quiet=vctx.quiet)
    else:
        vctx.client.nodes.disable_maintenance(key)
        output_success(f"Disabled maintenance mode on node '{node}'", quiet=vctx.quiet)


@app.command("restart")
@handle_errors()
def node_restart(
    ctx: typer.Context,
    node: Annotated[str, typer.Argument(help="Node name or key")],
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation")
    ] = False,
) -> None:
    """Restart a node."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.nodes, node, "Node")

    if not confirm_action(f"Restart node '{node}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    vctx.client.nodes.restart(key)
    output_success(f"Restarting node '{node}'", quiet=vctx.quiet)
```

### `src/verge_cli/commands/storage.py` (final)

```python
"""Storage tier management commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import STORAGE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

app = typer.Typer(
    name="storage",
    help="Manage storage tiers.",
    no_args_is_help=True,
)


def _tier_to_dict(tier: Any) -> dict[str, Any]:
    """Convert a StorageTier object to a dict for output."""
    return {
        "key": tier.key,
        "tier": tier.get("tier"),
        "description": tier.get("description", ""),
        "capacity_gb": tier.get("capacity_gb"),
        "used_gb": tier.get("used_gb"),
        "free_gb": tier.get("free_gb"),
        "used_percent": tier.get("used_percent"),
        "dedupe_ratio": tier.get("dedupe_ratio"),
        "dedupe_savings_percent": tier.get("dedupe_savings_percent"),
        "read_ops": tier.get("read_ops"),
        "write_ops": tier.get("write_ops"),
    }


@app.command("list")
@handle_errors()
def storage_list(
    ctx: typer.Context,
) -> None:
    """List all storage tiers."""
    vctx = get_context(ctx)

    tiers = vctx.client.storage_tiers.list()
    data = [_tier_to_dict(t) for t in tiers]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=STORAGE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def storage_get(
    ctx: typer.Context,
    tier: Annotated[str, typer.Argument(help="Storage tier number or key")],
) -> None:
    """Get details of a storage tier."""
    vctx = get_context(ctx)

    # Storage tiers are typically accessed by numeric tier number or key.
    if tier.isdigit():
        tier_obj = vctx.client.storage_tiers.get(int(tier))
    else:
        key = resolve_resource_id(
            vctx.client.storage_tiers, tier, "Storage tier"
        )
        tier_obj = vctx.client.storage_tiers.get(key)

    output_result(
        _tier_to_dict(tier_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("summary")
@handle_errors()
def storage_summary(
    ctx: typer.Context,
) -> None:
    """Show aggregate storage summary across all tiers."""
    vctx = get_context(ctx)

    summary = vctx.client.storage_tiers.get_summary()

    # Summary returns a dict or dict-like object
    if isinstance(summary, dict):
        data = summary
    else:
        data = dict(summary) if hasattr(summary, "__iter__") else {"result": str(summary)}

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### `tests/unit/test_cluster.py` (final)

```python
"""Tests for cluster commands."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_cluster_list(cli_runner, mock_client, mock_cluster):
    """vrg cluster list should list all clusters."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.list.assert_called_once()


def test_cluster_list_empty(cli_runner, mock_client):
    """vrg cluster list should handle empty results."""
    mock_client.clusters.list.return_value = []

    result = cli_runner.invoke(app, ["cluster", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_cluster_list_json(cli_runner, mock_client, mock_cluster):
    """vrg cluster list --output json should output JSON."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["--output", "json", "cluster", "list"])

    assert result.exit_code == 0
    assert '"name": "Cluster1"' in result.output


def test_cluster_get(cli_runner, mock_client, mock_cluster):
    """vrg cluster get should show cluster details."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "Cluster1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output


def test_cluster_get_by_key(cli_runner, mock_client, mock_cluster):
    """vrg cluster get by numeric key should work."""
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(app, ["cluster", "get", "1"])

    assert result.exit_code == 0
    assert "Cluster1" in result.output


def test_cluster_create(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should create a new cluster."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "create", "--name", "Cluster1"]
    )

    assert result.exit_code == 0
    assert "Cluster1" in result.output
    mock_client.clusters.create.assert_called_once()


def test_cluster_create_with_options(cli_runner, mock_client, mock_cluster):
    """vrg cluster create should accept all options."""
    mock_client.clusters.create.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        [
            "cluster",
            "create",
            "--name",
            "Cluster1",
            "--description",
            "Primary",
            "--enabled",
            "--compute",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.create.call_args[1]
    assert call_kwargs["name"] == "Cluster1"
    assert call_kwargs["description"] == "Primary"
    assert call_kwargs["enabled"] is True
    assert call_kwargs["is_compute"] is True


def test_cluster_create_no_name(cli_runner, mock_client):
    """vrg cluster create without --name should fail."""
    result = cli_runner.invoke(app, ["cluster", "create"])

    assert result.exit_code == 2


def test_cluster_update(cli_runner, mock_client, mock_cluster):
    """vrg cluster update should update a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.update.return_value = mock_cluster

    result = cli_runner.invoke(
        app,
        ["cluster", "update", "Cluster1", "--description", "Updated"],
    )

    assert result.exit_code == 0
    mock_client.clusters.update.assert_called_once()
    call_args = mock_client.clusters.update.call_args
    assert call_args[0][0] == 1  # key
    assert call_args[1]["description"] == "Updated"


def test_cluster_update_no_changes(cli_runner, mock_client, mock_cluster):
    """vrg cluster update with no options should fail."""
    mock_client.clusters.list.return_value = [mock_cluster]

    result = cli_runner.invoke(app, ["cluster", "update", "Cluster1"])

    assert result.exit_code == 2


def test_cluster_delete(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete should delete a cluster."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "delete", "Cluster1", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_called_once_with(1)


def test_cluster_delete_without_yes(cli_runner, mock_client, mock_cluster):
    """vrg cluster delete without --yes should prompt and abort on 'n'."""
    mock_client.clusters.list.return_value = [mock_cluster]
    mock_client.clusters.get.return_value = mock_cluster

    result = cli_runner.invoke(
        app, ["cluster", "delete", "Cluster1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.clusters.delete.assert_not_called()


def test_cluster_vsan_status(cli_runner, mock_client):
    """vrg cluster vsan-status should show vSAN health."""
    mock_status = {
        "status": "healthy",
        "total_drives": 24,
        "online_drives": 24,
        "rebuilding": False,
    }
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(app, ["cluster", "vsan-status"])

    assert result.exit_code == 0
    assert "healthy" in result.output
    mock_client.clusters.vsan_status.assert_called_once()


def test_cluster_vsan_status_with_name(cli_runner, mock_client):
    """vrg cluster vsan-status --name should pass cluster name."""
    mock_status = {"status": "healthy", "total_drives": 8}
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["cluster", "vsan-status", "--name", "Cluster1"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["cluster_name"] == "Cluster1"


def test_cluster_vsan_status_with_tiers(cli_runner, mock_client):
    """vrg cluster vsan-status --include-tiers should pass flag."""
    mock_status = {
        "status": "healthy",
        "tiers": [{"tier": 1, "status": "online"}],
    }
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["cluster", "vsan-status", "--include-tiers"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.clusters.vsan_status.call_args[1]
    assert call_kwargs["include_tiers"] is True


def test_cluster_vsan_status_json(cli_runner, mock_client):
    """vrg cluster vsan-status with JSON output."""
    mock_status = {"status": "healthy", "total_drives": 24}
    mock_client.clusters.vsan_status.return_value = mock_status

    result = cli_runner.invoke(
        app, ["--output", "json", "cluster", "vsan-status"]
    )

    assert result.exit_code == 0
    assert '"status": "healthy"' in result.output
```

### `tests/unit/test_node.py` (final)

```python
"""Tests for node commands."""

from verge_cli.cli import app


def test_node_list(cli_runner, mock_client, mock_node):
    """vrg node list should list all nodes."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "node1" in result.output
    mock_client.nodes.list.assert_called_once()


def test_node_list_empty(cli_runner, mock_client):
    """vrg node list should handle empty results."""
    mock_client.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["node", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_node_list_with_cluster_filter(cli_runner, mock_client, mock_node):
    """vrg node list --cluster should filter by cluster name."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "list", "--cluster", "Cluster1"])

    assert result.exit_code == 0
    assert "node1" in result.output
    call_kwargs = mock_client.nodes.list.call_args[1]
    assert call_kwargs["cluster"] == "Cluster1"


def test_node_list_json(cli_runner, mock_client, mock_node):
    """vrg node list --output json should output JSON."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["--output", "json", "node", "list"])

    assert result.exit_code == 0
    assert '"name": "node1"' in result.output


def test_node_get(cli_runner, mock_client, mock_node):
    """vrg node get should show node details."""
    mock_client.nodes.list.return_value = [mock_node]
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "node1"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_get_by_key(cli_runner, mock_client, mock_node):
    """vrg node get by numeric key should work."""
    mock_client.nodes.get.return_value = mock_node

    result = cli_runner.invoke(app, ["node", "get", "10"])

    assert result.exit_code == 0
    assert "node1" in result.output


def test_node_maintenance_enable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --enable should enable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--enable"]
    )

    assert result.exit_code == 0
    mock_client.nodes.enable_maintenance.assert_called_once_with(10)


def test_node_maintenance_disable(cli_runner, mock_client, mock_node):
    """vrg node maintenance --disable should disable maintenance."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--disable"]
    )

    assert result.exit_code == 0
    mock_client.nodes.disable_maintenance.assert_called_once_with(10)


def test_node_maintenance_no_flag(cli_runner, mock_client, mock_node):
    """vrg node maintenance without --enable or --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(app, ["node", "maintenance", "node1"])

    assert result.exit_code == 2


def test_node_maintenance_both_flags(cli_runner, mock_client, mock_node):
    """vrg node maintenance with both --enable and --disable should fail."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "maintenance", "node1", "--enable", "--disable"]
    )

    assert result.exit_code == 2


def test_node_restart(cli_runner, mock_client, mock_node):
    """vrg node restart --yes should restart the node."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "restart", "node1", "--yes"]
    )

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_called_once_with(10)


def test_node_restart_without_yes(cli_runner, mock_client, mock_node):
    """vrg node restart without --yes should prompt and abort on 'n'."""
    mock_client.nodes.list.return_value = [mock_node]

    result = cli_runner.invoke(
        app, ["node", "restart", "node1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_client.nodes.restart.assert_not_called()
```

### `tests/unit/test_storage.py` (final)

```python
"""Tests for storage tier commands."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_storage_list(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list should list all storage tiers."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.list.assert_called_once()


def test_storage_list_empty(cli_runner, mock_client):
    """vrg storage list should handle empty results."""
    mock_client.storage_tiers.list.return_value = []

    result = cli_runner.invoke(app, ["storage", "list"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_storage_list_json(cli_runner, mock_client, mock_storage_tier):
    """vrg storage list --output json should output JSON."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]

    result = cli_runner.invoke(app, ["--output", "json", "storage", "list"])

    assert result.exit_code == 0
    assert '"description": "SSD Storage"' in result.output


def test_storage_get(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get should show tier details."""
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "1"])

    assert result.exit_code == 0
    assert "SSD" in result.output
    mock_client.storage_tiers.get.assert_called_once_with(1)


def test_storage_get_by_name(cli_runner, mock_client, mock_storage_tier):
    """vrg storage get by name should resolve and show details."""
    mock_client.storage_tiers.list.return_value = [mock_storage_tier]
    mock_client.storage_tiers.get.return_value = mock_storage_tier

    result = cli_runner.invoke(app, ["storage", "get", "Tier 1 - SSD"])

    assert result.exit_code == 0
    assert "SSD" in result.output


def test_storage_summary(cli_runner, mock_client):
    """vrg storage summary should show aggregate storage data."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
        "tier_count": 2,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(app, ["storage", "summary"])

    assert result.exit_code == 0
    assert "20480" in result.output
    mock_client.storage_tiers.get_summary.assert_called_once()


def test_storage_summary_json(cli_runner, mock_client):
    """vrg storage summary with JSON output."""
    mock_summary = {
        "total_capacity_gb": 20480,
        "total_used_gb": 12288,
        "total_free_gb": 8192,
        "overall_used_percent": 60.0,
    }
    mock_client.storage_tiers.get_summary.return_value = mock_summary

    result = cli_runner.invoke(
        app, ["--output", "json", "storage", "summary"]
    )

    assert result.exit_code == 0
    assert '"total_capacity_gb": 20480' in result.output
```

### `src/verge_cli/cli.py` (final diff)

The only changes needed:

**Line 11** — update import:
```python
from verge_cli.commands import cluster, configure, network, node, storage, system, vm
```

**Lines 21-24** — update registrations:
```python
# Register sub-commands
app.add_typer(cluster.app, name="cluster")
app.add_typer(configure.app, name="configure")
app.add_typer(network.app, name="network")
app.add_typer(node.app, name="node")
app.add_typer(storage.app, name="storage")
app.add_typer(system.app, name="system")
app.add_typer(vm.app, name="vm")
```

---

## Summary

| Task | Files Created/Modified | Tests | Commands Added |
|------|----------------------|-------|----------------|
| 1 | `conftest.py`, `columns.py` | 0 (fixtures only) | 0 |
| 2 | `cluster.py`, `test_cluster.py`, `cli.py` | 5 | cluster list, get |
| 3 | `cluster.py`, `test_cluster.py` | 7 | cluster create, update, delete |
| 4 | `cluster.py`, `test_cluster.py` | 4 | cluster vsan-status |
| 5 | `node.py`, `test_node.py`, `cli.py` | 6 | node list, get |
| 6 | `node.py`, `test_node.py` | 6 | node maintenance, restart |
| 7 | `storage.py`, `test_storage.py`, `cli.py` | 7 | storage list, get, summary |
| 8 | `cli.py` (verify) | 0 (regression) | 0 |
| **Total** | **8 files** | **35 tests** | **12 commands** |

### Estimated Time

| Task | Estimated Time |
|------|---------------|
| Task 1: Fixtures + columns | 3-5 min |
| Task 2: Cluster list + get | 3-5 min |
| Task 3: Cluster create/update/delete | 3-5 min |
| Task 4: Cluster vsan-status | 2-3 min |
| Task 5: Node list + get | 3-5 min |
| Task 6: Node maintenance + restart | 3-5 min |
| Task 7: Storage list/get/summary | 3-5 min |
| Task 8: Registration + regression | 2-3 min |
| **Total** | **22-36 min** |

---

## Task Checklist

- [x] Task 1: Add conftest fixtures + column definitions
- [x] Task 2: cluster.py — list + get commands (TDD)
- [x] Task 3: cluster.py — create, update, delete (TDD)
- [ ] Task 4: cluster.py — vsan-status command (TDD)
- [ ] Task 5: node.py — list + get commands (TDD)
- [ ] Task 6: node.py — maintenance + restart (TDD)
- [ ] Task 7: storage.py — list, get, summary (TDD)
- [ ] Task 8: Registration + full regression
