# Wenu artificial-satellite scientific and implementation guide

**Status:** Living 50S work-in-progress guide  
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

## 2. Scientific product

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

## 3. Canonical satellite flow

The proposed scientific flow is:

```text
provider response
    -> validated immutable OMM/TLE snapshot
    -> SGP4 geometric TEME state
    -> declared Earth-orientation transformation
    -> observer-relative topocentric state
    -> apparent spherical direction in the requested field frame
    -> exact trajectory/footprint intersection
    -> optional conservative candidate index
    -> illumination and optional photometry
    -> reports
    -> optional shared Wenu chart pipeline
```

Acquisition never occurs inside propagation, field search, chart construction,
rendering, or export. Candidate indexing accelerates the exact calculation but
does not become a second propagation authority.

## 4. Identity and catalogue snapshot

### 4.1 Canonical ingestion model

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

### 4.2 Snapshot identity

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

## 5. Provider policy

Provider policy is a scientific reproducibility and operational-safety input,
not merely a networking detail. It must be rechecked before any change to
endpoint, workload, concurrency, cadence, caching, retry, packaging, or
redistribution.

### 5.1 CelesTrak candidate policy

As checked on 2026-09-14, CelesTrak requests clients to use cached GP data by
default, check for updates no more often than once every two hours, request
only needed data, inspect HTTP status, and stop/report errors rather than
retrying. Wenu's proposed adapter therefore uses one supported bulk request,
serial access, validation before atomic publication, and no automatic retry.

OMM-compatible CSV or XML is preferred to legacy TLE because new catalogue
identifiers exceed TLE's five-digit field. Redistribution is not authorized by
this guide and requires a separately recorded licensing decision.

### 5.2 Space-Track candidate policy

Space-Track requires an account and publishes request and bandwidth guidance.
It is not the automatic Wenu default. A future adapter is opt-in,
credential-external, serial, bulk-oriented, and cached. Account-derived data
must not be packaged or redistributed without explicit permission under the
then-current terms.

### 5.3 SatChecker role

IAU CPS SatChecker is an independent comparison oracle for selected
ephemerides, range, motion, illumination, and field-crossing results. It is not
the sole Wenu production dependency because reproducible queries must work
from a frozen local snapshot without relying on service availability.

## 6. Propagation and reference systems

### 6.1 SGP4 contract

General-perturbations elements are mean elements fitted for SGP4. They are not
osculating Keplerian elements and must not be silently propagated with a
two-body or unrelated numerical model.

Wenu will use a Vallado-compatible SGP4 implementation verified against the
published reference vectors. Scalar and array evaluation must implement the
same model and error behavior. Each result retains propagator identity and
version, element epoch, evaluation instant, time offset from the element
epoch, and SGP4 status/error code.

### 6.2 TEME is an explicit state

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

### 6.3 Freshness and uncertainty

Element age is always reported. There is no universal age cutoff because drag,
maneuvers, orbit regime, required timing precision, and field size differ.
Invalid or decayed records fail explicitly. A stale but propagatable record
may remain in a result with a warning unless the query declares an exclusion
policy.

An element age or published mean residual is not a per-event covariance.
Wenu must not present an unquantified prediction as a confidence interval.
Future covariance or empirical along-track uncertainty is additional state,
not a reinterpretation of SGP4 output.

## 7. Field and crossing definitions

### 7.1 Field

A field is spherical scientific geometry independent of chart projection.
Initially planned forms are:

- circular field, defined by centre and angular radius;
- spherical rectangle, defined by centre, orientation, width, and height;
- WCS or instrument footprint, defined by a validated spherical boundary.

The field declares its coordinate frame and position status. Boundary touch
counts as intersection. RA wrap, poles, and projection seams are handled by
spherical geometry, never by an unqualified RA/Dec bounding box.

### 7.2 Query interval

Start and stop are explicit UTC instants and the interval is inclusive.
Exposure windows, when supplied, retain exact start and duration. A trajectory
may enter the same field more than once; disconnected visits are separate
crossing events.

### 7.3 Crossing record

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

## 8. Complete-scan correctness oracle

The first implementation scans every valid object in the snapshot. A fixed
sampling grid alone is not a completeness proof because a fast LEO pass may
cross a narrow field between samples.

The oracle uses adaptive interval subdivision with a conservative motion
bound. Intervals that cannot exclude the field are subdivided or refined using
bracketed boundary roots and closest-approach extrema. It must remain callable
after optimization so 50S.3 can compare every indexed result against it.

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

## 9. Conservative high-performance search

The leading 50S.3 design is a time-slab and hierarchical-sky-pixel index:

1. vectorize SGP4 over satellite batches and bounded time slabs;
2. construct a conservative swept spherical cover for each object/slab;
3. dilate the cover for footprint radius, between-sample motion and curvature,
   transformation/numerical allowance, and boundary tolerance;
4. map `(time slab, sky pixel)` to candidate satellite identifiers;
5. refine every candidate using the exact crossing solver.

HEALPix is the leading pixelization candidate, not yet a mandated dependency.
An initial simple inverted index is preferred to an opaque combined
space-time tree. An isolated query may build ephemeral bounds; repeated
pointings may reuse an immutable observer/night index.

The index key includes snapshot digest, observer, Earth-orientation policy,
interval, sampling/bounding policy, SGP4 implementation and version, and Wenu
software version.

The acceptance invariant is zero false negatives against the complete scan.
False candidates affect performance and are measured, but do not invalidate
scientific completeness. Unsafe approaches include nearest sampled-point
tests, unconstrained interpolation, plain RA/Dec boxes, and any index without
an exact fallback.

## 10. Illumination

Illumination uses explicit Sun-Earth-satellite-observer geometry. The minimum
accepted physical model distinguishes sunlight, penumbra, and umbra using the
finite angular size of the Sun. Model inputs, ephemeris, Earth shape, and
boundary tolerance are retained.

Atmospheric refraction and absorption near shadow ingress and egress can
modify observed brightness. They remain separate from the minimum geometric
shadow state until a model is selected and empirically validated.

## 11. Apparent brightness

### 11.1 Required inputs

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

### 11.2 Model hierarchy

Wenu uses the most specific defensible level:

1. `unknown` when no supported empirical or physical model exists;
2. a satellite-family magnitude distribution normalized to a declared range
   and conditioned on available geometry;
3. a diffuse physical model with explicit size, attitude, and reflectance
   assumptions;
4. a spacecraft-specific attitude/BRDF model with published parameters and
   independent validation.

A result is labelled model magnitude or magnitude distribution, never
guaranteed brightness. Scatter, bias, outliers, unmodeled glints, and tumbling
limitations are reported. A single standard magnitude does not replace a
phase function.

### 11.3 Validation

Before 50S.4B acceptance, compare at least two materially different satellite
families over varied range, phase, elevation, and illumination geometry using
calibrated, time-resolved observations. Report passband transformations,
range normalization, residual bias and scatter, outliers, phase coverage,
and orbit-age or trajectory-timing contribution.

### 11.4 Detector contamination is later

Trail signal or detectability also depends on angular speed, exposure time,
optics, aperture, throughput, defocus and PSF, pixel scale, sky background,
saturation, blooming, and detector response. Those belong to a later
instrument model and must not be inferred from apparent magnitude alone.

## 12. Validation hierarchy

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

## 13. Performance evidence

Performance acceptance uses a recorded current full-catalogue snapshot rather
than only a reduced fixture. Measure:

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

## 14. Source ownership direction

No production module is admitted by this guide. Before 50S.1, the source-tree
admission review must compare the proposed responsibility with existing
ephemeris, coordinate, resource, acquisition, moving-track, and report owners.

The satellite domain is expected eventually to justify a coherent
`src/wenu/satellites/` package because snapshot ingestion, SGP4 state,
crossing geometry, indexing, illumination, and photometry have distinct
collaborating responsibilities. It must not be created merely to carry a
milestone number, and it must not duplicate Wenu's coordinate service,
trajectory geometry, projection, preparation, renderer, semantic SVG, or
export machinery.

## 15. Milestone evolution

- **50S.0:** maintain this literature, provider-policy, scientific, and
  architecture guide; no runtime behavior.
- **50S.1:** add and validate frozen-snapshot SGP4/TEME state and explicit
  topocentric transformation; update implemented ownership here and in
  `source_tree.md`.
- **50S.2:** add field types and the complete-scan crossing oracle.
- **50S.3:** add the conservative index and prove zero false negatives.
- **50S.4A:** add geometric and illumination reports and statistical products.
- **50S.4B:** add only empirically validated brightness models.
- **Later detector slice:** add instrument-specific trail signal and
  detectability.
- **50S.5:** draw selected tracks through the existing Wenu pipeline and close
  the program.

At every milestone, revise this living guide to match accepted science and
implemented ownership. When 50S foundation work is merged, decide explicitly
whether this guide remains separate or is integrated into
`coordinate_system_guide_v0.9.5.md`; do not merge documents mechanically.
