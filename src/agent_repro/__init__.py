"""Safe, replayable failure bundles for AI agents."""

from .core import (
    ReproError,
    build_bundle,
    load_bundle,
    parse_jsonl,
    redact,
    redact_text,
    render_markdown,
    replay_lines,
    write_bundle,
)

__all__ = [
    "ReproError",
    "build_bundle",
    "load_bundle",
    "parse_jsonl",
    "redact",
    "redact_text",
    "render_markdown",
    "replay_lines",
    "write_bundle",
]

__version__ = "0.1.0"
