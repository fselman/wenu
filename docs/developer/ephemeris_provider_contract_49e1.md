# Milestone 49E.1 — Ephemeris-provider contract audit

**Status:** Scientifically and pedagogically accepted; merged in `d14ca52`

**As-is baseline:** `85c7392`

**Date:** 2026-08-29

## 1. Purpose

49E.1 defines the scientific ownership needed between the accepted 49D.2
layer-realization handoff and a later Sun, Moon, or planet layer. It deliberately
does not install an ephemeris provider, choose a first body, expose a public
option, or draw a moving object.

The design prevents two scientifically incorrect shortcuts:

1. treating a raw barycentric Cartesian state as though it were already a sky
   direction; and
2. letting a renderer, SVG serializer, or chart layer silently choose
   light-time, aberration, gravitational deflection, observer, frame, origin,
   time scale, or kernel policy.

## 2. As-is findings

### 2.1 Existing generic position boundary

`positions.py::PositionProvider.position(instant: str | None)` returns
`SphericalPoints`. Current catalogue providers can use this small protocol
because their native product is already a set of spherical catalogue
directions with a `CoordinateSpec`.

That return type is insufficient as the sole solar-system ephemeris contract.
A physical ephemeris state also needs target identity, centre, frame
orientation, position and velocity units, evaluation epoch and scale, kernel
identity and coverage, and provenance. Distance and velocity cannot be
discarded before light-time and observer-relative realization are resolved.

### 2.2 Current ephemeris ownership

`observer.py::Observer` currently loads the configurable Skyfield kernel
(default `de440s.bsp`), constructs the Earth-plus-site observer, and exposes
the established `observer.skyfield` compatibility attribute. Stars and
constellation lines reuse that observer-bound Skyfield machinery.

This is useful installed infrastructure but not yet a general provider
contract. A future provider may adapt the already loaded resource; it must not
silently load a second competing kernel or make `Observer` the universal
owner of every solar-system target.

### 2.3 Accepted realization insertion point

`LayerRealizationContext` already carries the requested spherical product
`CoordinateSpec`, observation context, provider-evaluation instant/time
scale, and resolved reference equinox. `SkyLayer.realize()` is the optional
pre-projection hook.

49E must supply scientifically identified provider output to that hook. It
must not add another projection, scene, renderer, or export path.

## 3. Required two-stage boundary

A solar-system direction is not merely an ephemeris table lookup. Wenu needs
two explicit scientific stages.

### Stage A — ephemeris state source

An ephemeris source evaluates a target state relative to a declared centre in a
declared Cartesian frame. Conceptually:

```python
state = source.state(request)
```

The result is a typed physical state, not projected geometry and not
necessarily a line of sight.

### Stage B — solar-system direction realization

A solar-system realizer combines provider states with the declared observer,
reception instant, and correction policy. It produces an explicitly identified
geometric, astrometric, apparent, topocentric, or observed spherical direction.
Conceptually:

```python
native_direction = realizer.direction(state_source, request, observation)
product_direction = coordinate_service.transform(
    native_direction,
    context.product_coordinate_spec,
    observation=context.observation,
)
```

The realizer may need repeated target evaluations at retarded emission times.
Therefore the API must not assume that one target state sampled at the
reception instant is sufficient for an astrometric or apparent place.

`CoordinateService` owns the subsequent coordinate representation/frame
transformation. It does not invent omitted light-time or apparent-place
physics.

## 4. Minimum state-source vocabulary

The 49E.2 runtime design should represent at least the following information.

| Field | Scientific meaning |
| --- | --- |
| target key | Stable Wenu target identity; provider-native/NAIF identifier is separate provenance |
| centre key | Body or barycentre relative to which the vector is measured |
| frame | Orientation of the Cartesian axes, independently of the centre |
| evaluation instant | Physical epoch of the returned state |
| time scale | Scale used to interpret that epoch, commonly TDB for planetary ephemerides |
| position | Three Cartesian components |
| velocity | Three Cartesian components when supplied by the source |
| position and velocity units | Explicit, never inferred from a kernel filename |
| provider/model | Skyfield/JPL/SPICE or another declared authority and model |
| kernel identity | Filename plus durable version/checksum or equivalent dataset identity |
| coverage | Valid target/time interval or a deterministic coverage failure |
| provenance | Source lineage and any provider-native segment/identifier information |
| corrections | Normally empty for a geometric state; never inferred |

Following SPK terminology, a state is the position and velocity of a target
relative to a centre, expressed in a reference frame. **Centre and frame are
not synonyms.** “Barycentric,” “geocentric,” and “topocentric” describe origin
or centre; ICRS, GCRS, ITRS, and provider `J2000` conventions describe axis
orientation or coordinate systems.

## 5. Minimum evaluation-request vocabulary

A real ephemeris request must identify:

- one target;
- the observation/reception instant and its input time scale;
- the requested scientific position status;
- the observer or centre required by that status;
- an explicit correction policy;
- the provider/dataset selection or an already resolved provider;
- deterministic behavior outside kernel coverage.

The public civil time may enter Wenu as UTC, while a JPL-style ephemeris is
evaluated on a dynamical scale such as TDB. These are two representations of
one physical instant, not two independent chart times. Conversion authority and
leap-second provenance must remain explicit.

For an apparent place, the target is generally evaluated at an emission time
earlier than the reception time by the one-way light time. Wenu must retain
enough provenance to state which epoch each vector represents.

## 6. Position-status and correction policy

The following meanings are required for solar-system work.

| Product | Minimum meaning |
| --- | --- |
| geometric state/direction | Simultaneous coordinate difference; no light-time or apparent-place correction |
| astrometric direction | Observer-to-target line of sight including light-time, before apparent deflection and aberration |
| apparent direction | Astrometric direction plus the declared gravitational-deflection and aberration models |
| topocentric direction | Origin is the terrestrial observing site; this alone does not say which corrections were applied |
| observed AltAz | Topocentric apparent direction plus the declared atmospheric/refraction policy |

`PositionStatus.TOPOCENTRIC` is scientifically misplaced because
topocentricity is an origin choice rather than a correction status. The as-is
usage audit found only the enum declaration, the default in
`observer_altaz_spec()`, and two focused tests. Wenu has not released this
interface, so 49E.2 must remove the enum member and migrate those uses
atomically instead of preserving or deprecating a faulty abstraction. New
observer-centred products combine an explicit observer/topocentre origin with
`ASTROMETRIC`, `APPARENT`, or `OBSERVED` status.

Correction provenance must enumerate applied physics, including where
applicable:

- one-way light time and iteration/convergence policy;
- stellar/annual aberration;
- gravitational deflection and the deflecting bodies/model;
- Earth orientation, precession-nutation, and polar motion;
- diurnal aberration and site displacement if provided;
- atmospheric refraction only for an observed product.

No correction may be implied merely by a class name such as “apparent.”

## 7. Kernel, resource, and reproducibility policy

The provider owns kernel opening, target lookup, coverage validation, and
resource lifetime. The request or resolved configuration owns kernel
selection. A chart layer must not call a global downloader.

The first implementation should evaluate whether it can reuse the kernel
already resolved by `Observer` without preserving the present coupling as the
final public design. Whichever owner is selected must guarantee:

- one resolved kernel authority per request;
- deterministic target resolution;
- explicit coverage errors;
- clean resource closing;
- no hidden network access during rendering;
- recorded kernel/model provenance in exported metadata where supported.

A kernel's **model**, **file identity**, and **content identity** are distinct.
For example, `DE440` names the astronomical solution family;
`de440s.bsp` names a particular short-coverage distribution; and a SHA-256
digest fingerprints the exact bytes that Wenu opened. The resolved resource
must record all three, plus coverage and provider/segment provenance. A
filename alone is not reproducible because files can be renamed or replaced;
a model name alone does not identify which subset or coverage was used.

The SHA-256 digest is computed once when the resource is resolved, retained in
its immutable identity, and reused for every body evaluation. It is not
recomputed for each coordinate. Full provenance belongs in a manifest and
machine-readable SVG/PDF metadata where supported; a printed chart may show
only a concise credit such as “JPL DE440.”

Loading order matters when ephemeris datasets contain competing segments.
Therefore “a JPL ephemeris was used” is not sufficient reproducibility
metadata.

## 8. Relationship to Wenu geometry and products

A raw ephemeris state is not `SphericalGeometry`. Only after the direction
realizer establishes observer, physical status, corrections, and native
coordinate identity may it create `SphericalPoints`.

The future moving-object layer then:

1. obtains the typed direction realization;
2. transforms it exactly once into
   `LayerRealizationContext.product_coordinate_spec`;
3. assigns stable semantic identity before projection;
4. enters the existing projection, preparation, renderer, and single exporter.

PNG, PDF, and SVG consume the same projected record. SVG may serialize the
reserved `solar-system/sun`, `solar-system/moon`, and
`solar-system/planets` hierarchy but does not evaluate an ephemeris or alter
coordinates.

## 9. Body geometry deliberately deferred

A centre direction is not yet the complete visual/physical model of a nearby
resolved body.

Later vertical slices must separately decide:

- angular radius from physical radius and observer distance;
- lunar or planetary phase and illuminated limb;
- orientation of the rotation axis, equator, rings, and surface features;
- occultation, eclipse, transit, and mutual-event geometry;
- labels, trails, magnitude/brightness model, and visibility selection.

These are renderer-neutral astronomical data or chart policy as appropriate.
They must not be reconstructed from SVG marker size or paint appearance.

## 10. Proposed milestone sequence

### 49E.1 — this audit

Agree on the two-stage state-source/direction-realizer boundary, required
identity/provenance, time semantics, corrections, kernel ownership questions,
and non-goals. Documentation only.

### 49E.2 — minimal runtime contracts

Add frozen request/state/provenance types and structural protocols, with
deterministic test sources. Do not load a real kernel or add a body.

### 49E.3 — installed kernel adapter

Adapt one resolved Skyfield/JPL kernel behind the contract, verify target
identity, coverage, units, time-scale conversion, resource ownership, and
numerical state comparisons. Still no chart layer unless separately approved.

### 49I.1 — Venus vertical slice

Add Venus first through the accepted realization, coordinate, semantic,
projection, renderer, and export path. Begin with an accurately realized
planetary position/symbol; retain the three-dimensional distance and state
needed for a later resolved illuminated disk, angular diameter, phase, and
elongation validation. The Moon follows as the strongest topocentric-parallax
and rapidly varying resolved-body test.

## 11. Explicit non-goals

49E.1 does not:

- add runtime source, request, state, or realizer classes;
- change `PositionProvider`;
- choose Skyfield, Astropy, SPICE, or Horizons as the permanent public API;
- select a kernel beyond recording the current `de440s.bsp` default;
- add or download ephemeris data;
- add the Sun, Moon, planet, phase, disk, trail, label, or magnitude;
- expose CLI or TOML options;
- change `Observer`, `CoordinateService`, or current chart output;
- create an SVG-specific astronomical path;
- change numerical or visual baselines.

## 12. Accepted scientific decisions

Fernando accepted the revised 49E.1 design on 2026-08-30:

1. preserve the two-stage state-source/direction-realizer separation;
2. define `EphemerisState` as a complete six-component position-velocity
   state; a future position-only source must use a differently named type;
3. require resolved kernel identity to include provider/model, filename,
   SHA-256 content fingerprint, coverage, and provenance;
4. remove `PositionStatus.TOPOCENTRIC` atomically in 49E.2 because Wenu is
   unreleased and topocentricity belongs in the origin dimension;
5. move toward one request/session-scoped ephemeris resource while permitting
   the first adapter to reuse the already-open Observer kernel without loading
   a duplicate; and
6. use Venus for 49I.1, followed by the Moon.

No visual comparison is required because this audit changes no runtime code or
output.

Acceptance verification passed all 41 current-documentation tests in 3.26
seconds on Fernando's Mac. The review confirmed the scientific distinctions,
accepted decisions, kernel-identity explanation, implementation ownership, and
pedagogical treatment. No visual comparison was required because 49E.1 changes
no runtime code, geometry, or output.
