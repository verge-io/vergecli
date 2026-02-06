"""Tests for template unit parsing."""

import pytest

from verge_cli.template.units import (
    format_disk_size,
    format_ram,
    parse_disk_size,
    parse_ram,
)


class TestParseRam:
    """Tests for RAM parsing (output: MB int)."""

    def test_megabytes(self):
        assert parse_ram("512MB") == 512

    def test_gigabytes(self):
        assert parse_ram("4GB") == 4096

    def test_terabytes(self):
        assert parse_ram("1TB") == 1048576

    def test_passthrough_int(self):
        assert parse_ram(2048) == 2048

    def test_passthrough_int_string(self):
        assert parse_ram("2048") == 2048

    def test_case_insensitive(self):
        assert parse_ram("4gb") == 4096
        assert parse_ram("512mb") == 512

    def test_with_spaces(self):
        assert parse_ram("4 GB") == 4096

    def test_fractional(self):
        assert parse_ram("1.5GB") == 1536

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid size format"):
            parse_ram("4PB")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid"):
            parse_ram("lots")

    def test_zero(self):
        with pytest.raises(ValueError, match="must be positive"):
            parse_ram("0GB")

    def test_negative(self):
        with pytest.raises(ValueError):
            parse_ram("-4GB")


class TestParseDiskSize:
    """Tests for disk size parsing (output: GB int)."""

    def test_megabytes(self):
        assert parse_disk_size("512MB") == 0  # rounds down, < 1GB

    def test_megabytes_large(self):
        assert parse_disk_size("2048MB") == 2

    def test_gigabytes(self):
        assert parse_disk_size("50GB") == 50

    def test_terabytes(self):
        assert parse_disk_size("1TB") == 1024

    def test_passthrough_int(self):
        assert parse_disk_size(50) == 50

    def test_passthrough_int_string(self):
        assert parse_disk_size("50") == 50

    def test_fractional(self):
        assert parse_disk_size("1.5TB") == 1536


class TestFormatRam:
    """Tests for RAM formatting (input: MB, output: human string)."""

    def test_exact_gb(self):
        assert format_ram(4096) == "4GB"

    def test_exact_tb(self):
        assert format_ram(1048576) == "1TB"

    def test_sub_gb(self):
        assert format_ram(512) == "512MB"

    def test_non_exact_gb(self):
        assert format_ram(1536) == "1536MB"

    def test_large_exact_gb(self):
        assert format_ram(32768) == "32GB"


class TestFormatDiskSize:
    """Tests for disk size formatting (input: GB, output: human string)."""

    def test_exact_gb(self):
        assert format_disk_size(50) == "50GB"

    def test_exact_tb(self):
        assert format_disk_size(1024) == "1TB"

    def test_sub_tb(self):
        assert format_disk_size(500) == "500GB"

    def test_large_exact_tb(self):
        assert format_disk_size(2048) == "2TB"
