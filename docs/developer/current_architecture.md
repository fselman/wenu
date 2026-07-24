# Wenu Current Architecture

**Branch**

`feature/regional-stereographic-charts`

**Status**

This document describes the architecture of the current implementation of Wenu.

It is intentionally descriptive rather than prescriptive. Its purpose is to document the software exactly as it exists in this branch. Every statement in this document should be verifiable from the source code.

Future architectural evolution is described separately in `target_architecture.md`.

---

# 1. Introduction

Wenu is a Python package for generating publication-quality astronomical charts.

Its architecture is organized as a sequence of layers that progressively transform astronomical information into graphical output while maintaining a clear separation between astronomy, geometry and rendering.

The principal concepts of the current architecture are

- an **Observer**, defining where and when the sky is seen,
- a **CelestialSphere**, describing the sky visible to that observer,
- a collection of **sky layers**, representing the astronomical contents of the celestial sphere,
- coordinate transformations,
- map projections,
- projected Cartesian geometry,
- rendering.

Although the architecture continues to evolve, these concepts already form the foundation of the current implementation.

---

# 2. Conceptual Architecture

At the highest level, Wenu is organized as

```
Observer
    │
    ▼
CelestialSphere
    │
    ▼
Sky Layers
    │
    ▼
Coordinate Transformations
    │
    ▼
Projection
    │
    ▼
Projected Geometry
    │
    ▼
Chart
    │
    ▼
Renderer
    │
    ▼
Matplotlib
```

This diagram represents the conceptual organization of the software rather than the exact sequence of method calls.

---

# 3. Observer

The `Observer` defines the observing conditions.

Its responsibilities include

- observing site,
- observing time,
- astronomical reference frames,
- Skyfield observer,
- Astropy coordinate systems.

Conceptually, the observer answers a single question:

> **Where and when is the sky being observed?**

Every astronomical object within Wenu is associated with an `Observer`.

---

# 4. CelestialSphere

`CelestialSphere` is the central orchestration object of the current Wenu architecture.

It represents the celestial sphere visible to an `Observer` at a particular location and time.

`CelestialSphere` is **not** itself an astronomical object. Instead, it owns and coordinates the collection of objects that together describe the sky.

Its current responsibilities are

- owning the associated `Observer`,
- owning the collection of sky layers,
- loading astronomical catalogues,
- creating celestial reference structures,
- coordinating the generation of charts,
- providing the principal public interface between notebooks and Wenu.

## Sky Layers

A **sky layer** is any object that contributes one logical component to the celestial sphere.

Examples include

- stellar catalogues,
- constellation line systems,
- constellation boundaries,
- celestial points,
- celestial curves,
- coordinate grids.

Each sky layer performs its own astronomical computations while participating in the construction of a chart.

The celestial sphere maintains an ordered collection of these layers.

---

# 5. Astronomical Layers

The current implementation supports several kinds of sky layers.

```
CelestialSphere
    │
    ├── Stars
    ├── Constellations
    ├── Constellation Boundaries
    ├── Celestial Points
    ├── Celestial Curves
    └── Coordinate Grids
```

Each layer is responsible for its own astronomical calculations while remaining conceptually independent of the others.

## Stars

The `Stars` layer represents the Hipparcos stellar catalogue.

Its current responsibilities include

- loading stellar catalogues,
- applying catalogue selection criteria,
- computing apparent stellar positions,
- computing plotting properties,
- projecting stellar positions,
- rendering the stellar field.

The current implementation therefore combines astronomical and rendering responsibilities inherited from the original planisphere implementation.

## Constellations

Constellation layers manage

- constellation line systems,
- constellation labels,
- constellation boundaries.

They obtain stellar positions through the `Stars` layer using Hipparcos identifiers.

## Celestial Points

Celestial points represent isolated reference locations on the celestial sphere.

Examples include

- celestial poles,
- galactic centre,
- ecliptic poles,
- equinoxes,
- solstices.

## Celestial Curves

Celestial curves represent sampled one-dimensional structures on the celestial sphere.

Examples include

- celestial equator,
- ecliptic,
- galactic equator,
- altitude circles,
- declination circles.

## Coordinate Grids

Coordinate grids are collections of celestial curves representing astronomical coordinate systems.

---

# 6. Coordinate Transformations

Astronomical layers may be defined in different celestial coordinate systems.

The current implementation supports transformations involving

- ICRS,
- Galactic,
- Ecliptic,
- Horizontal (Alt/Az).

The `Observer` supplies the astronomical context required to perform these transformations.

The current branch also introduces a more general spherical coordinate transformation framework intended to support coordinate-system-independent projections.

---

# 7. Projection

The projection subsystem converts spherical coordinates into projected Cartesian coordinates.

The current implementation provides a stereographic projection.

Its principal mathematical interface is

- `project_spherical()`.

Compatibility interfaces currently include

- `project()`,
- `project_point()`,
- `project_curve()`,
- `project_polygon()`.

The mathematical projection itself is independent of any particular astronomical coordinate system.

---

# 8. Projected Geometry

Following projection, astronomical information is represented as projected Cartesian geometry.

Current projected classes include

- `ProjectedPoint`,
- `ProjectedCurve`,
- `ProjectedPolygon`.

These classes contain no astronomical knowledge.

They represent purely geometric objects in the projected plane.

---

# 9. Charts

Conceptually, a **chart** is the graphical representation of a `CelestialSphere` after projection.

In the current implementation, charts are represented implicitly by the collection of projected geometry together with the graphical objects created by the rendering backend.

A dedicated `Chart` class has not yet been introduced.

---

# 10. Rendering

Rendering is responsible for converting projected geometry into graphical output.

The current rendering backend is Matplotlib.

Rendering primitives currently include functions for drawing

- points,
- collections of points,
- curves,
- polygons,
- text.

Rendering is intentionally separated from astronomical computations.

---

# 11. Current Implementation Flow

Although the conceptual architecture is organized around the `CelestialSphere`, individual layers currently perform portions of the processing pipeline themselves.

For example, the current stellar pipeline is

```
Hipparcos Catalogue
        │
        ▼
Apparent Positions
        │
        ▼
Horizontal Coordinates
        │
        ▼
Projection
        │
        ▼
Projected Coordinates
        │
        ▼
Rendering
```

Other astronomical layers follow analogous processing sequences.

This implementation reflects the current evolution of the software and should not be interpreted as the intended long-term architectural organization.

---

# 12. Transitional Components

The current branch contains both mature architectural components and components inherited from the original planisphere implementation.

The following subsystems already follow the newer layered architecture:

- projected geometry,
- rendering,
- viewport,
- spherical coordinate transformations.

The following classes continue to combine responsibilities inherited from the original implementation:

- `Stars`,
- `CelestialPoints`,
- `CelestialCurves`.

These remain active parts of the current implementation.

---

# 13. Documentation Status

Some existing documentation files no longer describe the current implementation exactly.

These include

- `roadmap.md`,
- `wenu_current_uml.dot`.

This document is intended to become the authoritative architectural description of the current branch.

---

# 14. Summary

The current implementation already exhibits a clear separation between

- astronomical computations,
- celestial organization,
- coordinate transformations,
- map projection,
- projected geometry,
- rendering.

The central organizing abstraction is the `CelestialSphere`, which coordinates the collection of sky layers describing the visible sky and serves as the principal interface through which charts are generated.

The remaining architectural evolution primarily concerns the continued separation of responsibilities inherited from the original planisphere implementation while preserving the conceptual organization described in this document.
