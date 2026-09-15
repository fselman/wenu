# 50S.6A conservative local crossing acceleration audit

**Status:** Candidate documentation-only scientific and API audit  
**Base:** accepted 50S.5 closure at merge commit `cc454de`  
**Date:** 2026-09-15

## 1. Purpose

This audit defines the only admissible acceleration boundary above the accepted
50S.5 exhaustive local crossing oracle. It adds no runtime filter, index,
dependency, package data, generated product, CLI, report, drawing,
illumination, photometry, or detector behavior.

The performance objective is to avoid expensive SGP4 and Earth-orientation
evaluation for records or intervals that can be proved unable to reach the
fixed closed circular field. The scientific objective is stricter: every
crossing returned by the accepted 50S.5 oracle must remain reachable by the
accelerated route. A doubtful rejection is forbidden; uncertainty passes the
record or interval to the exact oracle.

## 2. Retained authority

`LocalSatelliteCrossingOracle.solve(query)` remains independently callable and
continues to scan every selected snapshot record. It is the correctness oracle,
not an implementation detail to be replaced after optimization.

The accelerated route must consume the same immutable
`LocalSatelliteCrossingQuery`, installed digest-verified snapshot, observer,
fixed geometric GCRS-axis field, inclusive UTC interval, and declared time and
angular tolerances. Every retained candidate reaches the accepted 50S.5
record-level adaptive solver. Acceleration may reduce work before exact solving;
it may not alter entry, exit, closest approach, ordering, result provenance, or
failure semantics.

## 3. Meaning of conservative

A filter may reject a record or interval only when a finite, explicitly
recorded bound proves that every physically reachable topocentric direction is
strictly outside the field after including:

- the field angular radius;
- the accepted oracle angular tolerance;
- numerical roundoff and transformation margins;
- the complete interval, including both endpoints;
- the observer displacement and Earth rotation where relevant;
- the radial and angular envelope admitted by the filter model;
- any model discrepancy measured against accepted SGP4/topocentric states.

Equality, overlap, unavailable inputs, non-finite values, unsupported regimes,
bound exhaustion, or an unvalidated model must pass through to the exact
oracle. A filter is therefore tri-state: `reject`, `retain`, or
`indeterminate`. Only `reject` removes work; `indeterminate` is not a
negative result.

Conservative here means validated zero false negatives over the declared
domain and test matrix. It is not a formal interval-arithmetic proof of SGP4.

## 4. Proposed ownership and immutable evidence

A later 50S.6B implementation may add
`src/wenu/satellites/crossing_acceleration.py` as the sole owner of:

- an immutable acceleration policy with individually enabled stages;
- immutable per-stage bounds and decisions;
- an ordered retained-record set;
- an accelerated coordinator that invokes the accepted exact record solver;
- aggregate evaluation counts and timing evidence used for benchmarks.

The accepted `crossing_oracle.py` retains exact adaptive solving, root and
minimum refinement, connected-visit assembly, and convergence failure.
`sgp4.py`, `topocentric.py`, and `snapshots.py` retain their existing
responsibilities. No filter may duplicate TEME propagation, Earth orientation,
topocentric transformation, or the exact angular crossing predicate.

Each rejection must identify the full NORAD catalogue identifier, filter
version, input snapshot digest, query identity, interval, numerical bound,
safety margin, and decisive inequality. Retained and indeterminate decisions
must also be inspectable. Result provenance must state that acceleration was
used while retaining the exact solver identity and lower-level evidence.

## 5. Staged filter order

Stages are admitted separately and remain individually disableable. A later
stage must not be used to disguise weakness or incorrectness in an earlier one.

### 5.1 Topocentric cone versus bounded orbital shell

The first proposed stage bounds the satellite's Earth-centred radial shell and
the reachable orientation of its orbital plane over the complete query
interval, then asks whether that entire shell/plane envelope can intersect the
observer-origin field cone.

The bound may use immutable OMM elements and validated auxiliary SGP4 samples,
but it may not treat the epoch osculating plane as fixed. Precession, drag,
eccentric radial motion, observer displacement, Earth rotation, interval
length, and measured SGP4-versus-envelope discrepancy require explicit outward
margins. If a complete envelope cannot be constructed for a record, the record
is retained.

A geocentric great-circle distance alone is insufficient: the observer is not
at Earth's centre, the satellite has finite and changing range, and near-field
parallax can move the topocentric direction materially.

### 5.2 Phase and reachable-arc rejection

Only records retained by the shell/plane stage may enter a phase stage. Epoch
mean anomaly and mean motion may seed a reachable-arc envelope, but the
rejection bound must include eccentricity, secular rates, drag terms, interval
duration, wrap, and calibrated disagreement with SGP4.

The phase stage may reject only when the complete reachable arc plus its safety
margin cannot intersect the cone/shell overlap. A nominal phase point, fixed
cadence, or endpoint-only check is not conservative.

### 5.3 Coarse propagated-state envelope

A later optional stage may evaluate vectorized coarse SGP4 states and construct
a swept topocentric angular tube using conservative rate and curvature bounds.
Sampling alone proves nothing between samples. Every coarse interval that
cannot be certified outside passes to the accepted adaptive oracle.

The vectorized path must use the same WGS-72, split-Julian-date, status, and
record identity rules as 50S.4C. Earth-orientation transformation remains owned
by the accepted 50S.4D service; batching must not introduce a second coordinate
path.

## 6. Rejected or deferred filters

### Horizon rejection

The accepted 50S.5 query is a geometric fixed-field query and has no
above-horizon or observability predicate. It can intentionally describe a field
below the observer's horizon. A horizon filter would therefore change result
semantics and can create false negatives relative to 50S.5. It is rejected from
50S.6 acceleration. A future explicit observability query may use horizon state
as a separate scientific predicate after its own audit.

### Earth-occultation rejection

The accepted oracle reports geometric directional crossings, not visibility
through an opaque Earth. Earth occultation is likewise not an admissible
50S.6 rejection criterion. It belongs with later independent visibility or
illumination geometry unless the public query contract is explicitly extended
and separately validated.

### HEALPix and time indexing

HEALPix or a time index is deferred until representative medium/full-snapshot
or many-pointing benchmarks demonstrate material benefit beyond the staged
bounds above. Any later pixel cover must enclose the complete swept
topocentric trajectory tube including uncertainty margins. Pixel membership
may select candidates only; every candidate still reaches the exact oracle.

## 7. Exact-solver composition seam

The accepted exhaustive `solve(query)` behavior must remain unchanged. A
later implementation may extract its already existing per-record evaluation
into one shared internal exact seam so that:

1. exhaustive `solve(query)` calls it for every ordered record;
2. the accelerated coordinator calls it only for conservatively retained
   ordered records;
3. both routes use identical trajectory evaluation, root/minimum refinement,
   visit assembly, provenance, warning, and convergence code;
4. no public caller can relabel a partial record set as an exhaustive result.

The accelerated coordinator owns the proof that rejected records are safe to
omit and the proof that final results retain full-NORAD/entry ordering.

## 8. Validation matrix

Acceptance requires exact accelerated-versus-exhaustive equality for result
count, satellite identity, entry, closest approach, exit, separation, ordering,
warnings, and scientific provenance, apart from additional acceleration
evidence.

The zero-false-negative matrix must include:

- central crossings;
- grazing and zero-duration tangent contact;
- crossings wholly between coarse samples;
- disconnected repeated visits;
- zenith and near-zenith motion;
- horizon-adjacent and below-horizon geometric fields;
- longitude wrap, pole, and coordinate-seam cases;
- short exposures and contacts at both interval endpoints;
- eccentric, high-drag, high-angular-rate, near-Earth, and deep-space records;
- intervals spanning phase wrap and materially different Earth rotation;
- unsupported or indeterminate bounds that must pass through;
- invalid propagation or Earth-orientation state that must still fail closed.

Analytic/adversarial filter tests must remain independent of SGP4 where
possible. Installed-snapshot composition must compare with the accepted 50S.5
oracle rather than with 50S.4E sampled specimens. Randomized or property-based
campaigns may supplement but never replace named deterministic edge cases.

## 9. Benchmark admission

Correctness is required before performance measurement. Report cold and warm
runs separately and measure at least:

- records rejected, retained, and indeterminate by each stage;
- exact SGP4 and topocentric evaluations avoided and performed;
- filter time, exact-solver time, and total wall time;
- exhaustive-versus-accelerated speedup;
- snapshot size, interval, field radius, observer, and pointing distribution.

The three-record synthetic snapshot proves composition, not useful speed.
Representative immutable medium/full-snapshot evidence is required before
claiming benefit. A stage that adds complexity without material measured benefit
must remain disabled or be rejected.

## 10. Failure and reproducibility policy

Acceleration never converts a provider, element, propagation, Earth-orientation,
coordinate, or exact-solver failure into an empty result. Filter arithmetic
failure becomes `indeterminate`; lower-level failures on retained candidates
follow the accepted fail-closed behavior.

Policies, bounds, calibration fixtures, software versions, snapshot digests,
and benchmark inputs must be immutable and reproducible. No live provider,
network acquisition, mutable cache refresh, or machine-dependent hidden default
is permitted during a search or acceptance test.

## 11. Documentation and test ownership

A later 50S.6B implementation should extend
`tests/test_satellite_crossing_oracle.py` only for the shared exact-solver
seam. A distinct `tests/test_satellite_crossing_acceleration.py` is justified
for the durable conservative-filter oracle, tri-state decisions, equivalence
matrix, stage isolation, and benchmark-evidence contracts.

This 50S.6A audit changes documentation and its current-documentation contract
only. It creates no source or acceleration test file and changes no package
boundary.

## 12. Explicit non-goals

50S.6 does not add illumination, eclipse or shadow state, observer-night
classification, brightness, flare probability, detector response, exposure
contamination, CLI, reporting, chart layers, drawing, rendering, export, live
catalogue access, snapshot acquisition, or new footprint shapes.

## 13. Candidate acceptance and authorization

Acceptance requires Fernando's scientific and architectural review, the focused
documentation gate, and clean branch-diff evidence. Acceptance of 50S.6A would
authorize only a bounded 50S.6B first implementation of the topocentric
cone/orbital-shell conservative selector and its exact-oracle equivalence
evidence.

Phase/reachable-arc filtering, coarse vectorized propagation, HEALPix/time
indexing, horizon/occultation semantics, 50S.7, and all later behavior would
remain unauthorized.
