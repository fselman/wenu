# Wenu Architecture Roadmap

## Phase I — Foundations

### ✓ Commit 0 — Package foundation
- Create the package structure.
- Establish imports and basic project organization.
- Configure testing infrastructure.

### ✓ Commit 1 — Coordinate and observer foundations
- Observer abstraction.
- Time and location handling.
- Coordinate transformations.

### ✓ Commit 2 — Spherical frame abstraction
- Separate astronomical coordinate systems from rendering.
- Introduce spherical-frame abstractions.

### ✓ Commit 3 — Viewport abstraction
- Introduce the Viewport class.
- Define the rectangular projected region independently of rendering.

---

## Phase II — Geometry Pipeline

### ✓ Commit 4 — Projected geometry abstraction

Introduce renderer-independent Cartesian geometry.

Classes:

- ProjectedPoint
- ProjectedCurve
- ProjectedPolygon

Projection now produces projected geometry objects instead of plotting directly.

---

### ✓ Commit 5 — Visibility and segmentation

Introduce a dedicated visibility module.

Responsibilities:

- altitude visibility determination
- visibility masks
- contiguous visible segment construction

Implemented:

- visibility_mask()
- split_visible_segments()
- visible_segments()

Projection and CelestialCurve now delegate visibility logic to this module.

Dedicated unit tests added.

---

### □ Commit 6 — Cartesian clipping

Purpose:

Clip projected geometry to a rectangular viewport.

The clipping stage operates **only** on projected Cartesian geometry.
It has no knowledge of astronomy or map projections.

#### 6.1 Low-level clipping

Provide low-level Cartesian clipping algorithms.

- Liang–Barsky line clipping
- polyline clipping helper

#### 6.2 Point clipping

Public API:

- clip_point_to_viewport()

Returns:

- ProjectedPoint
- or None

#### 6.3 Curve clipping

Public API:

- clip_curve_to_viewport()

Input:

- ProjectedCurve

Output:

- list[ProjectedCurve]

Responsibilities:

- preserve metadata
- split disconnected visible fragments
- support closed curves
- treat non-finite samples as curve breaks

#### 6.4 Polygon clipping

Public API:

- clip_polygon_to_viewport()

Input:

- ProjectedPolygon

Output:

- ProjectedPolygon
- or None

Implementation:

- Sutherland–Hodgman clipping

#### 6.5 Pipeline integration

Insert clipping between projection and rendering.

Final pipeline:

Celestial object
→ sampled geometry
→ visibility
→ projection
→ projected geometry
→ clipping
→ renderer

---

### □ Commit 7 — Rendering

Separate rendering completely from projection.

Responsibilities:

- Matplotlib renderer
- future SVG/PDF renderers
- future interactive renderers

Projection produces geometry only.

Renderer consumes geometry only.

---

## Phase III — Astronomical Objects

### □ Commit 8 — Stars

Complete geometry pipeline for stars.

Responsibilities:

- projection
- clipping
- rendering

---

### □ Commit 9 — Celestial points

Support:

- poles
- galactic center
- equinoxes
- solstices
- labels

---

### □ Commit 10 — Celestial curves

Support:

- celestial equator
- ecliptic
- galactic equator
- constant declination
- constant latitude
- future coordinate grids

---

### □ Commit 11 — Constellations

Support:

- constellation lines
- boundaries
- labels
- multiple line systems

---

### □ Commit 12 — Regional charts

Complete chart-generation pipeline.

Support:

- arbitrary chart centers
- arbitrary spherical coordinate systems
- arbitrary tangent points
- publication-quality regional charts

This marks the completion of the core Wenu geometry architecture.
