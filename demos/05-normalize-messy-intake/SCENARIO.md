# 05 — Clean up inconsistent intake data with `--normalize`

**Situation.** Records came in from a careers form, a job fair, and a
recruiter's notes. Capitalization, whitespace, email case, phone punctuation,
and date formats are all over the place. You want one canonical, tidy set.

**Where the data came from.** `messy_intake.json` is three canonical-keyed
records with realistic inconsistencies (only the formatting is messy — every
value is otherwise valid):

- `I-7001` — name `"  ELENA   petrova "` (extra spaces, wrong case), uppercase
  email, US date `04/27/2026`.
- `I-7002` — hyphenated name `jean-luc`, padded email, long-form date
  `5 Mar 2026`.
- `I-7003` — `Apr 9, 2026` style date.

**What to expect.** Normalization title-cases names (preserving the hyphen in
`Jean-Luc`), lowercases/trims emails, compacts phones to a digit string
(keeping a leading `+`), and rewrites every date to ISO `YYYY-MM-DD`.

## Run

```bash
# normalize and emit canonical JSON
atslens map demos/05-normalize-messy-intake/messy_intake.json \
  --to canonical --normalize

# or normalize straight into a CSV
atslens export demos/05-normalize-messy-intake/messy_intake.json \
  --format csv --normalize
```

Prove it conforms afterward:

```bash
atslens validate demos/05-normalize-messy-intake/messy_intake.json --normalize
```

## How to act

Normalization is conservative: anything it cannot confidently parse is left
untouched so `validate` can still flag it. Treat normalize-then-validate as the
standard pre-load gate.
