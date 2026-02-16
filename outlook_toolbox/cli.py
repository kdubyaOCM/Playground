"""CLI entrypoint for outlook-toolbox."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from outlook_toolbox import __version__
from outlook_toolbox.core.scanner import scan_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outlook-toolbox",
        description="Archive and process email data.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="Scan email sources and extract metadata.")
    scan.add_argument("path", type=Path, help="File or directory to scan.")
    scan.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        dest="output_format",
        help="Output format (default: jsonl).",
    )
    scan.add_argument(
        "--include-body",
        action="store_true",
        default=False,
        help="Include a text body preview in output.",
    )
    scan.add_argument(
        "--max-body-chars",
        type=int,
        default=2000,
        help="Max characters for body preview (default: 2000).",
    )

    sub.add_parser("dedupe", help="Deduplicate messages in an archive.")
    sub.add_parser("export-pdf", help="Export archived messages to PDF.")

    return parser


def _cmd_scan(args: argparse.Namespace) -> int:
    records = scan_path(
        args.path,
        include_body=args.include_body,
        max_body_chars=args.max_body_chars,
    )
    dicts = [r.to_dict() for r in records]

    if args.output_format == "json":
        json.dump(dicts, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        for d in dicts:
            sys.stdout.write(json.dumps(d, ensure_ascii=False) + "\n")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "scan":
        return _cmd_scan(args)

    print(f"{args.command}: not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
