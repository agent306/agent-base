# Agent-base

Public, reusable working defaults for coding agents. Ordinary work stays direct;
substantial work uses the smallest useful team. Quality, scope and truthful evidence
matter more than orchestration volume. This is a personal baseline, not project safety
infrastructure and not a promise of flawless model behavior.

- [Set up or update this device](BOOTSTRAP.md)
- [Provider-neutral principles](governance/core.md)
- [Codex mapping](profiles/codex/AGENTS.md) and [runtime diagnosis](docs/runtime.md)
- [Claude Code mapping](profiles/claude/CLAUDE.md): Opus orchestrates and plans, Sonnet codes, Haiku does mechanical work
- [Optional worker procedure](governance/workers.md)
- [Admin design fallback](design/README.md) and [shared UI/UX skill](skills/ui-ux/SKILL.md)
- [Validation cases and evidence levels](docs/validation.md)

The installer composes core and adapter into one global AGENTS.md (about 680 words),
without mandatory includes. Their source files remain the authority; setup/update
regenerates the installed file. Detailed resources are optional. Scoped project
instructions/design win; projects must contain their own required safeguards.

Codex roots default to Astra/High as orchestrator; Sol/Medium is every coding
worker, Astra/High workers plan read-only, and Luna handles searches and mechanical
edits (up to five concurrent workers, excluding the root; five is a ceiling, not a
target). This installation does not change a running root selection, install custom role
pins or enable experimental features. Accepted worker overrides are not proof of
execution identity. No relative subscription savings are claimed.

Python3.11+ and Git are required. Use a stable user-owned checkout, reuse a valid
existing installation, inspect conflicts, and keep recovery material private.
Each device needs its own setup; account sign-in does not synchronize these files.
Codex has an installed provider adapter. Claude Code has a user-approved model mapping
(profiles/claude/CLAUDE.md, composed into ~/.claude/CLAUDE.md by hand; no installer yet).
Other providers require verified discovery/configuration mechanisms and a user-approved model mapping.

No secrets, machine configuration, project-private documents or local audit
snapshots belong in this repository. Preserve history; publish reviewed changes
without force pushes.
