from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union
import re
import math

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
    """
    Parse human-readable size string into bytes.

    Supports:
    - Decimal units: B, kB, MB, GB, TB, PB
    - Binary units: B, KiB, MiB, GiB, TiB, PiB
    - GNU units: B, K, M, G, T, P (base depends on default_binary)
    - Optional whitespace and mixed case
    - Fractional values
    - Optional thousands separators (commas) if allow_thousands_separator=True

    Ambiguity handling:
    - Full units (kB, KiB, etc.) are unambiguous and always accepted.
    - Short GNU units (K, M, etc.) are accepted only if default_gnu=True.
      When accepted, the base (1000 or 1024) is determined by default_binary.
    - If default_gnu=False and a short unit is encountered, raises ValueError if strict=True.
    - No unit means bytes.

    Error handling:
    - Invalid strings: ValueError
    - Unknown units: ValueError if strict=True, else assume bytes
    - Empty strings: ValueError
    - NaN/inf values: ValueError
    - Negative values: allowed (returns negative bytes)

    Rounding: applied to fractional byte values.
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty string")

    # Regex for number and unit
    if allow_thousands_separator:
        # Allow commas in number
        num_pattern = r'[+-]?(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?'
    else:
        num_pattern = r'[+-]?(?:\d+(?:\.\d+)?)'
    
    match = re.match(rf'^({num_pattern})\s*([a-zA-Z]*)$', text)
    if not match:
        raise ValueError(f"Invalid size string: {text}")
    
    num_str, unit = match.groups()
    if allow_thousands_separator:
        num_str = num_str.replace(',', '')
    
    try:
        num = float(num_str)
    except ValueError:
        raise ValueError(f"Invalid number: {num_str}")
    
    unit = unit.lower()
    
    # Multipliers
    decimal_multipliers = {
        '': 1,
        'b': 1,
        'kb': 1000,
        'mb': 1000**2,
        'gb': 1000**3,
        'tb': 1000**4,
        'pb': 1000**5,
    }
    binary_multipliers = {
        '': 1,
        'b': 1,
        'kib': 1024,
        'mib': 1024**2,
        'gib': 1024**3,
        'tib': 1024**4,
        'pib': 1024**5,
    }
    base = 1024 if default_binary else 1000
    gnu_multipliers = {
        '': 1,
        'b': 1,
        'k': base,
        'm': base**2,
        'g': base**3,
        't': base**4,
        'p': base**5,
    }
    
    if unit in decimal_multipliers:
        multiplier = decimal_multipliers[unit]
    elif unit in binary_multipliers:
        multiplier = binary_multipliers[unit]
    elif unit in gnu_multipliers and default_gnu:
        multiplier = gnu_multipliers[unit]
    else:
        if strict:
            raise ValueError(f"Unknown or ambiguous unit: {unit}")
        else:
            multiplier = 1  # assume bytes
    
    bytes_value = num * multiplier
    if not math.isfinite(bytes_value):
        raise ValueError("Invalid value: inf or nan")
    
    # Round to int
    if rounding == "floor":
        result = math.floor(bytes_value)
    elif rounding == "ceil":
        result = math.ceil(bytes_value)
    elif rounding == "nearest":
        result = round(bytes_value)
    else:
        raise ValueError(f"Invalid rounding mode: {rounding}")
    
    return result
