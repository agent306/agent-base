# Operations UI defaults

Help an authorized person inspect state, understand consequences, make a bounded
change and verify its outcome. Keep identity, current scope and authority visible.

For desktop admin shells, a roughly 220 px sidebar, 45 px top bar and 1420 px
maximum working canvas are useful starting points, not constraints for other
products. Group navigation by actual user tasks and permission scope. Active
navigation uses a quiet fill and narrow purple rail. Search names its scope;
refresh never implies a write. Theme respects saved/system preference.

Page hierarchy: compact context label, concise title, one-sentence purpose,
permitted actions, relevant status/filters, then the primary workflow or collection.
Every metric and control must answer a real question. Tables suit comparisons;
cards suit bounded summaries/actions. Prefer continuous scrolling for collections,
preserving position and selection; project requirements may choose another pattern.

Keep record identity first, metadata subordinate, row actions nearby, full
identifiers inspectable, and sticky headers only where useful. Responsive tables
must not silently hide critical information. Forms have persistent labels, units,
ranges and consequences, grouped by decision rather than storage schema.
Safe secondary actions precede commit; destructive actions are clearly distinct.

Distinguish loading, no records, no matching results, not configured, not permitted,
pending, failure and committed success. Toggles are for immediate binary state;
high-impact changes use explicit commit actions. Prevent unsafe duplicate requests.
Do not fabricate readiness/data or show success before authoritative confirmation.

Explain save, validate, preview, stage, publish and live state distinctly when
those operations exist. Show schedule timezone/window semantics. A preview is
not proof of validation/publication. Preview content may follow its own design
while editor controls retain the operator surface's design.

Server permissions remain authoritative; UI visibility is not authorization.
Explain impact before high-consequence changes and preserve required audits.
Never expose credentials or direct privileged database access to browser code.
Show technical details only when they help the authorized audience decide/recover.

Acceptance: next action and scope are clear, consequences and authority are honest,
states are distinct, data is scannable, both themes work, and the primary journey
works without decorative styling.
