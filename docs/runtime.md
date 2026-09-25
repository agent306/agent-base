# Runtime diagnosis

Inspect the actual host, executable/version, OS, user home, CODEX_HOME, active
project, configuration profiles/launch overrides, tool schema, permissions and
advertised models/efforts. A CLI on PATH may differ from the desktop engine.
Do not infer subscription behavior from API/SDK documentation or pricing.

Trace global AGENTS.override.md before AGENTS.md, project root through the current
directory, then selected fallback filenames. Inspect the configured byte limit
(default documented as 32 KiB). A nearer scope takes precedence; an override can
replace a same-directory file. Follow explicitly referenced optional files only
when applicable. Existing conversations retain already injected context: use a
fresh session after cutover, not claims of retroactive reload.

Inspect custom agents in user/project supported agent directories. The documented
custom-role model/effort pins take precedence over resolved explicit spawn/default
values. Explicit spawn values otherwise precede agent defaults and parent settings.
Check the current runtime because schemas change. This baseline installs no custom
roles; it selects appropriate models per assignment. Project roles remain project-owned.

Supported defaults live in profiles/codex/config.toml. The concurrency cap excludes
the primary. No experimental flags are needed by this baseline. The prose prohibition
on recursive delegation complements the supported concurrent-worker cap.
A runtime may still limit delegation. Attribute such restrictions to the host at a
disclosable level, not an invented AGENTS.md rule.

Use inspect before setup/update. Its report can identify local contradictions but
cannot enumerate protected runtime policy. Unrelated MCP/plugin instructions are
not owned by this installer. Audit applicable skill/plugin guidance selectively;
do not remove integrations to simplify a report.

Official references (consulted 2026-09-25; check again for another runtime):
- [Instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents and role precedence](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
- [Skill discovery and duplicate names](https://learn.chatgpt.com/docs/build-skills)

Verification reports separate static/configuration checks, installer behavior, actual
agent behavior, execution identity, and untested platforms. A successful worker
request without execution metadata leaves identity UNVERIFIED. A host-blocked route
is PARTIAL/BLOCKED. No finite test promises flawless future behavior.
