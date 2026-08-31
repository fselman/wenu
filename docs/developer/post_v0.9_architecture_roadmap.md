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

### Milestone 49E.5 — Astrometric direction runtime

**Status:** Scientifically accepted by Fernando on 2026-08-30; ready for integration.

`solar_system_directions.py` implements frozen observer-state, request, and
result contracts plus a bounded one-way-light-time realizer. The observer is
evaluated once at reception; the target is repeatedly requested from the
existing `EphemerisStateSource` at retarded emission times. The result retains
ICRS `SphericalPoints`, distance, light time, both instants, iteration evidence,
observer/target identity, and exact resource provenance.

`skyfield_observer_barycentric_state()` borrows the same Observer kernel as the
49E.3 source and evaluates Earth plus the WGS84 site. Deterministic tests and a
no-download installed-DE440 Venus comparison protect the boundary. 49E.5 adds
no apparent-place correction, moving-body layer, command, projection,
renderer, or output change. 49E.6 remains apparent direction realization and
49I.1 remains the first drawable Venus.

The installed DE440 Venus comparison converged in four iterations and agreed
with direct Skyfield to `3.149e-11` degree in right ascension,
`1.544e-12` degree in declination, `1.348e-12` AU in distance,
`7.783e-15` day in light time, and `7.994e-15` day in emission time.
Fernando scientifically accepted 49E.5 on 2026-08-30. Verification passed 111
focused tests in 4.33 seconds, 1,848 routine tests with 30 deselected in 27.03
seconds, and all 1,878 tests in 85.55 seconds. No visual render was required.

### Milestone 49E.6 — Apparent direction runtime

**Status:** Scientifically accepted by Fernando on 2026-08-30; ready for integration.

`ApparentCorrectionPolicy`, `ApparentDirection`, and
`SkyfieldApparentDirectionRealizer` apply declared gravitational deflection and
aberration to the accepted 49E.5 result. The realizer reconstructs the retained
astrometric vector and calls `apparent()` without calling `observe()` or solving
light time a second time. 49E.5 now retains its already-computed relative
velocity so that this handoff is complete.

The output remains observer-origin, apparent, and ICRS-oriented. Its reception
instant is neither a position reference epoch nor an equinox; apparent status
does not select an equinox of date. Deterministic tests and the no-download
installed-kernel Venus comparison protect the boundary. 49E.6 creates no
moving-body layer or output change. 49I.1 remains the first drawable Venus and
must use the canonical shared PNG/PDF/SVG path.

The installed DE440 Venus comparison produced apparent ICRS coordinates
`198.3663730463236`, `-11.16330410839704` degrees and agreed with direct
Skyfield to `3.152e-11` degree in right ascension and `1.544e-12` degree in
declination. Fernando scientifically accepted 49E.6 on 2026-08-30 after 95
focused tests in 3.79 seconds and all 1,883 tests in 91.21 seconds passed.

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

### Milestone 49I.1 — Drawable Venus vertical slice

**Status:** Scientifically and visually accepted; completed through 49I.1B and
merged in `e7fa6ab` on 2026-08-30.

The as-is audit is recorded in `venus_vertical_slice_audit_49i1.md`. The
accepted 49E.3–49E.6 provider/direction chain is ready, but ordinary chart
facades do not yet supply the 49D.2 `LayerRealizationContext`. 49I.1 therefore
has two bounded steps: 49I.1A threads one output-neutral product-frame context
through every canonical chart family; 49I.1B adds one opt-in semantic Venus
layer that transforms the accepted apparent direction exactly once before
projection.

The proposed public selector is `--planet venus`. The initial Venus is a
symbolic marker with optional label, not a physical disk. Phase, magnitude,
angular diameter, trails, the Moon, and other bodies remain later work. PNG,
PDF, and SVG must consume the same projected record, with upstream semantic
path `sky/solar_system/planets/venus` and no post-export overlay.

Fernando scientifically and architecturally accepted this audit on
2026-08-30 after all 48 current-documentation tests passed in 3.30 seconds.
The next bounded implementation is 49I.1A; acceptance of the audit does not
pre-accept the output-neutral runtime handoff or the later Venus chart.

#### Milestone 49I.1A — Ordinary realization-context handoff

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-30; ready for integration.

`chart_request_realization_context()` now constructs one immutable
`LayerRealizationContext` before a declarative request's product loop. The
common export workflow and every canonical chart facade pass it to
`CelestialSphere.draw_chart()`. Existing layers use the accepted compatibility
adapter and retain their exact `spherical_geometry()` call.

The current ordinary product vocabulary maps planisphere, regional,
circumpolar, and binocular to observer-local AltAz, and all-sky to
observer-origin Galactic coordinates. The separately resolved reference
equinox remains context metadata; it is not assigned to either frame. 49I.1A
adds no Venus layer or visible output change. Acceptance verification passed
166 focused tests, 1,859 routine tests with 30 deselected, and all 1,890 tests.
The next bounded implementation after integration is 49I.1B, the opt-in Venus
layer.

#### Milestone 49I.1B — First drawable Venus layer

**Status:** Scientifically and visually accepted by Fernando and merged in
`e7fa6ab` on 2026-08-30.

The opt-in `VenusLayer` now consumes the accepted 49E.3–49E.6 direction chain
through the 49I.1A context and transforms once into the product frame. Public
selection is `--planet venus`; default charts remain unchanged. The same
projected point feeds PNG, PDF, and semantic SVG. Physical appearance remains
explicitly deferred. Scientific, numerical, semantic-SVG, and visual
acceptance passed. The 148-test implementation review and 35-test focused
post-correction regression passed, followed by all 1,898 tests in 82.01
seconds. Fernando confirmed that Venus agrees with Stellarium at the declared
La Ligua observation instant and that PNG, PDF, and SVG look the same. The SVG
run additionally exposed and closed a signed Green-catalogue semantic-key
collision without weakening hierarchy validation.

#### Milestone 49I.2 — Moon and shared solar-system-body pipeline

**Status:** Scientifically and architecturally accepted by Fernando and merged
in `fbf4dd9` on 2026-08-30.

`moon_shared_body_pipeline_audit_49i2.md` tests the single-pipeline goal
against the merged Venus implementation. The target is one typed downstream
path with interchangeable geometric-state sources and body-appearance
strategies, not one hard-coded algorithm pretending that JPL planets, orbital
elements, comets, and TEME satellites are scientifically identical.

The proposed sequence is 49I.2A Moon numerical direction validation, 49I.2B
shared renderer-neutral point-layer extraction with exact Venus parity, and
49I.2C the first opt-in drawable Moon point. Physical disk, phase,
illumination, angular diameter, and limb orientation remain 49I.3. The audit
adds no runtime or output change.

Fernando accepted all four audit decisions on 2026-08-30 after all 51
current-documentation tests passed in 1.88 seconds. The next bounded
implementation is 49I.2A Moon numerical direction validation; this acceptance
does not pre-accept its correction policy or numerical results.

##### Milestone 49I.2A — Numerical Moon-direction validation

**Status:** Scientifically accepted and full-suite verified; ready for
integration.

The existing provider-neutral astrometric and apparent direction machinery is
now exercised with target `moon`/NAIF 301 in deterministic tests. All 102
focused tests passed in 1.99 seconds, and all 1,902 tests passed in 89.59
seconds. The installed-DE440 validator agreed with
direct Skyfield to 0.1503 mas in right ascension and 0.0624 mas in declination,
measured 0.9500231004-degree topocentric-geocentric parallax, and measured a
27.91-mas displacement between the 52 m observer and zero elevation. Fernando
accepted the result and the `1e-7`-degree component tolerance. No Moon layer,
public option, shared point abstraction, or output change is added.

##### Milestone 49I.2B — Shared Solar-System point layer

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-30; ready for integration.

`SolarSystemPointDescriptor` now freezes body target, centre, selection and
entity keys, display name, and explicit apparent-correction policy.
`SolarSystemPointLayer` owns the shared renderer-neutral orchestration through
one product-frame transformation. Venus is migrated to a thin specialization;
a test-only Moon descriptor proves reuse without installing Moon content.
Current verification passed 13 direct tests in 1.86 seconds, 82 focused tests
in 1.82 seconds, and 1,881 routine tests with 30 deselected in 27.67 seconds.
Documentation verification passed 53 tests in 2.16 seconds and the complete
suite passed all 1,912 tests in 91.04 seconds. Main-versus-branch Venus parity
was exact: byte-identical PNG, zero differing PDF raster pixels, and identical
normalized SVG semantic and graphical content. Fernando scientifically and
architecturally accepted 49I.2B and its stated non-goals on 2026-08-30.

##### Milestone 49I.2C — First drawable Moon point

**Status:** Scientifically, architecturally, and visually accepted by Fernando
on 2026-08-30; ready for integration.

A frozen Moon descriptor now specializes the accepted shared point layer.
Class-aware `--planet venus` and `--moon` inputs converge into one internal
`solar_system_objects` selection, while the Moon retains the stable
`sky/solar_system/natural_satellites/moon` identity. Verification passed 89
direct tests, 219 broader architectural tests, 1,887 routine tests with 30
deselected, all 1,917 tests, and 54 documentation tests. Installed-DE440
PNG/PDF/SVG products agreed visually, and the correctly time-matched Stellarium comparison placed the Moon
closely against the same Pisces stars. Fernando scientifically,
architecturally, and visually accepted 49I.2C and its stated non-goals on
2026-08-30. Physical disk and phase remain 49I.3.


##### Milestone 49I.2D — Solar-System trajectory contract

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-31; ready for integration.

`solar_system_track_audit_49i2d.md` defines a shared, time-parameterized path
before physical-disk work. The proposed request names one body, a start instant,
a curve-sampling cadence, a major-tick cadence, and a tick count. Each sample
reevaluates the observer and body at its own physical reception instant, while
the assembled celestial path is transformed once into the fixed product frame
of the static chart. This distinction shows motion against the chart's stellar
field instead of tracing the Earth's rotation.

The completed path must become one ordinary `SphericalCurves` value before
projection. Existing vectorized coordinate transformation, projection-domain
guards, projection, clipping, renderer, and PNG/PDF/SVG export remain
authoritative. Exact major-time anchors remain scientific metadata; visible
perpendicular ticks and the starting-date label are constructed after
projection because they are page-space annotations.

The first proposed runtime target is one Venus track in regional and binocular
charts. Planisphere and all-sky tracks, multiple simultaneous CLI track
specifications, adaptive cadence, provider batching, physical disks, phase,
photometry, and visible output are not part of this audit. Proposed runtime
slices remain separately authorized; 49I.3 remains the physical
apparent-disk contract.

Fernando accepted the time semantics, fixed-frame meaning, ordinary
`SphericalCurves` reuse, exact tick anchors, projected tick ownership,
regional/binocular first scope, proposed CLI vocabulary, and non-goals.
Verification passed 55 documentation tests, 1,889 routine tests with 30
deselected, and all 1,919 tests. No visual comparison was required because
49I.2D changes no runtime source or output. Runtime slices remain separately
authorized.

###### Milestone 49I.2D.1 — Scientific Solar-System track curve

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-31; ready for integration.

`solar_system_track_curve_49i2d1.md` adds frozen sampling request/result
contracts and one renderer-neutral realizer. The accepted scalar
astrometric/apparent chain is reevaluated at every sample instant, exact
major-time anchors are merged into the cadence, and complete per-sample
evidence is retained. The apparent ICRS-oriented samples become one open
`SphericalCurves`, followed by exactly one transformation into the fixed
chart product frame.

The first validator uses installed DE440 for a 28-day La Ligua Venus path and
compares every retained apparent direction with direct Skyfield. 49I.2D.1 adds
no public command, registered layer, projected tick, style, label, semantic
SVG path, or visible output. Drawable Venus tracks remain 49I.2D.2 and require
separate authorization.

Fernando accepted 49I.2D.1 after the installed-DE440 29-sample Venus validator
agreed with direct Skyfield to `4.293e-10` degree in right ascension and
`8.471e-11` degree in declination. Verification passed 40 focused tests, 56
documentation tests, 1,899 routine tests with 30 deselected, and all 1,929
tests. No visual comparison was required because the slice cannot draw a
chart. 49I.2D.2 remains separately authorized.



### Milestone 49I.3A — Physical apparent-disk contract audit

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-31; ready for integration.

`physical_apparent_disk_audit_49i3a.md` separates the accepted apparent
centre direction from a future renderer-neutral physical-appearance state.
Physical angular diameter, illuminated fraction, bright-limb position angle,
body orientation, photometry, and display magnification remain distinct
quantities with distinct owners.

Default planets remain symbolic objects. Honest integration with the stellar
magnitude hierarchy requires a validated apparent-magnitude model; the current
fixed hollow Venus and Moon markers remain explicitly provisional until that
work. Regional and binocular charts may later opt into resolved disks.
Planisphere and all-sky charts retain symbols in the first slices.

Resolved disks must be explicit semantic geometry before projection, not
enlarged scatter markers or post-export overlays. Display magnification is a
positive, bounded, object-specific presentation factor and never changes the
recorded physical angular diameter, apparent centre, or visibility.

The proposed sequence is 49I.3B Venus physical-appearance state, 49I.3C first
resolved Venus disk, 49I.3D symbolic photometry and planet glyphs, 49I.3E Moon
physical-appearance state, and 49I.3F first resolved Moon disk. The ordering of
49I.3C and 49I.3D remains a review choice. 49I.3A changes no runtime or output.


Fernando accepted all eight audit decisions on 2026-08-31. Initial acceptance
verification passed 58 current-documentation tests in 2.51 seconds. Final
verification passed 58 current-documentation tests in 1.95 seconds, 1,926
routine tests with 30 deselected in 28.95 seconds, and all 1,956 tests in 91.38
seconds. This acceptance authorizes
the separately bounded 49I.3B numerical Venus appearance-state milestone; it
does not pre-accept that model, its tolerances, runtime API, or visible output.


#### Milestone 49I.3B — Venus physical-appearance state

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-31; integration verification in progress.

`venus_physical_appearance_49i3b.md` adds one frozen renderer-neutral
`SolarSystemApparentDisk` and realizer. The accepted retarded Venus direction
remains the centre and distance authority. JPL's 6051.8-km mean Venus radius
sets physical angular diameter; the Sun–target–observer phase angle sets the
spherical illuminated fraction; and the bright-limb direction is measured
from celestial north toward east in the apparent ICRS tangent plane.

Installed DE440 at La Ligua on 2026-08-30 gives 29.287846514361 arcsec angular
diameter, 101.448595072558 degrees phase angle, 0.400755659841 illuminated
fraction, and 295.354967208388 degrees bright-limb position angle. The same
tangent direction is 185.355190511946 degrees from the local zenith toward
increasing azimuth, confirming that 49I.3C must transform it rather than use it
as a page rotation.

Direct-Skyfield residuals are 6.927e-11 arcsec in diameter, 1.353e-10 degree
in phase, -1.158e-12 in illuminated fraction, and 2.080e-11 degree in
bright-limb angle. Fernando accepted the model, conventions, calibrated
comparison tolerances, values, and output-neutral boundary after all 9
deterministic appearance tests passed in 1.38 seconds. 49I.3B adds no layer,
disk geometry, display magnification, request, style, or visible output.
49I.3C remains separately authorized.

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

## Milestone 49I.2D.2 — Drawable Venus track

**Status:** Scientifically, architecturally, and visually accepted on
2026-08-31.

Regional and binocular requests now expose one Venus track through the accepted
fixed-frame spherical curve, ordinary projection, projected perpendicular
ticks, and shared output path. Optional dates use two chronological layouts
starting from opposite perpendicular sides and retain one side until curve,
label, or viewport obstruction justifies switching. The accepted colour is
amber orange `#FFB000`. A sixteen-week La Ligua stress test and all 1,955
tests passed. Physical apparent disks remain 49I.3.
