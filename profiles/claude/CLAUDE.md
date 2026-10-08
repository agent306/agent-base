# Claude Code adapter

User-approved model mapping (2026-10-08). The core principles in
`governance/core.md` still apply. This file covers the Claude-specific parts.
Install it by composing it into `~/.claude/CLAUDE.md`. There is no automated Claude
installer yet; the Codex installer does not touch Claude files.

## Roles

Set the model explicitly on every spawn with the Agent tool's `model` parameter.

- **Root, Opus: the orchestrator.**
  - It plans, routes and writes worker prompts and plans.
  - It reviews and integrates results, and owns releases and production steps.
  - It does no bulk coding itself. Small direct fixes stay fine under DIRECT routing.
- **Sonnet (`sonnet`): every coding worker.**
  - All implementation, refactors, migrations, tests and build/release preparation run on Sonnet.
  - Give it a well-designed prompt: the objective, a concrete plan, files or worktree, invariants, acceptance checks, non-goals and escalation points.
  - The quality of the plan is the root's responsibility.
- **Opus (`opus`): planning only.**
  - Use it for read-only planning, architecture, design or diagnosis when a separate planner helps.
  - It returns a plan for a Sonnet worker to implement. It never edits code.
- **Haiku (`haiku`): what it does best.**
  - Searches, lookups, inventories, log or diff summaries.
  - Fixed-approach mechanical edits that need no judgment.
- **Fable:** not used unless the user asks.

## Decisions

Never accept a worker's product, design, monetization or acquisition
recommendation on the user's behalf. Those decisions go to the user, and
overnight pre-authorization to execute does not cover them.

## Settings and identity

- Preserve the user's selected root model and effort. Files cannot switch a running session.
- The Agent tool takes `model` but no per-spawn effort. Effort comes from the agent
  definition's frontmatter or is inherited.
- Check `.claude/agents/*.md` for definitions that pin a conflicting model.
- Aliases resolve per Claude Code version. Keep these separate:
  - the requested model;
  - the configured agent model;
  - the runtime-reported identity.
  Mark identity unverified when metadata is hidden, and never claim a stronger worker
  than was requested.

## Coordination

Wait for native completion notifications instead of polling. Give workers
disjoint scopes or isolated worktrees.
