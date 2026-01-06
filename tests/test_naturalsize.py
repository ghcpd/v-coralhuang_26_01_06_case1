"""Tests for naturalsize function."""

import pytest

from mini_humanize import naturalsize


class TestNaturalizeBasic:
    """Test basic naturalsize functionality."""

    def test_bytes_decimal(self):
        assert naturalsize(0) == "0.0 B"
        assert naturalsize(1) == "1.0 B"
        assert naturalsize(512) == "512.0 B"

    def test_kilobytes_decimal(self):
        assert naturalsize(1000) == "1.0 kB"
        assert naturalsize(1500) == "1.5 kB"
        assert naturalsize(2000) == "2.0 kB"

    def test_megabytes_decimal(self):
        assert naturalsize(1_000_000) == "1.0 MB"
        assert naturalsize(1_500_000) == "1.5 MB"

    def test_gigabytes_decimal(self):
        assert naturalsize(1_000_000_000) == "1.0 GB"
        assert naturalsize(2_500_000_000) == "2.5 GB"

    def test_terabytes_decimal(self):
        assert naturalsize(1_000_000_000_000) == "1.0 TB"

    def test_petabytes_decimal(self):
        assert naturalsize(1_000_000_000_000_000) == "1.0 PB"

    def test_binary_kibibytes(self):
        assert naturalsize(1024, binary=True) == "1.0 KiB"
        assert naturalsize(1536, binary=True) == "1.5 KiB"

    def test_binary_mebibytes(self):
        assert naturalsize(1024 ** 2, binary=True) == "1.0 MiB"
        assert naturalsize(1536 * 1024, binary=True) == "1.5 MiB"

    def test_binary_gibibytes(self):
        assert naturalsize(1024 ** 3, binary=True) == "1.0 GiB"

    def test_binary_tebibytes(self):
        assert naturalsize(1024 ** 4, binary=True) == "1.0 TiB"

    def test_binary_pebibytes(self):
        assert naturalsize(1024 ** 5, binary=True) == "1.0 PiB"


class TestNaturalizeGNU:
    """Test GNU-style output."""

    def test_gnu_decimal(self):
        assert naturalsize(1000, gnu=True) == "1.0K"
        assert naturalsize(1500, gnu=True) == "1.5K"
        assert naturalsize(1_000_000, gnu=True) == "1.0M"

    def test_gnu_binary(self):
        assert naturalsize(1024, gnu=True, binary=True) == "1.0K"
        assert naturalsize(1536, gnu=True, binary=True) == "1.5K"
        assert naturalsize(1024 ** 2, gnu=True, binary=True) == "1.0M"

    def test_gnu_no_space(self):
        """GNU output should have no space between number and unit."""
        result = naturalsize(1_000_000, gnu=True)
        assert " " not in result
        assert result == "1.0M"


class TestNaturalizeFormatting:
    """Test formatting options."""

    def test_custom_format_string(self):
        result = naturalsize(1500, format="%.0f")
        assert result == "1 kB" or result == "2 kB"  # Depends on rounding

        result = naturalsize(1500, format="%.2f")
        assert result == "1.50 kB"

    def test_strip_trailing_zeros_false(self):
        """Default behavior: keep trailing zeros."""
        assert naturalsize(1000, format="%.1f", strip_trailing_zeros=False) == "1.0 kB"
        assert naturalsize(1024, binary=True, format="%.1f", strip_trailing_zeros=False) == "1.0 KiB"

    def test_strip_trailing_zeros_true(self):
        """Strip trailing zeros when enabled."""
        result = naturalsize(1000, format="%.1f", strip_trailing_zeros=True)
        assert result == "1 kB"

        result = naturalsize(1024, binary=True, format="%.1f", strip_trailing_zeros=True)
        assert result == "1 KiB"

    def test_strip_trailing_zeros_with_decimals(self):
        """Keep decimals when they're needed."""
        result = naturalsize(1500, format="%.1f", strip_trailing_zeros=True)
        assert result == "1.5 kB"

    def test_strip_trailing_zeros_multiple_decimal_places(self):
        """Strip zeros from multiple decimal places."""
        result = naturalsize(1100, format="%.2f", strip_trailing_zeros=True)
        assert result == "1.1 kB"

        result = naturalsize(1010, format="%.2f", strip_trailing_zeros=True)
        assert result == "1.01 kB"


class TestNaturalizeInputTypes:
    """Test different input types."""

    def test_int_input(self):
        assert naturalsize(1024) == "1.0 kB"

    def test_float_input(self):
        assert naturalsize(1024.5) == "1.0 kB"

    def test_string_numeric_input(self):
        assert naturalsize("1024") == "1.0 kB"

    def test_string_numeric_float_input(self):
        assert naturalsize("1024.5") == "1.0 kB"

    def test_invalid_string_input(self):
        with pytest.raises(ValueError):
            naturalsize("abc")

    def test_invalid_type(self):
        with pytest.raises(TypeError):
            naturalsize([1024])


class TestNaturalizeNegativeValues:
    """Test handling of negative values."""

    def test_negative_small_value(self):
        result = naturalsize(-512)
        assert result.startswith("-")
        assert "512.0 B" in result

    def test_negative_large_value(self):
        result = naturalsize(-1_000_000)
        assert result.startswith("-")
        assert "1.0 MB" in result

    def test_negative_with_strip_trailing_zeros(self):
        result = naturalsize(-1000, strip_trailing_zeros=True)
        assert result == "-1 kB"


class TestNaturalizeBackwardCompatibility:
    """Test backward compatibility - ensure default behavior is preserved."""

    def test_default_parameters_decimal_non_gnu(self):
        """Default should use decimal (base 1000), non-GNU (with spaces)."""
        # 1000 B -> 1.0 kB
        assert naturalsize(1000) == "1.0 kB"

        # 1024 B -> 1.024 kB (decimal, not binary)
        result = naturalsize(1024)
        assert "1.0 kB" in result or "1.024 kB" in result

    def test_default_format_is_percent_point_1f(self):
        """Default format should be %.1f."""
        # This should produce one decimal place
        assert naturalsize(1234) == "1.2 kB"

    def test_space_in_non_gnu_mode(self):
        """Non-GNU mode should have space between number and unit."""
        result = naturalsize(1000)
        assert " " in result
        assert result == "1.0 kB"

    def test_no_space_in_gnu_mode(self):
        """GNU mode should have no space between number and unit."""
        result = naturalsize(1000, gnu=True)
        assert " " not in result
        assert result == "1.0K"


class TestNaturalizeEdgeCases:
    """Test edge cases."""

    def test_zero(self):
        assert naturalsize(0) == "0.0 B"

    def test_very_large_value(self):
        result = naturalsize(1_000_000_000_000_000)
        assert "1.0 PB" in result

    def test_very_small_fractional_value(self):
        result = naturalsize(0.5)
        assert "0.5 B" in result or "0 B" in result


class TestNaturalizeRegressions:
    """Test specific regression cases to ensure no breaking changes."""

    def test_regression_1000_bytes_non_binary(self):
        """1000 bytes should be exactly 1.0 kB in decimal mode."""
        assert naturalsize(1000, binary=False) == "1.0 kB"

    def test_regression_1024_bytes_binary(self):
        """1024 bytes should be exactly 1.0 KiB in binary mode."""
        assert naturalsize(1024, binary=True) == "1.0 KiB"

    def test_regression_1000_bytes_gnu_decimal(self):
        """1000 bytes in GNU decimal should be 1.0K with no space."""
        assert naturalsize(1000, gnu=True, binary=False) == "1.0K"

    def test_regression_1024_bytes_gnu_binary(self):
        """1024 bytes in GNU binary should be 1.0K with no space."""
        assert naturalsize(1024, gnu=True, binary=True) == "1.0K"

    def test_regression_strip_trailing_zeros_with_format(self):
        """Test that strip_trailing_zeros works with custom format."""
        result = naturalsize(1000, format="%.2f", strip_trailing_zeros=True)
        # 1000 bytes = 1.00 kB -> "1 kB"
        assert result == "1 kB"
