import math
import subprocess
import sys

import pytest

from mini_humanize import naturalsize, parse_size


def test_naturalsize_backward_compatibility():
    # Regression-protection: lock in a few canonical outputs when
    # strip_trailing_zeros=False (default behavior)
    assert naturalsize(1500) == "1.5 kB"
    assert naturalsize(1536, binary=True) == "1.5 KiB"
    assert naturalsize(1000, gnu=True) == "1.0K"
    assert naturalsize(-1536, binary=True) == "-1.5 KiB"


def test_parse_decimal_and_binary_units():
    assert parse_size("1.5 kB") == 1500
    assert parse_size("1.5 kB", strict=True) == 1500
    assert parse_size("1.5 KiB") == 1536
    assert parse_size("2MB") == 2_000_000
    assert parse_size("2MiB") == 2 * 1024 * 1024


def test_gnu_single_letter_and_ambiguity():
    # Single-letter GNU suffix is ambiguous. In strict mode it is only
    # accepted if default_gnu=True.
    with pytest.raises(ValueError):
        parse_size("2K", strict=True, default_gnu=False)

    # When default_gnu=True it is accepted and interpretation follows
    # default_binary.
    assert parse_size("2K", default_gnu=True, default_binary=False) == 2000
    assert parse_size("2K", default_gnu=True, default_binary=True) == 2048

    # Permissive parsing accepts single-letter GNU even if default_gnu=False
    assert parse_size("2K", strict=False, default_gnu=False, default_binary=False) == 2000


def test_whitespace_and_case():
    assert parse_size(" 1.5 kB ") == 1500
    assert parse_size("1.5KB") == 1500
    assert parse_size("1.5 kib") == 1536


def test_fractional_rounding_modes():
    # 1.5 bytes -> nearest=2, floor=1, ceil=2
    assert parse_size("1.5 B", rounding="nearest") == 2
    assert parse_size("1.5 B", rounding="floor") == 1
    assert parse_size("1.5 B", rounding="ceil") == 2


def test_thousands_separators():
    assert parse_size("1,234.5 kB", allow_thousands_separator=True) == 1_234_500
    with pytest.raises(ValueError):
        parse_size("1,234.5 kB", allow_thousands_separator=False)
    # invalid placement
    with pytest.raises(ValueError):
        parse_size("12,34 kB", allow_thousands_separator=True)


def test_invalid_and_special_values():
    with pytest.raises(ValueError):
        parse_size("")
    with pytest.raises(ValueError):
        parse_size("not-a-number")
    with pytest.raises(ValueError):
        parse_size("1 QB")
    with pytest.raises(ValueError):
        parse_size("nan B")
    with pytest.raises(ValueError):
        parse_size("inf B")


def test_negative_policy():
    with pytest.raises(ValueError):
        parse_size("-1 kB", strict=True)
    assert parse_size("-1 kB", strict=False) == -1000


def test_extremely_large_values():
    # Very large but supported (Python ints are unbounded)
    val = parse_size("1P", default_gnu=True, default_binary=False)
    assert val == 1000 ** 5


def test_round_trip_consistency():
    # Choose values that format with one decimal digit and parse back exactly
    examples = [1500, 1536, 2_000_000, 2 * 1024 * 1024]
    for n in examples:
        # For each value pick matching flags so formatting is unambiguous
        if n in (1536, 2 * 1024 * 1024):
            s = naturalsize(n, binary=True, format="%.1f", strip_trailing_zeros=False)
            parsed = parse_size(s, default_binary=True, default_gnu=False, rounding="nearest", strict=False)
        else:
            s = naturalsize(n, binary=False, format="%.1f", strip_trailing_zeros=False)
            parsed = parse_size(s, default_binary=False, default_gnu=False, rounding="nearest", strict=False)
        assert parsed == n


def test_cli_format_and_parse():
    py = sys.executable

    # format: basic
    p = subprocess.run([py, "-m", "mini_humanize", "format", "1500"], capture_output=True, text=True)
    assert p.returncode == 0
    assert p.stdout.strip() == "1.5 kB"

    # format: binary
    p = subprocess.run([py, "-m", "mini_humanize", "format", "1536", "--binary"], capture_output=True, text=True)
    assert p.returncode == 0
    assert p.stdout.strip() == "1.5 KiB"

    # parse: simple (note: provide the entire text as a single argument)
    p = subprocess.run([py, "-m", "mini_humanize", "parse", "1.5 kB"], capture_output=True, text=True)
    assert p.returncode == 0
    assert p.stdout.strip() == "1500"

    # parse: GNU + default-binary
    p = subprocess.run([py, "-m", "mini_humanize", "parse", "2K", "--default-gnu", "--default-binary"], capture_output=True, text=True)
    assert p.returncode == 0
    assert p.stdout.strip() == "2048"
