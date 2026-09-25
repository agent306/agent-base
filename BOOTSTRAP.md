# Setup, update and recovery

For “set this up,” complete inspection, approved installation and verification.
Do not assume a CLI on PATH is the host serving the conversation.

## Inspect

Verify OS/native versus WSL, home, CODEX_HOME, provider, runtime version and supported
model/effort/tool controls. Python3.11+ is required. Use the existing stable user-owned
checkout when valid; otherwise clone this repository to a durable user-controlled
location. Never use a temporary checkout as the authoritative installation.

Read core and Codex adapter, then run:

```text
python bootstrap/agent_base.py inspect --provider codex
python bootstrap/agent_base.py validate --repo-only
python -m unittest discover -s tests
```

Inspect the relevant global/project instruction chain, overrides, fallbacks,
profiles, role pins, applicable skills and links. Do not print or upload credentials.
An inspection report cannot reveal every protected runtime instruction.

Identical content needs no replacement. Unambiguous additions may be merged.
For genuine behavioral conflicts or locally edited managed files, show the scoped
difference and obtain keep existing / use baseline / custom merge. Known replacement
of the owned baseline is preauthorized by a replacement request; do not ask per file.
Do not delete other providers, sessions, caches, authentication or unrelated skills.

## Install

For changes to existing files, request or reuse one explicitly authorized private
snapshot outside all instruction/skill discovery paths. The installer accepts a
snapshot directory; keep it out of this repository. Preserve it for rollback as
requested by the user. Do not create extra nonproduction backups by habit.

```text
python bootstrap/agent_base.py setup --provider codex --snapshot <private-directory>
python bootstrap/agent_base.py validate --provider codex
```

Use `--config-resolution baseline` only for an approved conflicting scalar replacement;
`keep` retains the chosen departure and must be reported. A genuinely custom
instruction replacement requires its reviewed hash and resolved content, not a blind
overwrite. See `--help` for the current exact conflict-review controls.

Only selected scalar defaults are merged into config.toml. Unrelated settings,
comments and integrations remain. Never link the entire config directory or replace
the entire config file. Old manifest-owned global role copies are retired only
after hash/ownership validation. Project roles are not global installer property.

The generated global AGENTS.md contains the core plus adapter directly. Optional
paths resolve to the installation's stable resource directory. Windows directory
junctions and Unix directory symlinks connect that resource directory and the shared
skill to the checkout; the global instruction file is an ordinary managed file.
File links are not directory junctions.

If links are unavailable, explicitly choose the managed-copy mode `--copy`.
Copies require setup/update with `--refresh-copy`; they never silently follow Git changes.
Validation checks content drift. The installer must stop on unowned occupied paths,
stale links or local modifications rather than recursively deleting targets.

## Update

Inspect dirty state and review the exact incoming revision in isolated staging.
Run validation/tests there before activating it. At a safe checkpoint between shared
operations, fast-forward the stable checkout to the reviewed commit, then run:

```text
python bootstrap/agent_base.py update --provider codex --reviewed-revision <full-SHA> --snapshot <private-directory>
python bootstrap/agent_base.py validate --provider codex
```

The update command validates the reviewed current checkout; it does not fetch or
execute newly pulled code. Review the installer itself before running it.
Linked optional resources change with the stable checkout, so do not pull it during
active work relying on them. Regenerate the global payload and copy installations.
Do not reset unrelated dirty work. Confirm installed revision and remote SHA separately.

## Uninstall and rollback

```text
python bootstrap/agent_base.py uninstall --provider codex --snapshot <private-directory>
python bootstrap/agent_base.py rollback --provider codex --snapshot <private-directory>
```

Uninstall deactivates owned baseline resources while preserving unrelated
configuration and locally edited content. Rollback restores the recorded prior
installation and managed values, refusing conflicts with newer edits.
If edited resources remain, uninstall reports PARTIAL with exit code 2 and retains
their ownership/recovery manifest. Move the kept resource outside discovery or
resolve it back to the installed content, then rerun uninstall. Setup and validation
reject partial deactivation; unrelated settings changed afterward remain preserved.
Neither operation deletes the authoritative checkout or follows a link into its
target for recursive deletion. Recovery is scoped, not a home-directory restore.
Snapshot content may include private configuration; never publish it.

File/link rollback does not rewind a linked Git checkout. When the command reports
SOURCE ROLLBACK REQUIRED, use the recorded prior revision and repository snapshot
to review a separate source rollback while preserving local edits, then validate
that installation with its corresponding installer. Never call restored loader
bytes proof that the old policy is active while its checkout is still new.

## Verify the interface actually used

Start a fresh session after cutover; the existing conversation retains old injected
instructions. Check neutral-project discovery, relevant project roots and an intentional
nested override. Run harmless trivial and substantial-work probes without supplying
their desired routing answers. See docs/validation.md for evidence categories.

A CLI-only result does not prove desktop behavior. Report hidden execution identity
as UNVERIFIED and unavailable platforms as UNTESTED. No install can guarantee model
compliance. Do not launch real application changes, deployments or migrations as tests.

## Another provider or device

Install separately on each device. If no approved provider profile exists, inspect
its official supported instruction/skill/configuration mechanisms and ask for the
model/effort mapping. Do not invent equivalents or copy Codex config into it.
Provider-neutral principles, design and the skill can be reused after that mapping.
