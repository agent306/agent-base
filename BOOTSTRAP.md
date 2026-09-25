# Bootstrap contract for a coding agent

For "set this up", complete this process; do not guess a provider or override conflicts.

1. Detect OS, home, current agent and available tools. This installer requires
   Python 3.11+. Do not install dependencies or request administrator rights silently.
2. For Codex, identify CODEX_HOME when set; otherwise verify the actual user home
   and its .codex directory. User skills are under ~/.agents/skills.
   Use explicit --home/--codex-home only for a verified alternative or isolated test.
3. Read profiles/codex/AGENTS.md and governance/core.md. Run inspect. Inspect the
   existing instruction contents locally, config's relevant values, global skill
   names and any design or override files. Never print secrets or upload user config.
4. Classify each difference:
   - A: identical/effectively identical: reuse without replacement.
   - B: additive: merge only when unambiguous and preserving both intentions.
   - C: conflicting: STOP that installation; report existing versus proposed behavior
     and ask **keep existing / use agent-base / custom merge**. Do not overwrite.
   Independent repository preparation may continue. An ambiguous custom merge
   needs the user's specific resolution before installation.
5. Config changes concern only the keys in profiles/codex/config.toml. For an
   approved replacement use --config-resolution baseline. Keep existing conflicting
   values with --config-resolution keep (validation reports departures).
   Custom values must first be explicitly settled, then edited locally with backup;
   do not silently encode guesses into the shared baseline.
6. An existing AGENTS.md is never discarded automatically. If its requirements
   are demonstrably preserved in the baseline (A/B), pass its exact SHA-256 from
   inspect with --reviewed-instructions-sha256. For C, use that option only after
   the user's chosen resolution has been implemented. Backups retain the old file.
   An unresolved AGENTS.override.md or alternate agent.md/agents.md stops setup:
   inspect and resolve its precedence before continuing; do not delete it automatically.
   For a user choice to keep the current entry, use --keep-instructions; installation
   reports that automatic baseline activation depends on that entry's contents.
   A custom merge belongs in the provider profile only if genuinely reusable.
   Otherwise back up and manually merge the user entry with an explicit reference
   to the linked provider entry plus resolved personal instructions, then use
   --keep-instructions. No automatic semantic merge or ambiguous precedence.
7. Setup preflights all conflicts before any writes, backs up replaced files, links
   the repository and selected skill, installs the loader, and merges only selected
   TOML scalar keys. It preserves unrelated comments, settings and secrets.
   It also installs the three `agent-base-*.toml` model-role files in CODEX_HOME/agents.
   Role updates require identical content or a match to the previous managed hash;
   locally edited, linked or colliding role files stop setup before any writes.
   Existing custom agents outside these names are not modified.
8. Run validate and inspect the resulting links and defaults. Report any limitations.
   New sessions load changes; this does not switch the running root model.

## Platform behavior

- macOS/Linux: directory symlinks for the baseline and skill; AGENTS.md symlinks
  to the provider entry point.
- Windows: directory junctions for baseline and skill; a tiny regular AGENTS.md
  loader reads the linked provider entry point. This is an intentional native
  adapter, not a copied policy. Git changes to the linked policy remain authoritative.
  config.toml remains an ordinary locally owned file with narrowly merged values.
- If links/junctions are impossible, setup fails visibly. A user may explicitly
  choose --copy. That mode is a managed snapshot, **not automatically synchronized**;
  validate detects drift. For refresh, inspect and back up the exact old snapshots,
  move those snapshots aside after conflict approval, then rerun setup --copy.
  The installer deliberately refuses to recursively replace an occupied snapshot.
  Never silently switch to copy mode.
- Backups and installation state live inside CODEX_HOME/agent-base-backups and
  CODEX_HOME/agent-base-install.json, never inside this repository.
- Do not recursively remove an existing link target, unrelated skill, config tree
  or unknown file. Existing conflicting links/skills require deliberate resolution.

## Other coding agents

Only Codex currently has a provider adapter. When the current agent is another
provider, explain that governance/design/the UI skill are provider-neutral and
can be used after its supported instruction/skill paths are confirmed. Ask what
models replace the high-judgment, normal-implementation and bounded-mechanical
roles (currently Astra/Sol/Luna) and which reasoning levels exist. Do not install
Codex config into that provider. Create its profile only after those answers and
official path/capability verification. No speculative provider folders/mappings.

## Safe updates

Use a clean checkout and review incoming changes to this security-sensitive repo.
The update command fetches first and shows the diff; it does not pull without
--reviewed-update <exact-upstream-SHA>. Review that exact commit, then rerun with
the SHA. It fast-forwards to that exact reviewed commit (fetch plus merge --ff-only)
and re-enters the reviewed installer for conflict-aware setup/validation. It does
not refetch an unreviewed newer commit during promotion. No non-fast-forward merge,
reset or force-push. An already-current checkout needs no redundant approval.
Linked instructions/skills change immediately when the checkout changes; config
scalars are reconciled by setup, so use a quiet boundary between agent sessions.

For a manual workflow: git fetch, review diff, git pull --ff-only, repository
validation, setup and installed validation. Copy mode needs explicit refresh.
Rollback by inspecting the backup and restoring only the affected paths; do not
overwrite newer local changes. Backups may contain secrets and must stay private.

## Verified documentation

[User configuration](https://learn.chatgpt.com/docs/config-file/config-basic),
[AGENTS discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[skill locations](https://developers.openai.com/codex/skills),
[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Same-named skills can both appear; precedence here is an explicit policy, not
a claim that the harness automatically merges or shadows skills.
