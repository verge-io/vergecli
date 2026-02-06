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
