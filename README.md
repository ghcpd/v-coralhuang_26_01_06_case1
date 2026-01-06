# mini_humanize

A Python library for formatting and parsing human-readable file sizes.

## APIs

### `naturalsize(value, *, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) -> str`

Formats a numeric value (bytes) into a human-readable string.

**Parameters:**
- `value`: The size in bytes (int, float, or numeric string)
- `binary`: If True, use binary units (1024 base) with "KiB", "MiB", etc. If False, use decimal units (1000 base) with "kB", "MB", etc.
- `gnu`: If True, use GNU-style output with short units ("K", "M", etc.) and no space between number and unit. If False, use long units with space.
- `format`: Printf-style format string for the number (default "%.1f")
- `strip_trailing_zeros`: If True, remove trailing ".0" from the formatted number

**Examples:**
```python
naturalsize(1000)  # "1.0 kB"
naturalsize(1024, binary=True)  # "1.0 KiB"
naturalsize(1000, gnu=True)  # "1.0K"
naturalsize(1024, binary=True, gnu=True)  # "1.0K"
naturalsize(1000, strip_trailing_zeros=True)  # "1 kB"
```

### `parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding="nearest", strict=True) -> int`

Parses a human-readable size string into bytes.

**Parameters:**
- `text`: The size string to parse
- `default_binary`: For ambiguous GNU units (K, M, etc.), use 1024 base if True, 1000 base if False
- `default_gnu`: If True, accept short GNU units (K, M, etc.). If False, only accept full units (kB, KiB, etc.)
- `allow_thousands_separator`: If True, allow commas as thousands separators in numbers
- `rounding`: How to round fractional bytes ("floor", "nearest", "ceil")
- `strict`: If True, raise errors for unknown units, ambiguous units, etc. If False, be more permissive

**Supported formats:**
- Decimal units: B, kB, MB, GB, TB, PB
- Binary units: B, KiB, MiB, GiB, TiB, PiB
- GNU units: B, K, M, G, T, P (when `default_gnu=True`)
- Optional whitespace and mixed case
- Fractional values
- Optional thousands separators (when `allow_thousands_separator=True`)

**Ambiguity handling:**
- Full units like "kB" or "KiB" are unambiguous and always accepted.
- Short GNU units like "K" are accepted only when `default_gnu=True`.
- When GNU units are accepted, the base (1000 or 1024) is determined by `default_binary`.
- If `default_gnu=False` and a short unit is encountered, raises `ValueError` if `strict=True`.

**Error handling:**
- Invalid strings: `ValueError`
- Unknown units: `ValueError` if `strict=True`, else assume bytes
- Empty strings: `ValueError`
- NaN/inf values: `ValueError`
- Negative values: allowed

**Rounding:** Applied to fractional byte values before returning int.

**Examples:**
```python
parse_size("1 kB")  # 1000
parse_size("1 KiB")  # 1024
parse_size("1K", default_gnu=True)  # 1000
parse_size("1K", default_gnu=True, default_binary=True)  # 1024
parse_size("1,000 kB", allow_thousands_separator=True)  # 1000000
parse_size("1.5 kB", rounding="floor")  # 1500
```

## CLI Usage

### Format command
```
python -m mini_humanize format <value> [--binary] [--gnu] [--format FORMAT] [--strip-trailing-zeros]
```

Examples:
```bash
python -m mini_humanize format 1000
# Output: 1.0 kB

python -m mini_humanize format 1024 --binary
# Output: 1.0 KiB

python -m mini_humanize format 1000 --gnu
# Output: 1.0K
```

### Parse command
```
python -m mini_humanize parse <text> [--default-binary] [--default-gnu] [--allow-thousands-separator] [--rounding {floor,nearest,ceil}] [--strict | --permissive]
```

Examples:
```bash
python -m mini_humanize parse "1 kB"
# Output: 1000

python -m mini_humanize parse "1K" --default-gnu
# Output: 1000

python -m mini_humanize parse "1K" --default-gnu --default-binary
# Output: 1024
```

## Running Tests

To run the full test suite:

```bash
./run_tests
```

This script will install required dependencies if missing and run pytest.