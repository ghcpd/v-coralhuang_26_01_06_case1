from __future__ import annotations

import math
import re
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
    """
    Parse human-readable size string into bytes.
    
    Args:
        text: Size string to parse (e.g., "1.5 GB", "512MB", "10K")
        default_binary: If True, treat ambiguous units as binary (base 1024)
        default_gnu: If True, treat ambiguous units (e.g., "K") as GNU-style
        allow_thousands_separator: If True, allow ',' or '_' in number
        rounding: How to round fractional bytes: "floor", "nearest", or "ceil"
        strict: If True, reject ambiguities; if False, use defaults
    
    Returns:
        Size in bytes as an integer
        
    Raises:
        ValueError: Invalid string, unknown unit, or empty string
        OverflowError: Value exceeds integer limits
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    if not text:
        raise ValueError("Input string is empty or whitespace only")
    
    # Normalize: remove thousands separators if allowed
    if allow_thousands_separator:
        text = text.replace(",", "").replace("_", "")
    
    # Pattern: optional sign, number (with optional decimal), optional whitespace, optional unit
    # This pattern allows: -1.5 GB, 512MB, 10 K, 1,024B (if allowed), etc.
    pattern = r"^\s*([+-]?)(\d+(?:[.,]\d+)?)\s*([a-zA-Z]*)?\s*$"
    match = re.match(pattern, text)
    
    if not match:
        raise ValueError(f"Invalid size format: '{text}'")
    
    sign_str, number_str, unit_str = match.groups()
    
    # Replace comma with dot for float parsing (thousands separator already handled)
    number_str = number_str.replace(",", ".")
    
    try:
        value = float(number_str)
    except ValueError:
        raise ValueError(f"Invalid number: '{number_str}'")
    
    # Handle negative values
    if sign_str == "-":
        value = -value
    
    if value < 0:
        raise ValueError("Negative size values are not supported")
    
    # Handle NaN/inf
    if math.isnan(value) or math.isinf(value):
        raise ValueError("NaN and infinity are not supported")
    
    # No unit means bytes
    if not unit_str:
        unit_str = "B"
    
    # Normalize unit case for matching
    unit_original = unit_str
    unit_lower = unit_str.lower()
    
    # Define unit multipliers
    # Decimal (base 1000)
    decimal_units = {
        "b": 1,
        "kb": 1_000,
        "mb": 1_000_000,
        "gb": 1_000_000_000,
        "tb": 1_000_000_000_000,
        "pb": 1_000_000_000_000_000,
    }
    
    # Binary (base 1024)
    binary_units = {
        "b": 1,
        "kib": 1024,
        "mib": 1024 ** 2,
        "gib": 1024 ** 3,
        "tib": 1024 ** 4,
        "pib": 1024 ** 5,
    }
    
    # GNU-style single letters (ambiguous: could be decimal or binary)
    gnu_units = {
        "b": 1,
        "k": 1024 if default_binary else 1000,
        "m": (1024 ** 2) if default_binary else (1000 ** 2),
        "g": (1024 ** 3) if default_binary else (1000 ** 3),
        "t": (1024 ** 4) if default_binary else (1000 ** 4),
        "p": (1024 ** 5) if default_binary else (1000 ** 5),
    }
    
    multiplier = None
    
    # Try to match unit
    if unit_lower in decimal_units:
        multiplier = decimal_units[unit_lower]
    elif unit_lower in binary_units:
        multiplier = binary_units[unit_lower]
    elif unit_lower in gnu_units:
        # GNU-style unit
        if strict and not default_gnu:
            raise ValueError(
                f"Ambiguous unit '{unit_original}' in strict mode. Use explicit units like 'KB'/'KiB' "
                f"or enable default_gnu=True"
            )
        multiplier = gnu_units[unit_lower]
    else:
        raise ValueError(f"Unknown unit: '{unit_original}'")
    
    # Calculate bytes
    bytes_value = value * multiplier
    
    # Apply rounding
    if rounding == "floor":
        result = int(math.floor(bytes_value))
    elif rounding == "ceil":
        result = int(math.ceil(bytes_value))
    else:  # "nearest"
        result = int(round(bytes_value))
    
    # Check for overflow
    if result > 2**63 - 1:
        raise OverflowError(f"Size value {result} exceeds maximum integer")
    
    return result

