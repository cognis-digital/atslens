# 03 — Migrate directly from one vendor layout to another

**Situation.** You are consolidating two recruiting teams. Team A's ATS uses
the camelCase `vendorA` layout; the surviving system uses the snake_case
`vendorB` layout. You want to translate A's export straight into B's field
names without writing a mapping by hand.

**Where the data came from.** `source_vendora.json` is a two-record export in
`vendorA` field names (`applicantId`, `givenName`, ...). Values are
illustrative.

**What to expect.** `atslens` routes the records *vendorA -> canonical ->
vendorB*, so the output keys are `cand_ref`, `fname`, `lname`, `email_addr`,
`req_title`, `stage`, etc. — the `vendorB` names. `A-5501` lands under
`cand_ref`.

## Run

```bash
atslens map demos/03-vendor-to-vendor-migration/source_vendora.json \
  --from vendorA --to vendorB
```

Confirm it is lossless by mapping back:

```bash
atslens map demos/03-vendor-to-vendor-migration/source_vendora.json \
  --from vendorA --to vendorB -o b.json
atslens map b.json --from vendorB --to vendorA   # == the original
```

## How to act

Load the `vendorB`-keyed output through that system's bulk-import endpoint.
Any field both layouts share round-trips exactly, so you can re-export from B
and `diff` against the original (see demo 06) to prove fidelity.
