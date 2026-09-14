# Artificial-satellite crossing and photometry audit (Milestone 50S.0)

**Status:** Candidate for Fernando's scientific and architectural review  
**Audit date:** 2026-09-14  
**Implementation baseline:** `862acaa`  
**Scope:** Literature, provider, algorithm, photometry, validation, and
architecture decisions only; no runtime satellite, catalogue acquisition, or
public crossing command

## 1. Scientific question

Wenu must accept an observer, an explicitly framed field centre and footprint,
and a UTC interval lasting minutes to hours, and return every artificial
satellite whose apparent topocentric path intersects the field. The same
machinery must support repeated studies versus local night time, season,
pointing, field size, and exposure duration.

The first correctness requirement is completeness: an optimization may retain
false candidates, but it must not discard a true crossing. Apparent brightness
is a later, probabilistic characterization of a geometrically selected pass;
it is not part of the crossing predicate and is not a detectability claim.

## 2. Primary sources reviewed

The following sources were checked on 2026-09-14.

### Orbit data, propagation, and reference systems

- CCSDS, *Orbit Data Messages*, CCSDS 502.0-B-3: OMM field and metadata
  standard.
- Vallado, Crawford, Hujsak, and Kelso, *Revisiting Spacetrack Report #3*,
  AIAA 2006-6753 Rev. 2: SGP4 theory, compatible implementation, verification
  cases, and the requirement to propagate GP mean elements with SGP4.
- CelesTrak, *A New Way to Obtain GP Data (aka TLEs)*: current OMM-compatible
  XML/KVN/CSV/JSON products, TEME/UTC/SGP4 metadata, catalogue-number limits,
  and usage policy.
- Space-Track, *API documentation*: authenticated GP/OMM and SATCAT access and
  published query limits.
- IERS Conventions (2010), IERS Technical Note 36: Earth orientation and
  terrestrial/celestial transformations.

### Crossing and survey-impact methods

- Osborn et al., *Astrosat: Forecasting satellite transits for optical
  astronomical observations*, MNRAS 509 (2022): observer- and field-specific
  orbit projection, transit prediction, and brightness context.
- Hu et al., *Satellite Constellation Avoidance with the Rubin Observatory
  Legacy Survey of Space and Time*, AJ 166 (2023): catalogue-scale ephemeris
  masks, scheduler queries, and the operational effect of prediction error.
- Górski et al., *HEALPix: A Framework for High-Resolution Discretization and
  Fast Analysis of Data Distributed on the Sphere*, ApJ 622 (2005): equal-area
  hierarchical spherical pixels and fast region lookup.
- IAU CPS SatHub, *SatChecker*: an open reference service for ephemerides,
  field-of-view interference, range, angular velocity, and illumination.
- Hainaut and Williams, *On the impact of satellite constellations on
  astronomical observations with ESO telescopes*, A&A 636, A121 (2020):
  representative night, latitude, altitude, illumination, field, and exposure
  workloads.

### Brightness and detector separation

- Tyson et al., *Mitigation of LEO satellite brightness and trail effects on
  the Rubin Observatory LSST*, AJ 160, 226 (2020): measured class differences,
  range normalization, trail surface brightness, defocus, saturation, and
  detector effects.
- Halferty et al., *Photometric characterization and trajectory accuracy of
  Starlink satellites*, MNRAS 516 (2022): calibrated Gaia-G photometry,
  population scatter, satellite-generation differences, and TLE residuals.
- Mallama, *The brightness of Starlink and OneWeb satellites during ingress
  and egress from terrestrial eclipses*, arXiv:2112.08310: atmospheric
  refraction and absorption around geometric shadow boundaries.
- Fankhauser et al., *Satellite optical brightness*, Nature 623 (2023):
  geometry- and spacecraft-dependent brightness modeling and empirical
  validation.
- IAU CPS, *Consolidated recommendations for LEO satellite constellation
  operators* (2023): common brightness reporting and mitigation context.

## 3. Provider-policy preflight

### 3.1 CelesTrak

Authoritative policy and format page:
`https://celestrak.org/NORAD/documentation/gp-data-formats.php`, checked
2026-09-14.

CelesTrak states that GP data are checked for updates once every two hours and
must not be downloaded more often. Clients must use cached data by default,
inspect timestamps, request only needed products, stop and report non-200
responses, and must not retry 301, 403, 404, or server errors aggressively.
Current limits also protect high-volume products and bandwidth. OMM-compatible
CSV or XML is preferred over legacy TLE because six- and nine-digit catalogue
identifiers cannot be represented in TLE.

**Decision — Adopt with hard constraints.** One snapshot acquisition checks
age before access, performs at most one supported bulk request for the needed
catalogue, validates before atomic publication, and then works locally. No
per-object requests, polling loop, parallel downloads, or automatic retry.
The exact response, retrieval time, URL/parameters, digest, and provider notice
are retained. Redistribution is not authorized by this audit and remains a
separate legal/licensing decision.

### 3.2 Space-Track

Authoritative documentation: `https://www.space-track.org/documentation`,
checked 2026-09-14. It requires an account and publishes API guidance including
fewer than 30 requests per minute and 300 requests per hour, with additional
bandwidth and query-shaping guidance. Space-Track-origin data can carry
redistribution restrictions; account terms must be reviewed by the person or
release process that acquires it.

**Decision — Defer as Wenu's automatic default.** Space-Track is valuable as
an authenticated independent source and validation oracle, but Wenu must not
embed credentials or redistribute account-derived snapshots without explicit
permission. Any future adapter must be opt-in, serial, bulk-oriented, cached,
credential-external, and governed by the then-current account terms.

### 3.3 SatChecker

Authoritative project and API documentation:
`https://github.com/iausathub/satchecker` and
`https://satchecker.readthedocs.io/`, checked 2026-09-14. The software is
BSD-3-Clause; its service consumes CelesTrak and Space-Track data and exposes
ephemeris and field-interference results.

**Decision — Adopt as an independent comparison oracle; reject as the sole
production dependency.** Wenu needs reproducible frozen snapshots and a local
complete-scan oracle. Service availability, its upstream snapshot, and its
request policy must not determine whether an offline Wenu query works.

## 4. Orbit-state contract

**Adopt OMM as the canonical ingestion model.** Preserve every available OMM
identity and model field, including `OBJECT_ID`, `NORAD_CAT_ID`, element-set
number, classification, epoch, reference frame, time system, centre, and mean
element theory. Accept legacy TLE only through an adapter that produces the
same typed internal record. Never truncate a catalogue identifier to five
digits.

**Adopt a frozen catalogue snapshot.** Its identity includes provider,
retrieval instant, exact response digest, query, schema/format version, and
all element records. Satellite identity and orbit-solution identity remain
separate. Duplicate catalogue entries and element epochs are resolved by an
explicit policy, never input order.

**Adopt the Vallado-compatible SGP4 implementation and verification vectors.**
GP mean elements are not osculating Keplerian elements. They must not be sent
through a two-body propagator or a different force model. Batch/vectorized
execution may change evaluation order, not the scientific model.

**Adopt explicit TEME state.** TEME is neither ICRS nor an observer frame.
Transformation to an Earth-fixed state must declare UTC and Earth-orientation
inputs; observer subtraction and topocentric apparent direction follow as
separate steps. Refraction is off for astronomical field intersection by
default and, if later offered, is an explicit observed-coordinate policy.

Orbit age is reported, not hidden. The query result retains element epoch,
prediction offset, and warnings. No universal freshness threshold is asserted:
acceptable prediction age depends on orbit regime, maneuvers, drag, and the
field/exposure tolerance. Decayed or invalid records are rejected explicitly;
stale or maneuver-prone records remain visible with warnings unless a declared
query policy excludes them.

For topocentric relative position `rho` and velocity `rho_dot`, instantaneous
angular speed is

```text
omega = |rho x rho_dot| / |rho|^2.
```

There is no safe catalogue-independent angular-speed constant: the expression
grows without bound as topocentric range approaches zero. Each interval bound
must therefore retain a conservative lower range and upper transverse-speed
bound derived from propagated state. If those bounds become singular or too
loose near a zenith pass, the interval is subdivided or sent to the exact
solver. A measured current-catalogue maximum is useful performance evidence,
not a proof bound for later snapshots.

## 5. Crossing semantics and exhaustive oracle

50S.2 must first implement a complete catalogue scan independent of drawing.
The predicate is intersection of a continuous apparent topocentric trajectory
with a closed spherical footprint during an inclusive interval. Boundary
touch counts as a crossing. Circular, spherical-rectangle, and later WCS
footprints share the same contract; a planar chart boundary is not the
scientific field definition.

A fixed time grid alone cannot prove completeness. LEO angular speed increases
strongly near a close zenith pass; entry and exit can occur between samples.
The reference algorithm therefore uses adaptive interval subdivision with a
conservative angular-motion bound, followed by bracketed root/extremum
refinement. It returns entry, exit, closest approach, time in field, angular
rate, range, illumination state, and every exposure overlap. Disconnected
visits are separate events.

**Decision — Adopt adaptive complete scan as the oracle.** Its tolerances are
derived from footprint size and requested time accuracy. It may be slower than
the final product, but it must be independently callable on a full snapshot
and on adversarial cases.

## 6. Fast candidate search

The reviewed literature supports bulk propagation and spatial/temporal masks,
but no reviewed method makes coarse point sampling alone a zero-false-negative
proof. Wenu therefore adopts a conservative hierarchy:

1. group queries by exact snapshot, observer, Earth-orientation policy, and
   bounded interval;
2. vectorize SGP4 evaluation over catalogue batches and time slabs;
3. construct a conservative swept spherical cap or pixel cover for each
   object/slab using endpoint directions plus a bound on angular displacement
   and numerical/transformation error;
4. query a hierarchical spherical pixel index (HEALPix is the leading
   candidate) and overlapping time intervals;
5. pass every retained candidate to the exact 50S.2 crossing solver.

The cover radius must include maximum possible between-sample curvature and
motion, footprint dilation, prediction/numerical allowance, and boundary
tolerance. Near-zenith intervals that cannot obtain a sufficiently tight
bound subdivide or fall back to exact evaluation; they are never rejected.

**Decision — Adapt hierarchical sky pixels plus interval slabs.** A simple
inverted mapping from `(time slab, sky pixel)` to candidate identifiers is
preferred before a more complex combined space-time tree. An immutable
observer/night index is appropriate for many pointings; isolated queries may
use ephemeral vectorized bounds. Index keys include snapshot digest, observer,
EOP policy, interval, bound/cadence policy, SGP4 implementation/version, and
software version.

**Reject** unconstrained linear interpolation, nearest sampled-point tests,
plain bounding boxes in right ascension/declination, or an index that lacks an
exact fallback. RA wrapping, polar convergence, horizon geometry, and zenith
singularity make these unsafe.

50S.3 acceptance requires zero false negatives against the complete-scan
oracle for adversarial grazing, seam, pole, horizon, fast-LEO zenith, high
eccentricity, boundary-touch, short-exposure, and interval-end cases. Measure
cold index construction, warm reuse, query latency, memory and disk size over
a current full catalogue, not only a small fixture.

## 7. Illumination and apparent brightness

### 7.1 Illumination

Adopt an explicit Sun-satellite-observer geometry. A geometric Earth umbra and
penumbra model is the minimum physical state; solar angular extent is not
collapsed to a point for penumbra. Atmospheric refraction and extinction near
shadow ingress/egress are deferred until empirically validated. Illumination
state and its model provenance are reported independently of brightness.

### 7.2 Photometric hierarchy

For reflected sunlight, distance and phase are necessary but insufficient.
At minimum a model must declare passband, solar magnitude/spectrum, observer
range, phase angle, projected area, attitude law, shape, and reflectance or
empirical phase function. Unknown attitude, tumbling, appendage orientation,
material BRDF, and specular paths can dominate the answer.

**Adopt a hierarchy rather than one universal magnitude:**

1. `unknown` when there is no defensible area/reflectance or empirical class;
2. an empirical satellite-family magnitude distribution normalized to a
   declared range and conditioned on available geometry;
3. a diffuse physical model only when size, attitude, and reflectance
   assumptions are explicit;
4. a spacecraft-specific BRDF/attitude model only with published parameters
   and independent observations.

Every result is a model magnitude or distribution with uncertainty and model
domain. It must never be labelled guaranteed brightness. Specular flares and
tumbling are reported as unmodeled or probabilistic tails unless validated
time-dependent attitude/BRDF data exist. A single standard magnitude is not a
substitute for a phase function.

Atmospheric extinction is a separate observer/passband policy and is not
silently applied. Detector contamination remains later work: magnitude does
not determine trail signal without angular speed, exposure, defocus/PSF,
aperture, throughput, pixel scale, sky background, saturation, and detector
response.

**Decision — Defer runtime photometry to 50S.4B.** 50S.0 accepts the hierarchy
and validation obligations, not coefficients. At least two materially
different satellite families and geometries must be compared with calibrated,
time-resolved observations before tolerances are selected. Report residuals,
bias, scatter, outliers, passband transformations, range normalization, phase
coverage, and orbit-age/trajectory error.

## 8. Workloads and validation

Performance specimens must include the complete current public catalogue and
representative LEO, MEO, GEO, and highly elliptical subsets; one isolated
short query; many pointings in one night; a wide survey field; a narrow
instrument field; exposures from seconds to minutes; twilight and deep-night
illumination; and observers at low, middle, and high latitude.

Scientific validation is layered:

- official Vallado SGP4 verification vectors for raw TEME propagation;
- independent SatChecker or Space-Track comparisons for selected states;
- direct coordinate-chain comparisons at multiple observers and orbit regimes;
- complete-scan versus optimized-index equivalence;
- calibrated observations for trajectory timing and photometry.

Catalogue size and orbital population change with time, so numerical
performance thresholds are chosen in 50S.3 from a recorded contemporary
snapshot and Mac measurement. The audit does not invent a fixed satellite
count or latency before measurement.

## 9. Wenu ownership and sequence

Artificial-satellite work is a coherent domain expected eventually to justify
`src/wenu/satellites/`, but 50S.0 adds no production package. Before 50S.1,
module admission must identify the closest current owners and preserve these
boundaries:

- acquisition and snapshot publication do not occur in propagation or charts;
- OMM/TLE parsing and SGP4/TEME state are separate from observer direction;
- field footprints and crossings are independent of chart projection;
- indexing accelerates queries but owns no propagation truth;
- illumination and photometry do not change geometric crossing results;
- reports and later drawing consume the same accepted crossing records;
- selected drawing reuses Wenu's existing trajectory, projection,
  preparation, renderer, semantic SVG, and export pipeline.

The implementation order remains 50S.1 validated states, 50S.2 exact crossing
oracle, 50S.3 conservative index, 50S.4A geometric reports, 50S.4B brightness,
and 50S.5 selected drawing and closure. Each slice requires a fresh provider
policy check because provider formats, catalogue identifiers, access limits,
and redistribution terms can change.

`coordinate_system_guide_v0.9.5.md` was reviewed for this audit and remains
current because 50S.0 installs no coordinate type, transformation, provider,
or public product. Milestone 50S.1 must update it when TEME and the
satellite-to-topocentric chain become implemented Wenu responsibilities.
During the foundation branch, `satellite_guide.md` separately maintains the
satellite vocabulary, equations, provider rules, data flow, and evolving
implementation map. Consolidation with the coordinate-system guide is a
deliberate merge-time decision rather than an automatic file combination.

## 10. Explicit non-goals

This audit does not authorize runtime acquisition, an installed satellite
catalogue, a public CLI, background network access, orbit fitting, covariance
propagation, maneuver prediction, radio interference, physical spacecraft
rendering, deterministic flare prediction, visibility/detectability claims,
or a satellite-specific projection/render/export pipeline.

## 11. Acceptance decision requested

Fernando is asked to accept, adapt, reject, or defer:

1. OMM-first frozen snapshots with legacy TLE only as an adapter;
2. CelesTrak as the candidate bulk source under its two-hour/cache/stop rules,
   with Space-Track opt-in and SatChecker as an independent oracle;
3. Vallado-compatible SGP4 and explicit TEME/EOP/topocentric stages;
4. adaptive complete scan as the 50S.2 correctness oracle;
5. conservative time-slab plus hierarchical-sky-pixel indexing for 50S.3;
6. zero false negatives as the optimization acceptance invariant;
7. empirical, class-aware magnitude distributions with explicit uncertainty,
   rather than a universal deterministic brightness formula;
8. strict separation of crossing, illumination, apparent magnitude, and
   detector-level contamination.
