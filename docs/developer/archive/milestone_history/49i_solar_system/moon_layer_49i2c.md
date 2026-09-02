# Milestone 49I.2C — First drawable Moon point

**Status:** Scientifically, architecturally, and visually accepted by Fernando
on 2026-08-30; ready for integration.  
**Implementation baseline:** `0416474`  
**Date:** 2026-08-30

## Boundary

49I.2C installs the first production Moon chart content as an opt-in symbolic
point. It reuses the accepted `SolarSystemPointLayer` orchestration and the
49I.2A Moon direction policy. The canonical path remains state source,
reception-time observer state, one astrometric light-time solution, explicit
apparent correction, stable point identity, exactly one transformation into the
product frame, ordinary projection, preparation, rendering, and shared export.

`MoonLayer` is a thin specialization configured by frozen `MOON_POINT` body
data. It owns no kernel, observer, projection, visibility test, renderer, or
exporter.

## One internal Solar-System selection

The public CLI remains class-aware:

- `--planet venus` selects Venus;
- `--moon` selects the Moon.

Both adapt into one request-owned
`SkyContentSelection.solar_system_objects` set. This replaces the
planet-only internal field without calling the Moon a planet. Detail
application maps both default-off layers through the same selection family,
and the maximal sphere registers both once for every chart family.

## Identity and appearance

The Moon's stable semantic path is
`sky/solar_system/natural_satellites/moon`. Its entity key is `moon`, display
name is `Moon`, and SVG metadata retains the accepted ephemeris provenance.

The first appearance is one style-owned hollow circular marker and optional
label. Marker size is symbolic and does not represent lunar angular diameter.
Projection-domain guards, viewport culling, masks, and chart boundaries retain
visibility ownership.

## Verification

Fernando's Mac passed:

- 89 direct Moon, shared-point, Venus, CLI, maximal-sphere, and semantic tests
  in 8.03 seconds;
- 219 request, detail, style, realization, configuration, and output-path tests
  in 4.05 seconds;
- 1,887 routine tests with 30 deselected in 25.82 seconds; and
- all 1,917 tests in 92.36 seconds; and
- 54 current-documentation tests in 1.91 seconds.

An installed-DE440 La Ligua regional request used
`2026-08-30T00:00:00Z`, equivalent to 2026-08-29 20:00 local time at UTC-4.
PNG, PDF, and semantic SVG looked the same. The SVG contained
`sky/solar_system/natural_satellites/moon` and display name `Moon`. Fernando
reported that the Moon lay approximately at the proper place and then compared
the correctly matched local instant with Stellarium; the relative position
against nearby Pisces stars corresponded closely.

## Scientific, architectural, and visual acceptance

Fernando accepted the shared internal Solar-System selection, thin Moon
specialization, natural-satellite semantics, provisional hollow marker,
PNG/PDF/SVG agreement, correctly time-matched Stellarium comparison, and all
stated non-goals on 2026-08-30. This acceptance authorizes integration of
49I.2C; it does not authorize physical lunar-disk or phase geometry.

## Non-goals

49I.2C adds no physical lunar disk, angular diameter, phase, illuminated
fraction, bright-limb position angle, surface detail, occultation geometry,
photometry, new projection, viewport, renderer, exporter, kernel download,
second observer, or second light-time solution. These physical-body contracts
remain 49I.3.
