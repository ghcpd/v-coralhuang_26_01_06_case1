import subprocess
import sys


def run_module(args):
    cmd = [sys.executable, "-m", "mini_humanize"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r


def test_format_subcommand_basic():
    r = run_module(["format", "1536", "--binary"])
    assert r.returncode == 0
    assert r.stdout.strip() == "1.5 KiB"


def test_format_subcommand_gnu():
    r = run_module(["format", "1536", "--binary", "--gnu"])
    assert r.returncode == 0
    assert r.stdout.strip() == "1.5K"


def test_parse_subcommand_basic():
    r = run_module(["parse", "1.5KiB", "--default-binary"])
    assert r.returncode == 0
    assert r.stdout.strip() == "1536"


def test_parse_subcommand_ambiguous_fails_in_strict():
    r = run_module(["parse", "1K"])
    assert r.returncode != 0
