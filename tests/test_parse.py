import math
import subprocess
import sys

import pytest

from mini_humanize import parse_size, naturalsize


def test_basic_decimal_and_binary_units():
    assert parse_size("1 kB") == 1000
    assert parse_size("1KB") == 1000
    assert parse_size("1 KiB") == 1024
    assert parse_size("1MiB") == 1024 * 1024
    assert parse_size("1 MB") == 1000 * 1000


def test_gnu_suffix_ambiguity_and_defaults():
    # Strict + no default_gnu -> ambiguous
    with pytest.raises(ValueError):
        parse_size("1K", strict=True, default_gnu=False)

    # Permissive: default_gnu False but strict False -> uses default_binary
    assert parse_size("1K", strict=False, default_binary=False, default_gnu=False) == 1000
    assert parse_size("1K", strict=False, default_binary=True, default_gnu=False) == 1024

    # default_gnu True resolves ambiguity using default_binary
    assert parse_size("1K", default_gnu=True, default_binary=False) == 1000
    assert parse_size("1K", default_gnu=True, default_binary=True) == 1024


def test_whitespace_and_case_and_fractional_values():
    assert parse_size(" 1.5 KiB ") == 1536
    assert parse_size("2.5 kB") == 2500
    assert parse_size("3.25MB") == 3250000


def test_rounding_modes():
    # 1.5 bytes rounds differently
    assert parse_size("1.5 B", rounding="floor") == 1
    assert parse_size("1.5 B", rounding="nearest") == 2
    assert parse_size("1.5 B", rounding="ceil") == 2


def test_thousands_separator_behavior():
    with pytest.raises(ValueError):
        parse_size("1,234.5 kB", allow_thousands_separator=False)

    assert parse_size("1,234.5 kB", allow_thousands_separator=True) == 1234500
    assert parse_size("1_234.5 kB", allow_thousands_separator=True) == 1234500


def test_invalid_and_edge_cases():
    with pytest.raises(ValueError):
        parse_size("")
    with pytest.raises(ValueError):
        parse_size("abc")
    with pytest.raises(ValueError):
        parse_size("1 XB")
    with pytest.raises(ValueError):
        parse_size("nan kB")
    with pytest.raises(ValueError):
        parse_size("inf K")


def test_negative_policy():
    with pytest.raises(ValueError):
        parse_size("-1 kB", strict=True)
    assert parse_size("-1 kB", strict=False) == -1000


def test_extremely_large_values():
    # should not overflow
    v = parse_size("1000000 PB")
    assert isinstance(v, int)
    assert v > 0


def test_round_trip_consistency():
    # For some sizes, formatting then parsing should be reversible (within rounding)
    x = 1536
    s = naturalsize(x, binary=True, gnu=False, format="%.1f", strip_trailing_zeros=False)
    assert s == "1.5 KiB"
    y = parse_size(s, default_binary=True, default_gnu=False)
    assert y == x
