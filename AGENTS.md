# Agent-base repository instructions

This private repository owns reusable user-level agent policy, design defaults,
skills and provider adapters. It contains no application implementation.

For "set this up", read BOOTSTRAP.md and inspect before installing. Do not treat
this repository file as the user's global AGENTS; that entry point is
profiles/codex/AGENTS.md. Keep provider-specific model/configuration in profiles/.
Keep generic governance in governance/, design defaults in design/, and skills
self-contained under skills/. Never import project names, assets or internals.

For changes: preserve conflict detection, backups and unknown user settings.
Validate with `python bootstrap/agent_base.py validate --repo-only` and
`python -m unittest discover -s tests`. No runtime provider/model probes unless
explicitly authorized or materially useful. Keep this repository private.
