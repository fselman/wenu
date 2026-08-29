# Wenu target architecture v0.9.5

**Status:** Implemented and accepted; 49C.4 merged in `1a15076`

**Date:** 2026-08-28

**Release status:** Architecture implementation accepted. This document does not claim a
`v0.9.5` Git tag or package release.

## Why this work exists

Before 49B/49C, Wenu distributed coordinate transformations across Astropy,
Skyfield, a handwritten RA/Dec-to-AltAz function, chart helpers, astronomical
objects, reference grids, and observer-keyed caches. Coordinate arrays did not
carry one enforceable statement of frame, origin, epoch/equinox, instant, time
scale, observer dependence, position status, and provenance.

The polar-planisphere equinox discrepancy demonstrated that independently
valid-looking geometry can reach one product through inconsistent scientific
assumptions. Future Moon, planet, comet, asteroid, and satellite support would
multiply those paths unless position generation and coordinate transformation
are separated now.

Architecture 0.9.5 therefore establishes one traceable scientific meaning for
every astronomical coordinate while preserving Wenu's existing geometry,
projection, clipping, rendering, SVG/PDF/PNG, and temporal-sequence pipeline.

## Target boundary

1. Every astronomical object obtains its native position through a common
   `PositionProvider`.
2. Constructed grids, planes, poles, and keypoints remain reference geometry,
   not astronomical-object positions.
3. Both source families produce existing `Spherical*` geometry carrying an
   immutable `CoordinateSpec`.
4. One Astropy-backed `CoordinateService` owns astronomical
   transformations.
5. `ObservationContext` enters only an explicitly observer-local path.
6. `SphericalFrame` remains a pure projection-alignment rotation.
7. Projection, clipping, preparation, rendering, furniture, and export remain
   astronomically neutral.

Adding a new astronomical object family must require a provider implementation,
not a coordinate, projection, or renderer modification.

## Minimal roadmap

### 49B.1 — Freeze scientific contracts

**Implementation status:** Accepted and merged in `d63c300`.

Add `CoordinateSpec`, `ObservationContext`, `PositionProvider`, and the
`SphericalGeometry` union without changing numerical transformations.

### 49B.2 — Attach identity to geometry

**Implementation status:** Accepted and merged in `db946cc`.

Add mandatory coordinate identity to `SphericalPoints`,
`SphericalCurves`, `SphericalPolygons`, and `SphericalGrid`. Prevent
silent relabelling.

### 49B.3 — Establish existing providers

**Implementation status:** Accepted and merged in `2492846`.

Make star and non-stellar position sources satisfy `PositionProvider` while
initially retaining their numerical behavior. Keep extended morphology and
constructed reference geometry separate.

### 49C.1 — Implement one coordinate service

**Implementation status:** Accepted and merged in `5131500`.

Implement an Astropy-backed `transform()` accepting every spherical geometry
kind and returning the same kind while preserving IDs, metadata, curve
segmentation, polygon rings, and semantic topology.

### 49C.2 — Migrate transformations

**Implementation status:** Accepted and merged in `f42f236`.

Migrate in this order:

1. reference points and grids;
2. chart-level equatorial/Galactic conversions;
3. deep-sky centres and outlines;
4. preserve Skyfield apparent stellar realization as provider work and reuse
   it for constellation lines;
5. preserve native AltAz horizon construction while routing celestial
   conversion and physical-planisphere furniture through the service.

### 49C.3 — Retire competing transformation owners

**Implementation status:** Accepted and merged in `034bdd8`.

The merged implementation removes `radec_to_altaz()` and
`charts/coordinate_frames.py`, routes every remaining production Astropy
transformation through `CoordinateService`, and removes Observer-owned ICRS,
Galactic, and ecliptic frame properties. `Observer.observation_context` is the
explicit immutable service input; AltAz and time properties remain provider
and public Astropy-coordinate compatibility inputs.

### 49C.4 — Accept and close

**Implementation status:** Accepted and merged in `1a15076`.

Scientific comparison with Astropy, topology/provenance preservation, current
as-is diagram review, and fixed-sky/rotating-horizon visual acceptance passed.
The final routine suite passed 1779 tests with 30 deselected in 27.31 seconds;
the complete suite passed 1809 tests in 84.99 seconds. The La Ligua
stereographic planisphere exposed and then verified the correction of a mixed
J2000-equator/ecliptic-of-date policy: its equatorial grid, celestial equator,
ecliptic, and four seasonal keypoints now share the J2000 policy. Fernando
visually accepted the corrected equinox intersections and the final fixed-sky
reference on 2026-08-28.

## Scientific companion

The living equations, conventions, current code map, object inventory, and
provenance record are maintained in
`coordinate_system_guide_v0.9.5.md` as the sole canonical source. Other
review formats are generated from that Markdown on demand.
