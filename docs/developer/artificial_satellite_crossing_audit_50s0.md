# Artificial-satellite crossing and photometry audit (Milestone 50S.0)

**Status:** Accepted by Fernando on 2026-09-14
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

**Decision — Adopt as the first bounded crossing provider and as an external
comparison oracle; reject as the sole long-term production dependency.** Wenu
first defines a provider-neutral crossing query and result contract, then uses
SatChecker for supported circular-field queries while retaining its exact
request, raw response, upstream-orbit provenance, async-task state, and stated
limitations. Service availability, its upstream snapshot, and its request
policy must not determine whether a later offline Wenu query works.

## 4. Orbit-state contract

**Adopt OMM as the canonical ingestion model.** Preserve every available OMM
identity and model field, including `OBJECT_ID`, `NORAD_CAT_ID`, element-set
number, classification, epoch, reference frame, time system, centre, and mean
element theory. Accept legacy TLE only through an adapter that produces the
same typed internal record. Never truncate a catalogue identifier to five
digits.

**Adopt a frozen catalogue snapshot.** This is a frozen copy of the provider's
orbit-element catalogue at one declared retrieval instant, not a set of
propagated satellite positions or an image of the sky. Its identity includes
provider, retrieval instant, exact response digest, query, schema/format
version, and all element records. Satellite identity and orbit-solution
identity remain separate. Duplicate catalogue entries and element epochs are
resolved by an explicit policy, never input order. Future positions are
propagated from these fixed inputs so a result remains reproducible after the
provider publishes newer elements.

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

50S.5 must first implement a complete local catalogue scan independent of
drawing.
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

The reviewed literature supports bulk propagation, geometric screening, and
spatial/temporal masks, but no reviewed method makes coarse point sampling
alone a zero-false-negative proof. Wenu therefore adopts a conservative
hierarchy after the complete local oracle exists:

1. reject orbital planes whose observer-centred FoV cones cannot intersect the
   orbit over its admissible radial shell;
2. use element epoch, mean motion, mean anomaly, and conservative perturbation
   margins to reject objects whose reachable orbital arcs cannot approach the
   field during the interval;
3. reject intervals that remain Earth-occulted or geometrically below the
   observer horizon;
4. vectorize SGP4 evaluation over remaining catalogue batches and use coarse
   states plus conservative angular-motion and curvature bounds;
5. pass every retained candidate to the exact 50S.5 crossing solver.

The orbital-plane test is topocentric, not merely a geocentric great-circle
comparison. For observer position `r_o`, line-of-sight direction `u`, range
`rho`, and plane normal `n`, a possible state must satisfy
`n . (r_o + rho u) = 0` at a positive admissible range. Plane proximity alone
must never reject a low satellite whose parallax moves its apparent path away
from the corresponding geocentric great circle.

The cover radius must include maximum possible between-sample curvature and
motion, footprint dilation, prediction/numerical allowance, and boundary
tolerance. Near-zenith intervals that cannot obtain a sufficiently tight
bound subdivide or fall back to exact evaluation; they are never rejected.

**Decision — Adopt plane, radial-shell, phase/reachable-arc, occultation, and
coarse-state filters before deciding whether to add a persistent spatial
index.** HEALPix plus time slabs remains the leading optional index for many
pointings over an observer/night or for seasonal sky characterization. The
initial small-snapshot specimen builder and complete oracle use brute force.
Benchmarks on larger snapshots decide whether an ephemeral or persistent
HEALPix index is justified. Any index key includes snapshot digest, observer,
EOP policy, interval, bound/cadence policy, SGP4 implementation/version, and
software version.

**Reject** unconstrained linear interpolation, nearest sampled-point tests,
plain bounding boxes in right ascension/declination, or an index that lacks an
exact fallback. RA wrapping, polar convergence, horizon geometry, and zenith
singularity make these unsafe.

50S.6 acceptance requires zero false negatives against the complete-scan
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
2. an empirical population distribution for a defensible class and orbital
   regime when no narrower model exists;
3. an empirical satellite-family magnitude distribution normalized to a
   declared range and conditioned on available geometry;
4. an object-specific empirical model when observations support it;
5. a diffuse physical model only when size, attitude, and reflectance
   assumptions are explicit;
6. a spacecraft-specific BRDF/attitude model only with published parameters
   and independent observations.

Every result identifies the selected model level and is a model magnitude or
distribution with uncertainty and model domain. It must never be labelled
guaranteed brightness. Ordinary brightness and glints are separate results;
absent glint evidence means `unknown`, never zero probability. Specular flares
and tumbling are reported as unmodeled or probabilistic tails unless validated
time-dependent attitude/BRDF data exist. A single standard magnitude is not a
substitute for a phase function.

Atmospheric extinction is a separate observer/passband policy and is not
silently applied. Detector contamination remains later work: magnitude does
not determine trail signal without angular speed, exposure, defocus/PSF,
aperture, throughput, pixel scale, sky background, saturation, and detector
response.

**Decision — Defer runtime photometry to 50S.8.** 50S.0 accepts the hierarchy
and validation obligations, not coefficients. At least two materially
different satellite families and geometries must be compared with calibrated,
time-resolved observations before tolerances are selected. Report residuals,
bias, scatter, outliers, passband transformations, range normalization, phase
coverage, and orbit-age/trajectory error.

## 8. Workloads and validation

Development begins with a small, geometrically representative immutable OMM
snapshot rather than the first arbitrary catalogue records. It spans orbit
regimes, inclinations, eccentricities, object classes, shared planes with
different phases, fast and grazing passes, occulted objects, shadow
transitions, known and unknown photometry, aged elements, and parser fault
fixtures. Ordinary tests use committed fixtures and local snapshots only;
provider-contract tests prefer exact raw-response cache entries; live tests
are explicit, serial, bounded, policy-checked, and never part of ordinary
pytest.

A developer specimen builder consumes the small snapshot, observer, bounded
search interval, FoV size, and requested case type. It selects a reproducible
FoV and time window, stores reference tracks and provenance, invokes the
ordinary Wenu crossing query, and produces both a machine-readable crossing
result and a FoV chart with marked tracks. Its dense/adaptive brute-force
reference calculation remains independent of production candidate filters so
the same defect cannot generate and verify a fixture. HEALPix may later help
find crowded, empty, or otherwise useful specimens in larger snapshots, but
exact spherical geometry certifies every stored case.

Performance specimens later include the complete current public catalogue and
representative LEO, MEO, GEO, and highly elliptical subsets; one isolated
short query; many pointings in one night; a wide survey field; a narrow
instrument field; exposures from seconds to minutes; twilight and deep-night
illumination; and observers at low, middle, and high latitude.

Scientific validation is layered:

- official Vallado SGP4 verification vectors for raw TEME states;
- cached SatChecker comparisons for bounded end-to-end circular-field cases;
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

The accepted implementation order is:

1. 50S.1 provider-neutral satellite identity, observer, FoV, interval,
   crossing-candidate, and crossing-result contracts;
2. 50S.2 SatChecker adapter with cached raw responses, asynchronous progress,
   bounded policy-compliant failure handling, and normalized provenance;
3. 50S.3 human-readable/JSON crossing reports and FoV charts using the same
   normalized results, with provider-derived illumination kept distinct;
4. 50S.4 small representative immutable OMM snapshot, Vallado-compatible SGP4
   foundation, and the developer crossing-specimen builder;
5. 50S.5 complete local FoV-crossing oracle;
6. 50S.6 conservative orbital-plane, radial-shell, reachable-arc,
   occultation, and coarse-state acceleration, with HEALPix/time indexing only
   if larger-snapshot benchmarks justify it;
7. 50S.7 independent sunlight, penumbra, umbra, and observer-night geometry;
8. 50S.8 empirical object/family/population photometry and glint limitations;
9. 50S.9 detector-specific trail contamination; and
10. 50S.10 night, season, observer, pointing, field-size, and exposure-duration
    statistical products.

Each slice requires a fresh provider policy check because provider formats,
catalogue identifiers, access limits, and redistribution terms can change.

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

## 11. Accepted decisions

Fernando accepted on 2026-09-14:

1. OMM-first frozen snapshots with legacy TLE only as an adapter;
2. SatChecker first as a bounded online crossing provider and external oracle,
   followed by local immutable snapshots; CelesTrak remains the candidate bulk
   source under its two-hour/cache/stop rules and Space-Track remains opt-in;
3. Vallado-compatible SGP4 and explicit TEME/EOP/topocentric stages;
4. adaptive complete scan as the 50S.5 local correctness oracle;
5. conservative plane, radial-shell, phase/reachable-arc, occultation, and
   coarse-state filters before optional HEALPix/time indexing in 50S.6;
6. zero false negatives as the optimization acceptance invariant;
7. empirical object-specific models where defensible, satellite-family and
   population distributions otherwise, explicit uncertainty and `unknown`,
   rather than a universal deterministic brightness formula;
8. strict separation of crossing, illumination, apparent magnitude, and
   detector-level contamination;
9. extensive cached-data use, network-free ordinary tests, and a small
   representative snapshot before progressively larger retained snapshots;
10. a developer specimen builder that derives reproducible FoV/time cases from
    cached data and verifies Wenu reports and marked-track charts; and
11. 50S.0 through 50S.3 end with SatChecker reports/charts, while local
    snapshot and specimen work begins in 50S.4.

## Candidate 50S.7A refinement of the illumination decision

The 50S.7A audit retains the accepted finite-Sun umbra/penumbra requirement
and expands the source vocabulary to four independent incident components:
Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine. Direct sources are
finite-disk beams; Earth-reflected sources are extended directional fields.
Neither is yet apparent brightness.

The candidate proposes WGS-84 vacuum Earth occultation, typed transitions,
and observer geometric twilight first. It reserves direct-source radiometry
and both reflected fields for later separately accepted 50S.7 slices, with
spacecraft attitude, projected area, BRDF, passband magnitude, and glints
remaining 50S.8. No runtime is authorized by this refinement.

## Accepted 50S.7A refinement of the illumination decision

Fernando accepted the documentation-only 50S.7A refinement on 2026-09-20.
Sunlight, solar Earthshine, Moonlight, and Lunar-Earthshine remain four
independent incident components; direct-source and extended Earth-reflected
geometry remain separate from spacecraft attitude, BRDF, apparent brightness,
and detector response.

After merge, only bounded 50S.7B finite uniform-Sun/WGS-84 vacuum occultation,
typed shadow state, observer geometric twilight, provenance, and offline
validation are authorized. Transition solving, radiometry, reflected fields,
brightness, detector effects, visibility, facility integration, and scheduling
remain unauthorized later work requiring separate acceptance.
## Candidate 50S.7B refinement of the illumination decision

The bounded candidate adds an output-neutral downstream illumination geometry
owner without changing the crossing foundation. Exact crossing intervals,
tracks, reports, charts, and planning advisories retain their accepted
identity and behavior. The new state composes one accepted topocentric state
with one same-instant installed-ephemeris Sun state in ITRS, evaluates uniform
finite-Sun/WGS-84 vacuum occultation with convergence evidence, and separately
classifies geometric observer twilight.

No crossing is filtered, relabeled, ranked, or scheduled by this state.
50S.7C transitions, radiometry, reflected light, brightness, detector,
facility, visibility, and scheduling work remain unauthorized.

## Accepted 50S.7B refinement of the crossing foundation

Fernando accepted 50S.7B at `054ac53a` on 2026-09-21. The implementation is
strictly downstream and leaves crossing intervals, tracks, reports, charts,
and planning advisories unchanged. Its illumination and night classes do not
filter or redefine a crossing.

Merge remains separate. After merge, only a documentation-first 50S.7C audit
is authorized; transition runtime and later behavior remain unauthorized.

## Candidate 50S.7C refinement of shadow-event separation

The documentation-only transition audit keeps shadow events strictly
downstream of the accepted geometric crossing foundation. A future event query
selects one immutable snapshot record and a closed UTC interval; it does not
change FoV membership, crossing intervals, exact tracks, reports, charts, or
planning advisories.

Contact time must come from continuous finite-Sun/WGS-84 limb geometry with a
certified bracket and complete bounded interval search, not visible-fraction
quadrature, crossing samples, or chart interpolation. The event carries
orbit/snapshot/ephemeris/EOP/shadow/search identity and fails closed on
uncertainty or exhausted work.

This audit changes no runtime. Transition implementation, radiometry,
reflected fields, brightness, detector effects, visibility, facility
integration, and scheduling remain unauthorized.

## Accepted 50S.7C refinement of shadow-event separation

Fernando accepted the documentation-only refinement at `030a6322` on
2026-09-21. After merge, a bounded transition implementation may compose the
accepted propagation and Earth-orientation route for one selected record
without changing geometric crossing identity or membership.

Continuous finite-source contact geometry, certified brackets, complete
bounded interval search, deterministic event identity, and terminal failure
remain mandatory. Transition attachment to crossings, tracks, reports, charts,
CLI, or planning advisories and all later light, brightness, detector,
visibility, facility, and scheduling behavior remain unauthorized.

## Candidate 50S.7C implementation refinement

The bounded candidate adds observer-independent direct-solar shadow events
strictly downstream of geometric crossings. One selected immutable record and
closed UTC interval produce ordered directed contact brackets or a typed
terminal failure. No crossing membership, interval, exact track, report,
chart, or planning identity changes.

Executable `69375fab` passed 58 focused tests and the independent installed-
resource SPICE/Skyfield receipt. Complete gates and acceptance remain pending.
Transition attachment and every 50S.7D+, radiometric, reflected-field,
brightness, detector, visibility, facility, or scheduling behavior remain
unauthorized.

## Accepted 50S.7C implementation refinement

Fernando accepted the bounded downstream shadow-event implementation at
`eaeab6085b52bfed6136d37f3010c2f353e59f53` on 2026-09-21. Preserve its
single-record observer-independent query, continuous finite-source contact
geometry, shared Earth-orientation route, complete bounded search, certified
directed brackets, deterministic identity, and terminal failure.

The accepted implementation does not change crossing membership, intervals,
tracks, reports, charts, CLI, or planning advisories. PR 183 merge and branch
deletion remain separate decisions. Transition attachment and all 50S.7D+
radiometric, reflected-field, brightness, visibility, detector, facility, or
scheduling behavior remain unauthorized.
## Candidate 50S.7D refinement of illumination separation

The documentation-only audit keeps direct-source incident radiometry strictly
downstream of geometric crossing and accepted illumination geometry. The first
proposed 50S.7D.1 value is only bolometric normal-plane Sunlight, derived from
the IAU nominal irradiance, Sun-satellite distance, and accepted visible-disk
fraction.

It cannot filter, relabel, rank, draw, report, or schedule a crossing. It adds
no spacecraft surface, attitude, BRDF, observer flux, apparent magnitude,
visibility, or detector meaning. Unknown Moonlight remains not evaluated, not
zero.

The candidate changes no runtime. 50S.7D.1 implementation, later direct-source
models, reflected fields, outputs, brightness, detector, facility, and
scheduling behavior remain unauthorized pending separate acceptance.

## Accepted 50S.7D refinement of illumination separation

Fernando scientifically and architecturally accepted the documentation-only
50S.7D audit at exact candidate
`362199d04bd917741a8be88f20608967af75530e` on 2026-09-21. All 214
plugin-disabled current-documentation tests passed in 7.00 seconds; the diff,
exact-upstream, and clean-tree checks passed.

After merge, only the bounded 50S.7D.1 direct-Sun bolometric normal-plane
irradiance implementation may begin. It must compose the accepted illumination
geometry without changing crossing identity or adding surface, attitude, BRDF,
observer-flux, magnitude, visibility, detector, output, facility, or scheduling
meaning. 50S.7D.2+ and 50S.7E+ remain unauthorized. PR 184 merge and branch
deletion remain separate explicit decisions.
