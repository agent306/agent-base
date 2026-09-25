# Codex user baseline

Locate the installed baseline at CODEX_HOME/agent-base (CODEX_HOME defaults to
the verified user's ~/.codex). Before substantive work, read its governance/core.md
once per session and apply its per-prompt routing. Project/scoped instructions
take precedence over these user defaults.

For model choice use this compact rule: GPT-6 Sol / Medium for ordinary reliable
implementation; GPT-6 Luna / Low for explicit bounded low-risk mechanical work;
GPT-6 Astra when additional judgment is justified by complexity, ambiguity,
architecture or regression risk. High/xHigh is a bounded escalation, not a whole
session default. Never use Terra. Do not infer subscription usage multipliers.

The root-session model and spawned worker model are distinct. Instructions cannot
change the current root model. Never spawn just to switch models. Before delegation
or changing settings, read agent-base/profiles/codex/routing.md and the worker contract.
Fixing worker routing does not authorize changing the main task's model/effort;
preserve it unless the user explicitly asks to change the main task's settings.
Every spawn must deliberately select a task-appropriate model and effort. With
the current spawn API, pass both explicitly with a non-full fork; never omit them
and call inheritance a routing decision. Check named-role pins before spawning.
For UI work follow core design precedence; only if project design is absent load
agent-base/design/README.md. Use the discovered ui-ux skill unless a project skill
supplies the applicable workflow. Do not load all design files or skills by default.
