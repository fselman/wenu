# Observed Venus disk sequence — Milestone 49I.3C.3.1A

**Status:** Scientifically and architecturally accepted  
**Implementation baseline:** `8a6cb0f`  
**Acceptance date:** 2026-08-31

## Purpose

This bounded slice implements the output-neutral scientific state for an
observed multi-epoch resolved Venus sequence. It adds no public command,
registered sky layer, chart-frame transformation, projection, display
magnification, style, renderer, semantic SVG path, or visible output.

The later 49I.3C.3.1B slice remains responsible for transforming the accepted
per-epoch physical geometry into one fixed chart frame and making it drawable
in regional and binocular charts.

## Runtime contract

`ObservedSolarSystemDiskSequenceRequest` declares:

- one accepted `SolarSystemPointDescriptor`;
- one start instant and time scale;
- one positive major step in days;
- a non-negative number of major intervals;
- display name, physical radius, and radius model.

The start is included. Therefore `n_steps = 8` produces nine exact sample
instants. There is no minor cadence and no interpolation.

`ObservedSolarSystemDiskSequenceRealizer.sequence()` borrows one ephemeris
resource and independently reevaluates at every sample instant:

1. the geographic observer's barycentric state;
2. Venus's retarded astrometric state;
3. the Sun's astrometric state;
4. apparent-place correction for both directions;
5. physical angular diameter, phase, illuminated fraction, and bright-limb
   orientation;
6. physical spherical centre, limb, terminator, and illuminated face.

`ObservedSolarSystemDiskSequence` retains the exact sample instants,
appearances, physical disk geometries, and observer-target distances. Distances
have explicit origin `observer` and unit `au`; every value must equal the
accepted astrometric distance rather than a reconstruction from angular or page
geometry. This evidence is intentionally durable for a possible separately
governed future 3D Solar-System visualizer.

## Ownership

The implementation lives in
`src/wenu/sky/solar_system_disk_sequences.py`, beside the accepted scientific
track orchestration. It uses the shared point descriptor, direction chain,
appearance realizer, and spherical disk-geometry realizer. It imports no chart,
projected-geometry, projection, rendering, or export package.

The result is still a tuple of per-epoch physical spherical geometries because
their native apparent coordinate specifications carry different physical
instants. 49I.3C.3.1B must transform each sample independently into the one
fixed product frame before combining drawable components. It must not relabel
different native instants as one coordinate specification.

## Deterministic verification

Thirteen new sequence tests cover:

- exact start-inclusive count and offsets;
- zero-interval single-sample behavior;
- immutable request and result records;
- validation of cadence, count, radius, names, and model;
- independent target and Sun evaluation at every epoch;
- exact appearance-to-geometry identity;
- explicit observer/AU distance ownership;
- rejection of altered distances and mismatched geometry;
- typed request enforcement.

Together with the existing appearance and track tests, all 51 focused tests
passed in 1.89 seconds.

## Installed-DE440 validation

The accepted validator uses installed `de440s.bsp` with SHA-256

`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`

for La Ligua, starting at `2026-08-30T00:00:00Z`, with three 28-day
intervals:

| UTC instant | Distance (AU) | Diameter (arcsec) | Phase (deg) | Illuminated | Limb PA (deg) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-08-30 | 0.569805772037 | 29.287846514 | 101.448595073 | 0.400755660 | 295.354967208 |
| 2026-09-27 | 0.370888964237 | 44.995633795 | 128.846522744 | 0.186381796 | 299.517716780 |
| 2026-10-25 | 0.272806655466 | 61.172935877 | 171.044398241 | 0.006095368 | 33.312059954 |
| 2026-11-22 | 0.369101922820 | 45.213484358 | 127.038228646 | 0.198826124 | 111.670568432 |

Maximum residuals from independent direct Skyfield evaluation were:

- right ascension: `4.615e-10 deg`;
- declination: `1.946e-10 deg`;
- observer-target distance: `3.128e-12 AU`;
- angular diameter: `3.795e-10 arcsec`;
- phase angle: `7.096e-10 deg`;
- illuminated fraction: `4.823e-12`;
- bright-limb position angle: `4.301e-09 deg`.

The accepted comparison tolerances are `1e-9 deg` per direction component,
`1e-11 AU` in distance, `1e-8 arcsec` in angular diameter, `1e-9 deg`
in phase, `1e-11` in illuminated fraction, and `1e-8 deg` in bright-limb
position angle. The distance tolerance corresponds to about 1.5 metres; the
limb-angle tolerance corresponds to 36 microarcseconds and covers the increased
orientation sensitivity of the very thin 2026-10-25 crescent.

## Architectural verification

All 91 focused sequence, appearance, track, direction, apparent-place,
Skyfield-adapter, dependency-boundary, and package-boundary tests passed in
4.17 seconds.

## Acceptance and next boundary

Fernando scientifically and architecturally accepted 49I.3C.3.1A on
2026-08-31. This acceptance authorizes documentation closure and regression
verification for the output-neutral scientific sequence.

It does not pre-accept 49I.3C.3.1B request vocabulary, fixed-frame
transformation/aggregation, component layers, projected per-centre
magnification, date labels, semantic SVG identity, styles, or visible output.
Frozen-Earth ecliptic mode remains 49I.3C.3.2; Mercury remains 49I.3C.3.3.


## Regression closure

Documentation verification passed all 64 current-documentation tests in 2.23
seconds. The routine suite passed 1,985 tests with 30 deselected in 25.46
seconds, preserving the sub-30-second gate. The complete suite passed all 2,015
tests in 84.38 seconds.
