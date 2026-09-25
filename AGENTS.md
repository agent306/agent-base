# Maintaining agent-base

This public repository contains reusable personal defaults, a Codex adapter,
shared design guidance, a UI/UX skill and installation tooling. Never commit
credentials, machine-private configuration, private project content or audit snapshots.

Read BOOTSTRAP.md for setup. This file governs repository maintenance; it is not
the installed user baseline. governance/core.md and profiles/codex/AGENTS.md are
the authoritative always-loaded sources. The installer composes them into one
global file; no nested mandatory loader. Keep their combined payload around
500–800 words. Detailed procedures belong in optional resources.

Preserve project independence and scoped design precedence. Keep provider mapping
in profiles/, generic principles in governance/, design in design/, skills
self-contained under skills/, and installer mechanics in bootstrap/.
A provider without an approved mapping requires user input, not guessed equivalents.

Before publishing, review the complete diff for private material. Preserve Git
history and unrelated edits. Run repository validation and the unittest suite.
Installer tests must use isolated homes and preserve unknown settings, links,
local edits and rollback state. Configuration PASS is not behavior PASS.
Document runtime-specific gaps honestly. Do not run model probes without a
concrete validation need or use real application/deployment mutations as fixtures.
