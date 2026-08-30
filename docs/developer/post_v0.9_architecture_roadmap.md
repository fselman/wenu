# Wenu post-v0.9 architecture roadmap

**Status:** Active; architecture 0.9.5, 49F, and 49G complete; 49H.3 accepted

**Planning baseline:** `52e9411`

**Decision date:** 2026-08-19

## 1. Purpose and authority

This roadmap preserves three future enhancements after the physical
polar-planisphere work:

1. rationalize astronomical coordinates and time-dependent position
   generation for planets, natural satellites, and artificial satellites;
2. make SVG a documented and verified vector-output product;
3. support time sequences in which celestial geometry, the observer horizon,
   and moving phenomena evolve on explicitly different timescales.

It records the active direction and sequencing after the closed v0.9
architecture. Each implementation stage requires a fresh as-is assessment and
its own small, testable milestone.

The coordinate decisions in `coordinate_transformation_audit_09a2afd.md`
remain authoritative scientific input. The longer-term astrometry sequence in
`archive/roadmap_history/polar_delivery_and_astrometry_roadmap.md` is consolidated here so that it no
longer depends on the urgent polar-delivery numbering.

## 2. Two independent development tracks

Post-v0.9 work has two complementary tracks.

### 2.1 Scientific-state architecture

This track owns reference frames, origins, epochs, observation instants, time
scales, physical position status, ephemeris/orbit providers, transformation,
and reusable celestial realization.

### 2.2 Product and output architecture

This track owns supported export formats and time-sequence products. It may
reuse the current canonical static-render pipeline but must not create a
second astronomical, projection, preparation, rendering, furniture, or
export pipeline.

SVG verification can proceed independently. Optimized horizon rotation and
moving-object sequences depend on the scientific-state contracts.

## 3. Preserved architectural boundaries

The canonical flow remains:

```text
catalogue, ephemeris, or orbit provider
    -> explicit astronomical state
    -> astronomical coordinate service
    -> typed spherical geometry in the product frame
    -> coordinate-neutral projection alignment
    -> projection
    -> projected geometry and chart preparation
    -> renderer
    -> furniture and export
```

Position generation and coordinate transformation are different operations.
A provider determines where an object is at an instant. The coordinate
service represents that state in an explicitly requested frame. Projection
alignment remains a coordinate-neutral spherical rotation and rendering
performs no astronomical calculation.

`CelestialSphere.draw_chart()` remains the canonical execution core until an
approved milestone deliberately evolves that public boundary.

## 4. Milestone 49A - Close v0.9 and refresh the as-is audit

- close the physical-planisphere acceptance and documentation;
- record the exact post-v0.9 implementation baseline;
- reconcile the 2026-08-16 coordinate audit with intervening changes;
- inventory every Astropy, Skyfield, handwritten, and chart-owned transform;
- inventory time parsing, UTC offsets, time scales, and observer construction;
- preserve current visual products as regression authorities.

This milestone changes documentation and tests only unless the audit exposes
a correctness defect that must be isolated separately.

## 5. Milestone 49B - Explicit astronomical-state vocabulary

### Milestone 49B.1 — Frozen coordinate vocabulary

**Status:** Accepted and merged in `d63c300`.

Add `CoordinateSpec`, `ObservationContext`, `PositionStatus`, the
structural `PositionProvider` protocol, and the `SphericalGeometry` union.
This milestone changes no numerical transformation, geometry constructor, or
chart output. Attaching coordinate identity to geometry remains 49B.2, and
adapting existing astronomical objects remains 49B.3.

Introduce immutable specifications for:

- reference frame and origin;
- coordinate epoch or equinox where applicable;
- observation instant and time scale where applicable;
- units and representation;
- geometric, astrometric, apparent, or topocentric status;
- provider/model identity and provenance;
- refraction, light-time, aberration, deflection, precession/nutation, and
  Earth-orientation policy when relevant.

Static celestial products resolve an explicit observer-independent product
frame. Local observing products resolve an explicit observer and AltAz
policy. Frame-less astronomical longitude/latitude must not cross the new
public boundary.

### Milestone 49B.2 — Typed spherical geometry

**Status:** Accepted and merged in `db946cc`.

Make `CoordinateSpec` a required keyword-only member of every
`SphericalPoints`, `SphericalCurves`, `SphericalPolygons`, and
`SphericalGrid` record. Every production constructor supplies an explicit
scientific identity; derived geometry preserves or deliberately replaces it,
and grids reject components whose identity differs from the grid identity.
This milestone changes no coordinate values or transformation equations.

### Milestone 49B.3 — Existing position providers

**Status:** Accepted and merged in `2492846`.

Adapt the existing stellar catalogue, non-stellar catalogue centres, and
open-cluster catalogue to the structural `PositionProvider` boundary. Providers
return native ICRS `SphericalPoints`; extended morphology and constructed
reference geometry remain separate. Static catalogues accept but do not use the
optional evaluation instant. No existing rendering path or coordinate
calculation changes.

## 6. Milestone 49C - One astronomical coordinate service

### Milestone 49C.1 — Central transformation service

**Status:** Accepted and merged in `5131500`.

Add one Astropy-backed service accepting every spherical geometry kind and
returning the same kind. Preserve semantic arrays, metadata, segmentation,
rings, grid component names, and closure topology. Support ICRS, Galactic,
barycentric mean ecliptic, and explicit observer-local AltAz transformations.
Do not migrate production callers in this milestone.

- add one Astropy-backed package service for supported astronomical frame
  transformations;
- transform points, curves, polygons, grids, and disconnected geometry while
  preserving identifiers, topology, labels, and provenance;
- keep specialized adapters for states such as TEME where their physical
  transformation path requires them;
- migrate reference grids, planes, poles, and ecliptic keypoints first;
- add spherical coincidence and round-trip tests;
- retire independent `radec_to_altaz()` mathematics after all callers move.

Projection classes must not import astronomical frames or infer them from
longitude/latitude argument names.

### Milestone 49C.2 — Migrate production transformations

**Status:** Accepted and merged in `f42f236`.

The accepted candidate routes reference points and grids, chart compatibility
conversions, deep-sky centres and morphology, constellation labels and
boundaries, observer-keyed caches, circumpolar boundaries, fixed-sky
orientation references, and regional celestial-north orientation through
`CoordinateService`.

Skyfield's Hipparcos apparent topocentric realization remains position-provider
work rather than being replaced by a second Astropy calculation. Constellation
lines reuse that single stellar realization. Native AltAz horizon geometry
also remains direct reference construction; only conversion of that geometry
to a celestial product frame passes through the service.

Acceptance evidence: the routine suite passed 1779 tests with 30 deselected in
26.99 seconds; the complete suite passed 1809 tests in 86.11 seconds; the
49H.3 fixed-sky/rotating-horizon reference frames were visually accepted by
Fernando on 2026-08-28.

### Milestone 49C.3 — Retire compatibility authorities

**Status:** Accepted and merged in `034bdd8`.

Retire `radec_to_altaz()`, remove the chart-owned compatibility wrappers, and
reduce `Observer` to explicit context construction without changing numerical
results or product appearance.

Acceptance evidence: the routine suite passed 1775 tests with 30 deselected in
24.59 seconds; the complete suite passed 1805 tests in 86.29 seconds; the
49H.3 fixed-sky/rotating-horizon reference frames were visually accepted by
Fernando on 2026-08-28.

### Milestone 49C.4 — Accept architecture 0.9.5

**Status:** Accepted and merged in `1a15076`.

The current as-is diagrams were reviewed and accepted. Scientific and topology
checks passed; the routine suite passed 1779 tests with 30 deselected in 27.31
seconds; and the complete suite passed 1809 tests in 84.99 seconds. Fernando
visually accepted both the corrected J2000 equinox intersections in the La
Ligua stereographic planisphere and the final fixed-sky/rotating-horizon
reference on 2026-08-28. Compatibility authorities are absent.

## 6.1 Immediate post-v0.9.5 public-interface follow-up

After the 49C.4 closure merge, audit every executable example and developer
tool before beginning new astronomical-object work:

- make the installed `wenu_chart` command the ordinary public route for every
  reproducible user example;
- reserve `tools/` for diagnostics, audits, benchmarks, migrations, and
  software acceptance rather than user workflows;
- move the physical planisphere demonstration into the examples area once
  `wenu_chart` can reproduce it completely;
- create one examples guide that identifies every supported example, its
  output, and the documented parameters users may adapt;
- expose coordinate system, frame, epoch/equinox, and relevant `of_date`
  policies through validated CLI and configuration values translated into
  `CoordinateSpec`;
- prohibit CLI, example, and tool code from constructing an independent
  astronomical transformation authority.

The public frame/equinox controls require their own small milestone and
scientific acceptance. They do not reopen the accepted internal 0.9.5
coordinate ownership.

### Public celestial reference policy — implemented and accepted

The first recommended slice is implemented and scientifically accepted. One
`CelestialReferencePolicy` carries a J2000, `of_date`, or explicit supported
equinox through ordinary request grids and the coupled celestial equator,
true ecliptic, and seasonal keypoints. The installed command exposes
`--reference-equinox`; schema-version-1 TOML exposes
`[coordinates.references].equinox`. J2000 remains the compatibility default.
Product-frame selection and provider position-epoch propagation remain out of
scope pending separate scientific milestones.

Acceptance used default J2000, explicit J2000.0, J2016.0, and `of_date`
regional SVGs. The default and explicit J2000 requests produced identical
normalized graphical records; J2016.0 and of-date moved the coupled reference
axes without moving apparent stellar directions. The first of-date render
found and closed the missing chart-view observer handoff. Final evidence was
1,786 routine tests passed with 30 deselected in 25.26 seconds and 1,816 full
tests passed in 86.71 seconds.

The completed as-is inventory, executable dispositions, public coordinate
vocabulary, validation constraints, and recommended implementation slices are
recorded in `public_interface_audit_v0.9.5.md`. Arbitrary supported equinoxes
are coordinate-representation requests; arbitrary position epochs remain
provider operations and must be rejected until the relevant provider can
propagate them physically.

## 7. Milestone 49D - Observer-independent celestial realization

### Milestone 49D.1 — Celestial-scene dependency and ownership audit

**Status:** Accepted and merged in `9e16ed2`.

The as-is inventory and minimum planet-enabling scene boundary are recorded in
`celestial_scene_dependency_audit_49d1.md`. It distinguishes the reusable
loaded sphere from its currently observer-bound spherical realizations and
classifies content as celestial background, dynamic astronomical objects, or
observer-local geometry.

All enabled layers must converge in one explicit spherical product frame
before the existing projection and preparation path. A future planet enters
after provider evaluation and coordinate transformation as an ordinary
semantic sky layer; it does not enter through the renderer, furniture, command,
or a parallel scene graph. This audit changes no runtime behavior and
authorizes no caching.

49D.2 may add the smallest immutable layer-realization context and a controlled
test provider while preserving the current
`layer.spherical_geometry(observer, **geometry_options)` compatibility call.
A real ephemeris provider remains Milestone 49E and the first planet remains a
49I vertical slice. Completing every 49D migration is not a prerequisite for
that planet, but this bounded dependency contract prevents the provider from
being attached at the wrong architectural layer.

Fernando accepted the dependency classification, convergence point, insertion
point, and non-goals on 2026-08-29. Verification passed 39 documentation tests
in 2.78 seconds, 1,789 routine tests with 30 deselected in 26.62 seconds, and
all 1,819 tests in 84.41 seconds. No visual comparison was required because
49D.1 changes no production source or runtime output.

### Milestone 49D.2 — Minimal layer-realization context

**Status:** Accepted and merged in `85c7392`.

The exact contract and acceptance requirements are recorded in
`layer_realization_context_49d2.md`. A frozen `LayerRealizationContext`
carries product coordinate identity, optional observation context, a paired
provider evaluation instant/time scale, and an optional resolved reference
equinox. It deliberately carries no projection, appearance, furniture, output,
or cache policy.

`SkyLayer.realize()` is the compatibility adapter to the existing
`spherical_geometry(observer, ...)` call.
`CelestialSphere.draw_chart(..., realization_context=None)` uses the new hook
only when a typed context is explicitly supplied. Ordinary chart requests do
not supply one in 49D.2 and therefore retain the exact existing dispatch.

A deterministic test-only provider and dynamic layer prove evaluation at the
declared instant, one `CoordinateService` transformation into the requested
product frame, preservation of identifiers, and entry through the canonical
projection/rendering path. Real ephemerides, installed moving-object layers,
request/CLI exposure, current-layer migration, and caching remain out of scope.

- realize catalogue stars and deep-sky geometry directly in the canonical
  celestial product frame;
- migrate constellations, boundaries, labels, the Milky Way, and Magellanic
  Clouds;
- remove the celestial-to-AltAz-to-celestial detour from polar and other
  observer-independent products;
- prove that changing observer location or time does not change their
  pre-furniture astronomical geometry;
- establish an immutable reusable celestial-scene or maximal-sphere boundary.

Fernando accepted the context fields, exact legacy compatibility branch,
controlled-provider proof, deferred 49E responsibilities, pedagogical guide,
and canonical SVG path on 2026-08-29. Acceptance evidence is 48 focused tests
in 2.21 seconds, 1,798 routine tests with 30 deselected in 27.61 seconds, and
all 1,828 tests in 90.00 seconds. No visual comparison was required because no
ordinary request can activate the context and production geometry is unchanged.

Gaia may replace or complement Hipparcos only through an explicit catalogue
milestone with provenance, epoch, proper-motion, magnitude, identifier, and
cross-match policies.

## 8. Milestone 49E - Position-provider boundary

### Milestone 49E.1 — Ephemeris-provider contract audit

**Status:** Accepted and merged in `d14ca52`.

The as-is audit and proposed scientific contract are recorded in
`ephemeris_provider_contract_49e1.md`. The existing generic
`PositionProvider.position(instant)` is suitable for native catalogue
spherical directions but cannot by itself preserve the Cartesian state,
target, centre, frame, distance, velocity, time scale, kernel coverage, and
provenance required by solar-system ephemerides.

The proposed boundary separates a **Cartesian state source** from a
**solar-system direction realizer**. The source returns an explicitly identified
Cartesian state. The realizer owns observer-relative geometry, retarded
emission-time evaluation, light-time, aberration, gravitational deflection,
and declared apparent-place policy. Only then does `CoordinateService`
transform the resulting native spherical direction into the requested product
frame.

Fernando accepted the two-stage boundary on 2026-08-30. The accepted 49E.2
direction requires a six-component position-velocity state, exact kernel
identity including SHA-256 and coverage, atomic removal of the unreleased
`PositionStatus.TOPOCENTRIC` abstraction, and one request/session-scoped
resource that may initially reuse the already-open Observer kernel. Venus is
the first 49I.1 body; the Moon follows as the stronger topocentric-parallax
test. Acceptance verification passed all 41 documentation
tests in 3.26 seconds on Fernando's Mac. No visual comparison was required
because the audit changes no runtime code, geometry, or output.

49E.1 changed no runtime type or output. 49E.2 implements the minimal frozen
request/state/provenance contracts; 49E.3 may adapt one installed kernel. The
first charted body remains the separately approved 49I.1 Venus vertical slice.

### Milestone 49E.2 — Minimal ephemeris runtime contracts

**Status:** Scientifically accepted by Fernando on 2026-08-30; ready for integration.

`ephemeris.py` adds frozen `EphemerisResourceIdentity`,
`EphemerisStateRequest`, and complete six-component `EphemerisState` values,
plus the runtime-checkable structural `EphemerisStateSource` protocol. The
resource identity requires provider, model, filename, a structurally valid
SHA-256 digest, coverage and coverage scale, and provenance. No real file is
opened or hashed in this milestone.

The unreleased `PositionStatus.TOPOCENTRIC` member is removed atomically.
Observer origin remains `origin="observer"`; `observer_altaz_spec()` now
requires every caller to declare `position_status`. Observer-transformed
celestial directions use `APPARENT`, while native horizon and AltAz-grid
references use `GEOMETRIC`. A deterministic test-only Venus source proves the
contract shape without installing a kernel
adapter, direction realizer, moving-object layer, or output change.

The exact contract and acceptance requirements are recorded in
`ephemeris_runtime_contracts_49e2.md`. 49E.3 remains responsible for one real
resolved-kernel resource/adapter and numerical validation. Venus remains a
later 49I.1 slice.

Define a protocol for time-dependent position sources before adding their
chart layers.

| Object class | Expected provider state |
| --- | --- |
| stars with space motion | catalogue astrometry with reference epoch and motion |
| Moon and planets | JPL or equivalent barycentric/geocentric ephemeris state |
| natural satellites | planet-centred ephemeris or orbit-model state |
| asteroids and comets | heliocentric or barycentric ephemeris/orbital state |
| artificial satellites | TLE/OMM plus SGP4 TEME state |

Providers compute or propagate states. They do not select charts, transform
through undocumented downstream paths, project, clip, style, or render.

Fernando scientifically accepted the immutable resource/request/state fields,
mandatory velocity, SHA-256 identity boundary, atomic removal of the unreleased
`TOPOCENTRIC` category, and explicit geometric/apparent observer-local
classifications on 2026-08-30. Acceptance evidence is 92 focused tests in 2.72
seconds, 1,821 routine tests with 30 deselected in 25.25 seconds, and all 1,851
tests in 84.12 seconds. No visual comparison was required because numerical
chart geometry and the canonical output path are unchanged.

The same boundary governs every output format. Future solar-system layers must
declare their semantic identity before projection and then use the existing
projection, preparation, Matplotlib renderer, and single exporter for PNG,
PDF, and SVG. The SVG product may serialize the reserved
`solar-system/sun`, `solar-system/moon`, and `solar-system/planets` paths;
it must not recompute moving-object geometry or use a separate SVG-only path.

### Milestone 49E.3 — Borrowed Skyfield ephemeris adapter

**Status:** Scientifically accepted by Fernando on 2026-08-30; integration pending.

`skyfield_ephemeris.py` adapts the already-open `Observer` Skyfield/JPL SPK
resource to `EphemerisStateSource`. Resolution fingerprints the exact BSP
bytes once, separates DE model from filename, and records the conservative
common SPK-segment coverage in TDB. Evaluation supports explicit geometric
ICRF target-minus-centre states in AU and AU/day with NAIF identifiers.

The adapter borrows but does not open, download, or close the kernel. Unknown
targets, unsupported frames, and coverage failures are explicit. The
deterministic tests use fake SPK structures; the controlled
`validate_49e3_skyfield_adapter.py` check refuses downloads and compares all
six Venus-relative-to-SSB components with direct Skyfield evaluation at a
fixed TDB instant.

The controlled Mac run identified the exact `de440s.bsp` bytes as
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`,
resolved NAIF 299 relative to NAIF 0, and obtained zero adapter/direct residual
within `1e-15` for all six components at the fixed TDB instant.

The exact contract is `skyfield_ephemeris_adapter_49e3.md`. This milestone
adds no direction realizer, chart layer, CLI/TOML control, or output change.
Venus rendering remains 49I.1 and must use the canonical PNG/PDF/SVG path.

Acceptance evidence is 72 focused tests in 1.73 seconds, 1,830 routine tests
with 30 deselected in 25.80 seconds, and all 1,860 tests in 84.78 seconds.
Fernando accepted the scientific boundary after the installed DE440 comparison
reported zero residual within `1e-15` for all six components.

Fernando also accepted living coordinate-guide version
`0.9.5.20260830.3` after MacDown verification of its separate-line header and
all explicit table-of-contents anchors. The final documentation gate passed
all 44 tests in 1.70 seconds.

### Milestone 49E.4 — Solar-System direction-realizer audit

**Status:** Scientifically accepted by Fernando on 2026-08-30; ready for integration.

The proposed contract is recorded in
`solar_system_direction_realizer_49e4.md`. It separates the retarded-emission
light-time solution that produces an astrometric observer-relative direction
from the later aberration and gravitational-deflection operation that produces
an apparent direction. Reception instant, retarded emission instant, distance,
one-way light time, iteration policy, observer state, and exact ephemeris
resource identity remain explicit.

The first runtime slice is 49E.5 astrometric Venus direction realization,
validated against direct Skyfield. 49E.6 adds explicit apparent-place policy;
49I.1 remains the first drawable Venus layer. The Moon follows as the stronger
topocentric-parallax test. 49E.4 changes no runtime type or output.

Fernando accepted the observer-state, retarded-emission, astrometric/apparent,
frame, timing, provenance, Venus-first, and canonical output boundaries on
2026-08-30. Verification passed all 45 current-documentation tests in 2.03
seconds. No visual comparison was required because the milestone changes no
runtime geometry or product.

## 9. Milestone 49F - SVG product verification

**Status:** Complete at `c70cb29` after eight-product cross-product acceptance.

The detailed as-is audit, product contract, font policy, verification matrix,
2D/3D boundary, constellation-artwork relationship, and implementation stages
are recorded in `archive/milestone_history/49f_svg/svg_output_audit_and_plan.md`.

Wenu already reaches Matplotlib's SVG backend when an `.svg` output path or
configured SVG extension is selected. This milestone promotes that incidental
capability into a supported product contract; it does not begin by creating a
new renderer.

SVG is a 2D publication and editing product, not Wenu's internal celestial
scene or the interchange format for future Wenu3D output. Wenu 1.0 should leave
renderer-neutral astronomical and semantic state that both 2D charts and a
later 3D realization can consume. glTF/GLB is the likely initial portable 3D
delivery format to evaluate independently. SVG may also serve as source artwork
when paired with separate celestial registration.

- document SVG in the CLI, configuration, implementation reference, and user
  guide;
- export representative all-sky, regional, binocular, circumpolar, and polar
  products through the canonical workflow;
- verify physical dimensions, view boxes, clipping, transparency, masks,
  symbols, lines, labels, legends, and furniture;
- define the font policy: retained text versus paths and font portability;
- detect unexpected raster image payloads;
- compare SVG geometry and appearance with the atlas-print baseline;
- add deterministic structural tests without snapshotting irrelevant backend
  serialization details.

A dedicated SVG renderer is considered only if this verification identifies
a concrete requirement that Matplotlib's backend cannot meet.

## 10. Milestone 49G - Temporal sequence contract

**Status:** 49G.1 immutable timeline and playback vocabulary implemented.

**Status:** 49G.2 observer-time sequence orchestration and real-render
acceptance complete.

**Status:** 49G.3 deterministic manifest and restart/resume policy
implemented and accepted.

**Status:** 49G.4 installed CLI and schema-version-1 configuration exposure
implemented and accepted; scientifically keyed reuse remains pending.

The implemented contracts are documented in
`archive/milestone_history/49g_temporal/temporal_sequence_contract_49g1.md`,
`archive/milestone_history/49g_temporal/observer_time_sequence_49g2.md`,
`archive/milestone_history/49g_temporal/sequence_manifest_49g3.md`, and
`archive/milestone_history/49g_temporal/temporal_sequence_cli_49g4.md`.

Represent a sequence as one immutable product definition plus an ordered set
of explicit instants. Separate state by its physical cadence:

| Change | Reusable or recomputed state |
| --- | --- |
| Earth rotation over hours | celestial sphere reusable; local horizon and AltAz realization change |
| planet motion over days or months | background sphere reusable; provider states change |
| artificial-satellite motion over seconds or minutes | background sphere reusable; orbit propagation and local transform change rapidly |
| proper motion or precession over years or centuries | catalogue/frame realization changes under an explicit epoch policy |
| appearance-only changes | astronomical and projected geometry remain reusable where valid |

The request must distinguish simulation time, display/civil time, time zone,
UTC offset, time scale, sampling interval, playback duration, and frames per
second. Presentation speed must never be mistaken for physical time.

## 11. Milestone 49H - Fixed sky and rotating horizon

**Status:** 49H.1 fixed celestial-anchor and frame-local observer planning
contract implemented.

**Status:** 49H.2 complete-render circumpolar baseline implemented,
visually characterized, and accepted as the record of prior behavior.

**Status:** 49H.3 renderer-neutral anchor transformation, canonical uncached
reference rendering, geometry proof, and visual acceptance complete. The
celestial scene remains fixed while the horizon and AltAz grid rotate.
Scientifically keyed reuse remains pending.

The ownership, baseline, and accepted reference contracts are documented in
`archive/milestone_history/49h_fixed_sky/fixed_sky_rotating_horizon_49h1.md`,
`archive/milestone_history/49h_fixed_sky/fixed_sky_complete_render_baseline_49h2.md`, and
`archive/milestone_history/49h_fixed_sky/fixed_sky_reference_rendering_49h3.md`.

Use the temporal contract to support the Earth-rotation presentation:

- stars, constellation geometry, and celestial reference grids remain fixed
  in their celestial frame;
- observer-local horizon, cardinal directions, AltAz grid, visibility, and an
  optional landscape/Earth mask change with time;
- chart projection and camera remain explicit and stable unless the product
  requests otherwise;
- cache only values whose frame, epoch, instant, observer, and product policy
  prove them reusable;
- compare frames against complete independent renders within declared
  scientific and graphical tolerances.

The existing `tools/render_circumpolar_movie.py` remains the reference
implementation: it changes observer time, performs complete canonical static
renders, and assembles PNG frames with FFmpeg. The optimized implementation
must reproduce that baseline rather than bypass the canonical pipeline.

## 12. Milestone 49I - Moving-object vertical slices

Add one object class at a time:

1. Moon or one planet through an ephemeris provider;
2. a natural satellite if its provider contract differs materially;
3. one artificial satellite through an independently validated SGP4/TEME to
   observer-local path.

Each slice must test provenance, time scale, origin, coordinate status,
transformation, visibility, labels, trails where requested, and repeatable
sequence output before the next class begins. It must also verify that PNG,
PDF, and semantic SVG consume the same projected moving-object records, with
stable upstream object identity and the appropriate reserved
`solar-system` semantic path; no post-export overlay is acceptable.

## 13. Milestone 49J - Performance and closure

- benchmark complete independent frames before optimizing;
- measure catalogue loading, provider evaluation, transformation, projection,
  preparation, rendering, and encoding separately;
- cache by explicit immutable scientific keys rather than mutable global
  state;
- retain the complete-render path as a correctness oracle;
- update current architecture, implementation reference, source tree, user
  documentation, and examples;
- close or supersede this roadmap only after focused, full, scientific, SVG,
  visual, and sequence tests pass.

## 14. Stop conditions

Stop and re-audit if a proposed milestone would:

- create a second celestial-sphere, projection, rendering, or export path;
- let a renderer or projection choose an astronomical frame;
- treat TEME, Earth-fixed, AltAz, FK4/FK5, ecliptic, or Galactic coordinates
  as ICRS by relabelling;
- hide time scale, origin, observer, refraction, or apparent/geometric status;
- make observer-independent geometry depend silently on observer time;
- optimize frames before a complete-render reference and benchmark exist;
- couple SVG output to different astronomical geometry.

## 15. Completion definition

The post-v0.9 program is complete when Wenu has one governed astronomical
state and transformation architecture, documented and verified SVG output,
and reproducible time sequences that reuse scientifically invariant state
while correctly recomputing observer-local and moving-object phenomena.
