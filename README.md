# mini_humanize

Mini utilities to format and parse human-readable byte sizes.

## Features ✅
- `naturalsize(value, ...)` — format bytes into human-readable strings
- `parse_size(text, ...)` — parse human-readable size strings back to integer bytes
- CLI: `python -m mini_humanize format ...` and `python -m mini_humanize parse ...`

---

## Python API 🔧

### naturalsize(value, *, binary=False, gnu=False, format='%.1f', strip_trailing_zeros=False) -> str
- Purpose: Convert a numeric `value` (int, float, or numeric string) into a human readable string.
- Parameters:
  - `binary` (bool): use binary (1024) units when True, decimal (1000) otherwise.
  - `gnu` (bool): use GNU-style unit suffixes (e.g., `K`, `M`) and omit the separating space.
  - `format` (str): printf-style format for the numeric component.
  - `strip_trailing_zeros` (bool): when True, strip trailing zeros from the formatted number.

Behavior notes:
- Default behavior preserves historical outputs: decimal units by default (`kB`, `MB`, ...), with a space between number and suffix.
- When `gnu=True`, suffixes become `K/M/G/...` and no space is used.

### parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding='nearest', strict=True) -> int
- Purpose: Parse `text` into an integer number of bytes.
- Parameters:
  - `default_binary` (bool): when GNU-style single-letter units are used (e.g., `1K`), choose binary (1024) units if True, decimal (1000) otherwise.
  - `default_gnu` (bool): whether single-letter suffixes like `K` should be accepted as GNU-style units; when False and `strict=True`, single-letter units are considered ambiguous and will raise an error.
  - `allow_thousands_separator` (bool): if True, `,` and `_` are permitted inside the integer portion (e.g., `1,234.5`). If False, such separators raise `ValueError`.
  - `rounding` (`'floor'|'nearest'|'ceil'`): how to convert fractional bytes to ints.
  - `strict` (bool): when True, disallow ambiguous GNU suffixes and negative values; when False, be permissive and resolve ambiguity using `default_binary`.

Supported input patterns:
- Numeric values may use decimal points and optional scientific notation (e.g., `1.5`, `1e3`).
- Units supported (case-insensitive):
  - Bytes: `B` or no unit
  - Decimal: `kB`, `MB`, `GB`, `TB`, `PB` (multipliers 1000^1..)
  - Binary: `KiB`, `MiB`, `GiB`, `TiB`, `PiB` (multipliers 1024^1..)
  - GNU-style single letters: `K`, `M`, `G`, `T`, `P` — ambiguous between decimal and binary and controlled by `default_binary` and `default_gnu`.

Ambiguity and strictness:
- If an input uses GNU single-letter suffix (e.g., `1K`) and `default_gnu=False` with `strict=True`, `parse_size` will raise `ValueError` to avoid guessing.
- If `strict=False` or `default_gnu=True`, the choice between 1000 vs 1024 for `K/M/...` is decided by `default_binary`.

Error policies:
- Empty strings, invalid numbers (including `NaN`/`Inf`), unknown unit strings, and disallowed thousands separators raise `ValueError`.
- Negative values are rejected in `strict=True` mode (raise `ValueError`); allowed in permissive mode (`strict=False`).

Rounding rules:
- `floor`: round down toward -inf
- `nearest`: round to nearest integer (ties away from zero)
- `ceil`: round up toward +inf

---

## CLI usage 💻

Examples:
- Format bytes -> human readable:
  - python -m mini_humanize format 1536 --binary  # -> "1.5 KiB"
  - python -m mini_humanize format 1536 --binary --gnu  # -> "1.5K"

- Parse human readable -> bytes:
  - python -m mini_humanize parse 1.5KiB --default-binary  # -> 1536
  - python -m mini_humanize parse "1,234.5 kB" --allow-thousands-separator  # -> 1234500

Ambiguous inputs:
- `1K` is ambiguous: use `--default-binary` and/or set `strict`/`permissive` accordingly.

---

## Tests and one-click test script 🧪

Run the full test suite with a single command:

```
python run_tests
```

The script will install `pytest` and `pytest-cov` if they are missing, then run the tests and exit with an appropriate status code.

---

## Notes
- No third-party runtime dependencies are required (tests use `pytest`).
- Type annotations are present for public functions.
