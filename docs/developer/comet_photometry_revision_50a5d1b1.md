# Comet photometry operational revision (Milestone 50A.5D.1B.1)

**Status:** Revised contract accepted by Fernando on 2026-09-14;
implementation and operational acceptance pending.

**Exact base:** `0563a03`

## Reason for reopening

The first 50A.5D.1B implementation passed its narrow McNaught acceptance
case, but broader live use exposed three defects. A long discovery interval
also became the photometry interval, the fixed 50-comet and 367-epoch guards
escaped as tracebacks, and a legal discrete-time list could exceed practical
GET URL length and fail with HTTP 414. The earlier acceptance evidence remains
historically valid, but it is not sufficient for operational closure.

## Accepted revised contract

1. `START` and `STOP` select comet perihelia only. They do not define one
   shared photometry interval.
2. Each selected comet receives an independent UTC photometry window centered
   on its own TDB perihelion instant converted by Astropy. The default and
   currently only public policy is ±30 days around perihelion.
3. When `--magnitude-step` is omitted, Wenu selects a reproducible cadence,
   normally `1d`, and coarsens it when necessary to remain within 367
   endpoint-inclusive samples.
4. An explicit cadence is never silently changed. If it exceeds 367 samples,
   the command reports the minimum usable cadence without a traceback.
5. The default workload guard remains 50 sequential comet requests. The user
   may explicitly authorize a larger complete workload with
   `--max-photometry-comets COUNT`; Wenu must never silently truncate rows.
6. Discrete epochs use the official Horizons file API POST transport so the
   request does not depend on GET URL length. The submitted batch parameters
   and raw response remain provenance.
7. Expected validation, filesystem, network, and provider failures produce a
   concise `wenu_retrieve_comets: error:` diagnostic and status 2.
   `--debug` restores the original traceback.
8. A zero-match table says `Matched comets: 0`; JSON retains an empty
   `records` array and the declared selection/provenance.
9. Horizons calls remain sequential and any failure still fails the whole
   result. Model magnitude remains characterization, not a visibility or
   detectability forecast.

## Ownership and non-goals

`comet_photometry.py` remains the correct owner because sampling policy,
Horizons transport, provider validation, and photometry provenance share one
failure lifecycle. `comet_discovery.py` remains the SBDB selection owner, and
`cli/comets.py` owns parsing and publication. No new production module or
subpackage is justified.

This revision adds no chart integration, SPK acquisition, response cache,
empirical activity correction, visibility model, parallel provider calls,
partial-result semantics, or 50A.5D.3 moving-object report behavior.

## Required evidence before closure

- focused parser, sampling, transport, workload, CLI-error, serialization,
  and documentation tests on the exact final branch;
- the complete regression suite;
- live narrow McNaught table and JSON preservation;
- live broad discovery cases demonstrating per-comet windows, deliberate
  workload authorization, no HTTP 414, and clean errors without `--debug`;
- `--debug` traceback restoration;
- clean working tree, `git diff --check`, and substantive diff inspection.

The implementation must remain pending until Fernando accepts those live
results. PR #121 must not be merged merely because the earlier narrow
acceptance passed.
