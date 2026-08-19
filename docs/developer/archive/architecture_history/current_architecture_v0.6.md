# Wenu current architecture v0.6

**Status:** Implemented baseline for the v0.7 migration
**Baseline commit:** `054d0c0`
**Date:** 2026-08-04
**Target:** `target_architecture_v0.7.md`
**Migration plan:** `wenu_migration_0.6_to_0.7.md`

## 1. Purpose

This document records Wenu as implemented after completion of v0.6 and the
addition of the installed-example command. It is descriptive, not
aspirational. The v0.7 target and roadmap define the proposed changes.

Wenu remains a Python library for accurate, reproducible,
publication-quality static sky charts. It is not an interactive planetarium.

## 2. Canonical architecture

All chart families retain one execution path:

```text
chart request
    -> ChartComposition
    -> render-local detail and layer options
    -> CelestialSphere.draw_chart()
    -> renderer
    -> canonical chart furniture
    -> one export
```

Chart type owns geometry, style owns appearance, output mode adapts the
medium, detail owns astronomical selection and density, and chart furniture
owns legends, references, poles, and credits. No example owns projection,
clipping, renderer dispatch, legend assembly, or final saving.

## 3. Canonical examples and installed copies

The five user examples are:

- `planisphere.py`;
- `regional_constellation_group.py`;
- `regional_constellation.py`;
- `circumpolar.py`;
- `binocular_object.py`.

The `wenu_examples` command installs packaged copies from
`wenu.example_scripts` into `wenu_examples/`. A contract test requires every
packaged copy to remain byte-for-byte identical to its canonical source.

## 4. Implemented coordinate-grid model

Wenu implements `EquatorialGrid`, `EclipticGrid`, and `GalacticGrid`. Each is
a separate registered sky-layer object and carries a distinct
`coordinate_system` value. All three nevertheless share the low-level
`layer_name = "coordinates_grid"`.

The style layer already resolves line appearance from `coordinate_system`.
The detail layer does not: it translates every grid to the single semantic
name `coordinate_grids`. Resolved detail options are also accumulated by the
shared registered name. Consequently, detail and command-line controls cannot
independently enable multiple registered grid systems.

Canonical examples currently register only an equatorial grid. The
`sgr-sco-oph-ser` regional product additionally enables that grid and its
labels implicitly.

## 5. Implemented shared content controls

The canonical command line includes generic `--coordinate-grid` and
`--coordinate-grid-labels` switches. Labels imply the generic grid. These
switches do not identify a coordinate system.

Constellation labels and boundaries are opt-in, but constellation lines are
enabled by the resolved atlas and cartoon detail defaults. Generic coordinate
grids are not consistently removed from atlas detail when their switch is
omitted. Therefore the current interface does not yet satisfy a strict
all-reference-content-is-opt-in contract.

Reference-plane furniture and pole furniture are already opt-in. The
ecliptic and Galactic planes are selected by `--references`; poles and their
labels are independently selected.

## 6. Grid and reference-label appearance

Grid style already distinguishes equatorial, ecliptic, and Galactic lines,
but one global coordinate-label color may replace the system line color.
There is no system-specific command-line label selection.

Reference-plane labels use boundary-aware visible-curve anchors. An anchor
contains only projected `x` and `y`; it does not carry the local projected
curve tangent. Matplotlib therefore writes `Ecliptic` and `Galactic plane`
horizontally rather than parallel to the curve at the selected point.

## 7. Circular planisphere composition

Circular exports deliberately leave the canvas outside their boundary
transparent. `BinocularChart` paints an opaque, style-colored interior before
installing its transparent-face clip boundary. `FullSkyChart` installs the
boundary but does not paint the equivalent interior, so a planisphere may be
transparent inside its horizon as well as outside it.

The default planisphere legend plan places object and stellar legends at the
upper-right and lower-right axes corners. Those are rectangular-chart
placements and sufficiently large legends overlap the circular sky.

## 8. Validation baseline

At commit `054d0c0`, the installed-example focused tests passed and the full
suite reported 924 passing tests. The working tree was clean after push.

## 9. Constraints retained for v0.7

- retain `CelestialSphere.draw_chart()` as the execution core;
- do not add a second grid, reference, legend, circular-background, or export
  pipeline;
- keep grid selection in render-local content/detail policy;
- keep grid and label appearance in style;
- keep examples declarative;
- preserve atlas-print scientific content except where the v0.7 opt-in
  contract explicitly changes defaults;
- require visual approval for every changed canonical product.
