"""Command-line interface for agent-repro."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import ReproError, load_bundle, replay_lines, write_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-repro",
        description="Turn an AI-agent JSONL trace into a redacted, replayable failure bundle.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pack = subparsers.add_parser("pack", help="Redact and package a JSONL trace")
    pack.add_argument("trace", type=Path, help="Input JSONL trace")
    pack.add_argument("-o", "--output", type=Path, default=Path("agent-repro-bundle"), help="Output directory")

    report = subparsers.add_parser("report", help="Print the Markdown report from a bundle")
    report.add_argument("bundle", type=Path, help="Path to bundle.json")

    replay = subparsers.add_parser("replay", help="Print a deterministic replay plan")
    replay.add_argument("bundle", type=Path, help="Path to bundle.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "pack":
            bundle_path = write_bundle(args.trace, args.output)
            print(f"Created {bundle_path}")
            print(f"Created {args.output / 'report.md'}")
        elif args.command == "report":
            bundle = load_bundle(args.bundle)
            print((args.bundle.parent / "report.md").read_text(encoding="utf-8") if (args.bundle.parent / "report.md").exists() else "\n".join(replay_lines(bundle)))
        elif args.command == "replay":
            print("\n".join(replay_lines(load_bundle(args.bundle))))
        return 0
    except (ReproError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
