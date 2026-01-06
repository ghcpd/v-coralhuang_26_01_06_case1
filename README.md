mini_humanize
=================

A tiny, dependency-free helper for formatting and parsing human-readable byte sizes.

APIs
----

- `naturalsize(value, *, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) -> str`
  - Purpose: Format a numeric byte value into a compact human-readable string.
  - Parameters:
    - `value`: int, float, or numeric string to format (may be negative).  
    - `binary`: when True use 1024-based units (`KiB`, `MiB`, ...); when False use 1000-based units (`kB`, `MB`, ...).
    - `gnu`: when True use tight GNU-style suffixes without a space (e.g. `1.5K`); when False include a space and use `kB`/`KiB` style.
    - `format`: printf-style format for the mantissa (default `"%.1f"`).
    - `strip_trailing_zeros`: when True remove trailing zeros and a trailing decimal point (for example `"1.0" -> "1"`).
  - Notes: Default behavior is preserved from the original implementation: `naturalsize(1500) -> "1.5 kB"`.

- `parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding="nearest", strict=True) -> int`
  - Purpose: Parse a human-friendly size string into an integer number of bytes.
  - Parameters:
    - `text`: the input string (e.g. `"1.5 kB"`, `"2MiB"`, `"2K"`).
    - `default_binary`: decides how ambiguous single-letter GNU suffixes are interpreted: if True they mean 1024-based multipliers; otherwise they mean 1000-based.
    - `default_gnu`: controls acceptance of single-letter GNU-style suffixes in strict mode (see below).
    - `allow_thousands_separator`: when True commas are accepted as thousands separators in the integer part (for example `"1,234.5 kB"`).
    - `rounding`: one of `"floor"`, `"nearest"`, or `"ceil"` and controls how fractional byte counts are converted to integers.
    - `strict`: when True (the default) parsing is conservative: negative sizes are rejected and single-letter GNU units are only accepted if `default_gnu=True`. When `strict=False` parsing is permissive: negative values are allowed and single-letter GNU suffixes are accepted regardless of `default_gnu`.

Supported unit forms
- Binary explicit: `KiB`, `MiB`, `GiB`, `TiB`, `PiB` (case-insensitive) => base 1024.
- Decimal explicit: `kB`, `MB`, `GB`, `TB`, `PB` (case-insensitive) => base 1000.
- GNU single-letter: `K`, `M`, `G`, `T`, `P` (case-insensitive). Interpretation (1000 vs 1024) is controlled by `default_binary`. Acceptance in strict mode is controlled by `default_gnu`.
- A bare number (no unit) is treated as bytes.

Error handling and edge-case policy
- Empty strings, non-numeric values, unknown units, and NaN/Infinity raise ValueError.
- By default (`strict=True`) negative sizes are rejected; set `strict=False` to allow them.
- Thousands separators (commas) are only accepted when `allow_thousands_separator=True` and must follow standard grouping.
- Very large values are accepted and returned as Python ints (no overflow errors thanks to Python's arbitrary-precision integers).

CLI
---

The package exposes a tiny CLI as a module: `python -m mini_humanize`.

Format examples
- python -m mini_humanize format 1500
  -> prints: 1.5 kB
- python -m mini_humanize format 1536 --binary
  -> prints: 1.5 KiB
- python -m mini_humanize format 1000 --gnu
  -> prints: 1.0K

Parse examples
- python -m mini_humanize parse "1.5 kB"
  -> prints: 1500
- python -m mini_humanize parse "2K" --default-gnu --default-binary
  -> prints: 2048
- python -m mini_humanize parse "1,234.5 kB" --allow-thousands-separator
  -> prints: 1234500

One-click test
--------------

To run the full test-suite (this command will install pytest if needed):

    python run_tests

Files added or modified
-----------------------
- Modified: `src/mini_humanize/sizecodec.py` (implemented `parse_size`)
- Added: `README.md`
- Added: `tests/test_sizecodec.py` (pytest test-suite)
- Added: `run_tests` (one-click test runner)
- Added: `.gitignore`

