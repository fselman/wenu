# Wenu current architecture

**As-is baseline:** `6708f54a0d8984c0be348b2c8cb02b311646a02b` (2026-10-17).
This document describes implemented behavior. The proposed kernel and package
architecture lives separately in the [roadmap](kernel_roadmap_v0.9.5.md).

The separate [K2 kernel project](../../packages/wenu_kernel/README.md)
implements immutable direction records, explicit registration and synchronous
sessions and reproducible certified direction reuse. The current candidate adds
SI Cartesian full-model states with optional velocity and separate uncertainty
channels. It has no runtime dependencies or existing
product consumers. The production pipeline below is unchanged; routing it
through the kernel remains K3. Real providers and the SDK freeze are pending.

## Canonical pipeline

Catalogue/provider → spherical geometry → projection-domain guard → projection
→ projected geometry → preparation → renderer → furniture/export.
`sky/celestial_sphere.py::CelestialSphere.draw_chart()` is the existing core.
There must be no second scientific or rendering pipeline during migration.
`geometry/frame.py::SphericalFrame` aligns a projection; it is not an
astronomical frame transformation.

## Responsibility map

| Area | Existing owner | Boundary |
|---|---|---|
| Catalogue objects | `objects/` | Centres, source tables and extended morphology |
| Sky layers | `sky/` | Spherical content and observer-dependent realization |
| Coordinate meaning | `coordinates.py`, `coordinate_service.py` | Explicit frame/origin/status/time and transformations |
| Solar-System states | `ephemeris.py`, `skyfield_ephemeris.py`, `solar_system_directions.py` | Resource-bound states, light time and apparent directions |
| Minor bodies | `minor_body_*.py`, shared Solar-System layers | Explicit resource admission and descriptor-based point/track routes |
| Artificial satellites | `satellites/`, satellite report and presentation adapters | Snapshot, propagation, crossings, illumination and reports |
| Pure geometry | `geometry/` | Spherical/projected values, topology and clipping |
| Projection | `projections/` | Stereographic and Mollweide mapping |
| Products | `charts/`, `cli/` | Requests, framing, composition, atlas publication |
| Graphics | `rendering/`, `chart_document.py` | Preparation, Matplotlib and semantic SVG/PDF/PNG |

The [source map](source_tree.md) lists every production Python file.
There is currently one installed distribution, `wenu`; these directories are
not independent loadable astronomical packages.

## Implemented products and independent concerns

Ordinary charts include Galactic all-sky, observer-visible planisphere,
regional, circumpolar and binocular products. Physical polar-planisphere and
time-sequence products retain their separate product contracts while sharing
geometry, projection, preparation and export.

Chart family owns projection/framing/boundary. Detail owns selection. Style
owns appearance. Output mode owns physical display adaptation. Furniture and
legends have their own controls. Drawing selectors never supply a center;
centering is explicit. These concerns must not silently modify one another.

Atlas design, index and publication commands are implemented. Installed
layouts are 34-chart landscape, 36-chart portrait and two hemispheres.
Layout, full chart presentation and index presentation are separate inputs.
`atlas-v6` and `atlas-hemispheres-v2` are data presets, not scientific engines.
Their names do not freeze the set of styles that may be installed.
Publication uses native ICRS content, supports selected sheets, explicit saved
sky reuse, facing reports and criteria appendices. See the
[atlas guide](../user_guide/atlas.md) for current commands and limitations.

## Scientific state as implemented

`CoordinateSpec` and `ObservationContext` are immutable metadata contracts.
`CoordinateService` owns standards-based astronomical transformations;
provider-specific position generation remains separate.

The stellar catalogue is Hipparcos. `Stars.position(instant)` returns the
catalogue directions and ignores `instant`. Both Skyfield `Star` construction
sites currently supply only right ascension and declination: no catalogue
proper motions, parallax or radial velocity. The observed route does compute
apparent AltAz for the requested observer/date; lack of stellar space-motion
propagation does not mean Earth orientation is omitted. Native ICRS axes do
not precess. The two native output routes also disagree in their epoch
metadata (J1991.25 versus default J2000.0); this is a migration defect to fix,
not a scientific convention to preserve. No Gaia astrometric provider exists.

Solar-System Cartesian resources, state requests and astrometric/apparent
direction realizers have stronger typed contracts. They solve light time
separately from apparent corrections. These facilities must be reused rather
than reimplemented in a new kernel.

## Abstraction barriers that remain incomplete

1. `CelestialSphere` and `maximal_sphere` know concrete layer classes. There is
   no provider registry behind a uniform epoch-state query interface.
2. `SkyLayer.realize()` has a legacy fallback that discards the context and
   calls `spherical_geometry(observer)`. Physical state and observation are
   therefore not uniformly separated.
3. Frozen coordinate metadata does not make every geometry result immutable:
   general arrays, dictionaries and layer collections remain mutable.
4. Request preparation temporarily installs layers and rebinds resolvers.
   The audit identified incomplete rollback of added minor-body layers after
   request-resolution failure. Isolate and fix this with failure injection
   before relying on shared kernel sessions.
5. `charts/atlas_publication.py` calls request generation, while request
   generation imports atlas-specific private furniture/report helpers.
   This creates a cycle across the intended chart/atlas barrier.
6. Native snapshots are existing transport/reuse objects, not a universal
   physical-state store. A saved design-bound snapshot is not interchangeable
   with an arbitrary epoch/observer request.

Existing package-boundary tests protect the broad geometry/projection/domain
separation, but do not enforce all these semantic or internal product barriers.
See the [as-is diagram](kernel_roadmap_v0.9.5.md#current-architecture).

## Current incomplete science and compatibility

Keep implemented planet, Moon, minor-body and satellite functionality during
migration. Incomplete capability is not enabled merely by registering a package.
See [scientific contracts](scientific_contracts.md) for retained resource,
time, provenance, uncertainty, photometry and satellite limitations.
Ancient-calendar input and long-baseline stellar propagation are not currently
supported by the ordinary observer parser.

## Verification and history

Baseline production content passed all 3,606 plugin-disabled Mac tests at
`ea8dc505` before merge; the merge has the identical Git tree. Follow the
[testing policy](testing_policy.md) for subsequent changes. Numerical, visual
and print evidence are different obligations; one does not substitute for another.
Full historical text is retained in the
[baseline archive](archive/pre_kernel_20261017/INDEX.md).
