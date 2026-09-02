# Venus spherical disk geometry — Milestone 49I.3C.1

**Status:** Scientifically and architecturally accepted

**Acceptance date:** 2026-08-31

**Implementation baseline:** `a308ba2`

## 1. Purpose

49I.3C.1 converts the accepted `SolarSystemApparentDisk` state into ordinary
physical spherical geometry. It adds one centre point, one closed limb, one
visible terminator, and one illuminated-face polygon.

The milestone adds no sky layer, chart request, display magnification, style,
renderer behavior, semantic SVG artist, or visible output. It is the
output-neutral scientific prerequisite for 49I.3C.2.

## 2. Runtime ownership

`src/wenu/solar_system_disk_geometry.py` owns:

- `SolarSystemDiskGeometry`, a frozen bundle of the four spherical records;
- `SolarSystemDiskGeometryRealizer.geometry()`, the physical construction;
- `DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES = 720`;
- the explicit geometry-model identity.

The module imports ordinary spherical geometry and the accepted appearance
state. It imports no sky, projection, chart, rendering, or export package.

## 3. Frozen geometry bundle

`SolarSystemDiskGeometry` contains:

- the source `SolarSystemApparentDisk`;
- a one-point `SphericalPoints` centre;
- a one-curve closed `SphericalCurves` limb;
- a one-curve open `SphericalCurves` terminator;
- a one-polygon `SphericalPolygons` illuminated face;
- the even physical boundary sample count.

Every component preserves the appearance direction's exact
`CoordinateSpec`. Metadata records target, display name, physical angular
radius, phase angle, illuminated fraction, bright-limb position angle and
convention, sample count, geometry model, radius model, provenance, and
component name.

## 4. Accepted physical construction

Let the accepted apparent centre direction be `z`. At that direction, let
`n` and `e` point toward apparent celestial north and east. For the
accepted bright-limb position angle `chi`, measured north through east,

`l = cos(chi) * n + sin(chi) * e`

points toward the apparent Sun, and

`m = -sin(chi) * n + cos(chi) * e`

is its perpendicular tangent direction.

The physical angular radius is half the accepted 49I.3B angular diameter.
The limb uses a unit circle in local disk coordinates. For phase angle `i`,
the visible terminator uses

- `x = cos(i) * cos(u)`;
- `y = sin(u)`;
- `u` from 90 to 270 degrees.

The illuminated polygon joins the Sun-facing limb semicircle from bottom to
top to the visible terminator from top to bottom. The construction gives:

- a full disk at phase 0 degrees;
- a gibbous disk below 90 degrees;
- a diameter terminator at 90 degrees;
- a crescent above 90 degrees;
- a zero-area limiting polygon at 180 degrees.

A local point with normalized radius `r` is mapped to the celestial sphere
at angular offset `r * physical_angular_radius`. The accepted model identity
is `orthographic spherical phase with radial angular-offset mapping`.

This is a physical, renderer-neutral phase model. It does not apply display
magnification and does not claim surface texture, atmospheric scattering,
limb darkening, or body-axis markings.

## 5. Sampling contract

The default limb has 720 evenly spaced vertices. The visible terminator has
361 vertices including both limb endpoints. The illuminated polygon has 720
vertices after shared endpoints are represented once and implicit polygon
closure is used.

A custom sample count must be an even integer of at least 16. Boolean,
floating-point, string, odd, and smaller values are rejected.

The sample count and model identity remain in metadata. 49I.3C.2 must validate
that this physical sampling is adequate for its supported maximum
post-projection magnification and output resolution. Magnification is not
implemented by 49I.3C.1.

## 6. Deterministic validation

The deterministic suite covers:

- concrete geometry types, counts, closure, coordinate specification, and
  metadata;
- constant physical angular radius around the limb;
- quarter-phase diameter and shared terminator endpoints;
- normalized illuminated areas at phase angles 0, 60, 90, 120, and 180
  degrees;
- bright-limb midpoint orientation at position angles 0, 37, 90, and 295
  degrees;
- exact centre identity and appearance provenance;
- invalid sample counts and appearance types;
- frozen bundle behavior.

All 29 appearance and disk-geometry tests passed in 1.94 seconds. All 54
focused appearance, coordinate-service, and dependency-boundary tests passed
in 4.80 seconds.

## 7. Installed-DE440 validation

`tools/validate_49i3c1_venus_disk_geometry.py` refuses to download a missing
kernel and validates La Ligua at `2026-08-30T00:00:00Z` using the installed
DE440 kernel with SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`.

The accepted physical radius is `14.643923257181 arcsec`. The validator
measured:

| Quantity | Residual | Acceptance tolerance |
| --- | ---: | ---: |
| maximum limb radius | `9.799e-11 arcsec` | `1e-7 arcsec` |
| terminator endpoint closure | `0.000e+00 arcsec` | `1e-7 arcsec` |
| normalized illuminated area | `-5.087e-06` | `2e-5` |
| bright-limb midpoint angle | `-1.495e-10 deg` | `1e-9 deg` |

The finite illuminated-area residual is the expected straight-segment
approximation of a curved 720-vertex boundary. Radius, closure, and orientation
residuals are numerical roundoff at the stated scale.

## 8. Architectural consequences

49I.3C.1 proves that resolved phase geometry can remain ordinary typed
spherical geometry through the existing coordinate service and projection
path. It does not require a mixed `SphericalGrid`, special projection, custom
renderer, or format-specific geometry.

The bundle itself is not a new geometry kind for `CoordinateService`.
49I.3C.2 will transform and project its ordinary centre, polygon, and curve
records through the canonical layer pipeline.

## 9. Non-goals

49I.3C.1 does not:

- draw Venus;
- magnify projected geometry;
- select chart families or representation mode;
- install CLI or Python chart-request vocabulary;
- choose fill, stroke, colour, line width, alpha, or z-order;
- attach final semantic SVG paths to artists;
- create multi-epoch disks;
- add photometry or magnitude-scaled symbolic appearance;
- generalize the validated Venus model to the Moon or another body.

## 10. Acceptance

Fernando accepted the geometry model, 720-sample default, numerical
tolerances, installed-DE440 result, and output-neutral boundary on
2026-08-31.

Final verification passed all 61 current-documentation tests in 2.35 seconds,
1,958 routine tests with 30 deselected in 27.07 seconds, and all 1,988 tests
in 89.21 seconds. Acceptance of 49I.3C.1 does not pre-accept the future
49I.3C.2 request, magnification range, style, semantic output, or visual
result.
