# Wenu architecture diagrams

**Status:** Current as of the v0.9 closure baseline `5da93cc`

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

- all sources produce one typed `AstronomicalState`;
- products declare a `ProductFrameRequest` instead of transforming data;
- one coordinate service validates, normalizes, and transforms;
- observer context enters only the explicitly observer-local AltAz path;
- celestial and observer-local realizations retain typed scientific identity;
- projection alignment and every downstream rendering stage remain
  astronomically neutral.

The ephemeris and orbit adapters are shown as later consumers of the same
boundary; 49B/49C do not implement those providers.

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
It then shows which current owners lose transformation authority and where the
proposed immutable state types, coordinate service, and adapters enter.

The candidate `src/wenu/astronomy/` package name, its module split, and the
new type names are design proposals to freeze during 49B/49C—not claims about
current code. The intended design adds composition and small protocols rather
than replacing the retained hierarchy with a second deep inheritance tree.

Static-structure notation:

- `inherits`: a real subclass/generalization relationship;
- `contains` or `composes`: lifecycle or value ownership;
- dashed dependency: a call, construction, protocol implementation, or use;
- package boundary: the source directory in which the type or procedure lives.

### Runtime sequence: proposed 49B/49C calls

[Open the proposed coordinate runtime-sequence SVG](coordinate_runtime_sequence_target_49bc.svg)

Source: `coordinate_runtime_sequence_target_49bc.dot`

This sequence view shows procedures and returned values in time order for both
an observer-independent celestial product and an explicitly observer-local
product. Its horizontal arrows are runtime calls or returns, never inheritance.
The two paths deliberately converge before projection and rendering.

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
