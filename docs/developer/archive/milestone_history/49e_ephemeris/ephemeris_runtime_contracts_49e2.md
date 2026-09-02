# Milestone 49E.2 — Minimal ephemeris runtime contracts

**Status:** Scientifically accepted by Fernando on 2026-08-30; ready for integration

**Implementation baseline:** `d14ca52`

**Date:** 2026-08-30

## 1. Purpose

49E.2 implements the smallest runtime portion of the accepted 49E.1 design. It
adds immutable Cartesian ephemeris-resource, request, and six-component state
contracts plus a structural state-source protocol. It also removes the
unreleased `PositionStatus.TOPOCENTRIC` category atomically.

The milestone does not open a kernel, evaluate a real body, realize an apparent
direction, add a sky layer, or draw Venus.

## 2. Implemented types

### `EphemerisResourceIdentity`

One frozen resolved-resource identity records:

- provider;
- scientific model;
- actual filename;
- 64-hexadecimal SHA-256 content fingerprint;
- coverage start and end;
- coverage time scale;
- provenance entries.

The digest and coverage scale are normalized to lowercase. The digest is
validated structurally but not calculated here: a later resource owner computes
it once when resolving a real kernel.

### `EphemerisStateRequest`

One frozen geometric state request records:

- stable Wenu target key;
- centre key;
- Cartesian frame;
- evaluation instant;
- evaluation time scale.

Frame and time scale are normalized to lowercase. Target and centre remain
distinct. The request contains no observer, projection, appearance, chart,
output, download, or cache policy.

### `EphemerisState`

One frozen source result requires:

- a typed `EphemerisStateRequest`;
- exactly three finite position components;
- exactly three finite velocity components;
- explicit position and velocity units;
- a typed `EphemerisResourceIdentity`;
- optional provider-native target and centre identifiers;
- state-specific provenance.

There is no default or optional velocity. A position-only producer cannot
construct an `EphemerisState`; a future need for such a product requires a
separately named contract.

### `EphemerisStateSource`

The runtime-checkable structural protocol is:

```python
class EphemerisStateSource(Protocol):
    def state(
        self,
        request: EphemerisStateRequest,
    ) -> EphemerisState:
        ...
```

It owns native geometric state evaluation only. It does not own observer
selection, light-time/apparent-place realization, coordinate transformation,
projection, rendering, SVG, or export.

## 3. Position-status correction

49E.2 removes `PositionStatus.TOPOCENTRIC`. Topocentricity is represented by
`CoordinateSpec.origin == "observer"`, independently of the physical status.

The as-is executable inventory contained only:

1. the enum declaration;
2. the default status in `observer_altaz_spec()`; and
3. two focused coordinate-service tests.

There is no released interface to preserve. `observer_altaz_spec()` now requires an explicit `position_status`; it has no
scientific default. Catalogue and celestial directions transformed for an
observer declare `APPARENT`. Native observer-local horizon, cardinal/zenith,
and AltAz-grid constructions declare `GEOMETRIC`. The helper continues to set
`origin="observer"` independently. Skyfield stellar and constellation paths
had already requested `APPARENT` explicitly.

This is an atomic internal correction, not a compatibility deprecation.

Requiring the keyword prevents future callers from silently assigning one
physical meaning to unlike geometry. It also leaves `OBSERVED` reserved for a
future non-vacuum atmospheric/refraction realization.

## 4. Scientific boundary preserved

The new state is geometric Cartesian provider output. It is deliberately not:

- `CoordinateSpec`;
- `SphericalGeometry`;
- an astrometric or apparent direction;
- an observer-local AltAz coordinate;
- a drawable body;
- a projected or semantic SVG record.

A later direction realizer may call an `EphemerisStateSource` repeatedly at
retarded emission times, combine target and observer states, and apply declared
light-time, aberration, and gravitational-deflection policies. Only its typed
spherical result may proceed through `CoordinateService` and the accepted
49D.2 layer-realization hook.

## 5. Deterministic proof

`tests/test_ephemeris.py` uses no real kernel. Its test-only source satisfies
the structural protocol and returns a deterministic Venus state. Tests protect:

- frozen values;
- text and time-scale normalization;
- exact SHA-256 shape;
- typed request/resource ownership;
- exactly three finite position and velocity components;
- rejection of position-only construction;
- structural provider conformance;
- removal of `TOPOCENTRIC`; and
- mandatory explicit AltAz status, apparent observer-transformed directions,
  and geometric native observer-local references.

This proves contract shape and ownership, not ephemeris accuracy.

## 6. Relationship to Venus and output products

Venus remains the first planned 49I.1 body, but 49E.2 does not create it. A
future Venus layer must receive a direction from the later realizer, transform
once into the requested product frame, assign stable
`solar-system/planets/venus` semantic identity before projection, and use the
same projected record for PNG, PDF, and SVG.

The state retains position, velocity, distance-bearing Cartesian geometry, and
exact resource identity so later Venus work can add elongation, angular
diameter, phase, and an illuminated disk without redesigning the provider
boundary.

## 7. Explicit non-goals

49E.2 does not:

- calculate a SHA-256 digest from a file;
- open, download, select, or close a kernel;
- add a resource cache or global ephemeris singleton;
- adapt Skyfield, Astropy, SPICE, or Horizons;
- convert UTC to TDB;
- evaluate light time or an emission epoch;
- implement a direction realizer;
- add Venus, the Moon, the Sun, or another body;
- add phase, angular radius, magnitude, trail, label, or disk geometry;
- expose CLI/TOML configuration;
- modify `Observer`, `LayerRealizationContext`, `CoordinateService`,
  projection, renderer, or exporter;
- change visual output.

## 8. Acceptance requirements

49E.2 is accepted when:

1. focused ephemeris, coordinate-service, vocabulary, realization, and
   documentation tests pass;
2. the routine and complete suites pass;
3. Fernando accepts the state/resource/request fields and atomic
   `TOPOCENTRIC` removal;
4. the test source remains outside installed code;
5. no current numerical or visual output changes unexpectedly; and
6. the coordinate guide remains scientifically and pedagogically correct.

No new visual render was required because no ordinary chart request or layer
uses the new state boundary and numerical chart geometry did not change.

## 9. Acceptance outcome

Fernando scientifically accepted 49E.2 on 2026-08-30. Acceptance confirms:

- the immutable resource, request, and complete position-velocity state fields;
- SHA-256 resource identity and coverage provenance;
- atomic removal of the unreleased `TOPOCENTRIC` status;
- independence of observer origin from geometric, apparent, and observed status;
- explicit `GEOMETRIC` native AltAz references and `APPARENT`
  observer-transformed celestial directions; and
- the canonical layer, composition, renderer, and PNG/PDF/SVG export path for
  future Venus, Moon, planet, and Sun products.

Verification evidence was 92 focused tests in 2.72 seconds, 1,821 routine tests
with 30 deselected in 25.25 seconds, and all 1,851 tests in 84.12 seconds.
After merge, 49E.3 may add one real resolved-kernel adapter; Venus remains a
later 49I.1 slice.
