# Wenu artificial-satellite scientific and implementation guide

**Status:** Living 50S work-in-progress guide; 50S.0 decisions accepted by
Fernando on 2026-09-14
**Established:** 2026-09-14
**Initial baseline:** `862acaa`
**Current authority:** the accepted portions of this guide together with the
active 50S milestone record and the general Wenu architecture documents

## 1. Purpose

This guide keeps the scientific meaning, provider constraints, mathematical
conventions, data flow, ownership boundaries, and validation plan for Wenu's
artificial-satellite program in one place while 50S is developed.

It is intentionally separate from `coordinate_system_guide_v0.9.5.md` during
the 50S foundation branch. The two guides may be consolidated when the
satellite foundation is merged, but only after checking that no satellite
meaning, equation, provider rule, or validation obligation is lost.

This document is not evidence that a described capability is implemented.
Each section distinguishes accepted direction, proposed implementation, and
future work. The as-built source ownership remains in `source_tree.md` and the
public interface remains in `implementation_reference.md`.

## 2. Acronyms and specialized abbreviations

- **AltAz — altitude–azimuth:** observer-local horizontal coordinates.
- **BRDF — bidirectional reflectance distribution function:** a model of how
  a surface reflects incident light into an outgoing direction.
- **BSTAR — SGP4 drag-like coefficient:** the historical `B*` element carried
  by GP records; it is not by itself a physical ballistic coefficient.
- **CCSDS — Consultative Committee for Space Data Systems:** standards body
  that defines OMM and related navigation messages.
- **CPS — Centre for the Protection of the Dark and Quiet Sky from Satellite
  Constellation Interference:** the IAU centre responsible for SatHub and
  SatChecker.
- **CSV — comma-separated values:** a tabular text serialization.
- **EOP — Earth-orientation parameters:** quantities such as UT1−UTC and polar
  motion used in terrestrial/celestial transformations.
- **GCRS — Geocentric Celestial Reference System:** relativistic celestial
  reference system centred at Earth.
- **GEO — geosynchronous Earth orbit:** orbit whose period follows Earth's
  rotation; geostationary orbit is the circular equatorial special case.
- **GP — general perturbations:** the orbit-element/model family to which TLE
  and the corresponding OMM data belong.
- **HEALPix — Hierarchical Equal Area isoLatitude Pixelization:** a
  hierarchical equal-area tessellation of the sphere.
- **HTTP — Hypertext Transfer Protocol:** the protocol used by provider web
  services.
- **IAU — International Astronomical Union.**
- **ICRS — International Celestial Reference System:** the adopted
  barycentric celestial reference system.
- **ITRS — International Terrestrial Reference System:** the Earth-fixed
  terrestrial reference system.
- **LEO — low Earth orbit.**
- **MEO — medium Earth orbit.**
- **NORAD — North American Aerospace Defense Command:** the historical source
  of the catalogue-number terminology retained in `NORAD_CAT_ID`.
- **OMM — Orbit Mean-Elements Message:** the CCSDS extensible message standard
  used to exchange mean orbital elements and their metadata.
- **PSF — point-spread function:** an instrument's response to a point source.
- **RA — right ascension.**
- **SGP4 — Simplified General Perturbations 4:** the propagation model paired
  with public GP mean elements.
- **SHA-256 — Secure Hash Algorithm with a 256-bit digest:** used to identify
  exact immutable bytes.
- **SVG — Scalable Vector Graphics:** Wenu's editable vector-output format.
- **TEME — True Equator, Mean Equinox:** the reference frame convention of an
  SGP4 state; despite its name, it is not ICRS or an observer frame.
- **TLE — two-line element set:** the legacy fixed-width serialization of GP
  mean elements.
- **TT — Terrestrial Time:** a uniform time scale used in astronomical
  transformations.
- **URL — Uniform Resource Locator:** the address of a provider resource.
- **UT1 — Universal Time 1:** Earth-rotation angle expressed as a time scale.
- **UTC — Coordinated Universal Time:** the civil time scale used for Wenu
  query instants and OMM epochs.
- **WCS — World Coordinate System:** metadata mapping instrument/image
  coordinates to celestial coordinates.
- **XML — Extensible Markup Language:** a structured text serialization.

OMM and TLE are not two competing propagation models. A provider can publish
the same GP/SGP4 mean-element solution in either representation. TLE is a
compact historical card format with fixed columns, a two-digit epoch year, and
a five-character catalogue-number field. OMM is a metadata-rich CCSDS message
that names the object, epoch, reference frame, time system, centre, and mean
element theory explicitly and supports larger catalogue identifiers. Wenu
therefore treats OMM as the canonical data model and translates legacy TLE
into it before any propagation.

## 3. Scientific product

The primary product is a field-crossing query. Given:

- an observer location;
- a start and stop instant spanning minutes to hours;
- a field centre and an explicitly framed spherical footprint;
- optional exposure start instants and durations; and
- an immutable orbit-catalogue snapshot;

Wenu returns every artificial satellite whose apparent topocentric trajectory
intersects the closed field during the inclusive interval.

The same evaluated events support statistical studies versus local time at
night, season, observer, pointing, field size, and exposure duration. Drawing
selected tracks is a later consumer, not the definition of a crossing.

Four results remain scientifically separate:

1. **geometric crossing:** whether and when the trajectory intersects the
   field;
2. **illumination:** whether direct sunlight reaches the satellite under a
   declared shadow model;
3. **apparent brightness:** a passband-specific model value or distribution;
4. **detector contamination:** signal, saturation, masking, or detectability
   for a particular instrument and exposure.

No later stage may change the result of an earlier geometric crossing test.

## 4. Canonical satellite flow

The proposed scientific flow is:

```text
provider-neutral crossing query
    -> SatChecker adapter and cached response
    -> normalized crossing result
    -> reports and shared Wenu chart pipeline

later local provider
    -> validated immutable OMM/TLE snapshot
    -> SGP4 geometric TEME state
    -> declared Earth-orientation transformation
    -> observer-relative topocentric state
    -> exact trajectory/footprint intersection
    -> conservative candidate filters
    -> optional HEALPix/time index
    -> the same normalized crossing result
    -> illumination, optional photometry, and later contamination
```

Acquisition never occurs inside propagation, field search, chart construction,
rendering, or export. Candidate indexing accelerates the exact calculation but
does not become a second propagation authority.

## 5. Identity and catalogue snapshot

### 5.1 Canonical ingestion model

The Orbit Mean-Elements Message (OMM) vocabulary is the canonical ingestion
model. Preserve, when supplied:

- `OBJECT_NAME`;
- `OBJECT_ID` or international designator;
- `NORAD_CAT_ID`, without a five-digit limit;
- classification;
- element-set and revolution numbers;
- element epoch;
- centre, reference frame, time system, and mean-element theory;
- mean motion and its derivatives, eccentricity, inclination, right ascension
  of ascending node, argument of pericentre, mean anomaly, and `BSTAR`;
- provider-specific source and solution metadata.

Legacy TLE is an input adapter only. It must produce the same typed internal
record and must not define the internal identity model. Catalogue identity,
international designator, display name, and one exact orbit solution remain
separate values.

### 5.2 Snapshot identity

A snapshot is a frozen copy of the provider's orbit catalogue at one declared
retrieval instant. It is not a set of satellite positions and it is not an
image of the sky. It contains the orbital-element solutions from which Wenu
can later propagate positions for requested times. Freezing those inputs is
what makes a calculation reproducible after the provider has replaced its
live elements with newer orbit solutions.

An immutable snapshot records:

- provider and authoritative endpoint;
- exact query parameters and response bytes;
- retrieval instant;
- media type, schema, and format version;
- SHA-256 digest;
- every retained element record and its epoch;
- deterministic duplicate-resolution and ordering policy;
- validation result and software version;
- applicable provider notice, policy URL, and policy-check date.

Ordinary queries use an already published snapshot. Refresh is an explicit
acquisition operation. A derived observer/night index always names the exact
snapshot digest from which it was built.

## 6. Provider policy

Provider policy is a scientific reproducibility and operational-safety input,
not merely a networking detail. It must be rechecked before any change to
endpoint, workload, concurrency, cadence, caching, retry, packaging, or
redistribution.

### 6.1 CelesTrak candidate policy

As checked on 2026-09-14, CelesTrak requests clients to use cached GP data by
default, check for updates no more often than once every two hours, request
only needed data, inspect HTTP status, and stop/report errors rather than
retrying. Wenu's proposed adapter therefore uses one supported bulk request,
serial access, validation before atomic publication, and no automatic retry.

OMM-compatible CSV or XML is preferred to legacy TLE because new catalogue
identifiers exceed TLE's five-digit field. Redistribution is not authorized by
this guide and requires a separately recorded licensing decision.

### 6.2 Space-Track candidate policy

Space-Track requires an account and publishes request and bandwidth guidance.
It is not the automatic Wenu default. A future adapter is opt-in,
credential-external, serial, bulk-oriented, and cached. Account-derived data
must not be packaged or redistributed without explicit permission under the
then-current terms.

### 6.3 SatChecker role

IAU CPS SatChecker is Wenu's first bounded online crossing provider and an
external comparison oracle for selected ephemerides, range, motion,
illumination, and circular-field candidates. Fernando accepted the 50S.2A review on 2026-09-15. It covers
SatChecker 1.8.0 at commit `a638d72`. Its current service samples at one-second
steps with a stop-exclusive grid and accepts points within 1.2 times the
requested radius. It therefore supplies a candidate envelope and sampled
evidence, not exact connected crossing events.

Wenu's provider-neutral domain remains authoritative. The adapter must record
the explicit UTC-to-UT1 conversion, source-inferred geometric topocentric
ICRF/ICRS-oriented coordinate meaning, exact request and response receipts,
orbit source/epoch, provider version, async progress, and limitations.
Submissions and polls are serial, automatic retry is forbidden, and ordinary
tests are network-free. Exact response bytes remain local until provider-data
redistribution terms are clarified. SatChecker is not the sole long-term
production dependency because later reproducible queries must work from a
frozen local snapshot without relying on service availability.

## 7. Propagation and reference systems

### 7.1 SGP4 contract

General-perturbations elements are mean elements fitted for SGP4. They are not
osculating Keplerian elements and must not be silently propagated with a
two-body or unrelated numerical model.

Wenu will use a Vallado-compatible SGP4 implementation verified against the
published reference vectors. Scalar and array evaluation must implement the
same model and error behavior. Each result retains propagator identity and
version, element epoch, evaluation instant, time offset from the element
epoch, and SGP4 status/error code.

### 7.2 TEME is an explicit state

The SGP4 Cartesian result is geometric TEME position and velocity. TEME is not
ICRS, GCRS, ITRS, or topocentric AltAz. It must remain typed until a declared
transformation consumes it.

The transformation chain declares:

- input and output frames;
- UTC and any internal UT1 or TT conversion;
- polar motion and Earth-orientation data source;
- observer geodetic datum, longitude, latitude, and height;
- refraction policy;
- output physical status and axes.

Refraction is off by default for astronomical field intersection. If an
observed/refracted field is later supported, it is an explicit policy and must
be applied consistently to both satellite directions and the field boundary.

### 7.3 Freshness and uncertainty

Element age is always reported. There is no universal age cutoff because drag,
maneuvers, orbit regime, required timing precision, and field size differ.
Invalid or decayed records fail explicitly. A stale but propagatable record
may remain in a result with a warning unless the query declares an exclusion
policy.

An element age or published mean residual is not a per-event covariance.
Wenu must not present an unquantified prediction as a confidence interval.
Future covariance or empirical along-track uncertainty is additional state,
not a reinterpretation of SGP4 output.

## 8. Field and crossing definitions

### 8.1 Field

A field is spherical scientific geometry independent of chart projection.
Initially planned forms are:

- circular field, defined by centre and angular radius;
- spherical rectangle, defined by centre, orientation, width, and height;
- WCS or instrument footprint, defined by a validated spherical boundary.

The field declares its coordinate frame and position status. Boundary touch
counts as intersection. RA wrap, poles, and projection seams are handled by
spherical geometry, never by an unqualified RA/Dec bounding box.

### 8.2 Query interval

Start and stop are explicit UTC instants and the interval is inclusive.
Exposure windows, when supplied, retain exact start and duration. A trajectory
may enter the same field more than once; disconnected visits are separate
crossing events.

### 8.3 Crossing record

An exact event retains at least:

- satellite and orbit-solution identity;
- snapshot digest and element epoch;
- observer and coordinate policy;
- field identity and boundary convention;
- entry and exit instants;
- closest-approach instant and angular separation;
- time in field;
- range and angular rate at declared event instants;
- overlap and trail length for each exposure;
- illumination/shadow state and prediction warnings;
- solver tolerance and software provenance.

## 9. Complete-scan correctness oracle

The first *local* implementation scans every valid object in the small
representative snapshot. A fixed sampling grid alone is not a completeness
proof because a fast LEO pass may cross a narrow field between samples.

The oracle uses adaptive interval subdivision with a conservative motion
bound. Intervals that cannot exclude the field are subdivided or refined using
bracketed boundary roots and closest-approach extrema. It must remain callable
after optimization so 50S.6 can compare every accelerated result against it.

For topocentric relative position `rho` and velocity `rho_dot`, instantaneous
angular speed is

```text
omega = |rho x rho_dot| / |rho|^2.
```

No catalogue-independent finite maximum is safe because angular speed grows
as range decreases. A conservative interval must retain a lower range bound
and an upper transverse-speed/curvature bound. Near-zenith or otherwise
singular intervals subdivide or fall back to exact evaluation; they are never
rejected merely because the bound is loose.

## 10. Conservative high-performance search

The first local acceleration is a cascade of conservative geometric and state
filters:

1. orbital-plane/FoV-cone intersection over the admissible radial shell;
2. element-epoch phase and reachable-orbital-arc rejection;
3. Earth-occultation and geometric-horizon rejection over the interval;
4. vectorized coarse SGP4 states with angular-motion and curvature bounds;
5. exact refinement of every retained candidate.

For observer position `r_o`, sight direction `u`, satellite range `rho`, and
orbital-plane normal `n`, a possible line-of-sight state satisfies
`n . (r_o + rho u) = 0`. The admissible positive range, orbit radial shell,
FoV cone, interval, and conservative perturbation margin are all required.
Testing only the angular distance to a geocentric orbital great circle is
unsafe for low satellites because topocentric parallax is large.

For repeated pointings or larger snapshots, a time-slab and
hierarchical-sky-pixel index may add another candidate stage:

1. vectorize SGP4 over satellite batches and bounded time slabs;
2. construct a conservative swept spherical cover for each object/slab;
3. dilate the cover for footprint radius, between-sample motion and curvature,
   transformation/numerical allowance, and boundary tolerance;
4. map `(time slab, sky pixel)` to candidate satellite identifiers;
5. refine every candidate using the exact crossing solver.

HEALPix is the leading pixelization candidate, not yet a mandated dependency.
The small-snapshot specimen builder and complete oracle use brute force first.
Benchmarks must show that an index materially improves medium/full-snapshot or
repeated-night workloads before Wenu adopts it. A simple inverted index is
preferred to an opaque combined space-time tree. An isolated query may build
ephemeral bounds; repeated pointings may reuse an immutable observer/night
index.

The index key includes snapshot digest, observer, Earth-orientation policy,
interval, sampling/bounding policy, SGP4 implementation and version, and Wenu
software version.

The acceptance invariant is zero false negatives against the complete scan.
False candidates affect performance and are measured, but do not invalidate
scientific completeness. Unsafe approaches include nearest sampled-point
tests, unconstrained interpolation, plain RA/Dec boxes, and any index without
an exact fallback.

## 11. Illumination

Illumination uses explicit Sun-Earth-satellite-observer geometry. The minimum
accepted physical model distinguishes sunlight, penumbra, and umbra using the
finite angular size of the Sun. Model inputs, ephemeris, Earth shape, and
boundary tolerance are retained.

Atmospheric refraction and absorption near shadow ingress and egress can
modify observed brightness. They remain separate from the minimum geometric
shadow state until a model is selected and empirically validated.

## 12. Apparent brightness

### 12.1 Required inputs

A reflected-sunlight model declares, when known:

- photometric passband and solar magnitude or spectrum;
- observer range and solar phase angle;
- spacecraft shape and projected area;
- attitude law, appendage orientation, and tumbling state;
- diffuse/specular reflectance or empirical phase function;
- shadow state;
- atmospheric-extinction policy;
- model family, calibration data, valid domain, and uncertainty.

Range and phase alone do not determine brightness. Unknown attitude, surface
properties, and specular geometry may dominate the observed flux.

### 12.2 Model hierarchy

Wenu uses the most specific defensible level:

1. `unknown` when no supported empirical or physical model exists;
2. a population distribution for a defensible object class and orbital regime;
3. a satellite-family magnitude distribution normalized to a declared range
   and conditioned on available geometry;
4. an object-specific empirical model supported by observations;
5. a diffuse physical model with explicit size, attitude, and reflectance
   assumptions;
6. a spacecraft-specific attitude/BRDF model with published parameters and
   independent validation.

A result is labelled model magnitude or magnitude distribution, never
guaranteed brightness. Ordinary brightness and glints remain separate:
missing flare evidence produces `unknown`, never zero flare probability.
Scatter, bias, outliers, unmodeled glints, and tumbling limitations are
reported. A single standard magnitude does not replace a phase function.

### 12.3 Validation

Before 50S.8 acceptance, compare at least two materially different satellite
families over varied range, phase, elevation, and illumination geometry using
calibrated, time-resolved observations. Report passband transformations,
range normalization, residual bias and scatter, outliers, phase coverage,
and orbit-age or trajectory-timing contribution.

### 12.4 Detector contamination is later

Trail signal or detectability also depends on angular speed, exposure time,
optics, aperture, throughput, defocus and PSF, pixel scale, sky background,
saturation, blooming, and detector response. Those belong to a later
instrument model and must not be inferred from apparent magnitude alone.

## 13. Cached development data and specimen construction

Development uses provider data from cache wherever possible. Ordinary unit,
focused, documentation, and full tests are network-free. Reviewed exact raw
responses may become committed fixtures; provider-contract tests prefer cache;
live checks are explicit, serial, bounded, policy-checked, and never ordinary
pytest gates. Refresh creates new immutable bytes rather than overwriting a
reproducibility specimen.

Local development begins with a small representative OMM snapshot spanning
orbit regimes, inclinations, eccentricities, object classes, shared orbital
planes with different phases, fast and grazing passes, Earth occultation,
shadow transitions, known/unknown photometry, aged elements, and parser fault
cases. Larger retained snapshots follow only after the complete machinery is
correct.

The bounded 50S.4E developer specimen builder accepts the installed synthetic snapshot,
observer, evaluation grid, and FoV size. It stores propagated sampled tracks
and query inputs only. It does not find a useful field automatically, emit
expected crossings, invoke a crossing query, calculate entry/exit or closest
approach, or certify central, grazing, between-sample, multiple-crossing,
non-crossing, horizon, shadow-transition, seam, or polar cases. Those
crossing-oracle responsibilities belong to 50S.5. The future 50S.5
dense/adaptive brute-force reference path must remain independent of production
rejection filters.

## 14. Validation hierarchy

The satellite program uses independent layers of evidence:

1. Vallado SGP4 reference vectors for raw TEME states;
2. independent SatChecker or Space-Track comparisons for selected propagated
   directions and ranges;
3. direct coordinate-chain comparisons across observers and orbit regimes;
4. observed trajectory timing for representative passes;
5. exact complete scan against analytic/adversarial field crossings;
6. optimized index against the complete-scan oracle;
7. calibrated photometry for each accepted brightness model;
8. human and machine inspection of reports and, later, shared chart outputs.

Adversarial crossing cases include grazing contact, boundary touch, RA seam,
polar fields, horizon proximity, fast zenith LEO motion, short exposure,
interval endpoints, high eccentricity, multiple visits, stale elements, and
propagation error states.

## 15. Performance evidence

Correctness development begins with the small representative snapshot.
Performance acceptance later uses progressively larger retained snapshots and
a recorded current full-catalogue snapshot rather than only the reduced
fixture. Measure:

- cold snapshot parsing and propagation setup;
- exact complete-scan time;
- cold index construction;
- warm index reuse and query latency;
- peak memory and persisted index size;
- retained-candidate and false-candidate counts;
- scaling with catalogue size, interval, cadence, field size, exposure count,
  and number of pointings.

Representative workloads include LEO, MEO, GEO, and highly elliptical orbits;
wide and narrow fields; seconds-to-minutes exposures; twilight and deep night;
one query and many pointings over a night; and observers at low, middle, and
high latitude.

Measured maxima tune performance but never replace conservative bounds or the
complete-scan equivalence test.

## 16. Source ownership direction

The 50S.1 admission review found no existing owner for provider-neutral
satellite field and crossing semantics. `coordinates.py` remains the coordinate
vocabulary owner, `ephemeris.py` remains the Cartesian state boundary, and the
minor-body, moving-track, chart, renderer, and report owners have different
lifecycles and failure modes.

`satellite_crossings.py` therefore owns the first immutable satellite-domain
contracts: `SatelliteIdentity`, `SatelliteObserver`,
`SatelliteFieldOfView`, `InclusiveTimeInterval`,
`SatelliteCrossingCandidate`, and `SatelliteCrossingResult`. The first field
is circular, spherical, explicitly framed, and closed. A candidate binds
identity, observer, field, interval, source, optional orbit/snapshot evidence,
provenance, and warnings. A normalized result represents one connected visit,
keeps ordered entry, closest-approach, and exit instants inside the inclusive
query interval, and accepts boundary touch.

This is a distinct scientific-domain responsibility: it owns neither provider
acquisition nor propagation and is independent of chart projection. A
`src/wenu/satellites/` package remains deferred until snapshot ingestion, SGP4
state, crossing geometry, indexing, illumination, and photometry form several
collaborating production modules. Later work must not duplicate Wenu's
coordinate service, trajectory geometry, projection, preparation, renderer,
semantic SVG, or export machinery.

Fernando accepted these 50S.1 contracts and ownership boundaries on 2026-09-15.
The focused Mac gate passed all 139 tests in 3.07 seconds, the complete
plugin-disabled suite passed all 2,428 tests in 85.52 seconds, and PR #123
merged the verified implementation into the satellite integration branch as
`23b851b`.

The accepted 50S.2B provider module is `satchecker.py`. It owns exact
versioned request translation, explicit no-download UTC-to-UT1 conversion,
immutable response receipts, one-shot submit/poll access, provider task/schema
normalization, ordered sampled evidence, and the content-addressed local cache.
It imports the 50S.1 contracts rather than redefining them. The adapter accepts
only geometric topocentric-direction ICRS fields and never constructs an exact
connected-visit result. `tests/test_satchecker.py` is the durable provider
boundary owner; ordinary tests inject transport and remain network-free. The
bounded live check reached real HTTP 200 PENDING states and a later SUCCESS
receipt; the adapter normalized 13 candidates and 26 ordered samples while
retaining the candidate-only boundary.

## 17. Milestone evolution

- **50S.0:** maintain this literature, provider-policy, scientific, and
  architecture guide; no runtime behavior.
- **50S.1:** provider-neutral identity, observer, FoV, interval, candidate, and
  crossing-result contracts; no propagation yet.
- **50S.2A:** accepted audit of SatChecker endpoints, time and coordinate semantics,
  candidate envelope, async policy, exact cache, failures, and redistribution.
- **50S.2B:** accepted cached circular-field adapter, candidate-only
  normalization, provider-sampled evidence, explicit progress, and exact cache.
- **50S.3A:** accepted audit of honest human-readable/JSON reports and FoV charts from
  provider-sampled candidate evidence, with no invented exact crossing events.
- **50S.3B:** accepted deterministic reports plus drawable sampled-track and
  sample-point layers through the shared renderer/export path; provider
  illumination remains separate evidence.
- **50S.4A:** audit direct dependency, OMM/snapshot, SGP4/TEME,
  Earth-orientation/topocentric validation, and specimen contracts.
- **50S.4B:** canonical OMM elements and a tiny immutable synthetic snapshot.
- **50S.4C:** Vallado-validated SGP4 and typed geometric TEME state.
- **50S.4D:** independently validated no-download topocentric transformation.
- **50S.4E:** network-free propagated-specimen builder and 50S.4 closure.
- **50S.5:** complete local catalogue scan and adaptive exact-crossing oracle.
- **50S.6:** conservative plane, radial-shell, phase/reachable-arc,
  occultation, and coarse-state filters; add HEALPix/time indexing only if
  measured larger-snapshot workloads justify it; prove zero false negatives.
- **50S.7:** independent Sun/penumbra/umbra and observer-night geometry.
- **50S.8:** empirically validated object, family, and population brightness
  models with explicit `unknown` and separate glint limitations.
- **50S.9:** instrument-specific trail signal and detector contamination.
- **50S.10:** statistical products versus night time, season, observer,
  pointing, FoV, and exposure duration; close the program after numerical,
  performance, report, and visual acceptance.

Fernando accepted 50S.2B on 2026-09-15 after 45 provider/domain tests, 168
expanded focused tests, all 2,457 tests, and the bounded live provider check
passed. Fernando accepted 50S.3A on 2026-09-15; only the bounded 50S.3B implementation is authorized next.

At every milestone, revise this living guide to match accepted science and
implemented ownership. When 50S foundation work is merged, decide explicitly
whether this guide remains separate or is integrated into
`coordinate_system_guide_v0.9.5.md`; do not merge documents mechanically.


## 18. 50S.3 sampled-evidence presentation boundary

The 50S.3A admission review found reusable coordinate, projection,
preparation, renderer, semantic SVG, and export paths, but no existing
satellite report owner. `SolarSystemTrackResult` is not reusable as a data
type because it means ephemeris realization, while SatChecker supplies ordered
provider samples.

Every 50S.3 product must therefore identify its content as **SatChecker sampled
candidate evidence — not verified crossings**. Human-readable reports, JSON,
and charts consume the same already-normalized SUCCESS result. Two or more
samples may form one open polyline in supplied order; a singleton remains a
point. No interpolation, propagation, entry, exit, closest approach, continuous
containment, illumination calculation, magnitude, or detector consequence may
be inferred.

Chart geometry declares geometric topocentric-direction ICRS and follows
`CelestialSphere.draw_chart()`. Semantic identity uses the full NORAD
catalogue identifier rather than provider order or display name. Provider
illumination, if present, remains separately attributed evidence and cannot
change track admission or style.

Fernando accepted 50S.3A on 2026-09-15 after all 126 focused documentation
tests and the candidate diff check passed. The audit itself changes no runtime
behavior. Acceptance authorizes only bounded renderer-neutral reports and a
drawable sampled-candidate layer in 50S.3B.


## 19. Accepted 50S.3B implementation

`satellite_presentations.py` now provides one deterministic presentation
model over a terminal normalized SatChecker response. Text and JSON share the
same document, retain query and receipt provenance, sort candidates by full
NORAD catalogue identifier, preserve supplied samples in temporal order, and
state that the product is not a verified crossing report.

`sky/satellite_candidate_layer.py` supplies two cooperating ordinary layers.
The track layer returns an open curve for two or more samples and a point for a
singleton. The samples layer returns only supplied points and may expose their
exact normalized UTC instants as labels. Both assemble multi-instant geometric
topocentric-direction ICRS evidence with per-sample time metadata, then use the
accepted fixed chart-product transformation convention and canonical
`CelestialSphere.draw_chart()` pipeline.

Stable semantic identity is based on the full NORAD catalogue identifier.
Names remain display labels. Provider illumination is retained only in
metadata/report evidence and does not control geometry or style. There is no
entry, exit, closest approach, interpolation, propagation, network, cache-read,
retry, CLI, local catalogue, brightness, or detector behavior.

The candidate focused gate passed 90 tests, including actual Matplotlib
PNG/PDF/SVG serialization through the canonical chart pipeline. Fernando then
accepted the regenerated network-free specimen on 2026-09-15: the explicit
closed circular FoV annotation, red ordered sample path, four UTC annotations,
candidate-only title, and PNG/PDF/SVG products were correct. The final expanded focused gate passed all 217 tests, and the complete
plugin-disabled suite passed all 2,473 tests in 83.98 seconds. Fernando accepted 50S.3B on 2026-09-15. This closes SatChecker sampled
candidate reporting and drawing; only the documentation-only 50S.4A audit is authorized next.


## 20. 50S.4 snapshot and propagation admission review

The 50S.4A review separates five responsibilities that cannot share one
acceptance boundary: contract audit, immutable snapshot/domain, SGP4/TEME
propagation, Earth-orientation/topocentric transformation, and developer
specimen construction.

Wenu will declare `sgp4>=2.25,<3` directly rather than relying on Skyfield's
transitive dependency. The adapter will use explicit WGS-72 OMM
initialization, split Julian dates, typed geometric TEME position/velocity,
and explicit status codes. It will be a wrapper around the upstream
Vallado-compatible implementation, not a copied propagator.

The first installed snapshot will be a tiny hand-authored synthetic OMM/GP
collection spanning LEO, MEO, and geosynchronous-like geometry. It is
non-operational and avoids redistributing live provider data. Full integer
NORAD identity, UTC epoch, TEME/Earth/SGP4 declarations, exact canonical
content, SHA-256 identity, provenance, and validation remain mandatory.

Topocentric work will follow Astropy's documented TEME-to-ITRS and
observer-subtraction chain with automatic IERS download disabled. Results
retain EOP identity and fail outside available coverage. A separate numerical
stage must settle the name and convention of an instantaneous geometric
topocentric vector expressed in celestial axes; it must not be called
geometric ICRS merely because the axes are ICRS-oriented.

The developer builder will emit **propagated sampled specimens — not verified
crossings**. It cannot create `SatelliteCrossingResult` or claim completeness;
those belong to 50S.5.

Fernando accepted the documentation-only 50S.4A audit on 2026-09-15 after
the focused gate passed all 128 tests and the branch diff check was clean.
50S.4A changed no runtime, dependency, or package data. It is now closed, and
only 50S.4B immutable OMM element and snapshot work is authorized next.


### Accepted 50S.4B immutable OMM snapshot

The dedicated 50S.4B branch implements only the element/snapshot boundary
authorized by 50S.4A. `SatelliteElementRecord` retains all required OMM mean
elements, full six-digit synthetic NORAD identity, canonical UTC epoch,
`EARTH`/`TEME`/`UTC`/`SGP4` declarations, source-record digest, and
provenance. Invalid, incomplete, unknown-field, non-finite, wrong-frame, or
wrong-theory input fails closed.

`SatelliteElementSnapshot` and its manifest enforce exact canonical JSON
bytes, content and per-record SHA-256 identities, record count, ascending full
NORAD ordering, duplicate rejection, immutable lookup, and installed-resource
loading. The first snapshot contains only three hand-authored, non-operational
LEO-like, MEO-like, and geosynchronous-like specimens. It copies no live
CelesTrak, Space-Track, SatChecker, or tracked-object record.

The branch declares `sgp4>=2.25,<3` directly so installation owns its future
propagation dependency. It deliberately constructs no propagator and produces
no TEME state, terrestrial/topocentric transformation, field intersection, or
crossing result. Those remain gated by 50S.4C and later milestones.

At production commit `d3cb597`, all 158 expanded focused tests and all 2,483
complete-suite tests passed. The wheel was then installed into an isolated
virtual environment and the snapshot loaded from `site-packages` with exact
digest
`b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457`,
record count three, and ordered identifiers 900001–900003. The first two
wheel-import attempts exposed unrelated environment issues—missing
dependencies in a no-dependency environment and a broken inherited
`spiceypy` shared library—before the package-local resource check isolated
the intended boundary. Neither failure involved the snapshot. Fernando
accepted 50S.4B on 2026-09-15. The immutable snapshot boundary is closed, and
only 50S.4C validated SGP4/TEME propagation is authorized next.


### Accepted 50S.4C SGP4 and geometric TEME state

The 50S.4C adapter is deliberately narrow: canonical OMM record → explicit
WGS-72 Vallado-compatible `Satrec` → immutable successful geometric TEME
state, or an explicit `SatellitePropagationError`. It retains split Julian
dates, element age, upstream version/backend, operation mode, source/snapshot
identity, and units. It does not silently accept NaNs or non-zero statuses.

The published Vallado verification vectors for near-Earth satellite 5 and
deep-space satellite 4632 are pinned as wrapper oracles. A published decaying
case verifies terminal error propagation. Scalar and accelerated-array routes
agree within the declared sub-millimetre position tolerance.

The 50S.4C preflight caught that the original synthetic identifiers
900001–900003 cannot be represented by upstream `Satrec`, whose current
maximum is 339999. The corrected installed snapshot uses 300001–300003,
preserving six-digit identity while remaining valid for the actual propagator.
All record digests and the snapshot digest changed accordingly; Wenu never
substitutes an internal ID.

Every result remains geocentric geometric TEME. No Earth rotation, polar
motion, ITRS state, observer subtraction, range, AltAz, celestial direction,
FoV test, or drawing occurs in this milestone.

At production commit `e0d7c78`, all 167 expanded focused tests and all 2,492
complete-suite tests passed. An isolated installed wheel loaded the corrected
snapshot from `site-packages` and propagated identifiers 300001, 300002, and
300003 at 2026-09-15T00:10:00Z. Each result reported TEME, WGS-72, status zero,
and finite position and velocity. Fernando scientifically and architecturally
accepted 50S.4C on 2026-09-15. The SGP4/TEME boundary is closed, and only
50S.4D Earth-orientation and topocentric state work is authorized next.


### Accepted 50S.4D local topocentric state

The candidate local path is:

```text
canonical OMM record
    -> WGS-72 SGP4 geometric TEME state
    -> explicit installed IERS-A TEME-to-ITRS transform
    -> WGS-84 observer subtraction in Cartesian ITRS
    -> range plus vacuum geometric AltAz
    -> optional topocentric geometric direction in GCRS axes
```

Every result retains the full source TEME state, observer, satellite and
observer ITRS vectors, topocentric vector/velocity, range, angular directions,
exact IERS-A SHA-256 and coverage, interpolated UT1−UTC and polar motion,
software versions, coordinate identity, provenance, and warnings. Automatic
IERS download and degraded accuracy are disabled; out-of-coverage instants fail
closed.

The GCRS-axis longitude/latitude are not an ICRS position, formal geocentric
GCRS coordinate, astrometric place, apparent place, or observed direction.
They are the instantaneous observer-subtracted geometric vector expressed in
celestial axes. Refraction, field intersection, exact visits, illumination,
brightness, detector effects, reporting, drawing, and specimen generation are
not part of 50S.4D. Fernando scientifically and architecturally accepted this
boundary on 2026-09-15. Only the bounded 50S.4E propagated-specimen builder is
authorized next.

### Accepted 50S.4E propagated specimen builder

The candidate `tools/build_50s4_satellite_specimens.py` tool loads the
installed three-record synthetic snapshot and evaluates an explicit ordered
UTC grid for the La Ligua observer by default. Its one JSON product records
snapshot and record digests, evaluation grid, observer, exact IERS-A identity
and sampled values, SGP4 identity, WGS-72 policy, Wenu version, TEME states,
topocentric states, and query inputs.

The product is explicitly labelled **propagated sampled specimens — not
verified crossings**. It is deterministic for identical installed resources
and arguments, performs no network access, and writes only below the required
caller-selected output directory. It contains no `SatelliteCrossingResult`,
entry/exit, closest approach, completeness claim, production tolerance, chart,
or field-search behavior. Focused, full-suite, generated-product, diff, and
Fernando acceptance gates remain pending.

#### Accepted 50S.4E verification result

The dedicated, expanded, and documentation Mac gates passed 10, 99, and 134
tests. The complete plugin-disabled suite passed all 2,522 tests in 105.38
seconds.
The inspected generated product had SHA-256
`16137e9380404dca03789532ab029c4159755c69dd2ab0ca5990a82cd9c42374`
and preserved the exact snapshot, observer, grid, IERS-A, propagator, and
software identities. Its three default synthetic tracks were below the La
Ligua horizon, so the product correctly made no visibility or crossing claim.
The branch and diff checks were clean. Fernando scientifically and architecturally
accepted 50S.4E on 2026-09-15. This closes 50S.4 and authorizes only bounded
50S.5 complete local FoV-crossing oracle work.

50S.6 acceleration and every later satellite milestone remain unauthorized.


## 21. Accepted 50S.5A complete local crossing-oracle audit

The first local oracle is restricted to a fixed closed circular field whose
centre and the accepted 50S.4D trajectory are both topocentric geometric
directions expressed in GCRS axes. Provider apparent ICRS, AltAz, projected
coordinates, and mixed position statuses are rejected rather than compared
numerically.

Every valid record in the selected immutable snapshot is scanned. Completeness
means validated numerical completeness under explicit time and angular
tolerances. Endpoint and midpoint state, topocentric Cartesian motion,
instantaneous angular rate, curvature evidence, and successive refinement form
an operationally conservative envelope. A possible-contact interval
subdivides; a singular or non-converged interval fails closed. A fixed grid,
endpoint signs alone, unconstrained interpolation, and measured
catalogue-wide speed maximum are not completeness evidence.

Bracket-preserving roots establish entry and exit. Bounded minimum refinement
detects tangency without requiring a sign change. Query endpoints are
inclusive, boundary touch counts, disconnected visits stay separate, and
uncertain refinement raises an explicit convergence error. Analytic
trajectory oracles remain independent of SGP4/Astropy composition tests.

This documentation-only review adds no solver. Fernando scientifically and
architecturally accepted it on 2026-09-15. Acceptance authorizes only bounded
50S.5B; 50S.6 and later behavior remain unauthorized.

## 22. Accepted 50S.5B complete local crossing oracle

The accepted `LocalSatelliteCrossingOracle` scans every record in the selected
immutable snapshot and composes the accepted SGP4/TEME and installed-IERS-A
observer chain. It compares only fixed-field and trajectory unit vectors in
GCRS axes. No horizon, orbital-plane, phase, HEALPix, or population filter may
remove an interval or record.

Adaptive subdivision uses endpoint/midpoint separation, topocentric angular
rate, curvature evidence, bounded roots and minima, and recursive
time-and-angular tolerance connectivity. A tangent is retained as one
zero-duration boundary event; disconnected visits remain separate. Failure or
resource exhaustion is explicit and fail closed. This is validated numerical
completeness, not formal interval arithmetic, and it authorizes no runtime 50S.6 work.

Fernando scientifically and architecturally accepted 50S.5B on 2026-09-15.
Only a documentation-first 50S.6 conservative-acceleration audit is authorized
next.

## 23. Accepted 50S.6A conservative crossing acceleration audit

The accepted exhaustive oracle remains the scientific reference. Acceleration
may reject a record only when a complete topocentric field-cone and bounded
orbital-shell envelope, including tolerance and model margins, proves that no
contact is reachable. Uncertainty means retain and solve exactly.

The first proposed implementation stage is the cone/shell selector. Nominal
orbital-plane distance, endpoint sampling, mean anomaly alone, or a fixed
sampling grid cannot establish absence. Horizon and Earth occultation do not
belong in the current geometric query predicate. Phase, coarse vectorized
states, and HEALPix/time indexing require later separate admission and measured
benefit. Fernando scientifically and architecturally accepted 50S.6A on 2026-09-15.
Only bounded 50S.6B implementation of the first cone/orbital-shell selector is
authorized; all later acceleration stages and satellite behavior remain
unauthorized.

## 24. Accepted 50S.6B cone-shell selector

The first selector is intentionally narrow. It supports only the installed
three-record synthetic snapshot and query intervals up to 60 seconds. It
constructs one whole-interval reachable angular cap from an accepted initial
topocentric state and a deliberately inflated orbital-shell speed bound.

A record is rejected only when the cap is strictly disjoint from the closed
field after tolerance and numerical margins. Retain and indeterminate both
mean “send to the exact oracle.” The selector does not use altitude or
occultation, does not sample a nominal track to infer absence, and does not
return crossings or make a performance claim. Fernando scientifically and
architecturally accepted this bounded selector on 2026-09-16. Only a
50S.6C documentation-first coordination and admission audit is authorized next.

## 25. Accepted 50S.6C coordination and admission audit

The proposed accelerated route does not create a second crossing solver.
Exhaustive and accelerated searches must share one exact record operation;
the exhaustive route invokes it for every record, and acceleration may omit
only records carrying a validated conservative reject decision. Retain and
indeterminate both mean exact solve.

Fernando scientifically and architecturally accepted this audit on 2026-09-16.
Only bounded 50S.6D coordination in the existing admitted domain is authorized
next.

Complete ordered decision coverage, invariant checking, fallback, exact-result
equivalence, and fail-closed behavior precede optimization. A selector error or
unsupported query cannot become an empty result. The installed synthetic
three-record snapshot remains a composition fixture, not evidence of useful
speed or broader catalogue validity.

Widening the selector requires immutable regime-covering fixtures and
zero-false-negative comparison with the independent exhaustive oracle.
Performance claims require predeclared representative workloads, repeated cold
and warm measurements, evaluation counts, timing distributions, and material
total-wall-time benefit. This documentation-only candidate authorizes no
runtime coordinator or broader acceleration.


## 26. Accepted 50S.6D bounded accelerated coordinator

The exhaustive crossing oracle remains the default and independently callable.
The accepted coordinator validates the complete ordered result of the accepted
cone-shell selector and calls the same exact record solver for every retain or
indeterminate decision. Only a validated reject may omit exact work.

`solve(query)` returns ordinary exact crossing results.
`solve_with_evidence(query)` additionally returns separate immutable
selection and evaluation accounting. Selector failure falls back to the
complete exhaustive route by default or fails closed under explicit policy;
invalid coverage and rejection outside the installed three-record, 60-second
domain always fail closed.

This accepted implementation makes no useful-speed claim and adds no broader catalogue
domain, default acceleration, new filter, visibility semantics, CLI, report,
or drawing behavior.


Fernando scientifically and architecturally accepted 50S.6D on 2026-09-16.
Broader-domain activation, benchmarking claims, default acceleration, new
filter stages, and later satellite behavior remain unauthorized.


## Accepted 50S.6E multi-FoV and delivery sequence

The proposed primary workload is one observer with any non-empty number of
different FoVs and independently bounded intervals. The centre of every field
must satisfy a configurable airmass limit throughout its complete interval.
The initial policy uses geometric vacuum AltAz and plane-parallel `X = sec(z)`
above the horizon, with `X_max = 2` by default (exactly 30 degrees minimum
centre altitude in this model). Only the centre is checked; the FoV radius does
not enter airmass admission. This is an FoV admission condition, not a
satellite horizon or occultation filter;
it imposes no civil-date or inferred-twilight boundary. Ten FoVs are the
ordinary benchmark and proposed internal chunk, never a hard-coded public
maximum. Disjoint, overlapping, and identical intervals are separate evidence
cases; identical intervals are a maximum-reuse research case.

A bounded 50S.6F implementation would precede representative-scale admission,
generic JSON/ECSV/VOTable reports, and exact binocular/regional/stereographic
tracks in 50S.6G. Direct Paranal or ELT compatibility requires the separate
50S.6H interface audit. 50S.7 then treats Sunlight, solar Earthshine,
Moonlight, and Lunar-Earthshine as separate geometric components; 50S.8 adds
component-resolved flux or magnitude distributions. Fernando scientifically and architecturally accepted 50S.6E on 2026-09-16.
No multi-FoV runtime or later milestone is implemented or automatically
authorized. Only bounded 50S.6F is authorized next.


## Accepted 50S.6F bounded batch implementation

The accepted Python API accepts an immutable ordered non-empty tuple of
complete single-field queries. All fields must share one observer and immutable
snapshot; field identifiers are unique, intervals and exact-solver tolerances
remain independent, and the installed synthetic 60-second domain remains the
only admitted runtime. The field-centre airmass ceiling is configurable and
defaults to 2. The radius is not part of admission.

Validation is atomic and precedes all crossing work. One typed exception
retains every rejected field and reason in input order, preparing a later 50S.6G
file/CLI adapter to write a validation file and resubmit the valid subset
without adding that behavior now. Valid fields are processed in execution-only
chunks of 10 by default and results retain input order. The candidate composes
50S.6D independently per field; it does not yet claim useful acceleration or
shared propagation/topocentric-state reuse. Fernando scientifically and
architecturally accepted 50S.6F on 2026-09-17 after 2,577 plugin-disabled tests
passed. Only a separately bounded 50S.6G audit is authorized next.


## Accepted 50S.6G delivery sequence

The candidate delivery audit separates external immutable snapshot loading,
policy-governed representative acquisition/evidence, canonical reports,
CLI/file workflow, exact drawable evidence, binocular/regional charts, and
stereographic planispheres into separately accepted slices.

Direct Python and CLI requests fail atomically. An invalid JSON request file
solves no FoV but may atomically produce a second validation-output JSON that
marks every failed FoV and embeds the ordered valid subset. Explicitly feeding
that file to a second call revalidates and calculates only the valid subset.

JSON is the canonical nested exchange; ECSV and VOTable encode the same logical
model for scientific interoperability. Exact chart tracks require certified
samples between exact entry and exit and reuse the ordinary Wenu chart path.
They remain geometric crossings; illumination, brightness, detector effects,
and observatory scheduling remain later milestones.
Fernando scientifically and architecturally accepted this sequence on
2026-09-17 after all 145 plugin-disabled current-documentation tests passed in
4.36 seconds. Only bounded 50S.6G.1A external immutable snapshot loading is
authorized next.


## Accepted 50S.6G.1A external snapshot loading

The accepted Python seam loads one explicitly selected local immutable
snapshot directory and returns the same `SatelliteElementSnapshot` used by the
installed synthetic route. The directory name is operational only; the
validated manifest and canonical records digest retain scientific identity.

The directory and both required files must be real non-symlink filesystem
objects. Every manifest, canonical JSON, digest, full-NORAD, ordering, OMM,
epoch, provenance, warning, and count check is shared with the installed
loader. This slice neither obtains nor publishes data and does not broaden the
three-record, 60-second crossing domain.

Fernando scientifically and architecturally accepted 50S.6G.1A on 2026-09-17
after the 164-test focused gate and all 2,583 plugin-disabled tests passed.
Only a separately bounded 50S.6G.1B audit is authorized next.


## Accepted 50S.6G.1B representative snapshot preflight

The candidate audit makes policy a frozen reproducibility input. Wenu first
records the exact official CelesTrak policy bytes and digest; a later
acquisition requires explicit acknowledgement of that digest before a single
fixed Active-group CSV request. Network failure, redirect, changed policy, or
invalid data stops without retry and publishes nothing.

CelesTrak Active is a large representative population, not a complete census
of payloads, rocket bodies, debris, analyst, restricted, or lost objects. Raw
response and policy bytes remain local. A deterministic medium tier is derived
offline from the same parent response, while the installed synthetic snapshot
remains the fast oracle. Exact equality and resource evidence are bound to the
canonical snapshot digest; ordinary runtime defaults do not change.

Fernando scientifically and architecturally accepted 50S.6G.1B on 2026-09-17
after all 147 plugin-disabled current-documentation tests passed in 4.54
seconds. Only bounded 50S.6G.1B.1 fake-transport implementation is authorized
next; policy-digest approval for live acquisition remains separate.

### Offline 50S.6G.1B.1 builder

The implemented builder freezes exact policy bytes and requires their SHA-256
as the acquisition acknowledgement before invoking an injected GP transport.
It accepts only the fixed Active CSV header, preserves full NORAD identifiers,
adds only the four documented OMM constants, sorts by full NORAD identity, and
publishes only after typed-record and explicit-directory validation succeed.
The included developer command consumes local response files only. No live
transport, representative admission, or evidence matrix is implemented.

Fernando accepted 50S.6G.1B.1 on 2026-09-17 after 175 focused tests and all
2,594 plugin-disabled tests passed. No live provider access was exercised or
authorized by that acceptance.

A future provider may be audited only if it is public, reliable, and genuinely
independent in observation or orbit determination, rather than a mirror of
CelesTrak or Space-Track. It must have stable machine-readable access, explicit
policy and provenance, complete identifiers, and an auditable OMM-compatible
mapping. Introduce it first as a separate validation oracle, never as silent
fallback, automatic merge, or replacement of the authorized provider.

Fernando accepted the exact `non-HTTP 200` policy-clause compatibility
correction on 2026-09-17 after 10 focused tests and all 2,595 plugin-disabled
tests passed. The frozen 14,643-byte response has SHA-256
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`. The acceptance covers the parser and receipt only; it does not
approve a GP request or the digest acknowledgement required before one.

The first external Active snapshot contains 16,559 records. Its retained raw
response SHA-256 is `e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014`; its canonical-record SHA-256 is
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`. CelesTrak's suffix-free six-fractional-digit `EPOCH` is UTC
by the provider contract and is stored with explicit `Z`; the captured HTTP
media type remains `text/plain; charset=UTF-8`. Fernando accepted this repair
and snapshot on 2026-09-17 after 15 focused and 2,600 complete plugin-disabled
tests. No second provider request or 50S.6G.1B.2 work was authorized.


## Accepted 50S.6G.1B.2A external admission

The validated Active snapshot is not an ordinary runtime default. The
accepted admission boundary requires its exact canonical-record SHA-256 plus
validated manifest identity through one explicit evidence-only token shared by
the conservative selector, accelerated coordinator, and multi-FoV batch.
Logical `snapshot_id`, directory name, raw-response digest, or policy digest
alone cannot authorize scientific use. Unsupported records remain
indeterminate or fail closed and must reach the accepted exact path where
required. Fernando scientifically and architecturally accepted this boundary
on 2026-09-17 after all 150 plugin-disabled current-documentation tests passed
in 3.84 seconds. Only bounded 50S.6G.1B.2B implementation is authorized next.


## Accepted 50S.6G.1B.2B admission

External evidence now requires an explicit immutable token created after exact
canonical-digest and manifest-identity comparison. The accepted CelesTrak
identity constant is inert: it neither locates nor loads the external
directory. The same token is checked by the conservative selector, accelerated
coordinator, and multi-FoV batch before their respective external work.

Missing, forged, mismatched, or substituted admission fails closed. Existing
synthetic defaults remain unchanged, and unsupported element or query domains
remain indeterminate or fail through their accepted paths. No external
snapshot is packaged, discovered, or enabled globally.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.


## Accepted 50S.6G.1B.2C medium specimen

The proposed 256-record default is a deterministic coverage specimen, not a
population-frequency sample. It covers declared mean-motion, inclination,
eccentricity, BSTAR, signed-age, and NORAD-width bins independently, taking two
digest-ranked representatives from every non-empty bin before deterministic
fill. It remains an external non-default product bound to the exact admitted
parent and a complete selection receipt.


Fernando scientifically and architecturally accepted 50S.6G.1B.2C on
2026-09-17 after all 153 plugin-disabled current-documentation tests passed in
4.58 seconds; `git diff --check` and the working tree were clean. Only bounded
fake-data implementation is authorized next. The first real medium selection,
50S.6G.1B.2D matrix execution, and later delivery remain separately
unauthorized.

### Candidate 50S.6G.1B.2C medium specimen

The candidate `satellites/snapshot_evidence.py` service creates a
deterministic coverage specimen from one explicitly admitted parent. It checks
the acquisition report and captured provider bytes, selects two digest-ranked
representatives per nonempty independent bin, fills deterministically, and
publishes canonical records plus a path-free receipt beneath the subset digest.
It is not a statistical sample or completeness claim.

The developer `select-medium` command is offline. The 2026-09-17 fake-data
gate passed 30 plugin-disabled tests in 5.99 seconds. No external medium
snapshot is packaged, discovered, or selected automatically; the first real
medium selection and 50S.6G.1B.2D remain unauthorized.

### Accepted 50S.6G.1B.2C implementation

Fernando scientifically and architecturally accepted the fake-data medium
selector on 2026-09-17 at `1d9d4e4`. The complete plugin-disabled suite
passed 2,622 tests in 225.75 seconds; 185 focused tests passed in 9.03 seconds.
No real medium snapshot has been produced. The first real offline selection
requires separate authorization, and 50S.6G.1B.2D remains unauthorized.

### Candidate real medium specimen

The external specimen contains 256 records with canonical-record SHA-256
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`.
Its canonical selection receipt has SHA-256
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
It derives from the accepted 16,559-record parent
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`
using age reference `2026-09-17T15:52:23.000000Z`.

The specimen has 48 mandatory representatives, 208 deterministic fill records,
and no empty bin. It remains an external deterministic coverage specimen—not a
statistical sample, complete catalogue, packaged default, or population claim.
The parent bytes were unchanged and the operation made no provider request.
Acceptance and 50S.6G.1B.2D authorization remain separate decisions.

### Accepted real 50S.6G.1B.2C specimen

Fernando accepted exact external specimen
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`
with receipt
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`
on 2026-09-17 at `c4cd009`; 157 plugin-disabled documentation tests passed
in 4.66 seconds. It remains external, immutable, and non-statistical.
50S.6G.1B.2D remains separately unauthorized.

### Candidate 50S.6G.1B.2D equivalence matrix

The documentation-only candidate defines 10 deterministic same-observer La Ligua fields on
one UTC night, with different centres and intervals plus a shared-interval
research control. The accepted 256-record specimen is explicitly admitted to
both exhaustive and accelerated services. Success requires identical ordered
crossing results, complete conservative-selection evidence, no fallback, and
no rejected satellite with an exhaustive crossing.

Resource measurements are descriptive evidence, not a speed claim. The matrix
is not executed by this audit and creates no chart, track, report route, or
runtime default.

### Accepted 50S.6G.1B.2D audit

Fernando accepted the strict equivalence-matrix audit on 2026-09-17 at
`6e7a8b9`; 159 plugin-disabled documentation tests passed in 10.75 seconds.
Only fake-data harness implementation is authorized next. The accepted real
256-record specimen must not be executed, and no speed or downstream delivery
claim is authorized.

### Candidate 50S.6G.1B.2D fake-data implementation

The candidate `satellites/crossing_matrix.py` implementation enforces exact
Python-result equality, canonical-byte and digest equality, complete
reject/retain/indeterminate evidence, forbidden exhaustive fallback, isolated
resource observations, and atomic evidence publication with manifest
revalidation. Candidate commit `19520f3` passed 2634 plugin-disabled
full-suite tests in 230.25 seconds on 2026-09-17.

This verification used fake data only. The accepted real 256-record specimen
was not read, the real ten-field matrix was not executed, and no speed or
capacity claim was made. Fernando's scientific and architectural acceptance
is required before any separately authorized real-matrix execution.

### Accepted 50S.6G.1B.2D fake-data implementation

Fernando scientifically and architecturally accepted the bounded fake-data
matrix implementation on 2026-09-17. Its recorded evidence is 2634
plugin-disabled full-suite tests in 230.25 seconds at `19520f3`, followed by
161 plugin-disabled current-documentation tests in 3.32 seconds at
`3ef6a4d`. The accepted closure neither reads the real 256-record specimen
nor executes the real ten-field matrix. Only a separately bounded
real-execution audit is authorized next.

### Candidate real-execution readiness audit

The accepted fake-data matrix core at `9bdf301` is not yet ready for the
first real run. The exact ten-field La Ligua fixture, production whole-interval
airmass certifier, isolated subprocess worker, and explicit offline developer
command remain to be implemented and proven with fake data. This audit did not
read the accepted real 256-record specimen or execute either route. Only the
bounded production-path implementation may proceed next; the real matrix and
all performance conclusions remain unauthorized.

### Accepted real-execution readiness audit

Fernando scientifically and architecturally accepted the not-ready finding on
2026-09-17 after 163 plugin-disabled current-documentation tests passed in
3.80 seconds at `054ac39`. Only the bounded fake-data production-path
implementation may proceed next. The accepted real 256-record specimen must
remain untouched and the real ten-field matrix must not be executed.\n

### Candidate offline equivalence-matrix execution path

The candidate `run-equivalence-matrix` developer command is explicit and
offline. It requires the snapshot and output directories, all three accepted
digests, and an exact operator acknowledgement. Before any route process
starts it validates the complete accepted selection receipt, constructs the
digest-frozen La Ligua fields, and atomically certifies their centre-only
airmass. Each route/query/repetition then runs in a fresh subprocess. The
fixture contains only 15- and 60-second intervals and its tests use fake data
and bounded subprocess doubles. The command performs no discovery, download,
refresh, fallback, concurrency, or cache reuse.\n

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

### Candidate first real equivalence run

Candidate 50S.6G.1B.2D.1 proposes exactly one operator-started use of
`run-equivalence-matrix` with explicit absolute snapshot and output paths,
all three accepted digests, and the exact acknowledgement. The output root
must be new, empty, external, and have at least 2 GiB free. The run allows no
network, discovery, refresh, substitution, retry, resume, changed fixture, or
changed policy. A successful evidence directory remains external and
unaccepted until a separate review.\n

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

### Candidate equivalence-run progress display

The offline matrix command candidate displays a terminal bar with completed
workers over the policy-derived total, integer percentage, field, route, and
phase. Under the accepted default it advances from 0/80 to 80/80. The display
is parent-only stderr text and is not scientific evidence. A running worker may
leave the same line visible for a long time; completion advances only after
that fresh subprocess returns successfully.

## Candidate equivalence-run progress verification

Candidate `b0b4432` passed 180 focused plugin-disabled tests in 5.44 seconds and the full 2647-test plugin-disabled suite in 239.53 seconds on 2026-09-18; the diff check was clean. The progress display remains parent-only and outside canonical evidence. The real specimen was not accessed, the run has not started, and renewed authorization remains pending.

## Accepted equivalence-run progress display

Fernando scientifically and architecturally accepted candidate `96b9ba0` on 2026-09-18 after the recorded focused, full-suite, final-documentation, and diff verification. The display remains parent-only and outside canonical evidence. The real specimen has not been accessed, the run has not started, and execution still requires post-merge renewed authorization.

## Renewed single real equivalence run

After progress-display merge `9c4b808`, Fernando explicitly renewed authorization on 2026-09-18 for exactly one real matrix run. It must use the accepted immutable specimen, exact fixture and 10 fields, only 15/60-second intervals, both routes, one warm-up and three measurements, at most 80 fresh subprocesses, a new empty external output root, and no retry or resume. Progress is operational stderr only; successful artifacts remain unaccepted candidate evidence.

## Accepted renewed single real run

Fernando scientifically and architecturally accepted candidate `dd71e01` on 2026-09-18 after 169 plugin-disabled documentation tests passed in 4.29 seconds and repository checks were clean. The run remains unstarted and unconsumed; merge and repeated external preflight are required before execution.

## Candidate first real equivalence evidence

The consumed one-run authorization produced candidate report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` from `9d93113` on 2026-09-18. Ten fields, both 15/60-second intervals, 60 measured observations, all decision classes, and exact route equality passed with no fallback. All fields had zero crossings, so positive crossing remains synthetic-only evidence. The observed acceleration is descriptive for the exact specimen and 2017 Intel Mac, not a general speed claim.

## Accepted first real equivalence evidence

Fernando scientifically and architecturally accepted report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` at `186e255` on 2026-09-18 after 171 documentation tests passed in 4.46 seconds. This closes the first real run as exact empty-result equivalence and conservative partition evidence. All fields had zero crossings; observed timing is descriptive only, and no rerun or parallelization is authorized.


## Candidate bounded 50S.6G.1B closure

At integrated baseline `b010a6c`, the representative-snapshot foundation is
implemented and its accepted real matrix demonstrates exact empty-result
equivalence and complete conservative partitions. All ten real fields had zero
crossings; positive-crossing behavior remains synthetic evidence.

The candidate closure expressly defers a full-snapshot matrix, wider FoV-count
matrix, comprehensive real crossing geometries, and universal performance,
capacity, concurrency, or reuse claims. The consumed real-run authority is not
renewed. No provider request, artifact refresh, rerun, report, CLI, track,
chart, illumination, or brightness work is authorized.

Pending Fernando's separate scientific and architectural acceptance,
50S.6G.1B remains open. Acceptance would authorize only a separate
documentation audit of 50S.6G.2A canonical exact-crossing reports and
deterministic JSON, not implementation.


## Accepted bounded 50S.6G.1B closure

Fernando scientifically and architecturally accepted the bounded closure on
2026-09-19 at `c62a451`, after all 173 plugin-disabled documentation tests
passed in 3.82 seconds and repository checks were clean. The representative
foundation is closed with exact empty-result equivalence and conservative
partition integrity; every real field had zero crossings. Deferred scale and
performance evidence remains explicitly unclaimed.

Only a bounded 50S.6G.2A documentation audit is authorized next. No report,
JSON Schema, encoder, round trip, CLI, track, or chart implementation is
authorized.
