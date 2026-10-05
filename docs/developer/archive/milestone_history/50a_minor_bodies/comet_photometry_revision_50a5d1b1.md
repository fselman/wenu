# Comet photometry operational revision (Milestone 50A.5D.1B.1)

**Status:** Revised contract accepted by Fernando on 2026-09-14;
implementation and operational acceptance closed by Fernando on 2026-10-05.

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
5. The default workload guard remains 50 comet requests. The user
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
9. The initial implementation used sequential calls. Fernando's broad
   270-comet trial completed successfully but established that serial latency
   and the absence of progress or reusable partial work were operational
   defects. JPL's Fair Use Policy explicitly requires one API request at a
   time, so Wenu preserves sequential access and deterministic discovery order.
   Any request failure still fails the whole result.
10. Horizons target headers may identify the selected solution with a
    provider label such as `JPL#27` or `SAO_2008`. Wenu accepts arbitrary
    non-empty source labels only when they match the SBDB orbit solution after
    the narrow documented JPL notation normalization. A per-comet parse error
    names the canonical designation that failed.
11. Interactive terminals receive a one-line progress bar on stderr with
    completed/total counts, designation, source, elapsed time, and ETA.
    `--progress` forces it and `--no-progress` suppresses it; stdout and result
    files remain clean.
12. Each validated raw response is atomically cached under
    `~/.cache/wenu/comet_photometry`, keyed by the exact endpoint and request
    parameters. A repeated or interrupted workload reuses completed entries
    with their original retrieval time and digest. `--refresh-photometry`
    deliberately replaces matching entries. Cache corruption fails closed.

## Ownership and non-goals

`comet_photometry.py` remains the correct owner because sampling policy,
Horizons transport, provider validation, and photometry provenance share one
failure lifecycle. `comet_discovery.py` remains the SBDB selection owner, and
`cli/comets.py` owns parsing and publication. No new production module or
subpackage is justified. Wenu currently has no generic Horizons client: SPK
acquisition and photometry use different API, identity, coverage, validation,
and cache contracts. A shared transport module should be admitted only when
another consumer establishes a durable common responsibility.

Concurrent requests are prohibited by the provider's Fair Use Policy and are
not an accepted acceleration mechanism. Caching avoids redundant requests;
fewer first-run requests would require a different scientific model or a new
provider capability.

This revision adds no chart integration, SPK-cache coupling, empirical
activity correction, visibility model, partial-result publication semantics,
or 50A.5D.3 moving-object report behavior.

## Closure criteria (satisfied on 2026-10-05)

- focused parser, sampling, transport, workload, CLI-error, serialization,
  and documentation tests on the exact final branch;
- the complete regression suite;
- live narrow McNaught table and JSON preservation;
- live non-JPL `C/2007 B4` / `SAO_2008` solution binding;
- live broad discovery cases demonstrating per-comet windows, deliberate
  workload authorization, no HTTP 414, and clean errors without `--debug`;
- `--debug` traceback restoration;
- clean working tree, `git diff --check`, and substantive diff inspection.

The earlier narrow acceptance was insufficient. Fernando accepted the revised
live results on 2026-10-05; [PR #121](https://github.com/fselman/wenu/pull/121)
merged at `91f7841235d4ed49b20ae6bf5d6b3e678de4e5c5`.
This closes 50A.5D.1B.1 only, not the minor-body program.

## Provider-policy recheck before live acceptance (2026-10-05)

Primary policy: <https://ssd-api.jpl.nasa.gov/doc/>; checked on 2026-10-05.
Transport reference: <https://ssd-api.jpl.nasa.gov/doc/horizons_file.html>.

The current policy requires an application-specific User-Agent containing
the product name, version, and contact information. The comet SBDB GET and
Horizons file-API POST transports now identify Wenu using its existing
package version and the public project issue URL as a contact channel.
This is confined to those two transport owners; no generic client or new
module is introduced. The closest existing test file,
`tests/test_comet_discovery.py`, adds a two-provider transport assertion for
this newly verified external-provider contract.

Sequential access, validated caching, and fail-whole behavior remain in
force. Automated calls must stop after a service failure rather than retry
repeatedly. The policy also prohibits website embedding, warns that API
formats can change, and offers no availability guarantee. This acceptance
exercise performs no redistribution of provider responses. The coordinate
guide was reviewed and remains current: headers change no scientific state,
coordinate frame, provenance quantity, or chart pipeline.

## Final acceptance evidence (2026-10-05)

Exact accepted implementation: `5b9b8e11539d2d5550c84a2dcfe86de876af2a63`.
The merge tree is identical to that tested head. The Mac focused gate passed
262 tests in 10.44 seconds and the complete suite passed 2,923 tests in
257.25 seconds. Diff and clean synchronized-tree checks passed.

- McNaught from La Ligua: table and JSON routes, 121 samples every 12 hours
  within its own ±30-day window, unchanged cache files, and preserved original
  retrieval time and raw-response digest. The solution remained JPL 27.
- The complete 2007 selection processed 214 comets with explicit workload
  limit 250: 61 samples every day per comet, exact per-perihelion windows,
  sequential POST, and identical photometry and provenance on cache reuse.
  First execution took 117 seconds; the cached execution took 7 seconds.
  C/2007 B4 remained bound to `SAO_2008`.
- The 2007–2027 discovery returned 1,516 records; workload limit 300 rejected
  the request before photometry. That interval was not a completed broad
  photometry trial. The accepted operational trial was the 214-comet year.
- Default limit 50 and explicit 1h cadence produced concise status-2 errors
  with empty stdout; the latter reported minimum usable cadence 4h.
  `--debug` restored the traceback and status 1.

The local evidence directory was `/tmp/wenu-comet-review.ZM6hp0`; it is a
transient receipt location, not an installed resource or durable archive.
The sampled provider values remain models, not continuous minima, visibility,
detectability, empirical coma brightness, or physical tail morphology.
See the [current resumption checkpoint](../../../post_v0.9_architecture_roadmap.md#current-forward-roadmap)
for reports, database/lifecycle work and final minor-body closure.
