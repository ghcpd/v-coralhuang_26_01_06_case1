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
    """
    Parse a human-readable size string and return the number of bytes as an int.

    Supported inputs
    - Binary units: "KiB", "MiB", "GiB", "TiB", "PiB" (case-insensitive) => base 1024
    - Decimal units: "kB", "MB", "GB", "TB", "PB" (case-insensitive) => base 1000
    - GNU-style single-letter units: "K", "M", "G", "T", "P" (case-insensitive)
      These are ambiguous: whether they mean 1000 or 1024 is decided by
      ``default_binary``. Their acceptance is controlled by ``strict`` and
      ``default_gnu`` (see behavior below).
    - Unit may be separated from the number by optional whitespace, and
      letter case is ignored.
    - Fractional quantities are supported (for example "1.5 kB").
    - Optional thousands separators (commas) are allowed when
      ``allow_thousands_separator=True``.

    Ambiguity & strictness
    - If ``strict=True`` (the default):
      - Single-letter GNU-style units (for example "K") are only accepted if
        ``default_gnu=True``. If they are not accepted, they raise ValueError.
      - Negative values are rejected (ValueError).
    - If ``strict=False`` (permissive):
      - Single-letter GNU units are accepted regardless of ``default_gnu``.
      - Negative values are allowed and the resulting integer will be
        negative.

    Interpretation rules
    - If the unit explicitly contains an "i" (e.g. "KiB") the binary
      (1024) interpretation is used.
    - If the unit explicitly contains "B" (e.g. "kB") the decimal (1000)
      interpretation is used.
    - If the unit is a single letter ("K"/"M"/...), the multiplier is
      1024**n when ``default_binary=True``, otherwise 1000**n.
    - If no unit is provided, the value is treated as bytes.

    Numeric & error handling
    - Empty strings, non-numeric values, NaN or infinity, and unknown units
      raise ValueError.
    - If ``allow_thousands_separator=False`` and the number contains commas,
      a ValueError is raised. When allowed, commas must be placed as standard
      thousands separators (groups of three digits to the left of the
      decimal point).
    - Python's unlimited-precision integers are used; there is no overflow
      error raised for very large values.

    Rounding
    - After applying the unit multiplier the resulting byte count may be a
      non-integer. The ``rounding`` parameter controls conversion to an
      integer: "floor" (math.floor), "nearest" (round to nearest), or
      "ceil" (math.ceil).
    """
    import math
    import re

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    s = text.strip()
    if s == "":
        raise ValueError("empty size string")

    # Split the string into a numeric prefix and an optional unit by
    # locating the first ASCII letter. This approach is simpler and more
    # robust than trying to capture all valid numeric forms with a single
    # giant regex.
    alpha = re.search(r"[A-Za-z]", s)
    if alpha:
        num_part = s[: alpha.start()].strip()
        unit_str = s[alpha.start() :].strip()
    else:
        num_part = s
        unit_str = ""

    if num_part == "":
        raise ValueError(f"could not parse size: {text!r}")

    # Build a stricter numeric-validation regex depending on thousands
    # separator policy. This guarantees that malformed groupings like
    # "12,34" are rejected.
    if allow_thousands_separator:
        num_regex = re.compile(r"^[+-]?(?:[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\.[0-9]+)$")
    else:
        num_regex = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$")

    if not num_regex.match(num_part):
        raise ValueError(f"could not parse numeric part: {num_part!r}")

    # Normalize and validate thousands separators if present
    if "," in num_part:
        if not allow_thousands_separator:
            raise ValueError("thousands separators not allowed")
        int_part, _, frac_part = num_part.partition(".")
        groups = int_part.split(",")
        if any(g == "" for g in groups):
            raise ValueError("invalid thousands separator placement")
        if len(groups[0]) > 3 or any(len(g) != 3 for g in groups[1:]):
            raise ValueError("invalid thousands separator placement")
        num_clean = int_part.replace(",", "") + ("." + frac_part if frac_part else "")
    else:
        num_clean = num_part

    # Extract sign separately so later logic can check policies
    sign_str = ""
    if num_clean[0] in "+-":
        sign_str = num_clean[0]
        num_clean = num_clean[1:]
    num_str = num_clean

    # Parse numeric value
    try:
        value = float(num_clean)
    except ValueError:
        raise ValueError(f"invalid numeric value: {num_clean!r}")

    if math.isnan(value) or math.isinf(value):
        raise ValueError("NaN or infinite values are not allowed")

    if sign_str == "-" and strict:
        raise ValueError("negative sizes are not allowed in strict mode")

    # Determine multiplier
    unit = unit_str.lower()
    if unit == "":
        multiplier = 1
    else:
        # Accept explicit byte forms
        if unit in ("b", "byte", "bytes"):
            multiplier = 1
        else:
            # Normalize common forms
            # Accept a trailing 'b' or not; decision depends on presence of 'i' or 'b'
            # Binary explicit: kib, mib, ...
            if unit.endswith("ib") and len(unit) == 3:
                prefix = unit[0]
                powers = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5}
                if prefix not in powers:
                    raise ValueError(f"unknown unit: {unit_str!r}")
                multiplier = 1024 ** powers[prefix]
            # Decimal explicit: kb, mb, ...
            elif unit.endswith("b") and len(unit) == 2:
                prefix = unit[0]
                powers = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5, "b": 0}
                if prefix not in powers:
                    raise ValueError(f"unknown unit: {unit_str!r}")
                multiplier = 1000 ** powers[prefix]
            # Single-letter GNU-style: K/M/G/T/P
            elif len(unit) == 1 and unit in "kmgtp":
                if strict and not default_gnu:
                    raise ValueError(
                        "single-letter GNU-style units are disallowed in strict mode unless default_gnu=True"
                    )
                powers = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5}
                mult_base = 1024 if default_binary else 1000
                multiplier = mult_base ** powers[unit]
            else:
                raise ValueError(f"unknown unit: {unit_str!r}")

    total = value * multiplier

    # Convert to integer according to rounding mode
    if rounding == "floor":
        result = math.floor(total)
    elif rounding == "ceil":
        result = math.ceil(total)
    else:
        # nearest
        result = int(round(total))

    if sign_str == "-":
        result = -result

    return int(result)
