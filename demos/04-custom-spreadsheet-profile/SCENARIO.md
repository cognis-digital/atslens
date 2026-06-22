# 04 — Bring your own profile for a legacy spreadsheet export

**Situation.** Years of hiring data live in a spreadsheet with home-grown
column headers (`ID`, `First`, `Last`, `Role`, `Stage`, ...). None of the
built-in layouts match it, so you author a one-off **profile** that names the
columns and feed it in with `--profile`.

**Where the data came from.** `legacy_spreadsheet.json` is two rows exported
from that sheet as JSON. `spreadsheet_profile.json` is the matching profile
(the `vendorC` example layout) — it maps each spreadsheet column to a
canonical field. All values are illustrative.

**What to expect.** Mapping with `--profile` as the *source* turns `ID` into
`candidate_id`, `Role` into `job_title`, `Stage` into `status`, etc.

## Run

```bash
# spreadsheet columns -> canonical
atslens map demos/04-custom-spreadsheet-profile/legacy_spreadsheet.json \
  --profile demos/04-custom-spreadsheet-profile/spreadsheet_profile.json \
  --to canonical
```

You can also inspect the profile as a layout:

```bash
atslens layouts            # shows built-ins; your profile is data-driven
```

## How to act

Once the rows are canonical, validate (demo 02), then map them out to whatever
destination layout the new system uses. Keep the profile in version control —
it documents exactly how the legacy columns were interpreted.
