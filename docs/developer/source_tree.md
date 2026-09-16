# Wenu source organization

**Architecture version:** 0.9

Milestone 46A extends the registered coordinate-grid family with native
observer-local `AltAzGrid` geometry. Selection remains in render-local detail,
appearance remains in style, and the chart type continues to own the horizon.
**Status:** Implemented

The current ownership and execution overview is
`diagrams/current_architecture_v0.9_overview.svg`. The coordinate-transformation
as-is state and planned 49B/49C change seams are
`diagrams/coordinate_transformation_as_is_v0.9.svg`. Actual coordinate
classes, dataclasses, functions, inheritance, and module placement are shown
in `diagrams/coordinate_static_structure_as_is_v0.9.svg`. The proposed
architecture 0.9.5 ownership is frozen in
`target_architecture_v0.9.5.md`; its living scientific equations, current
code map, object inventory, and provenance are maintained in
`coordinate_system_guide_v0.9.5.md` as the sole canonical source; other
review formats are generated from it on demand.

The source tree is organized by responsibility. Astronomical objects and sky
layers do not import chart or renderer policy, and all chart styles and modes
share the same geometry and rendering pipeline.

## Principal packages

```text
src/wenu/
├── coordinates.py              coordinate vocabulary and legacy conversion
├── coordinate_service.py       central Astropy-backed geometry transformation
├── positions.py                astronomical PositionProvider protocol and provider boundary
├── observer.py                 observing context
├── objects/                    catalogues and physical object layers
├── sky/                        celestial layers and draw orchestration
├── geometry/                   spherical/projected values and algorithms
├── projections/                coordinate-neutral map projections
├── charts/                     chart types, composition, detail, styles,
│                               legends, boundaries, and export workflow
├── rendering/                  preparation and Matplotlib backend
├── resources.py                installed-resource access
├── cli/                        installed command adapters
├── example_scripts/            packaged canonical user examples
├── data/                       distributed astronomical datasets
└── utils/                      general utilities
```

`coordinate_service.py` owns the accepted 49C.1 Astropy-backed transformation boundary for every `SphericalGeometry` kind. It preserves concrete geometry type, semantic arrays, metadata, curve segmentation, polygon rings, and grid component names. The merged 49C.2 milestone routes reference geometry, chart conversions, deep-sky geometry, constellation references, caches, and chart-orientation reference directions through this service. The 49C.3 candidate also owns the external `SkyCoord` compatibility adapter and every remaining production Astropy `transform_to()` call.

`coordinates.py` owns the immutable `CoordinateSpec`, `PositionStatus`, and `ObservationContext` vocabulary. The handwritten `radec_to_altaz()` authority is removed in 49C.3. `positions.py`
owns the structural `PositionProvider` protocol. In 49B.3,
`Stars`, `NonStellar`, and `OpenClusters` implement native ICRS point providers; extended morphology and constructed reference geometry remain outside the boundary. Skyfield's apparent topocentric Hipparcos realization remains specialized stellar provider work and is reused by constellation lines; it is not duplicated by `CoordinateService`. `geometry/spherical.py` exports the
`SphericalGeometry` type union, and every record carries mandatory coordinate
identity.

`projections/mollweide.py` owns coordinate-neutral equal-area projection and
longitude-seam topology for points, curves, grids, and polygon rings. It has
no astronomical-frame, chart, renderer, or Matplotlib dependency.

`projections/polar_azimuthal_equidistant.py` owns the backend-neutral linear
polar-distance projection for north- and south-centred physical sky disks. It
reuses the ordinary spherical geometry dispatch contract and contains no
chart, calendar, horizon, style, renderer, or export policy.

`charts/polar_binocular_targets.py` validates the packaged curated identifier
and compact-label policy in `data/polar_binocular_targets.json`. It returns
ordinary detail-selection contracts and contains no catalogue loading,
projection, renderer, or page-furniture implementation.

Within `sky/`, `maximal_sphere.py` owns the immutable catalogue load profile
and the one canonical complete-content factory. The resulting object is an
ordinary `CelestialSphere`; chart geometry and presentation remain outside
the factory.
Its ordinary `generate_celestial_sphere()` entry point leaves the sphere and
every canonical layer observer-independent. The compatibility
`build_maximal_sphere(observer, ...)` entry point remains available while the
request facade migrates.
`docs/developer/archive/milestone_history/49d_scene/celestial_scene_dependency_audit_49d1.md` records that this is
a load-time ownership boundary: ordinary spherical realization still flows
through `CelestialSphere.draw_chart()` and
`layer.spherical_geometry(observer, ...)`. It classifies celestial
background, future dynamic astronomical objects, and observer-local geometry,
and fixes their sole convergence before projection in an explicit spherical
product frame. Milestone 49D.1 adds no runtime module or alternate scene
graph.
`docs/developer/archive/milestone_history/49e_ephemeris/ephemeris_provider_contract_49e1.md` owns the accepted 49E.1
state-source/direction-realizer audit. `ephemeris.py` owns the frozen 49E.2
resource identity, geometric state request, complete position-velocity state,
and structural state-source protocol. It owns no kernel I/O, direction
realization, coordinate transformation, chart, or output policy. The deterministic contract source remains in
`tests/test_ephemeris.py`. `skyfield_ephemeris.py` now owns the first real
49E.3 adapter: it borrows the already-open Observer kernel, fingerprints its
exact bytes, records conservative common SPK coverage, and returns geometric
ICRF Cartesian states. It owns no kernel close, direction realization, or
installed moving-body layer. `coordinates.py::observer_altaz_spec()` requires explicit status at every
call site; no observer-local physical status is inferred from origin.

`sky/realization.py` owns the frozen 49D.2 `LayerRealizationContext`.
`sky/sky_layer.py::SkyLayer.realize()` owns the compatibility adapter, and
`sky/celestial_sphere.py::CelestialSphere.draw_chart()` selects it only for an
explicit typed context. Ordinary request paths still call the existing
`spherical_geometry(observer, ...)` route. The controlled provider and
dynamic layer exist only in `tests/test_layer_realization.py`; no installed
moving-object layer or alternate scene graph is added.
`sky/observed_cache.py` defines observer/time/source cache-key identity and
freezes shared point and polygon arrays; individual layers continue to own
their cached spherical realizations.
`sky/horizon.py` owns the semantic `HorizonReference` layer. It delegates its
single closed altitude-zero spherical curve to native `AltAzGrid` geometry
without registering the coordinate grid or acquiring projection, masking,
style, or chart-boundary responsibility.
`sky/constellation_lines.py` adapts the packaged Western `Ser` line record
into the `Ser1` and `Ser2` catalogue identities required by loading and
framing, while retaining both the visual line joining Caput to Cauda and
`Ser` as the caller-facing selection alias. The separate IAU boundary regions
are unchanged. Request-level IAU normalization remains in
`charts/constellation_resolver.py`.
Within `charts/`, `request.py` owns the immutable ordinary-user request graph,
including catalogue exclusions and the independent horizon-reference and
horizon-mask declarations; it contains no catalogue resolution, projection,
rendering, or export work.
`charts/chart_arguments.py` owns their shared `--horizon` and
`--horizon-mask` syntax with the other content controls.
`charts/command_line.py` and `charts/drawing.py` transport those declarations
through the common example and ordinary-Python adapters; they do not create
horizon geometry, masks, or appearance.
`charts/request_horizon.py` owns request-time removal and conditional
registration of the semantic horizon reference. It is independent of
`charts/request_grids.py`; neither module acquires style, masking, projection,
or example responsibility.
`charts/horizon_mask.py` owns projection-neutral preparation of the
above-horizon mask opening and stereographic field-visibility classification.
It delegates spherical AltAz geometry to `sky/horizon.py`, stereographic
projection-domain protection to `rendering/preparation.py`, and Galactic
transformation and Mollweide seam topology to their established chart and
projection owners. It does not compose masks, select appearance, or render.

`charts/styles.py` owns the flat semantic horizon-reference appearance and
the common resolved outside-mask style boundary. `charts/style_components.py`
stores the corresponding composed `GridStyle` reference fields and the one
existing `MaskStyle`; output-mode adapters may change those visual values but
not geometry. Circular wrappers pass the resolved mask mapping into regional
rendering rather than allowing a second fallback policy.
The horizon contracts are distributed by ownership: argument and drawing
tests cover the shared controls, request-horizon tests cover reusable-sphere
lifecycle, horizon-mask geometry tests cover field classification and frame
transformation, chart-family tests cover final boundaries, and composed-mask
tests cover seam grouping, intersection winding, and single-opacity drawing.
`charts/target_resolver.py` owns offline alias resolution over the packaged
`data/targets.json` cross-identification resource.
`charts/object_center.py` owns the overloaded, output-neutral conversion of a
resolved fixed target or descriptor-driven moving body into one apparent
observer-horizontal `ObjectCenter`. It delegates coordinates to
`CoordinateService` and moving directions to `SolarSystemPointLayer`; it owns
no name lookup, provider acquisition, projection, framing dimensions, style,
or rendering. `cli/chart.py` resolves an unambiguous moving-body selection
before `get_chart_view()` when that object must govern a regional center.
For an exact numbered-asteroid selection it also invokes installed-CLI
preflight before sphere or view construction. `minor_body_acquisition.py`
alone owns network access, coverage verification, locking, staging, and
content-addressed immutable publication. Downstream owners remain offline.
`charts/constellation_resolver.py` owns IAU abbreviation normalization and
offline teaching-group resolution over `data/constellation_groups.json`.
It is the sole translation boundary for Serpens line, boundary, and label
identities.
`charts/request_resolver.py` combines those resolved subjects with immutable
content selection and validates request ceilings against the selected
maximal-sphere profile. It performs no chart construction or rendering.
It also resolves explicit and family framing defaults while marking arbitrary
constellation framing as a downstream geometry operation.
`charts/regional.py` performs that geometry-derived framing from loaded
official constellation-region vertices, retaining figure endpoints as the
compatibility fallback for direct callers that do not request region framing;
the request resolver does not inspect sky geometry. It also owns the reusable
tangent-plane position-angle operation used to put celestial north, or another
explicit horizontal direction such as the north ecliptic pole, at chart top.
It also owns explicit named-versus-literal orientation resolution and the
backend-neutral pointwise parallactic/meridian tangent geometry retained for
future furniture. `charts/request_chart.py` may instead give the same chart a
fixed horizontal altitude/azimuth centre without changing selected content.
`charts/spatial_selection.py` owns vectorized field-footprint selection over
cached catalogue centers; it applies explicit exclusions, returns immutable
content, and does not render.
`charts/request_chart.py` maps a resolved request onto the established
chart types and invokes that selector; composition and export remain in their
existing modules.
`charts/all_sky.py` owns the complete-sphere Galactic Mollweide chart,
including its elliptical boundary, chart context, frame preparation, full
catalogue footprint, and optional disjoint constellation-mask openings.
`charts/request_generation.py` is the ordinary facade over those boundaries.
It owns observer/maximal-sphere lifetime for one-call generation and delegates
all composition, rendering, furniture, and saving to the existing canonical
APIs. Its prepared-request entry point permits later sphere reuse without a
parallel export pipeline.
The same module exposes `build_chart_request()` and `ChartRequestBuild` as the
family-neutral non-exporting preparation facade used by compatibility builders
and by `generate_chart_request()` itself. The result owns cleanup explicitly;
it does not create another construction or rendering path.
The generation facade also accepts a compatible caller-owned maximal sphere;
request observer identity and the declared load profile are checked before
resolution, and ownership remains with the caller.
`charts/request_grids.py` owns view-span-dependent request-time coordinate-grid
density and replacement. It registers only selected semantic grids
and removes prior grid layers so a reused sphere never accumulates duplicates;
it does not modify maximal catalogue content.
`charts/request_composition.py` owns immutable detail-policy and visual-style
overrides for one exact selected product. It deliberately contains no chart
geometry; `request_generation.py` consumes it only when calling the canonical
composition boundary.
`charts/composition.py` also applies the built-in all-sky stellar-area
adaptation after mode resolution and before caller style overrides, so the
renderer and magnitude furniture consume one resolved visual scale.
`charts/request_furniture.py` realizes family-neutral declarative chart and
observer context only after a request chart exists. It feeds the established
legend furniture and contains no chart construction or example policy.
Canonical chart execution and its downstream geometry and furniture helpers
accept an explicit scientific observer while retaining their bound-observer
compatibility form. This is the seam for the later observer-independent
maximal-sphere factory; it does not yet remove the observer accepted by the
existing factory.
`charts/view.py` owns the ordinary observer-bound geometrical view adapter. It
translates friendly arguments into the existing request resolver and chart
preparation boundary and returns frozen geometry/provenance without adding a
construction, projection, rendering, or export pipeline.
Projection and spherical coordinate-frame names are immutable request
geometry; the view exposes their resolved values rather than maintaining a
parallel tag.
`charts/projection_selection.py` pairs each registered projection identity
with an accepted spherical frame in one frozen value. Stereographic supports
both its established horizontal charts and the equatorial polar-disk
alternative. The module constructs the selected backend-neutral projection
lazily from chart-owned geometry and owns no chart family, calendar, physical
page, style, renderer, or export policy.
`charts/polar_planisphere.py` owns one north- or south-polar disk face:
projection choice, selected pole, limiting declination, normalized and
physical scale, handedness, exact circular boundary, square viewport, chart
context, and canonical render/export adaptation. It owns no paired-face,
calendar, registration, horizon, content, or appearance policy.
Its circular boundary also owns the final inset that suppresses constellation
label anchors before their text can enter the physical date ring.
`charts/polar_label_curation.py` owns reviewed south-face-only print
clearances and the quiet extended-Hyades marker. These presentation overrides
are applied after projection and do not alter catalogue selection, spherical
coordinates, constellation geometry, or the north face.
`charts/polar_planisphere_pair.py` owns paired-face resolution and frozen
assembly geometry. It validates shared scale and physical size, compatible
north/south polar radii, projection-aware opposite RA direction, common
centres and optional calendar/pivot radii, and reflected asymmetric
registration metadata. It draws no marks and contains no calendar, site,
content, style, renderer, or export orchestration.
`charts/polar_calendar.py` owns the immutable 365-day common-year calendar
model. It calibrates a neutral date ring from configurable longitude,
standard UTC offset, and non-leap reference year; advances by a closed mean
common-year step; and returns semantic day, true-month-arc, boundary, and
month-label-key records. It owns no face handedness, drawing, translation,
daylight-saving, horizon, content, style, or export policy.
`charts/polar_calendar_furniture.py` maps that neutral calendar onto a resolved
paired disk as immutable physical millimetre geometry. It owns daily and month
ticks, day and semantic month-label positions, outward-base rotations, the
reserved central star-disk radius, and projection-derived opposite face
handedness. It owns no Matplotlib realization, localized text, style, horizon,
astronomical content, or export orchestration.
Labelled-day identity is retained separately from tick length so a renderer
can emphasize those ticks by weight without changing calendar geometry.
`charts/polar_magnitude_scale.py` owns the polar-only magnitude intervals and
resolves their representative marker areas through the configured stellar
style. `charts/polar_magnitude_scale_rendering.py` is their shared Matplotlib
realization. Disk-page and pouch furniture retain separate millimetre
placements but reference the same immutable semantic scale.
`charts/polar_page_furniture.py` resolves one paired physical disk into
immutable A4 paper coordinates and semantic face information. It owns page
size, safe margins, the common disk centre, centre-punch radius, horizontally
reflected registration marks and their orientation glyphs, a measurable scale
ruler, bilingual classroom instructions, site/time calibration, face identity,
rights notice, coverage, product identity, and required source revision. It
consumes paired geometry but owns no chart projection, astronomical content,
style, localization framework, Matplotlib artist, or export orchestration.
`charts/polar_page_rendering.py` is the sole Matplotlib realization of those
resolved calendar and A4 page records. It expands the already-rendered polar
chart axes to the physical date-ring radius, draws Spanish month furniture,
and realizes the cut line, black centre punch, solid-black reflected
registration glyphs, scale
ruler, and semantic text on a transparent millimetre page axes. It calculates
no astronomy and performs no save.
`charts/polar_page_export.py` owns paired physical-product orchestration. It
creates an A4 print composition and physical disk axes for each resolved face,
then calls `PolarPlanisphereChart.export()` once per destination. The chart
continues through `export_composed_chart()`; its additional-furniture hook
realizes the page immediately before the existing single save. PDF metadata
records the product and source revision. No alternate sphere, renderer, or
export path is introduced.
`charts/polar_horizon_overlay.py` resolves the canonical semantic altitude-zero
curve through the existing horizontal-to-equatorial adapter, normalizes right
ascension to the local meridian, clips the result through each existing polar
chart, and maps it into immutable physical page coordinates. It owns the
paired horizon segments, observer latitude, meridian reference, and cut-
clearance value. Opposite face handedness remains owned by the paired polar
projections and is not reflected a second time by the overlay. Geographic
letters are deliberately absent: they are fixed pouch furniture, not projected
sky anchors. The module owns no catalogue selection, artist, calendar/hour
furniture, text placement, or save.
`charts/polar_pouch_furniture.py` rigidly translates the resolved horizon pair
onto the accepted folded A4 construction and owns the resulting physical
furniture records. It places the fold tangent to the bottom of the complete
195 mm disk, three identical 37.5-degree annular date windows with 5-degree
gaps, face-handed 19:00-05:00 hour marks, upright tangent numerals, external
short ticks, fixed geographic letters, `HORIZONTE`, the south-face title, and
side glue zones. Geographic text positions are paper instructions and never
projected sky anchors. The module calculates no astronomy, draws no artist,
and performs no save.
`charts/polar_pouch_rendering.py` is the sole Matplotlib realization of one
resolved pouch face. It draws the closed sky-window cut path, strengthened
astronomical horizon, three annular date-window cuts, partial hour circle,
upright numerals, external ticks, fixed labels, fold, disk guide, and black
glue zones. It consumes millimetre records and saves nothing.
`charts/polar_pouch_export.py` creates one actual-size A4 figure per resolved
face and delegates its sole save to the established `ExportOptions` boundary.
It requires explicit source provenance, preserves a non-tight A4 media box,
and owns no horizon, window, hour, label, or fold calculation.
`charts/polar_pouch_preview.py` composes diagnostics from canonical rendered
disks and clean pouch marks. It supports both the legacy paired-face review
and the single-sheet affine placements, clips each disk to its panel, fades
it, applies an explicit date/hour registration rotation, and keeps pouch
marks opaque. It is not part of fabrication PDF export.
`charts/polar_pouch_sheet.py` owns the single-A4 imposition records: two 148
mm panels, the one-millimetre spine, affine face placements, clipping bounds,
and the resulting 47 mm disk protrusion. It changes no face geometry.
`charts/polar_pouch_sheet_rendering.py` realizes both placed vector faces on
one A4 axes. `charts/polar_pouch_sheet_export.py` owns the corresponding
single-save actual-size export boundary.
`charts/polar_planisphere_style.py` owns the provisional configurable physical
paper palette and its pure adaptation of the existing atlas style. It changes
appearance only: white paper, a calibrated stellar magnitude curve, darker
filled outline-free Milky Way and Clouds, restrained constellation, reference,
and boundary hierarchy, and calendar typography. `style_components.CalendarStyle`
carries the resolved calendar text appearance to page realization. The palette
owns no content selection, projection, calendar geometry, renderer, or export.
`rendering/symbols.py` owns the normalized filled five-point path alongside
the established semantic markers. Generic stellar style and preparation own
its threshold and magnitude-area mapping; the polar renderer owns none of it.
`charts/coordinate_frames.py` is removed in 49C.3. Charts and furniture call `CoordinateService` directly; no chart package owns astronomical transformation. `charts/reference_furniture.py` retains the single reference-overlay path. For polar disks it configures the four canonical RA meridians and requests the service transformation before polar projection. Short 20-degree
declination marks are projected disk furniture rather than spherical
parallels. Principal-plane labels, ecliptic cardinal points, and explicitly
selected north/south pole annotations remain semantic furniture rather than
catalogue layers.
`charts/view_defaults.py` owns the immutable public geometry defaults for the
five ordinary view forms. It contains no catalogue, cache, layer, style,
furniture, renderer, or output policy.
`charts/drawing.py` owns the ordinary one-product drawing adapter. It translates
direct presentation choices onto the prepared view's immutable request,
configures semantic grids through `request_grids.py`, and delegates the sole
composition, render, furniture, and save operation to `request_generation.py`.
`charts/command_line.py` owns the shared parser additions and translation from
common command-line controls to `draw_chart_view()`, including the ordinary
labeled-equatorial-grid default and its suppression switch. It may iterate the
selected product matrix, but it owns no sphere construction, chart geometry,
projection, renderer, furniture drawing, or saving procedure.
`charts/subject_arguments.py` owns reusable command-line adaptation of an
arbitrary IAU constellation set or optional packaged-group alias into typed
friendly view arguments. It does not resolve internal constellation geometry,
frame a chart, test visibility, project, mask, or clip.
Installed commands resolve centers independently through
`charts/center_arguments.py`; constellation content and masks carry their own
explicit IAU selections.
`charts/_masking.py` selects official mask boundaries before projection and
composes constellation and above-horizon openings into one renderer mask.
Independent opening groups are retained as compound-path winding metadata so
the renderer paints their excluded union once instead of stacking alpha. For
observer-visible full-sky charts it rejects wholly hidden regions while
preserving complete partly visible, possibly disjoint polygons for clipping
by the chart-owned final boundary; regional masks retain their viewport-only
behavior.
`charts/horizon_mask.py` prepares the above-horizon opening for ordinary
stereographic fields and the transformed, seam-aware Galactic Mollweide map;
it does not paint or own appearance.

## Responsibility mapping

| Responsibility | Principal implementation |
|---|---|
| Observer and time | `observer.py` |
| Physical catalogues | `objects/` |
| Sky layers and execution core | `sky/` |
| Spherical and projected geometry | `geometry/` |
| Projection | `projections/` |
| Chart framing and composition | `charts/` |
| Rendering and preparation | `rendering/` |
| Package resources | `resources/` |
| Astronomical data | `data/` |

## Charts package

The v0.7 chart workflow is concentrated in `wenu.charts`:

```text
charts/
├── regional.py, full_sky.py, all_sky.py,
│   circumpolar.py, binocular.py  chart geometry and export entry points
├── context.py                    output-neutral chart geometry context
├── composition.py                style/mode/detail/legend resolution
├── chart_arguments.py            shared canonical chart request arguments
├── command_line.py               ordinary shared command-line adapter
├── product_options.py            style/mode product selection and naming
├── style_overrides.py            immutable post-mode visual overrides
├── export_workflow.py            render, decorate, and save once
├── detail.py                     detail policies, including polar content
├── detail_application.py         render-local layer options
├── styles.py, style_components.py,
│   presets.py                    composed visual styles
├── atlas_modes.py,
│   cartoon_modes.py              medium-specific style adaptation
├── legend_plan.py and
│   legend_* modules              legend policy, metadata, symbols, layout
├── boundaries.py                 chart and grid-label boundary helpers
└── constellation_label_placement.py
                                   visible-region label placement
```

The deprecated `cartoon_composition.py` contains compatibility wrappers only.
It is lazily imported when an old public entry point is requested and is not
part of canonical composition.

## Dependency direction

```text
objects ─┐
         ├─> sky ─> geometry ─> projections
observer ┘
                    charts ─> rendering
                       └────> sky execution core
```

More precisely, chart production flows from registered layers through
spherical geometry, projection-domain guarding, projection, projected
geometry, preparation, rendering, legends, and one final export. Styles,
modes, detail policies, and legends configure that flow; they do not create
parallel implementations.

## Architectural boundaries

- `objects` owns catalogue interpretation, not plotting.
- `sky` owns drawable layer contracts and `CelestialSphere.draw_chart()`.
- `geometry` and `projections` are independent of Matplotlib.
- `charts` owns projection/framing choices and resolves chart concerns.
- `rendering` owns graphical backend behavior.
- examples request charts and may supply documented label overrides, but do
  not implement clipping, catalogue joins, legends, or repeated saving.
- all six canonical examples use the ordinary three-stage interface; each
  source and installed resource is byte-identical, shorter than 70 lines, and
  contains no private catalogue construction, request graph, renderer, legend
  assembly, or export loop.

See `archive/architecture_history/target_architecture_v0.7.md` for the
implemented architecture,
`archive/migration_history/wenu_migration_0.6_to_0.7.md` for the completed
roadmap, `archive/architecture_history/current_architecture_v0.6.md` for the
historical baseline, and
`implementation_reference.md` for current public usage.

The structured user guide is rooted at `docs/user_guide/index.md`; its
`configuration.md` page owns the editable-template, value-vocabulary, and
single-file profile guidance. Its `assets/` directory contains only the
provenance-controlled README image.

The user-facing `examples/` directory contains only the six canonical chart
families as short declarations over the shared sphere, view, drawing, and CLI
facades. Historical component demonstrations that still provide regression
coverage live under `tests/fixtures/example_regressions/`; they are test-local
fixtures, not supported user examples.

`docs/developer/archive/audits/public_interface_audit_v0.9.5.md` classifies every executable
public example, user recipe, diagnostic, benchmark, catalogue-maintenance
utility, and repository tool after architecture 0.9.5. It also records the
as-is gap between internal `CoordinateSpec` capability and public system,
frame, equinox, and epoch selection.

`examples/circumpolar.py` and its byte-identical packaged resource expose the
family's existing limiting-declination framing value as an ordinary argument.
They still only declare a view and delegate horizon controls to the shared
request and drawing facades. The shared `--declination-step` control travels
through `DetailOverrides` to request-time equatorial-grid configuration; it
does not create family-local grid geometry or alter right-ascension spacing.

`tests/test_canonical_all_sky_example.py` owns the all-sky declaration's
explicit Galactic Mollweide geometry, default detail, optional disjoint mask,
shared drawing delegation, and observer cleanup. Shared example and installer
tests own CLI parity, short-source boundaries, and byte identity with the
packaged resource; `tests/test_user_guide.py` owns its guide contract.

## Test-suite responsibility and tiers

`docs/developer/archive/audits/configuration_default_audit.md` is the Milestone 46D authority
map for public defaults. It separates public values from derived values,
invariants, and implementation details; inventories every responsibility and
appearance source; and records duplications that must be removed as TOML
becomes authoritative. It is an audit input, not a runtime registry.

`docs/developer/configuration_schema_v2.md` is the current structural
contract for the future authoritative TOML document. It orders every public
namespace, defines scalar and closed-vocabulary validation, requires
independent color/line-width/line-style keys, and specifies complete-path
diagnostics and the non-executable data boundary. It is not a parser, packaged
default file, overlay loader, command implementation, or runtime registry.

`src/wenu/configuration/defaults.toml` is the complete commented schema-v2
public-default document. Its package contains data only;
it has no renderer, catalogue, geometry, or execution dependency. Tests load
it through `importlib.resources` and TOML parsing. Runtime contracts do not
consume it until later 46D.3 validation and translation slices are complete.

`src/wenu/configuration/validation.py` is the Milestone 46D.3B parser and
strict complete-document validation boundary. It reads the package resource,
uses its values as the sole default authority, and supplies only structural
and semantic validation behavior in Python. It has no catalogue, observer,
geometry, chart, renderer, furniture-drawing, or export dependency and does
not yet translate values into those runtime owners.

`src/wenu/configuration/style_mode_translation.py` is the Milestone 46D.3C
translation seam for existing immutable style, mode, and palette dataclasses.
It contains translations but no public default literals, composition registry,
renderer dispatch, or mutation. Milestone 46D.4A adds one process-local cached
packaged translation; named composition consumes that immutable authority
through the existing style and mode adapters.

`src/wenu/configuration/translation.py` is the Milestone 46D.5A aggregate
translation boundary. Together with the partial-overlay functions in
`validation.py`, it loads an optional user TOML file over a fresh packaged
mapping, validates the complete result, and returns the three existing frozen
typed contract groups without installing mutable process state. Runtime and
shared-command adaptation remain outside this slice.

Milestone 46D.5B makes that aggregate explicit request-adjacent state on an
ordinary `ChartView`. `view.py`, `composition.py`, `drawing.py`, and
`export_workflow.py` carry it through their existing geometry, appearance,
detail, furniture, product, and export owners. `command_line.py` owns the
shared `--config` adapter and resolves omitted product arguments only after
the effective document is available. Canonical examples validate it before
maximal-sphere construction; no active-configuration singleton exists.

Milestone 46D.6 adds `src/wenu/cli/chart.py` as the installed `wenu_chart`
adapter. It owns the six subcommand parsers, effective observer and center
argument selection, observer lifetime, output-path reporting, and verbatim
`defaults.toml` display. Chart commands delegate to
`generate_celestial_sphere()`, `get_chart_view()`, and
`draw_chart_view_from_arguments()` and do not import `example_scripts` or own
catalogue, projection, rendering, furniture, or export behavior.

Milestone 46D.7 keeps editable-template export in that same CLI adapter.
`packaged_defaults_text()` reads the installed resource verbatim and
`write_defaults_template()` writes its exact UTF-8 bytes. It does not
serialize typed translations or acquire schema, validation, profile
inheritance, catalogue, or chart responsibility.

`tests/test_wenu_chart_example_parity.py` owns Milestone 46D.8A's
front-end-neutral view contract. It executes every canonical example adapter
and an equivalent `wenu_chart` invocation against the same effective
configuration, normalizes only documented omitted geometry, and compares the
observer, center, projection, coordinate frame, frame, orientation, pole,
declination-limit, and mask requests before catalogue loading or rendering.

`tests/test_wenu_chart_drawing_parity.py` owns Milestone 46D.8B's downstream
installed-command contract. It lets `draw_chart_view_from_arguments()` resolve
the complete public drawing vocabulary and captures the immutable arguments
at the existing `draw_chart_view()` boundary. It also proves deterministic
four-product naming without constructing catalogues or a renderer.

`tests/test_wenu_chart_configuration_isolation.py` owns Milestone 46D.8C's
installed-command overlay boundary. It proves sequential partial overlays and
packaged defaults remain independent on one reused sphere identity and that
explicit command observer, center, geometry, product, title, language, and
destination values retain final precedence. `tests/test_wenu_chart_cli.py`
owns the complementary early-failure order before observer, sphere, view, or
drawing work.

`tools/render_46d8_visual_matrix.py` and
`tests/test_visual_acceptance_matrix.py` own Milestone 46D.8D's reproducible
visual handoff. The tool drives the actual command module in fresh processes
and writes 18 untracked PNGs plus a checksum manifest. The test verifies the
matrix shape and role coverage without rendering; human acceptance is recorded
in `docs/developer/archive/acceptance_history/visual_acceptance_46d8.md` only after Mac review.

`tools/render_48e2_polar_preview.py` owns the v0.9 physical-style checkpoint.
It drives the canonical generated sphere, paired charts, atlas-print
composition, and calendar geometry to write two untracked PNGs and a checksum
manifest. It supports explicit DPI and routes external Astropy anchor input
through `CoordinateService`. It is a diagnostic only; product export and physical A4 assembly
remain later milestones. Human review is recorded in
`docs/developer/archive/acceptance_history/visual_acceptance_48e2.md`.
Milestone 48E.3 reuses that genuine two-face diagnostic; its separate review
criteria and disposition live in `docs/developer/archive/acceptance_history/visual_acceptance_48e3.md`.
`tests/test_polar_classroom_disk_freeze.py` records commit `09a2afd` as the
accepted classroom astronomical checkpoint. It freezes the paired projection,
limits, physical scale, handedness, and face-neutral content policy, and proves
that resolving physical calendar furniture cannot mutate celestial geometry.
It deliberately compares renderer-neutral geometry rather than raster pixels,
so later page furniture can be reviewed without silently moving the sky.
`tools/render_48e4_polar_pages.py` is the actual-size Milestone 48E.4 handoff.
It resolves the accepted paired disk, calendar, and A4 page information, calls
the paired canonical exporter, and writes exactly two PDF pages plus a checksum
manifest outside the repository. Physical review is recorded in
`docs/developer/archive/acceptance_history/visual_acceptance_48e4.md`.
`tools/render_48g2_polar_pouch.py` is the actual-size folded-pouch review
entry point. It resolves the ordinary paired disk, page, canonical horizon,
and pouch furniture owners. It writes one clean, one-sided A4 fabrication PDF
with south above and inverted north below, plus one faded canonical-disk PNG
diagnostic and one checksum manifest.

`tools/render_zodiac_constellations.py` is a review-only batch entry point. It
uses `generate_celestial_sphere()`, `get_chart_view()`, the shared command-line
adapter, configured furniture, and ordinary request export to emit selected
traditional zodiac constellations separately. Its `--constellations IAU,...`
control reuses the package's public constellation-list parser; omission emits
all twelve, while an explicit list may additionally select Ophiuchus without
renumbering the established zodiac outputs. The Ophiuchus review subject uses
the ordinary `Oph,Ser` constellation-set resolver so both Serpens figure
components accompany Ophiuchus without tool-owned component logic. The north
ecliptic pole defines chart up. Its render-local `SerCau` label displacement
uses the shared discrete constellation-label placement resolver and does not
alter the catalogue anchor or any other chart. Fixed content is Hipparcos
stars through magnitude 5.5, one figure
and Spanish label, the ecliptic, celestial equator, and equatorial grid. Titles
carry the Spanish constellation name and J2000 center RA/Dec to minutes.
`--constellation-mask` receives the packaged cartoon warm-white mask unchanged;
the tool contains no mask color, opacity, polygon, or renderer policy. Its
cartoon/presentation review overrides strengthen only the ecliptic and enlarge
coordinate labels through `ChartStyleOverrides`. The optional
`--constellation-boundaries` switch remains owned by the shared chart-detail
adapter, and `--dpi` immutably overrides the configured presentation-mode
resolution before the ordinary request is prepared and exported. Its
furniture requests the four canonical ecliptic keypoints through the shared
reference overlay; normal
regional clipping shows only keypoints actually inside each constellation
field. Charts containing one receive its localized lower-left name key from
the same projected reference result. The ordinary stellar legend is an
inclusive vertical 0--5 scale at lower right while retaining the rendered
star-size law. The shared rectangular grid-label anchor filters
projected samples to the axes viewport and reserves prior label positions
before placing RA or declination text, so visible parallels cannot lose
labels to off-page samples or stack at a shared chart edge.
The tool also inherits the shared `--sky-color` option through
`ChartStyleOverrides`; it contains no renderer-specific background-color
path.
The zodiac review selects the inclusive 0--5 canonical stellar scale on an
opaque sky-colored frame. It does not alter constellation framing for
keypoints. Reference furniture consumes the same resolved -90-degree clipping
limit as every other layer in a rectangular composition, leaving the final
viewport as the only visibility test.

`charts/reference_keypoint_legend.py` realizes the optional compact key for
the canonical ecliptic points. It consumes the reference overlay's completed
projected point result and never recomputes celestial coordinates or clipping.

`data/translations.json` is the single packaged dictionary for generated
visual labels. `translations.py` loads it immutably, validates the requested
language, and preserves unknown text. Shared command-line furniture resolves
reference-plane labels through this boundary; examples do not own translations.

Milestone 46D.8E keeps those owners but narrows diagnostic claims: all-sky and
regional constellation masks are isolated from horizon openings, binocular
acceptance covers its actual field and furniture, and circumpolar retains the
crossing horizon case. The acceptance document owns the normalized remediation
register; production chart modules remain untouched.

Milestone 46D.8F assigns common remediation to existing owners:
`configuration/defaults.toml` and `charts/presets.py` own semantic appearance,
`charts/request_grids.py` owns family sampling, `charts/styles.py` owns numeric
formatting and rectangular fallback placement, and `charts/boundaries.py` owns
circular and elliptical label anchors. Examples contain none of these values.

Milestone 46D.8G keeps density in those same detail owners. Named atlas
composition selects the packaged policy for the chart family when no explicit
policy is supplied. The packaged cartoon policy owns its bright deep-sky
subset and thresholds. Canonical examples delegate both decisions and contain
no family magnitude, size, or layer-density literals.

Milestone 46D.8H keeps outside-mask appearance in the existing packaged style
owners: `configuration/defaults.toml` is authoritative and
`charts/presets.py` retains the compatibility default. Translation and the
shared mask renderer continue to consume `MaskStyle` without family, example,
or geometry-specific overrides.

Milestone 46D.8H.1 corrects `charts/cartoon_modes.py` at the mode-realization
boundary: it preserves the style-owned mask instead of replacing its color
with the mode sky. Configuration translation and the shared mask renderer
remain the owners on either side; atlas mode resolution is unchanged.

Milestone 46D.8H.2 returns final appearance ownership to
`configuration/defaults.toml`, with `charts/presets.py` retaining its exact
compatibility value and the translation contract proving parity. Examples and
mode adapters contain no cartoon mask color or opacity literals.

Milestone 46D.8I keeps binocular remediation distributed by responsibility:
`charts/command_line.py` and `cli/chart.py` own the family grid default;
`charts/binocular.py` retains the resolved target center as geometry;
`charts/reference_furniture.py` constructs its unregistered marker overlay;
`charts/request_furniture.py` owns the center-and-diameter title; and
`configuration/defaults.toml` owns the binocular-only stellar sizing exponent.
The canonical example declares those public policies without drawing them.

Milestone 46D.8J leaves runtime ownership unchanged.
`docs/developer/archive/acceptance_history/visual_acceptance_46d8.md` owns the truthful closure record:
accepted source, reviewer, date, and explicit full-matrix deferral.
`tests/test_visual_acceptance_matrix.py` prevents that disposition from being
silently rewritten as a completed rerun.

`src/wenu/configuration/geometry_detail_translation.py` is the Milestone
46D.3D translation seam for existing immutable family-view, detail-policy,
content-selection, and stellar-sizing contracts. It preserves the current
geometry/detail owners and rejects values the current contracts cannot
represent. Milestone 46D.4B adds one process-local cached packaged translation;
the family-default gateway and neutral/cartoon composition consume it without
changing chart construction, catalogue selection, or rendering.

`src/wenu/configuration/furniture_product_export_translation.py` is the
Milestone 46D.3E translation seam for immutable furniture, family legend,
magnitude-legend, product, and export contracts. Milestone 46D.4C adds one
process-local cached packaged translation consumed by the existing ordinary
drawing, legend-plan, magnitude-legend, footer, product-naming, parser, and
canonical export owners. The module itself still contains no furniture
drawing, path creation, rendering, or saving.

Milestone 46D.4D completes packaged runtime activation at the ordinary drawing
and immutable request boundaries: omitted style, mode, language, and title
come from the packaged product contract. Literal defaults retained by direct
typed constructors are compatibility signatures only and are not consumed by
the canonical named runtime gateways.

Permanent test modules are named for current responsibilities rather than the
milestones that introduced them. Scientific geometry and catalogue contracts
remain ordinary unit tests. Cross-component canonical chart construction is
marked `integration`, while rendered appearance and image-structure contracts
are marked `visual`. The registered `slow` tier is reserved for future tests
that are intrinsically slow, not for inefficient tests that should be fixed.

The supported validation loops are:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -m "not integration and not visual and not slow"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -m integration
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -m visual
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

The full suite remains the release authority. Atlas print remains the visual
reference baseline.

`tools/benchmark_reusable_sphere.py` is a diagnostic closure harness rather
than a runtime dependency or test threshold. It loads one observer-independent
canonical sphere, prepares and exports every chart family for three
observer/instant identities, and writes JSON phase timings and cache-entry
counts beside deterministic atlas-print products. Profiler categories are
reported independently and may overlap; they diagnose ownership costs rather
than claiming an additive wall-time decomposition. Its 37-step progress output
covers one catalogue load, 18 view preparations, and 18 atlas-print exports.
The regional-single and regional-group requests explicitly exercise outside
masks; the other four families remain unmasked.

`tools/benchmark_cold_frames.py` is the accepted 49J.4 cold independent-frame
diagnostic. It sends three resolved circumpolar requests through the unchanged
complete static generator, attributes every profiled interval to one exclusive
stage or residual, and records raw/summary timings with environment, resource,
request, semantic/projection, and output identities. It introduces no cache,
alternate chart path, or pass/fail threshold; caller-selected products and JSON
belong outside the repository.

`tools/render_46d8_visual_matrix.py` is the final command-surface visual
acceptance harness. It is intentionally separate from the reusable-sphere
benchmark: each entry launches `python -m wenu.cli.chart` in a fresh process,
and its output directory remains ignored rather than becoming a golden-image
test fixture.

The committed suite has no session-scoped fixture or `tests/conftest.py`.
`test_reusable_canonical_sphere.py` uses module-scoped fixtures for its
intentional reuse and order contracts. The accepted evidence is archived in
`archive/milestone_history/49j_performance/test_architecture_and_accepted_practice_audit_49j1.md`.

The accepted
`archive/milestone_history/49j_performance/test_practice_decisions_49j2.md`
policy permits a narrowly
keyed session-scoped registry only after immutability, teardown, order
independence, isolated-execution, and retained cold-builder evidence exists.
It also proposes a new-test admission rule: composing already-tested
functionality justifies tests for the new seam and fault model, not automatic
duplication of every lower-level contract. Neither policy is implemented yet.


## SVG product modules (Milestones 49F.2C–49F.3)

- `src/wenu/output_policy.py` owns the public `png`, `pdf`, and `svg`
  vocabulary independently of Matplotlib.
- `src/wenu/chart_document.py` owns renderer-neutral editing classifications
  used by projected semantic content.
- `src/wenu/svg_document.py` annotates already-saved SVG artist groups with
  Wenu semantic, paint-order, and editing metadata. It does not own
  astronomical selection, projection, rendering, or a second save path.
- `src/wenu/charts/product_options.py` resolves explicit output selection and
  deterministic filenames.
- `src/wenu/rendering/matplotlib.py` carries Wenu semantic identity from
  rendering to the final SVG annotation boundary.

SVG remains a downstream 2D product. It is not Wenu's scientific scene, an
internal `.wenu` representation, or the interchange format for Wenu3D. Future
Sun, Moon, and planet layers must supply their semantic identities upstream
and reach SVG through this same renderer/export boundary. No separate SVG
astronomy generator or post-export coordinate overlay is permitted.

## Temporal sequence modules (Milestone 49G.1)

- `src/wenu/temporal.py` owns immutable physical timeline and separate
  playback vocabulary. It has no chart, observer, projection, renderer,
  encoder, or FFmpeg dependency.
- `tools/render_circumpolar_movie.py` is the reference external adapter. It
  consumes the temporal contracts, invokes complete ordinary `wenu_chart`
  renders, and only then assembles their PNG outputs with FFmpeg.
- `tests/test_temporal.py` verifies physical/civil time separation, uniform
  and irregular sampling, playback independence, validation, and
  deterministic filenames.
- `tests/test_render_circumpolar_movie.py` verifies that the reference
  adapter resolves the established twelve-hour/180-frame/15-second contract.

A package sequence request, frame manifest, CLI, and scientifically keyed
reuse remain future 49G increments.

### Observer-time sequence orchestration (Milestone 49G.2)

- `src/wenu/charts/sequence.py` owns immutable observer-time frame plans,
  canonical static-generation orchestration, and ordered result metadata.
- It depends on `ChartRequest`, `TemporalTimeline`, and
  `generate_chart_request()`; it does not construct sky, projection,
  renderer, export, or encoder alternatives.
- `tests/test_chart_sequence.py` verifies deterministic frame requests,
  observer-time replacement, civil display metadata, canonical executor
  ownership, output validation, and the bounded one-product contract.

Celestial realization epochs for proper motion/precession and provider
evaluation instants for moving objects are separate future owners. They must
not enter through the observer-time sequence API.



### Sequence manifest and resume (Milestone 49G.3)

- `src/wenu/charts/sequence_manifest.py` owns deterministic JSON plan
  identity, schema validation, verified completion records, and atomic
  manifest persistence.
- `src/wenu/charts/sequence.py` remains the canonical repeated-static
  orchestrator and now selects explicit restart or manifest-verified resume.
- `tests/test_sequence_manifest.py` verifies deterministic serialization,
  portability, tamper rejection, compatibility, and completion records.
- `tests/test_chart_sequence.py` verifies restart/resume orchestration,
  selective rerendering, incompatible-plan rejection, and real-frame reuse.

Manifest logic does not construct or cache sky state and does not render,
project, clip, style, encode, or infer astronomical equivalence.


## Temporal sequence CLI modules (Milestone 49G.4)

`charts/sequence_arguments.py` owns the public temporal CLI vocabulary and
translates explicit switches over immutable TOML defaults into
`TemporalTimeline`, optional `PlaybackSpec`, and `SequenceRestartPolicy`.
It performs no chart construction, rendering, caching, or media encoding.

`configuration/sequence_translation.py` owns immutable `SequenceDefaults`.
The aggregate configuration contract transports it with existing style,
mode, detail, furniture, product, and export defaults.

`charts/command_line.py` now resolves one shared static/sequence product plan.
`charts/drawing.py::chart_view_request()` converts that plan into the same
immutable `ChartRequest` used by ordinary drawing. The installed
`cli/chart.py` chooses static drawing or the existing sequence orchestrator
after this common translation; it does not own another scientific or export
pipeline.

`charts/fixed_sky_sequence.py` owns the 49H.1 renderer-neutral planning
contract for one fixed celestial/camera anchor and per-frame observer-local
instants. It produces separate immutable celestial requests and local observer
values without rendering, caching, manifest mutation, or a second execution
pipeline. Catalogue reference epochs and proper-motion policy remain provider
state rather than UTC timeline values.

`charts/fixed_sky_baseline.py` owns the 49H.2 independent circumpolar
complete-render baseline adapter and explicit RGBA comparison measurements. It
delegates baseline generation to the ordinary observer-time static pipeline,
keeps candidate and baseline directories separate, rejects unproved chart
families, and contains no optimized renderer or cache.

`tools/render_49h2_complete_render_baseline.py` is the reproducible
characterization adapter for that baseline. It selects both celestial and observer-local
content, invokes only the public oracle boundary, and records hashes,
dimensions, timeline instants, and manifest identity in JSON.



### Fixed-sky reference rendering (Milestone 49H.3)

- `charts/fixed_sky_orientation.py` owns the renderer-neutral astronomical
  anchor rotation and its explicit provenance.
- `charts/fixed_sky_sequence.py` resolves planned dual-time frames into
  ordinary local-time chart requests and provides the deliberately uncached
  canonical reference executor.
- `tests/test_fixed_sky_orientation.py` proves fixed celestial projection and
  moving local-horizon projection without asserting a guessed sidereal angle.
- `tools/render_49h3_fixed_sky_reference.py` produces the visually accepted
  fixed-sky/rotating-horizon audit and records per-frame orientation metadata,
  dimensions, and hashes.

# Public celestial reference policy

- `src/wenu/charts/reference_policy.py`: validates and resolves the coupled
  FK5/ecliptic reference equinox and translates it to coordinate identities.
- `src/wenu/charts/request_grids.py`: applies the request policy to ordinary
  equatorial and ecliptic grids.
- `src/wenu/charts/reference_furniture.py`: applies the same resolved equinox
  to the celestial equator, ecliptic, and seasonal keypoints.

`docs/developer/archive/milestone_history/49e_ephemeris/skyfield_ephemeris_adapter_49e3.md` owns the 49E.3 scientific
contract. `tools/validate_49e3_skyfield_adapter.py` is the explicit
no-download installed-kernel Venus/SSB acceptance check.

`docs/developer/archive/milestone_history/49e_ephemeris/solar_system_direction_realizer_49e4.md` owns the proposed
49E.4 observer-relative direction boundary. It is documentation-only: no
runtime realizer or moving-body layer exists yet. The proposed astrometric
result retains distance, light time, reception/emission instants, observer
state, and resource provenance before any product-frame transformation.

`src/wenu/solar_system_directions.py` owns the 49E.5 typed observer state,
astrometric request/result, bounded light-time iteration, and deterministic
direction errors. `src/wenu/skyfield_ephemeris.py` additionally owns the
same-kernel Skyfield observer-state adapter. The detailed contract is
`docs/developer/archive/milestone_history/49e_ephemeris/astrometric_direction_runtime_49e5.md`; the controlled
real-resource check is `tools/validate_49e5_astrometric_direction.py`.

`src/wenu/solar_system_directions.py` also owns the 49E.6 apparent-policy and
result contracts, while
`src/wenu/skyfield_ephemeris.py::SkyfieldApparentDirectionRealizer` consumes
the retained 49E.5 vector without a second `observe()` call. The detailed
contract is `docs/developer/archive/milestone_history/49e_ephemeris/apparent_direction_runtime_49e6.md`; the controlled
installed-resource comparison is
`tools/validate_49e6_apparent_direction.py`. No moving-body layer exists yet.

`docs/developer/archive/milestone_history/49i_solar_system/venus_vertical_slice_audit_49i1.md` owns the proposed first
drawable Venus boundary. It identifies the missing ordinary-request
`LayerRealizationContext` handoff and reserves upstream semantic path
`sky/solar_system/planets/venus`. It adds no runtime layer, CLI option, or
output change.

`src/wenu/charts/request_realization.py` owns the 49I.1A translation from an
ordinary resolved request and matching observer to one output-neutral
`LayerRealizationContext`. `charts/request_generation.py`,
`charts/export_workflow.py`, and the existing chart facades forward that value
to `CelestialSphere.draw_chart()`. `VenusLayer` is now the first installed
moving-body override of `realize()`; no Moon or generic shared-body layer is
installed. The detailed context contract is
`docs/developer/archive/milestone_history/49i_solar_system/ordinary_realization_context_49i1a.md`.
Fernando accepted the output-neutral implementation on 2026-08-30 after the
complete 1,890-test Mac suite passed.

`src/wenu/sky/venus.py` owns the bounded 49I.1B moving-body layer. It composes
the existing ephemeris and direction services and returns product-frame
spherical geometry without projecting or rendering. The layer's stable
semantic path is `sky/solar_system/planets/venus`.

`docs/developer/archive/milestone_history/49i_solar_system/moon_shared_body_pipeline_audit_49i2.md` owns the proposed
Moon validation and shared solar-system point-layer boundary. It records what
is invariant across bodies, what varies by typed state provider, and what
belongs to later physical-appearance geometry. It adds no runtime module or
output.

`tests/test_moon_direction_validation.py` is the deterministic 49I.2A proof
that Moon/NAIF 301 traverses the generic astrometric and apparent contracts.
`tools/validate_49i2a_moon_direction.py` is the explicit no-download
installed-kernel comparison against direct Skyfield, geocentric direction,
and zero-height observer. No `sky/moon.py` exists in 49I.2A.


`src/wenu/sky/solar_system_points.py` owns the 49I.2B frozen symbolic-body
descriptor and shared renderer-neutral direction-to-product-frame
orchestration. `src/wenu/sky/venus.py` is the thin Venus specialization.
`tests/test_solar_system_point_layer.py` proves generic reuse with a test-only
Moon descriptor; no production Moon layer exists in 49I.2B.


`src/wenu/sky/moon.py` owns only the 49I.2C frozen Moon descriptor and thin
shared-point specialization. `src/wenu/charts/chart_arguments.py` adapts
class-aware `--moon` and `--planet venus` controls into the request-owned
`solar_system_objects` selection. `sky/maximal_sphere.py` registers the
default-off layer once; existing detail, style, semantic, projection, renderer,
and exporter owners complete the canonical path.

`docs/developer/archive/milestone_history/49i_solar_system/solar_system_track_audit_49i2d.md` owns the accepted
documentation-only Solar-System trajectory boundary. It reuses
`geometry/spherical.py::SphericalCurves`,
`coordinate_service.py::CoordinateService`, and the existing projection,
preparation, renderer, and exporter owners. It adds no runtime module. A later
implementation may add one shared track realizer under `sky/`; it must not add
body-specific projection or rendering code.

`src/wenu/sky/solar_system_tracks.py` owns the 49I.2D.1 frozen scientific
sampling request/result and scalar track realizer. It shares
`SolarSystemPointDescriptor`, borrows one ephemeris source, reevaluates the
accepted direction chain at every sample, returns one fixed-product-frame
`SphericalCurves`, and owns no installed layer, chart request, projection,
annotation, style, renderer, or output. `tests/test_solar_system_tracks.py`
owns deterministic contract coverage;
`tools/validate_49i2d1_venus_track.py` owns the installed-DE440 comparison.

## Milestone 49I.2D.2 ownership

- `src/wenu/sky/solar_system_track_layer.py` owns only the context-required
  scientific layer and track realizer handoff.
- `src/wenu/charts/solar_system_track_annotations.py` owns projected path
  assembly, perpendicular ticks, the start anchor, and chronological two-pass
  date placement.
- `src/wenu/charts/request_tracks.py` installs the request-owned layer.
- `tests/test_solar_system_track_layer.py` covers projected preparation and
  label layout; `tests/test_solar_system_track_cli.py` and
  `tests/test_chart_request_tracks.py` cover public request plumbing.
- `tools/diagnose_49i2d2_venus_track_labels.py` reports retained tick and
  renderer-label evidence without owning production behavior.


## Milestone 49I.3A audit ownership

- `docs/developer/archive/milestone_history/49i_solar_system/physical_apparent_disk_audit_49i3a.md` owns the accepted
  symbolic-versus-resolved appearance contract, scientific/display quantity
  separation, canonical geometry route, Venus/Moon sequence, and non-goals.
- No production source file owns physical angular diameter, phase,
  bright-limb orientation, body orientation, photometry, or disk
  magnification yet.
- `tests/test_current_documentation.py` protects the accepted boundary.


## Milestone 49I.3B ownership

- `src/wenu/solar_system_appearance.py` owns the frozen physical state,
  angular-diameter and spherical-phase realization, identity validation, and
  apparent-ICRS bright-limb convention.
- `tests/test_solar_system_appearance.py` owns deterministic state,
  convention, validation, and failure coverage.
- `tools/validate_49i3b_venus_appearance.py` owns installed-DE440 comparison
  and celestial-versus-local orientation diagnostics.
- `docs/developer/archive/milestone_history/49i_solar_system/venus_physical_appearance_49i3b.md` owns the accepted
  scientific and architectural contract.
- No sky layer, chart request, style, renderer, or exporter consumes the new
  state in 49I.3B.


## Milestone 49I.3C audit ownership

- `docs/developer/archive/milestone_history/49i_solar_system/resolved_venus_disk_audit_49i3c.md` owns the accepted
  geometry, post-projection magnification, product, multi-epoch, semantic,
  validation, and implementation split for resolved Venus disks.
- Runtime ownership is not installed: scientific construction will produce
  one physically sampled illuminated spherical polygon and separate limb and
  terminator spherical curves; chart preparation will magnify projected
  offsets; chart policy will own opt-in representation and Venus-specific
  magnification; style will own appearance.
- Multi-epoch disks will reuse one fixed chart frame with independent physical
  appearance states. No production source file changes in this audit.


## Milestone 49I.3C.1 ownership

- `src/wenu/solar_system_disk_geometry.py` owns the frozen physical geometry
  bundle, 720-sample default, tangent-basis phase construction, radial
  angular-offset mapping, validation, and metadata.
- `tests/test_solar_system_appearance.py` owns deterministic limb,
  terminator, illuminated-area, orientation, provenance, and failure coverage.
- `tools/validate_49i3c1_venus_disk_geometry.py` owns installed-DE440
  physical-radius, closure, area, and orientation evidence.
- `docs/developer/archive/milestone_history/49i_solar_system/venus_disk_spherical_geometry_49i3c1.md` owns the accepted
  scientific and architectural contract.
- No sky layer, chart request, magnification, style, renderer, or exporter
  consumes the geometry in 49I.3C.1.


## Milestone 49I.3C.2 ownership

- `src/wenu/sky/venus_disk.py` owns the shared Venus appearance realization
  and the illuminated-face, limb, and terminator sky layers.
- `src/wenu/charts/request_disks.py` owns opt-in, object-specific resolved
  display selection and dynamic request-layer installation.
- `src/wenu/charts/solar_system_disk_preparation.py` owns exact
  post-projection scaling around the separately projected physical centre.
- `src/wenu/sky/celestial_sphere.py` exposes the canonical projector to
  projector-aware chart preparation without changing ordinary callables.
- `tests/test_venus_disk_display.py` owns CLI, scale, semantics, replacement,
  and centre-preserving magnification regressions.
- `docs/developer/archive/milestone_history/49i_solar_system/drawable_venus_disk_49i3c2.md` owns the accepted runtime,
  visual, and angular-scale calibration evidence.


## Milestone 49I.3C.3 audit ownership

- `docs/developer/archive/milestone_history/49i_solar_system/planet_disk_sequence_audit_49i3c3.md` owns the accepted
  distinction between observed and frozen-Earth ecliptic resolved disk
  sequences, common sequence evidence, permitted content, Sun semantics,
  proposed command vocabulary, physical-distance preservation, validation
  gates, and bounded runtime slices.
- No production source file owns this candidate yet; 49I.3C.3 changes no
  runtime type, chart, geometry, renderer, or output.


## Milestone 49I.3C.3.1A ownership

- `src/wenu/sky/solar_system_disk_sequences.py` owns the immutable observed
  sequence request/result and independent per-epoch observer, direction,
  appearance, disk-geometry, and distance realization.
- `tests/test_solar_system_disk_sequences.py` owns deterministic count,
  identity, distance, and orchestration evidence.
- `tools/validate_49i3c3_1a_observed_venus_sequence.py` owns the installed
  four-epoch direct-Skyfield comparison.
- `docs/developer/archive/milestone_history/49i_solar_system/observed_venus_disk_sequence_49i3c31a.md` owns acceptance
  evidence and the boundary to drawable 49I.3C.3.1B.


## Milestone 49I.3C.3.1B ownership

- `src/wenu/sky/venus_disk_sequence.py` owns independent fixed-frame
  transformation, aggregation, shared realization, and sequence layers.
- `src/wenu/charts/request_disks.py` owns the drawable sequence request and
  dynamic layer installation.
- `src/wenu/charts/solar_system_disk_preparation.py` owns per-sample projected
  magnification around separately projected centres.
- `src/wenu/charts/chart_arguments.py`, `command_line.py`, `request.py`, and
  `drawing.py` own public request and regional/binocular translation.
- `tests/test_observed_venus_disk_sequence_display.py` owns cadence, shared
  state, semantic paths, and per-centre magnification regressions.
- `docs/developer/archive/milestone_history/49i_solar_system/drawable_observed_venus_sequence_49i3c31b.md` owns accepted
  scientific, visual, operational, and regression evidence.


## Milestone 49I.3C.3.2A ownership

- `src/wenu/sky/frozen_earth_disk_sequences.py` owns the immutable request,
  frozen-Earth geometric direction and disk records, fixed-ecliptic transform,
  same-epoch physical state, retained vectors, distances, and provenance.
- `tests/test_frozen_earth_disk_sequences.py` owns deterministic cadence,
  freeze, identity, physical-state, immutability, and boundary evidence.
- `tools/validate_49i3c3_2a_frozen_earth_venus.py` owns the installed-DE440
  direct-vector and fixed-ecliptic comparison.
- `docs/developer/archive/milestone_history/49i_solar_system/frozen_earth_venus_sequence_49i3c32a.md` owns scientific,
  architectural, numerical, and regression acceptance evidence.


## Milestone 49I.3C.3.2B ownership

- `src/wenu/sky/frozen_earth_venus_disk_sequence.py` owns the shared drawable
  disk components and fixed six-point Sun geometry.
- `src/wenu/sky/frozen_earth_reference_grids.py` owns the observer-independent
  product-frame ecliptic and transformed FK5 equatorial grid.
- `src/wenu/charts/request_disks.py`, `request_grids.py`,
  `request_realization.py`, `reference_furniture.py`, and `drawing.py` own
  request integration, restricted content, localized title, and furniture.
- `src/wenu/charts/solar_system_disk_preparation.py` owns per-centre projected
  Venus magnification.
- `tests/test_frozen_earth_venus_sequence_display.py` and
  `tests/test_frozen_earth_reference_grids.py` own drawable, semantic,
  localization, and fixed-reference regressions.
- `docs/developer/archive/milestone_history/49i_solar_system/drawable_frozen_earth_venus_sequence_49i3c32b.md` owns
  scientific, visual, operational, and regression acceptance evidence.


## Milestone 49I.3C.3.3 audit ownership

- `docs/developer/archive/milestone_history/49i_solar_system/mercury_disk_sequence_audit_49i3c33.md` owns the proposed
  Mercury body/radius authority, provider-ID distinction, two-slice boundary,
  numerical and visual validation gates, non-goals, and stop conditions.
- Existing source files remain authoritative for the as-is implementation;
  this audit assigns no Mercury runtime owner and changes no production code.


## Milestone 49I.3C.3.3A moving-body ownership

- `src/wenu/sky/solar_system_bodies.py` owns typed body metadata,
  capabilities, classifications, relationships, and immutable catalog logic.
- `src/wenu/sky/solar_system_catalog.py` owns built-in registrations.
- Existing point, track, disk, and sequence modules own generic factories;
  Venus-named factories and class names are compatibility aliases only.
- `tests/test_solar_system_body_machinery.py` proves that a synthetic minor
  body needs no body-specific drawable machinery.
- `docs/developer/archive/milestone_history/49i_solar_system/moving_body_architecture_49i3c33a.md` owns the accepted
  architectural boundary and non-goals.


## Milestone 49I.3C.3.3B Mercury catalog validation

- `src/wenu/sky/mercury.py` owns Mercury's immutable physical descriptor,
  NAIF body identity, equal-volume mean radius, and frozen-only capability.
- `tests/test_mercury_catalog_state.py` proves descriptor-only registration
  and generic frozen state without public CLI exposure.
- `tools/validate_49i3c3_3b_mercury.py` owns the installed-DE440 direct
  Skyfield comparison and refuses kernel downloads.
- `docs/developer/archive/milestone_history/49i_solar_system/mercury_catalog_validation_49i3c33b.md` records the accepted
  numerical evidence and bounded runtime ownership.


## Milestone 49I.3C.3.3C drawable frozen-Earth Mercury

- The body catalog supplies Mercury capability and localized display metadata.
- Existing generic frozen-Earth sequence layers, disk preparation, semantic
  identity, chart integration, projection, styles, renderer, and exporters own
  the complete drawable path.
- `tests/test_frozen_earth_mercury_sequence_display.py` owns capability,
  conflict, semantic, magnification, fixed-Sun, and localization contracts.
- `docs/developer/archive/milestone_history/49i_solar_system/drawable_frozen_earth_mercury_sequence_49i3c33c.md` records
  the accepted architectural, visual, operational, and regression evidence.


## Milestone 49I.3D.1 apparent major planets

- `src/wenu/sky/major_planets.py` owns descriptor-only Mars-through-Neptune
  catalog data and preserves provider-barycentre versus physical-body IDs.
- The existing catalog, maximal sphere, `SolarSystemPointLayer`, correction
  chain, semantics, style, projection, renderer, and exporters own the runtime.
- `tests/test_apparent_major_planets.py` proves shared registration, selection,
  styling, semantics, and identity; the installed-DE440 validator owns direct
  numerical comparison.
- `docs/developer/archive/milestone_history/49i_solar_system/apparent_major_planets_49i3d1.md` owns the proposed acceptance
  boundary and explicit non-goals.


## Milestone 49I.3E.1 lunar appearance ownership

- `src/wenu/sky/earth.py` owns the non-drawable Earth parent identity.
- `src/wenu/sky/moon.py` owns the immutable Moon descriptor, NAIF body ID,
  equal-volume mean radius, radius authority, relationship, localization, and
  output-neutral appearance capability.
- `src/wenu/solar_system_appearance.py` remains the generic immutable physical
  state and realization owner; no Moon-specific appearance realizer exists.
- `tests/test_moon_appearance_state.py` owns deterministic identity,
  capability, radius, relationship, immutability, and generic-state evidence.
- `tools/validate_49i3e1_lunar_appearance.py` owns installed-DE440 comparison
  and refuses downloads.
- `docs/developer/archive/milestone_history/49i_solar_system/lunar_physical_appearance_49i3e1.md` records the bounded
  implementation and numerical acceptance gate.
- No disk geometry, chart request, magnification, style, renderer, exporter,
  or visible output is added in 49I.3E.1.


## Milestone 49I.3E.2 resolved single-Moon ownership

- `src/wenu/sky/moon.py` grants the accepted generic resolved-disk capability
  and all-five-family display policy to the existing Moon descriptor.
- `src/wenu/sky/solar_system_bodies.py` owns descriptor-level resolved-disk
  family authorization without inferring behavior from classification.
- `src/wenu/charts/chart_arguments.py` owns resolved-by-default Moon CLI
  adaptation, explicit symbolic compatibility, and magnification selection.
- Existing request disks, generic disk layers, physical geometry,
  transformations, projection preparation, renderer, semantic identity, and
  exporters own the drawable pipeline.
- `src/wenu/charts/styles.py` owns Moon disk presentation values; generic
  detail application selects them by descriptor entity key.
- `tests/test_moon_disk_display.py` owns selection, validation, semantics,
  sampling, family-policy, and compatibility contracts.
- `tools/render_49i3e2_resolved_moon_review.py` owns the five-family physical,
  legibly magnified, symbolic, star-only, and vector-export review matrix;
  automated request contracts exercise factor 1000 in every family.
- `docs/developer/archive/milestone_history/49i_solar_system/drawable_resolved_moon_49i3e2.md` records the boundary and
  accepted verification. Multi-epoch Moon behavior remains 49I.3E.3.


## Milestone 49I.3E.3 observed Moon sequence ownership

- `src/wenu/sky/moon.py` and `solar_system_bodies.py` own observed-sequence
  capability and chart-family policy.
- `src/wenu/charts/chart_arguments.py` adapts Moon-specific public spelling
  into the shared observed sequence request and rejects conflicts.
- Existing generic sequence state, complete-geometry fixed-frame transport,
  projection, per-centre magnification, labels, rendering, semantics, and
  exporters own runtime behavior.
- `tests/test_moon_disk_sequence.py` owns Moon adapter, conflict, family,
  generic-layer, and concise semantic-label contracts.
- `tools/validate_49i3e3_observed_moon_sequence.py` owns the installed-DE440
  comparison; `tools/render_49i3e3_observed_moon_sequence_review.py` owns
  the five-family fixed-chart review matrix.
- `docs/developer/archive/milestone_history/49i_solar_system/observed_moon_disk_sequence_49i3e3.md` records the boundary,
  accepted science, visuals, operation, and regression closure.



## Milestone 49I.3E resolved Moon ownership closure

- No new source owner is introduced by parent closure.
- `sky/moon.py` and the Solar-System body catalog own lunar identity,
  relationship, constants, and accepted capabilities.
- Generic Solar-System appearance, disk geometry, request, transformation,
  projection, preparation, rendering, semantic identity, and export owners
  serve both the resolved single Moon and observed Moon sequence.
- Documentation records closure of 49I.3E.0 through 49I.3E.3. Frozen-Earth lunar sequences and other excluded models remain unimplemented and separately governed.


## Milestone 49J performance-program ownership

- `tools/benchmark_reusable_sphere.py` remains the shared-sphere diagnostic;
  its profiler categories are intentionally overlapping and non-additive.
- `charts/request_generation.py` remains the complete static build/export
  authority and the cold independent-frame oracle.
- `charts/fixed_sky_sequence.py` remains the deliberately uncached first
  repeated-static workload.
- `archive/milestone_history/49j_performance/performance_and_closure_audit_49j0.md`
  retains the accepted diagnostic timing vocabulary and cache constraints.
- `archive/roadmap_history/test_performance_and_future_program_49j_50.md` retains
  the completed 49J program and superseded 50A/50B planning context;
  `post_v0.9_architecture_roadmap.md` owns current ordering and future scope
  without adding a source owner or runtime behavior.
- `archive/milestone_history/49j_performance/marker_truthfulness_49j3b.md`
  records the completed marker audit. Marker
  corrections change gate membership only; they do not create a runtime owner.
- `tests/repository_sources.py` owns the test-session immutable Python-file
  inventory, lazy UTF-8 source text, lazy AST index, and cached directory
  subsets used by independent architectural assertions.
- `tests/test_repository_sources.py` proves that every applicable repository
  Python file is included; `tests/test_package_boundaries.py` and
  `tests/test_dependency_boundaries.py` retain their separate package, domain,
  legacy-import, draw-method, and retired-coordinate fault models.
- `archive/milestone_history/49j_performance/repository_source_index_49j3c.md`
  records the completed 49J.3C audit and acceptance evidence.
- `tests/test_polar_binocular_targets.py::catalogue_positions` owns the one
  module-scoped immutable catalogue summary accepted by 49J.3D; it exposes
  nested read-only family/identifier/declination mappings, not mutable tables.
- `archive/milestone_history/49j_performance/immutable_catalogue_fixture_49j3d.md`
  owns the accepted safety proof and rejection of a session-scoped canonical
  sphere/build registry.
- `archive/milestone_history/49j_performance/cold_builder_kernel_oracles_49j3e.md`
  owns the accepted preservation decision for distinct cold builders and
  independently recomputed installed-DE440 validators.
- `archive/milestone_history/49j_performance/calendar_layout_cost_49j3f.md`
  owns the accepted proof that the calendar containment test removes only
  redundant full-canvas redraws.
- `archive/milestone_history/49j_performance/observer_time_sequence_oracle_49j3g.md`
  owns the accepted decision to preserve the cold complete observer-time route.
- `archive/milestone_history/49j_performance/test_suite_optimization_closure_49j3h.md`
  owns the accepted 49J.3 fault-model, repeated-run, and future test-file-growth
  closure.
- `archive/milestone_history/49j_performance/cold_frame_performance_baseline_49j4.md`
  owns the accepted 49J.4 cold-frame diagnostic evidence;
- `charts/fixed_sky_sequence.py` owns the accepted 49J.5 explicit cold versus
  observer-independent loaded-sphere sequence policy and fresh-observer
  lifecycle;
- `charts/request_generation.py` accepts that reusable sphere plus explicit
  observer while remaining the complete static request route;
- `tools/benchmark_cold_frames.py` remains the cold diagnostic;
  `charts/request_generation.py` remains its complete-render oracle and
  `tools/benchmark_reusable_sphere.py` remains non-additive and separate;
- `tools/benchmark_fixed_sky_reuse.py` owns the accepted 49J.5B exact
  scientific, normalized-SVG, PNG, rendered-PDF, and raw performance
  comparison; archived 49J.6 evidence records closure without changing that
  ownership.

## Accepted 50A minor-body ownership

- `archive/milestone_history/50a_minor_bodies/minor_body_scientific_provider_audit_50a0.md`
  owns the accepted provider, resource-chain, provenance, validity,
  uncertainty, photometry, and comet non-gravitational decisions; it changes
  no source-tree ownership;
- `ephemeris.py` remains the geometric state contract;
- `solar_system_directions.py` remains the light-time and astrometric-direction
  owner, while `skyfield_ephemeris.py` remains the apparent-place adapter;
- `sky/solar_system_bodies.py` and `sky/solar_system_catalog.py` remain the
  descriptor and catalog owners for later independently validated registration.

## 50A.1 minor-body state-provider ownership (accepted)

- `ephemeris.py` owns the new immutable primary-plus-dependency resource chain
  while preserving the original single-resource state contract;
- `minor_body_ephemeris.py` owns the Horizons solution identity, ordered
  target-segment selection, explicit planetary-centre composition, TDB/ICRF
  boundary, result subtype retaining solution/segment identity, and
  deterministic composition failures;
- `skyfield_ephemeris.py` additionally accepts explicit numeric provider IDs
  while retaining its borrowed single-planetary-kernel ownership;
- no descriptor, catalog, layer, direction realizer, coordinate service,
  projection, renderer, exporter, CLI, or data-package owner changes.

## 50A.2 asteroid numerical-validation ownership (accepted)

- `minor_body_ephemeris.py` additionally owns the CSPICE DAF handle and exact
  selected-segment evaluation, without SPICE global-kernel or path ownership;
- `ephemeris.py` exposes primary scalar provenance from a resource chain and
  owns explicit resource-membership comparison;
- `solar_system_directions.py` admits a target chain only when it contains the
  observer resource, while `skyfield_ephemeris.py` preserves target provenance
  through the existing apparent-place operation;
- `tools/acquire_50a2_asteroid_resources.py` is the explicit network boundary;
  `tools/validate_50a2_asteroids.py` is the offline installed-resource oracle;
- `tests/fixtures/horizons_asteroid_validation_50a2.json` owns frozen direct-
  Horizons reference values, not generated Wenu values;
- no descriptor, catalog, body, layer, projection, renderer, exporter, CLI,
  example, user-documentation, or packaged-data owner changes.

## 50A.3A first-drawable-asteroid audit ownership (accepted)

- `archive/milestone_history/50a_minor_bodies/first_drawable_asteroid_audit_50a3a.md`
  owns the accepted Ceres identity,
  manifest-backed resource, public selector, symbolic appearance, shared
  point/track reuse, evidence, and stop conditions;
- it identifies descriptor-aware provider resolution as the later 50A.3B seam
  and makes no source-tree or runtime ownership change itself;
- it preserves collection-oriented observed trajectories as the future common
  input to WCS/instrument-footprint planning, while keeping asteroid SPK/TDB
  and artificial-satellite OMM/TLE plus SGP4/TEME physics separate;
- current user documents, examples, and diagrams remain unchanged until an
  accepted implementation creates visible behavior.

## 50A.3B drawable-Ceres ownership (accepted)

- `sky/ceres.py` owns the Ceres descriptor and accepted Horizons solution
  identity;
- `minor_body_resources.py` owns explicit acquisition-manifest validation,
  descriptor-to-provider binding, one-open-kernel-per-build reuse, and
  deterministic close behavior;
- `sky/solar_system_points.py` and `sky/solar_system_tracks.py` own the generic
  target-source versus observer-source binding used by both planets and Ceres;
- chart arguments, requests, request generation, and drawing own opt-in
  selectors, resource-directory transport, and request-scoped lifecycle;
- the existing projection, preparation, renderer, exporter, and fixed-frame
  track owners remain unchanged;
- `tests/test_minor_body_resources.py` is a justified new test file because
  manifest failure and opened-kernel lifecycle are a new durable boundary; it
  does not repeat the 50A.2 numerical SPK or apparent-place oracles;
- `archive/milestone_history/50a_minor_bodies/drawable_ceres_50a3b.md` is the accepted implementation record,
  and `diagrams/drawable_ceres_50a3b.{dot,svg}` depicts the focused ownership
  boundary.

## 50A.3D installed-numbered-asteroid ownership (candidate)

- `minor_body_resources.py` owns structured collection validation, exact
  number/name lookup, manifest-derived descriptors, and provider lifecycle;
- chart arguments accept one numeric or candidate official-name spelling;
  command-line translation resolves it against the explicit resource set;
- `ChartRequest` owns request-specific descriptors, while request generation
  and direct drawing own temporary layer registration and restoration;
- `tools/acquire_numbered_asteroids.py` owns explicit Horizons/SBDB network
  acquisition and never participates in rendering;
- the built-in catalog, direction, projection, preparation, rendering, and
  export owners remain unchanged.

## 50A.3I numbered-asteroid CLI preflight ownership (candidate)

- `minor_body_acquisition.py` owns acquisition, policy, cache verification,
  coverage, locking, staging, and publication;
- `cli/chart.py` completes exact-number preflight before chart construction;
- `tools/acquire_numbered_asteroids.py` delegates to that acquisition owner;
- request, coordinate, projection, renderer, and export owners remain offline.

## 50A.4 comet numerical-validation ownership (accepted implementation)

- `tools/acquire_50a4_comet_evidence.py` alone owns deliberate network
  acquisition of raw 2P/Encke SBDB, Horizons SPK, vector, and observer evidence;
- `tools/build_50a4_comet_fixture.py` owns offline parsing, raw-evidence
  identity checks, and compact-oracle construction;
- `tests/fixtures/horizons_comet_validation_50a4.json` owns the frozen compact
  numerical oracle; the complete raw evidence remains local;
- `tools/validate_50a4_comet.py` owns accepted 50A.4 tolerance enforcement and
  optional non-accepting characterization while delegating provider and
  direction comparison to the existing 50A.2 scientific path;
- no descriptor, catalog, chart, CLI, rendering, or export owner changes.

## 50A.5A first-drawable-comet audit ownership

- `docs/developer/archive/milestone_history/50a_minor_bodies/first_drawable_comet_audit_50a5a.md` owns the accepted
  bounded 2P/Encke identity, resource, point, track, appearance, failure, and
  acceptance contract;
- existing runtime owners remain unchanged by the audit.

## 50A.5B.1 temporal-component corrective audit ownership

- `docs/developer/archive/milestone_history/50a_minor_bodies/solar_system_temporal_components_audit_50a5b1.md` owns the
  accepted common temporal-anchor and independently visible path, tick,
  symbol, label, and observed-phase reuse contract;
- `temporal_components.py` owns immutable start-inclusive `none`, `start`, and
  `major` selection without scientific realization;
- the generic Solar-System track realization is shared by its path, tick,
  symbol, and label views, while comet appearance supplies per-epoch
  orientation without reevaluating the target;
- the existing observed Venus and Moon and frozen-Earth Mercury sequence
  owners retain phase physics and apply the same policy only after complete
  scientific realization;
- Fernando accepted the Encke and Venus presentations, and the complete Mac
  gate passed all 2,331 tests in 84.56 seconds on 2026-09-13.

## 50A.5C second-drawable-comet audit ownership

- `docs/developer/archive/milestone_history/50a_minor_bodies/second_drawable_comet_audit_50a5c.md` alone owns the accepted
  161P/Hartley-IRAS second-resource evidence, generalization, visual-test, and
  acceptance boundary;
- the audit changes no runtime owner, fixture, command, or output;
- Fernando accepted the audit on 2026-09-13; bounded evidence acquisition and
  characterization are authorized, while tolerance selection remains pending
  measured-result review.
- `tools/acquire_50a5c_comet_identity.py` owns the first deliberate network
  checkpoint: it preserves signed SBDB and Horizons identity responses for
  `161P` without guessing or selecting an apparition record;
- `tests/test_acquire_50a5c_comet_identity.py` protects that new discovery
  boundary without repeating numerical, projection, or rendering tests.
- `tools/acquire_50a5c_comet_evidence.py` alone owns the subsequent full
  network acquisition bound to inspected record `90001107`, NAIF target
  `1000042`, solution `JPL#71`, and the three accepted 2026 characterization
  epochs; it publishes no partial evidence directory.
- `tools/build_50a4_comet_fixture.py` now exposes its existing parser through a
  parameterized comet specification while preserving the Encke wrapper;
- `tools/build_50a5c_comet_fixture.py` owns offline 161P identity binding and
  combines that shared numerical parsing with the accepted Sun/PsAng parser;
- `tools/validate_50a5c_comet.py` composes the existing minor-body numerical
  and antisolar validators; Fernando accepted the characterized shared comet
  envelopes, including `1e-5 deg` for observer-direction components and
  `0.01 deg` for PsAng, on 2026-09-13.
- `tests/fixtures/horizons_comet_validation_50a5c.json` is the frozen compact
  161P numerical, identity, SPK, observer, and provider-angle oracle;
- `tools/install_comet_resource.py` is the generic offline comet installer: it
  verifies fixture-declared evidence and the actual SPK segment before atomic
  publication, with no object-specific runtime branch;
- `MinorBodyResourceCollection` derives installed comet identity and exact
  aliases from that verified manifest, while `SkyfieldMinorBodyStateSource`
  exposes only exact installed provider `PsAng` epochs to the existing comet
  orientation adapter.
- `charts/center_arguments.py`, `charts/object_center.py`, and `cli/chart.py`
  jointly own generic named moving-center resolution. `--center-on-date`
  selects the apparent center and horizontal-frame instant; the existing
  temporal track owners retain every independent track-sample instant.


## 50A.5D comet-discovery and moving-object-report audit ownership

- `docs/developer/comet_discovery_and_reporting_audit_50a5d.md` alone owns the
  accepted discovery, generic comet preflight, report-sidecar, staged
  implementation, failure, and acceptance contract;
- the audit identifies SBDB query, existing minor-body preflight/cache, shared
  `SolarSystemTrackResult`, completed disk-sequence results, and request export
  as the future seams;
- the future scientific realization, not the serializer, owns instantaneous
  topocentric apparent rates in both right-ascension conventions, declination,
  and total sky-plane motion;
- no runtime, command, network, cache, coordinate, projection, renderer,
  semantic, report, or export owner changes in this audit.

## 50A.5D.1A deterministic comet-discovery ownership (accepted)

- `comet_discovery.py` owns SBDB query construction, UTC-to-TDB boundaries,
  typed rows, schema validation, sorting, and raw-response provenance;
- `cli/comets.py` owns only `wenu_retrieve_comets` parsing and table/JSON
  publication;
- `tests/test_comet_discovery.py` owns the provider query/parser/serialization
  boundary and uses a frozen provider-schema response without network access;
- `wenu_chart`, minor-body acquisition/cache, coordinate, projection,
  renderer, semantic, report, and export owners remain unchanged.

## 50A.5D.2A exact comet-name-resolution audit ownership

- `docs/developer/archive/milestone_history/50a_minor_bodies/comet_name_resolution_audit_50a5d2a.md` alone owns the
  candidate exact installed/provider identity-resolution contract;
- `MinorBodyResourceCollection` remains the installed-manifest alias
  authority, while `comet_discovery.py` remains the interval-set discovery
  owner;
- `minor_body_identity.py` is the candidate owner of exact installed/provider
  minor-body identity, mandatory class constraints, fixed SBDB response
  validation, alias construction, and provenance;
- `tests/test_minor_body_identity.py` owns the durable exact-identity seam and
  frozen unique, ambiguous, and wrong-class provider responses;
- the candidate authorizes no acquisition, cache, SPK, chart, coordinate,
  magnitude, report, renderer, semantic, or export integration.


## 50A.5D.2B generic comet-acquisition audit ownership

- `docs/developer/archive/milestone_history/50a_minor_bodies/comet_acquisition_audit_50a5d2b.md` alone owns the accepted
  provider, apparition, bounded-SPK, provenance, failure, and acceptance
  contract;
- `minor_body_identity.py` remains the exact identity owner;
- `minor_body_acquisition.py` is the authorized shared acquisition, coverage,
  validation, lock, and immutable-publication owner;
- `minor_body_resources.py` remains the installed manifest and resource
  lifecycle authority;
- `tests/test_minor_body_acquisition.py` remains the durable policy,
  acquisition, cache, lock, publication, and failure test owner;
- `cli/chart.py`, coordinate, projection, renderer, magnitude, report,
  semantic, and export owners do not change in the audit.

- the candidate implementation adds shared resolved-identity acquisition and
  policy entry points to `minor_body_acquisition.py`; it does not connect them
  to `cli/chart.py`;
- `tests/test_minor_body_acquisition.py` extends its existing responsibility
  with exact Horizons record binding, manifest loading, warm-cache, offline,
  target-mismatch, ambiguity, safe identity locks, and atomic-publication
  evidence.


## 50A.5D.2C exact comet CLI-preflight ownership (candidate implementation)

- `docs/developer/archive/milestone_history/50a_minor_bodies/comet_cli_preflight_audit_50a5d2c.md` owns the
  accepted request-composition, precedence, network, coverage, mixed-resource,
  failure, and acceptance contract;
- `cli/chart.py` collects typed asteroid/comet selections and coverage,
  validates an explicit directory, reuses an adequate complete warm cache,
  resolves missing exact identities, and installs one effective resource
  directory before sphere construction;
- `minor_body_identity.py`, `minor_body_acquisition.py`, and
  `minor_body_resources.py` retain exact identity, provider acquisition, and
  installed-resource authority respectively;
- `charts/command_line.py` and `charts/chart_arguments.py` retain parsing and
  request translation and acquire no data;
- coordinate, state, temporal-component, projection, renderer, semantic,
  style, furniture, and export owners do not change in the audit.

## 50S.1 provider-neutral satellite-crossing ownership (accepted)

- `src/wenu/satellite_crossings.py` owns immutable satellite identity,
  terrestrial observer/site, explicitly framed closed circular FoV, inclusive
  UTC interval, provider candidate, and normalized connected-visit result
  contracts;
- `src/wenu/coordinates.py` remains the shared coordinate vocabulary owner;
- `tests/test_satellite_crossings.py` owns the durable type, normalization,
  immutability, inclusive-endpoint, closed-boundary, ordering, query-containment,
  provenance, and invalid-input evidence;
- `docs/developer/satellite_guide.md` remains the living satellite scientific,
  provider-policy, equation, and evolving ownership guide;
- no `src/wenu/satellites/` package is admitted until several collaborating
  satellite production modules justify that boundary;
- acquisition, OMM/TLE ingestion, SGP4/TEME state, observer transformation,
  exact crossing solution, indexing, illumination, photometry, reports,
  charts, projection, rendering, semantic SVG, and export remain unchanged;
- Fernando accepted this ownership on 2026-09-15 after the focused 139-test
  gate and complete suite of 2,428 tests passed; PR #123 merged it as `23b851b`.


## 50S.2A SatChecker provider-contract audit ownership (accepted)

- `docs/developer/satchecker_provider_contract_audit_50s2a.md` owns the reviewed
  provider request, time-scale, coordinate, sampling, candidate-envelope,
  async, cache, failure, and redistribution decisions;
- `src/wenu/satellite_crossings.py` remains unchanged and retains the
  provider-neutral 50S.1 domain;
- no production adapter module is admitted by this documentation-only audit;
- the closest future production owner is a distinct provider boundary rather
  than coordinates, charts, rendering, or the provider-neutral domain module;
- ordinary provider-contract tests will use synthetic source-shaped specimens;
  no exact provider response may be committed until redistribution terms are
  clarified.


## 50S.2B SatChecker adapter ownership (accepted)

- `src/wenu/satchecker.py` owns the SatChecker-specific request translation,
  no-download UTC-to-UT1 boundary, exact receipts, one-shot submit/poll
  transport, task-state parsing, provider-schema normalization, sampled
  evidence, and exact local cache;
- `src/wenu/satellite_crossings.py` remains unchanged and owns only the
  provider-neutral candidate and exact-result domain;
- `tests/test_satchecker.py` owns the durable provider request, schema drift,
  identity/count consistency, sample containment, serial one-shot access,
  exact-byte cache, corruption, and no-network evidence;
- `tests/test_satellite_crossings.py` remains the independent 50S.1 domain
  owner and is included in the focused gate;
- no `src/wenu/satellites/` package is admitted by this second production
  module; later collaborating propagation and catalogue modules must re-review
  that package boundary;
- chart, projection, renderer, export, local SGP4/TEME, illumination,
  photometry, and detector-contamination owners remain unchanged.


## 50S.3A satellite report and drawing contract audit ownership (accepted)

- `docs/developer/satellite_report_drawing_audit_50s3a.md` owns the proposed
  sampled-candidate report, drawing, semantic, and acceptance contract;
- the audit changes no production module and admits no new runtime owner;
- `src/wenu/satchecker.py` remains the completed provider evidence owner and
  `src/wenu/satellite_crossings.py` remains the independent domain owner;
- future report and layer code must consume already-normalized evidence and
  must not reparse responses, access the network/cache, propagate, or synthesize
  `SatelliteCrossingResult`;
- existing coordinate, projection, preparation, renderer, semantic SVG, style,
  furniture, and PNG/PDF/SVG export owners remain authoritative;
- Fernando accepted the audit on 2026-09-15; only bounded 50S.3B report and sampled-candidate layer implementation is admitted next.


## 50S.3B satellite presentation ownership (accepted)

- `src/wenu/satellite_presentations.py` owns the terminal-response report
  model and deterministic human-readable/JSON serialization;
- `src/wenu/sky/satellite_candidate_layer.py` owns conversion of one
  normalized candidate's ordered samples into an open track or singleton point
  and optional supplied-sample points/UTC labels;
- `src/wenu/sky/semantic_identity.py` owns stable full-NORAD paths for the
  sampled track and samples;
- `tools/validate_50s3b_satellite_presentations.py` builds the network-free
  text/JSON and centered PNG/PDF/semantic-SVG acceptance products;
- `tests/test_satellite_presentations.py` owns report determinism,
  candidate-only wording, provenance, ordering, failure behavior, singleton
  behavior, point identities, coordinate handoff, semantic identity, and
  shared PNG/PDF/SVG pipeline evidence;
- `src/wenu/satchecker.py` remains unchanged and owns provider
  transport/cache/normalization; `src/wenu/satellite_crossings.py` remains
  unchanged and owns provider-neutral candidates and exact connected results;
- provider access, polling, cache reads, CLI orchestration, interpolation,
  propagation, exact crossing events, illumination calculation, photometry,
  and detector consequences are absent.


Fernando accepted the 50S.3B ownership and bounded implementation on
2026-09-15 after the 217-test focused gate, complete 2,473-test suite,
127-test documentation gate, clean diff check, and PNG/PDF/semantic-SVG visual
review passed. Only 50S.4 is authorized next.


## 50S.4A snapshot and propagation contract audit ownership (accepted)

- `docs/developer/satellite_snapshot_propagation_audit_50s4a.md` owns the
  proposed dependency, canonical OMM element, immutable snapshot,
  SGP4/geometric-TEME, Earth-orientation/topocentric, numerical validation, and
  developer-specimen contracts;
- the audit changes no production code, dependency, fixture, or package data;
- no current module absorbs these responsibilities;
- after acceptance, several collaborating modules justify the first
  `src/wenu/satellites/` package, with distinct element, snapshot, SGP4, and
  topocentric owners;
- `satchecker.py`, `satellite_crossings.py`, `ephemeris.py`,
  `coordinate_service.py`, presentation, chart, renderer, semantic, and
  export ownership remain unchanged;
- Fernando accepted 50S.4A on 2026-09-15 after the focused documentation
  gate passed all 128 tests and the branch diff check was clean;
- acceptance closes 50S.4A and authorizes only 50S.4B canonical elements and
  the tiny synthetic installed snapshot, not propagation or observer
  transformation.


## 50S.4B satellite element and snapshot ownership (accepted)

- `src/wenu/satellites/elements.py` owns the immutable canonical OMM/GP
  record, strict value/semantic validation, canonical JSON encoding, and
  source-record digest verification;
- `src/wenu/satellites/snapshots.py` owns versioned manifest validation,
  canonical-byte and snapshot-digest verification, deterministic full-NORAD
  ordering, duplicate rejection, immutable lookup, and installed loading;
- `src/wenu/data/satellites/snapshots/synthetic_50s4b_v1/` owns three
  hand-authored non-operational LEO/MEO/geosynchronous-like resources and
  their reviewed provenance;
- `tests/test_satellite_elements.py` owns immutability, six-digit identity,
  schema/semantic rejection, ordering/duplicate/count faults, installed
  loading, canonical bytes, and record/snapshot digest failure evidence;
- `pyproject.toml` declares `sgp4>=2.25,<3` directly and includes the
  snapshot JSON and README as package data;
- no SGP4 adapter, propagation, TEME state, Earth-orientation transformation,
  observer direction, acquisition, crossing solver, presentation, or
  rendering behavior is added.

At production commit `d3cb597`, the 158-test expanded gate, 2,483-test
complete suite, and isolated installed-wheel snapshot check passed. The
installed resource digest was
`b6ab95df3eb180b07694b1b9bafd47c2805b6cc7ebea8636490beec03cd71457`.
Fernando accepted this ownership on 2026-09-15. This closes 50S.4B and
authorizes only 50S.4C validated SGP4/TEME propagation.


## 50S.4C SGP4/TEME propagation ownership (accepted)

- `src/wenu/satellites/sgp4.py` owns canonical-OMM mapping, explicit WGS-72
  initialization, UTC-to-split-Julian-date conversion, scalar/array execution,
  upstream status translation, and immutable geometric TEME state provenance;
- `tests/test_satellite_sgp4.py` owns pinned Vallado near-Earth/deep-space
  wrapper vectors, terminal error behavior, split-date precision,
  snapshot-identity propagation, immutability, and scalar/array parity;
- the accepted synthetic snapshot now uses identifiers 300001–300003 because
  the upstream `Satrec` limit is 339999; its record and content digests were
  regenerated without hidden identity substitution;
- `elements.py` and `snapshots.py` retain their accepted responsibilities;
- TEME-to-ITRS transformation, EOP handling, observer subtraction,
  topocentric coordinates, crossings, acquisition, presentation, and
  rendering remain absent.

At production commit `e0d7c78`, the 167-test expanded gate and 2,492-test
complete suite passed. An isolated installed wheel verified snapshot digest
`2e5288a6aad9fbe29cfe6d9a60e0045be28501859d8c739135fd302460ece5fe`
and successful TEME/WGS-72/status-zero propagation for all three records.


Fernando accepted this ownership on 2026-09-15 after all implementation, complete-suite, documentation, and installed-wheel gates passed. Only 50S.4D Earth-orientation and topocentric state work is authorized next.


## 50S.4D Earth-orientation/topocentric ownership (accepted)

- `src/wenu/satellites/topocentric.py` owns explicit installed-IERS-A
  selection and identity, TEME → ITRS transformation, WGS-84 observer
  subtraction, topocentric Cartesian/range state, vacuum AltAz, and the
  carefully named GCRS-axis geometric direction;
- `tests/test_satellite_topocentric.py` owns exact resource identity,
  fail-closed coverage, independent Skyfield comparison, direct Cartesian
  subtraction/range, constructed zenith/horizon/wrap geometry, pathological
  sites, orbit-regime specimens, immutability, and policy rejection;
- `satellites/sgp4.py` retains propagation ownership;
- `satellite_crossings.py` retains query, candidate, and exact-result domain
  ownership;
- `coordinate_service.py` remains the spherical-geometry transform owner and
  does not absorb satellite Cartesian Earth-orientation work;
- crossing solution, field intersection, illumination, photometry,
  presentation, rendering, export, and 50S.4E specimens remain absent.

A new production module is justified because EOP resource provenance,
terrestrial transformation, observer subtraction, and coverage failure form a
distinct lifecycle and failure boundary from OMM snapshot loading, SGP4
propagation, and generic spherical geometry transformation. Fernando accepted
this ownership on 2026-09-15. Only 50S.4E specimen-builder work is authorized
next.

### Accepted 50S.4E developer specimen ownership

- `tools/build_50s4_satellite_specimens.py` owns explicit, deterministic,
  network-free composition of the installed synthetic snapshot with accepted
  SGP4/TEME and topocentric services. It writes only **propagated sampled
  specimens — not verified crossings** to a caller-selected directory.
- `tests/test_satellite_specimens.py` owns the durable output-schema,
  determinism, provenance, offline, explicit-destination, and no-crossing-claim
  contract for that developer tool.
- No new `src/wenu` module is admitted because 50S.4E adds no runtime
  authority. Crossing construction and oracle ownership remain reserved for
  50S.5.

Fernando accepted this ownership boundary on 2026-09-15. The tool remains
developer-only after 50S.4 closure; 50S.5 must establish its own durable runtime
oracle ownership rather than expanding this specimen builder.


### Accepted 50S.5A local crossing-oracle ownership

- `src/wenu/satellite_crossings.py` continues to own provider-neutral
  immutable crossing values; it does not own local numerical solving.
- `src/wenu/satellites/crossing_oracle.py` will own the distinct
  exhaustive trajectory-evaluation, adaptive convergence, root/extremum,
  connected-visit, provenance, and fail-closed responsibility in bounded
  50S.5B implementation.
- `tests/test_satellite_crossing_oracle.py` will own independent
  analytic/adversarial numerical-oracle evidence plus installed-snapshot
  composition and provenance. The closest existing
  `tests/test_satellite_crossings.py` remains focused on immutable value
  contracts.
- This audit creates neither future source nor test file and changes no
  package boundary.

Fernando scientifically and architecturally accepted this ownership contract
on 2026-09-15. Only bounded 50S.5B implementation is authorized next; 50S.6
and later behavior remain unauthorized.

### Accepted 50S.5B local crossing-oracle ownership

- `src/wenu/satellites/crossing_oracle.py` owns the immutable local query,
  exhaustive adaptive evaluation, root/minimum refinement, tolerance-connected
  visit assembly, deterministic ordering, provenance, and convergence failure;
- `src/wenu/satellite_crossings.py` retains provider-neutral identity, field,
  interval, candidate, and result value contracts;
- `tests/test_satellite_crossing_oracle.py` owns analytic trajectories
  independent of SGP4/Astropy plus installed-snapshot composition and resource
  provenance;
- `satellites/sgp4.py`, `satellites/topocentric.py`, and
  `satellites/snapshots.py` retain their accepted lower-level ownership.

The new production file is justified by its distinct numerical-convergence and
fail-closed lifecycle. It adds no provider, cache, rendering, reporting,
illumination, photometry, or 50S.6 responsibility. Fernando scientifically and
architecturally accepted this ownership on 2026-09-15. Only a documentation-first
50S.6 acceleration audit is authorized next.

### Accepted 50S.6A acceleration ownership audit

- `satellite_crossing_acceleration_audit_50s6a.md` owns the documentation-only
  conservative-filter, validation, benchmark, failure, and ownership decision;
- `src/wenu/satellites/crossing_oracle.py` remains the accepted exhaustive
  exact owner and is unchanged;
- a later `src/wenu/satellites/crossing_acceleration.py` may own only admitted
  candidate selection, rejection evidence, and exact-oracle coordination;
- a later `tests/test_satellite_crossing_acceleration.py` may own the durable
  tri-state filter oracle and zero-false-negative equivalence matrix.

This accepted audit creates neither future source nor acceleration test file
and changes no package boundary. Only bounded 50S.6B implementation of the
first cone/orbital-shell selector is authorized next.

### Accepted 50S.6B selector ownership

- `src/wenu/satellites/crossing_acceleration.py` owns immutable first-stage
  policy, tri-state decision, selection, and conservative cap construction;
- `src/wenu/satellites/crossing_oracle.py` remains unchanged and owns exact
  trajectory solving and crossing results;
- `tests/test_satellite_crossing_acceleration.py` owns the selector's durable
  domain-bound, tri-state, ordering, fallback, and exact-oracle rejection
  evidence;
- package exports expose the four selector contracts but no accelerated search
  service.

No phase, coarse-state, horizon, occultation, indexing, coordinator, reporting,
or rendering responsibility is added. Fernando accepted this ownership on
2026-09-16; only a documentation-first 50S.6C audit is authorized next.

### Accepted 50S.6C coordination ownership audit

- `satellite_crossing_coordination_audit_50s6c.md` owns the documentation-only
  coordinator, broader-domain, equivalence, failure, and benchmark-admission
  decision;
- `src/wenu/satellites/crossing_oracle.py` retains exact numerical solving and
  would own one shared record-level seam used by both routes;
- `src/wenu/satellites/crossing_acceleration.py` retains selector ownership
  and may later own only admitted coordination, ordered-decision validation,
  fallback, evaluation accounting, and acceleration evidence;
- `tests/test_satellite_crossing_oracle.py` remains the independent exact
  oracle suite, while `tests/test_satellite_crossing_acceleration.py` would
  own coordination and equivalence evidence;
- any later benchmark driver belongs under `tools/` and cannot become a
  runtime dependency.

This audit creates no source, runtime test, benchmark tool, fixture, dependency,
or package export. Fernando accepted this ownership on 2026-09-16; only a
bounded 50S.6D coordinator is authorized next.


### Candidate 50S.6D coordinator ownership

- `src/wenu/satellites/crossing_oracle.py` owns the unchanged exact numerical
  algorithm and one package-internal record seam used by both public routes;
- `src/wenu/satellites/crossing_acceleration.py` owns immutable coordinator
  policy, ordered evidence validation, selection composition, fallback,
  exact-evaluation accounting, and the opt-in accelerated service;
- `src/wenu/satellites/__init__.py` exports the three candidate coordinator
  contracts without changing the exhaustive default;
- `tests/test_satellite_crossing_oracle.py` remains the independent exact
  numerical authority;
- `tests/test_satellite_crossing_acceleration.py` owns fake-selector
  invariants, instrumented shared-seam accounting, fallback behavior, and
  real-selector exhaustive equivalence.

No new production module or test file is admitted: the new behavior has the
same selector-coordination lifecycle and ownership as
`crossing_acceleration.py`. No benchmark tool, fixture, dependency,
coordinate service, CLI, report, renderer, or exporter changes.
