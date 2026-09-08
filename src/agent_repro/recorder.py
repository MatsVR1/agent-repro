"""Tiny adapter for emitting agent-repro JSONL events from Python code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TextIO


class Recorder:
    """Write framework-agnostic agent events to a JSONL file or stream."""

    def __init__(self, destination: str | Path | TextIO):
        self._owns_stream = not hasattr(destination, "write")
        self._stream = open(destination, "a", encoding="utf-8") if self._owns_stream else destination

    def emit(self, event_type: str, **fields: Any) -> None:
        if not event_type or not event_type.strip():
            raise ValueError("event_type must be a non-empty string")
        event = {"type": event_type, **fields}
        self._stream.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        self._stream.flush()

    def run(self, run_id: str, agent: str | None = None, **fields: Any) -> None:
        payload = {"run_id": run_id, **fields}
        if agent is not None:
            payload["agent"] = agent
        self.emit("run", **payload)

    def llm(self, model: str, prompt: str, **fields: Any) -> None:
        self.emit("llm", model=model, prompt=prompt, **fields)

    def tool_call(self, name: str, arguments: Any = None, **fields: Any) -> None:
        payload = {"name": name, **fields}
        if arguments is not None:
            payload["arguments"] = arguments
        self.emit("tool_call", **payload)

    def error(self, message: str, **fields: Any) -> None:
        self.emit("error", status="error", message=message, **fields)

    def close(self) -> None:
        if self._owns_stream:
            self._stream.close()

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
