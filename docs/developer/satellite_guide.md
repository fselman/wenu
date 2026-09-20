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

### 7.2 Keplerian elements: osculating geometry and Wenu's mean-element input

A Cartesian position and velocity at one instant define an instantaneous
two-body conic. Its six classical Keplerian elements are:

- semimajor axis `a`, which sets orbit size and, in the two-body problem,
  period;
- eccentricity `e`, which sets shape;
- inclination `i`, the tilt of the orbital plane to the reference equator;
- right ascension of the ascending node `Omega`, the inertial direction of
  the equator crossing at which the satellite moves north;
- argument of pericentre `omega`, the angle in the orbital plane from the
  ascending node to pericentre; and
- true anomaly `nu`, the satellite's instantaneous angle from pericentre.

Together with epoch, central body, reference frame, and time scale, these form
an **osculating** element set: the Kepler ellipse tangent to the real
trajectory at that instant. Perturbations make this ellipse evolve
continuously. The elements are singular for some useful orbits: `Omega` is
undefined at zero inclination, `omega` is undefined at zero eccentricity,
and true longitude or nonsingular equinoctial elements are then often clearer.

Wenu does not ingest that parametrization directly. Its canonical OMM/SGP4
record carries epoch, `MEAN_MOTION` `n` in revolutions per day,
`ECCENTRICITY`, `INCLINATION`, `RA_OF_ASC_NODE`,
`ARG_OF_PERICENTER`, and `MEAN_ANOMALY`, plus `BSTAR`, mean-motion
derivatives, and metadata such as `REF_FRAME = TEME`, `TIME_SYSTEM = UTC`,
and `MEAN_ELEMENT_THEORY = SGP4`. Mean anomaly replaces true anomaly because
it advances uniformly in an unperturbed ellipse. For orientation only, a
two-body semimajor axis can be estimated from mean motion,

```text
a approximately equals (mu / n^2)^(1/3),
```

after converting `n` to radians per second. That conversion does **not**
turn a GP record into osculating elements. SGP4 mean elements have selected
short-period motion removed by the SGP4 theory and are model-dependent fit
parameters. They must be interpreted by SGP4; a generic Kepler solver or a
different force model need not reproduce the catalogue trajectory.

#### 7.2.1 Why elements change between revolutions

In a perfect spherical two-body problem, `a`, `e`, `i`, `Omega`, and
`omega` are constant and the anomaly advances by 360 degrees per orbit. For
an Earth satellite, the largest systematic departure in many low and medium
orbits is Earth's oblateness, represented first by the dimensionless
coefficient `J2 approximately 1.08263e-3`. Atmospheric drag, higher gravity
harmonics, the Moon and Sun, solar radiation pressure, tides, and maneuvers add
changes on other time scales. Osculating elements also contain short-period
within-orbit oscillations, so comparing two isolated osculating sets can mix a
secular drift with the phase of those oscillations.

For a first-order, orbit-averaged `J2` estimate, define

```text
p = a (1 - e^2)
n = sqrt(mu / a^3)
```

where `p` is the semilatus rectum. The secular rates of the node and
pericentre are approximately

```text
dOmega/dt = -(3/2) J2 n (R_E / p)^2 cos(i)

domega/dt =  (3/4) J2 n (R_E / p)^2 (5 cos(i)^2 - 1).
```

Equivalently, the accumulated change per revolution is approximately

```text
Delta Omega = -3 pi J2 (R_E / p)^2 cos(i)

Delta omega = (3 pi / 2) J2 (R_E / p)^2 (5 cos(i)^2 - 1).
```

These equations are a scale and sign guide, not Wenu's propagator. SGP4
contains its own consistent secular and periodic perturbation theory.

The dependence is instructive:

- per unit time the `J2` rates scale approximately as `a^(-7/2)`; per
  revolution they scale approximately as `a^(-2)`;
- eccentricity strengthens both rates through `(1 - e^2)^(-2)`, although a
  high-eccentricity orbit also demands attention to perigee altitude and to
  the validity of the averaged approximation;
- nodal regression is fastest for low-inclination prograde orbits, vanishes
  in the first-order formula at 90 degrees, and reverses sign for retrograde
  orbits;
- apsidal rotation vanishes at the critical inclinations near 63.4 and 116.6
  degrees, and its sign changes across them; and
- a retrograde near-polar LEO can be chosen for about +0.986 degree per day of
  nodal precession, matching the Sun's annual apparent motion and producing a
  Sun-synchronous orbit.

#### 7.2.2 Orders of magnitude

Using `J2` alone and nearly circular representative orbits gives useful
mental scales, not prediction tolerances:

| Regime | Representative scale | First-order nodal rate |
| --- | --- | --- |
| LEO, `a approximately 7000 km` | about 100 minutes per orbit | up to about 7 degrees/day times `cos(i)`, or about 0.5 degree/orbit times `cos(i)` |
| GPS-like MEO, `a approximately 26,600 km`, `i approximately 55 degrees` | about 12 hours per orbit | about -0.04 degree/day |
| GEO, `a approximately 42,200 km` | about one sidereal day per orbit | at most roughly -0.01 degree/day from `J2` |

At `a approximately 7000 km`, the first-order apsidal rate ranges from about
-3.6 degrees/day near polar inclination to about +14 degrees/day near the
equator, with zero at the critical inclination. A Sun-synchronous LEO is
deliberately near +1 degree/day in `Omega`, rather than the maximum LEO
rate, because its retrograde inclination makes `cos(i)` small and negative.

Semimajor axis and eccentricity have no first-order secular `J2` drift in
this averaged model, but their osculating values still vary periodically.
Drag usually reduces orbital energy and semimajor axis in LEO, increasing mean
motion and eventually shortening lifetime. Its rate varies strongly with
altitude, area-to-mass ratio, attitude, and solar-driven atmospheric density;
a single `BSTAR` value is only an SGP4 drag-like fit parameter, not a
universal physical decay rate. At high altitude, luni-solar torques and solar
radiation pressure can be comparable to or more important than drag. Maneuvers
can dominate all natural trends.

Therefore Wenu should answer “how fast are the elements changing?” by
propagating the accepted element set with SGP4 over the requested interval and,
when element histories are compared, by stating whether the values are SGP4
mean elements or osculating elements derived from propagated states. The
formulae above explain scale; they do not replace propagation or an uncertainty
model.

#### 7.2.3 References

- CCSDS, *Orbit Data Messages*, CCSDS 502.0-B-3, the normative definition of
  OMM fields and metadata:
  <https://public.ccsds.org/Pubs/502x0b3e1.pdf>.
- Vallado, Crawford, Hujsak, and Kelso, “Revisiting Spacetrack Report #3,”
  AIAA 2006-6753 Rev. 3, the SGP4 formulation and verification reference:
  <https://celestrak.org/publications/AIAA/2006-6753/AIAA-2006-6753-Rev3.pdf>.
- CelesTrak, “A New Way to Obtain GP Data,” a practical mapping of current GP
  JSON/CSV fields to OMM and the declared TEME/UTC/SGP4 metadata:
  <https://celestrak.org/NORAD/documentation/gp-data-formats.php>.
- Vallado, *Fundamentals of Astrodynamics and Applications*, 4th ed.,
  Microcosm Press, 2013, especially the classical-element and perturbation
  chapters, for the `J2` secular-rate derivation and limitations.

### 7.3 TEME is an explicit state

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

### 7.4 Freshness and uncertainty

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
observer, evaluation grid, and FoV size. Its scientific status is
propagated sampled specimens — not verified crossings. It stores propagated
sampled tracks and query inputs only. It does not find a useful field automatically, emit
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

## 17. Exact crossing reports

An exact crossing report is a renderer-neutral scientific record built from
already solved geometric crossings. It carries the observer, immutable
catalogue snapshot, field definitions, intervals, airmass admissions,
tolerances, connected visits, provenance, and warnings without recalculating
any orbit or coordinate.

Three distinctions are essential:

1. a validated field with zero crossings is a real result, not missing data;
2. a geometric crossing does not imply illumination, brightness, visibility,
   or detector contamination;
3. SatChecker sampled candidates and locally solved exact crossings have
   different scientific status and therefore different report products.

Deterministic JSON requires stable field and crossing order, finite values,
explicit UTC instants, a fixed schema version, and an immutable creation time
provided when the report is constructed. A report digest identifies the whole
logical record; it does not replace the separate snapshot digest.

Wenu's exact-report model therefore stores one immutable compact canonical
payload and returns detached document copies. The readable JSON form uses
sorted object keys, two-space indentation, Unicode text, and one final newline;
array order remains scientific. The report identity is SHA-256 of the compact
canonical scientific payload with only the identity field omitted.

The packaged version-1 schema closes every object and requires all fields.
Decoding is deliberately stricter than syntax validation: duplicate JSON keys,
non-finite numbers, unknown fields, invalid UTC instants, changed identity,
field/count/order mismatch, crossings outside their interval or field, and
inconsistent observer, snapshot, element, airmass, or acceleration context all
fail. The decoder reconstructs existing immutable Wenu domain values so the
same physical and coordinate invariants apply on both sides of serialization.

Illumination, apparent magnitude, detector effect, and exact-track samples are
required JSON nulls in version 1. Null means “not evaluated,” not false, dark,
zero, or absent. Adding those sciences requires a later schema version and its
own accepted physical model.

## 18. Development history

Chronological decisions, candidate states, verification evidence, and
acceptance records are maintained separately in
[satellite_program_log.md](satellite_program_log.md). They are not part of this
pedagogical guide. Keep the two responsibilities linked, but do not merge
documents mechanically.


## Lossless reusable tabular views of an exact-crossing report

A scientific report and a file format are different layers. Wenu's accepted
exact-crossing report has one logical identity derived from canonical JSON.
ECSV and VOTable can later provide interoperable tabular views without
changing that identity or recalculating a crossing.

The proposed design first projects the report into shared validated record
kinds: one report record, one record for every field, and records for its
crossings. A zero-crossing field still has a field record. Stable ordinals
preserve scientific array order, while units, masks, coordinate meaning, UTC
time metadata, provenance, and joins remain explicit. Thin format adapters can
then express those same records as one ECSV table or as related VOTable tables.

This is a reusable design: scientific flattening and validation are written
once, so two formats cannot quietly acquire different meanings, and later
publication code can reuse the same in-memory representation. ECSV is a
human-readable table format with YAML metadata; VOTable is an IVOA XML format
with astronomical FIELD, PARAM, and TIMESYS metadata. Neither format makes a
satellite visible, illuminated, bright, or damaging to a detector. This
candidate belongs to 50S.6G.2B and is not yet implemented.

## 50S.6G.2C file-protocol interpretation

The proposed two-call workflow is an audit-preserving selection protocol, not
a new visibility calculation. The first call evaluates every requested FoV and
solves none when any is invalid. Its deterministic JSON records all invalid
FoVs and the ordered valid subset. The second call leaves invalid FoVs explicit
but sends only that revalidated subset to the existing exact crossing service.
The resulting JSON, ECSV, and VOTable files describe the same accepted exact
local report; filesystem history does not change astronomical meaning.

## Accepted 50S.6G.2C reader boundary

The accepted next implementation is an offline transport and publication
layer. Readers should interpret its validation-output document as an explicit
audit-preserving partition of the original FoVs, not a scientific crossing
result. Only the revalidated embedded valid subset may reach the unchanged
exact crossing service on the second call.

## Candidate exact local track evidence

50S.6G.3A proposes a track as evidence for one already solved connected visit. It evaluates the accepted immutable orbit snapshot from entry through exit and retains entry, closest approach, and exit as exact sample anchors. Adaptive midpoint checks add samples between those anchors; declared limits fail closed instead of returning a shortened track.

This exact local evidence is different from SatChecker's provider-sampled candidate path. An output-neutral layer would only present retained evidence and would perform no propagation or crossing calculation. The audit is documentation-only and no implementation is yet authorized.

## Accepted exact local track audit

Fernando accepted the 50S.6G.3A documentation boundary on 2026-09-19. A bounded implementation may now construct immutable exact connected-visit evidence through the accepted local propagation route and expose it through a science-free layer. Chart integration and later track products remain separate milestones.

## Candidate exact local track implementation

The candidate now realizes one immutable sample set for each accepted connected visit. Event instants are always vertices; midpoint chord-deviation and maximum-step checks add intervening samples; limits fail closed. The layer reads that evidence and never propagates again.

The curve itself has no single time. UTC is therefore declared once on the evidence and retained on every sample, while the collection coordinate specification describes only the timeless GCRS-axis orientation and topocentric-direction origin. Focused verification passed; full verification and acceptance remain pending.

## Accepted exact local track implementation

50S.6G.3A is accepted: Wenu can now construct immutable exact track evidence for an already solved connected visit and expose its path and events without repeating propagation. This does not yet place a track on a binocular or regional chart; that integration begins with a separate 50S.6G.3B documentation audit.

## Candidate binocular and regional exact-track charts

50S.6G.3B proposes an explicit display request that carries already-computed exact evidence into an ordinary regional or binocular chart. The request may show the path, exact event markers, and optional event labels. Chart construction does not solve or propagate a satellite again; it only installs evidence views and uses Wenu's ordinary projection, clipping, styling, and export path.

The complete curve is shown in one fixed chart frame at the crossing field's reference instant. Planisphere tracks and later visibility or illumination science remain separate work. This audit is documentation-only.

## Accepted binocular/regional chart audit

Fernando accepted the 50S.6G.3B documentation boundary on 2026-09-19. A bounded implementation may now carry already-realized exact evidence into ordinary regional and binocular charts, with path/event/label controls and existing output paths. It may not perform satellite science or add planisphere support.

## Candidate binocular and regional track implementation

The candidate accepts already-realized exact evidence directly in a regional or binocular ChartRequest. It can draw the retained path, the exact entry/closest/exit markers, and optional English event labels. Reusing a sphere leaves no request-owned satellite layer behind, and chart provenance records only the track digest and bounded identity/event summary.

Deterministic offline specimens use a nearly straight short pass and export PNG, PDF, and semantic SVG from the same prepared chart. Boundary clipping is tested separately so the specimen does not invent an implausible bending satellite path. The implementation remains a candidate pending complete verification and acceptance.

## Candidate stereographic polar-planisphere exact tracks

50S.6G.4A proposes an event-specific overlay on Wenu's paired physical north
and south polar planisphere faces, not on the ordinary horizontal full-sky
planisphere. The same already-realized track is expressed in fixed equatorial
axes and projected independently onto both stereographic faces. A track in the
declination overlap may appear on both; a face boundary clips only the drawing
and never creates a new entry or exit event.

This product is valid only for the stated observing site and UTC interval. It
must not suggest that the satellite repeats the path whenever the planisphere
is rotated to the same sky. Horizon furniture remains separate and makes no
visibility claim. The audit is documentation-only; implementation and later
illumination or brightness science remain unauthorized.

## Accepted stereographic polar-planisphere audit

Fernando accepted the 50S.6G.4A documentation boundary on 2026-09-19. A
bounded implementation may now carry already-realized exact evidence through
the paired north/south stereographic page export, including event-specific
site/time validity, face overlap, cap clipping, cleanup, and existing semantic
outputs. It may not perform new satellite science or add other all-sky,
illumination, or brightness behavior.

## Corrective ordinary AltAz planisphere audit

The intended exact-track planisphere is Wenu's ordinary visible-hemisphere
chart: one zenith-centred stereographic FullSkyChart in observer-local AltAz,
bounded by the horizon. It is not the paired north/south equatorial physical
planisphere.

A future corrected implementation may reuse the same fixed horizontal
product-frame rule already accepted for regional and binocular charts. The
complete retained track is transformed at the chart reference instant;
per-sample UTC remains evidence. Horizon clipping changes only presentation
and never creates an event or establishes visibility.

The earlier paired-polar authorization is superseded. This corrective audit is
documentation only and requires Fernando's separate acceptance before any
runtime work.

## Accepted corrective AltAz planisphere audit

Fernando accepted the corrected ordinary visible-hemisphere product on
2026-09-20. A bounded implementation may display accepted exact tracks on one
zenith-centred AltAz stereographic FullSkyChart, using the existing fixed
chart-reference frame, horizon presentation boundary, lifecycle, semantics,
provenance, and exporters. Paired polar, circumpolar, Galactic all-sky, and
later science remain outside this milestone.

## Verified candidate ordinary-planisphere exact track

The candidate places one accepted connected visit on the ordinary La Ligua
visible-hemisphere planisphere. The complete track is expressed in the one
AltAz frame fixed at chart time; the sample times still identify retained
evidence. The horizon may clip drawing only and cannot invent an entry or exit
event. The physical manifest accompanies the chart with site, chart time,
complete visit interval, track identity, and output digests.

## Accepted ordinary-planisphere exact tracks

Wenu now accepts already-realized exact connected visits on the ordinary
observer-horizontal stereographic planisphere. One fixed AltAz frame describes
the chart, retained sample UTC records the evidence, and the horizon clips
presentation without inventing events. The accepted physical La Ligua
specimen and manifest demonstrate the PNG/PDF/semantic-SVG route and retain
site, chart time, complete visit interval, identity, and output digests.
## Accepted 50S.6H observatory-planning interpretation

A satellite crossing and an observing-plan decision are different claims.
The accepted exact report says when a propagated object intersects a declared
field for one observer. The authorized next 50S.6H advisory will say only that this
crossing interval overlaps a caller-supplied planned UTC interval.

It will not say that the satellite is illuminated, detectable, bright enough
to matter, harmful to a detector, or grounds to reschedule an observation.
Paranal OB constraints and time windows remain scientific and operational
inputs owned by ESO and the observer. ELT planning remains unspecified until
an official operational interface is available.
## Accepted offline satellite planning advisory

The accepted advisory answers only: “does this planned half-open UTC interval
overlap an accepted geometric satellite crossing interval?” Each positive row
retains the plan, crossing, overlap, object, observer, field, snapshot, and
report identities. A zero-row result means no geometric interval overlap was
found for those inputs; it is not a claim of an uncontaminated observation.

The fixed scientific-status text states that illumination, apparent
brightness, detector effect, and operational disposition are unknown. Human
review remains responsible for observatory action.
## Accepted advisory specimens

The positive specimen intersects a four-second geometric crossing with a
two-second planned interval and records exactly one two-second row. The second
planned interval begins at the crossing exit and records zero rows, confirming
half-open endpoint semantics. Both retain independent identities and state
that operational disposition is unknown. This is validation evidence, not an
observing recommendation.

## Candidate 50S.7A illumination vocabulary

Four source paths must be named independently:

- **Sunlight:** Sun to satellite;
- **Earthshine:** Sun to Earth to satellite;
- **Moonlight:** Sun to Moon to satellite; and
- **Lunar-Earthshine:** Sun to Moon to Earth to satellite.

The last term follows the explicit definition in Caddy et al. (2026) and must
not be confused with sunlight reflected from Earth onto the Moon. Sunlight and
Moonlight are finite-disk beams. Earthshine and Lunar-Earthshine arrive from
many Earth-surface directions and remain extended radiance fields until a
spacecraft surface and BRDF are introduced in 50S.8.

Satellite shadow and observer night are independent questions. A finite solar
disk behind the WGS-84 vacuum Earth limb yields sunlit, penumbra, umbra, or
possible antumbra geometry. Observer twilight uses the geometric altitude of
the Sun's center. Neither state says that a satellite is in the field, above
the horizon, bright enough to see, harmful to a detector, or grounds for a
schedule change. The 50S.7A candidate changes no runtime.

### Order-of-magnitude illumination memory scale

These are memory-scale estimates for incident illumination at a LEO satellite,
not Wenu model constants. The magnitude penalty assumes the same satellite
surface, attitude, BRDF, range, observer direction, and passband, so that only
the source irradiance changes.

| Source and favourable geometry | Incident scale | Relative to direct Sun | Same-geometry penalty |
| --- | ---: | ---: | ---: |
| Direct Sunlight near 1 au | `1.36e3 W m-2` | `1` | `0 mag` |
| Solar Earthshine onto a nadir-facing surface over sunlit Earth | roughly `1e1-4e2 W m-2` | `1e-2-3e-1` | roughly `+1.3 to +5 mag` |
| Direct full-Moon light | roughly `3e-3 W m-2` | `2.5e-6` | roughly `+14 mag` |
| Direct quarter-Moon light | roughly `3e-4 W m-2` | `2e-7` | roughly `+16.6 mag` |
| Full-Moon Lunar-Earthshine onto a favourable nadir-facing surface | roughly `1e-4-1e-3 W m-2` | `1e-7-1e-6` | roughly `+15 to +18 mag` |
| Quarter-Moon Lunar-Earthshine, scaled as a first estimate | roughly `1e-5-1e-4 W m-2` | `1e-8-1e-7` | roughly `+18 to +21 mag` |

The direct-Moon scale follows the Sun/full-Moon contrast of about `400,000`
(`14 mag`) quoted by Caddy et al. (2026). Their first-order lunar phase law
gives `m(90 deg) - m(0 deg) = 2.60 mag`, so quarter-Moon illumination is
about `0.091` of full Moon, not one half. Converting a visual contrast into
the bolometric-looking `W m-2` values above is deliberately only an
order-of-magnitude mnemonic; a real calculation must name its bandpass and
spectral model.

The reflected-Earth ranges are simple favourable-geometry estimates: a bright
Earth beneath LEO can return a few percent to a few tenths of the incident
source onto a nadir-facing surface. They can fall to zero when no suitably
illuminated Earth is visible, and clouds, land/ocean BRDF, specular geometry,
altitude, and spacecraft attitude can move the answer greatly.

Two papers anchor the scale:

- Fankhauser, Tyson, and Askari (2023), *Satellite Optical Brightness*
  (<https://doi.org/10.3847/1538-3881/ace047>), models direct Sunlight plus
  solar Earthshine with Earth and spacecraft BRDFs and finds Earthshine can
  materially increase apparent brightness, especially in civil twilight.
- Caddy et al. (2026), *The First Observations of Moonlit Satellites*
  (<https://arxiv.org/html/2609.07057v1>), reports `147` Moonlit ISS
  detections with median `V = 12.02 +/- 0.17 mag`, about
  `13.1 +/- 1.3 mag` fainter than daylight. In their representative STK ISS
  case, adding Lunar-Earthshine changed `V = 13.46` for direct Moonlight
  alone to `V = 12.98`: about `0.48 mag`, or `1.55x` in total flux. It
  added about `14%` to one directly Moonlit body component and dominated
  components that faced Earth but received no direct Moonlight.

The practical memory rule is therefore: Sunlight dominates an illuminated
surface; solar Earthshine can be a percent-to-tens-of-percent correction;
full Moon is about a millionth to a few millionths of Sunlight; quarter Moon
is about another factor of eleven down; and Lunar-Earthshine is commonly a
fraction of direct Moonlight in total flux but can be the entire illumination
of a nadir-facing component. These ratios do not by themselves predict an
observed satellite magnitude.

