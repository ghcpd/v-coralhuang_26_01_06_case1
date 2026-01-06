from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union

NumberOrString = Union[int, float, str]
RoundingMode = Literal["floor", "nearest", "ceil"]


@dataclass(frozen=True)
class SizeFormatSpec:
    binary: bool = False
    gnu: bool = False
    format: str = "%.1f"
    strip_trailing_zeros: bool = False


def naturalsize(
    value: NumberOrString,
    *,
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
    strip_trailing_zeros: bool = False,
) -> str:
    """
    Simplified naturalsize, inspired by python-humanize/humanize.

    Baseline behavior:
    - gnu=False:
        decimal units: B, kB, MB, GB, TB, PB
        binary units:  B, KiB, MiB, GiB, TiB, PiB
      Output: "<number> <suffix>"
    - gnu=True:
        decimal units: B, K, M, G, T, P (base 1000)
        binary units:  B, K, M, G, T, P (base 1024)
      Output: "<number><suffix>"

    NOTE: This baseline is intentionally naive for agent evaluation.
    """
    if isinstance(value, str):
        try:
            value_f = float(value)
        except ValueError:
            raise ValueError("value must be a number or numeric string")
    elif isinstance(value, (int, float)):
        value_f = float(value)
    else:
        raise TypeError("value must be int, float, or str")

    sign = "-" if value_f < 0 else ""
    size = abs(value_f)

    if binary:
        base = 1024.0
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
        gnu_units = ["B", "K", "M", "G", "T", "P"]
    else:
        base = 1000.0
        units = ["B", "kB", "MB", "GB", "TB", "PB"]
        gnu_units = ["B", "K", "M", "G", "T", "P"]

    idx = 0
    while size >= base and idx < len(units) - 1:
        size /= base
        idx += 1

    suffix = (gnu_units[idx] if gnu else units[idx])

    num = format % size
    if strip_trailing_zeros:
        if "." in num:
            num = num.rstrip("0").rstrip(".")
            if num == "-0":
                num = "0"

    if gnu:
        return f"{sign}{num}{suffix}"
    return f"{sign}{num} {suffix}"


def parse_size(
    text: str,
    *,
    default_binary: bool = False,
    default_gnu: bool = False,
    allow_thousands_separator: bool = False,
    rounding: RoundingMode = "nearest",
    strict: bool = True,
) -> int:
    """Parse a human-friendly size string and return the number of bytes as an int.

    Behavior (explicit and testable):
    - Accepts numeric values with an optional unit suffix, e.g. "1.5 kB", "2KiB", "3K".
    - Whitespace between number and unit is optional; letter case is ignored.
    - Recognised suffixes (case-insensitive):
        * Binary (base 1024) explicit: KiB, MiB, GiB, TiB, PiB
        * Decimal (base 1000) explicit: kB, MB, GB, TB, PB
        * GNU-style single-letter: K, M, G, T, P (ambiguous — see below)
        * Bytes: B, byte, bytes or no suffix => bytes
    - Ambiguity resolution for single-letter suffixes ("K", "M", ...):
        * If the suffix contains an "i" (e.g. "KiB") it is binary (1024).
        * If the suffix is multi-letter and explicitly indicates kB/MB it is decimal (1000).
        * Single-letter suffixes are accepted only when either
            - `default_gnu=True`, or
            - `strict=False` (permissive mode).
          Their meaning is then controlled by `default_binary`:
            - `default_binary=True`  => single-letter means 1024**n
            - `default_binary=False` => single-letter means 1000**n
    - If no unit is provided the value is interpreted as bytes.

    Numeric parsing and rounding:
    - If the numeric portion contains no decimal point or exponent it is parsed
      as ``int`` (preserving large integers exactly). Otherwise it is parsed
      as ``float``.
    - If ``allow_thousands_separator=True`` commas and underscores are
      permitted in the numeric literal and will be removed before parsing.
      If disabled, any appearance of those characters causes ValueError.
    - ``rounding`` controls conversion to integer bytes when the computed
      byte count is fractional: "floor", "nearest", or "ceil".
      "nearest" uses Python's ``round()`` (ties to even).

    Error policies:
    - Empty string, unknown units, NaN/inf, malformed numbers raise ValueError.
    - By default (``strict=True``) negative values are rejected with ValueError.
      If ``strict=False`` negatives are accepted and the sign is preserved.

    Notes on limits:
    - Python's integers are unbounded; this function does not artificially
      cap extremely large values (no OverflowError for large ints).

    Parameters mirror the CLI flags and are fully unit-tested.
    """
    import re
    import math

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    original = text
    text = text.strip()
    if not text:
        raise ValueError("empty size string")

    # regex: capture number (with optional separators/decimal) and optional unit letters
    m = re.match(r"^([+-]?[0-9][0-9,_]*(?:\.[0-9]+)?|[+-]?\.[0-9]+|[+-]?[0-9]+(?:\.[0-9]+)?)(?:\s*([A-Za-z]+))?$", text)
    if not m:
        raise ValueError(f"invalid size: {original!r}")

    num_s, unit_s = m.group(1), m.group(2) or ""

    # thousands separators
    if ("," in num_s or "_" in num_s) and not allow_thousands_separator:
        raise ValueError("thousands separators not allowed")

    cleaned_num = num_s.replace(",", "").replace("_", "")

    # parse number: prefer int when possible to preserve precision for large integers
    is_integer_literal = "." not in cleaned_num and "e" not in cleaned_num and "E" not in cleaned_num
    try:
        if is_integer_literal:
            number: float | int = int(cleaned_num)
        else:
            number = float(cleaned_num)
    except ValueError:
        raise ValueError(f"invalid numeric value: {num_s!r}")

    # reject NaN / inf
    if isinstance(number, float) and not math.isfinite(number):
        raise ValueError("NaN or infinite values are not allowed")

    sign = -1 if (isinstance(number, (int, float)) and number < 0) else 1
    if sign < 0 and strict:
        raise ValueError("negative sizes are not allowed in strict mode")

    unit = unit_s.lower()

    # unit-resolution helpers
    decimal_units = {"b": 0, "kb": 1, "mb": 2, "gb": 3, "tb": 4, "pb": 5}
    binary_units = {"b": 0, "kib": 1, "mib": 2, "gib": 3, "tib": 4, "pib": 5}
    single_letter = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5}

    multiplier: int
    if unit == "" or unit in ("b", "byte", "bytes"):
        multiplier = 1
    elif unit in binary_units:
        multiplier = 1024 ** binary_units[unit]
    elif unit in decimal_units:
        multiplier = 1000 ** decimal_units[unit]
    else:
        # handle single-letter GNU-style units like 'K', 'M'
        if unit.lower() in single_letter:
            if strict and not default_gnu:
                raise ValueError("single-letter units are ambiguous; enable default_gnu or use strict=False")
            exp = single_letter[unit.lower()]
            if default_binary:
                multiplier = 1024 ** exp
            else:
                multiplier = 1000 ** exp
        else:
            raise ValueError(f"unknown unit: {unit_s!r}")

    # compute byte value
    # preserve exactness when possible (int * int)
    if isinstance(number, int) and isinstance(multiplier, int):
        bytes_value_exact = number * multiplier
        return int(bytes_value_exact)

    bytes_value = float(number) * float(multiplier)

    # apply rounding
    if rounding == "floor":
        result = math.floor(bytes_value)
    elif rounding == "ceil":
        result = math.ceil(bytes_value)
    else:  # nearest
        # Python's round uses ties-to-even; this is documented behaviour
        result = int(round(bytes_value))

    return int(result)

