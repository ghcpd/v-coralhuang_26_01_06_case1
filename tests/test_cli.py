"""Tests for CLI functionality."""

import subprocess
import sys
import pytest


def run_cli(args):
    """Helper to run CLI command."""
    result = subprocess.run(
        [sys.executable, "-m", "mini_humanize"] + args,
        capture_output=True,
        text=True,
    )
    return result


class TestCLIFormat:
    """Test format subcommand."""

    def test_format_basic_decimal(self):
        """Test basic format command with decimal."""
        result = run_cli(["format", "1000"])
        assert result.returncode == 0
        assert "1.0 kB" in result.stdout

    def test_format_basic_binary(self):
        """Test format command with binary flag."""
        result = run_cli(["format", "1024", "--binary"])
        assert result.returncode == 0
        assert "1.0 KiB" in result.stdout

    def test_format_with_gnu(self):
        """Test format with GNU style."""
        result = run_cli(["format", "1000", "--gnu"])
        assert result.returncode == 0
        assert "1.0K" in result.stdout

    def test_format_with_gnu_binary(self):
        """Test format with GNU and binary."""
        result = run_cli(["format", "1024", "--gnu", "--binary"])
        assert result.returncode == 0
        assert "1.0K" in result.stdout

    def test_format_with_custom_format(self):
        """Test format with custom format string."""
        result = run_cli(["format", "1000", "--format", "%.0f"])
        assert result.returncode == 0
        # Output should be 1 kB or similar

    def test_format_with_strip_trailing_zeros(self):
        """Test format with strip trailing zeros."""
        result = run_cli(["format", "1000", "--strip-trailing-zeros"])
        assert result.returncode == 0
        assert "1 kB" in result.stdout

    def test_format_large_value(self):
        """Test format with large value."""
        result = run_cli(["format", "1000000000"])
        assert result.returncode == 0
        assert "1.0 GB" in result.stdout


class TestCLIParse:
    """Test parse subcommand."""

    def test_parse_simple_bytes(self):
        """Test parsing simple bytes."""
        result = run_cli(["parse", "1000"])
        assert result.returncode == 0
        assert "1000" in result.stdout

    def test_parse_kilobytes(self):
        """Test parsing kilobytes."""
        result = run_cli(["parse", "1KB"])
        assert result.returncode == 0
        assert "1000" in result.stdout

    def test_parse_with_default_gnu(self):
        """Test parsing with default-gnu flag."""
        result = run_cli(["parse", "1K", "--default-gnu"])
        assert result.returncode == 0
        assert "1000" in result.stdout

    def test_parse_binary_unit(self):
        """Test parsing binary unit."""
        result = run_cli(["parse", "1KiB"])
        assert result.returncode == 0
        assert "1024" in result.stdout

    def test_parse_with_thousands_separator(self):
        """Test parsing with thousands separator allowed."""
        result = run_cli(["parse", "1,000B", "--allow-thousands-separator"])
        assert result.returncode == 0
        assert "1000" in result.stdout

    def test_parse_rounding_floor(self):
        """Test parse with floor rounding."""
        result = run_cli(["parse", "1.9B", "--rounding", "floor"])
        assert result.returncode == 0
        assert "1" in result.stdout

    def test_parse_rounding_ceil(self):
        """Test parse with ceil rounding."""
        result = run_cli(["parse", "1.1B", "--rounding", "ceil"])
        assert result.returncode == 0
        assert "2" in result.stdout

    def test_parse_permissive_mode(self):
        """Test parse in permissive mode."""
        result = run_cli(["parse", "1K", "--default-gnu", "--permissive"])
        assert result.returncode == 0
        assert "1000" in result.stdout

    def test_parse_with_binary_default(self):
        """Test parse with default-binary."""
        result = run_cli(["parse", "1K", "--default-gnu", "--default-binary"])
        assert result.returncode == 0
        assert "1024" in result.stdout


class TestCLIErrors:
    """Test error handling in CLI."""

    def test_invalid_subcommand(self):
        """Test invalid subcommand."""
        result = run_cli(["invalid"])
        assert result.returncode != 0

    def test_format_invalid_input(self):
        """Test format with invalid input."""
        result = run_cli(["format", "abc"])
        assert result.returncode != 0

    def test_parse_invalid_input(self):
        """Test parse with invalid input."""
        result = run_cli(["parse", "xyz"])
        assert result.returncode != 0

    def test_parse_unknown_unit(self):
        """Test parse with unknown unit."""
        result = run_cli(["parse", "1ZB"])
        assert result.returncode != 0
