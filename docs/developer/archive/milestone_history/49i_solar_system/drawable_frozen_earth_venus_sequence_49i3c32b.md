# Drawable frozen-Earth Venus sequence — Milestone 49I.3C.3.2B

**Status:** Scientifically, architecturally, visually, and operationally accepted
**Implementation baseline:** `c30785c`
**Acceptance date:** 2026-09-01

## Accepted capability

Regional charts can draw the accepted frozen-Earth Venus construction with
`--planet-disk-sequence venus`, `--disk-sequence-model
frozen-earth-ecliptic`, an exact start, one positive major step, an interval
count, optional date labels, and one Venus display magnification. The start is
included, so `n_steps = 30` draws 31 independently realized disks.

The product freezes Earth's heliocentric ICRF vector at the start, advances
Venus at every requested epoch, and expresses the fixed Sun and all Venus disk
geometry in fixed J2000 mean-ecliptic axes with origin `frozen-earth`.
Directions remain geometric and are never described as apparent sky.

## Canonical drawing and restricted scene

`FrozenEarthVenusDiskSequenceRealization` adapts every accepted physical state
to ordinary illuminated-face, limb, terminator, centre, and Sun spherical
geometry. The canonical spherical guard, projection, per-centre preparation,
renderer, furniture, and PNG/PDF/SVG export remain authoritative.

The scene contains only the resolved Venus sequence, the central six-point Sun,
an optional equatorial grid, and an explicitly requested ecliptic reference.
The ecliptic is product-frame latitude zero. The equatorial grid is transformed
directly from FK5 into the same fixed mean-ecliptic axes; neither reference
passes through observer-dependent AltAz geometry. Horizon, ordinary tracks,
ordinary disks, catalogue content, unrelated reference furniture, legends,
context, and footer remain excluded.

The automatic title is `Frozen-Earth Venus sequence` in English and `Secuencia
de Venus desde una Tierra fija` in Spanish. Requested ecliptic labels use the
resolved chart language.

## Display, semantics, and provenance

One shared realization owns the independently identified illuminated, limb,
terminator, optional-label, and fixed-Sun layers. Venus semantic paths are
rooted at `sky/solar_system/planets/venus/frozen_earth_sequence`; physical
diameters, full ICRF vectors, frozen-earth/AU distances, exact instants, model,
and ephemeris provenance remain unchanged by display magnification.

Magnification scales each projected Venus component only about its separately
projected physical centre. The fixed Sun symbol is not magnified.

## Accepted visual calibration

Fernando accepted a La Ligua regional chart centred on Virgo, beginning
`2026-08-30T00:00:00Z`, with seven-day steps, 30 intervals, Venus
magnification 200, the ecliptic reference, and the equatorial grid. The final
chart showed 31 changing Venus disks, a fixed central Sun, the ecliptic through
the Sun, the distinct fixed-frame equatorial grid, the Spanish ecliptic label,
and the Spanish automatic title.

## Verification and boundary

The complete Mac suite passed all 2,037 tests in 84.41 seconds. The focused
coordinate, reference, drawing, command-line, and frozen-sequence suite passed
156 tests. All 67 current-documentation tests passed after this closure was
added.

Mercury remains the separately authorized and independently validated
49I.3C.3.3 milestone. No 3D Solar-System visualizer is installed or accepted.
