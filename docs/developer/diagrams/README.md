# Wenu architecture diagrams

**Status:** v0.9 as-is baseline plus architecture 0.9.5 implementation tracking through the 49C.2 candidate

These diagrams are a human inspection interface for the as-is software. They
are intended to let Fernando inspect architecture ownership, principal data
flow, preserved boundaries, and the exact areas affected by an upcoming
architectural change without first reconstructing the system from source.

## Current diagrams

### Architecture and execution flow

[Open the current v0.9 architecture SVG](current_architecture_v0.9_overview.svg)

Source: `current_architecture_v0.9_overview.dot`

This diagram separates request resolution, astronomical-state realization,
the shared geometry/rendering pipeline, and product orchestration. It shows
which products reuse the canonical path and where observer-local state enters.

### Coordinate transformations and 49B/49C seams

[Open the coordinate as-is SVG](coordinate_transformation_as_is_v0.9.svg)

Source: `coordinate_transformation_as_is_v0.9.dot`

Red boxes identify the current overlapping transformation authorities and
observer-dependent detour. Green boxes identify the planned ownership seams:

- 49B introduces typed astronomical-state vocabulary and enforceable
  scientific identity;
- 49C introduces one coordinate service and explicit celestial versus
  observer-local transformation paths;
- projection alignment, projection, clipping, and rendering remain
  coordinate-neutral and outside the rationalization.

### Coordinate target after 49B/49C

[Open the coordinate target-state SVG](coordinate_transformation_target_49bc.svg)

Source: `coordinate_transformation_target_49bc.dot`

This companion diagram shows the intended ownership after the first coordinate
rationalization:

- every astronomical object obtains its native position through the common
  `PositionProvider` protocol;
- star and deep-sky catalogue providers implement it now, while solar-system
  ephemeris and orbit providers implement the same boundary later;
- constructed grids, planes, and poles remain a separate
  `ReferenceGeometryProvider` family;
- both source families produce existing `Spherical*` geometry carrying one
  immutable `CoordinateSpec`;
- products declare a target `CoordinateSpec` instead of transforming data;
- one `CoordinateService` validates and transforms all geometry kinds while
  preserving topology;
- `ObservationContext` enters only the explicitly observer-local path;
- projection alignment and every downstream rendering stage remain
  astronomically neutral.

`PositionProvider` is the boundary for all astronomical objects, not a
Moon/planet special case. Adding a new object family requires only another
provider implementation; the coordinate service, geometry records, projection,
and renderer do not change.

## Software-engineering views

The coordinate diagrams use three complementary, UML-inspired views. They
must be read together; no single diagram is expected to encode structure,
ownership, and runtime order simultaneously.

### Static structure: current implementation

[Open the current coordinate static-structure SVG](coordinate_static_structure_as_is_v0.9.svg)

Source: `coordinate_static_structure_as_is_v0.9.dot`

This source-backed view names the current Python modules, actual classes,
dataclasses, functions, inheritance hierarchy, composition, and dependencies.
It distinguishes the real `SkyLayer` inheritance tree from the independent
`Spherical*` geometry records.

### Static structure: proposed 49B/49C result

[Open the proposed coordinate static-structure SVG](coordinate_static_structure_target_49bc.svg)

Source: `coordinate_static_structure_target_49bc.dot`

This is the direct counterpart to the current static-structure diagram. It
retains the same `SkyLayer` inheritance hierarchy, `CelestialSphere`,
`Spherical*` record family, observer, cache, and chart/projection columns.
The deliberately large canvas shows the complete proposed ownership and
linkage: all astronomical-object classes implement the common
`PositionProvider` protocol in `positions.py`; constructed reference
geometry remains distinct; existing `Spherical*` records gain an immutable
`CoordinateSpec`; `coordinate_service.py` is the one `CoordinateService`
owner, while `coordinates.py` retains the immutable vocabulary; and `ObservationContext` is supplied only for observer-local
transformations. The existing `SkyLayer` hierarchy and downstream projection
and rendering classes remain visible and retained. No parallel astronomical
state hierarchy is proposed.

Implemented migration boundary at 49C.2: reference geometry, chart
compatibility conversions, deep-sky geometry, constellation references,
observer caches, and chart-orientation reference directions now use the
service. Skyfield apparent stellar realization remains provider work, and
native AltAz horizon construction remains reference geometry.

Static-structure notation:

- `inherits`: a real subclass/generalization relationship;
- `contains` or `composes`: lifecycle or value ownership;
- dashed dependency: a call, construction, protocol implementation, or use;
- package boundary: the source directory in which the type or procedure lives.

### Runtime sequence: proposed 49B/49C calls

[Open the proposed coordinate runtime-sequence SVG](coordinate_runtime_sequence_target_49bc.svg)

Source: `coordinate_runtime_sequence_target_49bc.dot`

This sequence view shows one procedure order for every source. Existing layers
and future Moon/planet providers both enter by producing `Spherical*` geometry
with a source `CoordinateSpec`. Its horizontal arrows are runtime calls or
returns, never inheritance. Optional observer context changes only the service
input; the downstream sequence is identical.

## Maintenance contract

The diagrams must be updated whenever a milestone changes any of:

- package or type ownership;
- astronomical frame, origin, epoch, instant, time-scale, or position-status
  responsibility;
- the canonical request, geometry, preparation, rendering, or export flow;
- observer-independent versus observer-local realization;
- product reuse or cache boundaries.

For an architectural migration, preserve an explicit as-is diagram before
implementation, then update the current diagram in the closure milestone.
The before/after diagrams must make moved responsibilities visible rather than
merely changing version labels.

The hand-maintained Graphviz sources are authoritative because automated class
diagrams do not express runtime ownership or scientific meaning. Regenerate
the SVGs from the repository root with:

```bash
dot -Tsvg docs/developer/diagrams/current_architecture_v0.9_overview.dot \
  -o docs/developer/diagrams/current_architecture_v0.9_overview.svg
dot -Tsvg docs/developer/diagrams/coordinate_transformation_as_is_v0.9.dot \
  -o docs/developer/diagrams/coordinate_transformation_as_is_v0.9.svg
```

The current diagrams complement `../current_architecture_v0.9.md`,
`../implementation_reference.md`, `../source_tree.md`, and
`../coordinate_transformation_audit_09a2afd.md`; they do not replace the
precise contracts in those documents.
