"""Tests for parse_size function."""

import math
import pytest

from mini_humanize import parse_size


class TestParseNormalPaths:
    """Test normal, happy-path parsing scenarios."""

    # Decimal units without space
    def test_decimal_units_no_space(self):
        assert parse_size("1000B") == 1000
        assert parse_size("1KB") == 1000
        assert parse_size("1MB") == 1_000_000
        assert parse_size("1GB") == 1_000_000_000
        assert parse_size("1TB") == 1_000_000_000_000
        assert parse_size("1PB") == 1_000_000_000_000_000

    # Decimal units with space
    def test_decimal_units_with_space(self):
        assert parse_size("1 KB") == 1000
        assert parse_size("2 MB") == 2_000_000
        assert parse_size("3 GB") == 3_000_000_000

    # Binary units (KiB, MiB, etc.)
    def test_binary_units(self):
        assert parse_size("1KiB") == 1024
        assert parse_size("1 KiB") == 1024
        assert parse_size("1MiB") == 1024 ** 2
        assert parse_size("1GiB") == 1024 ** 3
        assert parse_size("1TiB") == 1024 ** 4
        assert parse_size("1PiB") == 1024 ** 5

    # Lowercase units
    def test_lowercase_units(self):
        assert parse_size("1kb") == 1000
        assert parse_size("1kib") == 1024
        assert parse_size("1mb") == 1_000_000

    # Mixed case
    def test_mixed_case(self):
        assert parse_size("1Kb") == 1000
        assert parse_size("1kB") == 1000
        assert parse_size("1KIB") == 1024
        assert parse_size("1Kib") == 1024

    # Fractional values (decimal)
    def test_fractional_values(self):
        assert parse_size("1.5KB") == 1500
        assert parse_size("2.5MB") == 2_500_000
        assert parse_size("0.5GB") == 500_000_000

    # Fractional values with rounding (nearest)
    def test_fractional_rounding_nearest(self):
        result = parse_size("1.5B", rounding="nearest")
        assert result == 2  # round(1.5) = 2

        result = parse_size("2.4B", rounding="nearest")
        assert result == 2

        result = parse_size("2.5B", rounding="nearest")
        assert result == 2  # Python banker's rounding

        result = parse_size("2.6B", rounding="nearest")
        assert result == 3

    def test_fractional_rounding_floor(self):
        result = parse_size("1.9B", rounding="floor")
        assert result == 1

        result = parse_size("2.5B", rounding="floor")
        assert result == 2

    def test_fractional_rounding_ceil(self):
        result = parse_size("1.1B", rounding="ceil")
        assert result == 2

        result = parse_size("2.5B", rounding="ceil")
        assert result == 3

    # GNU-style units with default_gnu
    def test_gnu_default_gnu_true(self):
        result = parse_size("1K", default_gnu=True)
        assert result == 1000  # Decimal by default

        result = parse_size("1K", default_gnu=True, default_binary=True)
        assert result == 1024  # Binary when default_binary=True

    # No unit (bytes)
    def test_no_unit(self):
        assert parse_size("42") == 42
        assert parse_size("0") == 0
        assert parse_size("1000") == 1000

    # Whitespace handling
    def test_whitespace_handling(self):
        assert parse_size("  1000  ") == 1000
        assert parse_size("  1 KB  ") == 1000
        assert parse_size("1   KB") == 1000
        assert parse_size("1KB   ") == 1000

    # Multiple spaces between number and unit
    def test_multiple_spaces(self):
        assert parse_size("1  MB") == 1_000_000
        assert parse_size("1   GB") == 1_000_000_000


class TestParseEdgeCases:
    """Test edge cases and error handling."""

    # Invalid strings
    def test_invalid_strings(self):
        with pytest.raises(ValueError):
            parse_size("abc")

        with pytest.raises(ValueError):
            parse_size("1 1 MB")

        with pytest.raises(ValueError):
            parse_size("MB")

    # Unknown units
    def test_unknown_units(self):
        with pytest.raises(ValueError, match="Unknown unit"):
            parse_size("1ZB")

        with pytest.raises(ValueError, match="Unknown unit"):
            parse_size("1XYZ")

    # Empty string
    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_size("")

        with pytest.raises(ValueError):
            parse_size("   ")

    # NaN and infinity
    def test_nan_and_inf(self):
        with pytest.raises(ValueError):
            parse_size("nan")

        with pytest.raises(ValueError):
            parse_size("inf")

    # Negative values
    def test_negative_values(self):
        with pytest.raises(ValueError):
            parse_size("-1GB")

        with pytest.raises(ValueError):
            parse_size("-100")

    # Very large values
    def test_very_large_values(self):
        # Should work for reasonable values
        result = parse_size("1000TB")
        assert result > 0

        # But overflow should be caught at some point
        with pytest.raises(OverflowError):
            parse_size("9999999999999999PB")

    # Non-string input
    def test_non_string_input(self):
        with pytest.raises(ValueError):
            parse_size(None)

        with pytest.raises(ValueError):
            parse_size(123)

    # Thousands separators - when allowed
    def test_thousands_separator_allowed(self):
        result = parse_size("1,000B", allow_thousands_separator=True)
        assert result == 1000

        result = parse_size("1,000,000B", allow_thousands_separator=True)
        assert result == 1_000_000

        result = parse_size("1_000B", allow_thousands_separator=True)
        assert result == 1000

    # Thousands separators - when not allowed
    def test_thousands_separator_not_allowed(self):
        # Comma is treated as decimal separator: "1,000" -> "1.000" -> 1
        # This parses but gives a different result than intended
        result = parse_size("1,000B", allow_thousands_separator=False)
        assert result == 1  # Because 1,000 -> 1.000 -> 1

        # Underscore in number is invalid
        with pytest.raises(ValueError):
            parse_size("1_000B", allow_thousands_separator=False)

    # Ambiguous units in strict mode
    def test_ambiguous_units_strict(self):
        with pytest.raises(ValueError, match="Ambiguous unit"):
            parse_size("1K", strict=True, default_gnu=False)

        with pytest.raises(ValueError, match="Ambiguous unit"):
            parse_size("1M", strict=True, default_gnu=False)

    # Ambiguous units in permissive mode
    def test_ambiguous_units_permissive(self):
        # Should not raise with default_gnu=True
        result = parse_size("1K", strict=False, default_gnu=True)
        assert result == 1000

        # Should not raise with default_binary=True
        result = parse_size("1K", strict=False, default_binary=True, default_gnu=True)
        assert result == 1024

    # Zero
    def test_zero(self):
        assert parse_size("0") == 0
        assert parse_size("0B") == 0
        assert parse_size("0KB") == 0

    # Fractional less than 1 byte
    def test_fractional_less_than_one_byte(self):
        result = parse_size("0.5B", rounding="ceil")
        assert result == 1

        result = parse_size("0.5B", rounding="floor")
        assert result == 0

        result = parse_size("0.5B", rounding="nearest")
        assert result == 0


class TestParseStrictVsPermissive:
    """Test strict mode vs permissive mode behavior."""

    def test_strict_mode_rejects_ambiguities(self):
        # GNU-style single letters are ambiguous without explicit default_gnu
        with pytest.raises(ValueError):
            parse_size("1K", strict=True, default_gnu=False)

    def test_permissive_mode_accepts_with_defaults(self):
        # Permissive mode should accept GNU units when default_gnu=True
        result = parse_size("1K", strict=False, default_gnu=True)
        assert result == 1000

    def test_strict_mode_with_explicit_units(self):
        # Explicit units should work even in strict mode
        assert parse_size("1KB", strict=True) == 1000
        assert parse_size("1KiB", strict=True) == 1024


class TestParseConsistency:
    """Test consistency properties and round-trip behavior."""

    def test_roundtrip_decimal_no_loss(self):
        """Test that formatting then parsing preserves value (no fractional loss)."""
        from mini_humanize import naturalsize

        # Test with integer bytes
        original = 1_500_000  # 1.5 MB
        formatted = naturalsize(original, binary=False)
        # formatted = "1.5 MB"
        parsed = parse_size(formatted, default_gnu=False)
        assert abs(parsed - original) <= 1  # Allow 1 byte tolerance for rounding

    def test_roundtrip_binary_no_loss(self):
        """Test binary roundtrip."""
        from mini_humanize import naturalsize

        original = 1536  # 1.5 KiB
        formatted = naturalsize(original, binary=True)
        # formatted = "1.5 KiB"
        parsed = parse_size(formatted, default_gnu=False)
        assert abs(parsed - original) <= 1

    def test_roundtrip_gnu_decimal(self):
        """Test GNU-style decimal roundtrip."""
        from mini_humanize import naturalsize

        original = 1_500_000  # 1.5 M in decimal
        formatted = naturalsize(original, gnu=True, binary=False)
        # formatted = "1.5M"
        parsed = parse_size(formatted, default_gnu=True)
        assert abs(parsed - original) <= 1

    def test_roundtrip_gnu_binary(self):
        """Test GNU-style binary roundtrip."""
        from mini_humanize import naturalsize

        original = 1536  # 1.5 K in binary
        formatted = naturalsize(original, gnu=True, binary=True)
        # formatted = "1.5K"
        parsed = parse_size(formatted, default_gnu=True, default_binary=True)
        assert abs(parsed - original) <= 1


class TestParseSpecialCases:
    """Test special formatting cases."""

    def test_comma_as_decimal_separator(self):
        """Test handling of comma in number (European format)."""
        # Allow thousands separators should handle both
        result = parse_size("1,5KB", allow_thousands_separator=True)
        # This should fail because comma is treated as thousands separator
        # 1,5 -> "15" -> 15KB = 15000
        assert result == 15000

    def test_decimal_point_in_number(self):
        """Test decimal point parsing."""
        assert parse_size("1.5KB") == 1500
        assert parse_size("0.5GB") == 500_000_000

    def test_capital_b_unit(self):
        """Test capital B as bytes unit."""
        assert parse_size("1000B") == 1000

    def test_lowercase_b_unit(self):
        """Test lowercase b as bytes unit."""
        assert parse_size("1000b") == 1000

    def test_really_small_values(self):
        """Test values less than 1 byte."""
        result = parse_size("0.1B", rounding="nearest")
        assert result == 0

        result = parse_size("0.9B", rounding="nearest")
        assert result == 1
