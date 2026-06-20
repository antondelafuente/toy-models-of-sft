# DATA_AUDIT_RESPONSE

## Finding 1 — MED format / masking

Accepted. The old masked trainer's `[^}]+` regex would stop inside nested-brace answers. Fixed in `DESIGN.md`: the run must use a balanced-brace final-box parser and the mask self-check must explicitly cover nested rows 11, 27, 46, 68, 80, 84, 132, and 145.

## Finding 2 — LOW intent wording

Accepted. Fixed in `data_audit_manifest.md`: arm `A` is not reasoning-free; it lacks the directive sentence and empty directive box.

## Finding 3 — LOW duplicate prompt strings

Accepted. Already fixed in `DESIGN.md`; reiterated in `data_audit_manifest.md`: primary metrics deduplicate exact prompt strings and full-400 continuity metrics are reported separately.
