# 07 — Export a pipeline snapshot to CSV for analytics

**Situation.** Recruiting ops wants a weekly spreadsheet of the active
pipeline so they can pivot on `job_title`, `source`, and `status` in Excel or
a BI tool. You have the records in canonical JSON and need a stable CSV.

**Where the data came from.** `pipeline_snapshot.json` is four canonical
records representing a single week's open-req pipeline. Values are
illustrative (note `O'Brien` — an apostrophe that CSV must quote correctly).

**What to expect.** `export --format csv` writes a header row using a stable
union of all keys followed by one row per candidate, with proper CSV quoting.

## Run

```bash
# to stdout
atslens export demos/07-csv-for-analytics/pipeline_snapshot.json --format csv

# to a file
atslens export demos/07-csv-for-analytics/pipeline_snapshot.json \
  --format csv -o pipeline.csv
```

## How to act

Open `pipeline.csv` in your spreadsheet tool and pivot
`status` x `job_title`, or `count(*)` by `source`, to see where candidates are
stalling. Heterogeneous records still line up because the header is the union
of every key seen.
