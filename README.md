# agent-repro

> **Turn a mysterious AI-agent failure into a safe GitHub issue in one command.**

`agent-repro` is a local-first open-source CLI and bundle format for capturing, redacting, summarizing, and replay-planning AI-agent runs. It converts a noisy JSONL trace into two portable artifacts: `bundle.json` for machines and `report.md` for humans.

The project targets a painful transition in modern AI software: agents can complete a happy-path demo, yet when they fail in production, teams often lack a safe, reproducible artifact that explains what happened. `agent-repro` does not attempt to replace an observability platform. Its deliberately narrow promise is more shareable and more useful in an incident: **package the failure so another developer can reproduce and discuss it without receiving your secrets.**

## Why this project exists

Current agent tooling is increasingly good at collecting traces, but a trace is not automatically a bug report, a regression fixture, or a safe artifact for a public issue. Developers need to know whether the agent failed, where the failure occurred, what the tool timeline looked like, and whether the evidence can be shared. The open-source core is intentionally offline and framework-agnostic, so it can sit beside LangChain, LangGraph, custom Python agents, browser agents, or a hand-written JSON logger.

## Features

| Capability | What it provides |
| --- | --- |
| Local-only packaging | Reads a JSONL trace and writes files without contacting a hosted service. |
| Secret redaction | Removes common API-key, bearer-token, password, token, and email patterns recursively. |
| Failure detection | Identifies failed statuses, error events, and exception events. |
| Stable run identity | Uses an explicit `run_id` or derives a deterministic content hash. |
| Human report | Produces an issue-ready Markdown timeline with failure messages. |
| Replay plan | Prints a deterministic sequence of model, tool, and event steps for reproduction work. |
| GitHub issue export | Creates a copy-pasteable issue body with timeline, failure summary, and environment placeholders. |
| Python recorder | Emits JSONL events from custom agents without a framework dependency. |
| Framework agnostic | Accepts simple JSON objects, so adapters can be built for any agent framework. |

## Quick start

Install from a local checkout or a future package release:

```bash
python -m pip install agent-repro
```

Package a trace:

```bash
agent-repro pack examples/failed-run.jsonl -o incident-42
```

This creates:

```text
incident-42/
├── bundle.json
└── report.md
```

Read the generated report or print a replay plan:

```bash
cat incident-42/report.md
agent-repro replay incident-42/bundle.json
agent-repro issue incident-42/bundle.json -o incident-42/github-issue.md
```

A generated report is suitable for pasting into a GitHub issue, attaching to an internal incident, or committing as a regression fixture. The bundle retains the event order and useful diagnostic fields while applying redaction before writing output.

## Input format

The input is newline-delimited JSON. Every line must be an object with a non-empty `type`. The tool is intentionally permissive about additional fields, allowing teams to start with a tiny logger and add framework-specific metadata later.

```jsonl
{"type":"run","run_id":"checkout-42","status":"failed","agent":"support-refund"}
{"type":"llm","model":"gpt-4.1-mini","prompt":"Find the refund policy","status":"ok"}
{"type":"tool_call","name":"issue_refund","arguments":{"order_id":"9911"},"status":"failed","message":"HTTP 422"}
{"type":"error","status":"error","message":"Agent selected an invalid action"}
```

The `issue` command turns the bundle into a GitHub-ready Markdown body without opening a browser or contacting GitHub. The Python adapter can instrument a custom agent in a few lines:

```python
from agent_repro import Recorder

with Recorder("run.jsonl") as trace:
    trace.run("checkout-42", agent="support-agent")
    trace.llm("your-model", "Find the refund policy")
    trace.tool_call("search_docs", {"query": "refund policy", "token": "secret"})
    trace.error("Tool returned an invalid schema")
```

The Python API is equally small:

```python
from agent_repro import build_bundle, render_markdown

bundle = build_bundle(events, source_name="production-trace.jsonl")
markdown = render_markdown(bundle)
```

## Launch kit

See [LAUNCH.md](LAUNCH.md) for a 30-second demo, a community-post draft, positioning guidance, and a staged growth plan. Read [SECURITY.md](SECURITY.md) before processing sensitive traces.

## Safety model and limitations

Redaction is conservative pattern matching, not a formal guarantee of privacy. Review the generated bundle before sharing it. Add organization-specific redaction rules before using the project with regulated or highly confidential data. The MVP does not call an LLM to explain failures, does not execute arbitrary tool calls, and does not claim that a replay plan is a fully deterministic replay engine. Those boundaries make the base tool safer and easier to audit.

## Roadmap

The most valuable next steps are framework adapters, a `pytest` regression-fixture command, configurable redaction rules, GitHub issue export, and a browser-based bundle viewer. A hosted team edition could add private retention, searchable incident history, CI regression alerts, role-based access, and integrations with Slack, GitHub, and incident-management systems without weakening the local open-source path.

## Business model

The repository is designed as an open-core funnel rather than a closed product. The free package creates adoption because developers can run it locally, inspect every generated file, and use it in CI. Revenue can come from a hosted team edition with private storage, collaboration, retention policies, and regression dashboards; paid framework adapters and enterprise support; and implementation services for companies deploying agents in production. This is a realistic path because the free artifact is useful on its own while the paid value is created by collaboration, governance, and operational scale.

There is no guarantee that a public repository will become popular or be acquired. GitHub stars are attention, not revenue. The project should earn trust by shipping useful releases, responding to issues, publishing before-and-after failure examples with synthetic data, and making the one-command workflow easy to demonstrate in a short video or README GIF.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
```

The test suite is offline and covers parsing errors, redaction, nested values, failure detection, deterministic identifiers, report generation, replay plans, and bundle round trips.

## License

MIT. See [LICENSE](LICENSE).

## Buy Me a Coffee

If `agent-repro` helps you debug an agent, you can support continued maintenance through [Buy Me a Coffee](https://www.buymeacoffee.com/yourusername). Replace `yourusername` with the maintainer’s actual handle before using this link in a public launch campaign.

## References

[1]: https://github.com/trending "GitHub Trending repositories"

[2]: https://www.reddit.com/r/AI_Agents/comments/1l7pjba/debug_ai_agents_automatically_and_improve_them/ "Reddit discussion about automatically debugging AI agents"

[3]: https://github.com/topics/agent-observability "GitHub agent-observability topic"
