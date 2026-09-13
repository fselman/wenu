# Deterministic comet discovery (Milestone 50A.5D.1A)

**Status:** Accepted by Fernando on 2026-09-13

**Base:** `0acfa260f9f2dac8bc50ee02008dff6e1819077f`

## Scope

The installed `wenu_retrieve_comets START STOP` command performs one explicit
network query against the NASA/JPL SBDB Query API. It selects comet solutions
whose perihelion falls within the two complete inclusive UTC civil days and
whose perihelion distance is at most 5 au by default. This is a perihelion
filter, not a visibility forecast.

`START` becomes 00:00:00 UTC and `STOP` becomes 23:59:59.999999 UTC. Both
boundaries are converted to JD TDB before constructing the provider's
inclusive `tp|RG` constraint. The explicit `q|LE` constraint carries the
selected `--max-perihelion-distance` value.

This bounded slice supplies table and JSON output. It does not implement
`--observer-location`, model apparent magnitude, comet acquisition, chart
preflight, reports, or any chart/runtime integration. Fernando agreed on
2026-09-13 to defer the observer-dependent Horizons query and its sampling
policy to a separately reviewed 50A.5D.1B.

## Ownership

- `comet_discovery.py` owns query construction, typed provider rows,
  time-scale conversion, schema validation, deterministic sorting, and exact
  raw-response provenance;
- `cli/comets.py` owns only command parsing and table/JSON publication;
- `wenu_retrieve_comets` is an explicit network command and is never imported
  or called by chart construction or rendering;
- `tests/test_comet_discovery.py` owns the new provider-query, parser,
  provenance, and serialization boundary without repeating orbital or chart
  tests.

## Data contract

The request fixes the complete ordered output field list, `sb-kind=c`, full
precision, `tp,pdes` provider sorting, and explicit JSON field constraints.
The response must carry the accepted SBDB Query API signature and the exact
requested schema. Every row must be a numbered or unnumbered comet.

The immutable result retains the UTC input interval, perihelion bound,
retrieval instant, provider identity/version, exact request parameters,
SHA-256 of the raw response, and typed rows. Missing provider values remain
`None` internally and `unknown` in the human table. The table includes a
short `Header key` defining every acronym, orbital symbol, provider code, and
unit used by its columns. The `1st obs.` column retains SBDB `first_obs` and is
explicitly labelled as the earliest observation used by the current orbit
solution, not necessarily the historical discovery date. JSON retains explicit
units and identifies perihelion JD/calendar values as TDB.

`M1`, `M2`, `K1`, and `K2` are labelled only as provider photometric model
parameters. No apparent magnitude is synthesized, and missing values are not
ranked.

## Failure behavior

The command fails before publication for an invalid or reversed date interval,
non-positive perihelion bound, invalid JSON, changed provider signature,
changed field schema, malformed row, non-comet row, invalid required numeric
value, or mismatch between the provider count and returned rows.

## Acceptance gates

1. syntax and focused deterministic tests using the frozen provider-schema
   response;
2. `git diff --check` and review of every changed file;
3. one deliberate live command producing table output and one JSON file;
4. human confirmation that the result is clearly a perihelion list rather
   than a visibility forecast;
5. the complete Mac test suite with pytest plugin autoload disabled.

No graphical or scientific-position output changes, so no visual chart or
PNG/PDF/SVG comparison is required for this slice.

## Acceptance

Fernando accepted the displayed table and bounded 50A.5D.1A behavior on
2026-09-13 after live SBDB verification. The accepted table includes canonical
designations, `1st obs.`, and a header key; `1st obs.` is explicitly not
claimed as the historical discovery date. The guide records the meanings of
`M1`, `M2`, `K1`, and `K2` and the standard total and nuclear magnitude
models without implementing an observer-dependent estimate.

The live September 2026 query returned `C/2025 E1` and `P/2026 N2`; the
latter's 2021 first observation demonstrated the required distinction between
`first_obs` and discovery date. Focused regression passed 123 tests, and the
complete pre-acceptance regression passed all 2,359 tests. No graphical output
changed.
