# Wenu migration roadmap

**Version:** 0.4  
**Date:** 2026-07-26  
**Status:** Draft  
**Target architecture:** `target_architecture_v0.4.md`  
**Implementation baseline:** commit `8c8abeb`

## 1. Purpose

This document defines the execution order for migrating Wenu from its current
post-Milestone-16 structure to the package organization and completed chart
architecture described in `target_architecture_v0.4.md`.

The target architecture answers:

- what the architectural components are;
- which responsibilities they own;
- which dependency directions are permitted;
- what the final package structure should be.

This migration plan answers:

- in what order the changes should be made;
- what belongs in each milestone;
- how each milestone is validated;
- when the migration is complete.

It intentionally does not repeat the full architectural rationale.

## 2. Migration principles

### 2.1 Clean break

There are no external users requiring compatibility with the current internal
module paths.

The migration will therefore:

- move modules directly to their final locations;
- update all internal imports immediately;
- update tests and examples in the same milestone;
- preserve intentional imports from the top-level `wenu` package;
- provide no forwarding modules for old internal paths;
- provide no deprecation shims for the old directory structure.

### 2.2 Structural changes before new behavior

The package reorganization must not be mixed with unrelated functional
changes.

During the structural milestones:

- public behavior remains unchanged;
- numerical algorithms remain unchanged;
- default styles remain unchanged;
- chart output remains visually equivalent;
- tests are moved or updated only as required by the new imports and package
  boundaries.

The new full-sky chart specification is implemented only after the package
reorganization is complete.

### 2.3 Small, recoverable milestones

Each milestone:

- has one principal responsibility;
- leaves the repository in a working state;
- runs the complete automated test suite;
- is committed and pushed separately;
- does not begin until the preceding milestone passes.

### 2.4 Source of truth

During migration:

1. `target_architecture_v0.4.md` defines the intended boundaries.
2. The tests define preserved behavior.
3. Existing visual examples define graphical regression expectations.
4. This plan defines execution order.

If the migration reveals a conflict in the target design, the target
architecture is discussed and amended before implementing an undocumented
exception.

## 3. Baseline

The migration begins from commit `8c8abeb` on
`feature/regional-stereographic-charts`.

The baseline contains:

- the canonical `SkyLayer` geometry pipeline;
- arbitrary tangent-point stereographic projection;
- spherical and projected geometry containers;
- generic preparation;
- `MatplotlibRenderer`;
- `CelestialSphere.draw_chart()`;
- the regional chart production API;
- `PublicationStyle`;
- dependency tests preventing legacy rendering paths;
- passing automated and visual chart tests.

Before the first structural move:

```bash
git status
pytest
python examples/milestone5_regional_charts.py
python examples/milestone16_regional_charts.py
```

Generated chart-output directories remain untracked.

## 4. Target source tree

The migration produces:

```text
src/wenu/
├── __init__.py
├── observer.py
├── coordinates.py
│
├── objects/
│   ├── __init__.py
│   ├── astronomical_object.py
│   └── stars.py
│
├── sky/
│   ├── __init__.py
│   ├── sky_layer.py
│   ├── geometrical_object.py
│   ├── celestial_sphere.py
│   ├── rendering_results.py
│   ├── celestial_points.py
│   ├── constellation_lines.py
│   ├── constellation_boundaries.py
│   ├── constellation_labels.py
│   ├── constellations.py
│   └── coordinate_grids.py
│
├── geometry/
│   ├── __init__.py
│   ├── spherical.py
│   ├── projected.py
│   ├── frame.py
│   ├── clipping.py
│   └── viewport.py
│
├── projections/
│   ├── __init__.py
│   └── stereographic.py
│
├── charts/
│   ├── __init__.py
│   ├── regional.py
│   ├── planisphere.py
│   └── styles.py
│
├── rendering/
│   ├── __init__.py
│   ├── preparation.py
│   ├── matplotlib.py
│   ├── _matplotlib_primitives.py
│   ├── _matplotlib_axes.py
│   └── layers.py
│
├── catalogs/
├── resources.py
└── data/
```

`charts/planisphere.py` is added after the structural migration. It is shown
here because it is part of the completed v0.4 target.

## 5. Milestone 17 — Documentation baseline

### Objective

Establish the v0.4 architectural documents before moving code.

### Changes

- replace the stale `current_architecture.md`;
- replace the stale `implementation_reference.md`;
- add `target_architecture_v0.4.md`;
- add this migration plan;
- retain v0.3 and the previous roadmap temporarily as historical migration
  inputs.

### Verification

- verify document links and filenames;
- verify that the current documents describe commit `8c8abeb`;
- verify that the target document distinguishes current implementation from
  future work;
- verify that no code is changed.

### Suggested commit

```text
Document current and target v0.4 architecture
```

## 6. Milestone 18 — Coordinate and geometry packages

### Objective

Create the coordinate-neutral geometry subsystem and free the `geometry` name
from the existing coordinate-conversion module.

### File moves

| Current path | Target path |
|---|---|
| `src/wenu/geometry.py` | `src/wenu/coordinates.py` |
| `src/wenu/spherical.py` | `src/wenu/geometry/spherical.py` |
| `src/wenu/projected.py` | `src/wenu/geometry/projected.py` |
| `src/wenu/spherical_frame.py` | `src/wenu/geometry/frame.py` |
| `src/wenu/clipping.py` | `src/wenu/geometry/clipping.py` |
| `src/wenu/viewport.py` | `src/wenu/geometry/viewport.py` |

Add:

```text
src/wenu/geometry/__init__.py
```

### Required updates

- update all package imports;
- update all test imports;
- update examples;
- update top-level exports in `wenu.__init__`;
- update dependency tests for `wenu.geometry`;
- update module docstrings where needed.

### Constraints

- do not alter geometry validation;
- do not alter clipping algorithms;
- do not alter spherical rotation;
- do not alter `radec_to_altaz()`;
- do not retain old forwarding modules.

### Verification

```bash
pytest
python examples/milestone5_regional_charts.py
python examples/milestone16_regional_charts.py
```

Compare representative full-sky and regional outputs with the baseline.

### Suggested commit

```text
Milestone 18: Organize geometry package
```

## 7. Milestone 19 — Projections package

### Objective

Separate map-projection implementations from geometry values and sky content.

### File moves

| Current path | Target path |
|---|---|
| `src/wenu/projection.py` | `src/wenu/projections/stereographic.py` |

Add:

```text
src/wenu/projections/__init__.py
```

### Required updates

- update imports in charts, tests, and examples;
- preserve the top-level `StereographicProjection` export;
- update dependency tests;
- ensure projection depends only on geometry and numerical libraries.

### Constraints

- do not change projection formulae;
- do not change tangent-point behavior;
- do not change `flip_ew`, radius, or position-angle semantics;
- do not add speculative projection implementations;
- do not retain `wenu.projection`.

### Verification

Run:

```bash
pytest
```

Pay particular attention to:

- projection regression tests;
- arbitrary tangent-point tests;
- spherical/projected geometry tests;
- regional chart tests.

Run both visual example programs.

### Suggested commit

```text
Milestone 19: Organize projections package
```

## 8. Milestone 20 — Charts package

### Objective

Group chart configuration and chart styles without inventing an unnecessary
base `Chart` class. Place orchestration results beside `CelestialSphere`,
which creates them.

### File moves

| Current path | Target path |
|---|---|
| `src/wenu/chart.py` | `src/wenu/sky/rendering_results.py` |
| `src/wenu/regional.py` | `src/wenu/charts/regional.py` |
| `src/wenu/styles.py` | `src/wenu/charts/styles.py` |

Add:

```text
src/wenu/charts/__init__.py
```

### Required updates

- update imports in `CelestialSphere`, tests, and examples;
- preserve intentional top-level exports;
- keep `LayerRenderingResult` and `ChartRenderingResult` independent of
  Matplotlib;
- keep `RegionalChart` immutable;
- keep style-derived options in the canonical layer-option mechanism.

### Constraints

- do not add a general `Chart` superclass;
- do not implement the full-sky specification yet;
- do not change regional projection or viewport calculations;
- do not change publication defaults.

### Verification

```bash
pytest
python examples/milestone16_regional_charts.py
```

Verify:

- explicit-center regional charts;
- constellation-centered charts;
- north-up charts;
- viewport-matched figure size;
- reproducible export.

### Suggested commit

```text
Milestone 20: Organize charts package
```

## 9. Milestone 21 — Rendering package

### Objective

Consolidate generic preparation and Matplotlib rendering under one package
while preserving their architectural separation.

### File moves

| Current path | Target path |
|---|---|
| `src/wenu/rendering.py` | `src/wenu/rendering/preparation.py` |
| `src/wenu/renderers/matplotlib_renderer.py` | `src/wenu/rendering/matplotlib.py` |
| `src/wenu/renderers/matplotlib.py` | `src/wenu/rendering/_matplotlib_primitives.py` |
| `src/wenu/renderers/matplotlib_axes.py` | `src/wenu/rendering/_matplotlib_axes.py` |
| `src/wenu/renderers/layers.py` | `src/wenu/rendering/layers.py` |

Add:

```text
src/wenu/rendering/__init__.py
```

Remove the now-empty:

```text
src/wenu/renderers/
```

### Required updates

- update imports in styles, charts, tests, and examples;
- preserve the top-level `MatplotlibRenderer` export;
- update dependency tests;
- retain explicit axes-patch clipping;
- retain geometry-type dispatch;
- retain common, entity, and component styling.

### Constraints

- preparation must remain backend-independent;
- `MatplotlibRenderer` must not import concrete sky layers;
- no astronomical calculation may move into rendering;
- no old `wenu.rendering` module or `wenu.renderers` compatibility package
  remains.

### Verification

```bash
pytest
python examples/milestone5_regional_charts.py
python examples/milestone16_regional_charts.py
```

Inspect:

- star symbol sizes;
- label placement;
- grid extent;
- curve and text viewport clipping;
- boundary closure;
- figure background and aspect ratio.

### Suggested commit

```text
Milestone 21: Consolidate rendering package
```

## 10. Milestone 22 — Structural boundary audit

### Objective

Verify that the reorganized source tree expresses and enforces the target
dependency directions.

### Changes

- expand dependency tests for the new packages;
- search for obsolete import paths;
- search for direct layer drawing or projection methods;
- verify that no forwarding or compatibility modules remain;
- verify top-level public exports;
- update package-level docstrings and `__all__` declarations.

### Required checks

No source or test file may import:

```text
wenu.spherical
wenu.projected
wenu.spherical_frame
wenu.clipping
wenu.viewport
wenu.projection
wenu.chart
wenu.regional
wenu.styles
wenu.renderers
```

The dependency tests must enforce:

- geometry independence;
- sky/object independence from projection and rendering;
- projection independence from sky and objects;
- rendering independence from concrete astronomical layers;
- chart orchestration through the canonical pipeline.

### Verification

```bash
pytest
```

Run repository-wide searches for old paths and manually inspect any result
that appears in documentation or generated files.

### Suggested commit

```text
Milestone 22: Enforce v0.4 package boundaries
```

## 11. Milestone 23 — First-class full-sky chart specification

### Objective

Complete the remaining functional target by introducing a public full-sky or
planisphere chart specification that uses the same pipeline as
`RegionalChart`.

### Design checkpoint

Before implementation, inspect the current full-sky example and identify:

- projection configuration;
- horizon or circular mask;
- viewport construction;
- east-west orientation;
- observer-time behavior;
- full-sky label defaults;
- figure sizing;
- style and export requirements.

Choose the public name from the actual semantics:

- `FullSkyChart` for a general full-sky chart;
- `PlanisphereChart` if the object specifically represents planisphere
  conventions.

Do not add both unless they represent genuinely distinct behavior.

### Target file

```text
src/wenu/charts/planisphere.py
```

The filename may be adjusted if `FullSkyChart` is selected as the more
accurate public abstraction.

### Required behavior

The new specification must:

- configure an existing projection;
- construct a viewport or circular chart patch;
- delegate all sky content to `CelestialSphere.draw_chart()`;
- use structured layer options;
- reuse generic preparation;
- use `MatplotlibRenderer`;
- support reproducible figure sizing and export;
- reproduce the established full-sky example without specialized layer
  drawing.

### Constraints

- no duplicate pipeline;
- no layer-specific draw methods;
- no astronomy in the renderer;
- no premature common `Chart` base class;
- no migration of functional behavior back into the example.

### Verification

Add focused tests for:

- projection and viewport configuration;
- horizon/circular clipping;
- full-sky layer orchestration;
- style application;
- figure size;
- export;
- result records.

Then run:

```bash
pytest
python examples/milestone5_regional_charts.py
python examples/milestone16_regional_charts.py
```

Replace or supplement the milestone-numbered full-sky example with a stable
public API example.

### Suggested commit

```text
Milestone 23: Add full-sky chart production API
```

## 12. Milestone 24 — Documentation and migration closure

### Objective

Make the reorganized implementation and completed v0.4 architecture the only
active developer guidance.

### Changes

- update `current_architecture.md` to the final source tree;
- update `implementation_reference.md` with the final import paths and
  full-sky API;
- mark `target_architecture_v0.4.md` as implemented or accepted;
- update the README public examples;
- update all example imports;
- remove or archive superseded active documents:
  - `target_architecture_v0.3.md`;
  - `wenu_migration_roadmap_v1.0.md`;
- retain this plan as the historical implementation record, marked complete.

### Verification

- follow the README examples in a clean environment;
- confirm all documented imports exist;
- confirm no document recommends an obsolete module path;
- run the full automated suite;
- regenerate full-sky and regional charts;
- inspect repository status and exclude generated output.

### Suggested commit

```text
Milestone 24: Complete v0.4 architecture migration
```

## 13. Validation matrix

Every milestone runs the full test suite. The following checks receive
additional attention at the indicated stages:

| Contract | M18 | M19 | M20 | M21 | M22 | M23 | M24 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Geometry containers | ✓ | ✓ |  |  | ✓ |  | ✓ |
| Projection regression | ✓ | ✓ |  |  | ✓ | ✓ | ✓ |
| Layer geometry | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Regional API | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Matplotlib rendering | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Dependency rules | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Full-sky public API |  |  |  |  |  | ✓ | ✓ |
| Full-sky visual output | ✓ | ✓ |  | ✓ |  | ✓ | ✓ |
| Regional visual output | ✓ | ✓ | ✓ | ✓ |  | ✓ | ✓ |
| Documentation/imports |  |  |  |  | ✓ |  | ✓ |

## 14. Visual acceptance criteria

The migration is not accepted on automated tests alone.

Representative charts must confirm:

- star positions are unchanged;
- star marker sizes are unchanged at a fixed physical figure size;
- constellation figures remain connected correctly;
- boundaries remain closed without spurious polar segments;
- constellation labels remain correctly selected and positioned;
- coordinate grids fill the intended viewport;
- curves terminate at the chart patch;
- north-up orientation remains correct;
- full-sky key points remain present;
- regional figure aspect ratios remain correct;
- no large unintended white canvas surrounds an exported chart.

Raster DPI may change output pixel dimensions but must not change physical
marker or text sizing.

## 15. Commit and repository policy

For every milestone:

1. begin with a clean or understood working tree;
2. exclude generated chart-output directories;
3. inspect `git diff --stat`;
4. inspect moved and deleted files;
5. run the required tests and examples;
6. stage only milestone files;
7. commit with a milestone-specific message;
8. push before beginning the next milestone.

If a structural change causes a functional regression, fix the regression
within that milestone before committing. Do not proceed with a known failing
intermediate architecture.

## 16. Completion definition

The v0.4 migration is complete when:

- Milestones 17 through 24 are committed and pushed;
- the target source tree is in place;
- obsolete internal module paths have been removed;
- dependency tests enforce the new boundaries;
- regional charts use the reorganized canonical pipeline;
- a first-class full-sky or planisphere API uses the same pipeline;
- full automated tests pass;
- full-sky and regional visual tests pass;
- active documentation matches the implementation;
- generated output remains outside version control.

At that point `target_architecture_v0.4.md` describes the implemented
architecture rather than a future destination.
