mini_humanize
================

A tiny, well-tested utilities module for formatting and parsing human-friendly byte sizes.

Features
- naturalsize(value, ...)  — format bytes into human readable strings (backward compatible)
- parse_size(text, ...)    — parse human-friendly size strings back to integer bytes
- CLI: python -m mini_humanize format|parse

Highlights
- Supports decimal (kB, MB...) and binary (KiB, MiB...) units
- Accepts GNU-style single-letter units (K/M/G...) with explicit ambiguity controls
- Configurable rounding and thousands-separator handling
- Strict and permissive modes for predictable ambiguity handling

Quick one-click test

Run the full test-suite (works on Windows/macOS/Linux):

    python run_tests

(Alternatively: ./run_tests)


API
---

naturalsize(value, *, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) -> str
- Purpose: format a numeric byte value into a human-friendly string.
- Parameters:
  - value: int | float | numeric string
  - binary: if True use base-1024 units (KiB, MiB...)
  - gnu: if True use compact GNU-style suffixes (no space, single-letter when appropriate)
  - format: printf-style format for the numeric portion (default "%.1f")
  - strip_trailing_zeros: remove trailing zeros and the decimal point when possible
- Backward compatibility: default behaviour is unchanged from earlier releases. Tests lock in a few canonical outputs.

parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding='nearest', strict=True) -> int
- Purpose: parse a human-readable size into the integer number of bytes.
- Parameters:
  - text: the size string to parse (e.g. "1.5 kB", "2KiB", "1K")
  - default_binary: when an ambiguous unit (like "K") is used, prefer binary (1024) if True
  - default_gnu: accept GNU single-letter suffixes (K/M/...) when True; otherwise single-letter units are rejected in strict mode
  - allow_thousands_separator: accept commas or underscores in the numeric literal (e.g. "1,234.5")
  - rounding: one of "floor", "nearest", "ceil" used when the computed byte count is fractional
    - "nearest" uses Python's round() (ties to even)
  - strict: when True perform stricter validation (reject negative numbers, ambiguous single-letter units unless default_gnu)

Ambiguity & strictness (summary)
- "KiB" / "kB": explicit — unambiguous (1024 vs 1000).
- Single-letter "K", "M", ...: considered ambiguous.
  - If `default_gnu=True` they are accepted and interpreted according to `default_binary`.
  - If `strict=True` and `default_gnu=False` they are rejected.
  - If `strict=False` they are accepted and interpreted according to `default_binary`.
- Missing unit => interpreted as bytes.

Error-handling policies
- Empty or malformed strings, unknown units, NaN/Infinity raise ValueError.
- Negative values: rejected in strict mode (ValueError); accepted and sign-preserved when strict=False.
- Thousands separators are rejected unless explicitly enabled via `allow_thousands_separator`.
- No artificial upper bound: extremely large integers are supported (Python ints are unbounded).

Rounding rules
- If the numeric-to-bytes conversion produces a fractional byte count, the `rounding` parameter controls how the result is converted to an integer:
  - "floor" — round toward -infinity
  - "ceil"  — round toward +infinity
  - "nearest" — Python's round() (ties to even)

CLI
---

Examples:
- Format bytes to human-readable (binary):

    python -m mini_humanize format 1536 --binary
    # => 1.5 KiB

- Parse a human-readable size (GNU K interpreted as 1000):

    python -m mini_humanize parse 1K --default-gnu
    # => 1000

- Parse permissively (accept negative and ambiguous units):

    python -m mini_humanize parse -1K --permissive --rounding floor


Testing
-------
- The project uses pytest. Run the full test-suite with the one-click command above.
- The test-suite covers normal operation, edge-cases, CLI behavior, and regression assertions that lock in core formatting outputs.


Development notes
-----------------
- No third-party runtime dependencies.
- Dev/test dependencies: pytest, pytest-cov (installed by the one-click script).
- Source layout: package under `src/`.

If you spot a behavior you disagree with (for example how an ambiguous "K" should be interpreted), open a small PR with proposed defaults and matching tests — the ambiguity rules are explicitly chosen to be conservative and testable.
