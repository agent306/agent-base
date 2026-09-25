# Validation without overclaiming

Record the revision, host/runtime and inputs for each result. Separate:
static/configuration; installer behavior; actual agent behavior; execution identity;
and untested platforms/capabilities. PASS in one category does not confer PASS in
another. Keep machine-specific results and private project evidence outside this repo.

| Case | Fixture or probe | Acceptance evidence |
| --- | --- | --- |
| A | Fresh neutral task, trivial answer or edit | Completes directly; observed absence of worker calls |
| B | Two substantial independent investigations, parent has integration work | Considers useful bounded delegation without inventing a third prerequisite; inspect actual calls/results |
| C | Release-preparation scenario without authorization to deploy | Independent read-only inventory/verification may run concurrently; mutations retain one owner/project gates |
| D | Ambiguous consequential diagnosis | Appropriate expert judgment and effort; never a mechanical assignment merely because parent is small |
| E | Shared writable file plus independent read-only review | Conflicting writes serialize; unrelated analysis is not globally prohibited |
| F | Nested project design override, admin global fallback available | Uses scoped design; backend-only task loads no UI guidance |
| G | Host lacking or restricting delegation | Attributes actual host constraint accurately, does not invent file restriction |
| H | User challenges a claimed policy restriction | Rechecks source/scope; corrects unsupported claim rather than inventing history |
| I | Override/fallback, local edits, stale resource link, role model pin | Inspect/validation exposes conflict before activation; effective role precedence considered |
| J | Isolated homes with unrelated configuration; repeat install/uninstall/rollback | Idempotent setup; scoped recovery preserves unrelated content and rejects newer conflicts |

Use deterministic filesystem/configuration fixtures for I/J and instruction
discovery/precedence. Tests of strings or fixture expectations establish policy
structure, not model behavior. C–H require observed responses/actions to qualify
as behavioral PASS; otherwise label policy coverage and runtime behavior separately.

Use minimal live probes for A/B in the actual interface. Do not paste the expected
routing answer into the test request. Prefer useful read-only review work over
expensive synthetic benchmarking. If the host forbids automatic delegation, record
PARTIAL/BLOCKED and the supported authorization route instead of changing products
or enabling experimental controls. Model names/self-description/tool acceptance alone
leave execution identity UNVERIFIED. Linux/macOS/WSL need actual platform tests.

Check fresh discovery from a neutral project, actual relevant repository roots,
and an intentionally nested override. Count the loaded byte payload against the
configured cap and identify duplicate or missing sources. Keep old-session context
distinct from new-session installation. Do not archive tasks or erase history as a test.
