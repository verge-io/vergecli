"""Tests for network DNS zone and record commands."""

from unittest.mock import MagicMock

import pytest

from verge_cli.cli import app


@pytest.fixture
def mock_network_for_dns():
    """Create a mock Network for DNS operations."""
    net = MagicMock()
    net.key = 1
    net.name = "test-network"
    return net


@pytest.fixture
def mock_zone():
    """Create a mock DNS Zone object."""
    zone = MagicMock()
    zone.key = 100
    zone.domain = "example.com"

    def mock_get(key: str, default=None):
        data = {
            "$key": 100,
            "domain": "example.com",
            "type": "master",
            "serial_number": 2024010101,
        }
        return data.get(key, default)

    zone.get = mock_get
    return zone


@pytest.fixture
def mock_record():
    """Create a mock DNS Record object."""
    record = MagicMock()
    record.key = 200

    def mock_get(key: str, default=None):
        data = {
            "$key": 200,
            "host": "www",
            "type": "A",
            "value": "10.0.0.100",
            "ttl": 3600,
            "mx_preference": 0,
        }
        return data.get(key, default)

    record.get = mock_get
    return record


# =============================================================================
# Zone List Tests
# =============================================================================


def test_zone_list(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone list should show DNS zones for a network."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]

    result = cli_runner.invoke(app, ["network", "dns", "zone", "list", "test-network"])

    assert result.exit_code == 0
    assert "example.com" in result.output


def test_zone_list_empty(cli_runner, mock_client, mock_network_for_dns):
    """Zone list should handle empty zone list."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = []

    result = cli_runner.invoke(app, ["network", "dns", "zone", "list", "test-network"])

    assert result.exit_code == 0


# =============================================================================
# Zone Get Tests
# =============================================================================


def test_zone_get(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone get should show zone details."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    result = cli_runner.invoke(
        app, ["network", "dns", "zone", "get", "test-network", "example.com"]
    )

    assert result.exit_code == 0
    assert "example.com" in result.output
    assert "master" in result.output


def test_zone_get_by_id(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone get should work with numeric ID."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    result = cli_runner.invoke(app, ["network", "dns", "zone", "get", "test-network", "100"])

    assert result.exit_code == 0
    mock_network_for_dns.dns_zones.get.assert_called_once_with(100)


# =============================================================================
# Zone Create Tests
# =============================================================================


def test_zone_create(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone create should create a new DNS zone."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.create.return_value = mock_zone

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "zone",
            "create",
            "test-network",
            "--domain",
            "example.com",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_zones.create.assert_called_once()
    call_kwargs = mock_network_for_dns.dns_zones.create.call_args[1]
    assert call_kwargs["domain"] == "example.com"


def test_zone_create_with_type(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone create should support zone type option."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.create.return_value = mock_zone

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "zone",
            "create",
            "test-network",
            "--domain",
            "example.com",
            "--type",
            "slave",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_network_for_dns.dns_zones.create.call_args[1]
    assert call_kwargs["type"] == "slave"
    assert call_kwargs["domain"] == "example.com"


# =============================================================================
# Zone Update Tests
# =============================================================================


def test_zone_update(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone update should update zone with new values."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    updated_zone = MagicMock()
    updated_zone.key = 100
    updated_zone.domain = "updated.com"
    updated_zone.get = lambda k, d=None: {
        "$key": 100,
        "domain": "updated.com",
        "type": "master",
        "serial_number": 2024010102,
    }.get(k, d)
    mock_network_for_dns.dns_zones.update.return_value = updated_zone

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "zone",
            "update",
            "test-network",
            "example.com",
            "--domain",
            "updated.com",
        ],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_zones.update.assert_called_once()


def test_zone_update_no_changes(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone update with no options should fail."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    result = cli_runner.invoke(
        app,
        ["network", "dns", "zone", "update", "test-network", "example.com"],
    )

    assert result.exit_code == 2
    assert "No updates specified" in result.output


# =============================================================================
# Zone Delete Tests
# =============================================================================


def test_zone_delete(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone delete should delete a DNS zone."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    result = cli_runner.invoke(
        app,
        ["network", "dns", "zone", "delete", "test-network", "example.com", "--yes"],
    )

    assert result.exit_code == 0
    mock_network_for_dns.dns_zones.delete.assert_called_once_with(100)


def test_zone_delete_cancelled(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Zone delete should be cancellable."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    result = cli_runner.invoke(
        app,
        ["network", "dns", "zone", "delete", "test-network", "example.com"],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_network_for_dns.dns_zones.delete.assert_not_called()


# =============================================================================
# Record List Tests
# =============================================================================


def test_record_list(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record list should show DNS records for a zone."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]

    result = cli_runner.invoke(
        app, ["network", "dns", "record", "list", "test-network", "example.com"]
    )

    assert result.exit_code == 0
    assert "www" in result.output


def test_record_list_with_type_filter(
    cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record
):
    """Record list should support filtering by record type."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]

    result = cli_runner.invoke(
        app,
        ["network", "dns", "record", "list", "test-network", "example.com", "--type", "A"],
    )

    assert result.exit_code == 0
    mock_zone.records.list.assert_called_once_with(type="A")


# =============================================================================
# Record Get Tests
# =============================================================================


def test_record_get(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record get should show record details."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]
    mock_zone.records.get.return_value = mock_record

    result = cli_runner.invoke(
        app, ["network", "dns", "record", "get", "test-network", "example.com", "www"]
    )

    assert result.exit_code == 0
    assert "www" in result.output
    assert "10.0.0.100" in result.output


def test_record_get_by_id(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record get should work with numeric ID."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.get.return_value = mock_record

    result = cli_runner.invoke(
        app, ["network", "dns", "record", "get", "test-network", "example.com", "200"]
    )

    assert result.exit_code == 0
    mock_zone.records.get.assert_called_once_with(200)


# =============================================================================
# Record Create Tests
# =============================================================================


def test_record_create_a(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record create should create an A record."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.create.return_value = mock_record

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "record",
            "create",
            "test-network",
            "example.com",
            "--name",
            "www",
            "--type",
            "A",
            "--address",
            "10.0.0.100",
        ],
    )

    assert result.exit_code == 0
    mock_zone.records.create.assert_called_once()
    call_kwargs = mock_zone.records.create.call_args[1]
    assert call_kwargs["host"] == "www"
    assert call_kwargs["type"] == "A"
    assert call_kwargs["value"] == "10.0.0.100"


def test_record_create_mx(cli_runner, mock_client, mock_network_for_dns, mock_zone):
    """Record create should support MX records with priority."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone

    mx_record = MagicMock()
    mx_record.key = 201
    mx_record.get = lambda k, d=None: {
        "$key": 201,
        "host": "@",
        "type": "MX",
        "value": "mail.example.com",
        "ttl": 3600,
        "mx_preference": 10,
    }.get(k, d)
    mock_zone.records.create.return_value = mx_record

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "record",
            "create",
            "test-network",
            "example.com",
            "--name",
            "@",
            "--type",
            "MX",
            "--address",
            "mail.example.com",
            "--priority",
            "10",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_zone.records.create.call_args[1]
    assert call_kwargs["mx_preference"] == 10


def test_record_create_with_ttl(
    cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record
):
    """Record create should support custom TTL."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.create.return_value = mock_record

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "record",
            "create",
            "test-network",
            "example.com",
            "--name",
            "www",
            "--type",
            "A",
            "--address",
            "10.0.0.100",
            "--ttl",
            "7200",
        ],
    )

    assert result.exit_code == 0
    call_kwargs = mock_zone.records.create.call_args[1]
    assert call_kwargs["ttl"] == 7200


# =============================================================================
# Record Update Tests
# =============================================================================


def test_record_update(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record update should update record with new values."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]
    mock_zone.records.get.return_value = mock_record

    updated_record = MagicMock()
    updated_record.key = 200
    updated_record.get = lambda k, d=None: {
        "$key": 200,
        "host": "www",
        "type": "A",
        "value": "10.0.0.200",
        "ttl": 3600,
        "mx_preference": 0,
    }.get(k, d)
    mock_zone.records.update.return_value = updated_record

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "record",
            "update",
            "test-network",
            "example.com",
            "www",
            "--address",
            "10.0.0.200",
        ],
    )

    assert result.exit_code == 0
    mock_zone.records.update.assert_called_once()


def test_record_update_no_changes(
    cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record
):
    """Record update with no options should fail."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]
    mock_zone.records.get.return_value = mock_record

    result = cli_runner.invoke(
        app,
        ["network", "dns", "record", "update", "test-network", "example.com", "www"],
    )

    assert result.exit_code == 2
    assert "No updates specified" in result.output


# =============================================================================
# Record Delete Tests
# =============================================================================


def test_record_delete(cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record):
    """Record delete should delete a DNS record."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]
    mock_zone.records.get.return_value = mock_record

    result = cli_runner.invoke(
        app,
        [
            "network",
            "dns",
            "record",
            "delete",
            "test-network",
            "example.com",
            "www",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    mock_zone.records.delete.assert_called_once_with(200)


def test_record_delete_cancelled(
    cli_runner, mock_client, mock_network_for_dns, mock_zone, mock_record
):
    """Record delete should be cancellable."""
    mock_client.networks.list.return_value = [mock_network_for_dns]
    mock_client.networks.get.return_value = mock_network_for_dns
    mock_network_for_dns.dns_zones.list.return_value = [mock_zone]
    mock_network_for_dns.dns_zones.get.return_value = mock_zone
    mock_zone.records.list.return_value = [mock_record]
    mock_zone.records.get.return_value = mock_record

    result = cli_runner.invoke(
        app,
        ["network", "dns", "record", "delete", "test-network", "example.com", "www"],
        input="n\n",
    )

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_zone.records.delete.assert_not_called()
