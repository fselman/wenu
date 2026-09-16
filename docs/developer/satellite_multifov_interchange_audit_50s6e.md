# 50S.6E same-observer, same-night multi-FoV and interchange audit

**Status:** Candidate documentation-only scientific, API, performance, and
interchange audit.

## 1. Purpose and authority

This audit answers whether Wenu can calculate crossings for several fields
substantially faster than repeated independent calls while preserving the
accepted 50S.5 exact crossing meaning. It also places exact chart tracks,
machine-readable observatory reports, four-source illumination, brightness,
detector contamination, and programme closure in their proper later
milestones.

This audit changes no runtime source, public API, dependency, packaged data,
benchmark tool, chart output, provider policy, or accepted admission domain.
The exhaustive single-FoV oracle remains independently callable and default.
The accepted 50S.6D coordinator remains opt-in and restricted to
`synthetic_50s4b_v1` and intervals no longer than 60 seconds.

## 2. Provider-capability finding

SatChecker 1.8.0 exposes one scalar observer, circular FoV centre, radius, and
time interval per `/fov/satellite-passes/` request. Its asynchronous mode
queues one such calculation; it is not a documented multi-FoV batch API.
Current source declares a request-rate limit, but that limit is not evidence
that simultaneous expensive jobs share propagation or that clients should
consume the allowance aggressively.

Distinct SatChecker FoVs have distinct exact cache keys. Bounded concurrent
single-FoV requests may reduce caller wall-clock latency, but they repeat
provider calculations and are not an algorithmic speedup. Wenu must not infer a
provider concurrency policy or submit load tests without explicit provider
permission.

## 3. Primary batch domain

The proposed local batch has:

- exactly one observer;
- any non-empty ordered number of circular FoV requests;
- an independently declared start, stop, radius, frame, centre, and solver
  tolerance for every field;
- intervals contained within one explicitly identified observing night;
- the accepted exact per-field closed-boundary and connected-visit semantics.

Ten FoVs are the reference workload and proposed default internal processing
chunk, not a hard-coded public cardinality or scientific limit. The public
contract must accept any number within resource bounds established by use
testing. A caller-supplied or policy-selected chunk size may change execution
only; it may not change results, ordering, precision, failure meaning, or
provenance.

The same-interval workload is a special research and optimization case, not a
precondition. The evidence matrix must include disjoint, partially overlapping,
and identical intervals in the same night. Different observers and intervals
crossing the accepted night boundary remain later domains.

## 4. Reuse and exactness boundary

A batch may share immutable catalogue loading, record validation,
Earth-orientation inputs, observer state, propagation, and topocentric states.
A reusable physical state must be keyed by every input that affects it,
including snapshot and record identity, observer, instant, Earth-orientation
identity, propagator identity, and software/model version.

Field separation, containment, adaptive subdivision, boundary roots,
tangency, closest approach, connected-visit assembly, and output remain
independent per field. A field-specific separation result must never be reused
as though it were a satellite physical state.

The union night envelope may organize setup and coarse work, but Wenu must not
blindly propagate every object at every time across that envelope. Candidate
implementations must compare independent calls, bounded concurrency, overlap
grouping, and on-demand shared-state caching. Every batch result must be
exactly equivalent to the ordered collection of independent exhaustive
single-FoV results under the same tolerances.

Failures are explicit. Invalid batch structure fails before work begins.
Record propagation or coordinate failure must be visible in every dependent
field. One invalid field must not silently alter valid-field results. The
implementation audit must decide and document whether field validation is
atomic or returns a typed per-field failure collection.

## 5. Performance evidence

The reproducible matrix uses 1, 2, 5, 10, 20, and, when practical, 50 FoVs.
Ten is the principal ordinary workload. It includes:

- different FoVs with disjoint same-night intervals;
- partially overlapping intervals;
- identical intervals as the maximum-reuse research case;
- a realistic sequential observing programme;
- reordered fields to prove order independence;
- cold and warm repeated runs.

Record wall-clock time, CPU time, peak memory, records considered, selector
decisions, SGP4 evaluations, topocentric transformations, physical-state cache
hits and misses, exact separation evaluations, fallback count, and per-field
result equality. Concurrent single-FoV wall-clock reduction is reported
separately from reduced total calculation. Mocked delay or synthetic
three-record speedup is not benchmark evidence.

No cardinality bound, default-enabled batch acceleration, production speed
claim, or full-catalogue admission follows until representative use testing
shows stable time, memory, equality, and failure behavior.

## 6. Chart-track roadmap

The accepted 50S.3B layer already draws normalized sampled candidate evidence
through shared spherical geometry, projection, preparation, renderer, and
PNG/PDF/SVG paths. It does not yet connect production local exact results to an
ordinary chart request.

After this audit:

1. 50S.6F may implement the bounded multi-FoV coordinator.
2. 50S.6G.1 may admit representative catalogue scale and same-night intervals.
3. 50S.6G.2 may adapt exact crossing results into the existing shared satellite
   track layer.
4. 50S.6G.3 may accept binocular and regional chart products.
5. 50S.6G.4 may accept stereographic planisphere seam, horizon, mask, clipping,
   orientation, and PNG/PDF/semantic-SVG behavior.

These are geometric tracks. Illumination, visibility, brightness, and detector
damage remain separate later claims.

## 7. Machine-readable observatory report

Every single- or multi-FoV calculation must be representable by one canonical,
versioned, lossless information model. The batch header records schema,
software, observer, catalogue snapshot/digest, Earth-orientation identity, and
calculation policy. Each record retains stable field identity, full NORAD
identity, element epoch, entry, closest approach, exit, minimum separation,
angular motion, exposure overlap, solver/convergence evidence, warnings,
uncertainty, and complete provenance. Optional ordered track samples declare
UTC, units, coordinate frame, and interpolation prohibition or policy.

The proposed encodings are:

- versioned JSON as the canonical nested exchange;
- Astropy ECSV for a unit-aware human-readable scientific table;
- IVOA VOTable for astronomical software interoperability;
- optional plain CSV only as a lossy convenience view;
- optional CCSDS OEM only for orbit/state samples, never as a substitute for
  Wenu crossing, illumination, or contamination semantics.

50S.6G must deliver the generic JSON/ECSV/VOTable reports with exact geometric
crossings. 50S.6H must audit Paranal, ELT, and at least one other observatory
planning interface before claiming direct compatibility. ESO Phase 2 JSON and
Observation Blocks make an adapter plausible, but no ESO operational import,
avoidance, scheduling, authentication, or write interface is accepted by this
audit. Observatory adapters consume the canonical report and do not enter the
crossing solver.

## 8. Four-source illumination roadmap

50S.7 must treat illumination as component-resolved geometry rather than one
Boolean. It must audit and, through separately authorized slices, model:

1. direct Sunlight: Sun to satellite;
2. solar Earthshine: Sun to Earth to satellite;
3. direct Moonlight: Sun to Moon to satellite;
4. Lunar-Earthshine: Sun to Moon to Earth to satellite.

The term Lunar-Earthshine is used for Moonlight reflected by Earth; ordinary
Earthshine remains sunlight reflected by Earth. Umbra, penumbra, lunar phase,
Earth and Moon visibility, incident directions, observer Sun/Moon altitude,
twilight, and model applicability remain explicit. Geometric crossings remain
present even when a component is absent.

Caddy et al. (2026), *The First Observations of Moonlit Satellites*,
arXiv:2609.07057, reports quantitative ISS and CSS detections illuminated only
by Moonlight and Lunar-Earthshine, extends `lumos-sat` with those components,
and compares observations with independent Ansys STK simulations. This is
strong evidence that the mechanisms are real and sometimes material,
especially for large nadir-facing surfaces. It does not establish a universal
magnitude model for arbitrary satellites.

50S.8 may convert accepted component geometries into separately reported flux
or magnitude distributions. Fluxes, never magnitudes, are summed. Every
component retains passband, phase law, Earth/lunar reflectance or BRDF,
satellite surface/attitude assumptions, atmospheric extinction, uncertainty,
model epoch, provenance, and validity domain. Unsupported objects or
geometries remain explicitly `unknown`.

50S.9 adds exposure-, telescope-, instrument-, and detector-specific trail
contamination to the same stable report schema. 50S.10 validates scientific
products and at least one external planning workflow.

## 9. Proposed sequence and authorization

The resulting sequence is:

- 50S.6E: this documentation-only audit;
- 50S.6F: bounded same-observer, same-night multi-FoV implementation;
- 50S.6G: representative admission, generic reports, and exact chart tracks;
- 50S.6H: observatory-interface audit and separately bounded adapters;
- 50S.7: four-source illumination geometry;
- 50S.8: component-resolved brightness;
- 50S.9: instrument/detector contamination;
- 50S.10: night/season/pointing products and closure.

Acceptance of this audit would authorize only a bounded 50S.6F implementation.
It would not authorize broader catalogue admission, a public cardinality
limit, a performance claim, chart integration, observatory writes, direct ESO
or ELT compatibility, illumination, photometry, detector effects, or any later
milestone.
