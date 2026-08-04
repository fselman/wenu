# Wenu migration roadmap: v0.6 to v0.7

**Status:** Proposed incremental roadmap
**Source:** `current_architecture_v0.6.md`
**Target:** `target_architecture_v0.7.md`
**Base commit:** `054d0c0`

## 1. Objective

Make coordinate grids and other celestial reference content explicitly
selectable, give each coordinate system independent grid and label controls,
align semantic reference labels with their curves, and complete planisphere
circular composition without creating a parallel pipeline.

## 2. Migration rules

- preserve `CelestialSphere.draw_chart()` as the execution core;
- keep geometry and low-level grid construction in `sky` and `geometry`;
- keep content selection in immutable, render-local chart detail;
- keep colors, widths, fonts, and line styles in chart style;
- keep chart boundary and circular footprint in the chart type;
- keep legend placement in legend policy;
- keep examples declarative and synchronized with packaged copies;
- compile, run focused and full tests, and approve affected visual products at
  every implementation milestone.

## 3. Milestone 45A — Define the v0.7 architecture and roadmap

### Goal

Record the implemented v0.6 baseline, the proposed v0.7 target, and this
migration sequence before runtime changes.

### Work

- add `current_architecture_v0.6.md`;
- add `target_architecture_v0.7.md`;
- add this roadmap;
- record shared grid-layer names and system-specific metadata;
- define opt-in constellation, grid, reference, pole, and legend behavior;
- define equatorial black, ecliptic orange, and Galactic blue as semantic
  line-and-label defaults;
- record tangent-label and circular-planisphere defects;
- update architectural authority and public developer references.

### Verification

- documents cross-reference one another and base commit `054d0c0`;
- the baseline is descriptive and the target aspirational;
- no runtime, rendering, or canonical example files change;
- documentation contract tests pass.

### Commit

```text
Milestone 45A: Define the Wenu v0.7 architecture and roadmap
```

## 4. Milestone 45B — Separate coordinate-grid detail identity

### Goal

Enable independent render-local selection of equatorial, ecliptic, and
Galactic grid objects.

### Work

- resolve grid semantic detail names from `coordinate_system`;
- introduce `equatorial_grid`, `ecliptic_grid`, and `galactic_grid`;
- prevent shared `coordinates_grid` names from overwriting resolved options;
- use layer-object identity for per-grid enablement;
- retain compatible low-level names where they do not block independence;
- update fixed, adaptive, and cartoon detail contracts.

### Tests

- one sky registers all three grid systems;
- each system can be enabled alone;
- enabling one system does not enable another;
- sequential detail applications do not leak selection;
- non-grid layer aliases remain unchanged.

### Commit

```text
Milestone 45B: Separate coordinate-grid detail identity
```

## 5. Milestone 45C — Add explicit content and grid-label controls

### Goal

Make constellation structure and each coordinate grid an independent opt-in
request.

### Work

- add `--constellation-lines`;
- replace generic grid switches with six system-specific switches;
- replace `--references` with comma-separated `--grid-references` selection;
- replace the vague `--all` product switch with `--all-products`;
- make each grid-label switch imply only its own grid;
- carry selected label systems through resolved detail;
- apply `draw_labels` through grid-object render-local options;
- suppress constellation lines, labels, boundaries, all grids, grid labels,
  references, poles, and legends unless explicitly requested;
- retain chart-owned horizons and boundaries.

### Tests

- default invocation disables every listed optional content item;
- every switch operates independently;
- labels imply only the matching grid;
- grid-label selection is not stored as a global style choice;
- cartoon constellation-star selection remains explicit and scientifically
  documented when line figures are hidden.

### Commit

```text
Milestone 45C: Make celestial reference content opt-in
```

## 6. Milestone 45D — Resolve semantic grid colors and examples

### Goal

Apply system-specific grid appearance and expose the controls consistently in
the five canonical chart families.

### Work

- set equatorial line and label defaults to black;
- set ecliptic line and label defaults to orange;
- set Galactic line and label defaults to blue;
- preserve system distinction under mode contrast adaptation;
- configure supported equatorial, ecliptic, and Galactic grids in canonical
  examples without enabling them by default;
- keep reference-plane inclusion disabled in grid layers;
- remove implicit Sgr-Sco-Oph-Ser grid and label defaults;
- synchronize every changed packaged example.

### Tests and visual acceptance

- line and label colors agree for each system;
- explicit color overrides retain precedence;
- each family parses the six grid switches;
- installed copies remain byte-identical;
- affected atlas/cartoon and print/presentation products are approved with
  explicit grid arguments.

### Commit

```text
Milestone 45D: Add semantic grid colors and canonical controls
```

## 7. Milestone 45E — Align reference labels with curve tangents

### Goal

Write `Ecliptic` and `Galactic plane` parallel to the visible projected curve
at their automatic or explicit placement.

### Work

- add an optional tangent to the generic projected-curve label placement;
- calculate a stable local tangent from neighboring finite samples;
- normalize text orientation for readability;
- apply rotation through the Matplotlib renderer without celestial semantics;
- preserve boundary-aware and legend-aware placement.

### Tests and visual acceptance

- finite tangent on clipped and disconnected curves;
- one semantic label per requested plane;
- labels remain within rectangular and circular chart footprints;
- ecliptic and Galactic labels rotate independently;
- reference state does not leak between products.

### Commit

```text
Milestone 45E: Align celestial-reference labels with curves
```

## 8. Milestone 45F — Repair circular planisphere composition

### Goal

Give planispheres the same opaque-interior, transparent-exterior contract as
other circular charts and keep legends clear of the sky circle.

### Work

- paint the `FullSkyChart` interior through the renderer circular-background
  operation;
- retain transparent export outside the final circle;
- keep the chart-owned horizon edge visible;
- give planisphere legends geometry-appropriate outside placements;
- keep all placement and background logic out of the example.

### Tests and visual acceptance

- exported corner alpha is zero and center alpha is one;
- boundary geometry is unchanged;
- object and stellar legends do not intersect the circle;
- atlas/cartoon and print/presentation planispheres are approved;
- horizon visibility is independent of optional content.

### Commit

```text
Milestone 45F: Repair planisphere circular composition
```

## 9. Milestone 45G — Documentation and v0.7 closure

### Goal

Make public and developer documentation describe the implemented v0.7
workflow and close the migration.

### Work

- update `implementation_reference.md`, `source_tree.md`, README, and user
  guide;
- document the six grid switches and color contract;
- update installed examples and example-installation documentation;
- mark the target implemented and this roadmap complete;
- record final test, warning, dependency, and visual audits.

### Verification

- documented commands execute;
- canonical and packaged examples agree;
- focused and full suites pass without unexpected warnings;
- complete affected visual matrix is approved;
- working tree is clean after closure.

### Commit

```text
Milestone 45G: Complete the Wenu v0.7 migration
```

## 10. Stop conditions

Pause and review if a change would require:

- a second grid, projection, rendering, reference, legend, or export path;
- style or mode deciding which astronomical grid is selected;
- detail policy owning colors or fonts;
- Matplotlib concepts in grid geometry or semantic content policy;
- manual patches, clipping, legend placement, or saving in examples;
- implicit enabling of unrequested reference content;
- accepting an unexplained atlas-print or circular-alpha regression.

## 11. Completion definition

The v0.6-to-v0.7 migration is complete when every target criterion is
implemented, the affected visual products are approved, all tests pass, and
the architecture documents agree with the repository.
