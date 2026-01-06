import pytest
import subprocess
import sys
from mini_humanize import naturalsize, parse_size


class TestNaturalSize:
    def test_basic_decimal(self):
        assert naturalsize(1000) == "1.0 kB"
        assert naturalsize(1000000) == "1.0 MB"

    def test_basic_binary(self):
        assert naturalsize(1024, binary=True) == "1.0 KiB"
        assert naturalsize(1024**2, binary=True) == "1.0 MiB"

    def test_gnu_decimal(self):
        assert naturalsize(1000, gnu=True) == "1.0K"
        assert naturalsize(1000000, gnu=True) == "1.0M"

    def test_gnu_binary(self):
        assert naturalsize(1024, binary=True, gnu=True) == "1.0K"
        assert naturalsize(1024**2, binary=True, gnu=True) == "1.0M"

    def test_strip_trailing_zeros(self):
        assert naturalsize(1000, strip_trailing_zeros=True) == "1 kB"
        assert naturalsize(1024, binary=True, strip_trailing_zeros=True) == "1 KiB"

    def test_negative(self):
        assert naturalsize(-1000) == "-1.0 kB"

    def test_string_input(self):
        assert naturalsize("1000") == "1.0 kB"

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            naturalsize("abc")
        with pytest.raises(TypeError):
            naturalsize([])

    def test_regression_strip_false(self):
        # Lock in specific outputs for backward compatibility
        assert naturalsize(512) == "512.0 B"
        assert naturalsize(1024) == "1.0 kB"
        assert naturalsize(1500) == "1.5 kB"
        assert naturalsize(1024, binary=True) == "1.0 KiB"
        assert naturalsize(1024, gnu=True) == "1.0K"
        assert naturalsize(1024, binary=True, gnu=True) == "1.0K"


class TestParseSize:
    def test_basic_bytes(self):
        assert parse_size("100") == 100
        assert parse_size("100 B") == 100
        assert parse_size("100b") == 100

    def test_decimal_units(self):
        assert parse_size("1 kB") == 1000
        assert parse_size("1 MB") == 1000000
        assert parse_size("1.5 kB") == 1500

    def test_binary_units(self):
        assert parse_size("1 KiB") == 1024
        assert parse_size("1 MiB") == 1024**2

    def test_gnu_units_with_default_gnu(self):
        assert parse_size("1K", default_gnu=True) == 1000
        assert parse_size("1M", default_gnu=True) == 1000000
        assert parse_size("1K", default_gnu=True, default_binary=True) == 1024
        assert parse_size("1M", default_gnu=True, default_binary=True) == 1024**2

    def test_whitespace_and_case(self):
        assert parse_size("  1  KB  ") == 1000
        assert parse_size("1 kib") == 1024

    def test_fractional(self):
        assert parse_size("1.5 kB") == 1500
        assert parse_size("0.5 KiB") == 512

    def test_negative(self):
        assert parse_size("-100") == -100
        assert parse_size("-1 kB") == -1000

    def test_thousands_separator(self):
        assert parse_size("1,000", allow_thousands_separator=True) == 1000
        assert parse_size("1,000 kB", allow_thousands_separator=True) == 1000000
        with pytest.raises(ValueError):
            parse_size("1,000", allow_thousands_separator=False)

    def test_rounding(self):
        assert parse_size("1.4 B", rounding="floor") == 1
        assert parse_size("1.4 B", rounding="nearest") == 1
        assert parse_size("1.6 B", rounding="nearest") == 2
        assert parse_size("1.1 B", rounding="ceil") == 2

    def test_strict_unknown_unit(self):
        with pytest.raises(ValueError):
            parse_size("1 XYZ", strict=True)
        assert parse_size("1 XYZ", strict=False) == 1  # assume bytes

    def test_strict_gnu_without_default_gnu(self):
        with pytest.raises(ValueError):
            parse_size("1K", default_gnu=False, strict=True)
        assert parse_size("1K", default_gnu=False, strict=False) == 1

    def test_empty_string(self):
        with pytest.raises(ValueError):
            parse_size("")

    def test_invalid_string(self):
        with pytest.raises(ValueError):
            parse_size("abc")
        with pytest.raises(ValueError):
            parse_size("1.2.3 kB")

    def test_nan_inf(self):
        with pytest.raises(ValueError):
            parse_size("inf")
        with pytest.raises(ValueError):
            parse_size("nan")

    def test_large_values(self):
        # Python handles large floats
        assert parse_size("1 PB") == 1000**5
        assert parse_size("1 PiB") == 1024**5


class TestConsistency:
    def test_round_trip_decimal(self):
        # For integer bytes, should round trip exactly
        for val in [0, 1, 1000, 1000000, 1000**5]:
            formatted = naturalsize(val)
            parsed = parse_size(formatted)
            assert parsed == val

    def test_round_trip_binary(self):
        for val in [0, 1024, 1024**2, 1024**5]:
            formatted = naturalsize(val, binary=True)
            parsed = parse_size(formatted)
            assert parsed == val

    def test_round_trip_gnu(self):
        for val in [1000, 1000000]:
            formatted = naturalsize(val, gnu=True)
            parsed = parse_size(formatted, default_gnu=True)
            assert parsed == val

    def test_tolerance_round_trip(self):
        # For values that lose precision in formatting
        val = 1500
        formatted = naturalsize(val)  # "1.5 kB"
        parsed = parse_size(formatted)
        assert parsed == 1500


class TestCLI:
    def run_cli(self, args):
        result = subprocess.run(
            [sys.executable, "-m", "mini_humanize"] + args,
            capture_output=True,
            text=True,
            cwd="c:\\Bug_Bash\\26_01_06\\1\\grok-fast"
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def test_format_basic(self):
        code, out, err = self.run_cli(["format", "1000"])
        assert code == 0
        assert out == "1.0 kB"

    def test_format_binary(self):
        code, out, err = self.run_cli(["format", "1024", "--binary"])
        assert code == 0
        assert out == "1.0 KiB"

    def test_parse_basic(self):
        code, out, err = self.run_cli(["parse", "1 kB"])
        assert code == 0
        assert out == "1000"

    def test_parse_gnu(self):
        code, out, err = self.run_cli(["parse", "1K", "--default-gnu"])
        assert code == 0
        assert out == "1000"

    def test_parse_strict_error(self):
        code, out, err = self.run_cli(["parse", "1K", "--strict"])
        assert code != 0
        assert "Unknown or ambiguous unit" in err