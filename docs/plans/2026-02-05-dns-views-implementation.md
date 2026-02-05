# DNS Views and Shakedown Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement DNS view support following the pyvergeos v1.0.1 hierarchical model and fix shakedown test issues.

**Architecture:** The CLI will mirror the SDK's hierarchy: Network → View → Zone → Record. All zone/record commands will require a view argument. Helper functions are organized by resource type for maintainability.

**Tech Stack:** Python 3.10+, Typer CLI, pyvergeos SDK v1.0.1, pytest

---

## Task 1: Update pyvergeos Dependency

**Files:**
- Modify: `pyproject.toml:27`

**Step 1: Update dependency version**

Edit `pyproject.toml` line 27 to require pyvergeos 1.0.1:

```python
# Change from:
"pyvergeos>=1.0.0",
# To:
"pyvergeos>=1.0.1",
```

**Step 2: Sync dependencies**

Run: `uv sync --extra dev`
Expected: Dependencies resolve successfully

**Step 3: Verify SDK has dns_views**

Run: `uv run python -c "from pyvergeos.resources.dns_views import DNSViewManager; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "build: require pyvergeos>=1.0.1 for DNS view support"
```

---

## Task 2: Add DNS View Fixtures to conftest.py

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Add mock_dns_view fixture**

Add after line 108 (after `mock_network` fixture):

```python
@pytest.fixture
def mock_dns_view() -> MagicMock:
    """Create a mock DNS View object."""
    view = MagicMock()
    view.key = 10
    view.name = "internal"

    def mock_get(key: str, default: Any = None) -> Any:
        data = {
            "$key": 10,
            "name": "internal",
            "recursion": True,
            "match_clients": "10.0.0.0/8;192.168.0.0/16;",
            "match_destinations": None,
            "max_cache_size": 33554432,
            "vnet": 1,
        }
        return data.get(key, default)

    view.get = mock_get
    return view
```

**Step 2: Run existing tests to verify no regressions**

Run: `uv run pytest tests/unit/ -v --tb=short`
Expected: All 130 tests pass

**Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add mock_dns_view fixture for DNS view tests"
```

---

## Task 3: Add DNS View Helper Functions

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view helper functions after imports (around line 13)**

Add after the existing imports:

```python
# =============================================================================
# View Helper Functions
# =============================================================================


def _transform_comma_to_semicolon(value: str | None) -> str | None:
    """Transform comma-separated values to semicolon-delimited format for SDK.

    Args:
        value: Comma-separated string (e.g., "10.0.0.0/8,192.168.0.0/16")

    Returns:
        Semicolon-delimited string with trailing semicolon (e.g., "10.0.0.0/8;192.168.0.0/16;")
        or None if input is None.
    """
    if value is None:
        return None
    # Split by comma, strip whitespace, rejoin with semicolons
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if not parts:
        return None
    return ";".join(parts) + ";"


def _resolve_view_id(network: Any, identifier: str) -> int:
    """Resolve a view name or ID to a key.

    Args:
        network: Network object with dns_views collection.
        identifier: View name or numeric key.

    Returns:
        The view key.

    Raises:
        ResourceNotFoundError: If view not found.
    """
    # If numeric, treat as key directly
    if identifier.isdigit():
        return int(identifier)

    # Try to find by name
    views = network.dns_views.list()
    for view in views:
        name = view.get("name") or getattr(view, "name", "")
        key = view.get("$key") or getattr(view, "key", None)
        if name == identifier and key is not None:
            return int(key)

    raise ResourceNotFoundError(f"DNS view '{identifier}' not found")


def _view_to_dict(view: Any) -> dict[str, Any]:
    """Convert a DNS View object to a dictionary for output.

    Args:
        view: View object from SDK.

    Returns:
        Dictionary representation of the view.
    """
    match_clients = view.get("match_clients", "")
    # Transform semicolon-delimited back to comma-separated for display
    if match_clients:
        match_clients = match_clients.replace(";", ", ").rstrip(", ")

    return {
        "id": view.get("$key") or getattr(view, "key", None),
        "name": view.get("name", ""),
        "recursion": view.get("recursion", False),
        "match_clients": match_clients,
        "max_cache_size": view.get("max_cache_size", 0),
    }
```

**Step 2: Run linting**

Run: `uv run ruff check src/verge_cli/commands/network_dns.py`
Expected: No errors

**Step 3: Commit**

```bash
git add src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): add view helper functions"
```

---

## Task 4: Add View Typer Subapp and List Columns

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view_app after record_app (around line 33)**

```python
# View subapp
view_app = typer.Typer(
    name="view",
    help="Manage DNS views.",
    no_args_is_help=True,
)
```

**Step 2: Register view_app (add after line 37)**

```python
app.add_typer(view_app, name="view")
```

**Step 3: Add VIEW_LIST_COLUMNS constant (after ZONE_LIST_COLUMNS)**

```python
# Default columns for view list output
VIEW_LIST_COLUMNS = ["id", "name", "recursion", "match_clients"]
```

**Step 4: Update ZONE_LIST_COLUMNS to include id and view_name**

```python
# Default columns for zone list output
ZONE_LIST_COLUMNS = ["id", "domain", "type", "view_name", "serial"]
```

**Step 5: Update RECORD_LIST_COLUMNS to include id**

```python
# Default columns for record list output
RECORD_LIST_COLUMNS = ["id", "host", "type", "value", "ttl", "priority"]
```

**Step 6: Run tests**

Run: `uv run pytest tests/unit/test_network_dns.py -v --tb=short`
Expected: Tests pass (they don't check columns yet)

**Step 7: Commit**

```bash
git add src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): add view subapp and update list columns"
```

---

## Task 5: Write Failing Tests for View List Command

**Files:**
- Modify: `tests/unit/test_network_dns.py`

**Step 1: Add view fixture after mock_record fixture**

```python
@pytest.fixture
def mock_view():
    """Create a mock DNS View object."""
    view = MagicMock()
    view.key = 10
    view.name = "internal"

    def mock_get(key: str, default=None):
        data = {
            "$key": 10,
            "name": "internal",
            "recursion": True,
            "match_clients": "10.0.0.0/8;192.168.0.0/16;",
            "max_cache_size": 33554432,
        }
        return data.get(key, default)

    view.get = mock_get
    return view
```

**Step 2: Add view list tests at end of file**

```python
# =============================================================================
# View List Tests
# =============================================================================


def test_view_list(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View list should show DNS views for a network."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]

    result = cli_runner.invoke(app, ["network", "dns", "view", "list", "test-network"])

    assert result.exit_code == 0
    assert "internal" in result.output


def test_view_list_empty(cli_runner, mock_client, mock_network_for_dns):
    """View list should handle empty view list."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = []

    result = cli_runner.invoke(app, ["network", "dns", "view", "list", "test-network"])

    assert result.exit_code == 0
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_list -v`
Expected: FAIL (command doesn't exist yet)

**Step 4: Commit**

```bash
git add tests/unit/test_network_dns.py
git commit -m "test(dns): add failing tests for view list command"
```

---

## Task 6: Implement View List Command

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view_list command after the view helper functions section**

```python
# =============================================================================
# View Commands
# =============================================================================


@view_app.command("list")
@handle_errors()
def view_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List DNS views for a network.

    DNS views enable split-horizon DNS where different clients see
    different responses for the same domain.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    views = net_obj.dns_views.list()
    data = [_view_to_dict(view) for view in views]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=VIEW_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_list tests/unit/test_network_dns.py::test_view_list_empty -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): implement view list command"
```

---

## Task 7: Write Failing Tests for View Get Command

**Files:**
- Modify: `tests/unit/test_network_dns.py`

**Step 1: Add view get tests**

```python
# =============================================================================
# View Get Tests
# =============================================================================


def test_view_get(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View get should show view details."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]
    mock_network_for_dns.dns_views.get.return_value = mock_view

    result = cli_runner.invoke(
        app, ["network", "dns", "view", "get", "test-network", "internal"]
    )

    assert result.exit_code == 0
    assert "internal" in result.output


def test_view_get_by_id(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View get should work with numeric ID."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.get.return_value = mock_view

    result = cli_runner.invoke(app, ["network", "dns", "view", "get", "test-network", "10"])

    assert result.exit_code == 0
    mock_network_for_dns.dns_views.get.assert_called_once_with(10)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_get -v`
Expected: FAIL

**Step 3: Commit**

```bash
git add tests/unit/test_network_dns.py
git commit -m "test(dns): add failing tests for view get command"
```

---

## Task 8: Implement View Get Command

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view_get command after view_list**

```python
@view_app.command("get")
@handle_errors()
def view_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    view: Annotated[str, typer.Argument(help="View name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Get details of a DNS view."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    view_key = _resolve_view_id(net_obj, view)
    view_obj = net_obj.dns_views.get(view_key)

    output_result(
        _view_to_dict(view_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_get tests/unit/test_network_dns.py::test_view_get_by_id -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): implement view get command"
```

---

## Task 9: Write Failing Tests for View Create Command

**Files:**
- Modify: `tests/unit/test_network_dns.py`

**Step 1: Add view create tests**

```python
# =============================================================================
# View Create Tests
# =============================================================================


def test_view_create(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View create should create a new DNS view."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.create.return_value = mock_view

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "view",
            "create",
            "test-network",
            "--name",
            "internal",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_views.create.assert_called_once()
    call_kwargs = mock_network_for_dns.dns_views.create.call_args[1]
    assert call_kwargs["name"] == "internal"


def test_view_create_with_options(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View create should support all options."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.create.return_value = mock_view

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "view",
            "create",
            "test-network",
            "--name",
            "internal",
            "--recursion",
            "--match-clients",
            "10.0.0.0/8,192.168.0.0/16",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_network_for_dns.dns_views.create.call_args[1]
    assert call_kwargs["recursion"] is True
    # Should be transformed to semicolon-delimited
    assert call_kwargs["match_clients"] == "10.0.0.0/8;192.168.0.0/16;"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_create -v`
Expected: FAIL

**Step 3: Commit**

```bash
git add tests/unit/test_network_dns.py
git commit -m "test(dns): add failing tests for view create command"
```

---

## Task 10: Implement View Create Command

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view_create command after view_get**

```python
@view_app.command("create")
@handle_errors()
def view_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    name: Annotated[str, typer.Option("--name", "-n", help="View name")],
    recursion: Annotated[
        bool, typer.Option("--recursion/--no-recursion", help="Enable recursive DNS queries")
    ] = False,
    match_clients: Annotated[
        str | None,
        typer.Option("--match-clients", help="Client networks to match (comma-separated CIDRs)"),
    ] = None,
    match_destinations: Annotated[
        str | None,
        typer.Option(
            "--match-destinations", help="Destination networks to match (comma-separated CIDRs)"
        ),
    ] = None,
    max_cache_size: Annotated[
        int, typer.Option("--max-cache-size", help="Max RAM for DNS cache in bytes")
    ] = 33554432,
) -> None:
    """Create a new DNS view.

    DNS views enable split-horizon DNS where different clients see
    different responses for the same domain. Changes require apply-dns.

    Examples:
        vrg network dns view create mynet --name internal --recursion
        vrg network dns view create mynet --name external --match-clients "0.0.0.0/0"
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    create_kwargs: dict[str, Any] = {
        "name": name,
        "recursion": recursion,
        "max_cache_size": max_cache_size,
    }

    # Transform comma-separated to semicolon-delimited
    if match_clients:
        create_kwargs["match_clients"] = _transform_comma_to_semicolon(match_clients)
    if match_destinations:
        create_kwargs["match_destinations"] = _transform_comma_to_semicolon(match_destinations)

    view_obj = net_obj.dns_views.create(**create_kwargs)

    view_name = view_obj.get("name") or name
    view_key = view_obj.get("$key") or getattr(view_obj, "key", None)
    output_success(f"Created DNS view '{view_name}' (id: {view_key})", quiet=vctx.quiet)

    output_result(
        _view_to_dict(view_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_create tests/unit/test_network_dns.py::test_view_create_with_options -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): implement view create command"
```

---

## Task 11: Implement View Update Command (TDD)

**Files:**
- Modify: `tests/unit/test_network_dns.py`
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view update tests**

```python
# =============================================================================
# View Update Tests
# =============================================================================


def test_view_update(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View update should update view with new values."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]
    mock_network_for_dns.dns_views.get.return_value = mock_view
    mock_network_for_dns.dns_views.update.return_value = mock_view

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "view",
            "update",
            "test-network",
            "internal",
            "--recursion",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_views.update.assert_called_once()


def test_view_update_no_changes(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View update with no options should fail."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]

    result = cli_runner.invoke(
        app,
        ["network", "dns", "view", "update", "test-network", "internal"],
    )

    assert result.exit_code == 2
    assert "No updates specified" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_update -v`
Expected: FAIL

**Step 3: Implement view_update command**

```python
@view_app.command("update")
@handle_errors()
def view_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    view: Annotated[str, typer.Argument(help="View name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New view name")] = None,
    recursion: Annotated[
        bool | None, typer.Option("--recursion/--no-recursion", help="Enable recursive DNS")
    ] = None,
    match_clients: Annotated[
        str | None, typer.Option("--match-clients", help="Client networks (comma-separated)")
    ] = None,
    match_destinations: Annotated[
        str | None, typer.Option("--match-destinations", help="Destination networks")
    ] = None,
    max_cache_size: Annotated[
        int | None, typer.Option("--max-cache-size", help="Max cache size in bytes")
    ] = None,
) -> None:
    """Update a DNS view.

    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    view_key = _resolve_view_id(net_obj, view)

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if recursion is not None:
        updates["recursion"] = recursion
    if match_clients is not None:
        updates["match_clients"] = _transform_comma_to_semicolon(match_clients)
    if match_destinations is not None:
        updates["match_destinations"] = _transform_comma_to_semicolon(match_destinations)
    if max_cache_size is not None:
        updates["max_cache_size"] = max_cache_size

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    view_obj = net_obj.dns_views.update(view_key, **updates)

    view_name = view_obj.get("name") or view
    output_success(f"Updated DNS view '{view_name}'", quiet=vctx.quiet)

    output_result(
        _view_to_dict(view_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_update tests/unit/test_network_dns.py::test_view_update_no_changes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_network_dns.py src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): implement view update command"
```

---

## Task 12: Implement View Delete Command (TDD)

**Files:**
- Modify: `tests/unit/test_network_dns.py`
- Modify: `src/verge_cli/commands/network_dns.py`

**Step 1: Add view delete tests**

```python
# =============================================================================
# View Delete Tests
# =============================================================================


def test_view_delete(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View delete should delete a DNS view."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]
    mock_network_for_dns.dns_views.get.return_value = mock_view

    result = cli_runner.invoke(
        app,
        ["network", "dns", "view", "delete", "test-network", "internal", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_views.delete.assert_called_once_with(10)


def test_view_delete_cancelled(cli_runner, mock_client, mock_network_for_dns, mock_view):
    """View delete should be cancellable."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_views.list.return_value = [mock_view]
    mock_network_for_dns.dns_views.get.return_value = mock_view

    result = cli_runner.invoke(
        app,
        ["network", "dns", "view", "delete", "test-network", "internal"],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_network_for_dns.dns_views.delete.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_delete -v`
Expected: FAIL

**Step 3: Implement view_delete command**

```python
@view_app.command("delete")
@handle_errors()
def view_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    view: Annotated[str, typer.Argument(help="View name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a DNS view.

    This will delete the view and all its zones and records.
    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    view_key = _resolve_view_id(net_obj, view)
    view_obj = net_obj.dns_views.get(view_key)

    view_name = view_obj.get("name") or str(view_key)

    if not confirm_action(f"Delete DNS view '{view_name}' and all its zones?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    net_obj.dns_views.delete(view_key)
    output_success(f"Deleted DNS view '{view_name}'", quiet=vctx.quiet)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_network_dns.py::test_view_delete tests/unit/test_network_dns.py::test_view_delete_cancelled -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/test_network_dns.py src/verge_cli/commands/network_dns.py
git commit -m "feat(dns): implement view delete command"
```

---

## Task 13: Refactor Zone Commands to Require View

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`
- Modify: `tests/unit/test_network_dns.py`

This is a breaking change. We need to update all zone commands to accept `<network> <view>` instead of just `<network>`.

**Step 1: Update _resolve_zone_id to accept view instead of network**

```python
def _resolve_zone_id(view: Any, identifier: str) -> int:
    """Resolve a zone domain or ID to a key.

    Args:
        view: View object with zones collection.
        identifier: Zone domain or numeric key.

    Returns:
        The zone key.

    Raises:
        ResourceNotFoundError: If zone not found.
    """
    # If numeric, treat as key directly
    if identifier.isdigit():
        return int(identifier)

    # Try to find by domain name
    zones = view.zones.list()
    for zone in zones:
        domain = zone.get("domain") or getattr(zone, "domain", "")
        key = zone.get("$key") or getattr(zone, "key", None)
        if domain == identifier and key is not None:
            return int(key)

    raise ResourceNotFoundError(f"DNS zone '{identifier}' not found")
```

**Step 2: Update _zone_to_dict to include id and view_name**

```python
def _zone_to_dict(zone: Any) -> dict[str, Any]:
    """Convert a DNS Zone object to a dictionary for output."""
    return {
        "id": zone.get("$key") or getattr(zone, "key", None),
        "domain": zone.get("domain", ""),
        "type": zone.get("type", "master"),
        "view_name": zone.get("view_name") or getattr(zone, "view_name", None),
        "serial": zone.get("serial_number", 0),
        "nameserver": zone.get("nameserver", ""),
        "email": zone.get("email", ""),
        "default_ttl": zone.get("default_ttl", ""),
    }
```

**Step 3: Update zone_list command**

```python
@zone_app.command("list")
@handle_errors()
def zone_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    view: Annotated[str, typer.Argument(help="View name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List DNS zones in a view.

    Shows all BIND DNS zones configured in the specified view.
    Changes require apply-dns to take effect.
    """
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    view_key = _resolve_view_id(net_obj, view)
    view_obj = net_obj.dns_views.get(view_key)

    zones = view_obj.zones.list()
    data = [_zone_to_dict(zone) for zone in zones]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=ZONE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 4: Update all other zone commands similarly (zone_get, zone_create, zone_update, zone_delete)**

Each command needs:
1. Add `view: Annotated[str, typer.Argument(help="View name or key")]` parameter after `network`
2. Add view resolution: `view_key = _resolve_view_id(net_obj, view)` and `view_obj = net_obj.dns_views.get(view_key)`
3. Use `view_obj.zones` instead of `net_obj.dns_zones`

**Step 5: Update tests to use new command signature**

Update all zone tests to pass view argument:
- `["network", "dns", "zone", "list", "test-network"]` → `["network", "dns", "zone", "list", "test-network", "internal"]`
- Add `mock_network_for_dns.dns_views.list.return_value = [mock_view]` and `mock_network_for_dns.dns_views.get.return_value = mock_view`
- Change `mock_network_for_dns.dns_zones` → `mock_view.zones`

**Step 6: Run all DNS tests**

Run: `uv run pytest tests/unit/test_network_dns.py -v`
Expected: All tests pass

**Step 7: Commit**

```bash
git add src/verge_cli/commands/network_dns.py tests/unit/test_network_dns.py
git commit -m "refactor(dns): zone commands now require view argument

BREAKING CHANGE: Zone commands now require <network> <view> instead of just <network>.
This aligns with the SDK's hierarchical model where zones belong to views."
```

---

## Task 14: Refactor Record Commands to Require View

**Files:**
- Modify: `src/verge_cli/commands/network_dns.py`
- Modify: `tests/unit/test_network_dns.py`

Similar to Task 13, update all record commands to accept `<network> <view> <zone>` and use ID-based identification.

**Step 1: Update _record_to_dict to use 'id' instead of 'key'**

```python
def _record_to_dict(record: Any) -> dict[str, Any]:
    """Convert a DNS Record object to a dictionary for output."""
    return {
        "id": record.get("$key") or getattr(record, "key", None),
        "host": record.get("host", ""),
        "type": record.get("type", "A"),
        "value": record.get("value", ""),
        "ttl": record.get("ttl", ""),
        "priority": record.get("mx_preference", 0),
        "weight": record.get("weight", 0),
        "port": record.get("port", 0),
        "description": record.get("description", ""),
    }
```

**Step 2: Update record_list to require view**

```python
@record_app.command("list")
@handle_errors()
def record_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    view: Annotated[str, typer.Argument(help="View name or key")],
    zone: Annotated[str, typer.Argument(help="Zone domain or key")],
    record_type: Annotated[
        str | None, typer.Option("--type", "-t", help="Filter by record type")
    ] = None,
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List DNS records in a zone."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    view_key = _resolve_view_id(net_obj, view)
    view_obj = net_obj.dns_views.get(view_key)

    zone_key = _resolve_zone_id(view_obj, zone)
    zone_obj = view_obj.zones.get(zone_key)

    filter_kwargs: dict[str, Any] = {}
    if record_type:
        filter_kwargs["record_type"] = record_type

    records = zone_obj.records.list(**filter_kwargs)
    data = [_record_to_dict(record) for record in records]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=RECORD_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 3: Update record_get, record_create, record_update, record_delete similarly**

- Add view parameter
- Rename `--address` to `--value` in create/update
- Record get/update/delete should accept ID only (no name resolution)

**Step 4: Update tests**

Update all record tests to:
- Pass view argument
- Use `--value` instead of `--address`
- Use numeric ID for get/update/delete

**Step 5: Run all DNS tests**

Run: `uv run pytest tests/unit/test_network_dns.py -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/verge_cli/commands/network_dns.py tests/unit/test_network_dns.py
git commit -m "refactor(dns): record commands now require view argument

BREAKING CHANGE: Record commands now require <network> <view> <zone>.
- Renamed --address to --value for clarity with non-A record types
- Record get/update/delete now use numeric ID instead of hostname"
```

---

## Task 15: Add --vnet-default-gateway to Network Create

**Files:**
- Modify: `src/verge_cli/commands/network.py`
- Create: `tests/unit/test_network_create.py`

**Step 1: Write failing test**

Create `tests/unit/test_network_create.py`:

```python
"""Tests for network create command."""

from unittest.mock import MagicMock

from verge_cli.cli import app


def test_network_create_with_vnet_default_gateway(cli_runner, mock_client, mock_network):
    """Network create should support --vnet-default-gateway option."""
    mock_client.networks.list.return_value = [mock_network]
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        [
            "network",
            "create",
            "--name",
            "test-net",
            "--cidr",
            "10.0.0.0/24",
            "--vnet-default-gateway",
            "test-network",
        ],
    )

    assert result.exit_code == 0
    mock_client.networks.create.assert_called_once()
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["interface_network"] == 1  # Resolved from mock_network.key
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_create.py -v`
Expected: FAIL (option doesn't exist)

**Step 3: Add option to network_create command**

In `src/verge_cli/commands/network.py`, add to `network_create` function signature:

```python
vnet_default_gateway: Annotated[
    str | None,
    typer.Option(
        "--vnet-default-gateway",
        help="Route traffic through this network (name or key)",
    ),
] = None,
```

And in the function body, before `vctx.client.networks.create()`:

```python
if vnet_default_gateway:
    gw_key = resolve_resource_id(vctx.client.networks, vnet_default_gateway, "network")
    create_kwargs["interface_network"] = gw_key
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_create.py -v`
Expected: PASS

**Step 5: Run all network tests**

Run: `uv run pytest tests/unit/test_network*.py -v`
Expected: All pass

**Step 6: Commit**

```bash
git add src/verge_cli/commands/network.py tests/unit/test_network_create.py
git commit -m "feat(network): add --vnet-default-gateway option to create command"
```

---

## Task 16: Add --description to Rule Update

**Files:**
- Modify: `src/verge_cli/commands/network_rule.py`
- Modify: `tests/unit/test_network_rule.py`

**Step 1: Write failing test**

Add to `tests/unit/test_network_rule.py`:

```python
def test_rule_update_description(cli_runner, mock_client):
    """Rule update should support --description option."""
    mock_net = MagicMock()
    mock_net.key = 1
    mock_net.name = "test-network"
    mock_client.networks.list.return_value = [mock_net]
    mock_client.networks.get.return_value = mock_net

    mock_rule = MagicMock()
    mock_rule.key = 100
    mock_rule.name = "test-rule"
    mock_rule.get = lambda k, d=None: {"$key": 100, "name": "test-rule", "description": "New desc"}.get(k, d)

    mock_net.rules.list.return_value = [mock_rule]
    mock_net.rules.get.return_value = mock_rule
    mock_net.rules.update.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        [
            "network",
            "rule",
            "update",
            "test-network",
            "test-rule",
            "--description",
            "New description",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_net.rules.update.call_args[1]
    assert call_kwargs["description"] == "New description"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_rule.py::test_rule_update_description -v`
Expected: FAIL

**Step 3: Add --description option**

In `src/verge_cli/commands/network_rule.py`, add to `rule_update` function:

```python
description: Annotated[
    str | None, typer.Option("--description", help="Rule description")
] = None,
```

And in the updates dict building:

```python
if description is not None:
    updates["description"] = description
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_rule.py::test_rule_update_description -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/verge_cli/commands/network_rule.py tests/unit/test_network_rule.py
git commit -m "feat(rule): add --description option to update command"
```

---

## Task 17: Investigate and Fix VM Restart

**Files:**
- Modify: `src/verge_cli/commands/vm.py`

**Step 1: Check SDK source for available actions**

The SDK's `guest_reboot()` method uses action `guestreset`. The API rejected this. Check what actions are valid.

From the pyvergeos source (`vms.py:215-219`), the SDK uses:
- `poweron` - power on
- `poweroff` - graceful ACPI shutdown
- `kill` - force power off
- `reset` - hard reset
- `guestreset` - guest reboot (requires guest agent)
- `guestshutdown` - guest shutdown

**Step 2: Test graceful approach - use stop + start**

The safest fix is to implement restart as graceful stop then start:

```python
@app.command("restart")
@handle_errors()
def vm_restart(
    ctx: typer.Context,
    vm: Annotated[str, typer.Argument(help="VM name or key")],
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for VM to restart")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Wait timeout in seconds")] = 300,
) -> None:
    """Restart a virtual machine (graceful stop then start).

    This performs a graceful shutdown followed by power on. For a hard reset
    (like pressing the reset button), use 'vrg vm reset' instead.
    """
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.vms, vm, "VM")
    vm_obj = vctx.client.vms.get(key)

    if not vm_obj.is_running:
        typer.echo(f"VM '{vm_obj.name}' is not running. Use 'vrg vm start' instead.")
        raise typer.Exit(1)

    # Graceful stop
    vm_obj.power_off(force=False)
    output_success(f"Stopping VM '{vm_obj.name}'...", quiet=vctx.quiet)

    # Wait for stop
    vm_obj = wait_for_state(
        get_resource=vctx.client.vms.get,
        resource_key=key,
        target_state=["stopped", "offline"],
        timeout=timeout // 2,  # Use half timeout for stop
        state_field="status",
        resource_type="VM",
        quiet=True,
    )

    # Start
    vm_obj.power_on()
    output_success(f"Starting VM '{vm_obj.name}'...", quiet=vctx.quiet)

    if wait:
        vm_obj = wait_for_state(
            get_resource=vctx.client.vms.get,
            resource_key=key,
            target_state="running",
            timeout=timeout // 2,
            state_field="status",
            resource_type="VM",
            quiet=vctx.quiet,
        )
        output_success(f"VM '{vm_obj.name}' has restarted", quiet=vctx.quiet)
```

**Step 3: Run VM tests**

Run: `uv run pytest tests/unit/test_vm*.py -v`
Expected: All pass

**Step 4: Commit**

```bash
git add src/verge_cli/commands/vm.py
git commit -m "fix(vm): restart now uses graceful stop+start instead of guestreset

The guestreset action is not accepted by the API. Changed to use
graceful power_off followed by power_on for reliable restart behavior."
```

---

## Task 18: Run Full Test Suite and Final Cleanup

**Files:**
- All modified files

**Step 1: Run full test suite**

Run: `uv run pytest tests/unit/ -v`
Expected: All tests pass

**Step 2: Run linting**

Run: `uv run ruff check src/ tests/`
Expected: No errors

**Step 3: Run type checking**

Run: `uv run mypy src/`
Expected: No errors (or only pre-existing ones)

**Step 4: Final commit if any cleanup needed**

```bash
git add -A
git commit -m "chore: cleanup and formatting"
```

---

## Summary

| Task | Description | Estimated Time |
|------|-------------|----------------|
| 1 | Update pyvergeos dependency | 2 min |
| 2 | Add view fixture to conftest | 3 min |
| 3 | Add view helper functions | 5 min |
| 4 | Add view subapp and columns | 3 min |
| 5-6 | View list (TDD) | 5 min |
| 7-8 | View get (TDD) | 5 min |
| 9-10 | View create (TDD) | 5 min |
| 11 | View update (TDD) | 5 min |
| 12 | View delete (TDD) | 5 min |
| 13 | Refactor zone commands | 15 min |
| 14 | Refactor record commands | 15 min |
| 15 | Add --vnet-default-gateway | 5 min |
| 16 | Add --description to rule update | 3 min |
| 17 | Fix VM restart | 10 min |
| 18 | Final test suite | 5 min |

**Total: ~90 minutes**
