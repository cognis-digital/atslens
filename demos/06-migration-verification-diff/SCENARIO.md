# 06 — Verify a migration with `diff` (NEW)

**Situation.** You migrated candidates from your old system into a new ATS that
uses the `vendorB` layout. Before you sign off, you want proof that every
candidate carried over and that no field was silently dropped or mangled.

**Where the data came from.**

- `before_canonical.json` — your pre-migration baseline (3 records, canonical
  schema).
- `after_vendorb.json` — what the **new** system exports afterward, in its own
  `vendorB` field names (`cand_ref`, `stage`, `contact_phone`, ...). It was
  hand-assembled to contain three realistic post-migration outcomes:
  - `M-9002` — `status` advanced `screen` -> `onsite` (a legitimate change
    that happened during the migration window).
  - `M-9003` — `phone` is **missing** (a real data-loss bug to catch).
  - `M-9004` — a brand-new candidate added after the baseline snapshot.

**What to expect.** `diff` translates the `after` side from `vendorB` into
canonical names (via `--from-after`), aligns both sides on `candidate_id`, and
reports added / removed / changed candidates. It exits **non-zero** because the
sets differ — exactly what you want a CI gate to catch.

## Run

```bash
atslens diff \
  demos/06-migration-verification-diff/before_canonical.json \
  demos/06-migration-verification-diff/after_vendorb.json \
  --from-after vendorB
echo "exit: $?"     # -> 1 (differences found)

# machine-readable
atslens diff \
  demos/06-migration-verification-diff/before_canonical.json \
  demos/06-migration-verification-diff/after_vendorb.json \
  --from-after vendorB --json
```

Expected human output (abridged):

```
DIFFERENCES: 3 -> 4 record(s) (added 1, removed 0, changed 2, unchanged 1)
  + M-9004  (only in after)
  ~ M-9002
      status: 'screen' -> 'onsite'
  ~ M-9003
      phone: '+55 11 5550 0199' -> None
```

## How to act

`M-9002` is an expected change — accept it. `M-9003` losing its phone is a
**migration defect**: re-run the export job's phone-field mapping. `M-9004`
is a new applicant, not a migration concern. A clean migration prints
`CLEAN: ...` and exits `0`.
