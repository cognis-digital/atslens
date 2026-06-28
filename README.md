# atslens

**ATS field-schema mapper & exporter for candidate-data portability.**

`atslens` helps you move candidate records between applicant-tracking systems
without lock-in. It maps records between a neutral *canonical* schema and named
vendor field layouts, validates records against a schema, normalizes fields
(names, dates, phone, email), and exports to CSV or JSON.

- Standard library only — no third-party dependencies.
- Data-driven mapping profiles: built-in `canonical` + two authored vendor
  layouts (`vendorA`, `vendorB`), plus bring-your-own via `--profile`.
- Lossless round-trips for fields shared between two layouts.

Maintainer: **Cognis Digital**
License: **COCL 1.0**

---


<!-- cognis:example:start -->
## 🔎 Example output

Real, reproducible output from the tool — runs offline:

```console
$ atslens --version
atslens 0.1.0
```

```console
$ atslens --help
usage: atslens [-h] [--version] {map,validate,export,diff,layouts} ...

ATS field-schema mapper & exporter for candidate-data portability.

positional arguments:
  {map,validate,export,diff,layouts}
    map                 remap records between field layouts
    validate            validate records against a schema
    export              export records to CSV or JSON
    diff                diff two record sets to verify a migration round-
                        tripped
    layouts             list known field layouts

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

> Blocks above are real `atslens` output — reproduce them from a clone.

**Sample result format** _(illustrative values — run on your own data for real findings):_

```
{
"candidate_data": [
    {
        "id": "1234567890",
        "name": "John Doe",
        "email": "johndoe@example.com"
    },
    {
        "id": "2345678901",
        "name": "Jane Smith",
        "email": "janesmith@example.com"
    }
]
}
```

<!-- cognis:example:end -->

## Install

Requires Python 3.10+.

```bash
python -m pip install -e ".[test]"
```

This installs the `atslens` console command.

## Concepts

A **layout** maps canonical field names to a vendor's field names. The
`canonical` layout is the identity map and is the hub through which all
remapping flows: a record is translated *source layout → canonical →
destination layout*. Fields a layout does not mention keep their canonical
names.

The **canonical schema** declares each field's type and whether it is required:

| field             | type    | required |
|-------------------|---------|----------|
| candidate_id      | string  | yes      |
| first_name        | string  | yes      |
| last_name         | string  | yes      |
| email             | email   | yes      |
| phone             | phone   | no       |
| applied_date      | date    | no       |
| job_title         | string  | no       |
| location          | string  | no       |
| years_experience  | integer | no       |
| source            | string  | no       |
| status            | string  | no       |

## Usage

### List known layouts

```bash
atslens layouts
atslens layouts --json
```

### Map records between layouts

```bash
# canonical -> vendorA (JSON to stdout)
atslens map examples/records.json --to vendorA

# vendorA -> vendorB
atslens map vendora_records.json --from vendorA --to vendorB -o out.json

# use a custom source profile
atslens map records.json --profile examples/custom_profile.json --to canonical

# normalize fields while mapping
atslens map examples/records.json --to vendorB --normalize
```

Output is JSON. (`--json` is accepted for explicitness; JSON is the default.)

### Validate records

```bash
atslens validate examples/records.json
atslens validate examples/records.json --json
atslens validate messy.json --normalize   # normalize, then validate
```

Checks required fields, types, and email/date/phone formats. **Exits non-zero**
when any record fails — handy in CI or migration scripts.

### Export records

```bash
atslens export examples/records.json --format csv -o candidates.csv
atslens export examples/records.json --format json -o candidates.json
atslens export examples/records.json --format csv --normalize
```

CSV uses a stable union-of-keys header so heterogeneous records export
predictably.

### Diff two record sets (migration verification)

```bash
# did the migration carry everything over faithfully?
atslens diff before.json after.json

# the 'after' export is in a vendor layout — translate it back first
atslens diff before_canonical.json after_vendorb.json --from-after vendorB

# machine-readable report for a CI gate
atslens diff before.json after.json --json
```

`diff` aligns both sides on `candidate_id` (override with `--key`) and reports
which candidates were **added**, **removed**, or **changed** (with per-field
`before -> after` values), plus a summary. It **exits non-zero** when the sets
differ, so it drops straight into a migration CI check. Use `--from-before` /
`--from-after` to translate either side from a vendor layout into canonical
names before comparing, and `--normalize` to compare on tidied values.

## Demos

The [`demos/`](demos) directory contains self-contained, real-use-case
walkthroughs. Each folder has an input file in the tool's real input format
plus a `SCENARIO.md` (where the data came from, the exact command, and how to
act on the output):

| demo | scenario |
|------|----------|
| [01-greenhouse-style-export](demos/01-greenhouse-style-export) | import a camelCase REST export into the canonical schema |
| [02-bad-data-triage](demos/02-bad-data-triage) | triage a dirty extract; `validate` exits non-zero with a problem list |
| [03-vendor-to-vendor-migration](demos/03-vendor-to-vendor-migration) | map `vendorA` -> `vendorB` directly, lossless round-trip |
| [04-custom-spreadsheet-profile](demos/04-custom-spreadsheet-profile) | bring-your-own `--profile` for a legacy spreadsheet |
| [05-normalize-messy-intake](demos/05-normalize-messy-intake) | clean inconsistent names/emails/phones/dates with `--normalize` |
| [06-migration-verification-diff](demos/06-migration-verification-diff) | verify a migration with `diff`; catch a dropped field |
| [07-csv-for-analytics](demos/07-csv-for-analytics) | export a pipeline snapshot to CSV for BI/pivots |
| [08-eu-international-records](demos/08-eu-international-records) | normalize day-first dates and international phones |

## Custom profiles

A profile is a small JSON file:

```json
{
  "name": "vendorC",
  "description": "Example custom profile.",
  "fields": {
    "candidate_id": "ID",
    "first_name": "First",
    "email": "Email"
  }
}
```

Only canonical fields listed under `fields` are remapped; others keep their
canonical names. See `examples/custom_profile.json`.

## Library API

```python
from atslens import (
    load_layout, load_profile, map_records,
    validate_records, normalize_records, to_csv, to_json,
    compute_diff, diff_is_clean,
)

records = [{"candidate_id": "1", "first_name": "ada", "last_name": "l",
            "email": "A@B.com"}]
problems = validate_records(records)          # [] when valid
clean = normalize_records(records)            # tidies names/email/dates/phone
vendor_a = map_records(clean, load_layout("canonical"), load_layout("vendorA"))
csv_text = to_csv(vendor_a)

report = compute_diff(records, clean)         # field-level migration diff
assert diff_is_clean(report) or report["summary"]["changed"] >= 0
```

## Development

```bash
PYTHONUTF8=1 python -m pytest        # run the test suite
```

CI (GitHub Actions, Ubuntu) installs the package and runs pytest plus a CLI
smoke test across Python 3.10–3.12.

## Scope

`atslens` is a utility for candidate-data portability and schema mapping. It
does no network I/O and stores no data of its own.
