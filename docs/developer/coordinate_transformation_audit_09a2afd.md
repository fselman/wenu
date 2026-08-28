# Wenu coordinate-transformation audit

**Status:** Package-wide as-is audit and migration contract

**Audit baseline:** `09a2afd06910f9bd2b0b3f8791224d8d7c7ca206`

**Milestone:** 48F.0

**Date:** 2026-08-16
**Scope:** Every astronomical coordinate transformation in Wenu

## 1. Decision

Coordinate transformation is a package service, not a chart-family detail.
Wenu must have one authoritative astronomical transformation scheme and one
implementation boundary for it.

The target scheme is:

```text
catalogue, ephemeris, or orbit model
    -> position provider
    -> coordinates with explicit frame, origin, epoch, and time
    -> canonical ICRS when the product contract uses it
    -> requested output frame or scientifically defined local path
    -> observer-local AltAz only when the product requires an observer
    -> coordinate-neutral projection alignment
    -> planar projection
    -> viewport clipping and rendering
```

Astropy coordinates and frames are the authority for transformations among
the astronomical frames they support, including ICRS, FK4/FK5, ecliptic,
Galactic, Earth-fixed frames, and AltAz. Wenu must not maintain a second
hand-written astronomical transform beside that authority. Skyfield, JPL
kernels, SGP4, or another specialized engine may provide time-dependent
states where its physical model is explicitly required, but a position
provider must not silently define a competing downstream frame path.

Position generation and coordinate transformation are separate operations.
An ephemeris or orbit provider determines where a moving object is at a
specified time. The coordinate service determines how that explicit state is
represented in another frame. Wenu must preserve that boundary when the Moon,
planets, natural satellites, asteroids, comets, or artificial satellites are
added.

`SphericalFrame` remains valid only as a coordinate-neutral rotation used to
align already-resolved spherical geometry with a projection. It is not an
astronomical reference frame and must never decide equinox, epoch, observer,
precession, nutation, aberration, or refraction.

## 2. Why Milestone 48E.3 exposed the problem

The polar planisphere combines an equatorial grid, celestial equator,
ecliptic, Galactic plane, ecliptic cardinal points, and coordinate poles in
one observer-independent disk. Those features should agree before projection.
They currently reach that disk through different frame definitions and
different transformation engines.

The apparent displacement of an equinox marker from the ecliptic/equatorial
intersection is therefore an upstream frame-contract failure. Moving the
marker or curve in projected coordinates would hide the symptom and corrupt
the scientific geometry.

## 3. As-is transformation inventory

| Owner | Source/native coordinates | Current transformation | Current output |
|---|---|---|---|
| `observer.py` | Site and UTC instant | Constructs Astropy ICRS, Galactic, `BarycentricMeanEcliptic(equinox=obstime)`, and AltAz frames; separately constructs Skyfield time, Earth, and topocentre | Two transformation ecosystems attached to one observer |
| `coordinates.py` | Nominal ICRS RA/Dec | Hand-written GMST/hour-angle trigonometry in `radec_to_altaz()` | Altitude and azimuth arrays |
| `charts/coordinate_frames.py` | AltAz spherical geometry | Astropy `SkyCoord.transform_to()` | ICRS or Galactic geometry, selected by chart code |
| `geometry/frame.py` | Generic spherical longitude/latitude | Orthogonal Cartesian rotation matrix | Projection-aligned spherical coordinates |
| `objects/stars.py` | Hipparcos RA/Dec | Skyfield `Star`, topocentric observation, apparent position, then `altaz()` | Observer-dependent AltAz |
| `objects/nonstellar.py` and packaged DSO layers | Catalogue ICRS centers/outlines | Astropy ICRS to observer AltAz, partly through `sky/observed_cache.py` | Observer-dependent AltAz |
| `sky/coordinate_grids.py` | AltAz, equatorial, ecliptic, or Galactic native samples | Mixed hand-written RA/Dec to AltAz and Astropy native-frame to ICRS conversion | Canonical geometry declared as AltAz |
| `sky/points.py` | ICRS, Galactic, or observer-provided mean-ecliptic `SkyCoord` | Native point to ICRS with Astropy, followed by hand-written ICRS to AltAz | Observer-dependent AltAz |
| `sky/milky_way.py` | ICRS isophote vertices | Astropy ICRS to AltAz | Observer-dependent AltAz polygons |
| `sky/magellanic_clouds.py` | ICRS isophote vertices | Astropy ICRS to AltAz | Observer-dependent AltAz polygons |
| `sky/constellation_lines.py` | Hipparcos vertex membership | Reuses the stellar Skyfield AltAz realization | Observer-dependent AltAz curves |
| `sky/constellation_labels.py` | ICRS label coordinates | Astropy ICRS to AltAz | Observer-dependent AltAz points |
| `sky/constellation_boundaries.py` | IAU FK4 B1875 boundary data | Astropy FK4 B1875 to AltAz | Observer-dependent AltAz curves |
| `charts/reference_furniture.py` | Mixed reference definitions | FK5 J2000 equator/grid; true ecliptic of observation date; Galactic; ecliptic keypoints independently converted to ICRS | A reference-only sky later realized and sometimes converted back to ICRS |
| `charts/circumpolar.py` | FK5 J2000 pole and limit | Astropy FK5 J2000 to observer AltAz before projection | Observer-dependent polar geometry |
| `charts/regional.py` | Target celestial coordinates | Both hand-written and Astropy/Skyfield paths occur in chart framing | Observer-dependent chart alignment |
| projection classes | Spherical geometry supplied by charts | Optional coordinate-neutral `SphericalFrame`, then projection law | Backend-neutral planar geometry |

This inventory covers the package owners of astronomical conversion. Renderer,
style, furniture typography, and export modules correctly do not own celestial
frame transformations.

## 4. Findings

### F1. Three transformation engines define astronomical positions

Wenu currently uses Astropy, Skyfield, and `radec_to_altaz()` for overlapping
astronomical conversions. Their physical assumptions are not identical. A
layer's apparent position can therefore depend on its class rather than only
on its source coordinate and the requested observing context.

### F2. The hand-written AltAz conversion is an unaudited parallel authority

`radec_to_altaz()` uses Skyfield GMST and spherical hour-angle formulae. It
does not express an Astropy source frame, target frame, observation scale,
Earth-orientation policy, atmospheric/refraction policy, or apparent-versus-
astrometric contract. It is used by reference points and grids while adjacent
layers use Astropy or Skyfield directly.

It must be removed from production geometry after callers migrate to the
canonical transformer. A temporary compatibility wrapper may delegate to the
canonical implementation during migration; it must not retain independent
mathematics.

### F3. Ecliptic definitions conflict

`Observer.ecliptic_frame` is `BarycentricMeanEcliptic` at the observation
date. `EclipticGrid` and the polar keypoint construction use
`BarycentricTrueEcliptic` at the observation date. Thus the public point API,
the ecliptic curve, and the polar cardinal points do not share one ecliptic
definition.

The polar star disk is explicitly observer-independent, yet its principal
ecliptic currently varies with the diagnostic observer time. This violates
the physical-product architecture even if the numerical displacement is
small.

### F4. Equatorial definitions conflict

The package uses ICRS, FK5 J2000, and FK5 of date as interchangeable
"equatorial" coordinates. They are not interchangeable contracts.
`CelestialSphere.add_equatorial_grid()` defaults to FK5 of date, polar
reference furniture requests FK5 J2000, catalogues are generally treated as
ICRS, and the polar chart returns to ICRS after an AltAz realization.

### F5. Observer-independent products take an observer-dependent detour

The canonical v0.8 sphere realizes most layers in AltAz. Polar planisphere
code then transforms that spherical geometry back to ICRS. Static catalogue
and reference geometry therefore acquires an unnecessary observer/time
dependency and a round trip:

```text
ICRS or native celestial frame -> AltAz(observer, time) -> ICRS -> projection
```

The target path is direct:

```text
native celestial frame -> canonical ICRS -> projection alignment -> projection
```

Observer-dependent AltAz is appropriate for horizon, visible-sky, and local
planisphere views, not for a printed celestial disk.

### F6. Geometry metadata does not enforce frame identity

Spherical geometry generally carries free-form strings such as
`coordinate_system="altaz"`. It does not require a typed frame specification,
equinox/epoch, observation time, location, representation convention, or
astrometric/apparent policy. The pipeline can therefore accept numerically
valid longitude/latitude arrays whose scientific meaning is ambiguous.

### F7. `SphericalFrame` has the right responsibility but an ambiguous name

The class performs a pure rotation and correctly avoids astronomical frame
semantics. Its use in projection classes is architecturally sound. However,
the word "frame" overlaps Astropy's astronomical frame terminology. The API
and documentation must consistently call it projection alignment (a future
rename may be separately considered); it must not become the package's
astronomical transformer.

### F8. Frame choice is partly owned by chart and furniture modules

`charts/coordinate_frames.py`, `reference_furniture.py`, `circumpolar.py`, and
`regional.py` construct or select astronomical frames. Charts should request
an output frame from the coordinate service, not implement conversions or
choose hidden equinox defaults.

## 5. Canonical target contract

The target ownership and flow are summarized visually in
`diagrams/coordinate_transformation_target_49bc.svg`; the Graphviz source is
`diagrams/coordinate_transformation_target_49bc.dot`. Proposed type/module
placement and runtime calls are shown separately in
`diagrams/coordinate_static_structure_target_49bc.svg` and
`diagrams/coordinate_runtime_sequence_target_49bc.svg`; their names and the
candidate `src/wenu/astronomy/` placement remain subject to 49B review.


### 5.1 Canonical celestial interchange frame

ICRS is Wenu's canonical celestial interchange frame for catalogue objects
and observer-independent atlas geometry. Catalogue loaders must declare their
native frame and transform once into ICRS, preserving source provenance and
native epoch/equinox metadata. Catalogue values must never be relabelled as
ICRS without a real transform.

Canonical does not mean that every source file must be rewritten. It means
that the first package boundary after loading yields explicit ICRS geometry.

Canonical does not mean that every time-dependent or local state must be
forced through ICRS. A scientifically defined transformation graph may use
another explicit path. Artificial-satellite TEME states, in particular, must
not be relabelled as ICRS; their route to Earth-fixed or observer-local
coordinates must follow a documented TEME transformation policy. The
single-system requirement is one governed transformation service and explicit
state semantics, not one compulsory intermediate frame for every problem.

### 5.2 Position-provider boundary

Moving-object support begins with specialized position providers:

| Object class | Position source | Typical native state |
|---|---|---|
| Stars with space motion | Catalogue astrometry | ICRS plus epoch and motion |
| Moon and planets | JPL or equivalent ephemeris | Barycentric/geocentric celestial state |
| Natural satellites | Planetary ephemeris or orbit model | Planet-centred state |
| Asteroids and comets | Ephemeris or orbital elements | Heliocentric/barycentric state |
| Artificial satellites | TLE/OMM plus SGP4 | TEME state |

Each provider must return an explicit state carrying at least:

- coordinate frame and origin;
- epoch and observation instant where applicable;
- time scale;
- position representation and units;
- geometric, astrometric, or apparent status;
- provider/model identity and provenance.

When relevant, the provider contract must also state light-time correction,
aberration, gravitational deflection, precession/nutation, Earth-orientation
data, and atmospheric-refraction policy. These are scientific semantics, not
renderer options.

The provider computes or propagates a state. It does not select a chart,
project, clip, style, or render, and it does not perform undocumented
downstream frame conversions.

### 5.3 Explicit product frame policy

Each chart request resolves one immutable celestial frame policy before
spherical realization:

- static celestial atlases and polar star disks: canonical ICRS geometry;
- legacy or publication grids requiring FK4/FK5: explicit frame and equinox;
- ecliptic references: one explicitly named mean or true ecliptic and one
  explicit equinox, never an implicit observation date;
- Galactic references: Astropy Galactic transformed through the same service;
- observer-local charts, horizons, and visibility: one explicit AltAz frame
  containing observation time and Earth location.

The canonical v0.9 physical polar planisphere must use a fixed documented
reference epoch/equinox so that regenerating it at a different time produces
the same star disk. Calendar calibration and later horizon overlays may use
site and civil-time inputs; those inputs must not move disk astronomy.

### 5.4 One transformer

A package-owned coordinate service must be the only production entry point
for astronomical frame conversions. Its responsibilities are:

1. accept coordinates or provider states with an explicit supported source
   frame, origin, and time semantics;
2. accept an explicit target frame or resolved product-frame policy;
3. use Astropy's transformation graph where Astropy defines the required
   frames, plus one documented adapter for specialized states such as TEME;
4. transform points and flattened curve/polygon collections without changing
   identifiers, labels, topology, or semantic metadata;
5. attach immutable source and target frame provenance to output geometry;
6. make atmospheric/refraction behavior explicit for AltAz;
7. reject frame-less astronomical longitude/latitude and origin-less moving
   states at public boundaries.

It does not compute an orbit or ephemeris, select catalogues, perform spatial
selection, rotate coordinates for projection alignment, project, clip,
render, or style.

### 5.5 Representation boundary

Astronomical transformation and projection alignment remain separate:

```text
Astropy frame transformation
    -> typed spherical geometry in the requested celestial frame
    -> coordinate-neutral projection alignment (`SphericalFrame` today)
    -> projection law
```

No projection class may import Astropy or infer an astronomical frame from
argument names such as `alt_deg` and `az_deg`.

### 5.6 Moving-object observation contract

Moon, planet, and satellite charts must choose their physical observation
contract explicitly. At minimum the request must resolve whether coordinates
are geometric, astrometric, or apparent and whether their origin is
barycentric, geocentric, planet-centred, Earth-fixed, or topocentric.

Topocentric apparent coordinates may depend on observer location, time,
light-time, aberration, deflection, Earth orientation, and optionally
refraction. These dependencies are correct for an observing product and must
be captured in immutable request/state provenance. They must not leak into an
observer-independent atlas product.

## 6. Required invariants and tests

The migration is not complete until tests establish all of these contracts.

### Frame and round-trip invariants

- ICRS -> Galactic -> ICRS round trips representative points within an
  explicit angular tolerance.
- ICRS -> selected ecliptic -> ICRS round trips representative points within
  the same declared tolerance.
- ICRS -> AltAz -> ICRS round trips for a fixed observer and time within the
  tolerance appropriate to the chosen physical policy.
- Point, curve, polygon, and grid transformations preserve shape, topology,
  identifiers, labels, names, and non-frame metadata.
- Empty and disconnected geometries preserve their structure.
- Provider states cannot enter the coordinate service without the frame,
  origin, instant, time scale, and physical-status metadata required by their
  object class.
- A supported artificial-satellite TEME-to-observer-AltAz reference case
  agrees with an independently validated SGP4/frame-transformation result.

### Reference-geometry invariants

- Equinox keypoints lie on both the selected ecliptic and the selected
  equatorial plane within spherical tolerance before projection.
- Solstice keypoints lie on the ecliptic and have the extrema required by the
  selected ecliptic/equatorial definition.
- Ecliptic poles are 90 degrees from every sampled point on the ecliptic.
- Galactic poles are 90 degrees from every sampled point on the Galactic
  equator.
- Celestial poles lie on every equatorial meridian.
- Projection does not change coincidences: independently constructed
  representations of the same celestial point project to the same x/y.

### Product invariants

- A polar star disk rendered with two different observer locations and times
  has identical pre-furniture astronomical geometry.
- Site/time changes affect calendar calibration, AltAz grids, horizons, and
  visibility only where their product contract requests them.
- Stars, constellation vertices, labels, boundaries, isophotes, grids, and
  reference points representing the same coordinate share one transformed
  position.
- Existing all-sky, regional, binocular, circumpolar, and planisphere chart
  baselines remain unchanged unless a reviewed migration step explicitly
  corrects their scientific geometry.

### Architectural enforcement

- Production modules outside the coordinate service may not call
  `SkyCoord.transform_to()` directly after migration.
- Production callers may not use independent RA/Dec-to-AltAz mathematics.
- Projection and rendering modules may not import Astropy coordinate frames.
- Observer-independent chart tests fail if astronomical geometry depends on
  observer location or observation time.

## 7. Migration sequence

The migration must remain incremental and leave Wenu usable after every
checkpoint.

### 48F.1: Frame vocabulary and typed policy

Introduce immutable frame specifications/product-frame policy and document
the fixed polar-disk policy. Do not change rendered output.

### 48F.2: Canonical geometry transformer

Add the single Astropy-backed geometry transformer with point, curve,
polygon, and grid support plus round-trip and metadata tests. Existing code
continues to operate until migrated.

### 48F.3: Reference geometry unification

Move equatorial, ecliptic, Galactic grids, poles, and ecliptic keypoints to
the canonical service and one shared frame policy. Add spherical coincidence
tests. This is the first step expected to correct the Milestone 48E.3 visual
misalignment without projected-coordinate adjustments.

### 48F.4: Observer-independent celestial layers

Provide direct canonical ICRS realization for stars, nonstellar catalogues,
constellation geometry, Milky Way, and Magellanic Clouds. Remove the
AltAz-to-ICRS detour from polar and other observer-independent products.

### 48F.5: Observer-local realization

Migrate horizon, AltAz grids, visibility, regional/planisphere observation,
and other local-sky paths to the same service. Replace
`radec_to_altaz()` with a compatibility delegate and then remove it when no
production caller remains.

### 48F.6: Position-provider and Skyfield boundary consolidation

Define the position-provider protocol before adding moving Solar System or
satellite layers. Make every remaining Skyfield responsibility explicit and
non-overlapping. Where stellar proper motion/apparent-place behavior is
required, define its output frame, origin, instant, and physical status and
feed it through the canonical geometry boundary. Reserve documented adapters
for JPL ephemerides and TEME/SGP4 states. Remove silent engine-dependent
differences between layer classes.

### 48F.7: Enforcement and documentation closure

Add import/source-boundary tests, update the active architecture,
implementation reference, source tree, and migration roadmap, and run the
full visual matrix. Only then resume horizon-overlay implementation.

## 8. Immediate scope boundary

Milestone 48F.0 changes documentation only. It deliberately does not:

- move the equinox markers;
- modify the ecliptic curve;
- change chart projections or handedness;
- change catalogue selection, styles, labels, or anchors;
- introduce a second sky pipeline;
- begin horizon-overlay implementation.

The first code change is Milestone 48F.1, after this audit and its fixed
polar-disk frame policy are reviewed.
