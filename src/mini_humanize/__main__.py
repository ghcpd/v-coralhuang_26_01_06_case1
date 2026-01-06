from __future__ import annotations

import argparse
import sys

from .sizecodec import naturalsize, parse_size


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mini_humanize")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_fmt = sub.add_parser("format", help="Format bytes into human readable size")
    p_fmt.add_argument("value")
    p_fmt.add_argument("--binary", action="store_true")
    p_fmt.add_argument("--gnu", action="store_true")
    p_fmt.add_argument("--format", default="%.1f")
    p_fmt.add_argument("--strip-trailing-zeros", action="store_true")

    p_parse = sub.add_parser("parse", help="Parse human readable size into bytes")
    p_parse.add_argument("text")
    p_parse.add_argument("--default-binary", action="store_true")
    p_parse.add_argument("--default-gnu", action="store_true")
    p_parse.add_argument("--allow-thousands-separator", action="store_true")
    p_parse.add_argument("--rounding", choices=["floor", "nearest", "ceil"], default="nearest")
    p_parse.add_argument("--strict", action="store_true", default=True)
    p_parse.add_argument("--permissive", action="store_true", default=False)

    args = p.parse_args(argv)

    if args.cmd == "format":
        out = naturalsize(
            args.value,
            binary=args.binary,
            gnu=args.gnu,
            format=args.format,
            strip_trailing_zeros=args.strip_trailing_zeros,
        )
        print(out)
        return 0

    if args.cmd == "parse":
        strict = args.strict and not args.permissive
        out = parse_size(
            args.text,
            default_binary=args.default_binary,
            default_gnu=args.default_gnu,
            allow_thousands_separator=args.allow_thousands_separator,
            rounding=args.rounding,
            strict=strict,
        )
        print(out)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
