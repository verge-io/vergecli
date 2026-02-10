"""Tests for certificate management commands."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from pyvergeos.exceptions import NotFoundError
from typer.testing import CliRunner

from verge_cli.cli import app


def test_cert_list(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test listing certificates."""
    mock_client.certificates.list.return_value = [mock_certificate]

    result = cli_runner.invoke(app, ["certificate", "list"])

    assert result.exit_code == 0
    assert "example.com" in result.output
    mock_client.certificates.list.assert_called_once_with(filter=None)


def test_cert_list_by_type(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test listing certificates filtered by type."""
    mock_client.certificates.list.return_value = [mock_certificate]

    result = cli_runner.invoke(app, ["certificate", "list", "--type", "letsencrypt"])

    assert result.exit_code == 0
    mock_client.certificates.list.assert_called_once_with(cert_type="LetsEncrypt", filter=None)


def test_cert_list_valid(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test listing valid certificates."""
    mock_client.certificates.list_valid.return_value = [mock_certificate]

    result = cli_runner.invoke(app, ["certificate", "list", "--valid"])

    assert result.exit_code == 0
    mock_client.certificates.list_valid.assert_called_once()


def test_cert_list_expired(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test listing expired certificates."""
    mock_client.certificates.list_expired.return_value = [mock_certificate]

    result = cli_runner.invoke(app, ["certificate", "list", "--expired"])

    assert result.exit_code == 0
    mock_client.certificates.list_expired.assert_called_once()


def test_cert_list_expiring(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test listing certificates expiring within N days."""
    mock_client.certificates.list_expiring.return_value = [mock_certificate]

    result = cli_runner.invoke(app, ["certificate", "list", "--expiring-in", "30"])

    assert result.exit_code == 0
    mock_client.certificates.list_expiring.assert_called_once_with(days=30)


def test_cert_list_valid_expired_exclusive(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test that --valid and --expired are mutually exclusive."""
    result = cli_runner.invoke(app, ["certificate", "list", "--valid", "--expired"])

    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_cert_get_by_key(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test getting a certificate by numeric key."""
    mock_client.certificates.get.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "get", "70"])

    assert result.exit_code == 0
    assert "example.com" in result.output
    mock_client.certificates.get.assert_called_once_with(key=70, include_keys=False)


def test_cert_get_by_domain(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test getting a certificate by domain name."""
    mock_client.certificates.get.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "get", "example.com"])

    assert result.exit_code == 0
    assert "example.com" in result.output
    mock_client.certificates.get.assert_called_once_with(domain="example.com", include_keys=False)


def test_cert_get_show_keys(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test getting a certificate with --show-keys."""
    mock_client.certificates.get.return_value = mock_certificate

    result = cli_runner.invoke(
        app, ["-o", "json", "certificate", "get", "example.com", "--show-keys"]
    )

    assert result.exit_code == 0
    mock_client.certificates.get.assert_called_once_with(domain="example.com", include_keys=True)
    # With --show-keys, PEM data should be in the output
    assert "BEGIN CERTIFICATE" in result.output


def test_cert_create_self_signed(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test creating a self-signed certificate."""
    mock_client.certificates.create.return_value = mock_certificate

    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "create",
            "--domain",
            "internal.local",
            "--type",
            "self-signed",
        ],
    )

    assert result.exit_code == 0
    assert "Created certificate" in result.output
    mock_client.certificates.create.assert_called_once_with(
        domain="internal.local",
        cert_type="SelfSigned",
    )


def test_cert_create_letsencrypt(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test creating a Let's Encrypt certificate."""
    mock_client.certificates.create.return_value = mock_certificate

    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "create",
            "--domain",
            "public.example.com",
            "--type",
            "letsencrypt",
            "--agree-tos",
            "--contact-user",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Created certificate" in result.output
    mock_client.certificates.create.assert_called_once_with(
        domain="public.example.com",
        cert_type="LetsEncrypt",
        agree_tos=True,
        contact_user_key=1,
    )


def test_cert_create_with_sans(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test creating a certificate with Subject Alternative Names."""
    mock_client.certificates.create.return_value = mock_certificate

    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "create",
            "--domain",
            "example.com",
            "--domains",
            "*.example.com,api.example.com",
        ],
    )

    assert result.exit_code == 0
    mock_client.certificates.create.assert_called_once_with(
        domain="example.com",
        cert_type="SelfSigned",
        domain_list=["*.example.com", "api.example.com"],
    )


def test_cert_create_manual_rejected(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test that creating manual type via create command is rejected."""
    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "create",
            "--domain",
            "example.com",
            "--type",
            "manual",
        ],
    )

    assert result.exit_code == 2
    assert "vrg certificate import" in result.output


def test_cert_import(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock, tmp_path: Any
) -> None:
    """Test importing a manual certificate from PEM files."""
    pub_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    pub_file.write_text("-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----\n")
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n")

    mock_client.certificates.create.return_value = mock_certificate

    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "import",
            "--domain",
            "manual.example.com",
            "--public-key",
            str(pub_file),
            "--private-key",
            str(key_file),
        ],
    )

    assert result.exit_code == 0
    assert "Imported certificate" in result.output
    mock_client.certificates.create.assert_called_once_with(
        domain="manual.example.com",
        cert_type="Manual",
        public_key="-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----\n",
        private_key="-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",
    )


def test_cert_import_file_not_found(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test import with missing PEM file."""
    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "import",
            "--domain",
            "example.com",
            "--public-key",
            "/nonexistent/cert.pem",
            "--private-key",
            "/nonexistent/key.pem",
        ],
    )

    assert result.exit_code != 0


def test_cert_update(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test updating a certificate."""
    mock_client.certificates.get.return_value = mock_certificate
    mock_client.certificates.update.return_value = mock_certificate

    result = cli_runner.invoke(
        app,
        [
            "certificate",
            "update",
            "70",
            "--description",
            "Updated description",
        ],
    )

    assert result.exit_code == 0
    assert "Updated certificate" in result.output
    mock_client.certificates.update.assert_called_once_with(70, description="Updated description")


def test_cert_delete(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test deleting a certificate with --yes."""
    mock_client.certificates.get.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "delete", "70", "--yes"])

    assert result.exit_code == 0
    assert "Deleted certificate" in result.output
    mock_client.certificates.delete.assert_called_once_with(70)


def test_cert_delete_no_confirm(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test deleting a certificate without --yes aborts."""
    mock_client.certificates.get.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "delete", "70"], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.output
    mock_client.certificates.delete.assert_not_called()


def test_cert_renew(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test renewing a certificate."""
    mock_client.certificates.get.return_value = mock_certificate
    mock_client.certificates.renew.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "renew", "70"])

    assert result.exit_code == 0
    assert "Renewed certificate" in result.output
    mock_client.certificates.renew.assert_called_once_with(70, force=False)


def test_cert_renew_force(
    cli_runner: CliRunner, mock_client: MagicMock, mock_certificate: MagicMock
) -> None:
    """Test renewing a certificate with --force."""
    mock_client.certificates.get.return_value = mock_certificate
    mock_client.certificates.renew.return_value = mock_certificate

    result = cli_runner.invoke(app, ["certificate", "renew", "70", "--force"])

    assert result.exit_code == 0
    mock_client.certificates.renew.assert_called_once_with(70, force=True)


def test_cert_not_found(cli_runner: CliRunner, mock_client: MagicMock) -> None:
    """Test domain resolution error (exit 6)."""
    mock_client.certificates.get.side_effect = NotFoundError(
        "Certificate for domain 'nonexistent.com' not found"
    )

    result = cli_runner.invoke(app, ["certificate", "get", "nonexistent.com"])

    assert result.exit_code == 6
