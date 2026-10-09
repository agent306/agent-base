# Codex adapter

User-approved role mapping, mirroring the Claude profile. Principles in the core
policy still apply.

## Roles

- **Root, GPT-6 Astra / High: orchestrator.** Plans, routes, writes worker prompts
  and plans, reviews, integrates, and owns releases and production steps. No bulk
  coding; small direct fixes stay fine under DIRECT routing.
- **GPT-6 Sol / Medium: every coding worker.** Implementation, refactors, migrations,
  tests, build and release preparation. Give it a concrete plan, files or worktree,
  invariants, acceptance checks, non-goals and escalation points; plan quality is
  the root's responsibility.
- **GPT-6 Astra / High as worker: planning only.** Read-only planning, architecture
  or diagnosis; returns a plan for Sol to implement and never edits code.
- **GPT-6 Luna:** searches, lookups, inventories, summaries, fixed-approach
  mechanical edits.
- xHigh is a bounded escalation for unresolved hard reasoning. Exclude Terra.

## Decisions

Never accept a worker's product, design, monetization or acquisition
recommendation on the user's behalf; those go to the user.

## Settings and identity

Preserve the user's selected root model and effort; files cannot switch a running
root. Before each spawn inspect the live tool schema, select model AND effort, and
check custom-role pins for conflicts. Unsupported controls require an accurate
capability report, not invented arguments. Keep selected root, requested worker
settings, effective role configuration and runtime-reported identity separate; mark
identity unverified when metadata is hidden.

Optional resources, loaded only when needed:
- Before delegation: `{{BASE}}/governance/workers.md`.
- Configuration or runtime diagnosis: `{{BASE}}/docs/runtime.md`.
- UI fallback selection: `{{BASE}}/design/README.md`, and the applicable UI/UX skill.

Project safety must stand on its own without this personal installation.
