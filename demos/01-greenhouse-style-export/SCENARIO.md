# 01 — Import a camelCase REST export into the canonical schema

**Situation.** Your team is leaving a REST-first ATS that exports candidate
records in a flat camelCase shape (`applicantId`, `givenName`,
`emailAddress`, ...). Before loading the data anywhere else, you want it in
the neutral **canonical** schema so the rest of your tooling speaks one
vocabulary.

**Where the data came from.** `vendora_export.json` is a three-record pull
from the vendor's "Export applicants (JSON)" admin screen. It uses the
built-in `vendorA` layout's field names. All values are illustrative.

**What to expect.** Each `applicantId` becomes `candidate_id`, `givenName`
becomes `first_name`, and so on — the canonical field names from the README's
schema table.

## Run

```bash
atslens map demos/01-greenhouse-style-export/vendora_export.json \
  --from vendorA --to canonical
```

Or save it:

```bash
atslens map demos/01-greenhouse-style-export/vendora_export.json \
  --from vendorA --to canonical -o canonical_records.json
```

## How to act

Pipe the canonical output into `atslens validate` (see demo 02) before you
trust it, then `atslens export --format csv` (demo 07) for analytics or
`atslens map --to <dest>` to push it into the next system.
