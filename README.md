# Agent-base

Private, reusable user-level defaults for coding agents. Quality comes first;
ordinary tasks use one agent, focused context and proportionate verification.

- [Set up on this device](BOOTSTRAP.md)
- [Generic governance](governance/core.md)
- [Codex adapter](profiles/codex/AGENTS.md) and [model routing](profiles/codex/routing.md)
- [Default design](design/README.md)
- [Reusable UI/UX skill](skills/ui-ux/SKILL.md)

Project instructions and applicable project design take precedence over defaults.
No application-specific architecture, names, assets or release procedures belong here.

## Commands

Requires Python 3.11+ and Git; Windows additionally uses built-in PowerShell for
directory junctions. Run from any checkout location:

```text
python bootstrap/agent_base.py inspect --provider codex
python bootstrap/agent_base.py setup --provider codex
python bootstrap/agent_base.py validate --provider codex
python bootstrap/agent_base.py update --provider codex
```

Setup stops on unresolved conflicts. See BOOTSTRAP.md for review/approval options.
Windows uses directory junctions and a small managed instruction loader without
administrator privileges; Unix uses symbolic links. Policies and skills remain
linked to this checkout. config.toml is merged, never wholly replaced or committed.
Run update after pulling to reapply reviewed scalar config defaults.

Setup also installs three model-bound roles in `~/.codex/agents/`: judgment
(Astra/High), implementation (Sol/Medium), and mechanical work (Luna/Low).
Both model and effort are validated. These small managed copies refresh during
setup/update; locally modified or colliding role files stop installation before
writes. Unrelated custom agents and user model overrides remain intact.

Keep the checkout at its installed location. Moving it requires setup against the
new location after conflict review. Backups stay in the user's config directory,
outside Git. Restart an agent session to refresh instruction/skill discovery.
