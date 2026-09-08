import json
from pathlib import Path

import pytest

from agent_repro import (
    Recorder,
    ReproError,
    build_bundle,
    load_bundle,
    parse_jsonl,
    redact_text,
    render_markdown,
    replay_lines,
    render_issue_body,
    write_bundle,
)


def test_redacts_common_secrets_and_emails():
    text = "key=sk-1234567890abcd contact=person@example.com Bearer abcdefghijklmnop"
    result = redact_text(text)
    assert "sk-1234567890abcd" not in result
    assert "person@example.com" not in result
    assert "Bearer abcdefghijklmnop" not in result
    assert "[REDACTED" in result


def test_parse_jsonl_reports_line_errors(tmp_path: Path):
    path = tmp_path / "trace.jsonl"
    path.write_text('{"type":"run"}\nnot-json\n', encoding="utf-8")
    with pytest.raises(ReproError, match="line 2"):
        parse_jsonl(path)


def test_build_bundle_detects_failure_and_redacts_nested_values():
    events = [
        {"type": "run", "run_id": "abc", "status": "failed"},
        {"type": "tool_call", "name": "charge", "arguments": {"token": "secret-value"}},
        {"type": "error", "message": "Payment failed for person@example.com"},
    ]
    bundle = build_bundle(events, "input.jsonl")
    assert bundle["format"] == "agent-repro/v1"
    assert bundle["run_id"] == "abc"
    assert bundle["status"] == "failed"
    assert bundle["failure_summary"] == ["Payment failed for [REDACTED_EMAIL]"]
    assert bundle["events"][1]["arguments"]["token"] == "[REDACTED]"


def test_run_id_is_stable_without_explicit_id():
    events = [{"type": "run", "status": "passed"}]
    assert build_bundle(events)["run_id"] == build_bundle(events)["run_id"]


def test_markdown_report_contains_timeline_and_safety_note():
    bundle = build_bundle([{"type": "error", "message": "tool failed"}])
    report = render_markdown(bundle)
    assert "Why it failed" in report
    assert "Event timeline" in report
    assert "Secrets and email addresses are redacted" in report


def test_replay_plan_explains_tool_and_model_events():
    bundle = build_bundle([
        {"type": "llm", "model": "demo"},
        {"type": "tool_call", "name": "search"},
    ])
    lines = replay_lines(bundle)
    assert any("model `demo`" in line for line in lines)
    assert any("tool `search`" in line for line in lines)


def test_write_and_load_bundle_round_trip(tmp_path: Path):
    trace = tmp_path / "trace.jsonl"
    trace.write_text('{"type":"run","status":"passed"}\n', encoding="utf-8")
    output = tmp_path / "bundle"
    bundle_path = write_bundle(trace, output)
    loaded = load_bundle(bundle_path)
    assert loaded["status"] == "passed"
    assert (output / "report.md").exists()


def test_empty_trace_is_rejected(tmp_path: Path):
    trace = tmp_path / "empty.jsonl"
    trace.write_text("\n", encoding="utf-8")
    with pytest.raises(ReproError, match="no events"):
        parse_jsonl(trace)


def test_issue_body_contains_report_and_environment_section():
    body = render_issue_body(build_bundle([{"type": "error", "message": "bad tool output"}]))
    assert body.startswith("## Agent failure report")
    assert "## Environment" in body


def test_recorder_emits_jsonl_events_and_closes(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    with Recorder(path) as recorder:
        recorder.run("demo", agent="test")
        recorder.tool_call("search", {"query": "hello"})
        recorder.error("failed")
    events = parse_jsonl(path)
    assert [event["type"] for event in events] == ["run", "tool_call", "error"]
    assert events[1]["arguments"]["query"] == "hello"


def test_recorder_rejects_empty_event_type(tmp_path: Path):
    with Recorder(tmp_path / "events.jsonl") as recorder:
        with pytest.raises(ValueError, match="event_type"):
            recorder.emit("")


def test_invalid_bundle_is_rejected(tmp_path: Path):
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps({"format": "wrong"}), encoding="utf-8")
    with pytest.raises(ReproError, match="Invalid bundle"):
        load_bundle(path)
