# Wenu Source Organization

**Branch**

`feature/regional-stereographic-charts`

**Status**

This document describes the organization of the Wenu source tree.

Its purpose is to explain how the current architecture maps onto the package structure. It complements `current_architecture.md`, which describes the software architecture independently of the directory layout.

---

# 1. Overview

The Wenu source tree is organized by software responsibility.

Major architectural concepts are generally grouped into separate packages, allowing astronomical computations, celestial-sphere constructs, projections, geometry and rendering to evolve independently.

The current source tree is

```text
src/wenu
│
├── geometry.py              Basic geometric utilities
├── observer.py              Observer definition and observing context
├── projected.py             Projected geometric objects
├── projection.py            Map projections
├── spherical_frame.py       Spherical coordinate transformations
├── viewport.py              Visible chart region
│
├── objects/
│   └── stars.py             Stellar catalogues
│
├── sky/
│   ├── celestial_sphere.py  CelestialSphere orchestration class
│   ├── constellations.py    Constellation layers
│   ├── curves.py            Celestial curves
│   ├── grids.py             Coordinate grids
│   └── points.py            Celestial reference points
│
├── renderers/
│   ├── matplotlib.py        Rendering primitives
│   └── matplotlib_axes.py   Matplotlib backend support
│
├── resources/               Package resource access
│
├── data/                    Astronomical catalogues and datasets
│
└── utils/                   General utilities
```

---

# 2. Top-Level Modules

## observer.py

Defines the observing conditions.

Provides the astronomical context shared by the entire package.

---

## spherical_frame.py

Implements spherical coordinate transformations independently of any particular astronomical coordinate system.

---

## projection.py

Implements spherical map projections.

The current implementation provides stereographic projection together with compatibility interfaces for the existing astronomical layers.

---

## projected.py

Defines projected Cartesian geometry produced by the projection subsystem.

Current projected classes include projected points, curves and polygons.

---

## viewport.py

Defines the visible region of a chart after projection.

---

## geometry.py

Contains geometric utilities shared by multiple subsystems.

---

# 3. Packages

## objects/

Contains physical astronomical objects and catalogues.

Current contents

```text
stars.py          Stellar catalogue management
```

---

## sky/

Contains celestial-sphere constructs.

These classes describe the organization of the sky rather than physical astronomical objects.

Current contents

```text
celestial_sphere.py    Central orchestration class

constellations.py      Constellation layers

curves.py              Celestial curves

grids.py               Coordinate grids

points.py              Celestial reference points
```

---

## renderers/

Contains rendering backends.

Current contents

```text
matplotlib.py          Rendering primitives

matplotlib_axes.py     Matplotlib backend support
```

---

## resources/

Contains utilities for locating package resources independently of the installation location.

---

## data/

Contains astronomical catalogues and other datasets distributed with Wenu.

---

## utils/

Contains general-purpose utilities used throughout the package.

---

# 4. Relationship Between Packages

The current organization of the principal packages is

```text
                   observer
                       │
                       │
                       ▼
                     sky
                   /  |  \
                  /   |   \
                 ▼    ▼    ▼
            objects projection
                  \      /
                   \    /
                    ▼  ▼
                 projected
                      │
                      ▼
                 renderers
```

This diagram illustrates the principal package dependencies in the current implementation. It is intended as a conceptual overview rather than a complete dependency graph.

---

# 5. Relationship to the Architecture

The mapping between the architectural concepts described in `current_architecture.md` and the source tree is summarized below.

| Architectural concept | Principal implementation |
|------------------------|--------------------------|
| Observer | `observer.py` |
| CelestialSphere | `sky/celestial_sphere.py` |
| Sky Layers | `sky/` and `objects/` |
| Coordinate transformations | `spherical_frame.py` |
| Projection | `projection.py` |
| Projected Geometry | `projected.py` |
| Rendering | `renderers/` |
| Resources | `resources/` |
| Astronomical data | `data/` |

---

# 6. Summary

The Wenu source tree mirrors the principal architectural concepts of the package.

Top-level modules implement the core mathematical infrastructure, while packages group related functionality according to their responsibilities within the architecture.

Detailed documentation of the classes contained in each source file is provided separately.


