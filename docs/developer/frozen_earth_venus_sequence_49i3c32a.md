# Frozen-Earth Venus sequence state — Milestone 49I.3C.3.2A

**Status:** Scientifically and architecturally accepted  
**Implementation baseline:** `447e701`  
**Acceptance date:** 2026-09-01

## Purpose

This bounded slice implements the output-neutral scientific state for the
frozen-Earth ecliptic Venus construction accepted in 49I.3C.3. It adds no
public command, registered layer, disk geometry, projection, magnification,
Sun glyph, restricted chart scene, renderer, semantic SVG path, or visible
output. Those responsibilities remain 49I.3C.3.2B.

## Frozen-observer construction

`FrozenEarthDiskSequenceRequest` declares one start instant, positive major
step, non-negative interval count, body descriptor, physical radius, radius
model, and fixed ecliptic equinox. The start is included, so `n_steps = 3`
produces four samples. There is no minor cadence or interpolation.

`FrozenEarthDiskSequenceRealizer.sequence()` evaluates Earth's heliocentric
ICRF vector once at the start and retains it unchanged. At every major epoch it
evaluates Venus's same-epoch heliocentric geometric vector and forms
`planet heliocentric vector - frozen Earth heliocentric vector`.

The fixed Sun vector is the negative frozen-Earth vector. Target and Sun
directions are transformed into fixed J2000 mean-ecliptic axes with declared
origin `frozen-earth` and status `geometric`. They are not topocentric,
astrometric, apparent, aberrated, retarded, or corrected for gravitational
deflection.

## Physical state and retained evidence

Every `FrozenEarthGeometricDisk` contains the exact sample instant; complete
frozen Earth heliocentric and frozen-Earth-to-Venus ICRF vectors; distance with
origin `frozen-earth` and unit `au`; fixed-ecliptic target and Sun directions;
physical angular diameter; phase and illuminated fraction; bright-limb
position angle; physical radius model; and ephemeris provenance.

This information is not reconstructed from page geometry and remains durable
for a possible separately governed future 3D Solar-System visualizer.

## Deterministic and architectural verification

Tests cover exact start-inclusive sampling, one and only one Earth evaluation,
major-epoch Venus evaluation, fixed Sun and Earth vectors, retained distances,
physical diameter/phase/fraction, fixed-ecliptic coordinate identity,
geometric status, immutability, ephemeris-resource identity, unit enforcement,
and package dependency direction. All 63 focused sequence, appearance, and
dependency-boundary tests passed in 5.24 seconds.

## Installed-DE440 validation

The accepted validator used installed `de440s.bsp` with SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`
for a frozen Earth position at `2026-08-30T00:00:00Z`, followed by three
28-day intervals. The fixed Sun direction in J2000 mean-ecliptic coordinates
was longitude `156.290639154097 deg`, latitude `-0.000983124711 deg`.

| UTC instant | Ecliptic lon (deg) | Ecliptic lat (deg) | Distance (AU) | Diameter (arcsec) | Phase (deg) | Illuminated | Limb PA (deg) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-08-30 | 201.178836059 | -3.134613226 | 0.569758840908 | 29.290258959 | 101.451188917 | 0.400733475 | 273.140760296 |
| 2026-09-27 | 131.570116506 | -7.513346896 | 0.329448131422 | 50.655573460 | 142.875179667 | 0.101338727 | 74.146634682 |
| 2026-10-25 | 111.458121822 | -2.052917174 | 0.845667085410 | 19.733987848 | 79.654977593 | 0.589787643 | 87.937772063 |
| 2026-11-22 | 124.412852392 | 0.001454818 | 1.341990243901 | 12.435547918 | 47.741024755 | 0.836241376 | 90.004200877 |

Maximum residuals were `2.365e-12 AU` in the frozen Earth vector,
`4.337e-12 AU` in target vectors, `1.968e-10 deg` in ecliptic longitude,
`2.064e-11 deg` in latitude, `1.274e-12 AU` in distance,
`1.111e-10 arcsec` in diameter, `2.702e-10 deg` in phase, `1.423e-12` in
illuminated fraction, and `1.627e-10 deg` in bright-limb position angle.

## Regression closure

All 66 current-documentation tests passed in 1.14 seconds.
The routine suite passed 1,997 tests with 30 deselected in 26.69 seconds,
preserving the sub-30-second gate. The complete suite passed all 2,027 tests
in 84.73 seconds.

## Acceptance and next boundary

Fernando scientifically and architecturally accepted 49I.3C.3.2A on
2026-09-01. It does not pre-accept 49I.3C.3.2B public vocabulary, spherical
disk adaptation, projected per-centre magnification, labels, central six-point
Sun, equatorial-grid transformation, restricted scene, semantics, styles, or
visible output. Mercury remains independently governed by 49I.3C.3.3.
