import sys
import subprocess

PY = sys.executable


def run(args: list[str]):
    p = subprocess.run([PY, "-m", "mini_humanize"] + args, capture_output=True, text=True)
    return p


def test_cli_format_binary():
    p = run(["format", "1536", "--binary"])
    assert p.returncode == 0
    assert p.stdout.strip() == "1.5 KiB"


def test_cli_format_gnu():
    p = run(["format", "1000", "--gnu"])
    assert p.returncode == 0
    assert p.stdout.strip() == "1.0K"


def test_cli_parse_unambiguous():
    p = run(["parse", "1.5 KiB"])
    assert p.returncode == 0
    assert p.stdout.strip() == "1536"


def test_cli_parse_ambiguous_with_flags():
    p = run(["parse", "1K", "--default-gnu"])
    assert p.returncode == 0
    assert p.stdout.strip() == "1000"

    p2 = run(["parse", "1K", "--default-gnu", "--default-binary"])
    assert p2.returncode == 0
    assert p2.stdout.strip() == "1024"
