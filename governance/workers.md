# Bounded worker contract

Use only after the core spawn gate passes. The parent determines the approach,
then supplies: exact objective; repository and owned files/components; expected
behavior; fixed architecture and constraints; behavior to preserve; explicit
non-goals; acceptance criteria; targeted tests; relevant design/instruction paths;
and evidence already established.

Tell the worker it is not alone: preserve other edits and accommodate concurrent
work. Uncovered architecture/design decisions must return to the parent; stop
rather than guess. No unrelated repositories, refactors, invented requirements,
recursive delegation or scope expansion.

Own disjoint files/worktrees. Serialize shared builds, database mutations, release
operations and cleanup. The parent does useful independent work and reviews the
actual diff and evidence, not just a summary. An extra reviewer solely for a second
opinion needs material risk; independent verification admitted by the core
multi-workstream trigger need not be high-risk. Dangerous/stateful operations
remain with the root as specified there.

Worker reports must separate completed work, checks actually run, assumptions and
remaining blockers. A spawn or message acceptance is not evidence that a worker
started, received a visible message or completed its assignment. Before relaying
worker success, inspect the relevant result and evidence; if unavailable, attribute
the report to the worker and state that it has not been independently verified.

Stop/reassign work on architectural misunderstanding, invented assumptions,
regressions, repeated constraint violations or multiple corrective prompts.
Retain valid evidence and take over or escalate directly; one focused clarification
for a small omission is reasonable. This is not a mandatory weakest-model-first ladder.

Observe task-class reliability, rework and regressions. Change future preferences
after repeated comparable evidence, not one failure. Keep compact evidence only
when it justifies a routing adjustment; avoid routine logging/benchmark probes.
