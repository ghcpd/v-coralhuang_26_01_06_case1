import math
import subprocess
import sys
from mini_humanize import parse_size, naturalsize


def test_parse_decimal_and_binary_units():
    assert parse_size("1 kB") == 1000
    assert parse_size("1 KiB") == 1024
    assert parse_size("1MB") == 1_000_000
    assert parse_size("1MiB") == 1024 * 1024


def test_parse_whitespace_and_case_and_fractional():
    assert parse_size("  1.5   kB ") == 1500
    assert parse_size("2.25 KiB") == int(round(2.25 * 1024))
    assert parse_size("1.5 kb") == 1500


def test_gnu_single_letter_and_defaults():
    # single-letter rejected by default in strict mode
    try:
        parse_size("1K", strict=True)
        raise AssertionError("expected ValueError for ambiguous single-letter unit in strict mode")
    except ValueError:
        pass

    # accepted when default_gnu is set
    assert parse_size("1K", default_gnu=True) == 1000
    assert parse_size("1K", default_gnu=True, default_binary=True) == 1024

    # permissive mode accepts single-letter and uses default_binary
    assert parse_size("1K", strict=False, default_binary=False) == 1000


def test_allow_and_reject_thousands_separators():
    assert parse_size("1,234 kB", allow_thousands_separator=True) == 1_234_000
    assert parse_size("1_234 kB", allow_thousands_separator=True) == 1_234_000
    try:
        parse_size("1,234")
        raise AssertionError("expected thousands separators to be rejected by default")
    except ValueError:
        pass


def test_rounding_modes_and_fractional_bytes():
    assert parse_size("1.5 B", rounding="nearest") == 2
    assert parse_size("1.5 B", rounding="floor") == 1
    assert parse_size("1.5 B", rounding="ceil") == 2

    # fractional KB -> rounding applies after multiplication
    assert parse_size("1.2345 KiB", rounding="floor") == math.floor(1.2345 * 1024)


def test_empty_nan_inf_and_unknown_unit():
    for bad in ["", "   "]:
        try:
            parse_size(bad)
            raise AssertionError("expected empty string to raise")
        except ValueError:
            pass

    for bad in ["nan", "inf", "-inf"]:
        try:
            parse_size(bad)
            raise AssertionError("expected NaN/inf to raise")
        except ValueError:
            pass

    try:
        parse_size("1 QB")
        raise AssertionError("expected unknown unit to raise")
    except ValueError:
        pass


def test_negative_policy():
    try:
        parse_size("-1 kB", strict=True)
        raise AssertionError("expected negative to be rejected in strict mode")
    except ValueError:
        pass

    assert parse_size("-1 kB", strict=False) == -1000


def test_extremely_large_value():
    big = "123456789012345678901234567890"
    assert parse_size(big) == int(big)


def test_roundtrip_consistency():
    # round-trip: parsing a formatted string should recover the original value
    # within the precision implied by the formatted output.
    for x in (0, 1, 512, 1023, 1024, 1536, 10_000, 123_456):
        s = naturalsize(x, binary=True, format="%.1f", strip_trailing_zeros=False)
        y = parse_size(s, default_binary=True, default_gnu=False, rounding="nearest")

        # derive tolerance from the formatted precision: half of the least-significant
        # digit expressed in bytes (e.g. "%.1f" => 0.1 * unit_bytes / 2)
        if "." in s:
            frac_digits = len(s.split(".")[-1].lstrip("0123456789"))
        # simpler: for the controlled format "%.1f" used above, allow a tolerance
        # derived from one decimal place at the unit scale
        unit = s.strip().split()[-1] if " " in s else "".join(ch for ch in s if ch.isalpha())
        unit_map = {"KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3, "B": 1}
        unit_bytes = unit_map.get(unit, 1)
        tol = max(1, int(0.5 * unit_bytes * 10 ** -1))
        assert abs(y - x) <= tol


def test_precision_preserved_for_integer_literals():
    # integer literal without decimal point should preserve exactness
    assert parse_size("9007199254740993") == 9007199254740993
