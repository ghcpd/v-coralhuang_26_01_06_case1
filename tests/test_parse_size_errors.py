import subprocess
import sys
import pytest

from mini_humanize import parse_size


def test_invalid_strings():
    with pytest.raises(ValueError):
        parse_size("")
    with pytest.raises(ValueError):
        parse_size("foobar")
    with pytest.raises(ValueError):
        parse_size("1 XB")


def test_nan_and_inf():
    with pytest.raises(ValueError):
        parse_size("nan")
    with pytest.raises(ValueError):
        parse_size("inf")


def test_negative_strict_behavior():
    with pytest.raises(ValueError):
        parse_size("-1 kB", strict=True)
    assert parse_size("-1 kB", strict=False) == -1000


def test_thousands_separator():
    assert parse_size("1,234 kB", allow_thousands_separator=True) == 1234_000
    with pytest.raises(ValueError):
        parse_size("1,234 kB", allow_thousands_separator=False)


def test_cli_ambiguous_gnu_fails():
    # invoking CLI parse on ambiguous '1K' should fail when strict
    p = subprocess.run([sys.executable, "-m", "mini_humanize", "parse", "1K"], capture_output=True, text=True)
    assert p.returncode != 0
