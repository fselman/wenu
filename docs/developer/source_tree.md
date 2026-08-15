# Wenu source organization

**Architecture version:** 0.8

Milestone 46A extends the registered coordinate-grid family with native
observer-local `AltAzGrid` geometry. Selection remains in render-local detail,
appearance remains in style, and the chart type continues to own the horizon.
**Status:** Implemented

The source tree is organized by responsibility. Astronomical objects and sky
layers do not import chart or renderer policy, and all chart styles and modes
share the same geometry and rendering pipeline.

## Principal packages

```text
src/wenu/
├── observer.py                 observing context
├── objects/                    catalogues and physical object layers
├── sky/                        celestial layers and draw orchestration
├── geometry/                   spherical/projected values and algorithms
├── projections/                coordinate-neutral map projections
├── charts/                     chart types, composition, detail, styles,
│                               legends, boundaries, and export workflow
├── rendering/                  preparation and Matplotlib backend
├── resources/                  installed-resource access
├── cli/                        installed command adapters
├── example_scripts/            packaged canonical user examples
├── data/                       distributed astronomical datasets
└── utils/                      general utilities
```

`projections/mollweide.py` owns coordinate-neutral equal-area projection and
longitude-seam topology for points, curves, grids, and polygon rings. It has
no astronomical-frame, chart, renderer, or Matplotlib dependency.

Within `sky/`, `maximal_sphere.py` owns the immutable catalogue load profile
and the one canonical complete-content factory. The resulting object is an
ordinary `CelestialSphere`; chart geometry and presentation remain outside
the factory.
Its ordinary `generate_celestial_sphere()` entry point leaves the sphere and
every canonical layer observer-independent. The compatibility
`build_maximal_sphere(observer, ...)` entry point remains available while the
request facade migrates.
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
the request resolver does not inspect sky geometry.
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
`charts/coordinate_frames.py` owns astronomical transformation of canonical
AltAz spherical geometry into a chart-selected celestial frame before
projection. It preserves geometry structure and metadata and contains no map
projection, seam, viewport, renderer, or style implementation.
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
All constellation-subject examples use this one adapter; a single region is
represented by a one-element `--constellations` value rather than a parallel
singular parser.
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
├── detail.py                     detail policies and resolved detail
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

See `target_architecture_v0.7.md` for the implemented architecture,
`wenu_migration_0.6_to_0.7.md` for the completed roadmap,
`current_architecture_v0.6.md` for the historical baseline, and
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

`examples/circumpolar.py` and its byte-identical packaged resource expose the
family's existing limiting-declination framing value as an ordinary argument.
They still only declare a view and delegate horizon controls to the shared
request and drawing facades.

`tests/test_canonical_all_sky_example.py` owns the all-sky declaration's
explicit Galactic Mollweide geometry, default detail, optional disjoint mask,
shared drawing delegation, and observer cleanup. Shared example and installer
tests own CLI parity, short-source boundaries, and byte identity with the
packaged resource; `tests/test_user_guide.py` owns its guide contract.

## Test-suite responsibility and tiers

`docs/developer/configuration_default_audit.md` is the Milestone 46D authority
map for public defaults. It separates public values from derived values,
invariants, and implementation details; inventories every responsibility and
appearance source; and records duplications that must be removed as TOML
becomes authoritative. It is an audit input, not a runtime registry.

`docs/developer/configuration_schema_v1.md` is the Milestone 46D.2 structural
contract for the future authoritative TOML document. It orders every public
namespace, defines scalar and closed-vocabulary validation, requires
independent color/line-width/line-style keys, and specifies complete-path
diagnostics and the non-executable data boundary. It is not a parser, packaged
default file, overlay loader, command implementation, or runtime registry.

`src/wenu/configuration/defaults.toml` is the Milestone 46D.3A complete
commented version-1 public-default document. Its package contains data only;
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
adapter. It owns the six subcommand parsers, effective observer and subject
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
observer, subject, projection, coordinate frame, frame, orientation, pole,
declination-limit, and mask requests before catalogue loading or rendering.

`tests/test_wenu_chart_drawing_parity.py` owns Milestone 46D.8B's downstream
installed-command contract. It lets `draw_chart_view_from_arguments()` resolve
the complete public drawing vocabulary and captures the immutable arguments
at the existing `draw_chart_view()` boundary. It also proves deterministic
four-product naming without constructing catalogues or a renderer.

`tests/test_wenu_chart_configuration_isolation.py` owns Milestone 46D.8C's
installed-command overlay boundary. It proves sequential partial overlays and
packaged defaults remain independent on one reused sphere identity and that
explicit command observer, subject, geometry, product, title, language, and
destination values retain final precedence. `tests/test_wenu_chart_cli.py`
owns the complementary early-failure order before observer, sphere, view, or
drawing work.

`tools/render_46d8_visual_matrix.py` and
`tests/test_visual_acceptance_matrix.py` own Milestone 46D.8D's reproducible
visual handoff. The tool drives the actual command module in fresh processes
and writes 18 untracked PNGs plus a checksum manifest. The test verifies the
matrix shape and role coverage without rendering; human acceptance is recorded
in `docs/developer/visual_acceptance_46d8.md` only after Mac review.

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
`docs/developer/visual_acceptance_46d8.md` owns the truthful closure record:
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
pytest -q -m "not integration and not visual and not slow"
pytest -q -m integration
pytest -q -m visual
pytest -q
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

`tools/render_46d8_visual_matrix.py` is the final command-surface visual
acceptance harness. It is intentionally separate from the reusable-sphere
benchmark: each entry launches `python -m wenu.cli.chart` in a fresh process,
and its output directory remains ignored rather than becoming a golden-image
test fixture.

Canonical integration tests use a session-scoped build registry to reuse an
identical example sphere and chart across read-only contracts. Distinct
observer, catalogue-depth, constellation-selection, target, mask, or framing
requests remain distinct builds. The registry closes every owned observer at
session teardown and does not replace the full builder smoke coverage for any
canonical chart family.
