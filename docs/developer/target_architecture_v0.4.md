# Wenu target architecture

**Version:** 0.4  
**Date:** 2026-07-26  
**Status:** Draft  
**Supersedes:** `target_architecture_v0.3.md`

## 1. Purpose

Wenu is a Python package for producing reproducible, publication-quality
charts of the sky.

It supports two principal kinds of output:

- full-sky charts and planispheres;
- regional charts, including charts centered on constellations or arbitrary
  celestial coordinates.

The target architecture defines how astronomical content, geometry,
projection, chart configuration, styling, and rendering are separated. It
also defines the package boundaries into which the present implementation
will be reorganized.

This document describes the desired architecture. Implementation sequencing
belongs in the migration roadmap.

## 2. Product priorities

Wenu is primarily a static chart-generation system, not an interactive
planetarium.

The architecture therefore prioritizes:

- astronomical correctness;
- reproducible output;
- publication-quality static graphics;
- full control of framing, orientation, cropping, labels, and styles;
- support for both full-sky and regional charts;
- efficient catalogue-sized point rendering;
- extension with new astronomical and geometrical layers;
- independence between astronomical data and graphical backends.

Interactive navigation, animation, and real-time planetarium behavior are not
architectural goals of version 0.4.

## 3. Fundamental model

The fundamental astronomical abstraction is the **celestial sphere**.

A chart is a configured representation of selected celestial-sphere content
for a particular observer, projection, viewport, style, and output medium.

Astronomical or celestial-sphere content that can appear on a chart is
represented by a `SkyLayer`. Presentation-only elements such as titles,
legends, borders, page furniture, and export metadata are chart or renderer
concerns and are not `SkyLayer` objects.

## 4. Canonical runtime pipeline

Every sky layer follows one canonical pipeline:

```text
Observer
    ↓
CelestialSphere
    ↓
SkyLayer
    ↓
Spherical Geometry
    ↓
Projection
    ↓
Projected Geometry
    ↓
Optional Preparation
    ↓
Renderer
    ↓
Graphical Output
```

The stages have distinct responsibilities:

| Stage | Responsibility |
|---|---|
| Observer | observing time, location, and coordinate-frame context |
| Sky layer | astronomical data, selection, native-frame construction, and observer-dependent transformation |
| Spherical geometry | coordinate-neutral representation on a sphere |
| Projection | conversion from spherical to Cartesian geometry |
| Preparation | optional geometry- and presentation-dependent transformations |
| Renderer | conversion of prepared projected geometry into backend output |

Full-sky and regional charts must use this same pipeline. A new chart type
must not introduce a parallel projection or rendering path.

## 5. Architectural layers

The target system contains six architectural areas:

1. astronomical domain;
2. sky composition and orchestration;
3. geometry;
4. projections;
5. chart specifications;
6. rendering.

### 5.1 Astronomical domain

The astronomical domain contains:

- `Observer`;
- catalogue and resource access;
- physical astronomical objects;
- astronomical coordinate transformations.

It may depend on coordinate libraries and spherical geometry, but it must not
depend on a projection or graphical backend.

### 5.2 Sky composition and orchestration

The sky subsystem contains:

- `SkyLayer`;
- `GeometricalObject`;
- celestial-sphere constructs;
- `CelestialSphere`;
- ordered layer registration;
- canonical chart orchestration.

It may depend on the observer and spherical geometry. It must not contain
projection mathematics or backend drawing code.

### 5.3 Geometry

The geometry subsystem contains:

- spherical geometry values;
- projected Cartesian geometry values;
- spherical-frame rotations;
- geometric clipping algorithms;
- the projected viewport.

It is coordinate-neutral and has no knowledge of catalogues, observers,
constellations, or Matplotlib.

### 5.4 Projections

The projections subsystem transforms spherical geometry into projected
geometry.

It depends on the geometry subsystem but not on sky layers, astronomical
objects, chart styles, or renderers.

### 5.5 Chart specifications

A chart specification combines:

- framing;
- projection configuration;
- orientation;
- viewport;
- layer selections;
- style;
- export configuration.

It configures the canonical pipeline; it does not replace it.

### 5.6 Rendering

Rendering contains two related but separate responsibilities:

- backend-independent preparation of projected geometry and renderer options;
- backend-specific production of graphical output.

The distinction between preparation and rendering remains explicit even when
both are contained in the same package.

## 6. Observer and coordinate policy

`Observer` is responsible for the observing context:

- location;
- time;
- access to required astronomical frames and time representations.

Astronomical layers are responsible for transforming their source coordinates
to the chart pipeline's spherical coordinates for that observer.

The following rules apply:

1. Source data remains associated with its correct native or catalogue frame.
2. A shape is constructed and sampled in the frame in which that shape is
   defined.
3. Observer-dependent transformation occurs after native-frame construction.
4. Spherical-frame rotation for projection is coordinate-neutral.
5. Atmospheric refraction, aberration, deflection, and similar corrections
   must be explicit policies rather than hidden projection behavior.

The constellation-boundary implementation is the reference example:
official polygons are assembled and sampled in B1875/FK4 before being
transformed to the observer-time frame. This avoids replacing geometrically
correct native-frame edges with unnecessarily dense approximations.

## 7. Sky-layer model

### 7.1 Contract

Every drawable astronomical or celestial-sphere entity implements:

```python
spherical_geometry(observer, **geometry_options)
```

It returns one of the supported spherical geometry values.

A layer may:

- load and select source data;
- evaluate observer-dependent coordinates;
- construct and sample native-frame geometry;
- attach identifiers, labels, names, semantic metadata, and neutral style
  hints.

A layer must not:

- project its geometry;
- create graphical artists;
- import a rendering backend;
- store projected or rendered state as part of normal drawing;
- implement a specialized chart pipeline.

### 7.2 `AstronomicalObject`

`AstronomicalObject` represents physical astronomical entities.

```text
SkyLayer
    └── AstronomicalObject
            ├── Stars
            └── future physical-object layers
```

`Stars` remains the first concrete catalogue-sized implementation. It owns
catalogue loading, identifiers, magnitudes, available colour data, filtering,
and observer-dependent coordinates.

Potential future layers such as clusters, galaxies, nebulae, Solar System
objects, or Milky Way brightness data are extension examples, not required
classes in version 0.4.

### 7.3 `GeometricalObject`

`GeometricalObject` represents constructs defined on the celestial sphere:

```text
SkyLayer
    └── GeometricalObject
            ├── CelestialPoints
            ├── ConstellationLines
            ├── ConstellationBoundaries
            ├── ConstellationLabels
            ├── CoordinatesGrid
            └── future geometrical layers
```

The difference between an astronomical object and a geometrical object is
semantic. It does not change the projection or rendering pipeline.

### 7.4 Grouping objects

A grouping or façade does not automatically become a `SkyLayer`.

For example, `Constellations` may group line, boundary, and label layers while
those individual layers remain the drawable units. Grouping objects must not
accumulate projected state or backend behavior.

## 8. Geometry model

### 8.1 Spherical geometry

The spherical geometry model contains:

- `SphericalPoint`;
- `SphericalPoints`;
- `SphericalCurve`;
- `SphericalCurves`;
- `SphericalGrid`;
- `SphericalPolygon`;
- `SphericalPolygons`.

Longitudes and latitudes are expressed in degrees. Their astronomical meaning
is supplied by the layer and observing context, not encoded in the geometry
type.

### 8.2 Projected geometry

The projected geometry model contains:

- `ProjectedPoint`;
- `ProjectedPoints`;
- `ProjectedCurve`;
- `ProjectedCurves`;
- `ProjectedGrid`;
- `ProjectedPolygon`;
- `ProjectedPolygons`.

Projected values use Cartesian `x` and `y` coordinates.

### 8.3 Singular and collection types

Singular classes represent individual geometrical objects.

Curve and polygon collections are lightweight wrappers around a reasonably
small number of their corresponding singular objects. They may carry
collection-level metadata.

`SphericalPoints` and `ProjectedPoints` are intentionally vectorized rather
than collections of scalar point instances. This is required for efficient
catalogue projection, masking, clipping, styling, and rendering.

### 8.4 Semantic preservation

Projection and preparation must preserve all applicable:

- identifiers;
- names;
- labels;
- closure information;
- component grouping;
- semantic metadata.

`ProjectedGrid` must preserve named components such as meridians, parallels,
and reference curves.

### 8.5 Metadata

Metadata is not an unrestricted communication channel.

The following rules apply:

- semantic metadata may travel with geometry;
- projection preserves semantic metadata;
- backend-specific objects must never be stored in geometry;
- neutral per-entity style hints may accompany geometry when they are intrinsic
  to the layer;
- substantial chart presentation policy belongs in chart styles and layer
  options.

## 9. Spherical frames and projection

Spherical-frame rotation and map projection are separate concepts.

`SphericalFrame` defines a coordinate-neutral rotation using:

- tangent-point longitude;
- tangent-point latitude;
- position angle.

A projection then maps the rotated spherical values into a plane.

`StereographicProjection` must support:

- scalar coordinates;
- vectorized coordinate arrays;
- all supported spherical geometry containers;
- arbitrary tangent points;
- position angle;
- east-west orientation;
- configurable projection radius.

Projection has no knowledge of:

- stars;
- constellations;
- coordinate grids;
- observers;
- chart styles;
- Matplotlib.

The projections package may contain additional algorithms in the future, but
version 0.4 does not require them.

## 10. Viewport and clipping

`Viewport` is a Cartesian rectangle in projected coordinates.

There are two distinct forms of clipping:

### 10.1 Spherical or semantic clipping

This occurs during preparation. Examples include:

- clipping to a minimum altitude;
- selecting visible points;
- retaining only the desired side of a spherical boundary.

It depends on spherical meaning and therefore cannot be delegated blindly to
the graphics backend.

### 10.2 Final viewport clipping

This occurs in the renderer and clips graphical output to the chart patch.

Regional curves and grids may be generated beyond the visible rectangle and
then clipped exactly at the viewport boundary by the renderer. This avoids
using layer-specific rectangular trimming.

## 11. Preparation

Preparation is an optional stage between projection and rendering.

It handles transformations such as:

- astronomical magnitude to marker area;
- per-point style derivation;
- label offsets;
- spherical latitude clipping;
- other backend-independent presentation transformations.

A preparation function receives spherical and projected geometry and returns
prepared projected geometry or information required by the renderer.

Preparation must not:

- load astronomical catalogues;
- perform observer transformations;
- create backend artists;
- become a hidden second renderer.

## 12. Celestial-sphere orchestration

`CelestialSphere` owns:

- the observer;
- an ordered set of sky layers;
- convenience methods for constructing standard layers;
- canonical chart execution.

For each layer it performs:

```python
spherical = layer.spherical_geometry(
    observer,
    **geometry_options,
)

projected = projection.project_geometry(spherical)

prepared = (
    prepare(spherical, projected)
    if prepare is not None
    else projected
)

artists = renderer.draw(
    prepared,
    **render_options,
)
```

The orchestration result retains the layer, spherical geometry, prepared
projected geometry, and graphical result for inspection and testing.

Layer order is explicit and determines graphical stacking.

## 13. Layer options

Per-chart variation is expressed through structured layer options:

```python
{
    "geometry": {...},
    "prepare": callable,
    "render": {...} | callable,
}
```

The sections have separate meanings:

- `geometry` determines what spherical content the layer produces;
- `prepare` transforms the spherical/projected pair before rendering;
- `render` determines backend presentation.

This mechanism supports:

- constellation selection;
- per-chart label selection;
- magnitude limits;
- horizon clipping;
- star sizes;
- component styles;
- chart-specific rendering overrides.

A selection that varies by chart should normally be supplied as a geometry
option rather than stored by mutating a shared layer.

## 14. Chart specifications

### 14.1 Responsibility

A chart specification is an immutable, reproducible description of how
celestial-sphere content is presented.

It may define:

- projection;
- tangent point;
- orientation;
- angular field;
- viewport;
- crop;
- layer selections;
- style;
- export options.

It delegates execution to the canonical `CelestialSphere` pipeline.

### 14.2 Regional charts

`RegionalChart` is the established regional specification.

It supports:

- explicit horizontal centers;
- centers derived from Astropy coordinates;
- centers derived from selected constellation figures;
- arbitrary position angles;
- celestial north up;
- rectangular angular fields;
- reproducible figure aspect and export.

### 14.3 Full-sky charts and planispheres

Version 0.4 targets a first-class public specification for full-sky charts and
planispheres.

It must share the same:

- sky layers;
- spherical geometry;
- projections;
- preparation;
- renderer;
- style principles;
- result records.

It may supply full-sky-specific framing, circular masks, horizon treatment,
orientation, and planisphere configuration.

The target architecture does not yet require `RegionalChart` and a future
full-sky specification to inherit from a common concrete `Chart` base class.
A shared protocol or base class should be introduced only after their actual
common behavior is established.

### 14.4 Presentation-only chart elements

The chart or rendering subsystem owns elements that are not celestial-sphere
content, including:

- titles;
- legends;
- borders;
- page backgrounds;
- scale information;
- output metadata.

These elements are not forced into the `SkyLayer` hierarchy.

## 15. Styles and export

A style provides reproducible presentation policy without altering
astronomical source data.

It may:

- configure backend axes or canvas properties;
- define common colours, widths, alpha values, fonts, and marker policies;
- produce structured layer options;
- configure label and grid policies.

Styles must not:

- calculate astronomical coordinates;
- perform projection;
- create or own sky layers;
- introduce specialized drawing paths.

Export configuration controls:

- output path handling;
- physical figure size;
- raster resolution;
- transparency and background;
- bounding-box policy;
- output metadata.

Physical figure size and raster DPI are independent. Increasing resolution
must not implicitly enlarge star symbols, line widths, or text.

## 16. Renderer boundary

A renderer consumes prepared projected geometry and produces backend output.

The renderer is responsible for:

- projected-geometry dispatch;
- backend artist or primitive construction;
- common, per-entity, and per-component styles;
- text and labels;
- final viewport clipping;
- returning the created graphical values.

A renderer must not:

- load catalogues;
- transform celestial coordinates;
- interpret constellation systems;
- perform spherical-frame rotation;
- perform map projection.

Matplotlib is the required backend for version 0.4.

The architecture defines the renderer boundary behaviorally. An abstract
renderer hierarchy is not required until a second backend demonstrates the
need for one.

## 17. Target package structure

The source tree will be reorganized to reflect the architectural boundaries:

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
│   └── styles.py
│
├── rendering/
│   ├── __init__.py
│   ├── preparation.py
│   └── matplotlib.py
│
├── catalogs/
├── resources.py
└── data/
```

This is the intended responsibility map. Additional package-internal helper
modules may be introduced when justified, but they must respect the same
boundaries.

## 18. Package responsibilities

### 18.1 `coordinates.py`

The current top-level `geometry.py` contains astronomical coordinate
conversion rather than geometry values. It becomes `coordinates.py`.

Coordinate transformations that remain outside `Observer` or concrete layers
belong here. The module must not become a second observer abstraction.

### 18.2 `objects/`

Contains physical astronomical entities and their source-data behavior.

### 18.3 `sky/`

Contains celestial-sphere constructs, layer contracts, grouping façades, and
the sky composition/orchestration object.

### 18.4 `geometry/`

Contains coordinate-neutral geometry values and algorithms.

The planned file moves are:

| Current | Target |
|---|---|
| `spherical.py` | `geometry/spherical.py` |
| `projected.py` | `geometry/projected.py` |
| `spherical_frame.py` | `geometry/frame.py` |
| `clipping.py` | `geometry/clipping.py` |
| `viewport.py` | `geometry/viewport.py` |

### 18.5 `projections/`

Contains map-projection implementations.

The current `projection.py` becomes
`projections/stereographic.py`.

### 18.6 `charts/`

Contains chart specifications, reusable chart styles, and eventually a public
full-sky/planisphere specification.

The planned file moves are:

| Current | Target |
|---|---|
| `chart.py` | `sky/rendering_results.py` |
| `regional.py` | `charts/regional.py` |
| `styles.py` | `charts/styles.py` |

Rendering results belong beside `CelestialSphere`, which creates them. This
preserves the dependency direction `charts → sky` and avoids `sky → charts`.
The name `rendering_results.py` reflects the present contents of `chart.py`
without inventing a `Chart` class.

### 18.7 `rendering/`

Contains generic preparation and graphical backends.

The planned file moves are:

| Current | Target |
|---|---|
| `rendering.py` | `rendering/preparation.py` |
| `renderers/matplotlib.py` | `rendering/matplotlib.py` |

Preparation and backend rendering remain architecturally distinct.

## 19. Source dependency rules

Runtime data flow and source dependencies are not the same diagram.

The intended source dependencies are:

```text
objects/ ──────────────┐
                       ├──→ sky/ ───────────→ geometry/
coordinates.py ────────┘

projections/ ───────────────────────────────→ geometry/

rendering/preparation.py ───────────────────→ geometry/
rendering/matplotlib.py ────────────────────→ geometry/

charts/ ───────────────→ sky/
charts/ ───────────────→ geometry/
charts/ ───────────────→ projections/
charts/ ───────────────→ rendering/
```

The following reverse dependencies are prohibited:

- `geometry/` importing `objects/`, `sky/`, `charts/`, or `rendering/`;
- `objects/` importing `projections/`, `charts/`, or rendering backends;
- `sky/` importing `projections/`, `charts/`, or rendering backends;
- `projections/` importing `objects/`, `sky/`, `charts/`, or rendering
  backends;
- a graphical backend importing concrete astronomical layers.

Dependency tests must enforce these rules.

## 20. Public API

Internal package organization and the intentional public API are distinct.

Principal user-facing names may continue to be exported from `wenu`:

```python
from wenu import (
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
    StereographicProjection,
    Viewport,
)
```

The exact exported set is maintained deliberately in `wenu.__init__`; internal
module paths are not automatically public contracts.

## 21. Clean-break policy

There are no external Wenu users requiring compatibility with the present
internal module paths. The package reorganization will therefore be a clean
break.

The migration will:

- move modules directly to their target packages;
- update every internal import;
- update tests, examples, and developer documentation;
- preserve intentional top-level exports from `wenu`;
- avoid forwarding modules for former internal paths;
- avoid deprecation shims for the old layout.

Functional changes should not be mixed into the structural reorganization.
The full automated suite and visual chart examples must pass before and after
the move.

## 22. Resource and catalogue boundary

Packaged data is accessed through resource helpers and logical names rather
than caller-visible source-tree paths.

Examples include:

- star catalogues;
- constellation line systems;
- official boundary data;
- future surface-brightness maps.

Layers request domain data through catalogue or resource APIs. Renderers and
geometry modules do not load astronomical resources.

Alternative cultural constellation systems remain data/layer configuration,
not new projection or renderer implementations.

## 23. Extension rules

### 23.1 Adding a sky layer

A new sky layer should:

1. implement the `SkyLayer` contract;
2. produce an existing spherical geometry type when possible;
3. preserve stable identities and semantic metadata;
4. rely on the canonical projection and renderer;
5. expose per-chart choices as geometry options.

### 23.2 Adding a geometry type

A new geometry type is justified only when point, curve, grid, and polygon
semantics cannot represent the required content.

It requires:

- spherical and projected representations where applicable;
- projection support;
- preparation behavior where applicable;
- renderer dispatch;
- validation and preservation tests.

### 23.3 Adding a projection

A new projection:

- consumes spherical geometry;
- produces standard projected geometry;
- remains independent of sky-layer types and rendering backends.

### 23.4 Adding a graphical backend

A new backend:

- consumes prepared projected geometry;
- uses the Cartesian viewport;
- implements final backend clipping;
- contains no astronomy or projection logic.

### 23.5 Adding a chart type

A new chart type:

- configures the canonical pipeline;
- reuses existing layers and geometry;
- defines only chart-specific framing and presentation behavior;
- does not implement specialized layer draw methods.

## 24. Architectural invariants

The following invariants define successful conformance to version 0.4:

1. Every astronomical or celestial-sphere layer produces spherical geometry.
2. No sky layer knows about a map projection or graphical backend.
3. Projection is coordinate-neutral.
4. Spherical-frame rotation is separate from projection.
5. Projection preserves identity, grouping, and semantic metadata.
6. `SphericalPoints` and `ProjectedPoints` remain vectorized.
7. Preparation is distinct from astronomical data acquisition and backend
   rendering.
8. Renderers consume projected geometry and contain no astronomical logic.
9. Full-sky and regional charts use the same layer pipeline.
10. Chart-specific choices do not require mutation of shared layers.
11. Final rectangular clipping is performed by the renderer's chart patch.
12. Native-frame geometry is constructed before observer-dependent
    transformation.
13. Package dependencies follow the directions in section 19.
14. There is no legacy or parallel rendering path.
15. Public chart output can be reproduced from explicit observer, chart,
    style, and export configuration.

## 25. Version 0.4 completion criteria

The target architecture is realized when:

- the source tree follows the package boundaries in section 17;
- the clean-break reorganization is complete;
- dependency tests protect the new boundaries;
- current regional charts operate through the reorganized canonical pipeline;
- a first-class full-sky or planisphere chart specification uses that same
  pipeline;
- examples demonstrate both regional and full-sky publication output;
- all automated tests pass;
- visual regression examples remain astronomically and graphically correct;
- current architecture and implementation-reference documents describe the
  reorganized code;
- no obsolete internal import path or specialized rendering path remains.

## 26. Non-goals

Version 0.4 does not require:

- interactive planetarium navigation;
- real-time animation;
- a graphical user interface;
- multiple rendering backends;
- multiple map projections;
- a speculative hierarchy of unimplemented astronomical object classes;
- an abstract `Chart` base class without demonstrated common behavior;
- compatibility shims for the pre-v0.4 internal directory layout.

## 27. Central target

The central target of architecture version 0.4 is:

> Provide full-sky and regional publication-quality chart specifications over
> one immutable, observable, coordinate-neutral, backend-separated geometry
> pipeline, organized into package boundaries that express those
> responsibilities directly.
