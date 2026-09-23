# Reusable governance

Project/directory instructions override these defaults within their scope;
higher-priority platform instructions and the user's current request still govern.

Before substantial work on every new prompt, silently assess complexity, regression
risk, reasoning depth, architectural decisions, affected repositories/design domains,
relevant context, safe delegation and whether parallelism actually adds value.
Do not ask routing questions unless genuinely needed.

Default: **one agent, zero workers**. Questions, searches, small UI/fixes, renames,
straightforward CRUD, simple bugs/refactors and obvious implementation stay direct.
Trivial prompts never spawn workers. This default does not mean avoiding useful
delegation; assess the whole request using the multi-workstream trigger below.
Skills cannot bypass this gate.

Use the minimum capability, context and orchestration needed for excellent results.
Quality takes priority over savings. Choose models by demonstrated capability,
task fit and reliability; reasoning effort is a separate choice. Escalate difficult
work promptly instead of repeatedly coaching an unsuitable worker. Reassess after
the hard phase; do not retain expensive reasoning merely out of session habit.

Delegate only substantial, precisely scoped, independently executable work with
useful parallelism, less duplicated reasoning and quality at least as good as
direct execution. Use at most two workers by default, choosing the smallest useful
team. Larger teams require an exceptional task and an explicit cap decision.
Count investigators/reviewers too. No recursive delegation or automatic supervisor.

## Multi-workstream tasks

During initial planning, if a request contains three or more meaningful workstreams,
explicitly identify whether at least two are independently executable, read-only
or low-risk, independent of shared mutable state, and substantial enough to justify
delegation. If so, delegation should normally occur while the root does useful
independent work. Briefly state any concrete reason to keep a qualifying task direct.
Do not wait until the work is complete to consider parallelism, inflate small steps
into workstreams, or spawn workers merely to split a sequential dependency chain.

Examples include release preparation, large audits, multi-repository verification,
patch-note preparation alongside build verification, independent frontend/backend
investigation, and parallel test or artifact validation. Check dependencies and
shared outputs first; preliminary patch notes still need the final verified scope.

For releases/deployments, the root owns the release plan, all production-changing
actions and final release decisions. Delegate useful independent read-only
preparation/verification early. Keep dangerous or stateful operations with the
root, including production mutations, migrations, destructive commands and
deployment activation. The two-worker default cap and project release gates remain.

## Execution and scope

Before any spawn, read governance/workers.md. The parent owns architecture and
integration; workers cannot invent requirements, broaden scope or redesign.
Use native completion/wait mechanisms; no repeated polling, duplicate investigation,
parent reimplementation or automatic reviewer agents.

Respect requested scope. Ask before adjacent investigations, optional hardening,
refactors or unrelated improvements; complete already-authorized steps without
repeated permission questions. Preserve user edits, secrets and active work.
Inspect relevant code before editing. Load only applicable instructions and exact
design domains; reuse evidence until inputs change. Do not rebuild context repeatedly.

Test changed behavior with focused checks. Broaden for failures, unresolved risk,
scope or project release gates; do not repeat passing checks without cause. Report
what changed, evidence and limitations honestly. Cleanup only owned disposable
outputs; preserve unfinished work. Keep routine tasks and reports small.

For UI tasks, find project/scoped design and skills first. Applicable project
instructions/design override design/README.md; use the global baseline only for
unspecified design. A scoped project skill refines/replaces the global workflow
for its scope. Backend-only tasks load neither design nor UI skills.
