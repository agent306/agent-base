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
Requests to fix delegation, routing, quality or subagent model choice do not
authorize changing the main task's model or effort. Preserve the user's root
selection unless they explicitly request that change. When messaging another
task, omit model/thinking overrides unless the user specifically authorized a
root-setting change; selecting Astra for a worker is a separate decision.

## Required selection before every spawn

After governance/core.md admits a worker, classify its actual assignment, not
just its role name or the parent's model. Apply this selection to each worker:

| Assignment | Model | Starting effort |
| --- | --- | --- |
| Explicit bounded low-risk mechanical/support work | gpt-6-luna | low |
| Bounded implementation or investigation with an established approach | gpt-6-sol | medium |
| Architecture, ambiguous cross-system failures, difficult debugging, consequential correctness/release review, or complex user-facing interaction decisions | gpt-6-astra | high |

Same-model teams are acceptable when each assignment qualifies; model variety
is not a goal. Do not label an assignment routine merely to keep the default.
An incident involving broken user state or repeated incorrect assumptions must
be reassessed for Astra before continuing the consequential decisions/review.
Reuse valid worker evidence and escalate the unresolved reasoning, not the entire
project. Do not retain high effort after the difficult phase without justification.

For the currently advertised spawn API, every request MUST include `model`,
`reasoning_effort` and `fork_turns: "none"` or a positive bounded turn count.
Omitted model/effort and full-history inheritance are not acceptable substitutes
for selection, even when the parent happens to use the desired model. Pass a
bounded contract with the context the worker needs. Example for an admitted
consequential review:

```json
{"task_name":"bounded_work","agent_type":"worker","fork_turns":"none",
 "model":"gpt-6-astra","reasoning_effort":"high",
 "message":"Exact bounded contract and required context"}
```

Check the live tool schema; omit `agent_type` when that tool does not expose it.
If a future tool cannot select the required model, inspect supported named-role
configuration or report the capability gap. Never silently substitute a weaker
model or fabricate unsupported arguments. If needed, keep independent work moving
while the affected assignment remains unresolved.

Named-role TOML can set `model` and `model_reasoning_effort`. Current official
documentation gives these file settings precedence over resolved spawn/default
values. Inspect both fields before choosing a named role; use a generic worker
with explicit controls if a pin conflicts with the assignment. Do not assume a
name such as reviewer, investigator or Astra UX identifies an execution model.
An Astra-named skill is a workflow, not evidence that Astra ran.

For project roles dedicated to consequential review or difficult judgment,
configure both model and effort and validate those pins in the project's checks.
Setup installs three globally available role files: `agent_base_judgment`
(Astra/High, read-only), `agent_base_implementation` (Sol/Medium), and
`agent_base_mechanical` (Luna/Low). Use them when the tool supports named roles
and their scope fits; otherwise use explicit model/effort controls. These roles
are configuration bindings, not extra agents that must be spawned for every task.
Keep generic defaults inexpensive; defaults are a fallback, not the task router.
Configuration checks protect named-role settings, but cannot intercept every
native spawn or guarantee that a model follows prose instructions.

Before treating a required review as satisfied, distinguish requested settings,
effective named-role configuration and any runtime-reported model. Record this
compactly in the worker contract/result when material. Do not ask a worker to
self-identify as proof. If the runtime hides identity, say what was requested and
configured rather than claiming independent execution-model verification.

A single read-only Luna/low non-full-fork spawn succeeded during setup research.
The tool accepted the override, but actual execution model/effort was not exposed.
Do not relabel this as independent identity verification or repeatedly probe workers.

The observed engine 0.155.0-alpha.16.3 exposed model/reasoning overrides despite
multi_agent_v2=false. No experimental flags are required or enabled by this
baseline. Model metadata and flags are dated observations, not permanent guarantees.

[Official subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [model controls](https://learn.chatgpt.com/docs/models).
