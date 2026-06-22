# 02 — Triage a dirty extract before a migration

**Situation.** A recruiter handed you a JSON dump pulled together by hand for
a migration. Before you load it anywhere, you want a fast, machine-readable
list of exactly what is wrong so you can hand corrections back.

**Where the data came from.** `dirty_records.json` is a canonical-keyed set of
four records with deliberately planted, realistic data-entry faults:

- `C-2002` — email typed as `lena.fischer(at)example.com` (no real `@`).
- `C-2003` — impossible `applied_date` `2026-13-09` (month 13) and a
  `years_experience` of `"five"` (string, not an integer).
- the fourth record — **missing** the required `candidate_id`.

**What to expect.** `validate` exits **non-zero** and prints one problem line
per fault. With `--json` you get `{"valid": false, "problems": [...]}` you can
feed into a script.

## Run

```bash
atslens validate demos/02-bad-data-triage/dirty_records.json
echo "exit: $?"          # -> 1

atslens validate demos/02-bad-data-triage/dirty_records.json --json
```

## How to act

Send `problems` back to the data owner. Some faults self-heal: re-run with
`--normalize` to lowercase/standardize first (it will *not* fix the month-13
date, the bad integer, or the missing id — those are genuine and must be
corrected at the source).
