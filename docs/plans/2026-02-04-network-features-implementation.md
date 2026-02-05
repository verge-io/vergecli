# Network Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add firewall rules, aliases, hosts, DNS zones/records, diagnostics, and apply operations to `vrg network` commands.

**Architecture:** Each feature is a separate Typer subapp registered under `network.app`. Commands follow existing patterns: `@handle_errors()` decorator, `get_context(ctx)` for client access, `resolve_resource_id()` for lookups, `output_result()` for output.

**Tech Stack:** Python 3.9+, Typer, Rich, pyvergeos SDK

**Test Environment:** See `.claude/TESTENV.md` for live system credentials (DEV System 1: 192.168.10.75)

---

## Task 1: Add Status Flags to Network List/Get

Update existing network commands to show `needs_restart`, `needs_rule_apply`, `needs_dns_apply` flags.

**Files:**
- Modify: `src/verge_cli/commands/network.py:21-22` (NETWORK_LIST_COLUMNS)
- Modify: `src/verge_cli/commands/network.py:282-300` (_network_to_dict)
- Test: `tests/unit/test_network_status.py` (new)

**Step 1: Write the failing test**

Create `tests/unit/test_network_status.py`:

```python
"""Tests for network status flags."""

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app


@pytest.fixture
def mock_network_with_flags():
    """Create a mock Network with status flags."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        data = {
            "description": "Test Network",
            "type": "internal",
            "network": "10.0.0.0/24",
            "ipaddress": "10.0.0.1",
            "status": "running",
            "running": True,
            "need_restart": True,
            "need_fw_apply": True,
            "need_dns_apply": False,
        }
        return data.get(key, default)

    net.get = mock_get
    return net


def test_network_list_shows_status_flags(cli_runner, mock_client, mock_network_with_flags):
    """Network list should show restart/rules/dns columns."""
    mock_client.networks.list.return_value = [mock_network_with_flags]

    result = cli_runner.invoke(app, ["network", "list"])

    assert result.exit_code == 0
    # Check that status flag columns appear
    assert "RESTART" in result.output or "restart" in result.output.lower()


def test_network_get_shows_status_flags(cli_runner, mock_client, mock_network_with_flags):
    """Network get should show status flags in output."""
    mock_client.networks.list.return_value = [mock_network_with_flags]
    mock_client.networks.get.return_value = mock_network_with_flags

    result = cli_runner.invoke(app, ["network", "get", "test-network"])

    assert result.exit_code == 0
    assert "needs_restart" in result.output or "need_restart" in result.output
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_status.py -v`
Expected: FAIL - "RESTART" not in output

**Step 3: Update network.py to include status flags**

In `src/verge_cli/commands/network.py`, update line 21:

```python
# Default columns for network list output
NETWORK_LIST_COLUMNS = ["name", "type", "network", "ipaddress", "status", "running", "restart", "rules", "dns"]
```

Update `_network_to_dict` function (line 282):

```python
def _network_to_dict(net: Any) -> dict[str, Any]:
    """Convert a Network object to a dictionary for output."""
    return {
        "key": net.key,
        "name": net.name,
        "description": net.get("description", ""),
        "type": net.get("type"),
        "network": net.get("network"),
        "ipaddress": net.get("ipaddress"),
        "gateway": net.get("gateway"),
        "mtu": net.get("mtu"),
        "status": net.get("status"),
        "running": net.get("running"),
        "dhcp_enabled": net.get("dhcp_enabled"),
        "dhcp_start": net.get("dhcp_start"),
        "dhcp_stop": net.get("dhcp_stop"),
        "dns": net.get("dns"),
        "domain": net.get("domain"),
        "needs_restart": net.get("need_restart", False),
        "needs_rule_apply": net.get("need_fw_apply", False),
        "needs_dns_apply": net.get("need_dns_apply", False),
        # Short aliases for list columns
        "restart": "Y" if net.get("need_restart", False) else "",
        "rules": "Y" if net.get("need_fw_apply", False) else "",
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_status.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/verge_cli/commands/network.py tests/unit/test_network_status.py
git commit -m "feat(network): add status flags to list/get output

Show needs_restart, needs_rule_apply, needs_dns_apply in network output.
Adds RESTART, RULES, DNS columns to list view."
```

---

## Task 2: Add Network Apply and Restart Commands

Add `apply-rules`, `apply-dns`, `restart`, and `status` commands to network.

**Files:**
- Modify: `src/verge_cli/commands/network.py` (add new commands)
- Test: `tests/unit/test_network_operations.py` (new)

**Step 1: Write the failing tests**

Create `tests/unit/test_network_operations.py`:

```python
"""Tests for network apply and restart operations."""

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app


@pytest.fixture
def mock_running_network():
    """Create a mock running Network."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        data = {
            "running": True,
            "status": "running",
            "need_restart": True,
            "need_fw_apply": True,
            "need_dns_apply": True,
        }
        return data.get(key, default)

    net.get = mock_get
    return net


def test_network_apply_rules(cli_runner, mock_client, mock_running_network):
    """Apply rules command should call network.apply_rules()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "apply-rules", "test-network"])

    assert result.exit_code == 0
    mock_running_network.apply_rules.assert_called_once()


def test_network_apply_dns(cli_runner, mock_client, mock_running_network):
    """Apply DNS command should call network.apply_dns()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "apply-dns", "test-network"])

    assert result.exit_code == 0
    mock_running_network.apply_dns.assert_called_once()


def test_network_restart(cli_runner, mock_client, mock_running_network):
    """Restart command should call network.restart()."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "restart", "test-network"])

    assert result.exit_code == 0
    mock_running_network.restart.assert_called_once()


def test_network_status(cli_runner, mock_client, mock_running_network):
    """Status command should show detailed status flags."""
    mock_client.networks.list.return_value = [mock_running_network]
    mock_client.networks.get.return_value = mock_running_network

    result = cli_runner.invoke(app, ["network", "status", "test-network"])

    assert result.exit_code == 0
    assert "test-network" in result.output
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_operations.py -v`
Expected: FAIL - "No such command 'apply-rules'"

**Step 3: Add the commands to network.py**

Add to `src/verge_cli/commands/network.py` after the `stop` command:

```python
@app.command("restart")
@handle_errors()
def network_restart(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    apply_rules: Annotated[
        bool,
        typer.Option("--apply-rules/--no-apply-rules", help="Apply firewall rules after restart"),
    ] = True,
    wait: Annotated[bool, typer.Option("--wait", "-w", help="Wait for network to be running")] = False,
    timeout: Annotated[int, typer.Option("--timeout", "-t", help="Timeout in seconds")] = 300,
) -> None:
    """Restart a virtual network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    net_obj.restart(apply_rules=apply_rules)
    output_success(f"Restarted network '{net_obj.name}'", quiet=vctx.quiet)

    if wait:
        from verge_cli.utils import wait_for_state

        net_obj = wait_for_state(
            vctx.client.networks.get,
            key,
            target_state="running",
            timeout=timeout,
            state_field="status",
            resource_type="network",
            quiet=vctx.quiet,
        )
        output_success(f"Network '{net_obj.name}' is now running", quiet=vctx.quiet)


@app.command("apply-rules")
@handle_errors()
def network_apply_rules(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
) -> None:
    """Apply pending firewall rules to a network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    if not net_obj.get("running"):
        typer.echo(f"Network '{net_obj.name}' is not running. Rules can only be applied to running networks.", err=True)
        raise typer.Exit(1)

    net_obj.apply_rules()
    output_success(f"Applied firewall rules to network '{net_obj.name}'", quiet=vctx.quiet)


@app.command("apply-dns")
@handle_errors()
def network_apply_dns(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
) -> None:
    """Apply pending DNS configuration to a network."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    if not net_obj.get("running"):
        typer.echo(f"Network '{net_obj.name}' is not running. DNS can only be applied to running networks.", err=True)
        raise typer.Exit(1)

    net_obj.apply_dns()
    output_success(f"Applied DNS configuration to network '{net_obj.name}'", quiet=vctx.quiet)


@app.command("status")
@handle_errors()
def network_status(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output format (table, json)"),
    ] = None,
) -> None:
    """Show detailed status of a network including pending changes."""
    vctx = get_context(ctx)

    key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(key)

    status_data = {
        "name": net_obj.name,
        "key": net_obj.key,
        "running": net_obj.get("running", False),
        "status": net_obj.get("status", "unknown"),
        "needs_restart": net_obj.get("need_restart", False),
        "needs_rule_apply": net_obj.get("need_fw_apply", False),
        "needs_dns_apply": net_obj.get("need_dns_apply", False),
        "needs_proxy_apply": net_obj.get("need_proxy_apply", False),
    }

    output_result(
        status_data,
        output_format=output or vctx.output_format,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_operations.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/verge_cli/commands/network.py tests/unit/test_network_operations.py
git commit -m "feat(network): add apply-rules, apply-dns, restart, status commands

- apply-rules: Apply pending firewall rule changes
- apply-dns: Apply pending DNS configuration changes
- restart: Restart network with optional --wait and --apply-rules
- status: Show detailed status including all pending change flags"
```

---

## Task 3: Create Firewall Rules Command Module

Create `network_rule.py` with list, get, create, update, delete, enable, disable commands.

**Files:**
- Create: `src/verge_cli/commands/network_rule.py`
- Modify: `src/verge_cli/commands/network.py` (register subapp)
- Test: `tests/unit/test_network_rule.py` (new)

**Step 1: Write the failing tests**

Create `tests/unit/test_network_rule.py`:

```python
"""Tests for network firewall rule commands."""

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_rules():
    """Create a mock Network for rule operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"

    def mock_get(key: str, default=None):
        return {"running": True}.get(key, default)

    net.get = mock_get
    return net


@pytest.fixture
def mock_rule():
    """Create a mock NetworkRule object."""
    rule = MagicMock()
    rule.key = 100
    rule.name = "Allow-HTTPS"

    def mock_get(key: str, default=None):
        data = {
            "name": "Allow-HTTPS",
            "direction": "incoming",
            "action": "accept",
            "protocol": "tcp",
            "destination_ports": "443",
            "enabled": True,
            "orderid": 1,
            "system_rule": False,
        }
        return data.get(key, default)

    rule.get = mock_get
    rule.is_system_rule = False
    rule.is_enabled = True
    return rule


def test_rule_list(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule list should show rules for a network."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]

    result = cli_runner.invoke(app, ["network", "rule", "list", "test-network"])

    assert result.exit_code == 0
    assert "Allow-HTTPS" in result.output


def test_rule_get(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule get should show rule details."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(app, ["network", "rule", "get", "test-network", "Allow-HTTPS"])

    assert result.exit_code == 0
    assert "Allow-HTTPS" in result.output


def test_rule_create(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule create should create a new rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.create.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        [
            "network", "rule", "create", "test-network",
            "--name", "Allow-HTTPS",
            "--direction", "incoming",
            "--action", "accept",
            "--protocol", "tcp",
            "--dest-ports", "443",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_rules.rules.create.assert_called_once()


def test_rule_delete(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule delete should delete a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "delete", "test-network", "Allow-HTTPS", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_rules.rules.delete.assert_called_once_with(100)


def test_rule_enable(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule enable should enable a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "enable", "test-network", "Allow-HTTPS"],
    )

    assert result.exit_code == 0
    mock_rule.enable.assert_called_once()


def test_rule_disable(cli_runner, mock_client, mock_network_for_rules, mock_rule):
    """Rule disable should disable a rule."""
    mock_client.networks.list.return_value = [mock_network_for_rules]
    mock_client.networks.get.return_value = mock_network_for_rules
    mock_network_for_rules.rules.list.return_value = [mock_rule]
    mock_network_for_rules.rules.get.return_value = mock_rule

    result = cli_runner.invoke(
        app,
        ["network", "rule", "disable", "test-network", "Allow-HTTPS"],
    )

    assert result.exit_code == 0
    mock_rule.disable.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_rule.py -v`
Expected: FAIL - "No such command 'rule'"

**Step 3: Create network_rule.py**

Create `src/verge_cli/commands/network_rule.py`:

```python
"""Network firewall rule commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="rule",
    help="Manage network firewall rules.",
    no_args_is_help=True,
)

# Default columns for rule list output
RULE_LIST_COLUMNS = ["name", "direction", "action", "protocol", "source_ip", "dest_ports", "enabled", "order"]


def _resolve_rule_id(network: Any, identifier: str) -> int:
    """Resolve a rule name or ID to a key."""
    # Try by name first
    rules = network.rules.list()
    for rule in rules:
        name = rule.get("name") or getattr(rule, "name", "")
        key = rule.get("$key") or getattr(rule, "key", None)
        if name == identifier:
            return key

    # If numeric, treat as key
    if identifier.isdigit():
        return int(identifier)

    from verge_cli.errors import ResourceNotFoundError
    raise ResourceNotFoundError(f"Rule '{identifier}' not found")


def _rule_to_dict(rule: Any) -> dict[str, Any]:
    """Convert a NetworkRule object to a dictionary for output."""
    return {
        "key": rule.key,
        "name": rule.get("name", ""),
        "description": rule.get("description", ""),
        "direction": rule.get("direction", "incoming"),
        "action": rule.get("action", "accept"),
        "protocol": rule.get("protocol", "any"),
        "interface": rule.get("interface", "auto"),
        "source_ip": rule.get("source_ip", ""),
        "source_ports": rule.get("source_ports", ""),
        "dest_ip": rule.get("destination_ip", ""),
        "dest_ports": rule.get("destination_ports", ""),
        "target_ip": rule.get("target_ip", ""),
        "target_ports": rule.get("target_ports", ""),
        "enabled": rule.get("enabled", True),
        "log": rule.get("log", False),
        "statistics": rule.get("statistics", False),
        "order": rule.get("orderid", 0),
        "system_rule": rule.get("system_rule", False),
        "packets": rule.get("packets", 0),
        "bytes": rule.get("bytes", 0),
    }


@app.command("list")
@handle_errors()
def rule_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    direction: Annotated[str | None, typer.Option("--direction", "-d", help="Filter by direction")] = None,
    action: Annotated[str | None, typer.Option("--action", "-a", help="Filter by action")] = None,
    enabled: Annotated[bool | None, typer.Option("--enabled/--disabled", help="Filter by enabled state")] = None,
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List firewall rules for a network."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    # Build filter kwargs
    filter_kwargs: dict[str, Any] = {}
    if direction:
        filter_kwargs["direction"] = direction
    if action:
        filter_kwargs["action"] = action
    if enabled is not None:
        filter_kwargs["enabled"] = enabled

    rules = net_obj.rules.list(**filter_kwargs)
    data = [_rule_to_dict(rule) for rule in rules]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=RULE_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def rule_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    rule: Annotated[str, typer.Argument(help="Rule name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Get details of a firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    rule_key = _resolve_rule_id(net_obj, rule)
    rule_obj = net_obj.rules.get(rule_key)

    output_result(
        _rule_to_dict(rule_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def rule_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    name: Annotated[str, typer.Option("--name", "-n", help="Rule name")],
    direction: Annotated[str, typer.Option("--direction", "-d", help="Direction (incoming/outgoing)")] = "incoming",
    action: Annotated[str, typer.Option("--action", "-a", help="Action (accept/drop/reject/translate/route)")] = "accept",
    protocol: Annotated[str, typer.Option("--protocol", "-p", help="Protocol (tcp/udp/tcpudp/icmp/any)")] = "any",
    interface: Annotated[str, typer.Option("--interface", help="Interface (auto/router/dmz/wireguard/any)")] = "auto",
    source_ip: Annotated[str | None, typer.Option("--source-ip", help="Source IP/CIDR or alias:name")] = None,
    source_ports: Annotated[str | None, typer.Option("--source-ports", help="Source ports")] = None,
    dest_ip: Annotated[str | None, typer.Option("--dest-ip", help="Destination IP/CIDR or alias:name")] = None,
    dest_ports: Annotated[str | None, typer.Option("--dest-ports", help="Destination ports")] = None,
    target_ip: Annotated[str | None, typer.Option("--target-ip", help="NAT target IP")] = None,
    target_ports: Annotated[str | None, typer.Option("--target-ports", help="NAT target ports")] = None,
    enabled: Annotated[bool, typer.Option("--enabled/--disabled", help="Enable rule")] = True,
    log: Annotated[bool, typer.Option("--log/--no-log", help="Enable logging")] = False,
    stats: Annotated[bool, typer.Option("--stats/--no-stats", help="Enable statistics")] = False,
    order: Annotated[int | None, typer.Option("--order", help="Rule order position")] = None,
    description: Annotated[str, typer.Option("--description", help="Rule description")] = "",
) -> None:
    """Create a new firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    create_kwargs: dict[str, Any] = {
        "name": name,
        "direction": direction,
        "action": action,
        "protocol": protocol,
        "interface": interface,
        "enabled": enabled,
        "log": log,
        "statistics": stats,
    }

    if source_ip:
        create_kwargs["source_ip"] = source_ip
    if source_ports:
        create_kwargs["source_ports"] = source_ports
    if dest_ip:
        create_kwargs["destination_ip"] = dest_ip
    if dest_ports:
        create_kwargs["destination_ports"] = dest_ports
    if target_ip:
        create_kwargs["target_ip"] = target_ip
    if target_ports:
        create_kwargs["target_ports"] = target_ports
    if order is not None:
        create_kwargs["order"] = order
    if description:
        create_kwargs["description"] = description

    rule_obj = net_obj.rules.create(**create_kwargs)

    output_success(f"Created rule '{rule_obj.name}' (key: {rule_obj.key})", quiet=vctx.quiet)

    output_result(
        _rule_to_dict(rule_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def rule_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    rule: Annotated[str, typer.Argument(help="Rule name or key")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New rule name")] = None,
    direction: Annotated[str | None, typer.Option("--direction", "-d", help="Direction")] = None,
    action: Annotated[str | None, typer.Option("--action", "-a", help="Action")] = None,
    protocol: Annotated[str | None, typer.Option("--protocol", "-p", help="Protocol")] = None,
    source_ip: Annotated[str | None, typer.Option("--source-ip", help="Source IP")] = None,
    source_ports: Annotated[str | None, typer.Option("--source-ports", help="Source ports")] = None,
    dest_ip: Annotated[str | None, typer.Option("--dest-ip", help="Destination IP")] = None,
    dest_ports: Annotated[str | None, typer.Option("--dest-ports", help="Destination ports")] = None,
    target_ip: Annotated[str | None, typer.Option("--target-ip", help="NAT target IP")] = None,
    target_ports: Annotated[str | None, typer.Option("--target-ports", help="NAT target ports")] = None,
    enabled: Annotated[bool | None, typer.Option("--enabled/--disabled", help="Enable/disable rule")] = None,
    log: Annotated[bool | None, typer.Option("--log/--no-log", help="Enable/disable logging")] = None,
    stats: Annotated[bool | None, typer.Option("--stats/--no-stats", help="Enable/disable statistics")] = None,
) -> None:
    """Update a firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    rule_key = _resolve_rule_id(net_obj, rule)

    # Build update kwargs (only non-None values)
    updates: dict[str, Any] = {}
    if name is not None:
        updates["name"] = name
    if direction is not None:
        updates["direction"] = direction
    if action is not None:
        updates["action"] = action
    if protocol is not None:
        updates["protocol"] = protocol
    if source_ip is not None:
        updates["source_ip"] = source_ip
    if source_ports is not None:
        updates["source_ports"] = source_ports
    if dest_ip is not None:
        updates["destination_ip"] = dest_ip
    if dest_ports is not None:
        updates["destination_ports"] = dest_ports
    if target_ip is not None:
        updates["target_ip"] = target_ip
    if target_ports is not None:
        updates["target_ports"] = target_ports
    if enabled is not None:
        updates["enabled"] = enabled
    if log is not None:
        updates["log"] = log
    if stats is not None:
        updates["statistics"] = stats

    if not updates:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    rule_obj = net_obj.rules.update(rule_key, **updates)

    output_success(f"Updated rule '{rule_obj.name}'", quiet=vctx.quiet)

    output_result(
        _rule_to_dict(rule_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def rule_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    rule: Annotated[str, typer.Argument(help="Rule name or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete a firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    rule_key = _resolve_rule_id(net_obj, rule)
    rule_obj = net_obj.rules.get(rule_key)

    rule_name = rule_obj.get("name", rule_key)

    if not confirm_action(f"Delete rule '{rule_name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    net_obj.rules.delete(rule_key)
    output_success(f"Deleted rule '{rule_name}'", quiet=vctx.quiet)


@app.command("enable")
@handle_errors()
def rule_enable(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    rule: Annotated[str, typer.Argument(help="Rule name or key")],
) -> None:
    """Enable a firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    rule_key = _resolve_rule_id(net_obj, rule)
    rule_obj = net_obj.rules.get(rule_key)

    rule_obj.enable()
    output_success(f"Enabled rule '{rule_obj.name}'", quiet=vctx.quiet)


@app.command("disable")
@handle_errors()
def rule_disable(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    rule: Annotated[str, typer.Argument(help="Rule name or key")],
) -> None:
    """Disable a firewall rule."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    rule_key = _resolve_rule_id(net_obj, rule)
    rule_obj = net_obj.rules.get(rule_key)

    rule_obj.disable()
    output_success(f"Disabled rule '{rule_obj.name}'", quiet=vctx.quiet)
```

**Step 4: Register the subapp in network.py**

Add to `src/verge_cli/commands/network.py` after imports:

```python
from verge_cli.commands import network_rule
```

Add after `app` definition (around line 18):

```python
app.add_typer(network_rule.app, name="rule")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_rule.py -v`
Expected: PASS

**Step 6: Run linting and type checking**

Run: `uv run ruff check src/verge_cli/commands/network_rule.py`
Run: `uv run mypy src/verge_cli/commands/network_rule.py`
Fix any issues.

**Step 7: Commit**

```bash
git add src/verge_cli/commands/network_rule.py src/verge_cli/commands/network.py tests/unit/test_network_rule.py
git commit -m "feat(network): add firewall rule commands

Add vrg network rule subcommand with:
- list: List rules with direction/action/enabled filters
- get: Get rule details by name or key
- create: Create new rule with full options
- update: Update existing rule
- delete: Delete rule with confirmation
- enable/disable: Toggle rule state

Rules support NAT translation, logging, statistics tracking."
```

---

## Task 4: Create IP Alias Command Module

Create `network_alias.py` with list, get, create, update, delete commands.

**Files:**
- Create: `src/verge_cli/commands/network_alias.py`
- Modify: `src/verge_cli/commands/network.py` (register subapp)
- Test: `tests/unit/test_network_alias.py` (new)

**Step 1: Write the failing tests**

Create `tests/unit/test_network_alias.py`:

```python
"""Tests for network IP alias commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_aliases():
    """Create a mock Network for alias operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"
    return net


@pytest.fixture
def mock_alias():
    """Create a mock NetworkAlias object."""
    alias = MagicMock()
    alias.key = 200
    alias.name = "webserver"

    def mock_get(key: str, default=None):
        data = {
            "ip": "10.0.0.100",
            "hostname": "webserver",
            "description": "Main web server",
        }
        return data.get(key, default)

    alias.get = mock_get
    alias.ip = "10.0.0.100"
    alias.hostname = "webserver"
    return alias


def test_alias_list(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias list should show aliases for a network."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]

    result = cli_runner.invoke(app, ["network", "alias", "list", "test-network"])

    assert result.exit_code == 0
    assert "webserver" in result.output


def test_alias_create(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias create should create a new alias."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.create.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        [
            "network", "alias", "create", "test-network",
            "--ip", "10.0.0.100",
            "--name", "webserver",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.create.assert_called_once()


def test_alias_delete(cli_runner, mock_client, mock_network_for_aliases, mock_alias):
    """Alias delete should delete an alias."""
    mock_client.networks.list.return_value = [mock_network_for_aliases]
    mock_client.networks.get.return_value = mock_network_for_aliases
    mock_network_for_aliases.aliases.list.return_value = [mock_alias]
    mock_network_for_aliases.aliases.get.return_value = mock_alias

    result = cli_runner.invoke(
        app,
        ["network", "alias", "delete", "test-network", "webserver", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_aliases.aliases.delete.assert_called_once_with(200)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_network_alias.py -v`
Expected: FAIL - "No such command 'alias'"

**Step 3: Create network_alias.py**

Create `src/verge_cli/commands/network_alias.py`:

```python
"""Network IP alias commands for Verge CLI."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from verge_cli.context import get_context
from verge_cli.errors import handle_errors, ResourceNotFoundError
from verge_cli.output import output_result, output_success
from verge_cli.utils import confirm_action, resolve_resource_id

app = typer.Typer(
    name="alias",
    help="Manage network IP aliases.",
    no_args_is_help=True,
)

# Default columns for alias list output
ALIAS_LIST_COLUMNS = ["hostname", "ip", "description"]


def _resolve_alias_id(network: Any, identifier: str) -> int:
    """Resolve an alias name, IP, or ID to a key."""
    aliases = network.aliases.list()
    for alias in aliases:
        hostname = alias.get("hostname") or getattr(alias, "hostname", "")
        ip = alias.get("ip") or getattr(alias, "ip", "")
        key = alias.get("$key") or getattr(alias, "key", None)
        if hostname == identifier or ip == identifier:
            return key

    if identifier.isdigit():
        return int(identifier)

    raise ResourceNotFoundError(f"Alias '{identifier}' not found")


def _alias_to_dict(alias: Any) -> dict[str, Any]:
    """Convert a NetworkAlias object to a dictionary for output."""
    return {
        "key": alias.key,
        "ip": alias.get("ip", ""),
        "hostname": alias.get("hostname", ""),
        "description": alias.get("description", ""),
        "mac": alias.get("mac", ""),
    }


@app.command("list")
@handle_errors()
def alias_list(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """List IP aliases for a network."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    aliases = net_obj.aliases.list()
    data = [_alias_to_dict(alias) for alias in aliases]

    output_result(
        data,
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        columns=ALIAS_LIST_COLUMNS,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("get")
@handle_errors()
def alias_get(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
    output: Annotated[str | None, typer.Option("--output", "-o", help="Output format")] = None,
    query: Annotated[str | None, typer.Option("--query", help="Extract field")] = None,
) -> None:
    """Get details of an IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    alias_obj = net_obj.aliases.get(alias_key)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=output or vctx.output_format,
        query=query or vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("create")
@handle_errors()
def alias_create(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    ip: Annotated[str, typer.Option("--ip", "-i", help="IP address or CIDR")],
    name: Annotated[str, typer.Option("--name", "-n", help="Alias name (used as alias:name in rules)")],
    description: Annotated[str, typer.Option("--description", "-d", help="Description")] = "",
) -> None:
    """Create a new IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_obj = net_obj.aliases.create(ip=ip, name=name, description=description)

    output_success(f"Created alias '{alias_obj.hostname}' ({alias_obj.ip})", quiet=vctx.quiet)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("update")
@handle_errors()
def alias_update(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
    ip: Annotated[str | None, typer.Option("--ip", "-i", help="New IP address")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n", help="New alias name")] = None,
    description: Annotated[str | None, typer.Option("--description", "-d", help="New description")] = None,
) -> None:
    """Update an IP alias (delete + create)."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    existing = net_obj.aliases.get(alias_key)

    # Merge updates with existing values
    new_ip = ip if ip is not None else existing.ip
    new_name = name if name is not None else existing.hostname
    new_desc = description if description is not None else (existing.get("description") or "")

    if ip is None and name is None and description is None:
        typer.echo("No updates specified.", err=True)
        raise typer.Exit(2)

    # Delete and recreate (SDK doesn't expose PUT for aliases)
    net_obj.aliases.delete(alias_key)
    alias_obj = net_obj.aliases.create(ip=new_ip, name=new_name, description=new_desc)

    output_success(f"Updated alias '{alias_obj.hostname}'", quiet=vctx.quiet)

    output_result(
        _alias_to_dict(alias_obj),
        output_format=vctx.output_format,
        query=vctx.query,
        quiet=vctx.quiet,
        no_color=vctx.no_color,
    )


@app.command("delete")
@handle_errors()
def alias_delete(
    ctx: typer.Context,
    network: Annotated[str, typer.Argument(help="Network name or key")],
    alias: Annotated[str, typer.Argument(help="Alias name, IP, or key")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Delete an IP alias."""
    vctx = get_context(ctx)

    net_key = resolve_resource_id(vctx.client.networks, network, "network")
    net_obj = vctx.client.networks.get(net_key)

    alias_key = _resolve_alias_id(net_obj, alias)
    alias_obj = net_obj.aliases.get(alias_key)

    alias_name = alias_obj.hostname or alias_obj.ip

    if not confirm_action(f"Delete alias '{alias_name}'?", yes=yes):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    net_obj.aliases.delete(alias_key)
    output_success(f"Deleted alias '{alias_name}'", quiet=vctx.quiet)
```

**Step 4: Register the subapp in network.py**

Add to imports in `src/verge_cli/commands/network.py`:

```python
from verge_cli.commands import network_alias
```

Add after rule registration:

```python
app.add_typer(network_alias.app, name="alias")
```

**Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_network_alias.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/verge_cli/commands/network_alias.py src/verge_cli/commands/network.py tests/unit/test_network_alias.py
git commit -m "feat(network): add IP alias commands

Add vrg network alias subcommand with:
- list: List aliases for a network
- get: Get alias by name, IP, or key
- create: Create new alias with IP and name
- update: Update alias (delete + create pattern)
- delete: Delete alias with confirmation

Aliases can be used in firewall rules as alias:name."
```

---

## Task 5: Create Host Override Command Module

Create `network_host.py` with list, get, create, update, delete commands.

**Files:**
- Create: `src/verge_cli/commands/network_host.py`
- Modify: `src/verge_cli/commands/network.py` (register subapp)
- Test: `tests/unit/test_network_host.py` (new)

**Step 1-6: Follow same pattern as Task 4**

The implementation follows the same structure as network_alias.py but uses:
- `network.hosts.list()`, `network.hosts.get()`, etc.
- Fields: hostname, ip, type (host/domain)
- SDK has `update()` method so no delete+create needed

Create `src/verge_cli/commands/network_host.py` and `tests/unit/test_network_host.py`.

**Commit:**

```bash
git commit -m "feat(network): add host override commands

Add vrg network host subcommand with:
- list: List host overrides for a network
- get: Get host by hostname, IP, or key
- create: Create new host override
- update: Update existing host
- delete: Delete host override

Changes require apply-dns to take effect."
```

---

## Task 6: Create DNS Zone and Record Command Modules

Create `network_dns.py` with zone and record subcommands.

**Files:**
- Create: `src/verge_cli/commands/network_dns.py`
- Modify: `src/verge_cli/commands/network.py` (register subapp)
- Test: `tests/unit/test_network_dns.py` (new)

**Step 1-6: Follow same pattern but with nested structure**

The DNS module has two subcommands: `zone` and `record`.

```python
# Structure:
dns_app = typer.Typer(name="dns", help="Manage DNS zones and records.")
zone_app = typer.Typer(name="zone", help="Manage DNS zones.")
record_app = typer.Typer(name="record", help="Manage DNS records.")

dns_app.add_typer(zone_app, name="zone")
dns_app.add_typer(record_app, name="record")
```

Records require both network and zone arguments.

**Commit:**

```bash
git commit -m "feat(network): add DNS zone and record commands

Add vrg network dns subcommand with:
- zone list/get/create/update/delete
- record list/get/create/update/delete

Zone commands work on networks with BIND enabled.
Record commands require zone identifier.
Changes require apply-dns to take effect.

Note: DNS View management blocked until SDK issue #24."
```

---

## Task 7: Create Diagnostics Command Module

Create `network_diag.py` with leases, addresses, stats commands.

**Files:**
- Create: `src/verge_cli/commands/network_diag.py`
- Modify: `src/verge_cli/commands/network.py` (register subapp)
- Test: `tests/unit/test_network_diag.py` (new)

**Step 1-6: Follow same pattern**

Uses `network.diagnostics(diagnostic_type=...)` and `network.statistics()` from SDK.

**Commit:**

```bash
git commit -m "feat(network): add diagnostics commands

Add vrg network diag subcommand with:
- leases: Show DHCP leases
- addresses: Show all network addresses
- stats: Show traffic and quality statistics

Useful for troubleshooting network issues."
```

---

## Task 8: Add needs_restart to VM List/Get

Update VM commands to show needs_restart flag.

**Files:**
- Modify: `src/verge_cli/commands/vm.py`
- Test: `tests/unit/test_vm_status.py` (new)

**Step 1-6: Follow same pattern as Task 1**

Add `needs_restart` field to `_vm_to_dict()` and add column to list output.

**Commit:**

```bash
git commit -m "feat(vm): add needs_restart flag to list/get output

Shows when a VM has pending changes that require restart."
```

---

## Task 9: Run Full Test Suite and Fix Issues

**Step 1: Run all unit tests**

Run: `uv run pytest tests/unit/ -v`

**Step 2: Run linting**

Run: `uv run ruff check src/verge_cli/commands/`
Run: `uv run ruff check --fix` (if needed)

**Step 3: Run type checking**

Run: `uv run mypy src/verge_cli/commands/`

**Step 4: Fix any issues found**

**Step 5: Commit fixes**

```bash
git commit -m "fix: resolve linting and type checking issues"
```

---

## Task 10: Integration Testing

**Test Environment:** See `.claude/TESTENV.md`
- DEV System 1: https://192.168.10.75 (admin/jenifer8)

**Step 1: Set environment variables**

```bash
export VERGE_HOST=https://192.168.10.75
export VERGE_USERNAME=admin
export VERGE_PASSWORD=jenifer8
export VERGE_VERIFY_SSL=false
```

**Step 2: Test network commands manually**

```bash
# List networks
uv run vrg network list

# Check status flags
uv run vrg network status <network-name>

# Test rule commands on a network
uv run vrg network rule list <network-name>
uv run vrg network rule create <network-name> --name "test-rule" --direction incoming --action accept --protocol tcp --dest-ports 8080
uv run vrg network rule list <network-name>
uv run vrg network rule delete <network-name> test-rule --yes

# Test alias commands
uv run vrg network alias list <network-name>
uv run vrg network alias create <network-name> --ip 10.0.0.200 --name "test-alias"
uv run vrg network alias delete <network-name> test-alias --yes

# Test apply commands
uv run vrg network apply-rules <network-name>
```

**Step 3: Document any issues found and fix**

**Step 4: Final commit**

```bash
git commit -m "test: verify integration with live VergeOS system"
```

---

## Summary

| Task | Description | Estimated Steps |
|------|-------------|-----------------|
| 1 | Add status flags to network list/get | 5 |
| 2 | Add apply/restart/status commands | 5 |
| 3 | Create firewall rules module | 7 |
| 4 | Create IP alias module | 6 |
| 5 | Create host override module | 6 |
| 6 | Create DNS zone/record module | 6 |
| 7 | Create diagnostics module | 6 |
| 8 | Add needs_restart to VM | 6 |
| 9 | Full test suite and fixes | 5 |
| 10 | Integration testing | 4 |

**Total: ~56 steps across 10 tasks**
