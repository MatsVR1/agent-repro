# Launch kit

## The 30-second demo

```bash
python -m pip install -e ".[test]"
agent-repro pack examples/failed-run.jsonl -o incident-42
agent-repro issue incident-42/bundle.json -o incident-42/github-issue.md
```

Open `incident-42/github-issue.md`. The output is a redacted, issue-ready report that preserves the event timeline without exposing the synthetic API key or email address in the example.

## Positioning

The memorable promise is: **“A safe GitHub issue from a failed AI-agent run, in one command.”** This is narrower than an observability platform and easier to understand in a README, a short screen recording, or a community post.

## Suggested launch sequence

Publish a short terminal recording showing the transformation from `failed-run.jsonl` to `github-issue.md`. Share the repository with a transparent explanation of what the project does not do: it does not upload traces, execute tools, or claim perfect privacy. Invite maintainers of agent frameworks to contribute small adapters that emit the JSONL format.

Next, publish synthetic failure fixtures for tool-schema errors, browser-agent timeouts, and incorrect structured outputs. Each fixture should show the input, generated issue, and a regression-test command. This gives readers a reason to clone the repository rather than only star it.

After initial feedback, prioritize integrations based on actual requests. A paid team product should only be built after users repeatedly ask for private retention, collaboration, CI alerts, or incident history. Stars are an attention signal, not proof of willingness to pay.

## Community post draft

> AI-agent failures are hard to share safely. I built `agent-repro`, a local-first CLI that turns a JSONL agent trace into a redacted `bundle.json`, a human-readable timeline, and a copy-pasteable GitHub issue. It never uploads data or executes tools. The goal is a tiny common artifact that framework authors and agent teams can use when a run fails. Feedback on the JSONL format and redaction rules is welcome.

## Commercial path

The open-source core should remain useful without an account. A hosted edition can charge for private storage, team permissions, searchable incident history, retention controls, CI regression alerts, and integrations. Paid adapters and implementation support are additional options for teams that want help instrumenting production agents.
