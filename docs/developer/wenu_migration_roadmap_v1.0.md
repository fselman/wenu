# Wenu Migration Roadmap

**Version:** 1.0  
**Date:** 2026-07-24  
**Status:** Fixed implementation roadmap  
**From:** current Wenu architecture  
**To:** `target_architecture_v0.3.md`

---

# 1. Purpose

This document defines the fixed sequence for migrating Wenu from its current implementation to the target architecture.

The priorities are:

1. reach useful regional stereographic charts rapidly;
2. preserve the working full-sky planisphere throughout the migration;
3. avoid a large preliminary rewrite;
4. introduce the target abstractions only when they are needed;
5. keep every milestone small, testable, and committable;
6. stop revising the architecture unless implementation reveals a genuine roadblock.

The target architecture is treated as frozen once this roadmap is accepted.

---

# 2. Fixed target

The implementation must converge on:

```text
Observer
    ↓
CelestialSphere
    ↓
SkyLayer
    ├── AstronomicalObject
    └── GeometricalObject
    ↓
Spherical Geometry
    ↓
Projection
    ↓
Projected Geometry
    ↓
Renderer
```

The two `SkyLayer` branches are:

```text
SkyLayer
│
├── AstronomicalObject
│   ├── Stars
│   ├── StarClusters
│   ├── Galaxies
│   ├── MilkyWay
│   ├── Nebulae
│   ├── MinorPlanets
│   ├── Comets
│   └── ...
│
└── GeometricalObject
    ├── ConstellationLines
    ├── ConstellationBoundaries
    ├── CoordinatesGrid
    ├── CelestialPoints
    └── ...
```

The geometry vocabulary is fixed as:

```text
SphericalPoints
SphericalCurves
SphericalGrid
SphericalPolygons

ProjectedPoints
ProjectedCurves
ProjectedGrid
ProjectedPolygons
```

Only collection-oriented geometry classes are used.

---

# 3. Current implementation baseline

The migration begins from a codebase that already contains much of the required mathematical and rendering infrastructure:

- `Observer`;
- `CelestialSphere`;
- `Stars`;
- `Constellations`;
- `ConstellationLines`;
- `ConstellationBoundaries`;
- `CelestialPoints`;
- equatorial, ecliptic, and galactic grid code;
- `SphericalFrame`;
- stereographic projection;
- projected point, curve, and polygon types;
- clipping and viewport support;
- Matplotlib renderer primitives;
- a working full-sky planisphere;
- a focused regression test suite.

The migration should reuse this work rather than replace it.

---

# 4. Development rules

Every milestone must satisfy the Definition of Done in `development_methodology_v0.2.md`.

In particular:

- one architectural objective per milestone;
- the repository remains runnable;
- existing behaviour is preserved unless intentionally superseded;
- focused tests pass;
- documentation is updated;
- the work is committed to Git before the next milestone begins.

Additional rule for this roadmap:

> No architecture change is permitted during implementation unless the current target cannot be implemented without contradiction, duplication, or a broken dependency direction.

Convenience issues, naming preferences, and speculative future features are not architectural roadblocks.

---

# Phase I — Regional chart capability as early as possible

The first phase produces a regional-chart MVP while changing only the minimum architecture required.

## Milestone 1 — Freeze the baseline

### Objective

Establish a clean and reproducible starting point before structural changes.

### Work

- run the complete current test suite;
- confirm the full-sky planisphere notebook or script runs;
- save one reference full-sky output;
- save one small representative constellation output if currently possible;
- record the current public imports and notebook usage;
- document known temporary architectural violations.

### Do not

- rename packages;
- introduce base classes;
- redesign APIs;
- add new features.

### Completion evidence

- all baseline tests pass;
- reference outputs are stored;
- `development_status.md` records the baseline commit.

---

## Milestone 2 — Complete collection-based geometry

### Objective

Make spherical and projected geometry use the fixed collection vocabulary.

### Implement

Spherical:

- `SphericalPoints`;
- `SphericalCurves`;
- `SphericalGrid`;
- `SphericalPolygons`.

Projected:

- `ProjectedPoints`;
- `ProjectedCurves`;
- `ProjectedGrid`;
- `ProjectedPolygons`.

### Migration strategy

- adapt existing projected point, curve, and polygon implementations rather than rewriting them;
- preserve vectorized NumPy arrays;
- retain names and metadata needed by current layers;
- represent one entity as a collection of length one;
- avoid introducing singular public geometry classes.

### Minimum metadata

Only metadata required by current code should be implemented:

- identifiers;
- labels;
- names;
- magnitudes;
- colours;
- closed/open state;
- layer-specific semantic metadata.

### Tests

- shape validation;
- matching coordinate lengths;
- empty and single-element collections where valid;
- metadata preservation;
- finite-coordinate behaviour;
- grid composition.

### Completion result

All subsequent code can communicate through the target geometry classes.

---

## Milestone 3 — Generic geometry projection

### Objective

Make `StereographicProjection` consume spherical geometry and return the corresponding projected geometry.

### Implement

```text
SphericalPoints   → ProjectedPoints
SphericalCurves   → ProjectedCurves
SphericalGrid     → ProjectedGrid
SphericalPolygons → ProjectedPolygons
```

### Preserve

- current stereographic formula;
- `flip_ew`;
- vectorized projection;
- curve segmentation;
- clipping behaviour;
- current full-sky geometry.

### Use existing work

Retain and consolidate:

- `SphericalFrame`;
- current point, curve, and polygon projection methods;
- visibility and clipping utilities;
- viewport behaviour.

### Boundary rule

Projection performs mathematics only. It must not:

- read catalogues;
- resolve HIP identifiers;
- calculate star sizes;
- render Matplotlib artists;
- know whether geometry represents stars, grids, or constellations.

### Tests

- existing projection regression tests;
- tangent point maps to the origin;
- horizon maps to the correct radius in the full-sky case;
- geometry type is preserved across projection;
- grid components remain grouped;
- metadata survives projection.

---

## Milestone 4 — Arbitrary tangent point and regional viewport

### Objective

Enable stereographic projection around an arbitrary celestial direction.

### Implement

- use `SphericalFrame` to rotate an arbitrary tangent point to the projection pole;
- keep spherical rotation separate from stereographic projection;
- support position angle around the tangent point;
- support a regional projected viewport or angular radius;
- preserve the existing zenith-centered full-sky configuration.

### Initial use cases

- tangent point supplied in equatorial coordinates;
- tangent point derived from a constellation center;
- tangent point equal to the observer zenith for the planisphere.

### Deferred

Do not yet redesign the complete astronomical frame/equinox/epoch system.

Use the existing Observer, Astropy, Skyfield, and spherical-rotation paths sufficient for current charts.

### Tests

- tangent point projects exactly to chart center;
- zero position angle has a documented orientation;
- position-angle rotation behaves consistently;
- the existing zenith-centered chart is unchanged;
- viewport clipping works for regional curves and polygons.

### Completion result

The mathematical foundation for regional charts is operational.

---

## Milestone 5 — Minimal regional chart prototype

### Objective

Produce a regional stereographic chart before the full class hierarchy is migrated.

### Work

Using the current layer classes plus the new geometry/projection path, produce:

- stars;
- constellation lines;
- selected labels;
- optional boundaries;
- configurable regional center;
- configurable chart extent;
- static Matplotlib export.

### Demonstrations

Create at least:

1. a regional chart centered on one southern constellation;
2. a chart containing more than one constellation;
3. a chart whose constellation lines cross the viewport edge;
4. the existing full-sky planisphere.

### Temporary adapters

Adapters are permitted at this milestone when needed to translate current layer outputs into target geometry.

They must be:

- small;
- clearly marked temporary;
- removed during Phase II.

### Completion result

Wenu can produce useful regional charts early, before completing the entire architectural migration.

This is the first major release checkpoint.

---

# Phase II — Introduce the fixed SkyLayer hierarchy

This phase migrates the domain classes without changing the already working regional projection path.

## Milestone 6 — Introduce `SkyLayer`

### Objective

Create the common contract for every chartable layer.

### Implement

A minimal `SkyLayer` abstraction defining the capability to produce spherical geometry.

Conceptually:

```python
class SkyLayer:
    def spherical_geometry(self, observer):
        ...
```

The exact use of `ABC`, `Protocol`, or a concrete base class should be chosen for the simplest implementation consistent with the target hierarchy.

### Rules

`SkyLayer`:

- contains no projection;
- contains no renderer;
- contains no Matplotlib axes or artists;
- does not calculate viewport clipping;
- may carry semantic metadata and default layer identity.

### CelestialSphere change

`CelestialSphere.add()` should validate the `SkyLayer` contract rather than the current `draw()` method.

### Transitional support

Current layers may use adapters until migrated individually.

### Tests

- valid layers are accepted;
- invalid objects are rejected;
- layer order is preserved;
- existing add/remove/clear behaviour remains.

---

## Milestone 7 — Introduce `AstronomicalObject` and migrate `Stars`

### Objective

Create the physical-object branch and make `Stars` its first concrete implementation.

### Implement hierarchy

```text
SkyLayer
    └── AstronomicalObject
            └── Stars
```

### `AstronomicalObject`

Keep the base class minimal. Shared behaviour should be added only when demonstrated by more than one physical-object implementation.

### `Stars` responsibilities retained

- catalogue selection and loading;
- HIP identifiers;
- future Gaia identifiers;
- magnitudes;
- colours;
- source astrometric data;
- observer-dependent coordinates;
- catalogue filtering;
- HIP lookup used by constellation structures.

### Remove from `Stars`

- projection objects;
- projected x/y storage;
- Matplotlib imports;
- artists;
- viewport logic;
- marker-size calculation;
- `draw()` methods;
- any direct renderer dependency.

### Output

```text
Stars
    ↓
SphericalPoints
```

`SphericalPoints` metadata should include only what later preparation and rendering require, such as:

- catalogue identifiers;
- magnitude;
- colour;
- label candidate data.

### Tests

- catalogue regression;
- magnitude filtering;
- colour metadata;
- HIP lookup;
- observer-dependent spherical coordinates;
- no projected-state attributes;
- no renderer or Matplotlib dependency.

### Completion result

The canonical target pipeline is established:

```text
Stars
    ↓
SphericalPoints
    ↓
Projection
    ↓
ProjectedPoints
    ↓
Renderer
```

---

## Milestone 8 — Introduce `GeometricalObject`

### Objective

Create the celestial-construct branch.

### Implement hierarchy

```text
SkyLayer
    └── GeometricalObject
```

The base class remains minimal and defines no projection or rendering behaviour.

### Scope

At this milestone, introduce the base abstraction and migrate no more than one very small representative geometrical object if useful for validation.

### Tests

- correct inheritance;
- valid spherical-geometry output;
- no projection/rendering imports.

---

## Milestone 9 — Migrate `CelestialPoints`

### Objective

Make celestial reference points a `GeometricalObject`.

### Implement hierarchy

```text
SkyLayer
    └── GeometricalObject
            └── CelestialPoints
```

### Preserve

- equatorial poles;
- galactic poles;
- ecliptic poles;
- galactic center and anticenter;
- equinox and solstice/cardinal points;
- visible-pole convenience;
- custom labels and styles as metadata.

### Output

```text
CelestialPoints
    ↓
SphericalPoints
```

### Remove

- direct projection;
- `draw()` methods;
- Matplotlib artists;
- point-by-point renderer calls.

---

## Milestone 10 — Migrate `ConstellationLines`

### Objective

Make constellation stick figures a `GeometricalObject`.

### Implement hierarchy

```text
SkyLayer
    └── GeometricalObject
            └── ConstellationLines
```

### Responsibilities

- line-system identity;
- constellation abbreviation;
- HIP endpoint relationships;
- selected-constellation filtering;
- arbitrary installed line systems such as western, Mapuche, or La Ligua;
- resolution of HIP positions through `Stars`.

### Output

```text
ConstellationLines
    ↓
SphericalCurves
```

### Critical rule

`ConstellationLines` may ask `Stars` for spherical star positions. It must never read projected x/y arrays from `Stars`.

### Preserve

- custom `.fab` systems;
- Serpens handling;
- selected constellation lists;
- current line semantics.

### Tests

- endpoint resolution;
- missing HIP behaviour;
- selected-system behaviour;
- custom system loading;
- spherical-curve output;
- regional clipping after projection.

---

## Milestone 11 — Migrate `ConstellationBoundaries`

### Objective

Make IAU boundaries a `GeometricalObject`.

### Implement hierarchy

```text
SkyLayer
    └── GeometricalObject
            └── ConstellationBoundaries
```

### Output

Prefer:

```text
ConstellationBoundaries
    ↓
SphericalPolygons
```

Where the source data or topology makes polygon closure unsuitable, the implementation may internally preserve boundary segments, but the public output must remain consistent with the fixed geometry model.

### Preserve

- selected constellations;
- installed boundary resources;
- boundary metadata;
- regional clipping.

### Tests

- selection;
- closure;
- metadata;
- edge crossing;
- viewport clipping.

---

## Milestone 12 — Migrate `CoordinatesGrid`

### Objective

Create the fixed `CoordinatesGrid` geometrical layer.

### Implement hierarchy

```text
SkyLayer
    └── GeometricalObject
            └── CoordinatesGrid
```

### Responsibilities

Group:

- meridians;
- parallels;
- emphasized reference curves;
- label anchors;
- key points;
- grid identity and coordinate frame.

### Output

```text
CoordinatesGrid
    ↓
SphericalGrid
```

### First concrete grids

Migrate the existing grids without broad redesign:

- equatorial;
- ecliptic;
- galactic.

Add horizontal only when immediately needed.

### Remove

- specialized direct-drawing grid methods;
- projection calls inside grid classes;
- Matplotlib dependencies.

### Tests

- expected meridian and parallel counts;
- grid identity;
- grouping survives projection into `ProjectedGrid`;
- label-anchor metadata;
- regional and full-sky rendering.

---

# Phase III — Generic rendering and final orchestration

## Milestone 13 — Renderer consumes only projected geometry

### Objective

Complete the renderer boundary.

### Implement

A Matplotlib renderer that consumes:

- `ProjectedPoints`;
- `ProjectedCurves`;
- `ProjectedGrid`;
- `ProjectedPolygons`.

### Rendering responsibilities

- marker drawing;
- line drawing;
- polygon drawing;
- text and labels;
- z-order;
- alpha;
- line width and style;
- marker size and shape;
- axes interaction.

### Style rule

Astronomical quantities remain in layers. Graphical symbolization belongs in rendering preparation or renderer-facing style logic.

In particular:

- magnitude remains a star property;
- marker size is derived outside `Stars`;
- constellation line width is not stored as geometry;
- grid styling is separate from coordinate generation.

### Scope control

Do not introduce a large style framework unless the current renderer cannot remain clean without one.

A small collection of dataclasses or dictionaries is sufficient initially.

### Tests

- representative artists;
- style forwarding;
- point collections;
- segmented curves;
- polygons;
- grid rendering;
- non-interactive export.

---

## Milestone 14 — `CelestialSphere.draw_chart()`

### Objective

Make `CelestialSphere` the stable orchestration object defined by the target architecture.

### Implement

Conceptually:

```python
sky.draw_chart(
    projection=projection,
    renderer=renderer,
    viewport=viewport,
    ...
)
```

Its internal sequence is:

```text
for each SkyLayer
    geometry = layer.spherical_geometry(observer)
    projected = projection.project(geometry)
    renderer.draw(projected)
```

### Responsibilities

- own and order `SkyLayer` objects;
- retain the `Observer`;
- request spherical geometry;
- invoke projection;
- invoke renderer;
- apply chart-level viewport configuration;
- return the rendering result.

### Must not

- contain catalogue-specific code;
- manually project stars;
- manually render individual layer types;
- accumulate a growing family of `draw_*` astronomy methods.

### Convenience API

The existing convenience methods may remain if they create and register layers:

- `add_stars(...)`;
- `add_constellations(...)`;
- `add_boundaries(...)`;
- `add_points(...)`;
- grid helpers.

They should not draw directly.

### Tests

- mixed-layer orchestration;
- layer order;
- full-sky planisphere;
- regional chart;
- repeated rendering of one `CelestialSphere` with different projections or viewports where practical.

---

## Milestone 15 — Remove temporary and legacy paths

### Objective

Ensure the implementation actually follows the target architecture everywhere.

### Remove

- layer `draw()` methods that bypass orchestration;
- projected coordinate state inside domain objects;
- projection imports from `objects` and `sky` domain modules;
- Matplotlib imports outside renderer modules;
- temporary adapters from Milestone 5;
- duplicate projection code;
- obsolete singular geometry classes;
- obsolete `CoordinateGrid` naming;
- stale notebook-side indexing and projection logic.

### Audit

Search the repository for:

```text
.draw(
projection
Projected
matplotlib
x
y
CoordinateGrid
```

and review every occurrence in domain packages.

### Completion result

The dependency direction is real and enforceable.

---

## Milestone 16 — Regional-chart production API

### Objective

Make regional charts fast to define and suitable for sustained guidebook work.

### Implement

- tangent-point helpers;
- constellation-centered chart helpers;
- explicit position angle;
- field-of-view or angular-radius convenience;
- aspect ratio and crop control;
- label selection;
- reusable publication styles;
- reproducible export;
- concise notebook examples.

### Required demonstrations

- one full-sky southern planisphere;
- one single-constellation regional chart;
- one multi-constellation regional chart;
- one chart using a non-western constellation-line system;
- one chart with an equatorial or other `CoordinatesGrid`;
- one chart with boundaries;
- one publication-quality saved output.

### Completion result

Regional chart production is no longer an architectural experiment. It is a stable Wenu capability.

This is the second major release checkpoint.

---

# Phase IV — Complete the target object family as needed

These milestones extend the fixed architecture. They do not alter it.

They begin after regional charts are stable.

## Milestone 17 — `MilkyWay`

### Hierarchy

```text
SkyLayer
    └── AstronomicalObject
            └── MilkyWay
```

### Representations

`MilkyWay` may support one or more representations:

- contour/isophote geometry;
- raster or intensity representation;
- future physically richer representation.

The class represents the astronomical entity. Contours or imagery are representations produced for charting.

Initial implementation should use the available Mellinger or other adopted dataset and produce the simplest publication-useful output.

---

## Milestone 18 — Additional physical-object classes

Add only when required by the guide:

- `StarClusters`;
- `Galaxies`;
- `Nebulae`;
- `MinorPlanets`;
- `Comets`.

Each class:

- inherits from `AstronomicalObject`;
- contributes spherical geometry;
- contains no projection or rendering code;
- reuses catalogue infrastructure where appropriate.

Do not create empty speculative classes merely to complete the hierarchy.

---

# Phase V — Deferred astronomical generalization

This phase is intentionally postponed until regional chart production is working.

## Milestone 19 — Explicit astronomical frame identity

Represent clearly:

- ICRS;
- FK5;
- Galactic;
- ecliptic;
- horizontal.

Keep astronomical transformation separate from chart spherical rotation.

---

## Milestone 20 — Epoch and equinox separation

Represent separately:

- catalogue reference epoch;
- coordinate frame and equinox;
- observation epoch;
- tangent-point coordinates and frame.

---

## Milestone 21 — Astrometric propagation

As supported by catalogue data:

- proper motion;
- parallax;
- radial velocity;
- epoch propagation;
- Gaia support.

---

## Milestone 22 — Observer central-body generalization

Generalize `Observer` to support:

- Earth;
- Mars;
- Moon;
- other Solar-System bodies.

This milestone must preserve the fixed chart pipeline.

---

# Phase VI — Publication enhancements

Implement according to guidebook priorities:

- label conflict resolution;
- improved automatic label placement;
- richer Milky Way representation;
- stylesheets and themes;
- SVG export;
- PDF export;
- page-layout integration;
- additional projections only when a concrete chart requires them.

---

# 5. Release checkpoints

## Checkpoint A — Regional mathematics

After Milestone 4:

- arbitrary tangent-point stereographic projection works;
- full-sky projection remains correct;
- regional viewport works.

## Checkpoint B — Regional Chart MVP

After Milestone 5:

- Wenu produces useful regional charts, even though some temporary adapters remain.

## Checkpoint C — Target hierarchy implemented

After Milestone 12:

- `SkyLayer`;
- `AstronomicalObject`;
- `GeometricalObject`;
- `Stars`;
- `CelestialPoints`;
- `ConstellationLines`;
- `ConstellationBoundaries`;
- `CoordinatesGrid`;

all follow the target model.

## Checkpoint D — Architecture migration complete

After Milestone 15:

- all layers use the generic pipeline;
- legacy paths are removed;
- dependency direction is enforced.

## Checkpoint E — Stable regional production

After Milestone 16:

- the public API is concise;
- regional charts are reproducible;
- guidebook chart production can proceed without further architectural work.

---

# 6. Frozen decisions

The following decisions are fixed for this migration:

1. `CelestialSphere` is the central public abstraction.
2. Every chartable entity is a `SkyLayer`.
3. Physical entities derive from `AstronomicalObject`.
4. Celestial geometric constructs derive from `GeometricalObject`.
5. `CoordinatesGrid` is the correct name.
6. `MilkyWay` is an `AstronomicalObject`.
7. Geometry uses collection classes only.
8. Projection is coordinate-system agnostic.
9. Spherical rotation is separate from projection.
10. Domain layers do not project or render themselves.
11. Renderer consumes projected geometry.
12. Regional stereographic charts are the immediate functional priority.
13. Full astronomical frame, epoch, Gaia, and planetary-observer generalization are deferred.
14. No architecture revisions are made unless implementation reaches a genuine roadblock.

---

# 7. Immediate next action

Start with **Milestone 1 — Freeze the baseline**.

After the baseline commit, proceed directly to **Milestone 2 — Complete collection-based geometry**.

Do not reopen the architectural discussion during these milestones.
