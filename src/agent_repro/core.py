"""Core data handling for safe, replayable AI-agent failure bundles."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


class ReproError(ValueError):
    """Raised when an agent trace cannot be parsed or safely packaged."""


_SECRET_PATTERNS = (
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^\s,'\"}]+"), r"\1=[REDACTED]"),
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def redact_text(value: str) -> str:
    """Redact common credentials and email addresses from arbitrary text."""
    result = value
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return _EMAIL.sub("[REDACTED_EMAIL]", result)


def redact(value: Any) -> Any:
    """Recursively redact strings in JSON-compatible values."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        sensitive_keys = {"api_key", "apikey", "api-key", "token", "access_token", "refresh_token", "secret", "password", "passwd", "client_secret"}
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key).lower()
            result[str(key)] = "[REDACTED]" if normalized_key in sensitive_keys else redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


def parse_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Read JSON objects from a JSONL trace file with line-specific errors."""
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReproError(f"Unable to read {source}: {exc}") from exc
    events: list[dict[str, Any]] = []
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ReproError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(event, dict):
            raise ReproError(f"Line {line_number} must contain a JSON object.")
        if not isinstance(event.get("type"), str) or not event["type"].strip():
            raise ReproError(f"Line {line_number} must contain a non-empty string 'type'.")
        events.append(event)
    if not events:
        raise ReproError("The trace contains no events.")
    return events


def _event_status(events: Iterable[Mapping[str, Any]]) -> str:
    statuses = [str(event.get("status", "")).lower() for event in events]
    if any(status in {"failed", "failure", "error"} for status in statuses):
        return "failed"
    if any(str(event.get("type", "")).lower() in {"error", "exception"} for event in events):
        return "failed"
    return "passed"


def _failure_messages(events: Iterable[Mapping[str, Any]]) -> list[str]:
    messages: list[str] = []
    for event in events:
        kind = str(event.get("type", "")).lower()
        status = str(event.get("status", "")).lower()
        if kind in {"error", "exception"}:
            message = event.get("message") or event.get("error") or event.get("output") or "Unspecified failure"
            messages.append(str(message))
        elif status in {"failed", "failure", "error"}:
            message = event.get("message") or event.get("error") or event.get("output")
            if message:
                messages.append(str(message))
    return messages


def _stable_run_id(events: list[Mapping[str, Any]]) -> str:
    explicit = next((event.get("run_id") for event in events if event.get("run_id")), None)
    if explicit:
        return str(explicit)
    digest = hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]
    return f"run-{digest}"


def build_bundle(events: list[dict[str, Any]], source_name: str = "trace.jsonl") -> dict[str, Any]:
    """Build a portable, redacted bundle object from raw events."""
    if not events:
        raise ReproError("Cannot build a bundle from zero events.")
    safe_events = redact(events)
    status = _event_status(safe_events)
    failures = _failure_messages(safe_events)
    run_id = _stable_run_id(safe_events)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "format": "agent-repro/v1",
        "run_id": run_id,
        "status": status,
        "created_at": now,
        "source": source_name,
        "failure_summary": failures,
        "events": safe_events,
    }


def render_markdown(bundle: Mapping[str, Any]) -> str:
    """Render a deterministic issue-ready Markdown report."""
    status = str(bundle.get("status", "unknown")).upper()
    run_id = str(bundle.get("run_id", "unknown"))
    failures = bundle.get("failure_summary") or ["No explicit failure event was recorded."]
    events = bundle.get("events") or []
    lines = [
        f"# Agent run {run_id}",
        "",
        f"**Status:** `{status}`  ",
        f"**Bundle format:** `{bundle.get('format', 'unknown')}`  ",
        f"**Source:** `{bundle.get('source', 'unknown')}`",
        "",
        "## Why it failed",
        "",
    ]
    lines.extend(f"- {message}" for message in failures)
    lines.extend(["", "## Event timeline", "", "| # | Type | Status | Detail |", "| ---: | --- | --- | --- |"])
    for index, event in enumerate(events, start=1):
        detail = event.get("message") or event.get("name") or event.get("tool") or ""
        detail = str(detail).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {index} | `{event.get('type', '')}` | `{event.get('status', '')}` | {detail} |")
    lines.extend([
        "",
        "## Reproduction",
        "",
        "```bash",
        "agent-repro replay bundle.json",
        "```",
        "",
        "> This report was generated locally. Secrets and email addresses are redacted before the bundle is written.",
        "",
    ])
    return "\n".join(lines)


def write_bundle(input_path: str | Path, output_dir: str | Path) -> Path:
    """Package a JSONL trace into bundle.json and report.md."""
    events = parse_jsonl(input_path)
    bundle = build_bundle(events, Path(input_path).name)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    bundle_path = destination / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "report.md").write_text(render_markdown(bundle), encoding="utf-8")
    return bundle_path


def load_bundle(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReproError(f"Unable to load bundle {source}: {exc}") from exc
    if not isinstance(value, dict) or value.get("format") != "agent-repro/v1" or not isinstance(value.get("events"), list):
        raise ReproError("Invalid bundle: expected agent-repro/v1 with an events array.")
    return value


def render_issue_body(bundle: Mapping[str, Any]) -> str:
    """Render a copy-pasteable GitHub issue body with a diagnostic summary."""
    report = render_markdown(bundle)
    return "## Agent failure report\n\n" + report + "\n\n## Environment\n\n- Add agent framework and package versions here.\n- Add the command or test used to produce this bundle here.\n"


def replay_lines(bundle: Mapping[str, Any]) -> list[str]:
    """Return shell-friendly replay guidance from a bundle."""
    lines = [f"# Replay plan for {bundle.get('run_id', 'unknown')}"]
    for index, event in enumerate(bundle.get("events", []), start=1):
        kind = event.get("type", "event")
        if kind == "tool_call":
            lines.append(f"{index}. tool `{event.get('name', event.get('tool', 'unknown'))}` with redacted arguments")
        elif kind == "llm":
            lines.append(f"{index}. model `{event.get('model', 'unknown')}` prompt replay")
        else:
            lines.append(f"{index}. {kind}")
    return lines
