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
    Parse human-readable size string into bytes.

    Intentionally left incomplete. Agent must implement:
    - decimal + binary units, with and without spaces
    - KiB/MiB... vs kB/MB...
    - GNU suffixes K/M/G/T/P with ambiguity controlled by defaults
    - optional thousands separators
    - negative handling policy + strict vs permissive behavior
    - rounding behavior for fractional bytes
    """
    import math
    import re

    if not isinstance(text, str):
        raise TypeError("text must be a str")

    txt = text.strip()
    if txt == "":
        raise ValueError("input is empty")

    # Extract sign, number, and unit
    m = re.match(r"^(?P<sign>[+-]?)(?P<number>[^a-zA-Z]*?)(?P<unit>[a-zA-Z]*)$", txt)
    if not m:
        raise ValueError("invalid size string")

    sign_s = m.group("sign") or ""
    number_s = (m.group("number") or "").strip()
    unit_s = (m.group("unit") or "").strip()

    if number_s == "":
        raise ValueError("no numeric value found")

    # Thousands separators
    if not allow_thousands_separator and ("," in number_s or "_" in number_s):
        raise ValueError("thousands separators not allowed")

    if allow_thousands_separator:
        number_s = number_s.replace(",", "").replace("_", "")

    # Normalize number and parse float
    try:
        # allow scientific notation
        number = float(number_s)
    except ValueError:
        raise ValueError("invalid numeric value")

    if math.isnan(number) or math.isinf(number):
        raise ValueError("numeric value must be finite")

    if sign_s == "-":
        number = -number

    # Unit handling
    u = unit_s.lower()

    # Map prefix letter to power
    prefixes = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5}

    def pow1000(p: int) -> int:
        return 1000 ** p

    def pow1024(p: int) -> int:
        return 1024 ** p

    multiplier: int = 1

    if u in ("", "b"):
        multiplier = 1
    else:
        # detect explicit i (binary) e.g., kib, mib, kib, kibi accepted
        # detect forms like k, kb, kB, KiB, Ki
        if len(u) >= 2 and u.endswith("ib"):
            # KiB style -> binary
            p = u[0]
            if p not in prefixes:
                raise ValueError(f"unknown unit '{unit_s}'")
            multiplier = pow1024(prefixes[p])
        elif len(u) >= 2 and u.endswith("i"):
            p = u[0]
            if p not in prefixes:
                raise ValueError(f"unknown unit '{unit_s}'")
            multiplier = pow1024(prefixes[p])
        elif len(u) >= 1 and u.endswith("b"):
            # kb, mb, etc -> decimal
            p = u[0]
            if p not in prefixes:
                raise ValueError(f"unknown unit '{unit_s}'")
            multiplier = pow1000(prefixes[p])
        elif len(u) == 1:
            # single-letter GNU suffix: ambiguous
            p = u[0]
            if p not in prefixes:
                raise ValueError(f"unknown unit '{unit_s}'")
            # If default_gnu is False and strict, it's an error
            if not default_gnu and strict:
                raise ValueError("ambiguous GNU unit; enable permissive mode or specify unit")
            use_binary = bool(default_binary)
            multiplier = pow1024(prefixes[p]) if use_binary else pow1000(prefixes[p])
        else:
            # unknown form
            raise ValueError(f"unknown unit '{unit_s}'")

    # Compute bytes as float
    bytes_f = number * multiplier

    # Negative handling
    if bytes_f < 0 and strict:
        raise ValueError("negative sizes are not allowed in strict mode")

    # Apply rounding
    if rounding == "floor":
        bytes_i = math.floor(bytes_f)
    elif rounding == "ceil":
        bytes_i = math.ceil(bytes_f)
    elif rounding == "nearest":
        # round half away from zero
        if bytes_f >= 0:
            bytes_i = int(math.floor(bytes_f + 0.5))
        else:
            bytes_i = int(math.ceil(bytes_f - 0.5))
    else:
        raise ValueError("invalid rounding mode")

    return int(bytes_i)
