"""CLI entrypoint for outlook-toolbox."""

from __future__ import annotations

import argparse
import sys

from outlook_toolbox import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outlook-toolbox",
        description="Archive and process email data.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("scan", help="Scan email sources and build an archive.")
    sub.add_parser("dedupe", help="Deduplicate messages in an archive.")
    sub.add_parser("export-pdf", help="Export archived messages to PDF.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    print(f"{args.command}: not implemented yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
