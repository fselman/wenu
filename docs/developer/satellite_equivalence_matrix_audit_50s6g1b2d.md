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

## 14. Acceptance record

Fernando scientifically and architecturally accepted this documentation-only
audit on 2026-09-17 after 159 plugin-disabled current-documentation tests
passed in 10.75 seconds; `git diff --check` and the working tree were clean at
`6e7a8b9`.

Acceptance authorizes only bounded fake-data implementation of the matrix
harness, canonical serializers, evidence validators, isolated resource
observation seam, and atomic external publication. It does not authorize
execution against the accepted real 256-record specimen, a speed claim,
50S.6G delivery, report/file interfaces, tracks, charts, illumination,
provider access, concurrency, or cache reuse.

## Candidate fake-data implementation record

The bounded 50S.6G.1B.2D fake-data implementation is present in
`satellites/crossing_matrix.py` at candidate commit `19520f3`. It implements
strict injected-route equivalence, canonical evidence, deterministic unordered
value serialization, atomic airmass admission, complete selector-partition
checks, forbidden exhaustive fallback, alternating measured route order, and
atomic publication with full manifest revalidation.

The candidate was verified on 2026-09-17 with 46 focused tests, 224 broader
implementation tests, and **2634 plugin-disabled full-suite tests passed in
230.25 seconds**. The verification used repository fake data only. No accepted real
256-record specimen was read, no real matrix was executed, and no performance
claim was established.

This candidate implementation awaits Fernando's scientific and architectural
acceptance. Acceptance may authorize only a separately bounded real-matrix
execution step; it does not itself execute that matrix or authorize later
50S.6G delivery, chart tracks, reports, illumination, provider access,
concurrency, or cache reuse.

## Accepted fake-data implementation closure

Fernando scientifically and architecturally accepted the bounded
50S.6G.1B.2D fake-data implementation on 2026-09-17. Acceptance rests on the
2634 plugin-disabled full-suite tests that passed in 230.25 seconds at
implementation commit `19520f3`, followed by 161 plugin-disabled
current-documentation tests that passed in 3.32 seconds at acceptance-record
baseline `3ef6a4d`.

This acceptance closes the fake-data implementation only. It does not authorize
reading the accepted real 256-record specimen or executing the real ten-field
matrix. Only a separately bounded real-execution audit is authorized next;
real execution, performance claims, and later 50S.6G delivery remain
unauthorized.

## Candidate real-execution readiness audit

**Finding:** not ready for real execution.

This audit inspected the accepted implementation at integrated baseline
`9bdf301` without reading the external 256-record specimen and without
executing either crossing route. The accepted `run_equivalence_matrix()`
owner correctly provides a strict orchestration and evidence boundary, but its
execution dependencies remain injected test seams. There is no approved
production path from an explicit operator command to isolated exhaustive and
accelerated route runs.

The following closure work is required before real execution can be proposed:

1. add an exact accepted-medium identity constant and validate the receipt's
   implementation identity, 24 nonempty bins, 48 mandatory representatives,
   208 fill records, and complete parent/subset/receipt binding;
2. freeze the exact ten-field La Ligua request fixture, including decimal GCRS
   centres, radii, UTC intervals, shared-interval control, coordinate metadata,
   tolerances, and a canonical request digest;
3. provide the production whole-interval airmass certifier used atomically
   before any route process starts;
4. implement a fresh-subprocess worker and executor for each route/query/run,
   with an explicit canonical input/output protocol, timeout, exit status,
   environment versions, and no cross-route object or cache reuse;
5. add the explicit offline `run-equivalence-matrix` developer command with
   required snapshot directory, output root, accepted digests, and operator
   acknowledgement—never discovery, newest-directory selection, provider
   access, refresh, or fallback;
6. extend fake-data tests to prove the production fixture, worker, command,
   timeout, subprocess isolation, receipt constraints, and fail-closed
   publication behavior.

The real execution gate remains closed until that bounded production-path
implementation is scientifically and architecturally accepted. Even then, the
first real matrix run requires separate explicit authorization and its external
evidence requires independent acceptance. This audit authorizes no specimen
read, propagation, coordinate transformation, matrix execution, performance
claim, or downstream 50S.6G delivery.

## Accepted real-execution readiness finding

Fernando scientifically and architecturally accepted the fail-closed
real-execution readiness audit on 2026-09-17 after 163 plugin-disabled
current-documentation tests passed in 3.80 seconds at `054ac39`; the
whitespace check and working tree were clean.

Acceptance confirms that the real matrix is not yet ready to run. It authorizes
only bounded fake-data implementation of the exact receipt constraints, frozen
ten-field fixture, production whole-interval airmass certifier,
fresh-subprocess route worker and protocol, explicit offline
`run-equivalence-matrix` command, and their fail-closed tests. It does not
authorize reading the accepted real specimen, executing either real route,
publishing real evidence, making a performance claim, or advancing later
50S.6G delivery.\n

## Candidate bounded production-path implementation

The dedicated candidate branch adds the exact accepted-medium receipt checks,
a digest-frozen ten-field La Ligua fixture, the production whole-interval
airmass adapter, a canonical fresh-subprocess protocol and worker, an explicit
offline `run-equivalence-matrix` command, and fake-data-only tests. Following
Fernando's 2026-09-17 direction to shorten tests, the fixture uses only 15- and
60-second intervals and the new test gate avoids repeated scientific route
runs by using bounded protocol doubles. Production policy retains one warm-up
and three measured isolated repetitions.

This candidate has not accessed the accepted real specimen and has not
executed the real matrix. It awaits focused and full-suite verification and
Fernando's scientific and architectural acceptance. Real execution, external
evidence publication, performance claims, and later delivery remain
unauthorized.\n

Candidate verification on Fernando's Mac completed at executable commit
`81f9031`: the 14-test focused matrix gate passed in 9.35 seconds, the
210-test immediate-boundary and documentation gate passed in 60.26 seconds,
and all 2,645 plugin-disabled tests passed in 243.71 seconds. `git diff
--check 5cd60fd...HEAD` and the working tree were clean. No accepted real
specimen was accessed and no real matrix was executed. The candidate still
requires Fernando's scientific and architectural acceptance.\n

### Accepted production-path implementation

Fernando scientifically and architecturally accepted the bounded fake-data
production-path implementation on 2026-09-18. The executable evidence remains
14 focused tests in 9.35 seconds, 210 immediate-boundary tests in 60.26
seconds, and all 2,645 plugin-disabled tests in 243.71 seconds at `81f9031`.
After documentation-only evidence recording, 164 current-documentation tests
passed in 3.94 seconds at `602eed7`; the whitespace check and working tree
were clean.

Preserve the exact accepted-medium and receipt constraints, digest-frozen
ten-field La Ligua fixture with only 15- and 60-second intervals, production
whole-interval airmass certifier, canonical fresh-subprocess worker/executor,
explicit offline command, and shortened fake-data test practice. This
acceptance does not authorize accessing the accepted real specimen, executing
the real matrix, publishing real evidence, making a performance claim, or
advancing later delivery. Any real execution requires a separate explicit
authorization.\n

## Candidate 50S.6G.1B.2D.1 first-real-execution authorization

**Status:** Candidate documentation-only authorization audit.

The accepted production path at merge commit `e1cdec9` is complete. No
further runtime implementation is proposed before the first real execution.
This audit does not read, stat, discover, hash, copy, propagate, or otherwise
access the accepted external specimen and does not execute a matrix worker.

Acceptance of this audit would authorize exactly one operator-started offline
run against the already accepted 256-record medium specimen. It would not
authorize a retry, a second run, another specimen, provider access, refresh,
substitution, packaging, concurrency, cache reuse, changed fixture, changed
policy, or downstream delivery.

### Frozen identities and command

The run must use only:

- medium canonical SHA-256
  `2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`;
- selection-receipt SHA-256
  `1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`;
- parent canonical SHA-256
  `e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`;
- acknowledgement
  `I_ACKNOWLEDGE_THE_EXPLICIT_OFFLINE_REAL_MATRIX_RUN`;
- the accepted digest-frozen ten-field La Ligua fixture, containing only
  15- and 60-second intervals;
- one explicit absolute snapshot directory and one distinct explicit absolute
  output root supplied by Fernando after audit acceptance.

The only authorized command is the installed repository developer command:

```bash
python tools/build_satellite_snapshot.py run-equivalence-matrix \
  --snapshot-directory <EXACT-ACCEPTED-MEDIUM-DIRECTORY> \
  --output-root <NEW-EMPTY-EXTERNAL-OUTPUT-ROOT> \
  --accept-medium-sha256 2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b \
  --accept-receipt-sha256 1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895 \
  --accept-parent-sha256 e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347 \
  --acknowledgement I_ACKNOWLEDGE_THE_EXPLICIT_OFFLINE_REAL_MATRIX_RUN
```

The placeholders are audit notation, not commands for Fernando to compose.
After acceptance, the assistant must resolve both exact absolute Mac paths and
provide the complete copy-and-paste-ready command. Neither path may be inside
the Git repository, a package directory, or an existing evidence directory.
The output root must be new and empty.

### Operational preflight and limits

Before the one authorized command, verify without changing the specimen:

1. the Mac is on the integrated audit branch at `e1cdec9` or an accepted
   documentation-only descendant, with a clean working tree;
2. the explicit snapshot and output paths are absolute, distinct, external to
   the repository, non-symlink paths, and the output root is new and empty;
3. at least 2 GiB are free on the output filesystem;
4. no prior matrix process is running;
5. automatic network access remains absent and no provider credential,
   response, or refresh path is supplied.

The accepted policy schedules 10 fields, two routes, one warm-up and three
measured repetitions: at most 80 fresh subprocess invocations. The existing
worker timeout remains 3600 seconds per subprocess. There is no automatic
retry and no outer performance deadline. Fernando may interrupt the run; an
interrupted or failed run is not evidence and authorizes no restart. A retry
requires a new explicit authorization after the failure is inspected.

### Fail-closed execution and publication

Any identity, receipt, manifest, airmass, propagation, transformation,
selector, convergence, subprocess, timeout, equality, digest, staging, or
publication failure stops the run. Do not weaken the command, change a
timeout, omit a field, reduce repetitions, switch routes, or resume from
partial state. A failure directory or console output is diagnostic only.

Success means exactly one new content-addressed directory beneath the empty
output root. Do not move, rename, edit, compress, upload, publish, or place it
in the repository. Do not delete the accepted specimen or successful evidence.

### Independent evidence review

A successful command does not itself accept the evidence. Before any speed,
capacity, delivery, or scientific conclusion, a separate review must verify:

- the complete manifest and every bound file digest;
- exact ordered exhaustive/accelerated Python and canonical-result equality;
- complete selector partitions, zero fallback, and no rejected exhaustive
  crossing;
- the accepted snapshot, receipt, request-fixture, implementation, environment,
  and isolation identities;
- all raw resource observations and the absence of path leakage;
- the explicit non-claim that timings and allocations are descriptive only.

The review may accept or reject the exact external evidence directory. It may
not generalize performance, authorize another run, or begin later 50S.6G
delivery without a separately accepted milestone.

Acceptance criteria for this audit are therefore narrow: one exact offline
run, one accepted specimen, one new empty output root, no retry, fail-closed
publication, and separate evidence acceptance. Until Fernando explicitly
accepts this audit, real specimen access and real matrix execution remain
unauthorized.\n

### Accepted first-real-execution authorization

Fernando scientifically and architecturally accepted 50S.6G.1B.2D.1 on
2026-09-18 after all 165 plugin-disabled current-documentation tests passed in
5.07 seconds at `af8044a`; the whitespace check and working tree were clean.

This acceptance authorizes exactly one operator-started offline execution
against the exact accepted 256-record medium, using the three frozen digests,
exact acknowledgement, accepted ten-field 15/60-second fixture, one new empty
external output root with at least 2 GiB free, the existing 3600-second
per-subprocess timeout, and no retry or resume. It does not itself start the
run. The exact absolute Mac paths must be resolved before the command is
issued. Failure or interruption authorizes no restart. Successful evidence
remains external and unaccepted pending an independent review; no performance
claim or later 50S.6G delivery is authorized.\n

## Candidate parent-process matrix progress display

Fernando requested a progress bar before the first real run. The authorized
execution has not started. This candidate changes only parent-process terminal
reporting: before each worker it displays the current field, route, warm-up or
measured repetition, completed count, declared total, and integer percentage;
after successful return it advances the completed count. Failure leaves the
scientific operation fail-closed and prints a terminal failed state.

The default accepted policy derives exactly 80 invocations from the frozen 10
fields, two routes, one warm-up, and three measured repetitions. The display
has no third-party dependency, is written to the parent standard-error stream,
does not enter the worker request or response, and is excluded from canonical
scientific evidence, digests, timing, and resource observations. It changes no
fixture, route order, timeout, retry policy, subprocess isolation, result,
selector, publication, or coordinate behavior.

The closest existing protocol test is extended with an in-memory stream and
the existing fake subprocess; no additional scientific route is run. The
previously accepted one-run authorization remains unconsumed but is paused.
The real specimen must not be accessed and the real run must not begin until
this candidate is verified, accepted, merged, and the one-run authorization is
explicitly renewed for the resulting integrated commit.

## Candidate 50S.6G.1B.2D.2 verification record

Fernando verified candidate commit `b0b4432` on macOS on 2026-09-18. The focused compile and gate completed with **180 plugin-disabled tests passing in 5.44 seconds**; the complete plugin-disabled suite completed with **2647 tests passing in 239.53 seconds**. `git diff --check 5aff265...HEAD` reported no errors and the working tree was clean. The coordinate-system guide was reviewed and remains current because this parent-process progress display changes no coordinate, scientific, worker-protocol, canonical-evidence, timing, or selection semantics. The accepted real specimen was not accessed and the authorized execution has not started. This is candidate verification evidence only; acceptance, merge, and renewed authorization remain separate decisions.

## Accepted 50S.6G.1B.2D.2 progress-display closure

Fernando scientifically and architecturally accepted the parent-process progress display on 2026-09-18 at candidate commit `96b9ba0`. Acceptance relies on the recorded candidate verification: 180 focused plugin-disabled tests passed in 5.44 seconds, the complete 2647-test plugin-disabled suite passed in 239.53 seconds, the final 167-test documentation gate passed in 4.22 seconds, and `git diff --check 5aff265...HEAD` reported no errors. This closes the bounded progress-display change only. It does not merge the feature branch, access the real specimen, start the matrix, or renew the single-run authorization.

## Renewed 50S.6G.1B.2D.3 one-run authorization

On 2026-09-18, after merge commit `9c4b808` installed the accepted parent-process progress display, Fernando explicitly stated: **“renew authorization for exactly one real matrix run.”** This renews authority for exactly one operator-started offline execution against the accepted immutable 256-record specimen and one new empty external output root. The run remains fixed at exactly 10 fields, only 15- and 60-second intervals, exhaustive and batch routes, one unreported warm-up plus three measured repetitions, and at most 80 fresh subprocess invocations with the existing 3600-second timeout per subprocess. The progress display is parent-process stderr only and excluded from canonical evidence. There is no automatic retry or resume: interruption, failure, or an already-created output root consumes this authorization and requires a new explicit decision. Success produces candidate evidence requiring independent review and does not itself establish equivalence or performance acceptance.

## Accepted 50S.6G.1B.2D.3 renewed authorization

Fernando scientifically and architecturally accepted the renewed one-run authorization record on 2026-09-18 at candidate commit `dd71e01`. Acceptance is supported by 169 plugin-disabled documentation tests passing in 4.29 seconds, a clean `git diff --check 9c4b808...HEAD`, and a clean working tree. This accepts the record and bounded run policy only; the run remains unstarted and unconsumed. Execution may begin only after this record is merged into the integration branch and the external preflight reconfirms the accepted specimen, a new output path, sufficient storage, and no running matrix process.

## Candidate 50S.6G.1B.2D.4 first real-matrix evidence

The single authorized offline run completed successfully on 2026-09-18 from integration commit `9d93113`; the authorization is consumed and no retry or second run is authorized. The immutable external result directory is named by equivalence-report SHA-256 `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258`; the matrix-manifest SHA-256 is `0cad196ea850a26d7cb5a2b73e73d932f06b2ae1ba2e36d745a1c3f1b2beb26c`. Independent read-only review confirmed canonical bytes and manifest/report linkage for all eight evidence files, exactly 10 fields, 60 measured observations split 30 exhaustive and 30 accelerated, three measured repetitions per field and route, and exact whole-matrix result-file equality at SHA-256 `64b5b4f99ca09fc78cdabb4a487382425317bacf71075825d40b3f28d4adee72`.

All equivalence flags are true; fallback count and rejected-exhaustive-crossing count are zero. Across 2,560 field–satellite decisions, totals are 2,455 reject, 101 indeterminate, and 4 retain. All 10 fields produced zero crossings. Therefore this real specimen verifies deterministic empty-result equivalence and conservative partition integrity, but it does not exercise a positive real crossing; positive-crossing behavior remains covered by synthetic evidence and must not be inferred from this run.

The 30 measured exhaustive observations totaled 38,292.318 wall seconds with a 1,268.734-second median; the 30 accelerated observations totaled 13,636.603 wall seconds with a 452.385-second median. Per-field median ratios ranged from 2.694 to 2.865, with acceleration faster in every field. These isolated observations describe this 2017 Intel Mac, exact specimen, and run only; they make no universal speed, capacity, memory, or hardware claim. The evidence is a candidate pending Fernando's scientific and architectural acceptance.
