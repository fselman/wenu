# Wenu post-v0.9 architecture roadmap

**Status:** Active; architecture 0.9.5, 49F, and 49G complete; 49H.3 accepted

**Planning baseline:** `52e9411`

**Decision date:** 2026-08-19


## Current forward roadmap

This is the single active sequence after merge commit `b877a74`. Completed
milestone detail belongs in `archive/`; the historical sections below retain
architectural rationale and accepted boundaries.

| Order | Milestone | Outcome |
|---:|---|---|
| 1 | 50A.5D.1B | Observer-dependent sampled Horizons comet model magnitude, explicitly not a visibility prediction. |
| 2 | 50A.5D.3 | Renderer-neutral text and JSON moving-object reports from already realized temporal results. |
| 3 | 50A.5E.0 | Audit the distributable Wenu asteroid/comet database, scientific representation, provenance, coverage, and lifecycle. |
| 4 | 50A.5E.1 | Build and verify a versioned distributable database, including important minor bodies and all governed dwarf planets. |
| 5 | 50A.5E.2 | Add the `wenu-database` policy and default cache → provider → database resolution order. |
| 6 | 50A.5E.3 | Add safe cache inspection, dry-run, pruning, and explicit minor-body cache flushing. |
| 7 | 50A.6 | Close minor-body provenance, public interfaces, validation, documentation, and PNG/PDF/SVG acceptance. |
| 8 | 50S.0 | Accepted satellite catalogue, provider, crossing, acceleration, illumination, photometry, and validation decisions. |
| 9 | 50S.1 | Define the provider-neutral satellite crossing domain. |
| 10 | 50S.2 | Add the policy-compliant cached SatChecker crossing adapter. |
| 11 | 50S.3A | Audit honest sampled-candidate reports, shared-path drawing, and semantic identity. |
| 12 | 50S.3B | Implement deterministic reports and drawable sampled-candidate tracks. |
| 13 | 50S.4A | Audit snapshot, dependency, propagation, Earth-orientation, validation, and specimen contracts. |
| 14 | 50S.4B | Add canonical OMM elements and a small immutable synthetic snapshot. |
| 15 | 50S.4C | Add Vallado-validated SGP4 propagation and typed geometric TEME state. |
| 16 | 50S.4D | Add and independently validate the explicit topocentric transformation chain. |
| 17 | 50S.4E | Add the network-free propagated-specimen builder and close 50S.4. |
| 18 | 50S.5 | Implement the complete local FoV-crossing oracle. |
| 19 | 50S.6A–D | Accepted conservative selection and bounded exact-solver coordination. |
| 20 | 50S.6E | Audit same-observer, airmass-bounded multi-FoV reuse, interchange, and the remaining delivery sequence. |
| 21 | 50S.6F | Implement the bounded multi-FoV coordinator after separate acceptance. |
| 22 | 50S.6G | Admit representative scale and connect exact results to generic reports and chart tracks. |
| 23 | 50S.6H | Audit Paranal, ELT, and other observatory planning adapters. |
| 24 | 50S.7 | Add Sunlight, solar Earthshine, Moonlight, Lunar-Earthshine, shadow-transition, and night geometry. |
| 25 | 50S.8 | Add component-resolved brightness models with uncertainty and explicit unknowns. |
| 26 | 50S.9 | Estimate detector-level trail contamination separately from apparent magnitude. |
| 27 | 50S.10 | Produce night/season/sky-position statistics and close the satellite program. |
| 28 | 50B.0 | Review accepted publication, printing, typography, accessibility, and atlas practice. |
| 29 | 50B.1 | Adopt Wenu physical-output profiles and numerical publication standards. |
| 30 | 50B.2 | Measure representative products at declared physical dimensions. |
| 31 | 50B.3 | Implement monochrome and limited-grayscale publication profiles. |
| 32 | 50B.4 | Perform physical print, reduction, grayscale, and photocopy acceptance. |
| 33 | 50B.5 | Close publication styles with accepted standards, examples, limitations, and evidence. |

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

The coordinate decisions in `archive/audits/coordinate_transformation_audit_09a2afd.md`
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
recorded in `archive/audits/public_interface_audit_v0.9.5.md`. Arbitrary supported equinoxes
are coordinate-representation requests; arbitrary position epochs remain
provider operations and must be rejected until the relevant provider can
propagate them physically.

## 7. Milestone 49D - Observer-independent celestial realization

### Milestone 49D.1 — Celestial-scene dependency and ownership audit

**Status:** Accepted and merged in `9e16ed2`.

The as-is inventory and minimum planet-enabling scene boundary are recorded in
`archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md`. It distinguishes the reusable
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
`archive/milestone_history/49d_scene/layer_realization_context_49d2.md`. A frozen `LayerRealizationContext`
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
`archive/milestone_history/49e_ephemeris/ephemeris_provider_contract_49e1.md`. The existing generic
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
`archive/milestone_history/49e_ephemeris/ephemeris_runtime_contracts_49e2.md`. 49E.3 remains responsible for one real
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

The exact contract is `archive/milestone_history/49e_ephemeris/skyfield_ephemeris_adapter_49e3.md`. This milestone
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
`archive/milestone_history/49e_ephemeris/solar_system_direction_realizer_49e4.md`. It separates the retarded-emission
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

The as-is audit is recorded in `archive/milestone_history/49i_solar_system/venus_vertical_slice_audit_49i1.md`. The
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

`archive/milestone_history/49i_solar_system/moon_shared_body_pipeline_audit_49i2.md` tests the single-pipeline goal
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

`archive/milestone_history/49i_solar_system/solar_system_track_audit_49i2d.md` defines a shared, time-parameterized path
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

`archive/milestone_history/49i_solar_system/solar_system_track_curve_49i2d1.md` adds frozen sampling request/result
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

`archive/milestone_history/49i_solar_system/physical_apparent_disk_audit_49i3a.md` separates the accepted apparent
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

`archive/milestone_history/49i_solar_system/venus_physical_appearance_49i3b.md` adds one frozen renderer-neutral
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
deterministic appearance tests passed in 1.38 seconds. Final verification
passed 116 focused architectural tests in 4.73 seconds, 1,936 routine tests
with 30 deselected in 27.32 seconds, and all 1,966 tests in 89.97 seconds.
49I.3B adds no layer,
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

### Milestone 49J.0 — Performance and closure audit

**Status:** Architecturally accepted and regression-verified on 2026-09-02; ready for integration.

`archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md`
distinguishes the existing
reusable-sphere diagnostic from the required cold independent-frame oracle. It
freezes mutually exclusive wall-time spans for resource loading, provider
evaluation, transformation, projection, preparation, rendering, and encoding;
requires immutable scientific cache keys; and retains complete rendering as
the correctness authority.

Fernando subsequently requested that current accepted practice be reviewed
before changing the test architecture, that Wenu decide explicitly which
recommendations to incorporate, and that the test loop be rationalized before
production optimization. The active sequence is therefore:

1. 49J.1 test architecture and accepted-practice audit;
2. 49J.2 explicit Wenu test-practice decisions;
3. 49J.3 accepted test-suite optimization;
4. 49J.4 cold independent chart and sequence measurement;
5. 49J.5 one bounded scientifically keyed fixed-sky circumpolar reuse;
6. 49J.6 performance closure.

`archive/roadmap_history/test_performance_and_future_program_49j_50.md` governs the scope, evidence,
decision ledger, ordering, and stop conditions. Every slice remains separately
authorized.

49J.1 is accepted and archived at
`archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md`.
Three routine runs had a 27.16-second median and 3.42-second range;
three complete runs had an 85.49-second median and 2.19-second range. Evidence
included an incompatible ambient pytest plugin and a mismatch between the
documented session registry and committed fixtures. The audit changes no test,
marker, fixture scope, runtime code, cache, output, or timing threshold.

Fernando accepted 49J.2 on 2026-09-09 as recorded in
`archive/milestone_history/49j_performance/test_practice_decisions_49j2.md`.
Its ledger includes explicit new-test admission and duplication control: a
capability that composes already-tested functions should test its new seam and
fault models rather than copy every lower-level test. Later 49J.3 changes
remain separately reviewable.

49J.3A implemented only the reproducible test-entry and new-test admission
documentation now archived at
`archive/milestone_history/49j_performance/test_entry_and_admission_49j3a.md`.
It changed no test, marker, fixture, runtime code, cache, output, or timing and
claimed no speedup. Focused Mac verification passed all 83
current-documentation tests in 2.43 seconds, and the slice was merged in
`21ee528`.

49J.3B audited marker truthfulness in
`archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md`. It narrowed
an overbroad module-level `visual` marker to the two tests that actually inspect
raster image structure or rendered physical layout, and an overbroad
module-level `integration` marker to the two tests that actually build across
the Cen A example/chart boundary. Five structural planisphere cases and one
constants contract return to the routine gate. No assertion, fixture, runtime
code, cache, or output changes.

Mac verification passed 94 focused tests, 21 integration tests, 3 visual
tests, 2,103 routine tests with 24 deselected, and all 2,127 tests. Fernando
accepted the slice; it was merged in `6fc8bee`.

49J.3C completed in
`archive/milestone_history/49j_performance/repository_source_index_49j3c.md`.
It consolidated the
immutable repository Python-file inventory and lazily cached source/AST index
while preserving independently named architectural assertions and adding an
exact full-inventory coverage proof. The separate subprocess import-isolation
oracle is unchanged. Fernando's Mac verification passed 2,105 routine tests
with 24 deselected and all 2,129 tests; the slice was merged in `23d1b32`.

49J.3D completed in
`archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md`.
It shares only a nested read-only catalogue-position summary between two
polar-binocular assertions. Mutable Astropy tables and canonical spheres remain
unshared; the slice was merged in `63beb17`.

49J.3E completed in
`archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md`.
Its audit preserves
the independent cold factory, reusable-sphere order, horizon-mutation,
complete-render, and observer-time sequence oracles. Standalone installed-DE440
validators retain fresh observers and direct Skyfield recomputation; no new
fixture, registry, cache, or speedup claim was introduced; the slice was merged
in `6db2272`.

49J.3F completed in
`archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md`. It
removes repeated
full-canvas redraws from the physical calendar-label containment test while
retaining 300 dpi renderer extents for every label, millimetre conversion, the
97.5 mm disk boundary, `visual` and `slow` markers, and deliberate fault
detection; the slice was merged in `a190a09`.

49J.3G completed in
`archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md`.
It retains the
two-frame real canonical observer-time sequence unchanged: each instant still
uses the complete public generation route, produces a distinct PNG, and proves
manifest resume. Fixed-sky reuse remains sequenced after the independent-frame
baseline in 49J.4; the slice was merged in `d7ba1d5`.

49J.3H completed in
`archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md`.
It maps every 49J.3 change to retained fault detection, installs durable
test-file placement and growth rules, and closed with three routine plus three
complete Mac runs; the slice was merged in `2c524d2`.

49J.4 completed in
`archive/milestone_history/49j_performance/cold_frame_performance_baseline_49j4.md`.
The diagnostic
measures three fresh fixed-sky circumpolar frames through the unchanged
complete-render oracle with exclusive request, resource, provider,
transformation, projection, preparation, rendering, export, and residual
accounting. It adds no cache, output change, or threshold; the slice was merged
in `f4dcf11`.

49J.5 is accepted and archived in
`archive/milestone_history/49j_performance/loaded_sphere_reuse_49j5a.md` and
`archive/milestone_history/49j_performance/fixed_sky_reuse_equivalence_49j5b.md`.
It introduces an explicit opt-in mode that reuses only one observer-independent
loaded canonical sphere. Every frame retains a fresh observer and the complete
canonical realization, projection, preparation, rendering, and export route.
Cold execution remains the default correctness oracle. Exact scientific, PNG,
normalized-SVG, and rendered-PDF equivalence plus measured Mac improvement
closed the candidate comparison.

49J.6 is accepted and archived at
`archive/milestone_history/49j_performance/performance_closure_49j6.md`. Final
non-overlapping Mac gates covered all 2,146 collected tests, documentation and
ownership were reconciled, both execution routes were retained, and 49J is
closed. Program 50A.0 is next.

The closed 49J program retains these requirements:

- benchmark complete independent frames before optimizing;
- measure catalogue loading, provider evaluation, transformation, projection,
  preparation, rendering, and encoding separately;
- cache by explicit immutable scientific keys rather than mutable global
  state;
- retain the complete-render path as a correctness oracle;
- update current architecture, implementation reference, source tree, user
  documentation, examples, and diagrams when ownership changes;
- close or supersede this roadmap only after focused, full, scientific, SVG,
  visual, and sequence tests pass.

49J.0 changes no runtime behavior, timing threshold, test classification,
cache, or output.

Final Mac verification passed 94 combined documentation/user-guide tests,
2,092 routine tests with 30 deselected, and all 2,122 tests. The observed
37.88-second routine run is retained as later characterization evidence; it
does not authorize weakening tests or optimizing under 49J.0.

## 13.1 Program 50A - Asteroids and comets

After 49J closure, extend the descriptor-driven moving-body architecture to
minor bodies. Audit provider accuracy and provenance first; then implement a
generic state provider, validate asteroids, add the first symbolic asteroid and
track, validate comets, add the first symbolic comet and track, and close the
public and scientific contract. Coma and tail morphology remain separate from
nucleus position.

50A.0 is accepted and archived in
`archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md`.
It selects a bounded, locally resolved Horizons small-body SPK plus explicit
companion planetary-resource provenance for the first provider; rejects live
network access during rendering and silent two-body fallback; and records
validity, uncertainty, identifiers, photometry, and comet non-gravitational
policy. It adds no runtime behavior or visible object. 50A.1 is next.

50A.1 is accepted and archived in
`archive/milestone_history/50a_minor_bodies/minor_body_state_provider_50a1.md`.
It adds
a typed primary-plus-dependency resource chain, a Horizons solution identity,
and an offline borrowed-kernel state provider. The provider composes the
small-body target-relative-to-segment-centre state with that centre's state
from the declared planetary dependency. It remains unconnected to bodies,
directions, charts, CLI, and output. Fernando accepted the explicit composition
on 2026-09-10, authorizing 50A.2 numerical validation as the next slice.

50A.2 is accepted and archived in
`archive/milestone_history/50a_minor_bodies/asteroid_numerical_validation_50a2.md`.
It uses CSPICE only to evaluate exact Horizons type-21 target segments, keeps
DE440/Skyfield as the explicit planetary and observer dependency, and compares
Ceres and fast nearby Apophis against frozen direct-Horizons Cartesian,
astrometric, apparent, distance, light-time, and parallax evidence. No body,
chart, CLI, or output is added. Fernando accepted its scientific tolerances,
physical interpretation, and hybrid CSPICE/Skyfield ownership on 2026-09-11;
50A.3 first-drawable-asteroid work is next.

50A.3A is accepted and archived in
`archive/milestone_history/50a_minor_bodies/first_drawable_asteroid_audit_50a3a.md`.
It selects
Ceres as the first bounded object and proposes an explicit manifest-backed
resource directory, class-aware `--asteroid` and `--asteroid-track` selectors,
descriptor-aware provider binding into the existing point/track route, stable
minor-body semantics, and fixed symbolic appearance without a magnitude
claim. It also preserves a collection-oriented trajectory seam for later
WCS/instrument-footprint and artificial-satellite planning without confusing
SPK/TDB minor-body physics with OMM/TLE plus SGP4/TEME satellite physics. It
changes no runtime behavior; Fernando's 2026-09-11 acceptance authorizes the
bounded 50A.3B implementation.

50A.3B is accepted and archived in
`archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md`. It connects only `(1) Ceres` through
an explicit manifest-backed resource directory and descriptor-aware target
versus observer source binding. The existing point, fixed-frame track,
projection, preparation, semantic, rendering, and export routes are retained;
there is no magnitude, implicit network, fallback propagator, discovery, or
field-query claim. Fernando accepted the final macOS PNG and semantic SVG on
2026-09-11. Fernando then accepted the bounded 50A.3C generalization audit in
`archive/milestone_history/50a_minor_bodies/numbered_asteroid_generalization_audit_50a3c.md`.
It defines manifest-backed selection of any installed numbered asteroid by
permanent number or manifest-declared official name, with unnamed main-belt
object `(79989)` as the acceptance specimen. 50A.3D implemented and validated
that contract without object-specific runtime branching or implicit network
lookup. PR 98 subsequently added explicit fixed- and moving-object centers and
separated CLI center, content, constellation, and mask responsibilities.
Milestone 50A.3G is the bounded documentation and visual-acceptance closure;
it was accepted on 2026-09-12 with all eleven visual products and 2,234 tests.
Accepted 50A.3H audits convenient one-command moving-object resolution
without admitting network access into chart construction or rendering. It
proposes a content-addressed local cache, explicit data policies, Horizons-SPK
preflight as the first implementation, a later separately validated orbital-
catalog provider, and wholly separate TLE/OMM plus SGP4 satellite dynamics.
Fernando accepted its decisions on 2026-09-12 after 104 focused documentation
tests passed. The bounded 50A.3I numbered-asteroid CLI preflight implementation
is authorized next. 50A.4 comet numerical validation retains its meaning and
follows that separately accepted implementation slice.

## 13.2 Program 50B - Publication legibility and economical printing

After the minor-body symbols and tracks are available, review current accepted
printing, typography, contrast, accessibility, cartographic, and astronomical-
atlas practice. Decide explicitly which recommendations Wenu adopts, adapts,
rejects, or defers before defining physical-output profiles. Then measure the
as-is products, implement monochrome and limited-grayscale styles, perform
actual-size print and reduction acceptance, and close the numerical standard.

The active detailed sequence and decision requirements for 50A and 50B are in
`archive/roadmap_history/test_performance_and_future_program_49j_50.md`.

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


## Milestone 49I.3C — Resolved Venus disk audit

**Status:** Scientifically and architecturally accepted on 2026-08-31.

`archive/milestone_history/49i_solar_system/resolved_venus_disk_audit_49i3c.md` accepts a renderer-neutral semantic group
containing an illuminated spherical polygon plus limb and terminator spherical
curves. Physical geometry is sampled before projection; Venus-specific display
magnification scales projected offsets about the projected physical centre in
chart preparation. The accepted sequence is 49I.3C.1 physical spherical
geometry, 49I.3C.2 one drawable regional/binocular disk, and 49I.3C.3 several
independently realized disks in one fixed chart frame. Symbolic defaults and
planisphere/all-sky behavior remain unchanged.


## Milestone 49I.3C.1 — Venus spherical disk geometry

**Status:** Scientifically and architecturally accepted on 2026-08-31.

`SolarSystemDiskGeometryRealizer` now constructs the physical apparent
centre, closed limb, visible terminator, and illuminated-face polygon from the
accepted 49I.3B state. The default 720-sample orthographic phase with radial
angular-offset mapping passed deterministic and installed-DE440 validation.
The slice adds no layer, request, magnification, style, renderer, or visible
output. 49I.3C.2 remains separately authorized.


## Milestone 49I.3C.2 — First drawable resolved Venus disk

**Status:** Scientifically, architecturally, visually, and operationally
accepted on 2026-08-31.

Regional and binocular requests can now opt into one resolved Venus disk.
Illuminated face, limb, and terminator share one physical state and retain
independent semantic paths and styles. Display magnification occurs after
ordinary projection around the exact separately projected physical centre.
Symbolic defaults and planisphere/all-sky behavior remain unchanged.

The accepted Virgo calibration uses La Ligua at
`2026-08-30T00:00:00Z`, a physical diameter of
`29.287846514361 arcsec`, magnification 200, and therefore a nominal
displayed diameter of `1.62710258413117 deg`. Multi-epoch disks remain 49I.3C.3. Final verification passed 1,970 routine
tests with 30 deselected and all 2,000 tests.


## Milestone 49I.3C.3 — Multi-epoch resolved planet-disk audit

**Status:** Scientifically and architecturally accepted on 2026-08-31.

`archive/milestone_history/49i_solar_system/planet_disk_sequence_audit_49i3c3.md` distinguishes an observed sequence
from a frozen-Earth ecliptic construction. Observed samples independently
reevaluate the topocentric observer, apparent direction, and physical
appearance at every exact major instant before entering one fixed chart frame.
Frozen mode fixes Earth's heliocentric position at the start, advances the
planet geometrically in a fixed ecliptic frame, and restricts content to planet
disks, a central six-point Sun, and the transformed equatorial grid.

Every sample preserves full physical distance, origin, unit, instant, and
provider provenance so later scientifically governed 3D work need not
reconstruct distance from 2D geometry. No 3D visualizer is implemented here.

Both policies converge on one typed sequence, accepted spherical disk
geometry, per-centre post-projection magnification, ordinary renderer, and
shared export. Proposed runtime slices are 49I.3C.3.1 observed Venus,
49I.3C.3.2 frozen-Earth ecliptic Venus and Sun, and 49I.3C.3.3 independently
validated Mercury support. Fernando accepted this audit after all 63 current-documentation tests passed
in 2.04 seconds. Final verification passed 63 documentation tests in 1.88
seconds, 1,971 routine tests with 30 deselected in 27.08 seconds, and all 2,001
tests in 85.97 seconds. This audit changes no runtime or output.


## Milestone 49I.3C.3.1A — Output-neutral observed Venus disk sequence

**Status:** Scientifically and architecturally accepted on 2026-08-31.

The immutable sequence request includes the start and produces
`n_steps + 1` exact major samples. Every epoch independently reevaluates the
topocentric observer, Venus and Sun apparent directions, physical appearance,
and spherical disk geometry. Full observer/AU distances and provenance are
retained for 2D science and possible future separately governed 3D use.

The four-epoch installed-DE440 validator agreed with direct Skyfield to
`4.615e-10 deg` in right ascension, `1.946e-10 deg` in declination,
`3.128e-12 AU` in distance, `3.795e-10 arcsec` in diameter,
`7.096e-10 deg` in phase, `4.823e-12` in illuminated fraction, and
`4.301e-09 deg` in bright-limb angle. All 51 focused scientific tests and 91
architectural tests passed. Final verification passed 64 documentation tests
in 2.23 seconds, 1,985 routine tests with 30 deselected in 25.46 seconds, and
all 2,015 tests in 84.38 seconds. No public request or visible output is added;
drawable observed Venus sequences remain 49I.3C.3.1B.


## Milestone 49I.3C.3.1B — Drawable observed Venus disk sequence

**Status:** Scientifically, architecturally, visually, and operationally
accepted on 2026-08-31.

Regional and binocular charts now expose start-inclusive observed Venus disk
sequences with exact major steps, optional dates, and one object-specific
post-projection magnification. Every epoch is independently transformed into
one fixed chart frame before aggregation; observer/AU distances and provenance
remain preserved.

The accepted four-epoch Virgo calibration used 28-day steps, magnification
200, an ecliptic-only reference, and no default equatorial grid. Verification
passed 211 focused tests, 1,988 routine tests with 30 deselected, and all 2,018
tests. Frozen-Earth Venus remains 49I.3C.3.2; Mercury remains 49I.3C.3.3.


## Milestone 49I.3C.3.2A — Output-neutral frozen-Earth Venus sequence

**Status:** Scientifically and architecturally accepted on 2026-09-01.

Earth's heliocentric ICRF vector is evaluated once at the sequence start and
retained unchanged. Same-epoch Venus heliocentric vectors at exact major steps
produce frozen-observer geometric directions, distances, physical appearance,
and fixed J2000 mean-ecliptic orientation. The fixed Sun vector is the negative
frozen-Earth vector. Full vectors and frozen-earth/AU distances remain
available for possible future separately governed 3D use.

The installed-DE440 comparison agreed to `4.337e-12 AU` in target vectors,
`1.968e-10 deg` in ecliptic longitude, `2.064e-11 deg` in latitude,
`1.274e-12 AU` in distance, and `1.627e-10 deg` in limb angle. Verification
passed 63 focused tests, 1,997 routine tests with 30 deselected, and all 2,027
tests. This slice adds no public request or visible output; drawable restricted
ecliptic presentation remains 49I.3C.3.2B, and Mercury remains 49I.3C.3.3.


## Milestone 49I.3C.3.2B — Drawable frozen-Earth Venus sequence

**Status:** Scientifically, architecturally, visually, and operationally
accepted on 2026-09-01.

Regional charts now expose the start-inclusive frozen-Earth construction with
exact major steps, one central fixed Sun, optional date labels, and per-centre
Venus display magnification. The restricted scene permits an explicitly
requested product-frame ecliptic and optional fixed-frame equatorial grid.
Automatic titles and reference labels are localized after language resolution.

Fernando accepted the 31-disk La Ligua Virgo calibration with seven-day steps,
magnification 200, the ecliptic through the Sun, the distinct equatorial grid,
and Spanish labeling. Verification passed 156 focused tests and all 2,037 Mac
tests in 84.41 seconds. Mercury remains 49I.3C.3.3.


## Milestone 49I.3C.3.3 — Mercury generalization and validation audit

**Status:** Scientifically and architecturally accepted on 2026-09-01.

`archive/milestone_history/49i_solar_system/mercury_disk_sequence_audit_49i3c33.md` identifies the accepted generic
frozen-sequence and disk-geometry seams, the remaining Venus-specific drawable
owners, Mercury body identity `199`, proposed JPL mean radius `2439.4 km`, and
the provider body-versus-barycentre distinction.

The moving-body foundation was inserted as 49I.3C.3.3A. The bounded Mercury
slices are therefore 49I.3C.3.3B output-neutral Mercury state plus
installed-DE440 comparison, followed only after acceptance by 49I.3C.3.3C
drawable frozen-Earth Mercury. Observed Mercury, symbolic Mercury, tracks,
single disks, photometry, rotation, multiple bodies, animation, and 3D remain
outside this audit. The audit changes no runtime or visible output.

Fernando accepted the two-slice boundary, JPL equal-volume mean radius,
physical-body/provider-barycentre distinction, frozen-only first drawable
scope, and explicit non-goals after all 68 current-documentation tests passed
on his Mac in 2.19 seconds.


## Milestone 49I.3C.3.3A — Descriptor-driven moving-body foundation

**Status:** Scientifically, architecturally, and visually accepted on
2026-09-01.

Before Mercury numerical state, replace the remaining Venus-specific drawable
control flow with a body descriptor, immutable catalog, capability resolution,
and generic point, track, disk, and disk-sequence factories. Preserve Venus
output. Prove extensibility with a deterministic synthetic minor body; do not
register Mercury or expose another CLI body in this slice.

Fernando accepted the abstraction after all 2,045 Mac tests passed in 86.49
seconds and human review confirmed unchanged frozen-Earth, single resolved,
and observed-sequence Venus output.


## Milestone 49I.3C.3.3B — Mercury catalog and numerical validation

**Status:** Scientifically and architecturally accepted on 2026-09-01.

Mercury is one immutable descriptor with physical body ID `199`, JPL
equal-volume mean radius `2439.4 km`, and frozen-Earth capability only. Direct
installed-DE440 validation passed every declared tolerance and the complete
Mac suite passed all 2,047 tests in 97.93 seconds. No public Mercury CLI was
added in this slice.


## Milestone 49I.3C.3.3C — Drawable frozen-Earth Mercury

**Status:** Scientifically, architecturally, visually, and operationally
accepted on 2026-09-01.

Expose Mercury only for the accepted frozen-Earth model through catalog
capability, generic drawable factories, generic semantics, and descriptor-owned
localized display names. Observed Mercury and every other unvalidated Mercury
capability remain rejected. No Mercury-specific drawable infrastructure is
authorized.

Fernando accepted the shared implementation after 119 focused tests passed in
3.06 seconds, PNG/PDF/SVG calibration parity passed visual review, and all
2,052 Mac tests passed in 89.90 seconds.


## Milestone 49I.3D.1 — Apparent major-planet symbolic points

**Status:** Implementation proposed; installed-DE440 and visual acceptance
pending.

Register Mercury, Mars, Jupiter, Saturn, Uranus, and Neptune for the same
ordinary apparent symbolic-point capability used by Venus. Earth remains the
observer body. Preserve the DE440s barycentre targets for Mars through Neptune
separately from physical planet identity, and reuse one generic point-layer,
correction, transformation, semantic, style, renderer, and export path.

This slice preserves the provisional Venus hollow marker for every planet.
Validated apparent photometry, planet glyphs, resolved disks, rings, tracks,
and observed sequences remain later capability-specific work.


## Milestone 49I.3E.1 — Output-neutral lunar physical appearance

**Status:** Scientifically accepted, regression-verified, integrated, and superseded by the completed parent milestone.

Register one catalog Moon identity with Earth relationship, NAIF physical body
ID `301`, JPL equal-volume mean radius `1737.4 km`, localization, symbolic
compatibility, and output-neutral spherical-appearance capability. Reuse the
generic `SolarSystemAppearanceRealizer` for centre, distance, diameter, phase,
illuminated fraction, and apparent-ICRS bright-limb orientation.

Validate a deterministic phase/distance/orientation case set against direct
Skyfield using the installed kernel and explicit topocentric parallax. Add no
disk geometry, CLI, magnification, chart-family change, style, renderer,
exporter, sequence, or visible output.

Fernando accepted the eight-case installed-DE440 validation on 2026-09-02.
Maximum residuals were `1.338e-07 deg` in apparent right ascension,
`2.885e-08 deg` in apparent declination, `4.427e-12 au` in distance,
`2.994e-06 arcsec` in angular diameter, `9.726e-08 deg` in phase,
`2.606e-10` in illuminated fraction, and `2.268e-06 deg` in wrapped
bright-limb position angle. Minimum topocentric parallax was `0.272607 deg`.
All values satisfy the accepted revised envelope. Final verification passed
73 documentation tests, 124 focused tests, 2,051 routine tests with 30
deselected, and all 2,081 tests. Integration subsequently completed in PR #71;
this slice alone did not pre-authorize 49I.3E.2.


## Milestone 49I.3E.2 — Drawable resolved single-epoch Moon

**Status:** Scientifically, architecturally, visually, operationally, and regression accepted.

Make bare `--moon` resolve to one physical lunar disk while preserving the
explicit `--moon-appearance symbolic` compatibility mode. Reuse descriptor-
driven 720-sample disk geometry, ordinary transforms, post-projection
magnification, rendering, semantic identity, and PNG/PDF/SVG export.

Authorize the Moon in all five chart families through descriptor policy while
leaving Venus family support unchanged. Exercise factor 1000 in automated
contracts for regional, binocular, circumpolar, planisphere, and Mollweide
all-sky products, and use a legible calibrated factor for human visual review.
Do not add any multi-epoch Moon behavior; that remains 49I.3E.3.

Fernando accepted the five-family visual matrix on 2026-09-02. Final
verification passed 69 focused tests, 74 documentation tests, 2,074 routine
tests with 30 deselected, and all 2,104 tests. This closes only 49I.3E.2.


## Milestone 49I.3E.3 — Observed fixed-chart Moon sequence

**Status:** Scientifically, architecturally, visually, operationally, and regression accepted.

Add `--moon-disk-sequence` as a public adapter into the shared observed
sequence request. Preserve start-inclusive cadence, independent physical state
at every sample, one distinct chart-epoch product frame, complete tangent
geometry transport, per-centre display magnification, date labels, stable
natural-satellite semantics, and all-five-family rendering/export.

Fernando accepted the installed-DE440 comparison and all sequence review
renders on 2026-09-02. Frozen-Earth lunar sequences, interpolation, animation,
texture, libration, eclipses, refraction, and occultation remain outside this
milestone.

Closure passed 75 documentation tests, 161 expanded focused tests, 2,088
routine tests with 30 deselected, and all 2,118 tests.



## Milestone 49I.3E — Resolved apparent Moon and fixed-chart sequence

**Status:** Complete; all authorized slices scientifically, architecturally,
visually, operationally, and regression accepted on 2026-09-02.

49I.3E.0 through 49I.3E.3 now form one closed capability: authoritative lunar
physical state, a resolved single-epoch Moon in all five ordinary chart
families, explicit symbolic compatibility, and observed independently realized
Moon samples projected through one fixed chart-epoch product frame. The work
reuses the shared descriptor, appearance, spherical-disk, projection,
preparation, renderer, semantic SVG, and export machinery without a Moon-
specific parallel pipeline.

PRs #70 through #73 are merged, ending at `bc45cc0`. Parent closure records
the already accepted final verification: 75 documentation tests, 161 expanded
focused tests, 2,088 routine tests with 30 deselected, and all 2,118 tests.

Parent-closure verification passed 76 documentation tests in 9.55 seconds, 2,089 routine tests with 30 deselected in 31.89 seconds, and all 2,119 tests in 87.44 seconds.

No additional runtime behavior is authorized by this parent closure. Frozen-Earth lunar sequences, interpolation, animation, texture, libration, eclipses,
refraction across the resolved disk, and occultation prediction remain outside
49I.3E.

## Milestone 50A.3I — Automatic numbered-asteroid CLI preflight

**Status:** Accepted and complete on 2026-09-12.

Implement accepted 50A.3H for exact positive permanent asteroid numbers. The
installed CLI may reuse or acquire verified bounded Horizons SPKs under
`acquire-if-missing`, `offline`, and `refresh` policies before ordinary chart
construction. Immutable content-addressed publication, provider receipts,
coverage validation, and an authoritative explicit resource directory preserve
reproducibility and offline rendering. Comets, satellites, name discovery, and
orbital-element propagation remain deferred.

Fernando accepted automatic acquisition and warm-cache offline reuse for
`(79989)` and `(79990)`. Closure passed 181 focused tests in 5.12 seconds and
all 2,248 tests in 91.13 seconds.

Accepted 50A.4 selects 2P/Encke for bounded comet nucleus-state validation.
It requires frozen non-gravitational model provenance, direct-Horizons state
and observer-table evidence, explicit characterization before tolerances, and
no drawable or automatically acquired comet behavior.
Fernando accepted the audit on 2026-09-12 after all 106 focused documentation
tests passed in 3.94 seconds. The accepted implementation freezes
the compact oracle, parses raw evidence offline, and provides a validator with
an optional non-accepting characterization mode. Fernando accepted the
characterized reproduction tolerances on 2026-09-12. Final Mac verification
returned `accepted: true`, passed all 151 focused tests in 4.99 seconds, and
passed the complete 2,262-test suite in 84.96 seconds. Milestone 50A.4 is
complete; the first symbolic comet and track remain the next bounded program
slice.

Accepted 50A.5A audits the first drawable comet before runtime work. It selects
2P/Encke as one explicitly installed, symbolic nucleus point and dated
track through the shared minor-body/Solar-System route. Comet identity remains
distinct from minor-planet numbering and keeps `P`, `D`, `I`, `C`, `X`, and
`A` designation classes structurally distinct. Syntax recognition does not
authorize drawing without separately validated installed state. Automatic
comet acquisition, brightness, coma, tail, photocentre, and physical nucleus
appearance remain deferred. The audit changes no runtime behavior. Fernando
accepted it on 2026-09-12, authorizing the bounded 50A.5B implementation.
Fernando subsequently requested antisolar rotation of the symbolic comet fan
and simultaneous planet, asteroid, and comet tracks when they share one field.
The proposed implementation therefore generalizes the singular track request
to a collection with one shared timeline; artificial satellites and per-track
timelines remain deferred.

Visual review of the provisional 50A.5B implementation exposed duplicate
target evaluation for symbols placed at track anchors. Corrective audit
50A.5B.1 therefore introduced one shared track realization with independently
selectable path, tick, symbol, and date-label components. The same exact-major-
anchor presentation policy is reused by observed Venus and Moon and by the
frozen-Earth-ecliptic Mercury phase sequence while their physical disk
realization remains separately owned. Fernando accepted the corrective
architecture and the Encke and Venus presentations on 2026-09-13. Final Mac
verification passed the complete 2,331-test suite in 84.56 seconds, closing
50A.5B.1.
The accepted symbol is constructed from a hollow circle, short radial spokes,
and three longer tail spokes; the central tail spoke is 1.5 times the exposed
length of the two symmetric outer spokes and their total fan angle is 25
degrees. Wenu owns one canonical immutable
normalized vector definition; each use applies only placement, antisolar
orientation, and magnification rather than reconstructing the geometry.
The antisolar direction claim is enforced against the accepted independent
direct-Horizons position-angle oracle; fixed fan length and opening remain
symbolic.

Accepted 50A.5C uses 161P/Hartley-IRAS during September and October 2026 as a
second independently validated installed comet before Program 50A closure.
It must prove that identity, provider state, temporal components, per-epoch
orientation, the canonical symbol, projection, rendering, semantics, and
export are resource- and descriptor-driven rather than Encke-specific. It
requires fresh SBDB/Horizons evidence and characterization before tolerances,
but authorizes no automatic comet acquisition, fuzzy discovery, photometric
claim, physical tail model, or parallel runtime pipeline.
Fernando accepted this bounded audit on 2026-09-13, authorizing evidence
acquisition and characterization but not a numerical tolerance before the
measured residuals and source precision are reviewed.
The subsequent 161P characterization remained within the accepted Encke
Cartesian, distance, light-time, parallax, and `0.01 deg` PsAng envelopes.
Fernando accepted those common values and relaxed only the common comet
observer-direction envelope from the theoretical five-decimal half-step to
one full printed step, `1e-5 deg` (`0.036 arcsec`), avoiding a platform-fragile
161P-specific fit.
Final Mac review reproduced and installed the fixture, accepted the 161P
complete and symbols-only charts, verified date-owned moving-object centering,
and passed the complete 2,346-test suite in 83.89 seconds. Milestone 50A.5C is
closed. Automatic comet discovery/acquisition and generic moving-object
sidecar reports require a new audit before implementation.


## Milestone 50A.5D — Comet discovery, acquisition, and moving-object reports

**Status:** Audit, 50A.5D.1A, and 50A.5D.2A through 50A.5D.2C accepted;
50A.5D.1B and 50A.5D.3 remain.

50A.5D.1A accepted by Fernando on 2026-09-13.

Fernando accepted the 50A.5D.1B audit on 2026-09-14. It is recorded in
`comet_model_magnitude_audit_50a5d1b.md` and authorizes only the bounded
implementation: daily endpoint-inclusive sampling over the discovery interval,
at most 367 epochs per comet and 50 comets, sequential Horizons requests,
brightest sampled `T-mag` as the public summary with separate `N-mag`, and
whole-result failure. The value remains a provider model, not a continuous
minimum, visibility forecast, or detectability claim.

The proposed audit separates an explicit `wenu_retrieve_comets` SBDB query,
exact policy-governed comet preflight, and renderer-neutral natural moving-
object sidecars. Discovery means a declared perihelion-time and perihelion-
distance filter, not visibility. Automatic resources remain provider-trusted;
the accepted Encke and 161P fixtures remain the independent numerical oracles.
Reports must consume the already realized temporal result and may not repeat an
ephemeris calculation. Artificial satellites remain outside this milestone.
The accepted report contract additionally requires instantaneous topocentric
apparent `dRA/dt`, `cos(dec) dRA/dt`, `dDec/dt`, and total sky-plane speed in
mas/s, with explicit telescope-driver convention warnings.

The accepted 50A.5D.1A implementation provides only the deterministic SBDB
query, typed rows, and table/JSON command. Fernando deferred observer-dependent Horizons
magnitude and its cadence to 50A.5D.1B. Comet acquisition and moving-object
reports remain unauthorized later slices.

The accepted 50A.5D.2A audit isolates exact comet identity resolution before
acquisition. It reuses exact installed aliases, permits one explicit SBDB
identity query for an uninstalled selection, and fails on partial, absent,
ambiguous, fragment-ambiguous, or bare-number input rather than guessing.
`10P/Tempel 2` is only the first acceptance specimen. Fernando accepted a
mandatory-class generic resolver core so asteroid and comet identity logic is
not duplicated; only the comet route is integrated in this slice. SPK
acquisition, cache publication, chart integration, magnitude, and reports
remain outside this accepted audit.

The 50A.5D.2A implementation was accepted by Fernando on 2026-09-13 after exact live SBDB success and failure checks, 150 focused Mac tests, and the complete 2,380-test Mac regression.

The accepted 50A.5D.2B audit isolates the shared acquisition service before
CLI composition. It requires an exact resolved identity, explicit unique
Horizons record/apparition and solution binding, a bounded validated type-21
SPK, retained non-gravitational provenance, and atomic content-addressed
publication. It changes no runtime code and does not authorize chart preflight
integration or reports. Fernando accepted this bounded audit on 2026-09-13.

Fernando accepted the bounded 50A.5D.2B acquisition-service implementation
on 2026-09-13 after live `10P/Tempel 2` acquisition, offline immutable-cache
reuse, 169 focused tests, and the complete 2,388-test Mac regression. It uses a
resolved identity, a unique explicit Horizons record, strict
solution/target/signature comparison, one validated type-21 segment, and the
existing immutable publication policy. This closes only the shared acquisition
service; CLI integration remains 50A.5D.2C.


The accepted 50A.5D.2C audit isolates exact comet CLI preflight composition.
It requires one request-level typed minor-body set, one complete coverage
interval, and one verified immutable resource collection before chart
construction. Explicit resource directories remain authoritative and offline;
warm-cache reuse performs no provider access. Mixed numbered-asteroid and comet
requests must not acquire parallel directories. Magnitude, fuzzy lookup,
automatic asteroid-name acquisition, new graphics, and reports remain outside
the accepted audit. Fernando accepted it on 2026-09-13, authorizing only the
bounded CLI-preflight implementation.

The accepted implementation performs that typed composition in
`cli/chart.py`: exact point, track, and explicitly classed center selections
share one coverage interval and one verified resource directory; explicit and
adequate warm-cache paths remain offline. Fernando accepted live and offline
numbered and provisional comet acquisition, the independent Lemmon comparison,
and the complete 2,404-test Mac suite. PR #116 merged at `2f30a95`.



## Milestone 50A.5E — Distributable minor-body database and lifecycle tools

**Status:** Planned after 50A.5D and before 50A.6; audit required before
implementation.

Wenu will support a versioned distributable database of important asteroids
and comets, including every dwarf planet admitted by the governed inclusion
policy. This is a third data source, distinct from a recently acquired
immutable cache and live provider acquisition. The accepted default resolution
order is:

```text
verified cache -> live provider acquisition -> packaged Wenu database
```

Explicit policy always overrides that fallback:

- `offline` uses verified cache only and performs no network access;
- `refresh` requires new provider acquisition and does not silently fall back;
- `wenu-database` uses only the installed distributable database;
- `acquire-if-missing` uses cache, then provider, then the database if
  acquisition is unavailable and the database adequately covers the request.

### 50A.5E.0 — Database scientific and packaging audit

Choose bounded SPKs, orbital elements plus an independently validated
propagator, or a governed hybrid. Define source authority, identity,
classification, solution/model provenance, validity and coverage, uncertainty,
database version, compatibility, update cadence, licensing, package-size
budget, selection criteria, dwarf-planet policy, and behavior outside database
coverage. A packaged database must never become an unvalidated two-body
fallback.

### 50A.5E.1 — Reproducible database-construction tool

Add a maintainer/package-construction tool that deliberately downloads
authoritative source data, validates identity and scientific coverage, freezes
provider receipts and checksums, builds a deterministic versioned artifact,
and verifies the installed artifact before release. The tool must not run
during ordinary chart construction or package import.

### 50A.5E.2 — Runtime database policy and fallback

Add the explicit `wenu-database` policy and the accepted
cache-to-provider-to-database default. All three sources must converge on one
verified resource-collection boundary before sphere, view, request, or
rendering construction. Reports and semantic output must identify which source
and database version supplied every object.

### 50A.5E.3 — Safe cache lifecycle tool

Add a cache-management command that can list entries, report size and
coverage, identify invalid or superseded entries, perform a dry run, prune by
an explicit policy, and flush the minor-body cache only after explicit
confirmation. It must resolve and validate Wenu's cache root, refuse broad or
unrelated paths, never delete the packaged database, and clearly state that
flushed cache data must be reacquired.

## Program 50S — Artificial-satellite crossings and contamination

**Status:** Planned after 50A.6 minor-body closure and before Program 50B
publication work; 50S.0 scientific and architectural decisions accepted by
Fernando on 2026-09-14.

This program must make field-crossing queries a first-class scientific product.
Given an observer, an explicitly framed field of view and centre, a start and
stop instant spanning minutes to hours, and an orbit-catalogue snapshot, Wenu
must efficiently return every artificial satellite whose apparent topocentric
trajectory intersects the field during that interval. The same evaluated
crossings must support statistical characterization of the night sky by local
time, season, pointing, field size, and exposure duration.

Artificial satellites may reuse Wenu's moving-body identity, observed
trajectory, fixed product-frame transformation, projection, clipping,
semantic-output, report, and instrument-footprint contracts. Their scientific
path remains separate from Solar-System and minor-body SPK/TDB providers:
current OMM or legacy TLE elements, SGP4 propagation in TEME, explicit
Earth-orientation data, topocentric transformation, orbit-epoch freshness,
Earth-shadow and illumination state, and prediction uncertainty must remain
identified and reproducible.

The online path begins with a provider-neutral query/result domain and a
policy-compliant SatChecker adapter. The later local fast path is a
conservative cascade:

1. reject impossible candidates with topocentric orbital-plane/FoV-cone,
   radial-shell, phase/reachable-arc, Earth-occultation, and horizon bounds;
2. propagate retained catalogue batches with vectorized SGP4 and conservative
   angular-motion/curvature bounds;
3. refine entry, exit, closest approach, and exposure overlap only for retained
   candidates, without missing a true crossing.

Repeated all-night or seasonal studies may reuse an immutable HEALPix/time
index keyed by orbit-catalogue digest, observer, Earth-orientation policy,
night or bounded interval, cadence/bounding policy, and scientific software
version, but only if larger-snapshot benchmarks justify it. Index or cache
policy must not enter propagation, coordinate, projection, or rendering
ownership, and the unindexed complete calculation must remain available as a
correctness oracle.

### 50S.0 — Scientific, catalogue, search, and photometry audit

**Status:** Accepted by Fernando on 2026-09-14 and recorded in
`artificial_satellite_crossing_audit_50s0.md` and the living
`satellite_guide.md`.

Review the scientific and technical literature before selecting either the
catalogue-wide crossing algorithm or an apparent-brightness model. Record
primary sources, implemented reference systems, assumptions, failure modes,
computational complexity, validation evidence, and an explicit
Adopt/Adapt/Reject/Defer decision for every material candidate.

The fast-search review must cover published orbit-to-field and
satellite-to-survey screening methods, including vectorized propagation,
adaptive temporal sampling, conservative swept-angle or swept-region bounds,
spherical spatial indexing, interval indexing, hierarchical sky
pixelizations, and combined space-time indexes. It must determine which
methods can guarantee that no true crossing is discarded, what bounds are
needed for fast low-Earth-orbit motion near the zenith, and whether an
observer/night catalogue index is preferable to per-query propagation.

The photometry review must cover reflected-sunlight models, range and phase
dependence, projected area, shape, attitude and tumbling, bidirectional
reflectance or empirical phase functions, passband and solar spectrum,
atmospheric extinction, Earth umbra and penumbra, specular flares, published
standard magnitudes, and empirical survey calibrations. It must distinguish a
model magnitude or magnitude distribution from a guaranteed observed
brightness or trail detection.

The same audit must select authoritative OMM/TLE sources and define identity,
provenance, licence, snapshot time, element epoch, freshness, decay/removal
policy, SGP4 variant, TEME meaning, time scales, Earth orientation,
topocentric and refraction policy, shadow/illumination model, uncertainty
communication, catalogue scale, and representative performance workloads.
Characterize the maximum angular motion that the candidate filter must
conservatively enclose. Add no visible satellite or public crossing command.

### 50S.1 — Provider-neutral satellite crossing domain

**Status:** Accepted by Fernando on 2026-09-15; merged through PR #123.

`satellite_crossings.py` defines immutable satellite identity, terrestrial
observer/site, inclusive UTC interval, explicitly framed closed circular FoV,
crossing candidate, and normalized connected-visit result contracts. Provider
candidates retain source, optional orbit/snapshot evidence, provenance, and
warnings; normalized results enforce ordered in-interval event instants and
closed-boundary intersection semantics. The module imports only the shared
`CoordinateSpec` vocabulary and remains independent of provider acquisition,
propagation, charts, projection, rendering, and export.

Spherical rectangles, WCS/instrument footprints, fixed Alt/Az and moving
fields, SatChecker adaptation, propagation, exact crossing verification,
illumination physics, reporting, and drawing remain later milestones.

Fernando accepted 50S.1 after the focused Mac gate passed all 139 tests in
3.07 seconds and the complete plugin-disabled suite passed all 2,428 tests in
85.52 seconds. PR #123 merged the verified implementation into the satellite
integration branch as commit `23b851b`.

### 50S.2A — SatChecker provider-contract audit

**Status:** Accepted by Fernando on 2026-09-15.

The audit in `satchecker_provider_contract_audit_50s2a.md` reviews SatChecker
1.8.0 at source commit `a638d72`. It records the versioned endpoints, explicit
UTC-to-UT1 conversion boundary, source-inferred geometric topocentric
ICRF/ICRS-oriented directions, one-second stop-exclusive sampling, 1.2-radius
candidate envelope, async states, serial no-retry access, exact local cache,
bounded failures, and unresolved response-data redistribution terms. It changes
no runtime behavior. Fernando's acceptance authorizes only the bounded 50S.2B
cached-adapter implementation.

### 50S.2 — SatChecker crossing adapter

**50S.2B status:** Accepted by Fernando on 2026-09-15.

`satchecker.py` provides the versioned geometric circular-field request,
explicit no-download UTC-to-UT1 conversion, exact-byte receipt, one-shot
submission and polling, explicit task states, provider-schema normalization,
candidate/sample evidence, and content-addressed exact local cache. It
serializes the complete Wenu request and Earth-orientation identity into the
cache key and fails closed on HTTP, media, JSON, identity, count, task, sample,
or cache drift.

Successful output is only `SatelliteCrossingCandidate` plus ordered
`SatCheckerSample` evidence. The implementation does not construct
`SatelliteCrossingResult`: provider samples do not establish exact entry,
closest approach, exit, or one connected visit. Synthetic source-shaped tests
perform no network access. No waiter loop, automatic retry, CLI, live fixture,
report, propagation, drawing, or export is added. The bounded live check
confirmed fail-closed IERS coverage, real PENDING submission/poll receipts, and
a later SUCCESS receipt normalized to 13 candidates and 26 ordered samples.
The focused provider/domain gate passed 45 tests, the expanded focused gate
passed 168 tests, and the complete suite passed all 2,457 tests. Acceptance
closes 50S.2B; accepted 50S.3A now authorizes only bounded 50S.3B reporting and shared-path drawing.

### 50S.3A — Satellite report and drawing contract audit

**Status:** Accepted by Fernando on 2026-09-15.

Freeze honest human-readable/JSON reporting and shared-path drawing for
provider-sampled candidate evidence. SatChecker samples are not exact connected
crossings: 50S.3 must not invent entry, exit, closest approach, continuous
containment, interpolation, propagation, illumination, or brightness. Reserve
stable semantic identity by full NORAD catalogue identifier and require one
normalized evidence source for every output.

### 50S.3B — SatChecker sampled-candidate reports and tracks

**Status:** Accepted by Fernando on 2026-09-15.

Implement deterministic reports and an
already-normalized-evidence sky layer. The layer emits typed spherical points
and open polylines and then uses Wenu's shared coordinate, projection,
preparation, renderer, semantic SVG, and PNG/PDF/SVG export paths. No CLI
acquisition workflow, polling loop, exact crossing solver, or 50S.4 work is
included.

The candidate implementation adds deterministic text/JSON reports, open
sampled-track or singleton-point geometry, optional UTC-labelled sample
points, stable full-NORAD semantic paths, and a shared PNG/PDF/SVG pipeline
gate. It remains network-free and does not synthesize exact crossing events.
Fernando accepted the synthetic report and centered FoV chart across PNG,
PDF, and semantic SVG on 2026-09-15. The final focused gate passed all 217 tests and the complete plugin-disabled
suite passed all 2,473 tests in 83.98 seconds. Fernando accepted 50S.3B on 2026-09-15. Acceptance closes SatChecker sampled
candidate reporting/drawing and authorizes only 50S.4 next.

### 50S.4A — Snapshot and propagation contract audit

**Status:** Accepted by Fernando on 2026-09-15.

Freeze the direct SGP4 dependency, synthetic distributable snapshot, OMM
element domain, content digest, Vallado validation, split-Julian-date,
geometric TEME state, no-download Earth-orientation, topocentric oracle, and
developer-specimen boundaries. This audit changes no runtime, dependency, or
packaged data. The focused documentation gate passed all 128 tests and the
branch diff check was clean. Acceptance closes 50S.4A and authorizes only
50S.4B immutable OMM element and snapshot work; propagation remains
unauthorized.

### 50S.4B — Immutable OMM element snapshot

**Status:** Accepted by Fernando on 2026-09-15.

The candidate adds typed canonical GP/OMM records, manifest and content-digest
validation, per-record digests, installed-resource loading, deterministic
full-NORAD ordering, duplicate rejection, immutable lookup, and a three-record
synthetic LEO/MEO/geosynchronous-like snapshot. It declares
`sgp4>=2.25,<3` directly. No live provider record, TLE adapter, propagation,
TEME state, Earth-orientation/topocentric transformation, or crossing result
is included. The initial focused domain and packaging gate passed all 29 tests. At
production commit `d3cb597`, the expanded gate passed all 158 tests and the
complete plugin-disabled suite passed all 2,483 tests in 87.11 seconds. An
isolated installed-wheel check loaded the snapshot from `site-packages`,
verified its exact manifest digest, and returned all three ordered identifiers.
Fernando accepted the scientific and architectural boundary on 2026-09-15.
Acceptance closes 50S.4B and authorizes only 50S.4C validated SGP4/TEME
propagation.

### 50S.4C — Validated SGP4/TEME propagation

**Status:** Accepted by Fernando on 2026-09-15.

The candidate maps accepted OMM fields explicitly into the upstream
Vallado-compatible propagator with WGS-72, split Julian dates, typed geometric
TEME position/velocity, explicit errors, element age, and scalar/array parity.
Pinned published near-Earth and deep-space reference vectors plus a terminal
error case validate the wrapper. Preflight corrected the synthetic identifiers
from unsupported 900001–900003 to valid six-digit 300001–300003 and regenerated
all affected digests; no hidden surrogate identity is used. The initial element/SGP4 gate passed all 15 tests. At production commit
`e0d7c78`, the expanded gate passed all 167 tests and the complete
plugin-disabled suite passed all 2,492 tests in 86.88 seconds. An isolated
installed-wheel check verified the corrected snapshot digest and successful
TEME/WGS-72/status-zero propagation of all three records. No Earth-fixed or
observer state is produced. Fernando accepted 50S.4C on 2026-09-15 after the
15-test initial gate, 167-test expanded gate, all 2,492 tests, the 132-test
documentation gate, and installed-wheel propagation check. Acceptance closes
50S.4C and authorizes only 50S.4D Earth-orientation and topocentric state work.

### 50S.4D — Earth-orientation and topocentric state

**Status:** Accepted by Fernando on 2026-09-15.

The candidate uses Astropy's declared TEME → ITRS → observer-subtracted
Cartesian chain with automatic IERS download and degraded accuracy disabled,
exact installed IERS-A SHA-256 and coverage, WGS-84 geodetic sites, vacuum
horizontal directions, and a topocentric geometric direction expressed in
GCRS axes. It fails closed outside local EOP coverage. Direct Cartesian
evidence, independent Skyfield comparison, constructed zenith/horizon/wrap
geometry, pathological sites, and installed LEO/MEO/GEO-like specimens pass
the 17-test dedicated and 89-test expanded Mac gates. The 133-test
documentation gate and complete plugin-disabled suite of 2,511 tests in 95.10
seconds also pass, and the final branch diff check is clean. Fernando
scientifically and architecturally accepted 50S.4D on 2026-09-15. Acceptance
closes the Earth-orientation/topocentric boundary and authorizes only bounded
50S.4E propagated-specimen builder work. No field-intersection solver is
included.

### 50S.4E — Propagated specimen builder and closure

Add a deterministic network-free developer builder that consumes the installed
synthetic snapshot and writes sampled propagated tracks/query inputs with full
provenance. Outputs say **propagated sampled specimens — not verified
crossings**. Exact crossing results and completeness claims remain 50S.5.
Close 50S.4 only after package, numerical, focused, full-suite, and developer
product acceptance.

### 50S.5 — Complete local FoV-crossing oracle

Implement a complete scan of every valid object in a selected snapshot with
adaptive interval subdivision, conservative motion bounds, bracketed boundary
roots, and closest-approach refinement. Boundary touch counts; disconnected
visits remain separate. This slower implementation remains independently
callable as the scientific oracle after optimization.

### 50S.6 — Conservative local crossing acceleration

Add, in order, topocentric orbital-plane/FoV-cone and radial-shell rejection,
phase/reachable-arc rejection from epoch and mean motion, Earth-occultation and
horizon rejection, then vectorized coarse SGP4 states with conservative motion
and curvature bounds. Prove zero false negatives against 50S.5 over central,
grazing, between-sample, zenith, horizon, seam, pole, short-exposure, and
interval-end cases.

HEALPix/time indexing remains optional. Add it only if medium/full-snapshot or
many-pointing benchmarks show material benefit beyond the plane/phase filter
cascade. Any pixel cover must enclose the complete swept trajectory tube, and
every candidate still reaches the exact solver.

### 50S.7 — Independent illumination and night geometry

Treat illumination as component-resolved geometry. Calculate direct Sunlight,
solar Earthshine, direct Moonlight, and Lunar-Earthshine (Moonlight reflected
by Earth), with finite Sun/Earth/Moon geometry, umbra, penumbra, lunar phase,
visibility, incident directions, and shadow transitions recorded independently
of crossing. Separately report Sun and Moon altitude and twilight/night state
at the observer. Default results retain all geometric crossings and annotate
each illumination component rather than silently erasing eclipsed crossings.
Audit Caddy et al. (2026), arXiv:2609.07057, and its modified `lumos-sat`
model before choosing any implementation.

### 50S.8 — Apparent-brightness estimation and validation

Use the strongest defensible model level for each of Sunlight, solar
Earthshine, Moonlight, and Lunar-Earthshine: object-specific empirical models,
satellite-family distributions, broader population distributions, or explicit
`unknown`. Sum fluxes, never magnitudes. Retain passband, range normalization,
solar/lunar phase dependence, Earth/lunar reflectance or BRDF, satellite
surface and attitude assumptions, atmospheric extinction, model epoch,
scatter, calibration provenance, validity domain, and limits. Treat ordinary
brightness and specular glints separately; absent flare evidence is `unknown`,
never zero probability. Validate materially different families and geometries
against time-resolved calibrated observations before accepting tolerances.

### 50S.9 — Detector-specific contamination

Combine crossing geometry and brightness distributions with angular speed,
exposure, optics, aperture, throughput, passband, defocus/PSF, pixel scale, sky
background, saturation, blooming, shutter behavior, and detector response.
Report assumptions and uncertainty. Do not reinterpret apparent magnitude as
trail signal or detectability.

### 50S.10 — Night, season, and sky-position products and closure

Generate reproducible maps, tables, and distributions versus local night time,
season, observer, pointing, FoV, and exposure duration. Close with provider and
snapshot provenance, numerical validation, complete-scan equivalence,
performance evidence over progressively larger snapshots, cached SatChecker
comparisons, observed-trail specimens when available, PNG/PDF/SVG inspection,
and public documentation. Do not create a satellite-specific projection,
renderer, exporter, or parallel sky pipeline.

## Program 50B — Publication legibility and economical printing

### 50B.0 — Accepted-practice review

Research and report current accepted practice before changing Wenu appearance.
Use maintained primary or standards-body material where available and clearly
distinguish normative requirements, professional-print recommendations,
accessibility references, cartographic convention, and empirical practice.

The review must cover:

- PDF print exchange, font embedding, output intent, color spaces,
  transparency, physical page boxes, and scale;
- ordinary office printing, professional printing, grayscale, pure black, and
  photocopy reproduction;
- nominal point size versus perceived size, x-height, weight, viewing distance,
  label spacing, and reduction after export;
- minimum reproducible line and symbol dimensions;
- luminance contrast for text and meaningful non-text graphics;
- redundant encodings using size, shape, line weight, and dash pattern rather
  than color alone;
- magnitude-dependent star symbols, crowded-field selection, grid hierarchy,
  line crossings, label collision, legends, angular scale, and apparent
  precision in respected astronomical and cartographic publications;
- needs of older readers and classroom handouts.

The review must evaluate the ISO 15930 PDF/X family, relevant print-production
standards, accessibility contrast guidance such as WCAG as a reference rather
than an automatic print rule, and empirical measurements from respected
printed star atlases. It must not invent universal minimum sizes where the
evidence depends on process, stock, printer, viewing distance, or reduction.

### 50B.1 — Wenu publication-standard decisions

Publish and review the Adopt/Adapt/Reject/Defer ledger. Define accepted Wenu
physical-output profiles only after that review. Candidate use cases include
full-page publication, half-page handout, book-column figure, ordinary
grayscale office print, monochrome photocopy-safe print, and classroom
projection.

For every accepted profile decide:

- intended final physical dimensions and viewing conditions;
- minimum text size by semantic role;
- minimum star-symbol diameter and line width by semantic role;
- contrast hierarchy and permitted gray levels;
- maximum useful content and label density;
- magnitude-limit and grid-label adjustment rules;
- legend requirements;
- whether post-export reduction is permitted;
- font embedding, PDF metadata, color-space, and print-exchange requirements;
- required physical print and reduction tests.

Fernando's printed scientific and pedagogical review is required before these
values become Wenu defaults or named profiles.

### 50B.2 — Physical-output measurement harness

Measure representative Wenu regional, binocular, circumpolar, all-sky, and
applicable planisphere products at their declared final sizes. Prefer vector
geometry and physical units over inference from raster pixels.

### 50B.3 — Monochrome and limited-grayscale styles

Implement the accepted profiles. Monochrome must remain usable without color;
limited grayscale must use only accepted reproducible levels. Keep ownership
separate: detail selects content, style selects appearance, output mode owns
physical dimensions and scale, chart type owns geometry, and furniture owns
legends.

### 50B.4 — Physical print and reduction acceptance

Produce actual-size PDF test sheets and declared reduction matrices. Inspect
ordinary printer output, grayscale behavior, and photocopy behavior where
practical. Screen PNG review is not sufficient.

### 50B.5 — Publication-style closure

Record accepted numerical standards, named profiles, examples, regression
products, limitations, and the human print-acceptance record.

### 50S.4E — Propagated specimen builder and closure (accepted)

**Status:** Accepted by Fernando on 2026-09-15.

The dedicated branch adds only
`tools/build_50s4_satellite_specimens.py` and its durable focused tests. The
tool composes accepted 50S.4B–D authorities into deterministic, network-free
**propagated sampled specimens — not verified crossings**, written only to a
caller-selected output directory. It records snapshot, grid, observer,
Earth-orientation, propagator, and software identities.

50S.4E does not emit `SatelliteCrossingResult`, search a complete catalogue,
derive entry/exit or closest approach, select production solver tolerances, or
authorize 50S.5. Closure still requires focused and full Mac gates, clean diff
evidence, inspection of the generated JSON, and Fernando's scientific and
architectural acceptance.

#### Accepted 50S.4E measured gates

The dedicated, expanded, and documentation Mac gates passed 10, 99, and 134
tests respectively; the complete plugin-disabled suite passed all 2,522 tests
in 105.38 seconds. The inspected generated specimen had SHA-256
`16137e9380404dca03789532ab029c4159755c69dd2ab0ca5990a82cd9c42374`,
preserved ordered identities 300001–300003, and declared the exact snapshot
and bundled IERS-A digests. The branch and diff checks were clean. Fernando scientifically and architecturally
accepted 50S.4E on 2026-09-15, closing 50S.4 and authorizing only bounded
50S.5 complete local FoV-crossing oracle work.

50S.6 acceleration, illumination, photometry, detector effects, CLI, reporting,
and drawing remain unauthorized.


### 50S.5A — Complete local crossing-oracle audit (accepted)

**Status:** Accepted by Fernando on 2026-09-15.

Freeze the coordinate compatibility, immutable query, declared tolerance,
validated numerical completeness, adaptive subdivision, root/extremum,
connected-visit, fail-closed, provenance, ownership, and independent
analytic/adversarial validation contracts before runtime work.

Acceptance authorizes only bounded 50S.5B implementation of the exhaustive
three-record local oracle. It does not pre-accept numerical tolerances, close
50S.5, or authorize 50S.6 acceleration, illumination, photometry, CLI,
reporting, drawing, or additional footprint types.


The candidate 50S.5A focused documentation gate passed all 136 tests in 3.27
seconds and the corrected branch diff check was clean. The final acceptance
documentation gate passed all 136 tests in 3.00 seconds. Fernando scientifically
and architecturally accepted 50S.5A on 2026-09-15. Only bounded 50S.5B is
authorized next; 50S.6 and later behavior remain unauthorized.

### 50S.5B — Complete local crossing-oracle implementation (accepted)

**Status:** Scientifically and architecturally accepted by Fernando on
2026-09-15.

The accepted implementation introduces the dedicated local numerical owner, immutable query,
explicit convergence failure, exhaustive all-record scan, adaptive motion and
curvature evidence, bracketed entry/exit refinement, bounded tangent detection,
recursive tolerance-connected visit assembly, deterministic ordering, and
complete SGP4/IERS/observer/solver provenance. It adds no 50S.6 acceleration or
later satellite behavior.

Mac verification passed the 13-test dedicated oracle gate in 60.62 seconds,
the 108-test expanded gate in 70.80 seconds, the 137-test documentation gate
in 3.33 seconds, and all 2,538 plugin-disabled tests in 163.36 seconds. The
working tree was clean and `git diff --check aa6f91a...HEAD` passed. Acceptance
closes 50S.5 and authorizes only a documentation-first 50S.6 conservative local
crossing acceleration audit. Runtime acceleration, 50S.7, and all later
satellite behavior remain unauthorized.

### 50S.6A — Conservative local crossing acceleration audit (accepted)

**Status:** Scientifically and architecturally accepted by Fernando on
2026-09-15.

The accepted audit preserves the independently callable 50S.5 exhaustive oracle and
defines tri-state conservative selection, recorded rejection inequalities,
topocentric cone/orbital-shell bounds, exact-oracle equivalence, stage isolation,
and benchmark admission. It rejects horizon and Earth-occultation removal under
the current geometric query semantics and defers phase, coarse vectorized
states, and HEALPix/time indexing.

Candidate verification passed all 138 plugin-disabled documentation tests in
3.99 seconds on Fernando's Mac. The working tree and corrected branch diff
check were clean.

Acceptance authorizes only bounded 50S.6B implementation of the first
topocentric cone/orbital-shell selector. Phase/reachable-arc filtering, coarse
vectorized propagation, HEALPix/time indexing, horizon/occultation filtering,
50S.7, and all later behavior remain unauthorized.

### 50S.6B — First conservative cone-shell selector (accepted)

**Status:** Scientifically and architecturally accepted by Fernando on
2026-09-16.

The accepted slice installs immutable policy, decision, and selection evidence plus
one conservative selector. Its admitted domain is only the installed synthetic
snapshot and intervals no longer than 60 seconds. It uses an accepted initial
state and a deliberately outward relative-displacement bound; strict
whole-interval non-overlap permits rejection and every uncertainty is
`indeterminate`.

The selector does not coordinate exact solving or change 50S.5. The dedicated
gate passed all 9 tests in 34.58 seconds and the expanded
acceleration/oracle/crossing/element/SGP4/topocentric/package gate passed all
78 tests in 99.99 seconds. The documentation gate passed all 139 tests in 4.72
seconds, the complete plugin-disabled suite passed all 2,549 tests in 200.47
seconds, and `git diff --check d609322...HEAD` was clean. Acceptance authorizes only a
documentation-first 50S.6C audit of exact-solver coordination, broader-domain
evidence, and benchmark admission. Further runtime acceleration remains
unauthorized.

### 50S.6C — Exact-solver coordination and admission audit (accepted)

**Status:** Accepted by Fernando on 2026-09-16.

Freeze the shared exact-record seam, complete decision-coverage validation,
fallback and fail-closed behavior, exhaustive-result equivalence,
broader-domain evidence matrix, and reproducible benchmark-admission rules
before runtime coordination.

The accepted 50S.5 exhaustive route remains independently callable and default.
The accepted 50S.6B selector remains restricted to
`synthetic_50s4b_v1` and at most 60 seconds. The three-record snapshot proves
composition, not useful speed. This audit adds no runtime coordinator, broader
domain, benchmark product, new selector stage, or performance claim.

Fernando scientifically and architecturally accepted 50S.6C on 2026-09-16.
Acceptance authorizes only bounded 50S.6D exact-solver coordination with the
existing selector and admitted domain. Broader-domain activation, benchmark
claims, default enablement, phase/coarse/index stages, 50S.7, and later behavior
remain unauthorized.


### 50S.6D — Bounded accelerated exact-solver coordination (accepted)

**Status:** Accepted by Fernando on 2026-09-16.

Extract one unchanged package-internal exact-record seam from the exhaustive
50S.5 oracle. Keep the exhaustive public route independently callable and
default. Add one opt-in coordinator that validates complete ordered selector
evidence, routes retain and indeterminate decisions through the shared seam,
and omits only accepted reject decisions.

Return exact crossing results separately from immutable acceleration evidence.
Selector exceptions fall back to exhaustive solving by default or fail closed
under explicit policy; malformed evidence and rejection outside the admitted
three-record, 60-second domain fail closed. Require fake-selector invariant
tests, instrumented exact-evaluation accounting, and real-selector equality
with exhaustive results.

This slice adds no broader domain, benchmark claim, default enablement,
phase/coarse/index stage, illumination, photometry, CLI, reporting, drawing,
or 50S.7 behavior.


Candidate verification at commit `a7aecba` passed all 37 dedicated tests, 93
expanded immediate-seam tests, 141 documentation tests, and the complete 2,566
plugin-disabled tests. Fernando scientifically and architecturally accepted 50S.6D on 2026-09-16.
No later acceleration milestone is authorized automatically.


### 50S.6E — Same-observer, airmass-bounded multi-FoV and interchange audit

**Status:** Accepted documentation-only audit.

The audit in `satellite_multifov_interchange_audit_50s6e.md` defines one
observer with any non-empty ordered number of independently timed circular
FoVs. The centre of every field must satisfy a configurable airmass limit
throughout its complete interval. The initial policy uses geometric vacuum
AltAz and plane-parallel `X = sec(z)` above the horizon, with `X_max = 2` by
default (exactly 30 degrees minimum centre altitude in this model). Only the
centre is checked; the FoV radius does not enter airmass admission. It is an
FoV admission condition, not a satellite horizon or occultation filter,
and it imposes no civil-date or inferred-twilight boundary. Ten FoVs are the reference workload and proposed default
internal processing chunk, never a hard-coded public limit. Identical intervals
are a maximum-reuse research case rather than a public precondition.

The audit separates bounded concurrency from genuine reduction in propagation
and coordinate work, requires exact per-field equivalence to independent
50S.5 calls, and defines 1/2/5/10/20/50-field evidence across disjoint,
overlapping, and identical intervals. It places a bounded coordinator in
50S.6F; representative catalogue admission, JSON/ECSV/VOTable reports, and
exact binocular/regional/stereographic chart tracks in 50S.6G; observatory
adapter auditing in 50S.6H; four-source Sunlight, solar Earthshine, Moonlight,
and Lunar-Earthshine geometry in 50S.7; component-resolved brightness in
50S.8; detector effects in 50S.9; and external-workflow validation in 50S.10.

This audit changes no runtime or output. Fernando scientifically and
architecturally accepted 50S.6E on 2026-09-16. Only a bounded 50S.6F
implementation is authorized next; every later claim remains separately
authorized.


### 50S.6F — Bounded atomic multi-FoV coordinator

**Status:** Accepted bounded implementation.

The accepted implementation adds an immutable Python batch of complete
`LocalSatelliteCrossingQuery` values. It requires one observer and snapshot,
unique ordered field identities, centre-only complete-interval airmass
admission, and at most 60 seconds per field in the installed synthetic domain.
Ten is the default internal processing chunk, never a public cardinality
limit. All fields validate before any crossing solve; every rejection is
returned in one ordered typed exception and no partial result is produced.

Valid batches compose the accepted 50S.6D single-field coordinator and preserve
input order, exact result meaning, independent field intervals and tolerances,
and separate airmass and acceleration evidence. This milestone establishes the
batch contract but makes no useful-speed or shared-physical-state-reuse claim.
CLI/file adapters, a validation-output file for a later second call, generic
reports, chart tracks, representative catalogue admission, and all 50S.6G+
behavior remain later.

Fernando scientifically and architecturally accepted 50S.6F on 2026-09-17
after 2,577 plugin-disabled tests passed. Only a separately bounded 50S.6G
audit is authorized next. Representative-scale catalogue admission, generic
reports, chart tracks, CLI/file adapters, and a validation-output file remain
unimplemented and unauthorized pending that audit.


### 50S.6G — Representative delivery, reports, files, and exact chart tracks

**Status:** Accepted documentation-only audit.

The accepted `satellite_delivery_audit_50s6g.md` decomposes delivery into an
external immutable snapshot seam; a policy-governed representative builder and
scale/equivalence matrix; one canonical exact-crossing model with deterministic
JSON, ECSV, and VOTable encodings; an atomic direct CLI plus JSON two-call file
protocol; certified exact local track evidence; binocular/regional products;
and a separate stereographic-planisphere audit and implementation.

File validation remains atomic. An invalid request file solves no fields and
may write one versioned validation-output JSON that records every rejected FoV
and embeds the ordered valid subset as a complete derived request. A second
explicit invocation revalidates that derived request before calculation.

All chart products reuse the canonical spherical-geometry, projection,
preparation, rendering, semantic-SVG, and export flow. 50S.6G reports and
tracks remain geometric: illumination, brightness, detector effects, direct
observatory adapters, scheduling decisions, and observatory writes remain
50S.6H–50S.10 work. This audit changes no runtime or output. Fernando
scientifically and architecturally accepted it on 2026-09-17 after all 145
plugin-disabled current-documentation tests passed in 4.36 seconds. Only
bounded 50S.6G.1A external immutable snapshot loading is authorized next.


#### 50S.6G.1A — External immutable snapshot seam

**Status:** Accepted bounded implementation.

The candidate adds an explicit local-directory loader beside the installed
snapshot loader. It accepts no implicit location and derives scientific
identity only from a completely validated manifest and canonical records
digest. The selected directory, `manifest.json`, and declared records file
must be real non-symlink filesystem objects. All accepted OMM semantics,
full-NORAD ordering, record-count, epoch, provenance, warning, and digest
checks remain shared with the installed route.

This slice performs no acquisition or network access, packages no
representative catalogue, and does not admit an external snapshot to the
50S.6F coordinator. It adds no builder, policy preflight, benchmark, CLI,
report, chart, track, illumination, or later 50S.6G behavior.

Fernando scientifically and architecturally accepted 50S.6G.1A on 2026-09-17
after the 164-test focused gate and all 2,583 plugin-disabled tests passed.
Only a separately bounded 50S.6G.1B representative snapshot preflight and
evidence audit is authorized next, not its implementation.


#### 50S.6G.1B — Representative snapshot preflight and evidence

**Status:** Accepted documentation-only audit.

The candidate `satellite_snapshot_preflight_audit_50s6g1b.md` defines a
two-phase CelesTrak policy receipt and human digest acknowledgement, one fixed
Active-group OMM-compatible CSV request, deterministic fail-closed
normalization, complete raw/canonical receipts, and atomic content-addressed
external publication. The Active group is labeled representative-scale rather
than complete population coverage; Space-Track, SupGP, multi-group unions, and
redistribution remain outside the slice.

Evidence retains synthetic, deterministic medium, and complete acquired Active
tiers; 1/2/5/10/20/50 FoVs; disjoint/overlapping/identical intervals; declared
geometry cases and observers; cold/warm resource measurements; selector and
exact-evaluation counts; and independent exhaustive equality. External
admission is digest-bound and evidence-only. No useful-speed, shared-state,
capacity, runtime-default, live-request, report, CLI/file, track, or chart claim
is made.

Fernando scientifically and architecturally accepted 50S.6G.1B on 2026-09-17
after all 147 plugin-disabled current-documentation tests passed in 4.54
seconds. Only bounded 50S.6G.1B.1 fake-transport policy-receipt and
deterministic-builder implementation is authorized next. A live provider
request and 50S.6G.1B.2 admission/evidence remain separately authorized.

**50S.6G.1B.1 implementation state.** The policy receipt, exact SHA-256
acknowledgement, fixed Active CSV normalization, raw receipts, staged
validation, and atomic external publication are implemented behind a mandatory
injected transport. The developer command is offline and consumes explicit
response files. A live CelesTrak transport/request remains a separate human
policy checkpoint; 50S.6G.1B.2 representative admission and evidence remain
future work.

Fernando accepted the 50S.6G.1B.1 implementation on 2026-09-17 after 175
focused plugin-disabled tests and all 2,594 plugin-disabled tests passed.
No live CelesTrak request or 50S.6G.1B.2 work is thereby authorized.

Any later second provider requires a separate audit and must be public,
reliable, and genuinely independent rather than a redistribution of CelesTrak
or Space-Track. Its first role is an explicit validation oracle; no automatic
fallback or catalogue merge is implied.

Fernando accepted the exact `non-HTTP 200` policy-clause compatibility
correction on 2026-09-17 after 10 focused tests and all 2,595 plugin-disabled
tests passed. The 14,643-byte policy receipt is bound to SHA-256
`67bf0faa7e026a7cd49799069db9d3355f2a867894133afd39e130d6185724aa`. No GP request was performed, and digest approval remains a
separate gate before the one authorized bulk request.

**50S.6G.1B.1 live-evidence closure.** Fernando accepted the strict CelesTrak
UTC-epoch normalization, exact captured HTTP media type, and the resulting
16,559-record external Active snapshot on 2026-09-17 after 15 focused and 2,600
complete plugin-disabled tests. The raw/canonical SHA-256 values are
`e54730e14b2097444c5e20bba6dd13d3e2d92f956797d49256ddb1a70ffe5014` and `e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`. Only one provider request occurred. Representative
admission, medium-tier selection, matrix evidence, and 50S.6G.1B.2 remain
separately accepted future work.


#### 50S.6G.1B.2A — External snapshot admission audit

**Status:** Accepted documentation-only audit.

The candidate isolates the first part of 50S.6G.1B.2: one explicit
evidence-only token bound to exact canonical-record SHA-256 plus validated
manifest identity. The selector, accelerated coordinator, and multi-FoV batch
currently admit independently by logical snapshot ID; a later bounded
50S.6G.1B.2B implementation would replace external ID-only authorization with
one shared predicate while preserving the installed synthetic default.

This slice changes no runtime. Deterministic medium selection is separately
50S.6G.1B.2C, and the exact-equivalence/resource matrix is separately
50S.6G.1B.2D. No report, CLI/file route, exact track, binocular/regional chart,
stereographic planisphere, illumination, provider request, runtime-default
change, or speed claim is authorized by this audit.

Fernando scientifically and architecturally accepted 50S.6G.1B.2A on
2026-09-17 after all 150 plugin-disabled current-documentation tests passed in
3.84 seconds; `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2B digest-admission implementation is authorized next.


**50S.6G.1B.2B accepted implementation.** The implementation provides one explicit
digest-plus-manifest admission token in a dedicated satellite policy owner.
The existing selector, accelerated coordinator, and multi-FoV batch consume
that same token before external work; the batch passes it into its default
single-field route. Ordinary synthetic defaults remain unchanged.

The accepted CelesTrak identity constant is evidence metadata, not a path,
loader, global allowlist, or automatic default. This implementation adds no
medium specimen, evidence matrix, external fixture, network access, report,
exact track, chart, illumination, provider fallback, or speed claim.
50S.6G.1B.2C and 50S.6G.1B.2D remain separately bounded future work.


Fernando scientifically and architecturally accepted 50S.6G.1B.2B on
2026-09-17 after 51 focused runtime tests, 151 current-documentation tests,
and all 2,611 plugin-disabled tests passed; the complete suite took 215.89
seconds. `git diff --check` and the working tree were clean. Only bounded
50S.6G.1B.2C deterministic medium-specimen work is authorized next; 50S.6G.1B.2D
matrix execution and later delivery remain separately unauthorized.


#### 50S.6G.1B.2C — Deterministic medium specimen

**Status:** Accepted documentation-only audit.

The candidate derives one external medium evidence tier from the exact admitted
Active parent without network access. It uses the acquisition stop instant for
signed element age, independent declared scalar bins, two digest-ranked
representatives per non-empty bin, deterministic fill to a configurable
default target of 256, and a complete receipt. It makes no statistical,
population-frequency, speed, capacity, or equivalence claim.

A later bounded implementation would own only offline selection and atomic
derived publication. The first real subset operation, 50S.6G.1B.2D matrix,
reports, files, exact tracks, and charts remain separately unauthorized.


Fernando scientifically and architecturally accepted 50S.6G.1B.2C on
2026-09-17 after all 153 plugin-disabled current-documentation tests passed in
4.58 seconds; `git diff --check` and the working tree were clean. Only bounded
fake-data implementation is authorized next. The first real medium selection,
50S.6G.1B.2D matrix execution, and later delivery remain separately
unauthorized.

### 50S.6G.1B.2C candidate implementation state

The bounded fake-data implementation is now a candidate. The dedicated
`satellites/snapshot_evidence.py` owner performs admitted-parent validation,
report and raw-response binding, deterministic independent-axis selection,
canonical receipt construction, and atomic content-addressed publication. The
offline `select-medium` developer command has no transport.

The focused 2026-09-17 gate passed 30 plugin-disabled tests in 5.99 seconds.
Scientific and architectural acceptance remains required before the first real
medium selection. 50S.6G.1B.2D matrix execution remains separately
unauthorized.

### 50S.6G.1B.2C accepted implementation

Fernando accepted the bounded fake-data implementation on 2026-09-17 at
`1d9d4e4`, after 2,622 plugin-disabled tests passed in 225.75 seconds and the
185-test focused gate passed in 9.03 seconds. The next possible step is one
separately authorized offline selection from the already accepted
16,559-record parent; it requires no provider request. This acceptance does not
authorize that operation or 50S.6G.1B.2D matrix execution.

### 50S.6G.1B.2C real-selection closure candidate

The external specimen contains 256 records with canonical-record SHA-256
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`.
Its canonical selection receipt has SHA-256
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
It derives from the accepted 16,559-record parent
`e80306c843b9e3004b1d5bf7a8e4e7eb76a4f56284cd659978dc9bd3461f2347`
using age reference `2026-09-17T15:52:23.000000Z`.

The authorized offline operation covered all 24 bins with a 48-record mandatory
union and 208-record deterministic fill. Parent bytes were unchanged and no
provider request occurred. Acceptance of this exact external artifact is the
remaining 50S.6G.1B.2C closure decision. 50S.6G.1B.2D remains separately
unauthorized.

### 50S.6G.1B.2C accepted real-selection closure

Fernando accepted the exact 256-record external specimen on 2026-09-17 at
`c4cd009`, after 157 plugin-disabled documentation tests passed in 4.66
seconds. The accepted subset digest is
`2e85c576e287a047b12fe58b9487f96533ae739c46a594945cedb4236f08ab8b`;
the receipt digest is
`1a1048a24d619ec15817dbbc63cb461240fbce243a5414f266179f9cba57a895`.
50S.6G.1B.2C is closed. Only a separately authorized 50S.6G.1B.2D matrix audit
may proceed next.

#### 50S.6G.1B.2D — Exact-equivalence and resource-matrix audit

**Status:** Candidate documentation-only audit.

The candidate binds the accepted 256-record medium and receipt identities to a
10-field same-observer, same-night matrix. Exhaustive and accelerated results
must be strictly equal as tuples, canonical bytes, per-field digests, and a
whole-matrix digest. Accelerated evidence must partition all 256 identifiers,
forbid fallback, and prove that no rejected record has an exhaustive crossing.

Resource observations are isolated, repeated, and descriptive only. A later
implementation would use fake data exclusively; real matrix execution requires
separate authorization. No delivery, charting, illumination, provider access,
or speed claim is authorized by this audit.

### 50S.6G.1B.2D accepted audit

Fernando accepted the exact-equivalence and resource-matrix audit on
2026-09-17 at `6e7a8b9`; 159 plugin-disabled documentation tests passed in
10.75 seconds. Only bounded fake-data matrix-harness implementation is
authorized next. Execution on the real accepted medium specimen and every
speed, capacity, delivery, track, chart, and illumination claim remain
separately unauthorized.

### 50S.6G.1B.2D candidate fake-data implementation state

The bounded fake-data-only equivalence owner is implemented in
`satellites/crossing_matrix.py` at candidate commit `19520f3`. Verification
on 2026-09-17 completed 2634 plugin-disabled full-suite tests in 230.25
seconds. The implementation creates strict canonical evidence and revalidates
the complete published manifest, but it has not read the accepted real
256-record specimen or executed the real ten-field matrix. Fernando's
scientific and architectural acceptance is required before a separately
bounded real-matrix execution may be authorized. Later 50S.6G delivery remains
unauthorized.

### 50S.6G.1B.2D accepted fake-data implementation

Fernando scientifically and architecturally accepted this bounded
implementation on 2026-09-17 after 2634 plugin-disabled full-suite tests passed
in 230.25 seconds at `19520f3` and 161 plugin-disabled
current-documentation tests passed in 3.32 seconds at `3ef6a4d`. The accepted
scope remains fake data only. Reading the accepted real specimen and executing
the real matrix remain unauthorized. Only a separately bounded real-execution
audit may proceed next; later 50S.6G delivery remains future work.

### 50S.6G.1B.2D real-execution readiness gate

The candidate readiness audit at integrated baseline `9bdf301` finds the real
matrix not ready to run. Before execution, Wenu still needs exact receipt
constraint validation, the frozen ten-field La Ligua fixture, a production
whole-interval airmass certifier, fresh-subprocess route workers, and the
explicit offline `run-equivalence-matrix` developer command. Only that
bounded production-path implementation and fake-data proof are authorized
next. Reading the real specimen, running the matrix, making a performance
claim, and advancing 50S.6G delivery remain separately unauthorized.

### 50S.6G.1B.2D accepted real-execution readiness finding

Fernando scientifically and architecturally accepted the not-ready finding on
2026-09-17 after 163 plugin-disabled current-documentation tests passed in
3.80 seconds at `054ac39`. The next authorized step is bounded fake-data
implementation of the production execution path. Reading the accepted real
specimen, executing the matrix, publishing real evidence, making performance
claims, and advancing later 50S.6G delivery remain separately unauthorized.\n

### 50S.6G.1B.2D candidate production execution path

The bounded candidate adds the exact receipt gate, frozen La Ligua fixture,
production airmass certifier, isolated worker protocol, and explicit offline
developer command required by the accepted readiness finding. The fixture uses
only 15- and 60-second intervals. Tests remain fake-data-only and are designed
to avoid repeated scientific route execution. No real specimen access or real
matrix execution is authorized before separate acceptance.\n

Candidate verification on Fernando's Mac completed at executable commit
`81f9031`: the 14-test focused matrix gate passed in 9.35 seconds, the
210-test immediate-boundary and documentation gate passed in 60.26 seconds,
and all 2,645 plugin-disabled tests passed in 243.71 seconds. `git diff
--check 5cd60fd...HEAD` and the working tree were clean. No accepted real
specimen was accessed and no real matrix was executed. The candidate still
requires Fernando's scientific and architectural acceptance.\n

### Accepted production-path implementation

Fernando scientifically and architecturally accepted the bounded fake-data
production-path implementation on 2026-09-18. The executable evidence remains
14 focused tests in 9.35 seconds, 210 immediate-boundary tests in 60.26
seconds, and all 2,645 plugin-disabled tests in 243.71 seconds at `81f9031`.
After documentation-only evidence recording, 164 current-documentation tests
passed in 3.94 seconds at `602eed7`; the whitespace check and working tree
were clean.

Preserve the exact accepted-medium and receipt constraints, digest-frozen
ten-field La Ligua fixture with only 15- and 60-second intervals, production
whole-interval airmass certifier, canonical fresh-subprocess worker/executor,
explicit offline command, and shortened fake-data test practice. This
acceptance does not authorize accessing the accepted real specimen, executing
the real matrix, publishing real evidence, making a performance claim, or
advancing later delivery. Any real execution requires a separate explicit
authorization.\n

### 50S.6G.1B.2D.1 candidate first real execution

The next proposed step is not more implementation. It is one separately
authorized offline execution against the exact accepted 256-record medium,
using one new empty external output root, the accepted 15/60-second fixture,
at most 80 fresh subprocess invocations, the existing timeout, and no retry.
The resulting external evidence requires independent acceptance before any
performance claim or later 50S.6G delivery.\n

### Accepted first-real-execution authorization

Fernando scientifically and architecturally accepted 50S.6G.1B.2D.1 on
2026-09-18 after all 165 plugin-disabled current-documentation tests passed in
5.07 seconds at `af8044a`; the whitespace check and working tree were clean.

This acceptance authorizes exactly one operator-started offline execution
against the exact accepted 256-record medium, using the three frozen digests,
exact acknowledgement, accepted ten-field 15/60-second fixture, one new empty
external output root with at least 2 GiB free, the existing 3600-second
per-subprocess timeout, and no retry or resume. It does not itself start the
run. The exact absolute Mac paths must be resolved before the command is
issued. Failure or interruption authorizes no restart. Successful evidence
remains external and unaccepted pending an independent review; no performance
claim or later 50S.6G delivery is authorized.\n

### 50S.6G.1B.2D.2 candidate progress display

Before the authorized first real execution, add only parent-process progress
visibility. Derive the total from the existing matrix policy, reuse the
accepted worker sequence, and exclude display text from evidence and timing.
Extend one existing fake protocol test; add no scientific run. The real run is
paused pending acceptance, merge, and renewed authorization.

## 50S.6G.1B.2D.2 candidate verification state

Candidate commit `b0b4432` passed 180 focused plugin-disabled tests in 5.44 seconds and the complete 2647-test plugin-disabled suite in 239.53 seconds on 2026-09-18; its diff check was clean. This verifies the bounded progress-display implementation but does not accept or merge it and does not renew authority for the real run.

## 50S.6G.1B.2D.2 accepted progress-display state

Fernando scientifically and architecturally accepted candidate `96b9ba0` on 2026-09-18 with the recorded 180 focused, 2647 full-suite, and 167 final-documentation plugin-disabled test results and clean diff check. The next actions are a separately requested merge and, only afterward, explicit renewal of the single real-run authorization.

## 50S.6G.1B.2D.3 renewed single-run authorization

Fernando explicitly renewed authorization on 2026-09-18 for exactly one real matrix run after progress-display merge `9c4b808`. Once this record is merged, only that bounded run may proceed. Any failure, interruption, or pre-existing output root consumes the authority; successful output remains candidate evidence pending independent review.

## 50S.6G.1B.2D.3 accepted renewed authorization

Fernando scientifically and architecturally accepted the renewed single-run record at `dd71e01` on 2026-09-18, with 169 documentation tests passing in 4.29 seconds and clean integrity checks. Merge and repeated external preflight remain prerequisites to starting the one authorized run.

## 50S.6G.1B.2D.4 candidate real-matrix evidence

The consumed single run from `9d93113` produced candidate report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` on 2026-09-18. Ten fields and 60 measured observations passed exact equivalence with zero fallback. All fields had zero crossings; record that limitation explicitly before any closure decision. No retry, second run, optimization, or universal performance claim is authorized.

## 50S.6G.1B.2D.4 accepted first real-matrix evidence

Fernando scientifically and architecturally accepted candidate `186e255` and report `d200f3920aeda64df4d385d6f695fc3a69694df519f1520341e90d25e3037258` on 2026-09-18. The closure establishes exact empty-result equivalence and partition integrity, explicitly not positive real-crossing validation because every field had zero crossings. Further serial closure review, refactoring, parallelization, or another real run requires separate authorization.


## 50S.6G.1B candidate bounded closure state

Integrated baseline `b010a6c` establishes the acquisition, immutable
admission, deterministic medium-specimen, exact empty-result equivalence, and
conservative partition foundation. The accepted real matrix had zero crossings
in every field. It does not establish positive real-crossing validation, a
full-snapshot matrix, the wider planned FoV-count matrix, comprehensive real
crossing geometries, or universal performance, capacity, concurrency, or reuse
claims.

The candidate closure does not renew the consumed execution authority and
changes no runtime. Missing scale/performance evidence is explicitly deferred
behind a future bounded audit. Until separate acceptance, 50S.6G.1B remains
open and 50S.6G.2A is unauthorized. Acceptance would authorize only a separate
50S.6G.2A documentation audit for the immutable report model, versioned JSON
Schema, deterministic JSON, and round trips—not implementation.


## 50S.6G.1B accepted bounded closure

Fernando scientifically and architecturally accepted the bounded closure on
2026-09-19 at `c62a451`, after all 173 plugin-disabled documentation tests
passed in 3.82 seconds with clean repository checks. 50S.6G.1B is closed only
for the acquisition/admission/evidence foundation, with exact empty-result
equivalence and conservative partition integrity. Every real field had zero
crossings, and all stated scale and performance limitations remain explicit.

The next authorized milestone is only the bounded 50S.6G.2A documentation
audit for the canonical exact-crossing logical model, versioned JSON Schema,
deterministic JSON, and round trips. Implementation is not authorized.


## 50S.6G.2A candidate exact-report audit

The candidate documentation audit defines one immutable canonical
exact-crossing report, packaged Draft 2020-12 JSON Schema, deterministic UTF-8
JSON, report identity digest, strict decoder, and typed/byte-identical round
trips. It preserves exact-local scientific status separately from SatChecker
sampled candidates and accepts validated zero-crossing fields as explicit
results.

This audit changes no runtime. ECSV/VOTable, CLI/files, tracks, charts,
illumination, brightness, detector effects, provider access, and another real
matrix run remain excluded. Implementation requires separate acceptance.


## 50S.6G.2A accepted audit state

Fernando scientifically and architecturally accepted the exact-report audit on
2026-09-19 at `835ddfe`, after 175 documentation tests passed in 3.27 seconds
with clean checks. The next authorized work is only the bounded immutable
logical model, packaged JSON Schema, deterministic JSON encoder/decoder, and
focused round-trip tests. 50S.6G.2B and later work remain unauthorized.


## 50S.6G.2A candidate implementation state

The bounded candidate implements only the accepted immutable exact-crossing
logical report, packaged closed Draft 2020-12 schema, deterministic JSON,
canonical report digest, strict typed decoder, and focused synthetic tests.
It preserves explicit zero-crossing fields and null version-1 future-science
values without recomputing any science.

ECSV/VOTable remains 50S.6G.2B; CLI/files and atomic publication remain
50S.6G.2C; exact tracks remain 50S.6G.3A. Charts, illumination, brightness,
detector effects, scheduling adapters, provider access, and another real run
remain unauthorized. Candidate verification and Fernando's separate
scientific and architectural acceptance are required.


## 50S.6G.2A accepted implementation

Fernando scientifically and architecturally accepted the bounded 50S.6G.2A
implementation on 2026-09-19. The executable candidate at `a65e5ac` passed
all 2,676 plugin-disabled tests in 234.08 seconds; the final pre-acceptance
documentation gate at `8af0d14` passed 179 tests in 5.05 seconds; diff and
working-tree checks were clean.

50S.6G.2A is complete within the audited JSON logical-model boundary.
50S.6G.2B ECSV/VOTable, 50S.6G.2C CLI/files and atomic publication, and
50S.6G.3A exact tracks remain separate future milestones. No later milestone
is authorized by this acceptance.


## 50S.6G.2B candidate audit state

A documentation-only audit now proposes lossless ECSV and IVOA VOTable 1.5
interoperability for the accepted exact report. The design uses one reusable
format-neutral tabular projection with thin adapters, retains explicit
zero-crossing fields, units, coordinate/time metadata, stable joins and order,
and reconstructs byte-identical canonical JSON with the same logical digest.

Candidate status authorizes no runtime work. Fernando's separate scientific and
architectural acceptance is required before implementation. 50S.6G.2C
CLI/files and atomic publication, 50S.6G.3A exact tracks, later visibility
science, provider access, and another real run remain separate and
unauthorized.

## 50S.6G.2B accepted audit state

Fernando scientifically and architecturally accepted the documentation-only
audit on 2026-09-19 at `ef14bc1`, after 181 plugin-disabled documentation
tests passed in 4.88 seconds and repository checks were clean.

Only the bounded pure in-memory interoperability implementation is authorized:
one reusable format-neutral tabular projection and thin ECSV/VOTable 1.5
adapters with strict lossless reconstruction. 50S.6G.2C filesystem/CLI
publication, 50S.6G.3A exact tracks, charts, visibility science, provider
access, and another real run remain separate and unauthorized.


## 50S.6G.2B complete implementation accepted

Fernando scientifically and architecturally accepted the complete bounded
50S.6G.2B implementation on 2026-09-19. Executable commit `3bbd82f` passed
208 focused tests in 6.68 seconds and all 2,689 plugin-disabled tests in
215.15 seconds. Documentation evidence commit `ece80c7` passed all 186
current-documentation tests in 4.60 seconds; diff checks and the clean,
synchronized Mac working tree passed.

50S.6G.2B is complete within its accepted boundary: one reusable
schema-derived projection, deterministic ECSV and VOTable 1.5/BINARY2
carriers, strict reconstruction, canonical JSON identity and
`report_identity_sha256`, and the Astropy 7.1.0 Unicode `__is_null`
companion contract. No later milestone is authorized by this acceptance.
50S.6G.2C filesystem/CLI publication and all track, chart, visibility,
provider, and new-execution work require separate audit and authorization.

## 50S.6G.2C candidate audit state

A documentation-only candidate now specifies the direct atomic CLI route and
the digest-bound two-call JSON file protocol. A first invalid file call solves
no FoV and publishes one deterministic validation record containing every
invalid FoV and the ordered valid subset. A second explicit call retains the
invalid audit entries, revalidates and calculates only that subset, and
publishes one no-clobber JSON/ECSV/VOTable bundle. This candidate authorizes no
implementation. 50S.6G.3A and later track/chart work remain unauthorized.

## 50S.6G.2C accepted audit and next authority

Fernando accepted the documentation-only CLI/two-call file-protocol audit on
2026-09-19 at `bcac404`. The next authorized step is only its bounded offline
implementation: direct atomic calculation, closed initial and validation JSON,
validated-subset second call, fixed digest-manifest bundle, safe no-clobber
publication, exit/interruption contracts, and focused tests. 50S.6G.3A and all
track, chart, provider, visibility, illumination, and brightness work remain
separately unauthorized.

## 50S.6G.2C candidate implementation

The candidate implementation is confined to the accepted offline CLI/file
protocol. It adds no later milestone. Verification and Fernando's separate
scientific and architectural acceptance are required before merge or
50S.6G.3A.

## 50S.6G.2C verified candidate state

The bounded implementation at `e08ebf5` is repository-verified but unaccepted.
The immediate 235-test gate and complete 2,709-test plugin-disabled suite
passed. Merge and 50S.6G.3A remain unauthorized pending Fernando's separate
scientific and architectural acceptance.

## 50S.6G.2C accepted implementation

The bounded offline CLI/file implementation is accepted and closed. Preserve
its explicit invalid-field audit record, validated-subset second call, fixed
lossless report bundle, digest manifest, no-clobber/symlink contract, exit
statuses, and interruption behavior. Only the bounded 50S.6G.3A documentation
audit is authorized next; exact track runtime and chart work remain
unauthorized.

## 50S.6G.3A candidate audit state

A documentation-only candidate now specifies immutable exact local track evidence for each accepted connected visit and a science-free output-neutral layer. It retains exact event anchors, per-sample UTC directions and range, declared coordinate identity, deterministic adaptive sampling, fail-closed limits, provenance, and a distinct track digest and semantic visit identity.

This candidate authorizes no implementation. 50S.6G.3B binocular/regional chart integration, 50S.6G.4A/B planisphere work, report or CLI changes, provider access, and visibility/illumination/brightness work remain unauthorized.

## 50S.6G.3A accepted audit and next authority

Fernando accepted the documentation-only audit on 2026-09-19 at `ce54971`. The next authorized step is only the bounded exact connected-visit evidence realizer and output-neutral layer, including exact anchors, deterministic fail-closed sampling, track identity, coordinate/provenance retention, and focused tests. 50S.6G.3B and 50S.6G.4A/B remain unauthorized.

## 50S.6G.3A candidate implementation

The bounded candidate implements exact connected-visit evidence, deterministic anchored adaptive sampling, fail-closed limits, identity/provenance, and output-neutral path/event layers. The implementation-preflight correction keeps the collection coordinate specification timeless and places UTC on the evidence and every sample. The 69-test focused gate passed. Full-suite verification and Fernando's separate implementation acceptance are required before merge or 50S.6G.3B.

## 50S.6G.3A verified candidate state

The complete bounded candidate at `f0a4164` passed all 2,728 plugin-disabled repository tests in 222.01 seconds; documentation, diff, and clean-tree gates also passed. Merge and 50S.6G.3B remain unauthorized pending Fernando's separate scientific and architectural implementation acceptance.

## 50S.6G.3A accepted implementation

The bounded exact connected-visit evidence and output-neutral layer implementation is accepted and closed. Evidence is realized once through accepted local science and reused without recomputation. The executable candidate passed 69 focused tests and all 2,728 plugin-disabled tests; final documentation closure remains authoritative.

Only the bounded documentation-first 50S.6G.3B binocular/regional chart-integration audit is authorized next. Chart implementation and 50S.6G.4A/B remain unauthorized.

## 50S.6G.3B candidate audit state

A documentation-only candidate now specifies explicit exact-track display requests for regional and binocular stereographic horizontal products. It freezes observer/reference-instant admission, fixed product-frame meaning, request-owned layer lifecycle, independent path/event/label controls, bounded provenance summaries, stable semantic SVG identity, and PNG/PDF/SVG acceptance specimens.

This candidate authorizes no implementation. 50S.6G.4A/B planisphere work, all-sky/circumpolar satellite tracks, report/CLI changes, providers, visibility, illumination, brightness, and detector effects remain unauthorized.

## 50S.6G.3B accepted audit and next authority

Fernando accepted the documentation-only audit on 2026-09-19 at `ef58180`. The next authorized step is only the bounded binocular/regional ordinary-request integration, lifecycle, detail/style/semantic/export seams, focused tests, and PNG/PDF/semantic-SVG specimens described by the audit. 50S.6G.4A/B and all later science remain unauthorized.

## 50S.6G.3B candidate implementation

The bounded candidate now carries immutable exact connected-visit evidence through ordinary regional and binocular request preparation and PNG/PDF/semantic-SVG export. It adds strict admission, independent path/event/label controls, request-owned cleanup, exact-visit semantics, bounded provenance, focused tests, and deterministic offline specimens. Physically plausible complete-track specimens and canonical clipping tests are separate evidence rather than one distorted trajectory.

Complete verification and Fernando's separate implementation acceptance are still required. 50S.6G.4A/B and all later science remain unauthorized.

### 50S.6G.3B accepted implementation and next authority

Fernando accepted the complete bounded binocular/regional exact-track implementation and authorized merge and cleanup on 2026-09-19. PR 172 merged it into `program/50s-crossing-foundation` at `05d4029` after 314 immediate, 2,741 complete, and 199 final documentation tests plus physical PNG/PDF/semantic-SVG review and clean repository checks.

Only a documentation-first 50S.6G.4A planisphere exact-track audit is authorized next. 50S.6G.4A/B runtime work and all later satellite science remain unauthorized pending separate acceptance.

## 50S.6G.4A candidate audit state

A documentation-only candidate now distinguishes the paired physical polar
planisphere from the ordinary horizontal full-sky planisphere and specifies
only stereographic north/south faces. It freezes event-specific non-recurrence
meaning, fixed GCRS/ICRS-axis projection, observer/reference admission,
intentional overlap, declination-cap clipping, longitude continuity, existing
horizon/mask/furniture separation, paired lifecycle cleanup, bounded
provenance, and PNG/PDF/semantic-SVG acceptance evidence.

This candidate authorizes no implementation. 50S.6G.4B, ordinary all-sky or
circumpolar satellite tracks, equidistant polar tracks, report/CLI changes,
providers, visibility, illumination, brightness, detector effects, scheduling
adapters, and 50S.7/50S.8 remain unauthorized.

## 50S.6G.4A accepted audit and next authority

Fernando accepted the documentation-only audit on 2026-09-19 at `c1d9015`.
The next authorized step is only the bounded 50S.6G.4B paired stereographic-
planisphere integration, focused evidence, and physical north/south PNG, PDF,
and semantic-SVG specimens described by the audit. Ordinary full-sky,
circumpolar, equidistant-polar, combined-face, pouch-sheet, visibility,
illumination, brightness, detector, scheduling, 50S.7, 50S.8, and later
satellite work remain unauthorized.

## 50S.6G.4B verified candidate state

Candidate `91eafff5` implements only ordinary AltAz stereographic planisphere
admission, focused evidence, and the physical La Ligua PNG/PDF/semantic-SVG
review tool. Focused and full repository gates passed, and the generated chart
was physically reviewed. Merge, acceptance, paired polar, circumpolar,
Galactic all-sky, provider, report/CLI, visibility, illumination, brightness,
detector, scheduling, 50S.7, and 50S.8 work remain unauthorized.

## 50S.6G.4A corrective audit state

Fernando rejected the unmerged 50S.6G.4B paired equatorial polar-planisphere
candidate because the intended product is the ordinary AltAz stereographic
planisphere. The 2026-09-19 paired-polar implementation authority is therefore
superseded.

A documentation-only corrective candidate now targets
ChartRequest(family="planisphere"), which already resolves to one
zenith-centred horizontal FullSkyChart with stereographic projection and a
horizon boundary. It proposes only reuse of the accepted 3A evidence, 3B fixed
AltAz product-frame rule, existing request lifecycle, FullSkyChart boundary,
canonical render/export path, semantics, and bounded provenance.

This candidate authorizes no implementation. Only after Fernando separately
accepts the corrective audit may a bounded corrected 50S.6G.4B admit exact
tracks on the ordinary planisphere and provide physical PNG, PDF, and semantic
SVG evidence. Paired polar disks, circumpolar and Galactic all-sky tracks, and
later satellite science remain unauthorized.

## 50S.6G.4A corrective audit accepted and next authority

Fernando scientifically and architecturally accepted the corrective
documentation audit on 2026-09-20 at 80855938 after all 201 plugin-disabled
current-documentation tests passed in 6.14 seconds and repository checks were
clean.

Only the bounded corrected 50S.6G.4B ordinary AltAz stereographic planisphere
integration, focused evidence, and one physical La Ligua PNG, PDF, and semantic
SVG specimen are authorized next. Paired polar disks, circumpolar and Galactic
all-sky tracks, provider or report/CLI changes, visibility, illumination,
brightness, detector effects, scheduling adapters, 50S.7, 50S.8, and later
satellite work remain unauthorized.

## 50S.6G.4B accepted implementation and 50S.6G closure

Fernando accepted the corrected ordinary AltAz planisphere implementation and
authorized merge on 2026-09-20. PR 176 merged final candidate `6bc623b` at
`f0730d8` after 252 focused, 2,744 complete, and 202 final documentation
tests, physical PNG/PDF/semantic-SVG review, and clean repository checks.

This closes 50S.6G delivery: representative snapshot evidence, interoperable
reports, the offline file protocol, exact connected-visit evidence, and exact
regional, binocular, and ordinary stereographic planisphere tracks are
accepted. Only a documentation-first 50S.6H Paranal, ELT, and general
observatory-planning adapter audit is authorized next. Adapter runtime, writes
to observatory systems, scheduling decisions, 50S.7 illumination, 50S.8
brightness, and later behavior remain unauthorized.
## Accepted 50S.6H observatory-planning adapter decision

Fernando accepted on 2026-09-20 the documentation-only audit in
`satellite_observatory_planning_adapter_audit_50s6h.md` proposes one bounded
next implementation after acceptance: a deterministic, offline general
planning-advisory JSON projection from the accepted exact crossing report.
Temporal overlap uses half-open planned and crossing intervals and applies no
brightness, illumination, severity, or scheduling policy.

Paranal p2 is a state-changing external system, so the proposed first slice
performs no network operation and no OB mutation. ELT remains a reserved,
unsupported profile pending a stable official operations interface and a new
audit. Only the bounded offline general planning-advisory implementation is
authorized next. Facility network access or writes, scheduling decisions, ELT
mapping, and 50S.7+ remain unauthorized.
## Accepted 50S.6H offline implementation state

The accepted bounded implementation provides the accepted general planning profile
as a pure offline projection. Frozen observation units reference existing
report `field_id` values and non-empty half-open UTC intervals. Output is
strict deterministic JSON with complete context, advisory rows, source report
and snapshot identities, scientific unknowns, and its own SHA-256 identity.

The candidate includes no Paranal or ELT operational profile, network client,
credentials, write behavior, scheduling policy, or 50S.7+ science. Acceptance followed the focused and complete test gates, offline specimens,
and clean repository evidence on 2026-09-20.
## Accepted complete 50S.6H gate

Revision `32dce675` passed 226 focused/documentation tests in 8.86 seconds,
2,769 complete tests in 217.10 seconds, offline positive and zero-row specimen
review, and clean repository checks. The general profile remains the only
admitted profile and performs no network access. Fernando accepted the complete verified candidate on 2026-09-20. After
merge, only the documentation-first 50S.7 audit is authorized next.

## Candidate 50S.7A illumination and night-geometry audit

The documentation-only 50S.7A candidate decomposes satellite illumination
into direct Sunlight, solar Earthshine, direct Moonlight, and
Lunar-Earthshine. It keeps finite-source occultation and observer twilight in
an output-neutral geometry owner, retains Earth-reflected terms as extended
directional fields, and defers spacecraft attitude/BRDF and apparent
brightness to 50S.8.

The proposed sequence is 50S.7B direct-Sun plus geometric-night state, 50S.7C
complete shadow-transition search, 50S.7D direct-source radiometry, 50S.7E
solar/lunar Earth-reflected fields, and 50S.7F component-bundle closure. This
candidate authorizes no runtime. Only 50S.7B may be considered after separate
scientific and architectural acceptance.

## 50S.7A accepted audit and next authority

Fernando scientifically and architecturally accepted the documentation-only
50S.7A audit on 2026-09-20 at `fdf7e005a41a5a4d45200f841e914815d37da870` after
206 plugin-disabled current-documentation tests and clean repository checks.

After merge, only the bounded 50S.7B direct-Sun and observer-night geometry
implementation is authorized: immutable geometry, finite uniform-Sun/WGS-84
vacuum occultation, typed shadow state, geometric twilight, provenance, and
focused offline validation. 50S.7C and later radiometry or reflected-source
work, 50S.8 brightness, 50S.9 detector effects, visibility, facility
integration, scheduling, and unrelated refactoring remain unauthorized.
## Candidate 50S.7B — Direct-Sun and observer-night geometry

The bounded candidate implements the first accepted illumination slice in
`satellites/illumination.py`: immutable same-instant ITRS geometry, uniform
finite-Sun occultation by the vacuum WGS-84 ellipsoid, typed shadow state,
geometric observer twilight, complete model/resource identity, and
bounded adaptive quadrature convergence evidence.

Focused unit evidence and an offline installed-DE440/Skyfield/SPICE validator
belong to this slice. The candidate remains unaccepted pending controlled
validation, complete repository gates, and Fernando's separate scientific and
architectural review. 50S.7C transition search and every radiometric,
reflected-source, brightness, detector, facility, visibility, and scheduling
slice remain unauthorized.
### Candidate 50S.7B validation progress

The 24-test focused gate and offline installed-resource validator passed at
`51b935f`. Selected SPICE classifications agree for sunlit, penumbra, umbra,
and antumbra; pinned DE440/Skyfield comparison agrees for 20 full-light and 5
full-shadow states. Complete-suite and final repository gates remain pending,
and 50S.7C remains unauthorized.

### Verified candidate 50S.7B gate

Revision `086e7da1` passed 291 expanded tests, 208 documentation tests, the
clean diff gate, and all 2,796 repository tests in 233.66 seconds, with exact
upstream and a clean tree. The candidate is ready for separate scientific and
architectural review. Merge, deletion, 50S.7C, and later work remain
unauthorized.

## Accepted 50S.7B — Direct-Sun and observer-night geometry

Fernando scientifically and architecturally accepted candidate `054ac53a` on
2026-09-21 after the complete numerical, repository, documentation, diff,
upstream, and clean-tree gates. PR 181 merge remains a separate explicit
decision.

After merge, the next permissible work is a documentation-first 50S.7C
shadow-transition audit. No transition solver implementation, radiometry,
reflected-source field, brightness, visibility, detector, facility, or
scheduling work is authorized by this acceptance.

## Candidate 50S.7C — Complete shadow-transition audit

The documentation-only candidate specifies one selected immutable snapshot
record over one closed UTC interval. A future solver must return every admitted
directed `sunlit`/`penumbra`/`umbra`/`antumbra` boundary with a
certified bracket or fail closed. It must use continuous finite-Sun/WGS-84
contact margins and conservative whole-interval exclusion, not visible-fraction
quadrature, fixed-cadence sign scans, chart samples, or the 50S.5 empirical
motion envelope.

The event product is observer-independent and output-neutral. The proposed
implementation remains in `satellites/illumination.py`, with only a minimal
shared geocentric ITRS extraction in the existing topocentric owner. The audit
authorizes no runtime. 50S.7D direct-source radiometry, reflected fields,
brightness, detector, visibility, facility, and scheduling work remain
unauthorized.

## Accepted 50S.7C shadow-transition audit

Fernando accepted the documentation-only audit at `030a6322` on 2026-09-21;
210 plugin-disabled current-documentation tests passed in 5.81 seconds and the
diff, upstream, and clean-tree checks passed.

After merge, only the bounded 50S.7C implementation is authorized: one selected
immutable record, one admitted closed UTC interval, continuous
finite-Sun/WGS-84 contact geometry, every directed class boundary, certified
brackets, deterministic identity, fail-closed budgets, a minimal shared
geocentric ITRS seam, focused tests, and offline independent event validation.
50S.7D+ and all report/chart/planning, brightness, visibility, detector,
facility, and scheduling integration remain unauthorized.

## Candidate 50S.7C — Shadow-transition implementation

The feature branch now contains the bounded observer-independent service
authorized by the accepted audit: shared geocentric ITRS state, continuous
finite-Sun/WGS-84 contact evidence, complete bounded search, six directed
adjacent transition kinds, certified UTC brackets, deterministic identity,
and fail-closed limits.

Executable `69375fab` passed 58 focused tests in 16.67 seconds. The offline
no-download validator independently reproduced full and annular four-contact
sequences with SPICE `gfoclt` and matched 20 full-light plus 5 full-shadow
Skyfield states using the installed DE440 kernel. Documentation and complete
repository gates remain next. The candidate is not accepted; 50S.7D+ and all
report/chart/planning or later scientific integration remain unauthorized.

## Verified candidate 50S.7C implementation gate

At exact candidate `bf877404`, the 311-test expanded gate, 212-test
documentation gate, clean diff, complete 2,816-test plugin-disabled suite,
exact upstream check, and clean-tree check passed. The expanded gate took
21.47 seconds, the documentation gate took 7.01 seconds, and the complete
suite took 218.58 seconds. The independent SPICE/Skyfield event receipt also
passed.

50S.7C now awaits Fernando's separate scientific and architectural review.
Merge, branch deletion, 50S.7D+, report/chart/planning integration, and all
later light, brightness, visibility, detector, facility, or scheduling work
remain unauthorized.
