# Wenu target architecture v0.7

**Status:** Implemented
**Completed:** 2026-08-04
**Implementation baseline:** `61fc73e`
**Source architecture:** `current_architecture_v0.6.md`
**Migration plan:** `wenu_migration_0.6_to_0.7.md`

## 1. Purpose

Version 0.7 makes constellation structure, coordinate grids, celestial
references, poles, and legends explicit chart requests. It also gives the
three coordinate-grid systems independent controls, aligns semantic
reference-plane labels with their curves, and completes circular planisphere
composition.

The target extends the v0.6 pipeline. It does not replace chart composition,
sky-layer geometry, projection, preparation, rendering, furniture, legends,
or export.

## 2. Independent grid identity

The three semantic detail names are:

```text
equatorial_grid
ecliptic_grid
galactic_grid
```

They resolve from the registered layer object's `coordinate_system`, not only
from its shared `layer_name`. Render-local grid enablement uses layer-object
identity so several `coordinates_grid` layers cannot overwrite one another.

Changing the low-level grid `layer_name` is not required. Existing style,
rendering, and compatibility behavior may continue to recognize
`coordinates_grid` while detail policy uses system-specific semantic names.

## 3. Canonical content switches

Every canonical example exposes:

```text
--constellation-lines
--constellation-labels
--constellation-boundaries

--equatorial-grid
--equatorial-grid-labels
--ecliptic-grid
--ecliptic-grid-labels
--galactic-grid
--galactic-grid-labels

--grid-references SELECTION
--poles
--pole-labels
```

The ambiguous `--coordinate-grid` and `--coordinate-grid-labels` controls are
replaced. A system's label switch enables that system's grid. It does not
enable another grid.

Constellation lines, labels, and boundaries remain independent. A label or
boundary request does not silently enable line figures.

With no content or furniture switches, constellation structure, all three
coordinate grids and their labels, ecliptic and Galactic reference planes,
poles, pole labels, and legends are off. The chart-owned horizon or field
boundary is not reference content and remains visible.

## 4. Grid-label selection and appearance ownership

Grid and label visibility are render-local content/detail decisions. Grid
line and label colors, widths, fonts, opacity, and line styles are style
decisions. Output modes may adapt appearance for legibility without changing
which systems are enabled.

The semantic default colors for both grid lines and the labels belonging to
that grid are:

| Grid system | Line default | Label default |
|---|---|---|
| Equatorial | black | black |
| Ecliptic | orange | orange |
| Galactic | blue | blue |

Named presentation or cartoon modes may adapt these defaults only where
necessary for contrast, while retaining an unambiguous visual distinction
between the three coordinate systems. Explicit caller color overrides retain
precedence over mode adaptation.

System-specific label visibility is not represented by one global
`draw_coordinate_labels` style flag. Resolved detail carries the selected
label systems, and detail application adds `draw_labels` to the render-local
options of each corresponding grid object.

## 5. Example grid configuration

Canonical examples register equatorial, ecliptic, and Galactic grid layers
when those layers are meaningful for the chart family. The examples configure
sampling and meridian/parallel intervals but do not draw a grid unless its
switch requests it.

Grid layers do not include their principal reference planes merely because a
grid is enabled:

```text
EquatorialGrid.include_equator = False
EclipticGrid.include_ecliptic = False
GalacticGrid.include_plane = False
```

The celestial equator, ecliptic, and Galactic plane remain canonical chart
furniture selected by comma-separated `--grid-references` values or `all`.
This avoids duplicate lines and keeps semantic reference labels independent
from numeric grid labels.

No named example product, including `sgr-sco-oph-ser`, silently enables a
grid or grid labels. A regression product must pass the system-specific
switches explicitly.

## 6. Tangent-aligned semantic reference labels

The semantic labels `Ecliptic` and `Galactic plane` are placed on visible,
prepared reference curves and rotated parallel to the local projected curve
tangent. The selected text orientation is normalized to remain readable
rather than appearing upside down.

The generic projected-curve label-placement contract carries position and an
optional tangent rotation. Rendering remains astronomy-neutral; it does not
contain ecliptic or Galactic semantics. Reference furniture computes the
placement from neighboring finite projected samples.

Numeric grid labels remain independently controlled and are not required to
adopt tangent rotation in this migration.

## 7. Circular planisphere composition

Every circular chart follows one background contract:

- the exported canvas outside the final circle is transparent;
- the interior is opaque and painted with the resolved style sky color;
- the final circle has a visible style-owned edge;
- all sky artists remain clipped to the chart-owned boundary.

`FullSkyChart` uses the same renderer-level circular-background operation
already used by `BinocularChart`. The example does not draw a patch or alter
clip paths.

The default planisphere legend policy keeps legends clear of the circular sky,
using geometry-appropriate outside placements included by tight export. An
example may select legends but does not position them manually.

## 8. Compatibility and examples

The five canonical families and their style/mode axes remain unchanged.
Examples continue through `add_chart_arguments()`, `chart_detail_overrides()`,
`compose_chart()`, chart export, and `CelestialSphere.draw_chart()`.

When a canonical example changes, its packaged `wenu.example_scripts` copy is
regenerated and the byte-equality contract remains mandatory.

The old generic grid switches are removed as an explicit pre-release CLI
correction because their meaning is ambiguous with several registered grid
systems. Internal compatibility APIs that do not prevent independent
selection may remain documented during migration.

The vague product switch `--all` is likewise replaced by `--all-products`.

## 9. Validation matrix

At minimum, automated tests cover:

- every grid independently enabled and disabled in a sky containing all three;
- each `*-grid-labels` switch enabling only its own grid and labels;
- all reference and constellation content off by default;
- semantic default line and label colors;
- tangent-aligned ecliptic and Galactic-plane labels;
- opaque planisphere interior and transparent exterior;
- planisphere legends outside the circle;
- no render-local state leaking between sequential products;
- packaged examples identical to canonical examples.

Visual approval covers every changed atlas/cartoon and print/presentation
product, with atlas print retained as the scientific reference product under
the new explicit-content request.

## 10. Completion criteria

Version 0.7 is complete when:

1. grid detail identity is system-specific and collision-free;
2. the six system-specific grid switches replace the two generic switches;
3. constellation structure and all reference content are opt-in;
4. grid labels can be selected independently by coordinate system;
5. default line and label colors follow the semantic color table;
6. canonical examples configure all supported selectable grids declaratively;
7. reference-plane labels follow their local curve tangents;
8. planisphere legends do not overlap its circle;
9. the planisphere interior is opaque and its exterior transparent;
10. focused, full, dependency, warning, and visual regressions pass;
11. implementation reference, source tree, user guide, and installed examples
    agree with the implementation.
