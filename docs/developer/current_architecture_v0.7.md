# Wenu current architecture v0.7

**Status:** Implemented baseline for the v0.8 migration
**Baseline commit:** `b72eef8`
**Date:** 2026-08-05

Wenu v0.7 implements independently selectable equatorial, ecliptic, and
Galactic coordinate-grid layers. It does not implement an observer-local
AltAz grid, although horizontal coordinates are already the canonical
spherical geometry used by projection and rendering. The horizon remains
chart-owned boundary geometry and is not optional reference content.

The canonical flow, ownership boundaries, declarative examples, render-local
detail policy, style ownership, and packaged-example parity documented by
`target_architecture_v0.7.md` remain in force.

The permanent test suite is organized by these current responsibilities rather
than by completed milestone history. Fast unit, integration, visual, and full
commands are recorded in `source_tree.md`; the full suite remains the release
authority and atlas print remains the visual reference baseline.

Milestone 46D.2 specifies the future version-1 TOML namespace in
`configuration_schema_v1.md`. The specification fixes responsibility and key
ordering, value vocabularies, validation rules, full-path diagnostics, and a
strict non-executable boundary. It is documentation only: no configuration
parser, packaged defaults, overlay, command, or runtime default authority is
implemented yet.

Milestone 46D.3A adds the complete commented version-1 document as the
installed `wenu.configuration/defaults.toml` resource. Resource and
characterization tests prove deterministic ordering, responsibility coverage,
independent line fields, and audited baseline values. Existing Python owners
remain the runtime authority until strict validation and typed translation are
implemented in later 46D.3 slices, so this step changes no chart behavior.

Milestone 46D.3B loads that resource without current-directory dependence and
strictly validates complete version-1 documents before any catalogue, chart,
or renderer work. Validation rejects unknown or missing paths, nondeterministic
ordering, wrong types, non-finite numbers, invalid colors and ranges,
unsupported vocabularies and versions, and contradictory combinations with a
complete configuration path. Typed chart owners still use their existing
Python defaults; translation remains the next 46D.3 responsibility.

Milestone 46D.3C translates the validated atlas and cartoon semantic bases,
print and presentation modes, and their palettes into the existing immutable
style and mode dataclasses. Exact equality with the established constructors
is characterized. Composition still constructs its existing Python defaults;
the translated objects are a parity seam only and cannot change rendering.

Milestone 46D.3D translates the six family geometry tables, neutral and
content detail, cartoon and adaptive policies, canonical family magnitude
ceilings, and binocular fixed detail and stellar sizing into the existing
immutable view, detail, and style-component contracts. Exact equality with
the established Python authorities is characterized. Regional width and
height remain unrepresentable in the current view-default contract and fail
with a complete path instead of being ignored. Active request resolution and
composition remain deliberately unconnected.

Milestone 46D.3E translates reference and pole annotations, footer and
context options, family legend plans, magnitude-legend appearance, default
product selection, and export options into their existing immutable owners.
Footer layout coordinates, product language/title/extension, and export
padding have no aggregate behavioral owner yet, so frozen translation
metadata preserves them without inventing runtime wiring. Exact constructor
parity is characterized, and request resolution, composition, rendering, path
generation, and export remain unchanged.

Milestone 46D.4A makes the cached packaged style/mode translation the runtime
authority for named atlas/cartoon and print/presentation composition. The
packaged presentation and cartoon palettes, label offset, clearance, and halo
opacity are passed explicitly through the existing mode adapters. Explicit
style and mode objects retain final precedence, and geometry, detail,
furniture, and export remain unchanged. Direct constructors remain supported
compatibility APIs but are no longer the canonical named-composition source.

Milestone 46D.4B makes the cached packaged geometry/detail translation the
runtime authority at `chart_view_defaults()` and for neutral/cartoon named
composition. Packaged default and cartoon content-layer sets travel with the
detail policies and govern layer additions/removals. Explicit view arguments,
detail policies, and detail overrides retain their established precedence.
Chart construction, projection, catalogue loading, and rendering are
unchanged.

Milestone 46D.4C makes one cached furniture/product/export translation the
runtime authority for neutral ordinary furniture, family legend placement,
stellar-magnitude legend appearance, footer layout, parser product defaults,
output extensions, and base export options. Output-mode DPI and transparency,
circular transparency, and canvas face color remain derived at composition
time. Legends and context remain opt-in furniture rather than becoming
visible merely because their configured contract defaults exist. Explicit
furniture, product arguments, output paths, and export options retain
precedence; zero packaged export padding preserves Matplotlib's established
atlas-print crop.

The v0.8 migration now provides one immutable canonical load profile and one
maximal-sphere factory. It loads complete reusable astronomical content for an
observer and returns the existing `CelestialSphere`; chart geometry,
coordinate-grid spacing, detail, presentation, and export remain downstream
request concerns.

Stellar AltAz realization is cached per loaded `Stars` layer using observer
location, instant, ephemeris identity, data directory, catalogue identity,
and source revision. Render-local magnitude and identifier selections mask
that immutable maximal realization, and constellation figures reuse it.
Vectorized point catalogues use the same key identity: open-cluster and
planetary-nebula selections index immutable maximal AltAz center arrays.
Milky Way and Magellanic Cloud level selections likewise index immutable
maximal observed ring arrays. Official constellation boundaries cache their
complete sampled B1875 realization; the native source revision and sampling
step are part of the cache identity, while the requested constellation set
remains render-local.
Extended-object layers cache complete observed outline catalogues at each
requested geometry quality. Sample count and minimum displayed angular size
belong to the cache identity; magnitude and identifier subsets are applied
afterward. Galaxies, Messier-style objects, globular clusters, and supernova
remnants share this policy through `NonStellar`.

Milestone 46C.7A adds an immutable public chart-request graph. It separates
the scientific observer and instant, subject identity, optional framing,
content, detail, furniture, product, language, title, and output. It is a
declarative contract only: resolution and generation continue to be added
incrementally over the canonical sphere and chart pipeline.

Milestone 46C.7B adds an offline packaged target cross-identification
resolver. A resolved target preserves its display identity and ICRS center
while separately naming every catalogue family and identifier required to
draw it. Unknown and ambiguous aliases raise explicit user-facing errors;
explicit coordinates retain user provenance and need no packaged component.

Milestone 46C.7C adds the corresponding offline constellation-subject
resolver. It accepts arbitrary IAU abbreviation sets and packaged teaching
groups, and resolves their public region identities into the distinct line,
boundary, and label identifiers required internally. In particular, a public
`Ser` request consistently expands to `Ser1`/`Ser2` figures and
`SerCap`/`SerCau` labels while retaining one official boundary identity.
Teaching-group framing and curated legacy-example content are packaged data,
not example-script globals.

Milestone 46C.7D adds one request-resolution boundary before construction.
It resolves targets or constellation subjects, unions the central target and
packaged group content into an immutable render-local selection, and rejects
detail ceilings that exceed the chosen maximal-sphere load profile. The
original request remains unchanged; no chart, renderer, or export work occurs
in this phase.

Milestone 46C.7E resolves family framing defaults without constructing chart
geometry. Binocular requests receive the established 6.5-degree field unless
overridden; packaged groups provide their recorded width and height; arbitrary
IAU sets explicitly defer automatic framing to their authoritative geometry.

Milestone 46C.7F completes that operation in the existing
`RegionalChart.from_constellations()` constructor. With no explicit field it
derives a spherical center and maximum great-circle extent from all unique
loaded figure endpoints, then applies configurable padding and a minimum
field. Explicit-radius calls retain their previous result.

Milestone 46C.7G adds render-local spatial catalogue selection after a chart
field exists. Catalogue centers reuse the observer/time point cache, are
projected through the selected chart, and are tested against its viewport and
circular field stop where present. Visible identifiers are unioned with
explicit selections and the already retained central target.

Milestone 46C.7H adds immutable catalogue exclusions to the chart request.
They are applied after packaged, explicit, and automatic field selection.
Contradictory explicit inclusion is rejected, and a resolved central target
cannot be excluded silently.

Milestone 46C.7I adds one chart-construction boundary over resolved requests.
It constructs the established full-sky, regional, circumpolar, or binocular
chart, then applies spatial content selection. `FullSkyChart` now owns the
same official-boundary outside-mask operation already used by regional charts;
its horizon also bounds spatial catalogue selection. No request facade
subclass or private example pipeline is required.

Milestone 46C.7J closes the ordinary declarative facade. Public
`generate_chart_request()` owns one observer and canonical maximal sphere,
resolves and prepares the request, composes each requested product through
the established composition API, exports each product exactly once, and
closes its observer even after failure. `export_prepared_chart()` exposes the
same final composition/export boundary for a caller that already owns a
compatible prepared sphere and chart request. Named targets without a
drawable packaged catalogue component are rejected before construction.

Milestone 46C.8A allows that same facade to receive a compatible prebuilt
maximal sphere. `ChartObserverRequest` normalizes its scientific location and
UTC instant without constructing an observer or loading an ephemeris; the
facade compares that identity and the sphere's declared load profile before
resolution. A supplied sphere remains caller-owned and is never closed or
rebuilt. Omitting it retains the standalone owned-sphere behavior.

Milestone 46C.8B moves canonical coordinate-grid density into one request-time
configuration boundary. Only grids explicitly selected by detail or label
options are registered. Before each request, previously registered semantic
grids are removed and the selected planisphere, regional, circumpolar, or
binocular configuration is installed in canonical drawing order. Astronomical
catalogue layers are untouched, the maximal load profile remains grid-free,
and repeated requests cannot accumulate duplicate grid layers.

Milestone 46C.8C adds immutable product-specific composition options to the
chart-request graph. An exact atlas/cartoon and print/presentation product may
select its detail policy and post-mode style overrides without changing the
request's family, frame, projection, mask, or other chart geometry. The
generation facade applies those options at the established composition
boundary; products without an explicit entry retain their previous defaults.

Milestone 46C.8D adds one family-neutral late context-furniture boundary.
`ChartContextOptions` records chart-center, active-grid, observer-location,
date, and local-time selections without requiring a constructed chart or sky.
The request exporter realizes those selections only after chart construction,
then supplies immutable context lines to the established legend furniture.
The same contract applies to all canonical chart families and contains no
target, framing, projection, or example-specific policy.

Milestone 46C.8E exposes the request facade's existing construction phase as
`build_chart_request()`. It resolves and prepares any chart family without
rendering or exporting, using either an owned canonical maximal sphere or a
compatible caller-owned sphere. Its `ChartRequestBuild` records resource
ownership, exposes the prepared chart, supports deterministic context-manager
cleanup, closes an owned observer at most once, and never closes a supplied
sphere. `generate_chart_request()` now delegates to this same preparation
boundary before the established single export.

Milestone 46C.8F migrates the canonical binocular example to that shared
request scaffold. The script declares its observer, packaged target, field,
content, products, detail, style overrides, furniture, and title; the common
facades own maximal content, target/component resolution, chart preparation,
composition, rendering, and single export. `TARGETS`, manual catalogue and
grid registration, Matplotlib orchestration, and repeated saving are removed.
Its compatibility `build_chart()` uses `build_chart_request()` and accepts a
caller-owned sphere. Any packaged drawable target is accepted without a script
change, while Centaurus A and Omega Centauri retain their approved fields and
publication identities.

Milestone 46C.8H introduces the execution seam required by the target
observer-independent sphere. `CelestialSphere.draw_chart()` accepts an
explicit observer, which overrides its compatibility bound observer, and the
canonical chart, masking, spatial-selection, label-placement, context, and
reference-furniture paths carry that observer without changing the layer
contract. Existing calls that omit it retain their v0.7 behavior.

Milestone 46C.8I adds `generate_celestial_sphere()` as the first ordinary
three-stage operation. It loads the canonical native catalogues and geometry
under an explicit load profile into an ordinary `CelestialSphere` whose
observer is `None`; its canonical layers are likewise unbound. The established
observer-bound `build_maximal_sphere()` and request facade remain compatible
until observer-bound views become the ordinary construction boundary.

Milestone 46C.8J adds `get_chart_view()` as the second ordinary operation. It
binds a caller-owned scientific observer to an observer-independent sphere,
resolves the friendly subject and frame vocabulary through the advanced
request graph, and prepares the established canonical chart geometry. The
returned frozen `ChartView` exposes geometry and resolved provenance but no
appearance, drawing, furniture, language, title, output, or cleanup state.
Only the implemented stereographic projection is accepted.

Milestone 46C.8K centralizes ordinary geometry defaults in immutable
`ChartViewDefaults` values. The five policies distinguish binocular,
regional-single, regional-group, planisphere, and circumpolar framing while
sharing stereographic projection, zero position angle, and an unmasked view.
The ordinary facade fills omitted values from this policy before translating
to the advanced request graph; explicit values still win. Canonical examples
will continue to state scientifically important publication geometry rather
than relying invisibly on these defaults.

Milestone 46C.8L adds `draw_chart_view()` as the third ordinary operation. A
call selects exactly one style/mode product and may supply a structured detail
policy, render-local overrides, semantic grids and labels, furniture, visual
overrides, title, language, and destination. The adapter retains the view's
chart and resolved spatial content, configures grids through the existing
request boundary, and delegates to the canonical request composition and
single-export workflow. Its return value is the resulting `ChartExportResult`.

Milestone 46C.8M adds the shared command-line adapter over that same ordinary
workflow. `add_chart_cli_arguments()` owns the complete common product,
content, appearance, legend, context, and credit switches;
`draw_chart_view_from_arguments()` resolves them and calls
`draw_chart_view()` once for every selected product. Examples retain only
their explicit geometrical defaults, subject arguments, and product-specific
detail policy. The adapter contains no catalogue loading, projection,
rendering, furniture-drawing, or export implementation of its own.

Milestone 46C.8N replaces all five canonical examples with short declarations
over `generate_celestial_sphere()`, `get_chart_view()`, and
`draw_chart_view_from_arguments()`. Each source and installed copy is
byte-identical and shorter than 70 lines. Packaged resolvers now supply target
and group data; examples retain only reproducible observer/time values,
explicit family geometry, family-specific detail, titles, and CLI arguments.
The former example-owned catalogue builders, request builders, renderer loops,
and compatibility-only `build_chart()` helpers are removed.

Milestone 46C.8O.4 makes planisphere constellation masks observer-visible
multi-patch geometry. Official selected boundaries are obtained before
projection; wholly hidden regions are omitted, while partially visible and
disjoint regions remain complete openings clipped by the chart-owned horizon.
The canonical planisphere exposes this through the shared constellation
subject adapter and an explicit mask switch without owning visibility or
clipping logic. All canonical examples with a constellation subject use the
same shared `--constellations IAU,...` / `--group ALIAS` parser; the former
single-constellation example is merely the one-element default case.

Milestone 46C.8P.1 makes projection and spherical coordinate-frame identity
part of the immutable request geometry. `ChartView` now exposes those values
from its resolved request rather than storing a disconnected projection tag.
Regional, binocular, circumpolar, and planisphere requests accept only
stereographic projection in the horizontal frame; the all-sky family accepts
only Mollweide projection in the Galactic frame.

Milestone 46C.8P.2 adds the chart-owned pre-projection transformation from
canonical observer-bound AltAz spherical geometry to Galactic longitude and
latitude. It handles points, curves, grids, and polygons without changing
their entity identity or collection metadata. The transformation uses the
observer's authoritative Astropy frames and remains separate from both sky
layers and coordinate-neutral map projections.

Milestone 46C.8P.3 adds a public coordinate-neutral `MollweideProjection`.
Its equal-area mathematics accepts generic longitude and latitude, centers a
configurable longitude, and follows Wenu's east-left orientation convention.
Before planar evaluation it unwraps and clips curves, grid components, and
polygon rings into longitude slabs, preserving separate seam pieces and
duplicating per-entity metadata without creating map-spanning chords.

Milestone 46C.8P.4 adds `AllSkyChart` as a distinct complete-sphere chart.
It transforms canonical observer-bound spherical geometry to Galactic
longitude and latitude immediately before the coordinate-neutral Mollweide
projection, centers Galactic longitude zero, and clips every layer and mask
patch at its 2:1 elliptical boundary. Complete-sphere catalogue selection
does not apply observer-horizon rejection. Ordinary all-sky drawing defaults
to a labeled Galactic grid; explicit equatorial and ecliptic grids remain
transformed overlays through the same sky execution path.

Milestone 46C.8P.5 adds the sixth canonical example, `all_sky.py`. Its source
and installed resource are byte-identical short declarations over the same
observer-independent sphere, observer-bound view, shared constellation
subject parser, drawing adapter, product matrix, and furniture adapter as the
other examples. It spells out the Galactic Mollweide request geometry while
leaving frame transformation, seam topology, elliptical clipping, density,
rendering, and export in their established library owners.
Composition reduces built-in all-sky stellar scatter area to one quarter of
the corresponding circular-chart value. This preserves approximately the
same marker diameter relative to the map when the output changes from a
circle to the physically half-height 2:1 ellipse; the resolved style also
keeps the magnitude legend on the identical scale.
Constellation-boundary content is rendered as transparent polygon outlines;
enabling official boundaries therefore never paints or darkens the interiors
of constellation masks.

Milestone 46C.8Q.1 records the approved next horizon contract without yet
changing runtime behavior. The planisphere retains its altitude-zero chart
boundary. Other families will gain independent optional horizon-reference and
below-horizon-mask roles derived from the same observer-bound geometry.
The horizon mask will reuse the resolved translucent outside-mask style, and
combined constellation and horizon restrictions will be composed into one
visible opening before a single mask is painted so opacity cannot accumulate.

Milestone 46C.8Q.2 adds public semantic `HorizonReference` geometry. It is an
observer-local `GeometricalObject` whose spherical realization delegates to
the existing native AltAz altitude-zero curve and records one closed
`horizon` reference. `CelestialSphere.add_horizon_reference()` registers it
independently of `AltAzGrid`; the canonical maximal sphere does not load it,
and no request, CLI, style, masking, or default drawing behavior changes yet.

Milestone 46C.8Q.3 adds independent immutable `horizon` and `horizon_mask`
values to `ChartRequest`, matching `--horizon` and `--horizon-mask` switches
to the shared content parser, and equivalent `draw_chart_view()` options.
The common command-line adapter forwards both values for every canonical and
installed example. They remain declaration-only in this milestone: no chart
registers or paints horizon content until the later lifecycle, mask, and
appearance milestones, so current rendering and planisphere behavior remain
unchanged.

Milestone 46C.8Q.4 gives the optional reference a request-time lifecycle.
`configure_chart_request_horizon()` first removes every prior semantic
`HorizonReference`, then registers exactly one only when `request.horizon` is
true and the family is not `planisphere`. The common build and drawing paths
invoke it beside, but independently from, grid configuration. AltAz request
grids continue to exclude their own horizon, `horizon_mask` alone registers
nothing, and registered horizon geometry remains enabled independently of
astronomical detail density. Appearance and below-horizon masking remain for
later milestones.

Milestone 46C.8Q.5 adds projection-neutral preparation of the mask's
above-horizon opening without painting it. `HorizonReference` tessellates the
native AltAz hemisphere into spherical polygon wedges derived from the same
altitude-zero geometry. Stereographic preparation inverse-projects the final
field boundary to classify it as wholly above, crossing, or wholly below the
horizon; only a crossing field projects the hemisphere tessellation through
the established projection-domain guard. Complete-sphere preparation applies
the chart-owned horizontal-to-Galactic transformation before Mollweide
projection, whose existing longitude-seam topology produces valid separate
pieces. Q.5 does not yet combine or draw masks.

Milestone 46C.8Q.6 composes every selected mask restriction before drawing.
Constellation regions and the above-horizon hemisphere remain independent
opening groups; the renderer encodes one viewport winding per group and all
group holes in one compound nonzero-winding path. The only transparent area
is therefore the intersection of the selected openings, while their excluded
union is painted once with the existing outside-mask style. Disjoint openings,
chart-boundary clipping, and Mollweide seam pieces remain intact without
stacking translucent patches. Planispheres ignore horizon masking and retain
their intrinsic horizon boundary.

Milestone 46C.8Q.7 gives the semantic horizon explicit style-owned color,
linewidth, linestyle, alpha, and z-order beside the other reference and grid
appearance. Atlas and cartoon output-mode adapters may scale or recolor that
line, but neither style nor mode participates in horizon geometry. Every
chart mask now obtains its appearance through
`resolved_outside_mask_style()`; binocular delegation transports that same
resolved `MaskStyle` to its regional renderer, so horizon-only and combined
masks use one color, alpha, and z-order policy in every chart family.

Milestone 46C.8Q.8 closes the behavioral contract with tests rather than a
second implementation. The shared CLI and Python facade preserve all four
horizon-reference/mask states independently. Regional, binocular,
circumpolar, Galactic Mollweide, and planisphere paths prove their respective
viewport, circular-boundary, seam, and no-op policies. Compound-path winding
is checked directly: only the intersection of independent openings has zero
winding, while one translucent patch covers their excluded union. Reordering
all horizon states on one reused sphere replaces or removes only the semantic
horizon and preserves unrelated layers.

Milestone 46C.8Q.9.1 begins visual closure without another rendering path.
All regression products use the six canonical examples and their shared
adapter. The circumpolar declaration exposes its existing chart-owned
limiting declination as `--limiting-declination`, allowing a horizon crossing
to be inspected without moving horizon logic into the example. Final approval
remains pending the fixed visual matrix.

The Q.9 visual review exposed that automatic regional framing still measured
only constellation-figure endpoints. Regional requests now keep the resolved
line identities for figure drawing but pass the separate official IAU region
identities to `RegionalChart.from_constellations()` for automatic centering
and radius. The resulting padded field contains every sampled boundary vertex;
explicit width and height requests remain authoritative.

Milestone 46C.9 validates every canonical chart family against one actual
observer-independent maximal sphere. Planisphere, regional-single,
regional-group, circumpolar, binocular, and Galactic all-sky views retain
their exact resolved subjects, masks, frames, and render-local catalogue
selections independently of request order. The same loaded sphere serves
additional La Ligua instants and Papudo without acquiring an observer.
Observer location, instant, ephemeris, data directory, catalogue identity,
and source revision remain part of observed-cache identity; returning to an
earlier compatible state reuses the immutable stellar AltAz arrays.

Milestone 46C.10 closes the reusable observed-sky work with a diagnostic Mac
benchmark, not a runtime timing threshold. One canonical sphere supplies 18
views spanning all six chart families and three observer/instant identities.
The measured run built the canonical sphere once in 4.530 seconds; populated
observed caches contained three compatible identities, optional unused outline
caches remained empty, and repeating the first stellar AltAz request added no
cache entry. Selection, projection,
preparation, rendering, and export profiler totals are reported separately;
the cumulative categories intentionally overlap. All required suites passed,
and the 18 atlas-print products were visually approved. Faint-star symbol
saturation remains a deferred appearance-curation concern rather than a
reusable-sphere architectural defect.
