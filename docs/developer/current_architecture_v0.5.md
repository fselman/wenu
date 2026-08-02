# Wenu current architecture v0.5

**Status:** Implemented baseline for the v0.6 migration
**Baseline commit:** `33cd5aa`
**Date:** 2026-08-02

## 1. Purpose

This document records the repository as it exists after completion of the
v0.5 architecture migration and warning-hygiene maintenance. It is descriptive
rather than aspirational. `target_architecture_v0.6.md` defines the next
target, and `wenu_migration_0.5_to_0.6.md` defines the migration sequence.

Wenu produces accurate, reproducible, publication-quality static sky charts.
It is not an interactive planetarium.

## 2. Implemented canonical flow

All chart types, styles, and modes share one execution path:

```text
catalogues and sky layers
    -> spherical geometry
    -> projection-domain guard
    -> projection
    -> projected geometry
    -> chart preparation
    -> render-local layer options
    -> CelestialSphere.draw_chart()
    -> Matplotlib renderer
    -> legends
    -> one final export
```

The canonical low-level execution core remains
`CelestialSphere.draw_chart()`. `chart.export()` coordinates the high-level
composition, rendering, legends, and saving without introducing a second
pipeline.

## 3. Independent chart concerns

The implemented `ChartComposition` separates:

- chart context: projection-neutral dimensions, viewport, tangent point, and
  boundary kind;
- chart style: atlas, cartoon, or a concrete style object;
- output mode: print/paper or presentation;
- detail policy: astronomical selection and density;
- legend policy: object, stellar-magnitude, and contextual legends.

Styles and modes do not change chart geometry. Detail application returns
render-local options and does not leak catalogue selection into later exports.

## 4. Chart types

The public chart types are:

- `RegionalChart`;
- `FullSkyChart`, used for planispheres and observer-dependent full-sky
  products;
- `CircumpolarChart`;
- `BinocularChart`.

Chart types own projection, framing, viewport, final boundary, and
projection-domain requirements. They do not own atlas or cartoon appearance.

`RegionalChart` already supports an optional
`outside_mask_constellations=(...)`. The mask dims the area outside the union
of selected IAU constellation regions. A single constellation and a group are
both supported; Serpens expands to its two official regions.

## 5. Styles, modes, and detail

Named styles:

- `style="atlas"`;
- `style="cartoon"`.

Named modes:

- `mode="print"`, with `paper` as an alias;
- `mode="presentation"`.

The atlas print appearance is the accepted detailed baseline. Presentation
modes adapt palette, figure size, DPI, fonts, lines, and symbols without
changing geometry. Cartoon is a normal style of the canonical pipeline, not a
separate chart system.

Implemented detail policies include fixed, adaptive, and cartoon policies.
Cartoon detail preserves constellation-vertex stars and can include additional
bright stars independently of the visual style.

## 6. Legends and current chart furniture

`LegendOptions` controls:

- canonical deep-sky object symbols;
- stellar magnitude-to-symbol-size entries;
- chart-center and coordinate-system context;
- observer, location, date, and local time where relevant.

Legend content is derived from enabled layers and rendered geometry. Export
draws legends before saving once.

The stellar legend currently records:

- visible brightest and faintest magnitudes;
- effective limiting magnitude;
- total visible-star count;
- integer magnitude entries and symbol areas.

It does not yet expose cumulative visible-star counts for each magnitude
entry.

Wenu does not yet have a canonical figure-footer contract for application
name/version or copyright text.

## 7. Coordinate references and points

The sky supports equatorial, ecliptic, and Galactic coordinate grids.
Ecliptic and Galactic grid layers can include their reference planes using
`include_ecliptic=True` and `include_plane=True`.

General grid labeling exists, but reference-plane labels are not independently
controlled. Enabling all grid labels may label ordinary coordinate curves and
may expose internal reference-curve names. There is no canonical semantic
"Ecliptic" or "Galactic plane" annotation policy.

`CelestialPoints` can add:

- north and south celestial poles;
- north and south ecliptic poles;
- north and south Galactic poles;
- ecliptic cardinal points;
- Galactic center and anticenter;
- arbitrary equatorial, ecliptic, and Galactic points.

The equatorial-pole default marker is `+`; ecliptic and Galactic pole defaults
are `x`. Their symbols, colors, labels, and mode adaptation are not yet
resolved through one semantic pole style.

## 8. Examples audit

The `examples/` directory currently contains 23 scripts. They mix four roles:

1. current user-facing chart examples;
2. historical milestone demonstrations;
3. component-level visual diagnostics;
4. modules imported directly by regression tests.

Current scripts closest to the requested user examples are:

- `la_ligua_planisphere.py`;
- `atlas_style.py`;
- `atlas_summer_triangle.py`;
- `circumpolar_atlas.py`;
- `cartoon_modes.py`;
- `cen_a_binocular.py`.

The first five use or approach canonical composition. The Centaurus A
binocular script still creates and clips some Matplotlib artists directly and
saves outside the composed-export workflow.

There is no canonical single-constellation example. Styles and modes are
currently demonstrated across separate scripts rather than through one
uniform command-line contract.

Several tests import diagnostic examples directly, including legend symbols,
stellar magnitude legends, galaxy regions, and the binocular example. These
tests prevent immediate deletion of those scripts. Their fixtures and visual
contracts must move into tests or stable package APIs before cleanup.

Historical scripts such as `milestone5_regional_charts.py` and
`milestone16_regional_charts.py` no longer belong in the final user-facing
examples directory.

## 9. Documentation and generated assets

The README describes canonical v0.5 composition but does not yet contain a
chart image generated by a stable reference example. There is no structured
user guide for the requested chart families.

Generated charts normally remain below `output/` and outside version control.
No implemented provenance contract currently connects a checked-in README
image to the exact script and arguments that generated it.

## 10. Compatibility and warning policy

The legacy `cartoon_output_mode()` and `compose_cartoon_chart()` wrappers remain
functional and emit documented `DeprecationWarning`s. Canonical examples do
not use them.

The test suite disables the unused external `pytest-remotedata` plugin, treats
`FutureWarning` as an error, and explicitly captures intentional Wenu
deprecation warnings. At the v0.5 baseline, 760 tests pass without a warning
summary.

## 11. Architectural constraints retained for v0.6

- no second sky, projection, clipping, rendering, legend, or export pipeline;
- no style-dependent chart geometry;
- no mode-dependent astronomical selection;
- no catalogue queries from legend or footer rendering;
- no Matplotlib dependency in geometry, sky, or semantic chart policy;
- no clipping, catalogue joins, legend assembly, or repeated final saving in
  ordinary examples;
- no deletion of an example until equivalent test and user coverage exists.
