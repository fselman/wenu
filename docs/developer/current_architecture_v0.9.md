# Wenu current architecture

**As-is baseline:** `6708f54a0d8984c0be348b2c8cb02b311646a02b` (2026-10-17).
This document describes implemented behavior. The proposed kernel and package
architecture lives separately in the [roadmap](kernel_roadmap_v0.9.5.md).

The separate [K2 kernel project](../../packages/wenu_kernel/README.md)
implements immutable direction records, explicit registration and synchronous
sessions, reproducible certified direction reuse and SI Cartesian full-model
states with optional velocity and separate uncertainty channels. Explicit
time-adapter admission, conversion receipts and bounded TT(TAI)/TAI conversion
remain separate from same-scale native state queries. A reusable stdlib
provider conformance kit verifies an external consumer with no repository fixtures.
The SDK has no runtime dependencies. Accepted PR #247 makes it a
separate Wenu dependency and routes native stellar realization through it.
Other state consumers and the SDK freeze remain pending. The canonical
projection and rendering pipeline is retained.

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
Wenu now depends on the separate `wenu-kernel` distribution. The astronomical
directories inside Wenu are not yet independent loadable packages.

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
not precess. The native position/realization routes now consistently declare
source epoch J1991.25; the former default J2000.0 metadata was incorrect.
No Gaia astrometric provider exists.

Native `Stars.realize()` now selects rows with the existing policy and obtains
finite directions from `stellar_state.LegacyNativeStellarProvider` through
`KernelSession.evaluate`. Returned kernel vectors supply the geometry; kernel
failures propagate. Cold skies and saved `_SnapshotStars` inherit this route.
The adapter is a source-native lookup, with J1991.25(TT) source epoch and
explicitly unknown errors, not a proper-motion or zero-motion model.
Missing-coordinate rows retain their legacy metadata/NaNs outside kernel
states for downstream filtering. No acquisition occurs during evaluation.
`Stars.position()` uses the same helper. `Stars.native_positions(identifiers)`
looks up explicit HIP identities in source order, independently of marker
magnitude selection. Native constellation lines consume only that public
interface and join returned IDs to their curated topology, including faint
vertices; they no longer read catalogue coordinates themselves. Saved stars
inherit both APIs. `stellar_catalogue.py` validates source metadata before
publication and mirrors it in an immutable record. Epoch/edition/provenance come
from the data document; native labels inherit the stellar specification too.
Snapshot v3 preserves that metadata; source-bound legacy v1/v2 admission remains
explicit. The metadata audit records remaining nonstellar and resource defects.
Open-cluster geometry now mirrors preserved row epochs/source lineage and source
metadata; a selected uniformly known epoch is scalar, otherwise it is explicitly
unknown at collection level. Snapshot v4 validates that header and restores older
bundles from their row facts. Nonstellar ingestion now preserves source table
metadata/unconsumed columns and converts declared angular units before atomic
publication. Geometry mirrors catalogue metadata; the existing snapshot table
transport retains it. Unitless inputs remain a legacy compatibility path;
full frame/epoch admission and other nonstellar snapshot epoch stamps remain open.
Observed Skyfield astrometry,
native constellation-label anchors and other families remain unmigrated. See the
[adapter contract](implementation_reference.md#native-stellar-kernel-adapter).
Solar-System Cartesian resources, state requests and astrometric/apparent
direction realizers have stronger typed contracts. They solve light time
separately from apparent corrections. These facilities must be reused rather
than reimplemented in a new kernel.

## Abstraction barriers that remain incomplete

1. `CelestialSphere` and `maximal_sphere` know concrete layer classes. There is
   no uniform registry behind all epoch-state consumers; only native stellar
   realization, public native positions and native line vertices currently use
   the SDK registry.
2. `SkyLayer.realize()` has a legacy fallback that discards the context and
   calls `spherical_geometry(observer)`. Physical state and observation are
   therefore not uniformly separated.
3. Frozen coordinate metadata does not make every geometry result immutable:
   general arrays, dictionaries and layer collections remain mutable.
4. Request preparation temporarily installs layers and rebinds resolvers.
   Minor-body registration/alias and atomic resolver rollback is accepted in
   PR #243. PR #244 adds a synchronous request-state journal
   around ordinary request preparation. It restores original layer identities
   and order, horizon/disk aliases and point-label flags on close or failure;
   overlapping builds on one mutable sky fail before configuration. Failed cleanup
   retains the lease; a returned build can retry close before another request. Configuration
   owners explicitly remember their writes; direct standalone configuration
   calls retain their persistent semantics. Catalogues/resources/scientific
   caches are not cloned or rewound. This is isolation of canonical request
   configuration, not thread safety, arbitrary caller mutations or kernel routing.
   `open_chart_request_scope()` now gives ordinary generation, direct
   `charts/drawing.py` execution and native atlas sheets the same entry/cleanup
   owner. The view path preserves its prepared geometry and helper order while
   journaling writes through `ChartRequestBuild.remember_attribute`. Native
   sheets acquire the lease without an observer or ordinary configuration.
   Their export pages use an owned offscreen Agg canvas at fixed 100-dpi layout
   resolution. This isolates grid-label measurements from GUI/display scaling;
   the requested raster export dpi remains a separate output setting.
   Atlas API/worker execution defaults to `wenu_chart atlas-sheet`, removing
   the direct-generator fallback. This accepted lifecycle change is distinct
   from the current native stellar kernel adapter.
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
