# Apparent major-planet symbolic points — Milestone 49I.3D.1

**Status:** DE440 validation passed; compact-glyph visual acceptance pending

**Implementation date:** 2026-09-01

## Purpose

Expose every non-Earth major planet on ordinary observer-bound charts through
the same apparent symbolic-point machinery already accepted for Venus. The
public `--planet` selector accepts a comma-separated list of Mercury, Venus,
Mars, Jupiter, Saturn, Uranus, and Neptune; the option may still be repeated.
Earth is not a drawable apparent target because it is the observer body. The
same selector and request path apply to all-sky, planisphere, regional,
circumpolar, and binocular products.

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

## Symbol and presentation policy

Each catalog descriptor owns its conventional astronomical symbol: `☿`, `♀`,
`♂`, `♃`, `♄`, `♅`, and `♆`. Visual labels use these glyphs while semantic
names and exported identity remain the full localized planet names. All
symbolic planets share the Venus point style. Its marker diameter is one half
of the earlier provisional size (Matplotlib area `42.0` to `10.5`), and atlas
presentation mode uses the accepted Venus cream `#FFE6A3` for both marker and
glyph.

## Visual calibration

The preferred compact syntax is
`--planet mercury,venus,mars,jupiter,saturn,uranus,neptune`.

The first all-sky and planisphere calibrations also exposed a request-overlay
error. A CLI planet selection replaced the complete resolved
`SkyContentSelection`, resetting unrelated fields such as
`milky_way_levels` to `None`. Request overlays now replace only explicitly
supplied fields, so selecting planets preserves the resolved Milky Way levels
and other unrelated sky content. Direct comparison with the source geometry
confirmed that the two principal `ol1` rings belong to the source geometry,
not a viewport edge or an artificial closing segment. Comparative renders of
each lowest level then established that only `ol1` produces the unnatural
broad envelope. Governed defaults therefore begin at `ol2`; `ol1` remains
explicitly selectable for inspection or specialized use.

For visual diagnosis and ordinary chart control, every chart family accepts
`--mw-contour OL1[,OL2,...]|all`. A comma-separated numbered selection
replaces the governed default contour set with exactly those levels; `all`
draws all five.
Comparing otherwise identical `OL1` and `OL2`
renders therefore compares the two source isophotes directly without changing
the projection, viewport, or planet selection.
Each level is packaged as its own single-feature GeoJSON file. An explicit
selection sends only the chosen file's rings into the coordinate and
projection pipeline, while the original combined D3-Celestial snapshot is
retained unchanged as provenance authority.

```bash
wenu_chart all-sky \
  --observer-location "La Ligua" \
  --observer-time "2026-08-30T00:00:00Z" \
  --style atlas \
  --mode presentation \
  --language en \
  --planet mercury,venus,mars,jupiter,saturn,uranus,neptune \
  --output /Users/fselman/Downloads/apparent-major-planets.png
```

Visual review must confirm that every selected body appears once at the
correct sky position, no unselected planet appears, labels and symbols remain
legible, and PNG/PDF/SVG use the same projected records. A corresponding
`planisphere` render must confirm identical catalog selection and styling on
both faces.
