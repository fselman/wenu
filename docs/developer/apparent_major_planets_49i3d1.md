# Apparent major-planet symbolic points — Milestone 49I.3D.1

**Status:** Implementation proposed; installed-DE440 and visual acceptance pending

**Implementation date:** 2026-09-01

## Purpose

Expose every non-Earth major planet on ordinary observer-bound charts through
the same apparent symbolic-point machinery already accepted for Venus. The
public `--planet` selector may be repeated for Mercury, Venus, Mars, Jupiter,
Saturn, Uranus, and Neptune. Earth is not a drawable apparent target because
it is the observer body.

This slice adds catalog data, not planet-specific layers. Every planet uses
`SolarSystemPointLayer`, the shared astrometric/apparent correction chain, one
product-frame transformation, ordinary projection and clipping, the common
symbolic-planet style, semantic identity, renderer, and PNG/PDF/SVG exporters.

## Provider and physical identities

DE440s supplies Mercury and Venus through physical targets `199` and `299`.
It supplies the other major planets through barycentre targets: Mars `4`,
Jupiter `5`, Saturn `6`, Uranus `7`, and Neptune `8`. Catalog metadata retains
the corresponding physical planet IDs `499`, `599`, `699`, `799`, and `899`
separately. A chart point therefore records an honest provider target without
claiming that a barycentre identifier is the physical body identifier.

The barycentre directions are accepted here only as symbolic chart positions.
Resolved disks, surface orientation, rings, photometry, tracks, and observed
disk sequences require separate capabilities and validation.

## Shared multiple-selection behavior

One request-level `solar_system_objects` selection contains every requested
body. Each registered generic point layer now accepts that shared set when its
own selection key is present. This removes a latent one-body restriction; it
does not create multi-body astronomical or rendering control flow.

## Evidence

`tests/test_apparent_major_planets.py` proves catalog identity, CLI choices,
Earth exclusion, provider/physical-ID separation, generic layer installation,
shared style, and stable semantic roots under
`sky/solar_system/planets/<planet>`. Existing Venus, Moon, point-layer,
maximal-sphere, and moving-body contracts remain authoritative.

`tools/validate_49i3d1_apparent_major_planets.py` requires the installed DE440
kernel and refuses downloads. For every planet it compares Wenu's apparent
ICRS direction with an independent direct-Skyfield observation, prints the
physical and actual provider identities, and applies the previously accepted
`1e-7 deg` component tolerance.

## Proposed visual calibration

The calibration repeats `--planet mercury` and the corresponding selector for
each remaining non-Earth planet.

```bash
wenu_chart all-sky \
  --observer-location "La Ligua" \
  --observer-time "2026-08-30T00:00:00Z" \
  --style atlas \
  --mode presentation \
  --language en \
  --planet mercury \
  --planet venus \
  --planet mars \
  --planet jupiter \
  --planet saturn \
  --planet uranus \
  --planet neptune \
  --output /Users/fselman/Downloads/apparent-major-planets.png
```

Visual review must confirm that every selected body appears once at the
correct sky position, no unselected planet appears, labels and symbols remain
legible, and PNG/PDF/SVG use the same projected records. Because photometry
and glyph policy remain 49I.3D work, this slice intentionally preserves the
same provisional hollow marker and style used by Venus.
