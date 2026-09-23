# Codex model and worker adapter

Select from models/efforts actually advertised by the current harness.
Sol normally performs implementation itself; no automatic Astra supervisor.
Luna gets only explicit, low-risk mechanical/support work. If retries look likely,
start with Sol. Astra handles meaningful architecture, ambiguity, difficult
debugging, complex permissions/state, risky migrations and consequential review.

Effort is independent: low for clear mechanical work, medium ordinarily, high
when risk/complexity warrants it; xhigh for the unresolved hard problem only.
Reassess after that phase. Do not select Max/Ultra as efficiency defaults: Ultra
can delegate automatically. Never select Terra.

No published API price or credit rate establishes relative included subscription
allowance for this account. Relative subscription weights remain unknown.

Root settings apply to ordinary NEW sessions where supported. Existing sessions
and explicit UI/CLI/project overrides may retain another model. Use real controls,
not claims that Markdown changes the running model. Do not edit global settings
or spawn a proxy worker to work around current selection without authorization.

## Heterogeneous worker mechanism

After governance/core.md admits a worker, supply an explicit contract and use a
non-full fork for an override, for example:

```json
{"task_name":"bounded_work","agent_type":"worker","fork_turns":"none",
 "model":"gpt-6-sol","reasoning_effort":"medium",
 "message":"Exact bounded contract and required context"}
```

Use Luna/low or Astra/high when the task warrants it. In the verified harness,
omitted fork_turns or "all" inherits parent model/effort and cannot take overrides.
"none" or a positive bounded turn count permits model/reasoning overrides.
Verify this schema again if the build changes; do not force unavailable controls.
Named roles may pin settings; inspect them or use an appropriate generic worker.
Explicit supported spawn settings take precedence over configured fallback values.

A single read-only Luna/low non-full-fork spawn succeeded during setup research.
The tool accepted the override, but actual execution model/effort was not exposed.
Do not relabel this as independent identity verification or repeatedly probe workers.

The observed engine 0.155.0-alpha.16.3 exposed model/reasoning overrides despite
multi_agent_v2=false. No experimental flags are required or enabled by this
baseline. Model metadata and flags are dated observations, not permanent guarantees.

[Official subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [model controls](https://learn.chatgpt.com/docs/models).
