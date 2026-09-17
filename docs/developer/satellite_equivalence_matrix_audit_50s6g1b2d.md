# 50S.6G.1B.2D — Exact-equivalence and resource-matrix audit

**Status:** Candidate documentation-only audit.

## 1. Purpose and roadmap position

50S.6G.1B.2D is the evidence gate between the accepted deterministic medium
specimen and later satellite delivery work. It defines how Wenu must compare
the exhaustive local crossing oracle with the conservative accelerated oracle
on the exact accepted external specimen.

The accepted evidence inputs are:

- parent Active canonical digest
  `e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`;
- medium canonical digest
  `2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`;
- medium receipt digest
  `1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`;
- 256 records, 24 nonempty selection bins, 48 mandatory representatives, and
  208 deterministic fill records.

This audit changes no runtime and executes no matrix. It authorizes neither
reports for users, request-file ingestion, chart tracks, illumination,
concurrency, caching, a new default, nor a performance claim.

## 2. Scientific question

For each admitted query, the accelerated oracle may omit a record only when
the conservative cone-shell proof rejects it. Every retained or indeterminate
record still enters the same exact per-record solver used by the exhaustive
oracle. Therefore the primary scientific question is strict:

> Does the accelerated route return exactly the same ordered crossing results,
> byte for byte after canonical serialization, as exhaustive evaluation of all
> 256 records?

Approximate agreement, matching counts, tolerance-only matching, or agreement
after sorting away semantic differences is insufficient. The acceleration is
an optimization, not a second scientific model.

The secondary engineering question is descriptive: how many records are
rejected, retained, or indeterminate, how many enter exact solving, and what
resources are observed for each route? Resource observations do not establish
a universal speed, capacity, or memory claim.

## 3. Exact snapshot admission

A matrix run receives one explicit medium-snapshot directory and must:

1. load it through `load_snapshot_directory()`;
2. require an `ExternalSnapshotAdmission` bound to the complete accepted
   medium manifest identity and canonical digest;
3. validate `selection-receipt.json` as canonical JSON;
4. require the accepted parent, subset, and receipt digests above;
5. require 256 records, the accepted implementation identity, 24 nonempty
   bins, 48 mandatory representatives, and 208 fill records;
6. hash all three medium files before and after execution and require them to
   remain unchanged.

Directory name, newest-file discovery, a logical snapshot ID alone, or a
caller-supplied count cannot admit the specimen. There is no provider access,
refresh, fallback, catalogue merge, or artifact substitution.

A later implementation must add an explicit accepted-medium identity constant;
it must not broaden the existing CelesTrak-parent admission policy.

## 4. Matrix request contract

The accepted matrix fixture contains exactly **10 fields**. Ten is an evidence
fixture size and the current batch default, not a hardcoded public limit.
Reusable matrix code accepts an ordered nonempty tuple; future use testing may
establish separate operational bounds.

Every query uses:

- the same accepted 256-record snapshot;
- the packaged La Ligua observer: longitude -71.230289 degrees, latitude
  -32.443342 degrees, elevation 52 m;
- vacuum refraction and bundled IERS-A Earth orientation;
- a GCRS-axes, topocentric-direction, geometric field centre;
- UTC instants;
- `time_tolerance_seconds = 0.01`;
- `angular_tolerance_deg = 1e-5`;
- a closed interval no longer than 60 seconds.

The 10 queries use distinct field IDs, different field centres, and different
intervals within one UTC night. Durations deliberately cover 15, 30, 45, and
60 seconds. Field radii cover narrow and wider chart use without claiming
complete product coverage. At least one pair shares the same interval as a
research control for possible later common-interval optimization; no such
optimization is implemented or assumed here.

Field centres are generated deterministically from declared hour-angle and
declination offsets at each interval midpoint, transformed once through the
accepted coordinate chain, and frozen as canonical decimal-degree values in
the request receipt. The generation recipe, Earth-orientation evidence, exact
centres, radii, intervals, tolerances, observer, and coordinate metadata are
all receipt fields. Neither wall clock nor snapshot row order participates.

Before matrix execution, every field must pass the existing whole-interval
airmass certification at maximum airmass 2.0. Admission is atomic: if any
field, observer, interval, snapshot, coordinate contract, or airmass
certificate fails, neither oracle runs.

## 5. Compared services

For each query, the harness invokes these production services without
reimplementing their science:

- `LocalSatelliteCrossingOracle.solve(query)` for exhaustive truth;
- `AcceleratedLocalSatelliteCrossingOracle.solve_with_evidence(query)` with
  the same exact medium admission token.

Both use the same `max_evaluations_per_record = 20000`. The acceleration
policy has `max_interval_seconds = 60` and
`selector_failure_mode = "fail_closed"`. Exhaustive fallback is forbidden in
the matrix because it would test equality without exercising admitted
selection.

The matrix harness must not call private `_solve_record`, bypass admission,
alter cone-shell policy limits, suppress convergence failures, or reuse
mutable propagated states between routes.

## 6. Canonical request and result identity

A dedicated evidence owner should be
`src/wenu/satellites/crossing_matrix.py`; it must not be added to a chart,
runtime loader, or ordinary crossing API. A thin offline
`run-equivalence-matrix` developer command may extend
`tools/build_satellite_snapshot.py`.

The harness defines versioned canonical mappings for:

- the ordered request set;
- each exhaustive result;
- each accelerated result;
- each `ConeShellDecision`;
- each `AcceleratedCrossingEvidence`;
- airmass admissions;
- resource observations;
- the final equivalence report.

Mappings include every public semantic field, nested candidate identity,
observer, FoV, interval, source, solution identity, element epoch, result
instant, closest approach, range, angular rate, illumination placeholder,
provenance, and warnings. JSON uses the existing canonical UTF-8 encoding,
rejects NaN and infinity, preserves full NORAD identifiers, and preserves the
production result ordering.

For each field:

1. Python result tuples must compare equal;
2. exhaustive and accelerated canonical result bytes must be identical;
3. their SHA-256 values must be identical;
4. ordered result counts and ordered NORAD/event identities must be identical.

The complete ordered ten-field result documents must also have the same
canonical SHA-256. No tolerance is applied after the production solvers return.

## 7. Acceleration evidence invariants

Every field must produce complete `AcceleratedCrossingEvidence` bound to its
snapshot digest, field ID, and interval. The ordered reject and exact-solver
sets must be disjoint, unique, NORAD ordered, and their union must equal all
256 snapshot identifiers.

The report records per field and in total:

- reject, retain, and indeterminate counts;
- exact-solver count;
- crossing count;
- fallback flag and reason;
- decision and evidence digests.

A successful matrix requires:

- no exhaustive fallback;
- no selector or convergence exception;
- no unsupported decision;
- at least one conservative rejection and at least one exact-solver record in
  every field;
- at least one retained record and at least one indeterminate record across the
  complete matrix;
- zero exhaustive crossings belonging to a conservatively rejected record;
- exact equality of exhaustive and accelerated result documents.

An indeterminate decision is valid conservative behavior, not a failure.
A rejection that removes a real exhaustive crossing is a scientific failure.

## 8. Execution isolation and resource observations

Scientific equality is independent of timing. Resource observations are
captured in fresh subprocesses so one route cannot reuse the other route's
Python objects or caches. Each route/query pair is run three times after one
unreported warm-up. The execution schedule is deterministic and alternates
route order by field to reduce systematic first-run bias.

Each measured run records:

- monotonic wall duration;
- process CPU duration;
- peak Python allocation from `tracemalloc`;
- exit status;
- Python, Wenu, NumPy, Astropy, Skyfield, and SGP4 versions;
- operating-system and machine identity;
- matrix implementation identity;
- snapshot, request, result, and evidence digests.

Raw observations are preserved. Medians may be reported descriptively, but no
outlier deletion, significance claim, throughput extrapolation, or universal
speedup claim is allowed. Resident-set measurements are platform-dependent and
must be omitted unless a later audit defines a portable owner.

If subprocess isolation changes canonical result bytes, the matrix fails. A
timing or memory observation never excuses scientific inequality.

## 9. Atomic external evidence publication

Successful evidence is staged beside an explicit external output root,
completely revalidated, and atomically renamed beneath its final report digest:

```text
<output-root>/<equivalence-report-sha256>/
    matrix-manifest.json
    requests.json
    exhaustive-results.json
    accelerated-results.json
    acceleration-evidence.json
    airmass-admissions.json
    resource-observations.json
    equivalence-report.json
```

The final report binds every file digest, the accepted medium and receipt
digests, the exact Wenu/Git identity, policy values, route identities, run
counts, equality assertions, and resource non-claims. It contains no local
filesystem path.

Existing destinations are never overwritten. Identical destinations are fully
revalidated before reuse. Failed or interrupted runs publish no success
directory. Matrix evidence remains outside the repository, package, release
assets, and installed defaults.

## 10. Failure semantics

Any of the following fails closed and prevents success publication:

- snapshot, receipt, admission, request, observer, or airmass mismatch;
- input mutation;
- result inequality or digest mismatch;
- incomplete or malformed acceleration evidence;
- fallback to exhaustive;
- rejected record with an exhaustive crossing;
- selector, propagation, transformation, or crossing convergence error;
- subprocess failure, timeout, or nondeterministic result digest;
- canonical serialization failure;
- staging or revalidation failure.

Failure must name the field, route, repetition, and exception class when
available. Partial scientific results must not be presented as a successful
matrix.

## 11. Test ownership and staged gates

A later implementation justifies
`tests/test_satellite_crossing_matrix.py`. All implementation tests use
hand-authored fake snapshots, receipts, queries, oracle doubles, and subprocess
doubles. They must not read the accepted external specimen or run the real
matrix.

The fake-data gate must prove:

- exact admission and receipt binding before any oracle call;
- deterministic 10-field request materialization and arbitrary ordered
  nonempty request support;
- same-observer, same-night, independent-interval, and shared-interval control;
- atomic airmass admission before solving;
- complete canonical serialization;
- strict tuple, byte, per-field digest, and whole-document equality;
- complete decision partitions and forbidden fallback;
- rejected-crossing detection;
- mismatch, convergence, timeout, mutation, and nondeterminism failures;
- subprocess isolation and raw resource capture;
- staging cleanup, no overwrite, and identical-product revalidation;
- no path in evidence;
- unchanged installed synthetic default and existing APIs.

After fake-data implementation acceptance, a separate authorization is required
to run the exact real matrix. Its output then requires independent scientific
acceptance before any speed statement or later delivery work.

## 12. Coordinates and non-goals

The matrix exercises the already accepted propagation, Earth-orientation,
topocentric, FoV, airmass, exhaustive crossing, and conservative acceleration
contracts. It adds no coordinate frame, transformation, refraction model,
illumination model, orbital model, or tolerance reinterpretation.

50S.6G.1B.2D does not:

- add concurrency, state reuse, cache sharing, or common-interval optimization;
- change the default field count or impose a public maximum;
- add reports for observatories or end users;
- accept general request files;
- create track samples or draw binocular, regional, or planisphere charts;
- compute sunlight, Moon illumination, or Earth-reflected moonlight;
- access or refresh a provider;
- package the medium specimen;
- alter ordinary synthetic defaults;
- claim operational completeness or statistical representativeness.

Those remain later, separately bounded roadmap work.

## 13. Acceptance criteria

This documentation audit is acceptable only if every active authority agrees
on:

- the exact accepted medium and receipt identities;
- the 10-field same-observer, same-night matrix and its shared-interval control;
- strict result equality and canonical digest comparison;
- complete acceleration-evidence invariants and forbidden fallback;
- subprocess isolation and resource non-claims;
- atomic external evidence publication and failure semantics;
- fake-data-only implementation gates;
- the prohibition on real execution until separately authorized;
- no coordinate or downstream-delivery expansion.
