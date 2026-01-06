# mini_humanize

A lightweight Python library for formatting and parsing human-readable file sizes.

## Features

- **Format bytes to human-readable strings** with `naturalsize()`
- **Parse human-readable size strings to bytes** with `parse_size()`
- Support for decimal (base 1000) and binary (base 1024) units
- Support for standard units (kB, MB, GB) and binary units (KiB, MiB, GiB)
- Support for GNU-style single-letter units (K, M, G, T, P)
- Configurable rounding behavior (floor, nearest, ceil)
- Flexible parsing with strict and permissive modes
- Optional thousands separator support

## Installation

No external dependencies required beyond Python 3.10+.

For development and testing, install optional dependencies:

```bash
pip install -e ".[dev]"
```

## Python API

### `naturalsize(value, *, binary=False, gnu=False, format="%.1f", strip_trailing_zeros=False) -> str`

Convert a number (int, float, or numeric string) to a human-readable size format.

**Parameters:**
- `value`: Number (int, float) or numeric string to format
- `binary` (bool, default: False): Use binary units (1024-based) instead of decimal (1000-based)
- `gnu` (bool, default: False): Use GNU-style output (no space, single letters)
- `format` (str, default: "%.1f"): Python format string for numeric precision
- `strip_trailing_zeros` (bool, default: False): Remove trailing zeros after decimal point

**Returns:** Formatted size string

**Output Formats:**
- Default (gnu=False, binary=False): `"<number> <unit>"` with decimal units (kB, MB, GB, TB, PB)
- Default (gnu=False, binary=True): `"<number> <unit>"` with binary units (KiB, MiB, GiB, TiB, PiB)
- GNU (gnu=True, binary=False): `"<number><unit>"` with decimal units (K, M, G, T, P) - no space
- GNU (gnu=True, binary=True): `"<number><unit>"` with binary units (K, M, G, T, P) - no space

**Examples:**

```python
from mini_humanize import naturalsize

naturalsize(0)                      # "0.0 B"
naturalsize(1024)                  # "1.0 kB"
naturalsize(1024, binary=True)      # "1.0 KiB"
naturalsize(1500000)               # "1.5 MB"
naturalsize(1000, gnu=True)         # "1.0K"
naturalsize(1000, strip_trailing_zeros=True)  # "1 kB"
naturalsize(1234, format="%.0f")    # "1 kB"
```

### `parse_size(text, *, default_binary=False, default_gnu=False, allow_thousands_separator=False, rounding="nearest", strict=True) -> int`

Parse a human-readable size string to bytes.

**Parameters:**
- `text` (str): Size string to parse (e.g., "1.5 GB", "512MB", "10K")
- `default_binary` (bool, default: False): Treat ambiguous units as binary (base 1024) instead of decimal
- `default_gnu` (bool, default: False): Treat single-letter units (K, M, G, T, P) as valid
- `allow_thousands_separator` (bool, default: False): Accept comma (,) or underscore (_) as thousands separators
- `rounding` (str, default: "nearest"): Rounding mode for fractional bytes: "floor", "nearest", or "ceil"
- `strict` (bool, default: True): Strict mode rejects ambiguous units; permissive mode uses defaults

**Returns:** Size in bytes as an integer

**Supported Units:**

| Unit Type | Decimal (base 1000) | Binary (base 1024) |
|-----------|---------------------|-------------------|
| Standard  | kB, MB, GB, TB, PB  | KiB, MiB, GiB, TiB, PiB |
| GNU       | K, M, G, T, P       | K, M, G, T, P (when `default_binary=True`) |
| Bytes     | B (or omitted)      | B (or omitted) |

**Ambiguity Handling:**

The parser must resolve several ambiguities. The behavior is controlled jointly by the `strict`, `default_binary`, and `default_gnu` parameters:

1. **GNU-style single letters (K, M, G, T, P):**
   - In `strict=True` mode without `default_gnu=True`: Raises `ValueError` (ambiguous)
   - In `strict=False` or with `default_gnu=True`: Accepted as valid
   - If `default_binary=True`: Interpreted as binary (1024-based)
   - If `default_binary=False` (default): Interpreted as decimal (1000-based)

2. **Mixed case (e.g., "Kb", "kB", "KIB"):**
   - Case is normalized (converted to lowercase)
   - Units are matched case-insensitively
   - Extra characters beyond the unit are ignored (e.g., "KIB" matches "KiB")

3. **Whitespace:**
   - Optional spaces between number and unit are allowed and ignored
   - Leading and trailing whitespace is stripped

**Error Handling:**

The function raises `ValueError` for:
- Empty or whitespace-only strings
- Invalid number formats
- Unknown units
- Negative values
- NaN or infinity values
- Ambiguous units in strict mode (when `default_gnu=False`)

The function raises `OverflowError` for:
- Values that exceed 2^63 - 1 bytes (maximum integer)

**Rounding Behavior:**

When parsing fractional bytes, the `rounding` parameter determines how fractional parts are handled:
- `"floor"`: Round down to nearest integer byte
- `"nearest"`: Round to nearest integer byte (uses Python's banker's rounding)
- `"ceil"`: Round up to nearest integer byte

**Examples:**

```python
from mini_humanize import parse_size

parse_size("1000")           # 1000
parse_size("1 KB")           # 1000
parse_size("1KiB")           # 1024
parse_size("1.5 MB")         # 1500000
parse_size("1K", default_gnu=True)  # 1000
parse_size("1K", default_gnu=True, default_binary=True)  # 1024
parse_size("1,000B", allow_thousands_separator=True)  # 1000
parse_size("1.5B", rounding="ceil")  # 2
parse_size("1.5B", rounding="floor")  # 1
```

## CLI Usage

The CLI can be invoked with `python -m mini_humanize <subcommand>`.

### format Subcommand

Format bytes into human-readable size.

**Syntax:**
```
python -m mini_humanize format VALUE [OPTIONS]
```

**Options:**
- `--binary`: Use binary units (base 1024)
- `--gnu`: Use GNU-style output (no space)
- `--format FORMAT`: Custom format string (default: "%.1f")
- `--strip-trailing-zeros`: Remove trailing zeros

**Examples:**
```bash
python -m mini_humanize format 1024
# Output: 1.0 kB

python -m mini_humanize format 1024 --binary
# Output: 1.0 KiB

python -m mini_humanize format 1000000 --gnu
# Output: 1.0M

python -m mini_humanize format 1000 --strip-trailing-zeros
# Output: 1 kB
```

### parse Subcommand

Parse human-readable size into bytes.

**Syntax:**
```
python -m mini_humanize parse TEXT [OPTIONS]
```

**Options:**
- `--default-binary`: Treat ambiguous units as binary
- `--default-gnu`: Treat single-letter units as valid
- `--allow-thousands-separator`: Accept comma/underscore in numbers
- `--rounding {floor|nearest|ceil}`: Rounding mode for fractional bytes
- `--strict`: Enable strict mode (default, rejects ambiguities)
- `--permissive`: Disable strict mode (uses defaults for ambiguities)

**Examples:**
```bash
python -m mini_humanize parse 1000
# Output: 1000

python -m mini_humanize parse "1 KB"
# Output: 1000

python -m mini_humanize parse 1KiB
# Output: 1024

python -m mini_humanize parse "1K" --default-gnu
# Output: 1000

python -m mini_humanize parse "1K" --default-gnu --default-binary
# Output: 1024

python -m mini_humanize parse "1.5B" --rounding ceil
# Output: 2
```

## Testing

Run the full test suite with:

```bash
./run_tests
```

This command will:
1. Install dependencies (if needed)
2. Run all tests with pytest
3. Display test summary and coverage

The test suite covers:
- **Normal paths**: All unit types, decimal/binary, GNU style, whitespace handling, mixed case, fractional values
- **Edge cases**: Invalid strings, unknown units, empty strings, very large values, NaN/inf, negative handling, thousands separators
- **Consistency**: Round-trip behavior (parse → format or format → parse)
- **CLI functionality**: Both format and parse subcommands
- **Regression protection**: Backward compatibility for naturalsize

## Implementation Notes

### Unit Multipliers

**Decimal units (base 1000):**
- B = 1
- kB = 1,000
- MB = 1,000,000
- GB = 1,000,000,000
- TB = 1,000,000,000,000
- PB = 1,000,000,000,000,000

**Binary units (base 1024):**
- B = 1
- KiB = 1,024
- MiB = 1,048,576
- GiB = 1,073,741,824
- TiB = 1,099,511,627,776
- PiB = 1,125,899,906,842,624

**GNU units:**
- When `default_gnu=False` (default): K=1,000, M=1,000,000, etc. (decimal)
- When `default_binary=True`: K=1,024, M=1,048,576, etc. (binary)

### Key Design Decisions

1. **Case insensitivity**: All units are normalized to lowercase for matching, allowing "KB", "kB", "kb", "Kb" to be equivalent.

2. **Flexible whitespace**: Both single and multiple spaces between number and unit are accepted.

3. **Extra characters in unit**: Extra characters beyond the recognized unit are ignored (e.g., "KIB" matches "KiB").

4. **Strict vs permissive**: The `strict` parameter provides explicit control over how ambiguities are resolved, allowing both safety and convenience.

5. **Rounding is explicit**: The default rounding behavior is "nearest", but users can choose "floor" or "ceil" for specific use cases.

6. **No negative values**: Negative sizes are rejected as they don't make semantic sense in this context.

## Version Information

- Python: 3.10+
- Type annotations: Supported on all function signatures

## License

This is a minimal evaluation project.
