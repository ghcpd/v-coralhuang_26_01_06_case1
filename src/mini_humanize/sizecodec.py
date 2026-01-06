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
    import re
    import math

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    s = text.strip()
    if not s:
        raise ValueError("empty string")

    # Capture sign, numeric part, and optional unit (letters)
    m = re.match(r"^([+-]?)([0-9][0-9_,]*(?:\.[0-9][0-9_,]*)?|\.[0-9][0-9_,]*)(?:\s*([A-Za-z]+))?$", s)
    if not m:
        raise ValueError(f"invalid size string: {text!r}")

    sign_s, num_s, unit_s = m.groups()

    # Thousands separator handling
    if ("," in num_s or "_" in num_s) and not allow_thousands_separator:
        raise ValueError("thousands separators not allowed")

    num_clean = num_s.replace(",", "").replace("_", "")

    try:
        num = float(num_clean)
    except ValueError:
        raise ValueError(f"invalid numeric value: {num_clean!r}")

    if math.isnan(num) or math.isinf(num):
        raise ValueError("invalid numeric value: NaN or Inf not allowed")

    if sign_s == "-":
        num = -num

    # Units
    if unit_s is None:
        # No unit -> bytes
        base = 1
        exp = 0
    else:
        u = unit_s.strip()
        if not u:
            base = 1
            exp = 0
        else:
            ul = u.lower()
            # bytes
            if ul in ("b", "byte", "bytes"):
                base = 1
                exp = 0
            else:
                # Check for explicit binary: kib, mib, gib, tib, pib (accept 'ki', 'kib')
                if ul.startswith("ki") or ul.startswith("kib") or ul.startswith("mi") or ul.startswith("mib") or ul.startswith("gi") or ul.startswith("gib") or ul.startswith("ti") or ul.startswith("tib") or ul.startswith("pi") or ul.startswith("pib"):
                    # e.g., kib, KiB
                    prefix = ul[0]
                    exp = {
                        "k": 1,
                        "m": 2,
                        "g": 3,
                        "t": 4,
                        "p": 5,
                    }[prefix]
                    base = 1024
                else:
                    # Endswith 'b' (kB, MB, etc.) -> decimal
                    if ul.endswith("b") and len(ul) >= 2:
                        prefix = ul[0]
                        if prefix not in "kmgtp":
                            raise ValueError(f"unknown unit: {unit_s!r}")
                        exp = {
                            "k": 1,
                            "m": 2,
                            "g": 3,
                            "t": 4,
                            "p": 5,
                        }[prefix]
                        base = 1000
                    else:
                        # Possibly GNU one-letter suffix like K/M/G
                        if len(ul) == 1 and ul in "kmgtp":
                            if strict and not default_gnu:
                                raise ValueError(f"ambiguous GNU unit: {unit_s!r}")
                            exp = {
                                "k": 1,
                                "m": 2,
                                "g": 3,
                                "t": 4,
                                "p": 5,
                            }[ul]
                            base = 1024 if default_binary else 1000
                        else:
                            raise ValueError(f"unknown unit: {unit_s!r}")

    # Compute bytes (float)
    try:
        multiplier = float(base) ** exp
        raw = num * multiplier
    except OverflowError:
        raise OverflowError("value too large")

    if math.isnan(raw) or math.isinf(raw):
        raise ValueError("resulting bytes value is not finite")

    # Negative handling
    if raw < 0 and strict:
        raise ValueError("negative values are not allowed in strict mode")

    # Apply rounding
    if rounding == "floor":
        b = math.floor(raw)
    elif rounding == "ceil":
        b = math.ceil(raw)
    elif rounding == "nearest":
        # Round half away from zero
        if raw >= 0:
            b = math.floor(raw + 0.5)
        else:
            b = math.ceil(raw - 0.5)
    else:
        raise ValueError(f"invalid rounding mode: {rounding!r}")

    return int(b)
