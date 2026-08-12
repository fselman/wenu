# Wenu source organization

**Architecture version:** 0.7

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
├── example_scripts/            packaged canonical user examples
├── data/                       distributed astronomical datasets
└── utils/                      general utilities
```

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
Within `charts/`, `request.py` owns the immutable ordinary-user request graph,
including catalogue exclusions; it contains no catalogue resolution,
projection, rendering, or export work.
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
constellation endpoints; the request resolver does not inspect sky geometry.
`charts/spatial_selection.py` owns vectorized field-footprint selection over
cached catalogue centers; it applies explicit exclusions, returns immutable
content, and does not render.
`charts/request_chart.py` maps a resolved request onto the four established
chart types and invokes that selector; composition and export remain in their
existing modules.
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
├── regional.py, full_sky.py,
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
- all five canonical examples use the ordinary three-stage interface; each
  source and installed resource is byte-identical, shorter than 70 lines, and
  contains no private catalogue construction, request graph, renderer, legend
  assembly, or export loop.

See `target_architecture_v0.7.md` for the implemented architecture,
`wenu_migration_0.6_to_0.7.md` for the completed roadmap,
`current_architecture_v0.6.md` for the historical baseline, and
`implementation_reference.md` for current public usage.

The structured user guide is rooted at `docs/user_guide/index.md`; its
`assets/` directory contains only the provenance-controlled README image.

The user-facing `examples/` directory contains only the five canonical chart
families as short declarations over the shared sphere, view, drawing, and CLI
facades. Historical component demonstrations that still provide regression
coverage live under `tests/fixtures/example_regressions/`; they are test-local
fixtures, not supported user examples.

## Test-suite responsibility and tiers

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

Canonical integration tests use a session-scoped build registry to reuse an
identical example sphere and chart across read-only contracts. Distinct
observer, catalogue-depth, constellation-selection, target, mask, or framing
requests remain distinct builds. The registry closes every owned observer at
session teardown and does not replace the full builder smoke coverage for any
canonical chart family.
