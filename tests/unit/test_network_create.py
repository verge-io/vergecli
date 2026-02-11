"""Tests for network create command."""

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


def test_network_create_cidr_auto_derives_ip(cli_runner, mock_client, mock_network):
    """When --cidr is given without --ip, auto-derive interface IP as first host."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        ["network", "create", "--name", "test-net", "--cidr", "10.99.99.0/24"],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["network_address"] == "10.99.99.0/24"
    assert call_kwargs["ip_address"] == "10.99.99.1"
    assert call_kwargs["network_type"] == "internal"  # default


def test_network_create_explicit_type(cli_runner, mock_client, mock_network):
    """Network create should pass --type to the SDK."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        ["network", "create", "--name", "test-net", "--type", "external"],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["network_type"] == "external"


def test_network_create_cidr_with_explicit_ip(cli_runner, mock_client, mock_network):
    """When both --cidr and --ip are given, use the explicit IP."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        [
            "network",
            "create",
            "--name",
            "test-net",
            "--cidr",
            "10.99.99.0/24",
            "--ip",
            "10.99.99.254",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert call_kwargs["network_address"] == "10.99.99.0/24"
    assert call_kwargs["ip_address"] == "10.99.99.254"


def test_network_create_no_cidr_no_ip(cli_runner, mock_client, mock_network):
    """When neither --cidr nor --ip is given, neither is passed to the SDK."""
    mock_client.networks.create.return_value = mock_network

    result = cli_runner.invoke(
        app,
        ["network", "create", "--name", "test-net"],
    )

    assert result.exit_code == 0
    call_kwargs = mock_client.networks.create.call_args[1]
    assert "network_address" not in call_kwargs
    assert "ip_address" not in call_kwargs
