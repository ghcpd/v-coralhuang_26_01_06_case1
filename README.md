mini_humanize
===============

A small utility to format and parse human-readable file sizes.

Installation
------------
This is a small library intended to be used in a project directly. To run tests, use the one-click test command below.

One-click test
--------------
Run the full test suite with:

    python run_tests

(That script will install pytest/pytest-cov if needed and then run pytest.)

API
---

Functions:

- `naturalsize(value, *, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) -> str`
  - Purpose: Format a numeric value (bytes) into a human-readable string.
  - Parameters:
    - `value`: int, float, or numeric string (bytes). Negative values are accepted.
    - `binary`: use base 1024 and binary unit names (`KiB`, `MiB`, ...) when True; otherwise base 1000 and `kB`, `MB`, ...
    - `gnu`: use GNU-style single-letter suffixes (`K`, `M`,...) and omit the separating space when True.
    - `format`: printf-style format for the number part (default `"%.1f"`).
    - `strip_trailing_zeros`: if True remove trailing zeros and decimal point after formatting.
  - Notes: Backward-compatible with previous behavior; tests lock in a couple of exact outputs.

- `parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding="nearest", strict=True) -> int`
  - Purpose: Parse a human-readable size string into a number of bytes (integer).
  - Parameters:
    - `text`: the input string to parse. Must be non-empty.
    - `default_binary`: when ambiguity exists (GNU one-letter suffix), if True prefer base 1024, else 1000.
    - `default_gnu`: allow GNU-style single-letter suffixes (K/M/G...). If False and `strict=True`, a single-letter suffix is considered ambiguous and will raise an error.
    - `allow_thousands_separator`: if True, accept `,` or `_` in the integer part, e.g. `1,234` or `1_234`.
    - `rounding`: how to convert fractional bytes to integer bytes. One of `"floor"`, `"nearest"`, `"ceil"`. `nearest` rounds halves away from zero.
    - `strict`: stricter validation mode. When True, ambiguous GNU suffixes are rejected and negative values are rejected; when False, many ambiguities are resolved using the `default_` flags and negative values are accepted.
  - Accepted unit forms:
    - Binary explicit: `KiB`, `MiB`, ... (case-insensitive) ⇒ base 1024
    - Decimal explicit: `kB`, `MB`, ... (case-insensitive) ⇒ base 1000
    - GNU-style single-letter: `K`, `M`, `G`, ... (case-insensitive) ⇒ allowed only when `default_gnu=True` or `strict=False` (then resolved using `default_binary`).
    - `B`, `byte`, `bytes` ⇒ bytes
    - If no unit present, the number is interpreted as bytes.
  - Error handling and special cases:
    - Empty string, invalid numeric values (NaN/Inf), unknown units, or malformed strings raise `ValueError`.
    - If `allow_thousands_separator` is False, commas or underscores in the number will raise an error.
    - Extremely large numeric literals that become infinite are rejected.
    - When `strict=True`, negative values raise `ValueError`; when `strict=False` negative values are accepted and returned as negative bytes.

Examples
--------

Formatting:

    >>> from mini_humanize import naturalsize
    >>> naturalsize(1536, binary=True)
    '1.5 KiB'
    >>> naturalsize(1500, gnu=True)
    '1.5K'

Parsing:

    >>> from mini_humanize import parse_size
    >>> parse_size('1 KiB')
    1024
    >>> parse_size('1K', default_gnu=True)
    1000      # or 1024 if default_binary=True

Ambiguities and rules
---------------------
- A single-letter suffix like `K` is ambiguous between decimal (1000) and binary (1024). If `strict=True` (default) and `default_gnu=False`, such inputs raise `ValueError`. If `strict=False` or `default_gnu=True`, the value is resolved using `default_binary`.
- `rounding='nearest'` rounds halves away from zero (e.g., 1.5 -> 2, -1.5 -> -2).

Testing and development
-----------------------
- The test suite uses `pytest`. Run the one-click script:

    python run_tests

Files changed / added
--------------------
- Added: `tests/` with pytest tests
- Added: `README.md`, `run_tests` (one-click test runner), `.gitignore`
- Modified: `src/mini_humanize/sizecodec.py` (implemented `parse_size`)

License
-------
MIT
