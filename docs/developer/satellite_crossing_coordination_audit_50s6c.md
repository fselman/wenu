# 50S.6C exact-solver coordination and acceleration admission audit

**Status:** Accepted by Fernando on 2026-09-16
**Base:** accepted 50S.6B closure at merge commit `93a7d41`
**Date:** 2026-09-16

## 1. Purpose

This accepted record remains a documentation-only scientific and API audit.
This audit defines the only admissible next boundary above the accepted 50S.6B
conservative cone-shell selector. It adds no runtime coordinator, broader
selector domain, benchmark fixture, dependency, package data, CLI, report,
drawing, illumination, photometry, detector behavior, or new crossing result.

The audit resolves three questions before runtime work:

1. how an accelerated route may coordinate the accepted selector with the
   accepted exact 50S.5 solver without duplicating scientific logic;
2. what evidence is required before widening the selector beyond its installed
   three-record, 60-second domain; and
3. what benchmark evidence is required before acceleration may be enabled or
   described as useful.

## 2. Retained scientific authority

`LocalSatelliteCrossingOracle.solve(query)` remains the independently callable
exhaustive reference and scans every ordered record. The accepted
`ConservativeConeShellSelector.select(query)` remains a tri-state evidence
producer only. It returns no crossing and its `reject` decisions are meaningful
only inside its admitted domain.

A later coordinator may reduce exact work only by omitting records carrying an
accepted `reject` decision. Both `retain` and `indeterminate` must reach the
same exact per-record seam used by exhaustive solving. Selection must never
become an alternate propagation, coordinate, containment, root, minimum,
connected-visit, warning, or provenance implementation.

## 3. Proposed coordination contract

A later bounded implementation may add immutable
`AcceleratedCrossingPolicy`, `AcceleratedCrossingEvidence`, and
`AcceleratedLocalSatelliteCrossingOracle` contracts in
`src/wenu/satellites/crossing_acceleration.py`.

The coordinator would:

- accept the same immutable `LocalSatelliteCrossingQuery`;
- invoke the admitted selector once and preserve every ordered decision;
- send all retained and indeterminate full NORAD identifiers to one shared
  exact record solver owned by `crossing_oracle.py`;
- combine only exact `SatelliteCrossingResult` values;
- preserve full-NORAD/entry-instant ordering and exact warnings;
- expose selection and evaluation evidence separately from scientific results;
- fail closed if selection evidence is missing, inconsistent, duplicated,
  unordered, or does not cover the query snapshot exactly.

The exhaustive public `solve(query)` route must continue to call the shared
exact seam for every record. No public caller may supply an arbitrary subset
and label the resulting search exhaustive.

## 4. Exact seam and equivalence

The smallest acceptable refactor extracts the existing record-level numerical
operation without changing its algorithm. The seam remains private or
package-internal and continues to own accepted SGP4/topocentric evaluation,
adaptive subdivision, bracketed roots, bounded minima, tolerance connectivity,
visit construction, lower-level provenance, and convergence failure.

For every admitted query, accelerated and exhaustive routes must be exactly
equivalent in:

- result count and full satellite identity;
- entry, closest-approach, and exit instants;
- closest separation and illumination value;
- result ordering, warnings, and scientific provenance;
- propagation, observer, Earth-orientation, tolerance, and solver evidence;
- failure behavior for every record that reaches exact solving.

Additional acceleration evidence may differ. It must not be inserted in a way
that changes equality of the underlying crossing results.

## 5. Failure and fallback semantics

Selector construction, selector arithmetic, unsupported policy, unsupported
snapshot, intervals longer than the admitted maximum, insufficient range, and
unavailable bound inputs must not produce an empty search. They either yield
ordered `indeterminate` decisions or cause the coordinator to fall back to the
complete exhaustive route.

A claimed `reject` outside the selector's declared domain is an invariant
violation and must fail closed. A rejected record is never propagated by the
accelerated route, but acceptance tests must compare that omission with the
independent exhaustive oracle. Any exact-solver failure on a retained or
indeterminate record remains `SatelliteCrossingConvergenceError`; partial
results are forbidden.

## 6. Broader-domain admission

The accepted 50S.6B domain may not be widened by changing policy constants
alone. Each proposed domain extension requires immutable, digest-identified
records spanning the new regime and must record:

- snapshot identity, content digest, ordered full identifiers, source/license,
  builder identity, and creation instant;
- eccentricity, mean motion, perigee/apogee radius, drag term, epoch offset,
  and deep-space/near-Earth regime coverage;
- observer, interval lengths, field radii, pointing distribution, and exact
  IERS-A identity;
- the measured maximum ratio between sampled relative displacement and the
  proposed speed bound, with an independently chosen outward safety margin;
- deterministic adversarial cases near every policy limit;
- accelerated-versus-exhaustive zero-false-negative evidence.

Acceptance must include near-limit and just-outside-limit cases. Out-of-domain
records remain `indeterminate`; evidence from the installed synthetic snapshot
cannot justify production-catalogue admission.

## 7. Validation matrix

The later coordinator gate must include:

- all-reject, all-retain, all-indeterminate, and mixed ordered decisions;
- zero records rejected and exhaustive fallback;
- one rejected record whose exhaustive route proves no crossing;
- crossing records that selectors must retain;
- query endpoints, tangency, disconnected visits, longitude wrap, poles,
  horizon-adjacent and below-horizon geometric fields;
- invalid decision coverage, duplicate identifiers, unknown identifiers, and
  reordered decisions;
- selector exception and exact-solver convergence failure;
- equality with exhaustive results over every admitted deterministic case;
- an instrumented proof that rejected records receive zero exact evaluations
  while every retain/indeterminate record reaches the shared exact seam once.

Tests must use an independent fake selector for coordination invariants and the
real selector for scientific composition. Mocked speedup is not benchmark
evidence.

## 8. Benchmark admission

Correctness and broader-domain admission precede performance claims. Benchmark
inputs must be immutable and representative; the installed three-record
synthetic snapshot remains a composition fixture, not a useful-speed fixture.

Each benchmark record must report:

- exact repository commit, environment, Python and dependency versions;
- machine and operating-system identity;
- snapshot digest and record count;
- observer, inclusive interval, field radius, pointing distribution, and
  warm-up policy;
- reject/retain/indeterminate counts;
- exact SGP4/topocentric evaluations avoided and performed;
- selector, exact-solver, and total wall time;
- exhaustive and accelerated distributions over repeated cold and warm runs;
- median, dispersion, speedup, and peak memory.

A performance claim is admissible only when total accelerated wall time improves
materially on a predeclared representative workload without any result or
failure-semantic difference. Selector-only timing, a single run, or a workload
chosen after measurement is insufficient. Until such evidence is accepted, an
accelerated coordinator must remain opt-in and the exhaustive route remains the
default.

## 9. Stage and policy restrictions

A later coordinator may compose only the accepted 50S.6B cone-shell selector.
This audit does not authorize phase/reachable-arc rejection, coarse vectorized
propagation, HEALPix/time indexing, horizon or Earth-occultation rejection,
automatic policy tuning, live provider data, or a mutable benchmark cache.

Selector versions and policy values must appear in immutable evidence. A future
stage must earn separate scientific, zero-false-negative, equivalence, and
benchmark admission before composition.

## 10. Ownership

- `crossing_oracle.py` retains all exact numerical and crossing-result
  ownership, including the shared record seam;
- `crossing_acceleration.py` may later own coordinator policy, selector
  composition, ordered decision validation, evaluation accounting, fallback,
  and acceleration evidence;
- `tests/test_satellite_crossing_oracle.py` remains the independent exact
  numerical oracle suite;
- `tests/test_satellite_crossing_acceleration.py` would own coordinator
  invariants, exhaustive equivalence, zero-false-negative composition, broader
  domain fixtures, and benchmark-contract tests;
- benchmark tooling, if later admitted, must live under `tools/` and may not
  become a runtime dependency.

This audit creates no source, runtime test, benchmark tool, fixture, dependency,
or package export.

## 11. Explicit non-goals

50S.6C adds no illumination, eclipse/shadow state, visibility semantics,
brightness, flare probability, detector response, exposure contamination,
provider acquisition, CLI, reporting, drawing, rendering, export, new field
shape, or population index.

## 12. Acceptance and authorization

The audit is documentation-only. On commit `ba1deaa`, the focused
plugin-disabled current-documentation gate passed all 140 tests in 3.55
seconds and `git diff --check 93a7d41...HEAD` was clean. Fernando
scientifically and architecturally accepted 50S.6C on 2026-09-16.

Acceptance authorizes only a bounded 50S.6D implementation of exact-solver
coordination using the already accepted cone-shell selector inside its existing
three-record, 60-second domain. Broader-domain activation, benchmark claims,
default enablement, phase/coarse/indexing stages, 50S.7, and all later behavior
would remain unauthorized.


## 13. Accepted 50S.6D implementation record

The accepted implementation extracts the existing exact per-record operation
into one package-internal seam owned by `crossing_oracle.py`. The exhaustive
public oracle still scans every record. The opt-in coordinator in
`crossing_acceleration.py` validates complete query identity and
NORAD-ordered coverage, solves every retain and indeterminate record through
that same seam, and records rejected and exactly evaluated identifiers in
immutable evidence.

Selector exceptions fall back to the complete exhaustive route by default or
fail closed under explicit policy. Malformed selection evidence and any reject
outside `synthetic_50s4b_v1` or the 60-second limit fail closed. Exact results
remain separate from acceleration evidence.

The accepted implementation adds no broader domain, fixture, benchmark claim, default
enablement, new filter stage, coordinate path, dependency, CLI, report,
drawing, illumination, photometry, or later satellite behavior. Acceptance required the dedicated acceleration gate, the expanded immediate-seam
gate, the complete plugin-disabled suite, documentation preflight, clean branch
diff, and Fernando's scientific and architectural review.


## 14. Accepted 50S.6D verification evidence

On macOS with Python 3.11.7 and ambient pytest plugins disabled, candidate
commit `a7aecba` passed:

- the 37-test dedicated acceleration/oracle gate in 116.58 seconds;
- the 93-test expanded acceleration, oracle, crossing-contract, element, SGP4,
  topocentric, and package-boundary gate in 128.74 seconds;
- the 141-test current-documentation gate in 4.36 seconds; and
- the complete 2,566-test suite in 213.87 seconds.

This evidence covers the accepted executable implementation and its initial
documentation. The final pre-acceptance documentation gate passed all 142 tests
in 4.06 seconds, the branch diff check was clean, and the working tree was
clean. Fernando scientifically and architecturally accepted 50S.6D on
2026-09-16. No performance, broader-domain, default-enablement, or later
acceleration claim is made or authorized.
