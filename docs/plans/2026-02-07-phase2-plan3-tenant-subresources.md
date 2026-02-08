# Phase 2 Plan 3: Tenant Sub-Resource Commands

**Goal:** Add tenant sub-resource management — compute nodes, storage allocation, networking (3 types), snapshots, and monitoring (stats + logs).

**Architecture:** Five new command modules following the vm_drive.py sub-resource pattern. Each uses a `_get_tenant()` helper that resolves the parent tenant and returns `(vctx, tenant_obj)`. Registration in `tenant.py` as sub-Typers.

**Tech Stack:** Python 3.10+, Typer, Rich, pyvergeos SDK, pytest

**Prerequisite:** Plan 2 (Tenant Core) must be completed first — it creates `tenant.py` which these modules register into.

---

## Task 1: Column definitions for all tenant sub-resources

### 1A: Add epoch formatting helpers to columns.py

Add two shared helper functions to `src/verge_cli/columns.py`, right after the `default_format` function (after line 113):

```python
def format_epoch(value: Any, *, for_csv: bool = False) -> str:
    """Format an epoch timestamp as a datetime string."""
    if value is None:
        return "" if for_csv else "-"
    if isinstance(value, (int, float)) and value > 0:
        dt = datetime.fromtimestamp(value)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def format_epoch_or_never(value: Any, *, for_csv: bool = False) -> str:
    """Format an epoch timestamp, treating 0/None as 'Never'."""
    if value is None or value == 0:
        return "" if for_csv else "Never"
    return format_epoch(value, for_csv=for_csv)
```

### 1B: Add storage used-percent style function

Add a shared `style_fn` to `columns.py` right after the epoch helpers:

```python
def style_percent_threshold(value: Any, row: dict[str, Any]) -> str | None:
    """Style function for percentage values — red >80, yellow >60."""
    if isinstance(value, (int, float)):
        if value > 80:
            return "red bold"
        if value > 60:
            return "yellow"
    return None
```

### 1C: Add TENANT_NODE_COLUMNS

Add at end of `src/verge_cli/columns.py`:

```python
TENANT_NODE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("cpu_cores", header="CPU"),
    ColumnDef("ram_gb", header="RAM GB"),
    ColumnDef("status", style_map=STATUS_STYLES, normalize_fn=normalize_lower),
    ColumnDef("is_enabled", header="Enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
    # wide-only
    ColumnDef("cluster_name", header="Cluster", wide_only=True),
    ColumnDef("host_node", header="Host Node", wide_only=True),
]
```

### 1D: Add TENANT_STORAGE_COLUMNS

```python
TENANT_STORAGE_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("tier_name", header="Tier"),
    ColumnDef("provisioned_gb", header="Provisioned GB"),
    # wide-only
    ColumnDef("used_gb", header="Used GB", wide_only=True),
    ColumnDef(
        "used_percent",
        header="Used %",
        wide_only=True,
        style_fn=style_percent_threshold,
    ),
]
```

### 1E: Add TENANT_NET_BLOCK_COLUMNS, TENANT_EXT_IP_COLUMNS, TENANT_L2_COLUMNS

```python
TENANT_NET_BLOCK_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("cidr", header="CIDR"),
    ColumnDef("network_name", header="Network"),
    # wide-only
    ColumnDef("description", wide_only=True),
]

TENANT_EXT_IP_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("ip_address", header="IP"),
    ColumnDef("network_name", header="Network"),
    # wide-only
    ColumnDef("hostname", wide_only=True),
]

TENANT_L2_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("network_name", header="Network"),
    ColumnDef("network_type", header="Type"),
    ColumnDef("is_enabled", header="Enabled", format_fn=format_bool_yn, style_map=BOOL_STYLES),
]
```

### 1F: Add TENANT_SNAPSHOT_COLUMNS

```python
TENANT_SNAPSHOT_COLUMNS = [
    ColumnDef("$key", header="Key"),
    ColumnDef("name"),
    ColumnDef("created", format_fn=format_epoch),
    ColumnDef("expires", format_fn=format_epoch_or_never),
    # wide-only
    ColumnDef("profile", wide_only=True),
]
```

### 1G: Add TENANT_STATS_COLUMNS and TENANT_LOG_COLUMNS

```python
TENANT_STATS_COLUMNS = [
    ColumnDef("timestamp", format_fn=format_epoch),
    ColumnDef("cpu_percent", header="CPU %", style_fn=style_percent_threshold),
    ColumnDef("ram_used_mb", header="RAM Used MB"),
    ColumnDef("ram_total_mb", header="RAM Total MB"),
    ColumnDef("disk_read_ops", header="Disk Read IOPS"),
    ColumnDef("disk_write_ops", header="Disk Write IOPS"),
]

TENANT_LOG_COLUMNS = [
    ColumnDef("timestamp", header="Time"),
    ColumnDef("type", header="Type"),
    ColumnDef("message", header="Message"),
]
```

### Verify

```bash
uv run ruff check src/verge_cli/columns.py
uv run mypy src/verge_cli/columns.py
```

### Commit

```bash
git add src/verge_cli/columns.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant sub-resource column definitions

Add ColumnDef lists for all tenant sub-resources (nodes, storage,
net-blocks, external IPs, L2 networks, snapshots, stats, logs).
Also add shared epoch formatting helpers and percent threshold style_fn.
EOF
)"
```

---

## Task 2: tenant_node.py — list + get (TDD)

### 2A: Write failing tests for list and get

Create `tests/unit/test_tenant_node.py`:

```python
"""Tests for tenant node sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Acme Corp Tenant",
            "status": "online",
            "state": "running",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


@pytest.fixture
def mock_tenant_node() -> MagicMock:
    """Create a mock Tenant Node object."""
    node = MagicMock()
    node.key = 100
    node.name = "tenant-node-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 100,
            "name": "tenant-node-1",
            "cpu_cores": 4,
            "ram": 8192,
            "status": "running",
            "enabled": True,
            "cluster": 1,
            "cluster_name": "Cluster1",
            "host_node": "Node1",
        }
        return data.get(key, default)

    node.get = mock_get
    return node


def test_tenant_node_list(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node list should list nodes on a tenant."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(app, ["tenant", "node", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output
    mock_tenant.nodes.list.assert_called_once()


def test_tenant_node_get(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node get should show node details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]
    mock_tenant.nodes.get.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app, ["tenant", "node", "get", "acme-corp", "tenant-node-1"]
    )

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output


def test_tenant_node_get_by_key(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node get should accept numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.get.return_value = mock_tenant_node

    result = cli_runner.invoke(app, ["tenant", "node", "get", "acme-corp", "100"])

    assert result.exit_code == 0
    assert "tenant-node-1" in result.output


def test_tenant_node_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant node list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "node", "list", "acme-corp"])

    assert result.exit_code == 0
```

### Run tests (should fail — module doesn't exist yet)

```bash
uv run pytest tests/unit/test_tenant_node.py -v -k "test_tenant_node_list or test_tenant_node_get" 2>&1 | head -20
```

### 2B: Create tenant_node.py with list and get

Create `src/verge_cli/commands/tenant_node.py`:

```python
"""Tenant node (compute allocation) sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_NODE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="node",
    help="Manage tenant compute nodes.",
    no_args_is_help=True,
)


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


def _tenant_node_to_dict(node: Any) -> dict[str, Any]:
    """Convert a Tenant Node object to a dict for output."""
    return {
        "$key": node.key,
        "name": node.name,
        "cpu_cores": node.get("cpu_cores"),
        "ram_gb": node.get("ram"),
        "status": node.get("status", ""),
        "is_enabled": node.get("enabled"),
        "cluster_name": node.get("cluster_name", ""),
        "host_node": node.get("host_node", ""),
    }


def _resolve_tenant_node(tenant_obj: Any, identifier: str) -> int:
    """Resolve a tenant node name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    nodes = tenant_obj.nodes.list()
    matches = [n for n in nodes if n.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple tenant nodes match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Tenant node '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def tenant_node_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List compute nodes allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    nodes = tenant_obj.nodes.list()
    data = [_tenant_node_to_dict(n) for n in nodes]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_NODE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_node_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    node: Annotated[str, typer.Argument(help="Node name or key")],
) -> None:
    """Get details of a tenant compute node."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    node_key = _resolve_tenant_node(tenant_obj, node)
    node_obj = tenant_obj.nodes.get(node_key)
    output_result(
        _tenant_node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### 2C: Register in tenant.py

Add import and registration at the top of `src/verge_cli/commands/tenant.py` (after existing imports and `app` definition):

```python
from verge_cli.commands import tenant_node

# ... after app = typer.Typer(...)
app.add_typer(tenant_node.app, name="node")
```

### Run tests

```bash
uv run pytest tests/unit/test_tenant_node.py -v -k "test_tenant_node_list or test_tenant_node_get"
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_node.py
uv run mypy src/verge_cli/commands/tenant_node.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_node.py tests/unit/test_tenant_node.py src/verge_cli/commands/tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant node list and get commands

Implement tenant node sub-resource with list and get commands following
the vm_drive.py sub-resource pattern. Includes _get_tenant helper,
_resolve_tenant_node resolver, and full test coverage.
EOF
)"
```

---

## Task 3: tenant_node.py — create, update, delete (TDD)

### 3A: Write failing tests for create, update, delete

Append to `tests/unit/test_tenant_node.py`:

```python
def test_tenant_node_create(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node create should create a compute node."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.create.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "create",
            "acme-corp",
            "--cpu-cores",
            "4",
            "--ram-gb",
            "8",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.nodes.create.assert_called_once()
    call_kwargs = mock_tenant.nodes.create.call_args[1]
    assert call_kwargs["cpu_cores"] == 4
    assert call_kwargs["ram_gb"] == 8


def test_tenant_node_create_with_options(
    cli_runner, mock_client, mock_tenant, mock_tenant_node
):
    """vrg tenant node create should accept optional flags."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.create.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "create",
            "acme-corp",
            "--cpu-cores",
            "8",
            "--ram-gb",
            "16",
            "--cluster",
            "1",
            "--name",
            "big-node",
            "--preferred-node",
            "2",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.nodes.create.call_args[1]
    assert call_kwargs["cpu_cores"] == 8
    assert call_kwargs["ram_gb"] == 16
    assert call_kwargs["cluster"] == 1
    assert call_kwargs["name"] == "big-node"
    assert call_kwargs["preferred_node"] == 2


def test_tenant_node_update(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node update should update node properties."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]
    mock_tenant.nodes.update.return_value = mock_tenant_node

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "node",
            "update",
            "acme-corp",
            "tenant-node-1",
            "--cpu-cores",
            "8",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.nodes.update.assert_called_once()


def test_tenant_node_update_no_changes(cli_runner, mock_client, mock_tenant):
    """vrg tenant node update with no flags should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(
        app, ["tenant", "node", "update", "acme-corp", "tenant-node-1"]
    )

    assert result.exit_code == 2


def test_tenant_node_delete(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node delete should remove a node with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(
        app, ["tenant", "node", "delete", "acme-corp", "tenant-node-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.nodes.delete.assert_called_once_with(100)


def test_tenant_node_delete_cancelled(cli_runner, mock_client, mock_tenant, mock_tenant_node):
    """vrg tenant node delete without --yes should prompt and cancel on 'n'."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.nodes.list.return_value = [mock_tenant_node]

    result = cli_runner.invoke(
        app, ["tenant", "node", "delete", "acme-corp", "tenant-node-1"], input="n\n"
    )

    assert result.exit_code == 0
    mock_tenant.nodes.delete.assert_not_called()
```

### Run tests (create/update/delete should fail)

```bash
uv run pytest tests/unit/test_tenant_node.py -v -k "create or update or delete" 2>&1 | head -20
```

### 3B: Add create, update, delete to tenant_node.py

Append to `src/verge_cli/commands/tenant_node.py`:

```python
@app.command("create")
@handle_errors()
def tenant_node_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    cpu_cores: Annotated[int, typer.Option("--cpu-cores", help="Number of CPU cores")],
    ram_gb: Annotated[int, typer.Option("--ram-gb", help="RAM in GB")],
    cluster: Annotated[int | None, typer.Option("--cluster", help="Cluster key")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="Node name")] = None,
    preferred_node: Annotated[
        int | None, typer.Option("--preferred-node", help="Preferred host node key")
    ] = None,
) -> None:
    """Allocate a compute node to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    node_obj = tenant_obj.nodes.create(
        cpu_cores=cpu_cores,
        ram_gb=ram_gb,
        cluster=cluster,
        name=name,
        preferred_node=preferred_node,
    )

    output_success(
        f"Created tenant node '{node_obj.name}' (key: {node_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _tenant_node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def tenant_node_update(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    node: Annotated[str, typer.Argument(help="Node name or key")],
    cpu_cores: Annotated[int | None, typer.Option("--cpu-cores", help="Number of CPU cores")] = None,
    ram_gb: Annotated[int | None, typer.Option("--ram-gb", help="RAM in GB")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name")] = None,
    enabled: Annotated[
        bool | None, typer.Option("--enabled/--disabled", help="Enable/disable node")
    ] = None,
) -> None:
    """Update a tenant compute node."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    node_key = _resolve_tenant_node(tenant_obj, node)

    updates: dict[str, Any] = {}
    if cpu_cores is not None:
        updates["cpu_cores"] = cpu_cores
    if ram_gb is not None:
        updates["ram_gb"] = ram_gb
    if name is not None:
        updates["name"] = name
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    node_obj = tenant_obj.nodes.update(node_key, **updates)
    output_success(f"Updated tenant node '{node_obj.name}'", quiet=vctx.quiet)
    output_result(
        _tenant_node_to_dict(node_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def tenant_node_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    node: Annotated[str, typer.Argument(help="Node name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a compute node from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    node_key = _resolve_tenant_node(tenant_obj, node)

    if not confirm_action(f"Delete tenant node '{node}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.nodes.delete(node_key)
    output_success(f"Deleted tenant node '{node}'", quiet=vctx.quiet)
```

### Run all tenant_node tests

```bash
uv run pytest tests/unit/test_tenant_node.py -v
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_node.py tests/unit/test_tenant_node.py
uv run mypy src/verge_cli/commands/tenant_node.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_node.py tests/unit/test_tenant_node.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant node create, update, delete commands

Complete tenant node sub-resource with create (--cpu-cores, --ram-gb),
update (--cpu-cores, --ram-gb, --name, --enabled/--disabled), and
delete (--yes) commands with full test coverage.
EOF
)"
```

---

## Task 4: tenant_storage.py — full CRUD (TDD)

### 4A: Write failing tests

Create `tests/unit/test_tenant_storage.py`:

```python
"""Tests for tenant storage sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Acme Corp Tenant",
            "status": "online",
            "state": "running",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


@pytest.fixture
def mock_tenant_storage() -> MagicMock:
    """Create a mock Tenant Storage object."""
    storage = MagicMock()
    storage.key = 200
    storage.name = "Tier 3 Storage"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 200,
            "name": "Tier 3 Storage",
            "tier_name": "Tier 3",
            "tier": 3,
            "provisioned_gb": 500,
            "used_gb": 120,
            "used_percent": 24.0,
        }
        return data.get(key, default)

    storage.get = mock_get
    return storage


def test_tenant_storage_list(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage list should list storage allocations."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.list.return_value = [mock_tenant_storage]

    result = cli_runner.invoke(app, ["tenant", "storage", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "Tier 3" in result.output
    mock_tenant.storage.list.assert_called_once()


def test_tenant_storage_get(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage get should show storage details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.list.return_value = [mock_tenant_storage]
    mock_tenant.storage.get.return_value = mock_tenant_storage

    result = cli_runner.invoke(
        app, ["tenant", "storage", "get", "acme-corp", "Tier 3 Storage"]
    )

    assert result.exit_code == 0
    assert "Tier 3" in result.output


def test_tenant_storage_get_by_key(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage get should accept numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.get.return_value = mock_tenant_storage

    result = cli_runner.invoke(app, ["tenant", "storage", "get", "acme-corp", "200"])

    assert result.exit_code == 0


def test_tenant_storage_create(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage create should allocate storage."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.create.return_value = mock_tenant_storage

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "storage",
            "create",
            "acme-corp",
            "--tier",
            "3",
            "--provisioned-gb",
            "500",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.storage.create.assert_called_once()
    call_kwargs = mock_tenant.storage.create.call_args[1]
    assert call_kwargs["tier"] == 3
    assert call_kwargs["provisioned_gb"] == 500


def test_tenant_storage_update(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage update should modify storage."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.list.return_value = [mock_tenant_storage]
    mock_tenant.storage.update.return_value = mock_tenant_storage

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "storage",
            "update",
            "acme-corp",
            "Tier 3 Storage",
            "--provisioned-gb",
            "1000",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.storage.update.assert_called_once()


def test_tenant_storage_update_no_changes(cli_runner, mock_client, mock_tenant):
    """vrg tenant storage update with no flags should exit 2."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant

    result = cli_runner.invoke(
        app, ["tenant", "storage", "update", "acme-corp", "Tier 3 Storage"]
    )

    assert result.exit_code == 2


def test_tenant_storage_delete(cli_runner, mock_client, mock_tenant, mock_tenant_storage):
    """vrg tenant storage delete should remove storage with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.list.return_value = [mock_tenant_storage]

    result = cli_runner.invoke(
        app,
        ["tenant", "storage", "delete", "acme-corp", "Tier 3 Storage", "--yes"],
    )

    assert result.exit_code == 0
    mock_tenant.storage.delete.assert_called_once_with(200)


def test_tenant_storage_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant storage list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.storage.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "storage", "list", "acme-corp"])

    assert result.exit_code == 0
```

### Run tests (should fail)

```bash
uv run pytest tests/unit/test_tenant_storage.py -v 2>&1 | head -20
```

### 4B: Create tenant_storage.py

Create `src/verge_cli/commands/tenant_storage.py`:

```python
"""Tenant storage allocation sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_STORAGE_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="storage",
    help="Manage tenant storage allocations.",
    no_args_is_help=True,
)


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


def _tenant_storage_to_dict(storage: Any) -> dict[str, Any]:
    """Convert a Tenant Storage object to a dict for output."""
    return {
        "$key": storage.key,
        "tier_name": storage.get("tier_name", ""),
        "provisioned_gb": storage.get("provisioned_gb"),
        "used_gb": storage.get("used_gb"),
        "used_percent": storage.get("used_percent"),
    }


def _resolve_tenant_storage(tenant_obj: Any, identifier: str) -> int:
    """Resolve a tenant storage name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    items = tenant_obj.storage.list()
    matches = [s for s in items if s.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple storage allocations match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Storage allocation '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def tenant_storage_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List storage allocations for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    items = tenant_obj.storage.list()
    data = [_tenant_storage_to_dict(s) for s in items]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_STORAGE_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def tenant_storage_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    storage: Annotated[str, typer.Argument(help="Storage name or key")],
) -> None:
    """Get details of a tenant storage allocation."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    storage_key = _resolve_tenant_storage(tenant_obj, storage)
    storage_obj = tenant_obj.storage.get(storage_key)
    output_result(
        _tenant_storage_to_dict(storage_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def tenant_storage_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    tier: Annotated[int, typer.Option("--tier", "-t", help="Storage tier number")],
    provisioned_gb: Annotated[
        int, typer.Option("--provisioned-gb", help="Provisioned size in GB")
    ],
) -> None:
    """Allocate storage to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    storage_obj = tenant_obj.storage.create(
        tier=tier,
        provisioned_gb=provisioned_gb,
    )

    output_success(
        f"Created storage allocation (key: {storage_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _tenant_storage_to_dict(storage_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def tenant_storage_update(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    storage: Annotated[str, typer.Argument(help="Storage name or key")],
    provisioned_gb: Annotated[
        int | None, typer.Option("--provisioned-gb", help="New provisioned size in GB")
    ] = None,
) -> None:
    """Update a tenant storage allocation."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    storage_key = _resolve_tenant_storage(tenant_obj, storage)

    updates: dict[str, Any] = {}
    if provisioned_gb is not None:
        updates["provisioned_gb"] = provisioned_gb

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    storage_obj = tenant_obj.storage.update(storage_key, **updates)
    output_success(f"Updated storage allocation", quiet=vctx.quiet)
    output_result(
        _tenant_storage_to_dict(storage_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def tenant_storage_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    storage: Annotated[str, typer.Argument(help="Storage name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a storage allocation from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    storage_key = _resolve_tenant_storage(tenant_obj, storage)

    if not confirm_action(f"Delete storage allocation '{storage}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.storage.delete(storage_key)
    output_success(f"Deleted storage allocation '{storage}'", quiet=vctx.quiet)
```

### 4C: Register in tenant.py

Add to `src/verge_cli/commands/tenant.py`:

```python
from verge_cli.commands import tenant_storage

app.add_typer(tenant_storage.app, name="storage")
```

### Run tests

```bash
uv run pytest tests/unit/test_tenant_storage.py -v
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_storage.py tests/unit/test_tenant_storage.py
uv run mypy src/verge_cli/commands/tenant_storage.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_storage.py tests/unit/test_tenant_storage.py src/verge_cli/commands/tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant storage CRUD commands

Implement tenant storage sub-resource with list, get, create, update,
and delete commands. Supports --tier, --provisioned-gb options with
full test coverage.
EOF
)"
```

---

## Task 5: tenant_net.py — three sub-Typer apps (TDD)

### 5A: Write failing tests

Create `tests/unit/test_tenant_net.py`:

```python
"""Tests for tenant networking sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Acme Corp Tenant",
            "status": "online",
            "state": "running",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


# --- Network Block fixtures ---


@pytest.fixture
def mock_net_block() -> MagicMock:
    """Create a mock Network Block object."""
    block = MagicMock()
    block.key = 300
    block.name = "block-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 300,
            "cidr": "10.0.0.0/24",
            "network_name": "DMZ",
            "description": "DMZ network block",
        }
        return data.get(key, default)

    block.get = mock_get
    return block


# --- External IP fixtures ---


@pytest.fixture
def mock_ext_ip() -> MagicMock:
    """Create a mock External IP object."""
    ip = MagicMock()
    ip.key = 400
    ip.name = "ext-ip-1"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 400,
            "ip_address": "203.0.113.10",
            "network_name": "External",
            "hostname": "web.acme.com",
        }
        return data.get(key, default)

    ip.get = mock_get
    return ip


# --- L2 Network fixtures ---


@pytest.fixture
def mock_l2() -> MagicMock:
    """Create a mock L2 Network object."""
    l2 = MagicMock()
    l2.key = 500
    l2.name = "l2-trunk"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 500,
            "network_name": "Trunk VLAN",
            "network_type": "physical",
            "enabled": True,
        }
        return data.get(key, default)

    l2.get = mock_get
    return l2


# ===== Network Block Tests =====


def test_net_block_list(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block list should list network blocks."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = [mock_net_block]

    result = cli_runner.invoke(app, ["tenant", "net-block", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "10.0.0.0/24" in result.output
    mock_tenant.network_blocks.list.assert_called_once()


def test_net_block_create(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block create should create a network block."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.create.return_value = mock_net_block

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "net-block",
            "create",
            "acme-corp",
            "--cidr",
            "10.0.0.0/24",
            "--network",
            "1",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.network_blocks.create.assert_called_once()
    call_kwargs = mock_tenant.network_blocks.create.call_args[1]
    assert call_kwargs["cidr"] == "10.0.0.0/24"
    assert call_kwargs["network"] == 1


def test_net_block_delete(cli_runner, mock_client, mock_tenant, mock_net_block):
    """vrg tenant net-block delete should remove a block with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = [mock_net_block]

    result = cli_runner.invoke(
        app, ["tenant", "net-block", "delete", "acme-corp", "block-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.network_blocks.delete.assert_called_once_with(300)


def test_net_block_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant net-block list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.network_blocks.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "net-block", "list", "acme-corp"])

    assert result.exit_code == 0


# ===== External IP Tests =====


def test_ext_ip_list(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip list should list external IPs."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.list.return_value = [mock_ext_ip]

    result = cli_runner.invoke(app, ["tenant", "ext-ip", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "203.0.113.10" in result.output
    mock_tenant.external_ips.list.assert_called_once()


def test_ext_ip_create(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip create should create an external IP."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.create.return_value = mock_ext_ip

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "ext-ip",
            "create",
            "acme-corp",
            "--ip",
            "203.0.113.10",
            "--network",
            "2",
            "--hostname",
            "web.acme.com",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.external_ips.create.assert_called_once()
    call_kwargs = mock_tenant.external_ips.create.call_args[1]
    assert call_kwargs["ip"] == "203.0.113.10"
    assert call_kwargs["network"] == 2
    assert call_kwargs["hostname"] == "web.acme.com"


def test_ext_ip_delete(cli_runner, mock_client, mock_tenant, mock_ext_ip):
    """vrg tenant ext-ip delete should remove an IP with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.external_ips.list.return_value = [mock_ext_ip]

    result = cli_runner.invoke(
        app, ["tenant", "ext-ip", "delete", "acme-corp", "ext-ip-1", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.external_ips.delete.assert_called_once_with(400)


# ===== L2 Network Tests =====


def test_l2_list(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 list should list L2 networks."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.list.return_value = [mock_l2]

    result = cli_runner.invoke(app, ["tenant", "l2", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "Trunk VLAN" in result.output
    mock_tenant.l2_networks.list.assert_called_once()


def test_l2_create(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 create should create an L2 network."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.create.return_value = mock_l2

    result = cli_runner.invoke(
        app,
        ["tenant", "l2", "create", "acme-corp", "--network-name", "Trunk VLAN"],
    )

    assert result.exit_code == 0
    mock_tenant.l2_networks.create.assert_called_once()
    call_kwargs = mock_tenant.l2_networks.create.call_args[1]
    assert call_kwargs["network_name"] == "Trunk VLAN"


def test_l2_delete(cli_runner, mock_client, mock_tenant, mock_l2):
    """vrg tenant l2 delete should remove an L2 network with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.l2_networks.list.return_value = [mock_l2]

    result = cli_runner.invoke(
        app, ["tenant", "l2", "delete", "acme-corp", "l2-trunk", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.l2_networks.delete.assert_called_once_with(500)
```

### Run tests (should fail)

```bash
uv run pytest tests/unit/test_tenant_net.py -v 2>&1 | head -20
```

### 5B: Create tenant_net.py

Create `src/verge_cli/commands/tenant_net.py`:

```python
"""Tenant networking sub-resource commands (net-block, ext-ip, l2)."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import (
    TENANT_EXT_IP_COLUMNS,
    TENANT_L2_COLUMNS,
    TENANT_NET_BLOCK_COLUMNS,
)
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

# ---------------------------------------------------------------------------
# Three Typer apps for three networking sub-resources
# ---------------------------------------------------------------------------

net_block_app = typer.Typer(
    name="net-block",
    help="Manage tenant network blocks.",
    no_args_is_help=True,
)

ext_ip_app = typer.Typer(
    name="ext-ip",
    help="Manage tenant external IPs.",
    no_args_is_help=True,
)

l2_app = typer.Typer(
    name="l2",
    help="Manage tenant L2 networks.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


# ---------------------------------------------------------------------------
# Sub-resource resolvers
# ---------------------------------------------------------------------------


def _resolve_net_block(tenant_obj: Any, identifier: str) -> int:
    """Resolve a network block name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    blocks = tenant_obj.network_blocks.list()
    matches = [b for b in blocks if b.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple network blocks match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Network block '{identifier}' not found.", err=True)
    raise typer.Exit(6)


def _resolve_ext_ip(tenant_obj: Any, identifier: str) -> int:
    """Resolve an external IP name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    ips = tenant_obj.external_ips.list()
    matches = [i for i in ips if i.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple external IPs match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: External IP '{identifier}' not found.", err=True)
    raise typer.Exit(6)


def _resolve_l2(tenant_obj: Any, identifier: str) -> int:
    """Resolve an L2 network name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    l2s = tenant_obj.l2_networks.list()
    matches = [l for l in l2s if l.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple L2 networks match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: L2 network '{identifier}' not found.", err=True)
    raise typer.Exit(6)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------


def _net_block_to_dict(block: Any) -> dict[str, Any]:
    """Convert a Network Block object to a dict for output."""
    return {
        "$key": block.key,
        "cidr": block.get("cidr", ""),
        "network_name": block.get("network_name", ""),
        "description": block.get("description", ""),
    }


def _ext_ip_to_dict(ip: Any) -> dict[str, Any]:
    """Convert an External IP object to a dict for output."""
    return {
        "$key": ip.key,
        "ip_address": ip.get("ip_address", ""),
        "network_name": ip.get("network_name", ""),
        "hostname": ip.get("hostname", ""),
    }


def _l2_to_dict(l2: Any) -> dict[str, Any]:
    """Convert an L2 Network object to a dict for output."""
    return {
        "$key": l2.key,
        "network_name": l2.get("network_name", ""),
        "network_type": l2.get("network_type", ""),
        "is_enabled": l2.get("enabled"),
    }


# ===== Network Block Commands =====


@net_block_app.command("list")
@handle_errors()
def net_block_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List network blocks allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    blocks = tenant_obj.network_blocks.list()
    data = [_net_block_to_dict(b) for b in blocks]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_NET_BLOCK_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@net_block_app.command("create")
@handle_errors()
def net_block_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    cidr: Annotated[str, typer.Option("--cidr", help="CIDR block (e.g., 10.0.0.0/24)")],
    network: Annotated[int, typer.Option("--network", help="Network key")],
) -> None:
    """Allocate a network block to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    block_obj = tenant_obj.network_blocks.create(
        cidr=cidr,
        network=network,
    )

    output_success(
        f"Created network block (key: {block_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _net_block_to_dict(block_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@net_block_app.command("delete")
@handle_errors()
def net_block_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    block: Annotated[str, typer.Argument(help="Network block name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove a network block from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    block_key = _resolve_net_block(tenant_obj, block)

    if not confirm_action(f"Delete network block '{block}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.network_blocks.delete(block_key)
    output_success(f"Deleted network block '{block}'", quiet=vctx.quiet)


# ===== External IP Commands =====


@ext_ip_app.command("list")
@handle_errors()
def ext_ip_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List external IPs allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    ips = tenant_obj.external_ips.list()
    data = [_ext_ip_to_dict(i) for i in ips]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_EXT_IP_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@ext_ip_app.command("create")
@handle_errors()
def ext_ip_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    ip: Annotated[str, typer.Option("--ip", help="IP address")],
    network: Annotated[int, typer.Option("--network", help="Network key")],
    hostname: Annotated[
        str | None, typer.Option("--hostname", help="Hostname for the IP")
    ] = None,
) -> None:
    """Allocate an external IP to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    ip_obj = tenant_obj.external_ips.create(
        ip=ip,
        network=network,
        hostname=hostname,
    )

    output_success(
        f"Created external IP (key: {ip_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _ext_ip_to_dict(ip_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@ext_ip_app.command("delete")
@handle_errors()
def ext_ip_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    ip: Annotated[str, typer.Argument(help="External IP name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove an external IP from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    ip_key = _resolve_ext_ip(tenant_obj, ip)

    if not confirm_action(f"Delete external IP '{ip}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.external_ips.delete(ip_key)
    output_success(f"Deleted external IP '{ip}'", quiet=vctx.quiet)


# ===== L2 Network Commands =====


@l2_app.command("list")
@handle_errors()
def l2_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List L2 networks allocated to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    l2s = tenant_obj.l2_networks.list()
    data = [_l2_to_dict(l) for l in l2s]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_L2_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@l2_app.command("create")
@handle_errors()
def l2_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    network_name: Annotated[
        str, typer.Option("--network-name", help="Network name for the L2 connection")
    ],
) -> None:
    """Allocate an L2 network to a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    l2_obj = tenant_obj.l2_networks.create(
        network_name=network_name,
    )

    output_success(
        f"Created L2 network (key: {l2_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _l2_to_dict(l2_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@l2_app.command("delete")
@handle_errors()
def l2_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    l2: Annotated[str, typer.Argument(help="L2 network name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Remove an L2 network from a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    l2_key = _resolve_l2(tenant_obj, l2)

    if not confirm_action(f"Delete L2 network '{l2}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.l2_networks.delete(l2_key)
    output_success(f"Deleted L2 network '{l2}'", quiet=vctx.quiet)
```

### 5C: Register in tenant.py

Add to `src/verge_cli/commands/tenant.py`:

```python
from verge_cli.commands import tenant_net

app.add_typer(tenant_net.net_block_app, name="net-block")
app.add_typer(tenant_net.ext_ip_app, name="ext-ip")
app.add_typer(tenant_net.l2_app, name="l2")
```

### Run tests

```bash
uv run pytest tests/unit/test_tenant_net.py -v
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_net.py tests/unit/test_tenant_net.py
uv run mypy src/verge_cli/commands/tenant_net.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_net.py tests/unit/test_tenant_net.py src/verge_cli/commands/tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant networking commands (net-block, ext-ip, l2)

Implement three tenant networking sub-resources in a single module:
network blocks, external IPs, and L2 networks. Each has list, create,
and delete commands with full test coverage.
EOF
)"
```

---

## Task 6: tenant_snapshot.py — list, get, create, delete, restore (TDD)

### 6A: Write failing tests

Create `tests/unit/test_tenant_snapshot.py`:

```python
"""Tests for tenant snapshot sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Acme Corp Tenant",
            "status": "online",
            "state": "running",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


@pytest.fixture
def mock_snapshot() -> MagicMock:
    """Create a mock Tenant Snapshot object."""
    snap = MagicMock()
    snap.key = 600
    snap.name = "daily-backup"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 600,
            "name": "daily-backup",
            "created": 1707300000,
            "expires": 0,
            "profile": "default",
        }
        return data.get(key, default)

    snap.get = mock_get
    return snap


def test_snapshot_list(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot list should list snapshots."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(app, ["tenant", "snapshot", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "daily-backup" in result.output
    mock_tenant.snapshots.list.assert_called_once()


def test_snapshot_get(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot get should show snapshot details."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]
    mock_tenant.snapshots.get.return_value = mock_snapshot

    result = cli_runner.invoke(
        app, ["tenant", "snapshot", "get", "acme-corp", "daily-backup"]
    )

    assert result.exit_code == 0
    assert "daily-backup" in result.output


def test_snapshot_get_by_key(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot get should accept numeric key."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.get.return_value = mock_snapshot

    result = cli_runner.invoke(
        app, ["tenant", "snapshot", "get", "acme-corp", "600"]
    )

    assert result.exit_code == 0


def test_snapshot_create(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot create should create a snapshot."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.create.return_value = mock_snapshot

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "snapshot",
            "create",
            "acme-corp",
            "--name",
            "daily-backup",
        ],
    )

    assert result.exit_code == 0
    mock_tenant.snapshots.create.assert_called_once()


def test_snapshot_create_with_retention(
    cli_runner, mock_client, mock_tenant, mock_snapshot
):
    """vrg tenant snapshot create should accept --retention."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.create.return_value = mock_snapshot

    result = cli_runner.invoke(
        app,
        [
            "tenant",
            "snapshot",
            "create",
            "acme-corp",
            "--name",
            "daily-backup",
            "--retention",
            "86400",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.snapshots.create.call_args[1]
    assert call_kwargs["retention"] == 86400


def test_snapshot_delete(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot delete should remove a snapshot with --yes."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(
        app, ["tenant", "snapshot", "delete", "acme-corp", "daily-backup", "--yes"]
    )

    assert result.exit_code == 0
    mock_tenant.snapshots.delete.assert_called_once_with(600)


def test_snapshot_restore(cli_runner, mock_client, mock_tenant, mock_snapshot):
    """vrg tenant snapshot restore should restore a snapshot."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = [mock_snapshot]

    result = cli_runner.invoke(
        app, ["tenant", "snapshot", "restore", "acme-corp", "daily-backup"]
    )

    assert result.exit_code == 0
    mock_tenant.snapshots.restore.assert_called_once_with(600)


def test_snapshot_list_empty(cli_runner, mock_client, mock_tenant):
    """vrg tenant snapshot list should handle empty list."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.snapshots.list.return_value = []

    result = cli_runner.invoke(app, ["tenant", "snapshot", "list", "acme-corp"])

    assert result.exit_code == 0
```

### Run tests (should fail)

```bash
uv run pytest tests/unit/test_tenant_snapshot.py -v 2>&1 | head -20
```

### 6B: Create tenant_snapshot.py

Create `src/verge_cli/commands/tenant_snapshot.py`:

```python
"""Tenant snapshot sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_SNAPSHOT_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="snapshot",
    help="Manage tenant snapshots.",
    no_args_is_help=True,
)


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


def _snapshot_to_dict(snap: Any) -> dict[str, Any]:
    """Convert a Tenant Snapshot object to a dict for output."""
    return {
        "$key": snap.key,
        "name": snap.name,
        "created": snap.get("created"),
        "expires": snap.get("expires"),
        "profile": snap.get("profile", ""),
    }


def _resolve_snapshot(tenant_obj: Any, identifier: str) -> int:
    """Resolve a snapshot name or ID to a key."""
    if identifier.isdigit():
        return int(identifier)
    snapshots = tenant_obj.snapshots.list()
    matches = [s for s in snapshots if s.name == identifier]
    if len(matches) == 1:
        return int(matches[0].key)
    if len(matches) > 1:
        typer.echo(
            f"Error: Multiple snapshots match '{identifier}'. Use a numeric key.",
            err=True,
        )
        raise typer.Exit(7)
    typer.echo(f"Error: Snapshot '{identifier}' not found.", err=True)
    raise typer.Exit(6)


@app.command("list")
@handle_errors()
def snapshot_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """List snapshots for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snapshots = tenant_obj.snapshots.list()
    data = [_snapshot_to_dict(s) for s in snapshots]
    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_SNAPSHOT_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def snapshot_get(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
) -> None:
    """Get details of a tenant snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)
    snap_obj = tenant_obj.snapshots.get(snap_key)
    output_result(
        _snapshot_to_dict(snap_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def snapshot_create(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="Snapshot name")] = None,
    retention: Annotated[
        int | None, typer.Option("--retention", help="Retention period in seconds")
    ] = None,
) -> None:
    """Create a snapshot of a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)

    snap_obj = tenant_obj.snapshots.create(
        name=name,
        retention=retention,
    )

    output_success(
        f"Created snapshot '{snap_obj.name}' (key: {snap_obj.key})",
        quiet=vctx.quiet,
    )
    output_result(
        _snapshot_to_dict(snap_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def snapshot_delete(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a tenant snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)

    if not confirm_action(f"Delete snapshot '{snapshot}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    tenant_obj.snapshots.delete(snap_key)
    output_success(f"Deleted snapshot '{snapshot}'", quiet=vctx.quiet)


@app.command("restore")
@handle_errors()
def snapshot_restore(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    snapshot: Annotated[str, typer.Argument(help="Snapshot name or key")],
) -> None:
    """Restore a tenant from a snapshot."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    snap_key = _resolve_snapshot(tenant_obj, snapshot)

    tenant_obj.snapshots.restore(snap_key)
    output_success(f"Restored tenant from snapshot '{snapshot}'", quiet=vctx.quiet)
```

### 6C: Register in tenant.py

Add to `src/verge_cli/commands/tenant.py`:

```python
from verge_cli.commands import tenant_snapshot

app.add_typer(tenant_snapshot.app, name="snapshot")
```

### Run tests

```bash
uv run pytest tests/unit/test_tenant_snapshot.py -v
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_snapshot.py tests/unit/test_tenant_snapshot.py
uv run mypy src/verge_cli/commands/tenant_snapshot.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_snapshot.py tests/unit/test_tenant_snapshot.py src/verge_cli/commands/tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant snapshot commands (list, get, create, delete, restore)

Implement tenant snapshot sub-resource with epoch timestamp formatting
for created/expires fields. Includes restore command for snapshot
recovery with full test coverage.
EOF
)"
```

---

## Task 7: tenant_stats.py — stats + logs (TDD)

### 7A: Write failing tests

Create `tests/unit/test_tenant_stats.py`:

```python
"""Tests for tenant stats and logs sub-resource commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_tenant() -> MagicMock:
    """Create a mock Tenant object."""
    tenant = MagicMock()
    tenant.key = 5
    tenant.name = "acme-corp"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "description": "Acme Corp Tenant",
            "status": "online",
            "state": "running",
        }
        return data.get(key, default)

    tenant.get = mock_get
    return tenant


@pytest.fixture
def mock_stats_current() -> dict[str, Any]:
    """Create mock current stats data."""
    return {
        "ram_used_mb": 4096,
        "ram_total_mb": 8192,
        "total_cpu_percent": 45.2,
        "tier1_used_gb": 100,
        "tier1_provisioned_gb": 500,
        "tier3_used_gb": 200,
        "tier3_provisioned_gb": 1000,
    }


@pytest.fixture
def mock_stats_history() -> list[dict[str, Any]]:
    """Create mock stats history data."""
    return [
        {
            "timestamp": 1707300000,
            "cpu_percent": 45.2,
            "ram_used_mb": 4096,
            "ram_total_mb": 8192,
            "disk_read_ops": 1200,
            "disk_write_ops": 800,
        },
        {
            "timestamp": 1707296400,
            "cpu_percent": 32.1,
            "ram_used_mb": 3800,
            "ram_total_mb": 8192,
            "disk_read_ops": 900,
            "disk_write_ops": 600,
        },
    ]


@pytest.fixture
def mock_log_entry() -> MagicMock:
    """Create a mock log entry."""
    entry = MagicMock()

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "timestamp": "2024-02-07 12:00:00",
            "type": "info",
            "message": "Tenant started successfully",
        }
        return data.get(key, default)

    entry.get = mock_get
    return entry


# ===== Stats Tests =====


def test_stats_current(cli_runner, mock_client, mock_tenant, mock_stats_current):
    """vrg tenant stats current should show current stats."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.get.return_value = mock_stats_current

    result = cli_runner.invoke(app, ["tenant", "stats", "current", "acme-corp"])

    assert result.exit_code == 0
    assert "ram_used_mb" in result.output or "4096" in result.output
    mock_tenant.stats.get.assert_called_once()


def test_stats_history(cli_runner, mock_client, mock_tenant, mock_stats_history):
    """vrg tenant stats history should show stats history."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.history_short.return_value = mock_stats_history

    result = cli_runner.invoke(app, ["tenant", "stats", "history", "acme-corp"])

    assert result.exit_code == 0
    mock_tenant.stats.history_short.assert_called_once()


def test_stats_history_with_limit(cli_runner, mock_client, mock_tenant, mock_stats_history):
    """vrg tenant stats history should accept --limit."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.stats.history_short.return_value = mock_stats_history

    result = cli_runner.invoke(
        app, ["tenant", "stats", "history", "acme-corp", "--limit", "10"]
    )

    assert result.exit_code == 0
    mock_tenant.stats.history_short.assert_called_once_with(limit=10)


# ===== Logs Tests =====


def test_logs_list(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should list log entries."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(app, ["tenant", "logs", "list", "acme-corp"])

    assert result.exit_code == 0
    assert "Tenant started" in result.output
    mock_tenant.logs.list.assert_called_once()


def test_logs_list_with_limit(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should accept --limit."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(
        app, ["tenant", "logs", "list", "acme-corp", "--limit", "10"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.logs.list.call_args[1]
    assert call_kwargs["limit"] == 10


def test_logs_list_errors_only(cli_runner, mock_client, mock_tenant, mock_log_entry):
    """vrg tenant logs list should accept --errors-only."""
    mock_client.tenants.list.return_value = [mock_tenant]
    mock_client.tenants.get.return_value = mock_tenant
    mock_tenant.logs.list.return_value = [mock_log_entry]

    result = cli_runner.invoke(
        app, ["tenant", "logs", "list", "acme-corp", "--errors-only"]
    )

    assert result.exit_code == 0
    call_kwargs = mock_tenant.logs.list.call_args[1]
    assert call_kwargs["errors_only"] is True
```

### Run tests (should fail)

```bash
uv run pytest tests/unit/test_tenant_stats.py -v 2>&1 | head -20
```

### 7B: Create tenant_stats.py

Create `src/verge_cli/commands/tenant_stats.py`:

```python
"""Tenant stats and logs sub-resource commands."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.columns import TENANT_LOG_COLUMNS, TENANT_STATS_COLUMNS
from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result
from verge_cli.utils import resolve_resource_id

# ---------------------------------------------------------------------------
# Two Typer apps: stats + logs
# ---------------------------------------------------------------------------

stats_app = typer.Typer(
    name="stats",
    help="View tenant resource statistics.",
    no_args_is_help=True,
)

logs_app = typer.Typer(
    name="logs",
    help="View tenant activity logs.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _get_tenant(ctx: typer.Context, tenant_identifier: str) -> tuple[Any, Any]:
    """Get the VergeContext and Tenant object."""
    vctx = get_context(ctx)
    key = resolve_resource_id(vctx.client.tenants, tenant_identifier, "Tenant")
    tenant_obj = vctx.client.tenants.get(key)
    return vctx, tenant_obj


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------


def _log_to_dict(entry: Any) -> dict[str, Any]:
    """Convert a log entry to a dict for output."""
    return {
        "timestamp": entry.get("timestamp", ""),
        "type": entry.get("type", ""),
        "message": entry.get("message", ""),
    }


# ===== Stats Commands =====


@stats_app.command("current")
@handle_errors()
def stats_current(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
) -> None:
    """Show current resource usage for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    stats = tenant_obj.stats.get()

    # Stats returns a dict — output as key-value table
    output_result(
        stats,
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@stats_app.command("history")
@handle_errors()
def stats_history(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of entries")] = 20,
) -> None:
    """Show historical resource usage for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    history = tenant_obj.stats.history_short(limit=limit)

    output_result(
        history,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_STATS_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


# ===== Logs Commands =====


@logs_app.command("list")
@handle_errors()
def logs_list(
    ctx: typer.Context,
    tenant: Annotated[str, typer.Argument(help="Tenant name or key")],
    limit: Annotated[int, typer.Option("--limit", "-l", help="Number of entries")] = 50,
    errors_only: Annotated[
        bool, typer.Option("--errors-only", help="Show only error entries")
    ] = False,
) -> None:
    """List activity log entries for a tenant."""
    vctx, tenant_obj = _get_tenant(ctx, tenant)
    entries = tenant_obj.logs.list(limit=limit, errors_only=errors_only)
    data = [_log_to_dict(e) for e in entries]

    output_result(
        data,
        output_format=vctx.output_format,
        query=vctx.query,
        columns=TENANT_LOG_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

### 7C: Register in tenant.py

Add to `src/verge_cli/commands/tenant.py`:

```python
from verge_cli.commands import tenant_stats

app.add_typer(tenant_stats.stats_app, name="stats")
app.add_typer(tenant_stats.logs_app, name="logs")
```

### Run tests

```bash
uv run pytest tests/unit/test_tenant_stats.py -v
```

### Verify

```bash
uv run ruff check src/verge_cli/commands/tenant_stats.py tests/unit/test_tenant_stats.py
uv run mypy src/verge_cli/commands/tenant_stats.py
```

### Commit

```bash
git add src/verge_cli/commands/tenant_stats.py tests/unit/test_tenant_stats.py src/verge_cli/commands/tenant.py
git commit -m "$(cat <<'EOF'
✨ feat: add tenant stats and logs commands

Implement tenant monitoring with stats current/history and logs list
commands. Stats current outputs a key-value table, stats history outputs
time series, and logs list supports --limit and --errors-only.
EOF
)"
```

---

## Task 8: Final registration, regression, and verification

### 8A: Verify all imports in tenant.py

Open `src/verge_cli/commands/tenant.py` and confirm it contains ALL of these registrations (Tasks 2-7 should have added them incrementally, but verify the full set):

```python
from verge_cli.commands import (
    tenant_node,
    tenant_storage,
    tenant_net,
    tenant_snapshot,
    tenant_stats,
)

# After app = typer.Typer(...)
app.add_typer(tenant_node.app, name="node")
app.add_typer(tenant_storage.app, name="storage")
app.add_typer(tenant_net.net_block_app, name="net-block")
app.add_typer(tenant_net.ext_ip_app, name="ext-ip")
app.add_typer(tenant_net.l2_app, name="l2")
app.add_typer(tenant_snapshot.app, name="snapshot")
app.add_typer(tenant_stats.stats_app, name="stats")
app.add_typer(tenant_stats.logs_app, name="logs")
```

### 8B: Run full regression

```bash
uv run pytest tests/unit/ -v
```

### 8C: Run linting and type checking

```bash
uv run ruff check src/verge_cli/
uv run ruff format --check .
uv run mypy src/verge_cli/
```

### 8D: Fix any issues found

If ruff or mypy reports issues, fix them before committing.

### 8E: Final commit

```bash
git add -A
git commit -m "$(cat <<'EOF'
✅ test: verify tenant sub-resource registration and full regression

Ensure all 8 tenant sub-resource typer apps are properly registered
in tenant.py. Full regression passes with ruff, mypy, and pytest.
EOF
)"
```

---

## Summary

### New Files Created

| File | Purpose |
|------|---------|
| `src/verge_cli/commands/tenant_node.py` | Tenant compute node CRUD |
| `src/verge_cli/commands/tenant_storage.py` | Tenant storage allocation CRUD |
| `src/verge_cli/commands/tenant_net.py` | Tenant net-block, ext-ip, l2 (3 apps) |
| `src/verge_cli/commands/tenant_snapshot.py` | Tenant snapshot CRUD + restore |
| `src/verge_cli/commands/tenant_stats.py` | Tenant stats + logs (2 apps) |
| `tests/unit/test_tenant_node.py` | Tenant node tests |
| `tests/unit/test_tenant_storage.py` | Tenant storage tests |
| `tests/unit/test_tenant_net.py` | Tenant networking tests |
| `tests/unit/test_tenant_snapshot.py` | Tenant snapshot tests |
| `tests/unit/test_tenant_stats.py` | Tenant stats/logs tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/verge_cli/columns.py` | +8 column definitions, +3 helper functions |
| `src/verge_cli/commands/tenant.py` | +8 `add_typer()` registrations |

### CLI Commands Added

| Command Group | Commands |
|---------------|----------|
| `vrg tenant node` | list, get, create, update, delete |
| `vrg tenant storage` | list, get, create, update, delete |
| `vrg tenant net-block` | list, create, delete |
| `vrg tenant ext-ip` | list, create, delete |
| `vrg tenant l2` | list, create, delete |
| `vrg tenant snapshot` | list, get, create, delete, restore |
| `vrg tenant stats` | current, history |
| `vrg tenant logs` | list |

**Total: 25 new commands across 8 sub-resource groups**

### Test Count

| Test File | Tests |
|-----------|-------|
| `test_tenant_node.py` | 10 |
| `test_tenant_storage.py` | 9 |
| `test_tenant_net.py` | 11 |
| `test_tenant_snapshot.py` | 9 |
| `test_tenant_stats.py` | 6 |
| **Total** | **45** |

### Estimated Time

| Task | Estimate |
|------|----------|
| Task 1: Column definitions | 5 min |
| Task 2: tenant_node list+get | 5 min |
| Task 3: tenant_node create+update+delete | 5 min |
| Task 4: tenant_storage full CRUD | 5 min |
| Task 5: tenant_net (3 apps) | 10 min |
| Task 6: tenant_snapshot | 5 min |
| Task 7: tenant_stats + logs | 5 min |
| Task 8: Registration + regression | 3 min |
| **Total** | **~43 min** |

---

## Task Checklist

- [x] Task 1: Column definitions for all tenant sub-resources
- [ ] Task 2: tenant_node.py — list + get (TDD)
- [ ] Task 3: tenant_node.py — create, update, delete (TDD)
- [ ] Task 4: tenant_storage.py — full CRUD (TDD)
- [ ] Task 5: tenant_net.py — three sub-Typer apps (TDD)
- [ ] Task 6: tenant_snapshot.py — list, get, create, delete, restore (TDD)
- [ ] Task 7: tenant_stats.py — stats + logs (TDD)
- [ ] Task 8: Final registration, regression, and verification
