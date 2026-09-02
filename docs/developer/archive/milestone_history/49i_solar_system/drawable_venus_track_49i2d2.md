# Milestone 49I.2D.2 — Drawable Venus track

**Status:** Scientifically, architecturally, and visually accepted by Fernando
on 2026-08-31; ready for integration  
**Implementation baseline:** `05b011e`  
**Date:** 2026-08-31

## Boundary

49I.2D.2 installs the first visible use of the accepted shared
Solar-System track curve. Regional and binocular charts can request a Venus
trajectory independently of the ordinary Venus point. Planisphere and all-sky
tracks, multiple simultaneous tracks, physical disks, phase, illumination,
photometry, and provider batching remain outside this milestone.

## Public request

The accepted command vocabulary is:

```text
--planet-track venus
--track-start 2026-08-30T00:00:00Z
--track-sample-step 12h
--track-tick-step 7d
--track-tick-count 8
--track-tick-labels
```

The first five fields own physical sampling and exact major-time anchors.
`--track-tick-labels` changes only annotation. Track selection remains
independent of `--planet venus`.

## Canonical realization and ownership

`SolarSystemTrackLayer` remains in `wenu.sky` and owns only the scientific
realization of one fixed-product-frame `SphericalCurves`. It imports no chart,
projected-geometry, or renderer policy.

`wenu.charts.solar_system_track_annotations` owns the downstream projected
path, page-space perpendicular ticks, start label, and date-label layout.
`detail_application.py` supplies style-owned appearance and installs those
options through the ordinary chart composition. The canonical projection,
preparation, renderer, semantic SVG, and shared PNG/PDF/SVG exporter remain
unchanged.

The semantic hierarchy is
`sky/solar_system/planets/venus/track`.

## Tick and label geometry

Every major tick is constructed perpendicular to the local projected tangent.
A stationary anchor uses the nearest distinct samples on both sides; an
unresolved tangent is omitted with deterministic metadata.

Each date has exactly two possible anchors, beyond the two ends of its
perpendicular tick. Labels never slide along the trajectory. Placement is
evaluated chronologically in two complete passes, beginning from opposite
sides. Within one pass the current side is retained unless the other side has
less obstruction from the nonlocal projected curve, earlier date labels, or
the viewport. The completed layouts are compared by curve conflicts, label
conflicts, boundary conflicts, and side changes. The start glyph/date uses a
separate inward-facing anchor.

## Appearance

Chart style owns the track, ticks, and date labels. The accepted presentation
colour is amber orange `#FFB000`, selected for strong projection contrast
against the atlas presentation blue. The path is a solid 1.2-point line; ticks
use 1.0 point; labels use 9-point type. These values have no scientific
meaning.

## Scientific and visual evidence

The installed-DE440 numerical authority remains the accepted 49I.2D.1
validation: maximum direct-Skyfield residuals were `4.293e-10` degree in
right ascension and `8.471e-11` degree in declination.

Fernando reviewed PNG and semantic SVG regional charts for La Ligua beginning
at `2026-08-30T00:00:00Z`. The eight-week case exercised the Venus
retrograde loop. A doubled sixteen-week stress test exercised the loop,
crowded labels, the following direct branch, and a wider range of tick
orientations. Fernando judged the result excellent and accepted it on
2026-08-31, while noting the expected residual clutter when both fixed
perpendicular positions are crowded.

## Verification

Mac verification passed:

- 4 package-boundary and coordinate-anchor regressions in 1.83 seconds;
- 127 focused track, style, request, and command tests in 3.09 seconds;
- 1,924 routine tests with 30 deselected in 27.29 seconds; and
- all 1,955 tests in 92.40 seconds.

The coordinate-system guide was reviewed. The milestone changes no scientific
frame, origin, observation-time, equinox, or provider meaning; it documents
the accepted fixed-frame track as a visible regional/binocular product.

## Non-goals

49I.2D.2 adds no physical apparent disk, angular diameter, illuminated limb,
phase, orientation, magnitude-scaled planetary symbol, Moon track, additional
planet descriptor, planisphere/all-sky track, adaptive sampling, spline,
provider batching, or second rendering/export pipeline.
