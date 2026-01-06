import math
import subprocess
import sys

from mini_humanize import parse_size, naturalsize


def test_decimal_units_basic():
    assert parse_size("1 kB") == 1000
    assert parse_size("1MB") == 1_000_000
    assert parse_size("1.5 kB", rounding="nearest") == 1500


def test_binary_units_basic():
    assert parse_size("1 KiB") == 1024
    assert parse_size("1MiB") == 1024 ** 2
    assert parse_size("1.5 KiB", rounding="nearest") == 1536


def test_mixed_case_and_whitespace():
    assert parse_size("  2.5 KiB  ") == 2560
    assert parse_size("2.5 kIb") == 2560


def test_gnu_suffix_resolution():
    # With default_gnu allowed, resolution uses default_binary
    assert parse_size("1K", default_gnu=True, default_binary=False) == 1000
    assert parse_size("1K", default_gnu=True, default_binary=True) == 1024

    # permissive (strict=False) falls back to default_binary
    assert parse_size("1K", strict=False, default_binary=False) == 1000
    assert parse_size("1K", strict=False, default_binary=True) == 1024


def test_fractional_bytes_rounding():
    # 1.4 B -> nearest -> 1, ceil -> 2, floor -> 1
    assert parse_size("1.4B", rounding="nearest") == 1
    assert parse_size("1.4B", rounding="ceil") == 2
    assert parse_size("1.4B", rounding="floor") == 1

    # negative allowed in permissive mode
    assert parse_size("-1.4 B", rounding="nearest", strict=False) == -1


def test_large_values_not_infinite():
    # Extremely large numeric literal should raise
    try:
        parse_size("1e5000")
        raise AssertionError("expected ValueError for inf")
    except ValueError:
        pass


def test_round_trip_small_bytes():
    for n in (0, 1, 42, 999):
        s = naturalsize(n, format="%.0f")
        assert parse_size(s) == n


def test_naturalsize_regression_examples():
    # lock regressions
    assert naturalsize(1536, binary=True) == "1.5 KiB"
    assert naturalsize(1500, gnu=True) == "1.5K"


def test_cli_format_and_parse(tmp_path):
    # Prepare environment so python -m can find the src package
    import os
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")

    # format
    p = subprocess.run([sys.executable, "-m", "mini_humanize", "format", "1536", "--binary"], capture_output=True, text=True, env=env)
    assert p.returncode == 0
    assert p.stdout.strip() == "1.5 KiB"

    # parse (permissive) with default-binary
    p = subprocess.run([sys.executable, "-m", "mini_humanize", "parse", "1.5KiB", "--default-binary"], capture_output=True, text=True, env=env)
    assert p.returncode == 0
    assert p.stdout.strip() == "1536"
