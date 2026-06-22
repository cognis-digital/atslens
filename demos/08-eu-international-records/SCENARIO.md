# 08 — International records: day-first dates and E.164 phones

**Situation.** A European recruiting partner sends candidates whose dates are
written day-first (`DD-MM-YYYY`) and whose phones are in international
`+CC ...` form. You need these in the same canonical, ISO-dated, validated
shape as everyone else before merging them into the global pipeline.

**Where the data came from.** `eu_candidates.json` holds three canonical-keyed
records from NL / PL / ES sources. Note `applied_date` values like
`12-03-2026` (12 March, **not** December 3) and accented names like
`Sofía García`. Values are illustrative.

**What to expect.**

- Raw, the dates `12-03-2026` etc. are **not** ISO, so plain `validate`
  reports `applied_date` failures.
- With `--normalize`, the day-first dash dates are rewritten to ISO
  (`2026-03-12`), accented names are preserved, and validation passes.
- Phones already in `+CC` form normalize to a compact `+...` digit string.

## Run

```bash
# raw validation flags the day-first dates
atslens validate demos/08-eu-international-records/eu_candidates.json
echo "exit: $?"     # -> 1

# normalize-then-validate passes
atslens validate demos/08-eu-international-records/eu_candidates.json --normalize
echo "exit: $?"     # -> 0

# emit clean canonical JSON
atslens map demos/08-eu-international-records/eu_candidates.json \
  --to canonical --normalize
```

## How to act

Always `--normalize` day-first regional exports before merging — the dash form
is ambiguous to a human but `atslens` resolves it deterministically as
day-month-year. Confirm the ISO dates look right for a couple of records, then
proceed to export or onward mapping.
