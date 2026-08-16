# Wenu implementation reference

**Architecture version:** 0.8
**Status:** Implemented
**Date:** 2026-08-15

This reference records the implemented public chart workflow. Lower-level
geometry, projection, preparation, and rendering APIs remain available for
advanced use, but ordinary chart production uses a resolved composition.

## 1. Canonical public imports

```python
from wenu import (
    AdaptiveDetailPolicy,
    AllSkyChart,
    AtlasChartStyle,
    BinocularChart,
    CartoonDetailPolicy,
    CelestialSphere,
    ChartContentOptions,
    ChartLegendSelection,
    ChartStyleOverrides,
    CircumpolarChart,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    SkyContentSelection,
    add_chart_arguments,
    chart_detail_overrides,
    compose_chart,
)
```

The stable named choices are:

- chart styles: `"atlas"` and `"cartoon"`;
- output modes: `"print"` (with `"paper"` as an alias) and
  `"presentation"`.

`Observer` owns its loaded Skyfield ephemeris. Call `observer.close()` when
its lifetime ends, or use `with Observer(...) as observer:` for deterministic
cleanup. Existing callers retain automatic finalization as a safety net.

## 2. Independent chart concerns

| Concern | Owns |
|---|---|
| Chart type | projection, framing, viewport, and final boundary |
| Style | visual appearance |
| Output mode | dimensions, DPI, and medium-specific visual scaling |
| Detail policy | astronomical selection and density |
| Legend policy | object, stellar-magnitude, and contextual furniture |

Styles and modes do not change chart geometry. Detail is resolved into
render-local layer options, so sequential exports of the same sky do not leak
selection state.

## 3. Canonical composition and export

```python
composition = compose_chart(
    chart,
    style="atlas",
    mode="print",
    detail=FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=6.0)
    ),
    legends=LegendOptions(
        objects=True,
        stellar_magnitudes=True,
        context=True,
    ),
)

result = chart.export(
    sky,
    MatplotlibRenderer(ax),
    "chart.png",
    composition=composition,
)
```

`chart.export()` resolves render-local layer options, invokes the existing
chart renderer, draws requested legends, and saves exactly once. It returns a
`ChartExportResult`; established two-value unpacking remains supported:

```python
rendering, saved = result
```

Compatibility `style=` and `layer_options=` arguments remain available for
existing callers.

Canonical examples may add the complete shared command-line contract with:

```python
add_chart_arguments(parser, default_output="output/example")
```

The parsed request separates product selection, astronomical content,
appearance, and legends. Content and legend switches are opt-in. Explicit
visual overrides are immutable and apply after style/mode resolution:

```python
composition = compose_chart(
    chart,
    style="cartoon",
    mode="presentation",
    style_overrides=ChartStyleOverrides(
        constellation_linewidth=2.0,
        constellation_line_color="white",
    ),
)
```

Omitting `style_overrides` preserves the resolved style and mode defaults.
`chart_detail_overrides(arguments)` applies the caller magnitude limit and
the explicitly selected constellation and coordinate-grid layers relative to
the selected detail policy. Constellation lines, labels, and boundaries are
independent opt-in requests. It retains cartoon constellation-vertex
selection even when line figures are hidden.

Each canonical example exposes independent equatorial, ecliptic, and Galactic
grid and grid-label switches. A `*-grid-labels` switch enables only its own
grid. The grid systems use black, orange, and blue respectively for both
their default lines and numeric labels. The principal equator, ecliptic, and
Galactic plane remain separate furniture selected with
`--grid-references SELECTION`.

Cartoon presentation resolves a trichromatic palette: deep-blue background,
yellow stars/lines/boundaries/context, and white footer credits. Cartoon print
uses white paper with black structure, context, and credits. Circular chart
boundaries obtain their appearance from the resolved cartoon mode without
changing their chart-owned geometry. When Milky Way or Magellanic Cloud
isophotes are selected as cartoon content, they use unshaded dotted contours:
yellow in presentation and black in print.

## 4. Chart types

The canonical workflow supports:

- `RegionalChart`;
- `FullSkyChart`;
- `AllSkyChart`;
- `CircumpolarChart`;
- `BinocularChart`.

Each chart exposes `chart_context`, `render(...)`, and `export(...)` according
to its geometry and boundary requirements. `FullSkyChart` may place its
stereographic tangent point independently of the observer zenith; the observer
still determines the AltAz sky and horizon. `CircumpolarChart` owns its
declination-parallel boundary and circular grid-label anchor; when no explicit
boundary appearance is supplied, it resolves that appearance from the chart
style before delegating clipping to its circular rendering chart.
`BinocularChart` uses the same shared boundary-resolution contract, so direct
binocular compositions receive a visible style-owned aperture rim while an
explicit `boundary_style` retains precedence.
Circular charts, including full-sky planispheres, paint their style-owned sky
color only inside the clipping
boundary. Their default raster export leaves the surrounding figure and axes
area transparent while retaining titles and footer furniture.
The canonical `all_sky.py` example requests the complete Galactic sphere with
Mollweide projection, central longitude zero, position angle zero, and an
adaptive atlas magnitude ceiling of 5.0. Its labeled Galactic grid is supplied
by the ordinary all-sky drawing default. The shared constellation-subject
parser optionally supplies arbitrary adjacent or disjoint region masks; no
example code transforms coordinates, splits the seam, or clips the ellipse.
Built-in atlas and cartoon compositions use one quarter of their ordinary
stellar scatter area for this half-height map, halving marker diameter while
keeping rendered stars and the magnitude legend consistent.
Constellation boundaries are outline-only content: their polygons always use
a transparent face, including when an outside-region mask is also enabled.
The canonical `binocular_object.py` example centers the same binocular chart
family on any drawable target in the packaged resolver and accepts an explicit
field diameter. Centaurus A (NGC 5128) and Omega Centauri (NGC 5139) remain
the documented regression targets. Like the other five canonical examples,
it generates one observer-independent sphere, obtains one observer-bound view,
and delegates the selected product matrix to
`draw_chart_view_from_arguments()`. It has no private target dictionary,
catalogue loading, request graph, renderer, or export loop.
The binocular stellar-magnitude legend defaults outside the rectangular axes
at lower right so its frame remains clear of the circular aperture.
Its stellar presentation opts into `StellarMagnitudeSizing` with the resolved
limiting magnitude as the reference, so the faintest selected magnitude uses
the configured minimum scatter area. Brighter stars grow by the configured
exponent and are bounded by the configured maximum area. The rendered stars
and stellar magnitude legend use the same sizing configuration.
Milestone 46D.8I makes binocular products grid-free by default; all four grid
systems remain explicit opt-ins. The title includes the resolved ICRS center
and field diameter, and unregistered reference furniture marks the resolved
target with a `+` through the ordinary projection and clipping pipeline. The
binocular-only exponent is `0.35`, with minimum area `1.0` and maximum area
`40.0`. Named binocular atlas composition selects the existing packaged fixed
detail policy, so its limiting-magnitude sizing reference is always defined.
The render callback is installed only when the supplied sphere contains a
stellar layer; catalogue-free and empty-sky composition remains empty.

Milestone 46D.8J changes no API or rendering behavior. It records acceptance
of the remediated `2883e67` implementation while retaining the fixed visual
matrix for a later complete rerun.
`ChartContext.horizon_altitude_deg` optionally carries a chart-owned altitude
floor into composition detail application. Circumpolar charts set it to
`-90.0`, so their declination field and reference furniture are not clipped
at the observer's horizon; other circular chart families retain their prior
behavior.

## 4.1 Canonical examples

The supported user examples are exactly:

- `planisphere.py`;
- `regional_constellation_group.py`;
- `regional_constellation.py`;
- `circumpolar.py`;
- `binocular_object.py`.

An installed Wenu distribution provides the `wenu_examples` command. Running
it creates `wenu_examples/` in the current directory and installs these five
scripts from package resources. Existing scripts are preserved unless the
caller supplies `--force`.

Catalogue, symbol, legend, clipping, and historical style demonstrations are
test-local regression fixtures rather than additional public examples.
Every canonical example is a fewer-than-70-line declaration, and its source
copy is byte-identical to the corresponding installed package resource.

## 5. Styles and modes

Named styles are resolved by `compose_chart()`:

```python
printed = compose_chart(chart, style="atlas", mode="print")
slides = compose_chart(chart, style="atlas", mode="presentation")
cartoon = compose_chart(chart, style="cartoon", mode="print")
```

Concrete style and mode objects may also be supplied. Use
`cartoon_chart_style(...)` when explicit cartoon label placement or palette
controls are required.

## 6. Detail policies

Available policies include:

- `FixedDetailPolicy` for explicit resolved values;
- `AdaptiveDetailPolicy` for field-size-dependent density, optionally with a
  fixed publication `star_magnitude_limit` while its deep-sky thresholds
  remain adaptive;
- `CartoonDetailPolicy` for restrained cartoon content while preserving
  constellation vertices and admitting only configured bright galaxies and
  large clusters alongside the Milky Way and Magellanic Clouds.

`DetailOverrides` modifies a policy without merging content choices into
style or mode. Layer selection is applied locally for each render.

`SkyContentSelection` carries immutable named subsets for one render and is
owned by `ResolvedDetail.content_selection`. `None` preserves a registered
layer's default selection, while an empty set explicitly selects no members
of that family. The v0.8 migration initially applies the catalogue and
constellation-label selections already supported by layer geometry. It also
applies constellation-line and boundary subsets and Milky Way, LMC, and SMC
isophote levels as render-local geometry options. These selections do not
change the registered layers' loaded content or defaults.
Resolved chart requests use the established `ol2` through `ol5` Milky Way
levels when no levels are supplied, thereby omitting the outer complement
without removing it from maximal loaded content. Explicit level requests
retain precedence.

`ResolvedDetail.extended_object_samples` may request a lower render-local
sampling density for extended-object outlines. It applies to Messier-style
non-stellar objects, galaxies, globular clusters, and supernova remnants.
The request cannot exceed the layer's construction-time maximum sampling
quality; fixed-symbol open clusters and planetary nebulae are unaffected.

## 7. Legends

`LegendOptions` independently controls:

- canonical deep-sky object symbols;
- the visible stellar magnitude scale;
- chart-center and coordinate-system context;
- observer, location, date, and time when applicable.

Legend content is derived from resolved enabled layers. Legends are drawn as
part of export before the single final save.
Planisphere legends use outside placements clear of the circular sky.
`LegendOptions.symbol_labels` and `LegendOptions.stellar_title` permit
example-local language overrides without changing global English defaults.

## 8. Canonical execution core

All chart combinations retain the same execution flow:

```text
catalogues and sky layers
    -> spherical geometry
    -> projection-domain guard
    -> projection
    -> projected geometry
    -> chart preparation
    -> CelestialSphere.draw_chart()
    -> renderer
    -> legends and export
```

The low-level call remains available to advanced callers:

```python
result = sky.draw_chart(
    projection=projection,
    renderer=renderer,
    viewport=viewport,
    layer_options=layer_options,
)
```

### Reusable maximal sphere

`build_maximal_sphere(observer)` loads the complete canonical astronomical
content once and returns an ordinary `CelestialSphere`. Its immutable
`CelestialSphereLoadProfile` records catalogue sources, magnitude ceilings,
and maximum extended-object sampling quality. Before resolving a chart
request, call `sky.load_profile.require(...)`; it raises `ValueError` rather
than allowing a request deeper than the loaded data.

The factory does not select a projection, chart frame, mask, grid spacing,
detail, style, legend, renderer, or output. Coordinate grids remain
request-time geometry because their spacing and extent differ by chart
family. Rendering continues through `CelestialSphere.draw_chart()`.

The loaded stellar layer computes its maximal observer-time AltAz arrays on
first use. Later magnitude selections and constellation-line geometry for the
same observer and instant reuse those immutable arrays. A different observer,
instant, ephemeris, data directory, catalogue, or source reload selects a
different cache entry; presentation and render state never enter the key.
Open clusters and planetary nebulae likewise transform their complete loaded
center catalogues once and obtain ordered render-local subsets by identifier.
Milky Way and Magellanic Cloud isophotes transform every loaded ring in one
maximal vectorized operation and apply level choices afterward. Constellation
boundaries do the same after native B1875 sampling; their cache key includes
the sampling step so geometry quality cannot be reused accidentally.
Sampled extended-object outlines are cached once per observer, loaded source,
source revision, sample count, and minimum displayed angular size. Identifier
and supported magnitude selections then index that immutable maximal
realization. This shared `NonStellar` behavior covers ordinary nonstellar
objects, galaxies, globular clusters, and supernova remnants.

`ChartRequest` is the immutable input shared by the Python facade and future
command-line adapter. `ChartObserverRequest` defines the actual observing
location and instant; `ChartSubjectRequest` accepts one target, explicit ICRS
coordinate, constellation set, or packaged group; and `ChartFrameRequest`
holds optional framing overrides. Existing `SkyContentSelection`,
`DetailOverrides`, `ChartFurnitureOptions`, and `ChartProductOptions` remain
the corresponding content, detail, furniture, and output contracts.
`ChartContentExclusions` names deep-sky catalogue identifiers that must be
omitted after field selection; it does not mutate loaded catalogue content.
`ChartProductCompositionOptions` optionally assigns a detail policy and
`ChartStyleOverrides` to one exact selected `ChartProduct`. These values are
resolved only at composition time. They cannot carry framing, projection,
masking, or other chart geometry, and duplicate or unselected product entries
are rejected when the request is constructed.
`ChartFurnitureOptions.context` may carry `ChartContextOptions` selecting
chart-center coordinates, the active coordinate-grid description, observer
location, date, and local time. These are declarative booleans rather than
precomputed strings. The request exporter resolves them after both the chart
and sky exist, appends any caller-supplied context lines, and passes the result
through the established immutable legend furniture. The contract is shared by
all four chart families.

`resolve_target(ChartSubjectRequest(...))` resolves packaged aliases without
network access. Its immutable `ResolvedTarget` records canonical key, display
name, ICRS coordinate, matched alias, provenance, and `TargetComponent`
values. The initial packaged cross-identifications cover the canonical
Centaurus A and Omega Centauri fields plus M13, M16, M17, M57, M7, and the
Veil Nebula usage-audit targets. Unknown and ambiguous aliases are errors,
not empty successful charts.
`ResolvedTarget.coordinate` provides its authoritative center as an ICRS
`SkyCoord`; `primary_identifier` exposes the first drawable component in
publication form. These preserve compatibility builders and titles without
duplicating coordinates or catalogue spelling in example scripts.

`resolve_constellation_subject(ChartSubjectRequest(...))` accepts either an
ordered IAU abbreviation set or a packaged teaching-group alias. Its
`ResolvedConstellationSubject` keeps public region identities separate from
the line, boundary, and label identifiers consumed downstream. A public
Serpens (`Ser`) request expands to the two figure and label identities
without requiring callers to know `Ser1`, `Ser2`, `SerCap`, or `SerCau`.
Packaged groups also carry their provenance, legacy canonical framing
defaults, and curated content identifiers until spatial field selection
replaces the latter in a later 46C.7 step.

`resolve_chart_request(request, profile)` combines those subject results with
the request's explicit `SkyContentSelection`. Target components are always
unioned into the appropriate catalogue family so a central target is not
lost to general thresholds. It calls the load profile's established
`require()` contract for requested stellar depth, galaxy depth, and outline
sampling, returning a new immutable `ResolvedChartRequest` without modifying
the input request or constructing a chart.

The returned `ResolvedChartFrame` records the effective explicit, family, or
packaged-group field and its provenance. `automatic_from_geometry=True` means
an arbitrary constellation set must be framed later from loaded authoritative
geometry; it is not replaced by a guessed fixed field.

`RegionalChart.from_constellations()` may omit `angular_radius_deg`. It then
frames all selected loaded figure endpoints using their spherical mean,
maximum great-circle separation, `framing_padding` (default 1.15), and
`minimum_angular_radius_deg` (default 5). Supplying radius and aspect ratio
continues to provide exact publication control.

`select_spatial_chart_content(sky, chart, resolved_request)` obtains cached
AltAz centers for every registered deep-sky catalogue, projects them through
the chart, and returns a new request containing field objects plus explicit
inclusions and target components, minus the request's explicit exclusions.
An identifier cannot be both explicitly included and excluded, and the
resolved central target cannot be excluded. Extended-object layers expose
`spherical_centers()` so selection does not sample their outlines.

`prepare_chart_request(sky, resolved_request)` constructs the established
chart type from the resolved family, target, constellation identities, field,
position angle, pole, and mask. It then applies the spatial selector and
returns an immutable `PreparedChartRequest`. It neither builds a second sky
nor composes, renders, or exports. A masked planisphere is an ordinary
`FullSkyChart` whose optional outside mask uses the shared official-boundary
masking operation; its chart-owned horizon limits automatic field objects.

`build_chart_request(request, sky=None)` is the public non-exporting facade
over observer/sphere acquisition, resolution, request-time grids, chart
construction, and spatial selection. It returns `ChartRequestBuild`, which
exposes `sky`, `prepared`, and `chart`. When it constructs the sphere it owns
the observer and closes it once through `close()` or context-manager exit; a
supplied compatible sphere remains caller-owned and is never closed. Failure
during an owned build closes the observer before propagating the error.

`generate_chart_request(request)` is the ordinary one-call facade. It owns
the observer and canonical maximal sphere, resolves and prepares the request,
and returns a `ChartRequestGeneration` containing the inspectable
`ChartExportResult` values and their output paths. It always closes the owned
observer. Advanced callers that already have a compatible sphere may call
`export_prepared_chart(sky, prepared_request)` after resolution and
preparation; this avoids rebuilding the sphere while retaining the same
canonical composition and single-export path.
The resolved request also carries `horizon_mask` through this export boundary
as a render option. Regional, binocular, circumpolar, and Galactic all-sky
charts prepare the above-horizon opening beside any constellation opening.
The mask composer passes all independent groups to one
`MatplotlibRenderer.draw_outside_mask()` call; nonzero winding leaves only
their intersection transparent and applies the resolved outside-mask alpha
once. A planisphere accepts the shared option but deliberately performs no
horizon-mask operation because its horizon is already the chart boundary.
Generation delegates its entire preparation phase to
`build_chart_request()`, then exports the returned prepared request and closes
only resources recorded as owned by that build result.
For each selected output, that export boundary applies the request's matching
`ChartProductCompositionOptions` before the common render-local detail
overrides. Omitting a matching entry preserves the established style-derived
detail and mode defaults.
It also realizes optional `ChartContextOptions` once per prepared request,
before product composition, so every product receives identical scientific
metadata without requiring example-side access to a constructed chart.

`generate_chart_request(request, sky=existing_sphere)` provides the simpler
reuse adapter needed by canonical examples and batch callers. The sphere must
declare a load profile and its observer's normalized latitude, longitude,
elevation, and UTC instant must match `request.observer`. The facade resolves,
prepares, composes, and exports against that sphere without rebuilding or
closing it. `ChartObserverRequest.scientific_identity()` performs this check
without loading an ephemeris. When `sky` is omitted, generation continues to
own and close its observer and sphere resources.

`configure_chart_request_grids(sky, request, frame=...)` owns coordinate grids as
request-time geometry. It derives explicit grid selection from
`DetailOverrides.enabled_layers`, `enabled_layer_additions`,
`disabled_layers`, and `grid_label_layers`; labels imply the corresponding
geometry. It replaces only prior `CoordinatesGrid` layers and registers a
15-degree density for resolved views smaller than 60 degrees and a 30-degree
density otherwise. This makes sequential
requests order-independent without adding coordinate grids to the maximal
load profile or mutating astronomical catalogue content. Ordinary generation
calls this boundary automatically after request resolution.

`HorizonReference(observer=None, samples=721)` is the semantic observer-local
altitude-zero curve. `spherical_geometry(observer)` returns one closed native
AltAz curve named `horizon`; an observerless instance requires the execution
observer explicitly. `CelestialSphere.add_horizon_reference()` registers the
layer without adding an `AltAzGrid`. The maximal-sphere factory does not add
this request-time geometry.

`ChartRequest.horizon` and `ChartRequest.horizon_mask` are independent frozen
request booleans. The shared chart-content parser exposes them as `--horizon`
and `--horizon-mask`; `draw_chart_view(..., horizon=False,
horizon_mask=False)` provides the matching ordinary Python interface, and
`draw_chart_view_from_arguments()` forwards both through the common adapter.
Q.3 declares and transports the controls only. Request-time layer lifecycle,
mask geometry, appearance, and visible behavior remain assigned to Q.4
through Q.7.

`configure_chart_request_horizon(sky, request)` owns the optional reference
lifecycle. It removes prior `HorizonReference` instances on every call,
clears `sky.horizon_reference`, and registers one replacement only when
`request.horizon` is true and the family is not `planisphere`. It returns the
registered reference or `None`. The canonical request builder and ordinary
drawing facade call this configurator after grid configuration. An AltAz grid
continues to use `include_horizon=False`; `horizon_mask` does not imply the
reference. Because registration itself is the selection boundary, resolved
astronomical detail policies do not disable a registered semantic horizon.
`PublicationStyle.horizon_reference_style()` supplies its explicit color,
linewidth, linestyle, alpha, and z-order. `ChartStyle` stores those semantic
values in `GridStyle`, and atlas/cartoon output adapters alter appearance only.
The reference remains an ordinary sky layer rendered through
`CelestialSphere.draw_chart()`; styles never construct or transform its
geometry.

`HorizonReference.visible_hemisphere_geometry(observer,
radial_step_deg=5)` returns native AltAz `SphericalPolygons` tessellating the
altitude-nonnegative hemisphere. Its metadata identifies an `above_horizon`
mask opening and its altitude-zero vertices come from the same sampled
semantic horizon used by the reference curve.

`resolved_outside_mask_style(style)` is the sole chart-family fallback and
conversion boundary for mask appearance. It returns the existing resolved
`MaskStyle` as Matplotlib face color, alpha, and z-order options. Horizon-only,
constellation-only, and combined masks all pass that same mapping to the one
compound mask draw; no horizon-specific opacity setting exists.

The packaged cartoon mask uses warm white `#fffdf5` at opacity `0.45` and
z-order `20.0`. Milestone 46D.8H.2 records the values selected through a local
user-overlay render; atlas appearance and the shared compound-mask geometry and
rendering contracts are unchanged.

Milestone 46D.8H.1 preserves that translated cartoon `MaskStyle` through mode
realization. The presentation palette continues to resolve the canvas and
semantic drawing colors but no longer substitutes its sky color into the mask.
User TOML therefore controls the final cartoon mask color and opacity.

The Q.8 contract suite exercises the four independent `(horizon,
horizon_mask)` control states through both shared adapters, chart-family mask
boundaries, planisphere idempotence with and without constellation masking,
Mollweide seam-piece grouping, compound-path winding and single alpha, and
forward/reverse request sequences on one reusable `CelestialSphere`. These
are tests of the established pipeline; Q.8 adds no alternate geometry,
projection, clipping, rendering, or export path.

The ordinary interfaces are final: shared scripts use `--horizon` and
`--horizon-mask`, while Python callers use `draw_chart_view(...,
horizon=True, horizon_mask=True)`. Neither interface implies the other role.
The canonical circumpolar declaration additionally exposes
`--limiting-declination`; this changes the chart-owned polar field boundary
and does not participate in horizon geometry or appearance.

For automatic regional fields, `RegionalChart.from_constellations()` accepts
`framing_constellations` independently of its figure-line identities. The
ordinary request builder supplies official IAU boundary identities there, so
the spherical center and padded angular radius cover the complete selected
regions. This does not select boundary-line appearance, alter Serpens figure
connectivity, or override an explicitly requested field size.

`StereographicProjection.unproject_spherical(x, y)` performs the inverse
planar mapping and returns coordinates in the projection's source frame. It
is the classification boundary used by horizon-mask preparation; it does not
perform astronomy, clipping, or masking.

`PolarAzimuthalEquidistantProjection(radius=2, pole="south",
position_angle_deg=0, flip_ew=True)` maps polar angular distance linearly in
projected radius. `radius` is the equatorial projected radius. The projection
supports north and south poles, forward and inverse spherical mapping,
position angle, handedness, radius conversion, viewport construction, and the
ordinary point, curve, grid, and polygon dispatch contract. Milestone 48B.1
does not connect it to a chart family or physical planisphere product.

`ProjectionSelection(name, coordinate_frame)` is the frozen projection
identity used at the request/view boundary. The accepted pairs are
stereographic/horizontal, stereographic/equatorial, Mollweide/Galactic, and
polar-azimuthal-equidistant/equatorial. `build(**geometry)` imports and
constructs a fresh selected
projection lazily; projection scale, position angle, handedness, pole, and
central longitude remain chart-owned constructor values. `ChartView` exposes
the value as `projection_selection`. Existing v0.8 families still reject the
polar pair until a polar chart owner is added.

`prepare_horizon_mask_opening(...)` returns a frozen `PreparedHorizonMask`
with `visibility` equal to `above`, `crossing`, or `below`, native spherical
openings, and prepared projected openings. Regional, binocular, and
circumpolar fields are classified from their final rectangular or circular
boundary. Wholly above fields use the viewport as their opening, wholly below
fields use no opening, and crossing fields project the AltAz tessellation
through `project_geometry_for_viewport()`. With `complete_sphere=True`, the
optional chart-owned transformation is applied before projection; Galactic
Mollweide therefore reuses its established seam splitting. This function
prepares geometry only and does not call a renderer.

`CelestialSphere.draw_chart(..., observer=observer)` selects the scientific
observer explicitly for every registered layer. The same optional keyword is
carried by canonical chart rendering and export, request preparation and
export, spatial selection, masking, constellation-label placement, and
contextual or celestial-reference furniture. Omitting it uses `sky.observer`
for backward compatibility; an observerless sphere must receive it explicitly.

`generate_celestial_sphere(profile=CANONICAL_MAXIMAL_SPHERE_PROFILE)` loads
one reusable observer-independent canonical sphere. The sphere owns its load
profile, native catalogue content, provenance, and observed-geometry caches,
but neither it nor its canonical layers select an observer or instant. The
compatibility `build_maximal_sphere(observer, profile=...)` retains the prior
observer-bound behavior.

`tools/benchmark_reusable_sphere.py` is the reproducible diagnostic for that
contract. It builds one sphere, prepares and exports six chart families for
three observer/instant identities, prints progress for 37 operations, and
writes operation timings, overlapping profiler categories, and observed-cache
counts to JSON. It deliberately defines no pass/fail timing threshold.

`get_chart_view(sky, observer, *, family, ...)` obtains one geometrical view
from that reusable sphere. `observer` is an existing caller-owned `Observer`;
the view neither creates nor closes it. Friendly target, coordinate,
constellation, group, field, position-angle, pole, declination-limit, and mask
arguments are resolved by the established request and preparation contracts.
The returned frozen `ChartView` exposes `chart`, `family`, `mask`,
`projection_name`, `coordinate_frame`, `target`, `constellations`, and
`frame`, and `projection_selection`. Both identities come from the resolved
immutable `ChartRequest` and the selection pairs them without constructing a
projection until requested.
Regional, binocular, circumpolar, and planisphere views use stereographic
projection in the horizontal frame. The all-sky view uses Mollweide projection
in the Galactic frame. Other combinations are rejected explicitly. Style,
mode, detail, grids, furniture, language, title, and output remain drawing
concerns.

`charts.coordinate_frames.horizontal_to_galactic(geometry, observer)` is the
chart-owned astronomical frame adapter reserved for Galactic all-sky views.
It accepts `SphericalPoints`, `SphericalCurves`, `SphericalGrid`, or
`SphericalPolygons`, interprets their generic longitude and latitude as the
canonical AltAz geometry for `observer.altaz_frame`, and returns the same
geometry form in `observer.galactic_frame`. Entity identifiers, labels,
names, closed-curve state, component groups, and metadata are preserved;
metadata records the AltAz source and Galactic result. It performs no seam
splitting, planar projection, clipping, rendering, or example adaptation.
`horizontal_to_equatorial(geometry, observer)` applies the same structure- and
metadata-preserving contract to `observer.icrs_frame`; it is the astronomical
transformation seam required by static polar disks.

`PolarPlanisphereChart(pole="south", limiting_declination_deg=None,
projection_name="polar_azimuthal_equidistant", position_angle_deg=0,
projection_radius=2, physical_diameter_mm=195, flip_ew=True)` describes one
immutable polar disk face. An omitted limit resolves to +20 degrees for the
south face and -20 degrees for the north face. The chart accepts either the
linear polar-equidistant projection or an equatorial stereographic
alternative, while retaining the same selected pole, circular declination
boundary, exact centre, square viewport, physical diameter, and canonical
AltAz-to-ICRS render/export path. Physical diameter is declared product
geometry and does not alter normalized projection coordinates. Pairing,
calendar furniture, registration, and horizon overlay are not part of this
class.

`PolarPlanispherePairRequest(...)` is the immutable source of truth for a
matched back-to-back pair. It accepts the shared projection name, position
angle, projection radius, physical diameter, boundary sampling, south-face
handedness, and optional calendar and pivot radii, plus independently named
north and south declination limits. Equal physical scale requires those limits
to produce equal polar angular radii. `resolve()` returns a
`PolarPlanispherePair` containing fresh north/south charts and frozen
`PolarFaceRegistration` records. The resolver derives projection-aware
opposite paper RA direction: the equidistant pair reverses the north
`flip_ew`, while stereographic retains it because its pole rotation already
reverses orientation. Corresponding asymmetric registration angles are
reflected between faces, centres and physical radii match, and
`text_mirrored` remains false. These records are geometry metadata; later
furniture owns drawing them.

`MollweideProjection(central_longitude_deg=0, flip_ew=True, radius=1)` is the
coordinate-neutral equal-area all-sky projection. `project_spherical()` maps
generic longitude and latitude directly; `project_geometry()` supports all
canonical spherical geometry forms. Points are vectorized. Curves and grid
components are unwrapped and clipped into separate open pieces at the
longitude seam. Polygon rings are clipped into valid closed pieces on either
side. Per-entity identifiers, labels, names, styles, and compound-ring
metadata are duplicated for every split piece. The projection owns no
astronomical frame conversion, chart boundary, renderer, or style behavior.

`AllSkyChart()` owns the complete-sphere Galactic Mollweide view. Its
projected boundary is the exact 2:1 Mollweide ellipse, and its chart context
reports 360 by 180 degrees and the full `4 pi` steradians. During canonical
`CelestialSphere.draw_chart()` execution it applies
`horizontal_to_galactic()` before projection, retains catalogue centers
without horizon rejection, and clips all artists and optional disjoint
constellation-mask openings at the ellipse. Ordinary drawing selects a
labeled Galactic grid by default; equatorial and ecliptic overlays remain
available explicitly.

`chart_view_defaults(family, group=False)` returns the corresponding frozen
`ChartViewDefaults` policy from `CHART_VIEW_DEFAULTS`:

| Ordinary view | Default framing |
|---|---|
| binocular | fixed 6.5-degree diameter |
| regional single | automatic from constellation geometry |
| regional group | automatic from an arbitrary set, or a packaged preset |
| planisphere | visible observer hemisphere |
| all_sky | complete Galactic sphere in a Mollweide ellipse |
| circumpolar | south pole through declination -69.75 degrees |

Every policy except `all_sky` uses stereographic projection and the horizontal
coordinate frame. `all_sky` uses Mollweide and Galactic coordinates. Every
policy uses position angle 0 degrees and no mask. Explicit arguments to
`get_chart_view()` take precedence. The advanced
`ChartRequest` API continues to require an explicit circumpolar declination
limit; the default is an ordinary-interface convenience rather than a change
to that contract.

`draw_chart_view(view, destination, ...)` completes the ordinary workflow and
returns one `ChartExportResult`. Direct choices are `style`, `mode`, `grids`,
`grid_labels`, `furniture`, `title`, and `language`. Advanced callers may also
supply a `DetailPolicy`, `DetailOverrides`, and `ChartStyleOverrides` without
leaving the ordinary facade. Grid names accept `altaz`, `equatorial`,
`ecliptic`, or `galactic`, with their `_grid` semantic names also accepted.
The view's spatial content is retained, the load profile validates explicit
detail ceilings, and the destination is saved exactly once.

```python
result = draw_chart_view(
    view,
    "output/m57.png",
    style="atlas",
    mode="print",
    grids=("equatorial",),
    grid_labels=("equatorial",),
    title="M57",
)
print(result.output)
```

Command-line examples add the complete common contract with
`add_chart_cli_arguments(parser, default_output=...)`. The resulting namespace
is passed to `draw_chart_view_from_arguments(view, arguments, stem=...)`, which
returns one `ChartExportResult` per selected product. A family may pass
`product_details` keyed by exact `ChartProduct` values or by style name when
an application needs to replace the packaged family policy, and may construct
localized furniture with `chart_cli_furniture()`; these remain declarative
inputs to `draw_chart_view()` rather than a second rendering path.
The ordinary CLI enables the labeled equatorial grid by default and accepts
`--no-equatorial-grid` to omit it. Equatorial right ascension is labeled as
`hh:mm`; declination and the other coordinate systems use degrees.

Constellation-family adapters may add the shared subject contract with
`add_constellation_subject_arguments(...)`. It accepts mutually exclusive
`--constellations IAU,...` and `--group ALIAS` forms.
`chart_constellation_subject(arguments)` returns immutable typed options whose
`view_arguments()` pass directly to `get_chart_view()`. Arbitrary sets use the
existing resolver and automatic spherical regional framing; packaged groups
remain optional aliases and no example owns IAU parsing or group geometry.
The subject may be optional for a family such as the planisphere by calling
`chart_constellation_subject(arguments, required=False)`.
Every canonical example that has a constellation subject uses this adapter,
including the one-element regional default. There is no separate singular
`--constellation` parsing path.

A masked stereographic planisphere accepts a possibly disjoint constellation
set. Its full-sky mask selects official boundary geometry before projection,
discards regions with no sampled vertex at or above the chart horizon, and
retains complete partially visible polygons. The renderer then clips those
separate mask openings at the chart-owned horizon, so an all-invisible set
correctly shades the complete visible hemisphere. Regional masks do not apply
observer-horizon rejection.

```python
sky = generate_celestial_sphere()
observer = Observer(location="La Ligua", time="2026-08-15 22:00")
view = get_chart_view(
    sky,
    observer,
    family="binocular",
    target="M57",
    field_diameter_deg=6.5,
)
```

```python
result = generate_chart_request(
    ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua",
            time="2026-08-15 22:00",
        ),
        family="binocular",
        subject=ChartSubjectRequest(target="Centaurus A"),
        product=ChartProductOptions(output="output/centaurus-a.png"),
    )
)
print(result.outputs)
```

## 8.1 Packaged configuration validation

`wenu.configuration.load_packaged_defaults()` reads and strictly validates a
fresh copy of the installed version-1 `defaults.toml`. The related
`parse_configuration()` and `validate_configuration()` functions validate
complete documents and mappings, and raise `ConfigurationError` with the full
configuration path on failure. `translate_style_mode_defaults()` constructs
existing immutable atlas/cartoon style, print/presentation mode, and palette
objects with exact current parity. `translate_geometry_detail_defaults()`
does the same for family view defaults, neutral/content/cartoon/adaptive
detail, canonical family ceilings, and binocular fixed detail and stellar
sizing. `translate_furniture_product_export_defaults()` completes the same
translation boundary for references, poles, footer/context options, family
legend plans, magnitude-legend appearance, product selection, and export
options. `packaged_style_mode_defaults()` caches the validated style/mode
translation, and canonical named composition now consumes its semantic bases,
modes, palettes, and cartoon label-transform values. Explicit style and mode
objects remain unchanged.

`packaged_geometry_detail_defaults()` likewise caches the validated family
view and detail translation. `chart_view_defaults()` returns its packaged
family contracts. Named atlas composition uses the corresponding all-sky,
planisphere, regional, or circumpolar adaptive policy; named cartoon
composition uses its restrained bright-content policy. Explicit frame
arguments, `DetailPolicy` values, and `DetailOverrides` continue to take
precedence.

`packaged_furniture_product_export_defaults()` caches the remaining validated
translation. Ordinary drawing uses its neutral references, poles, and footer
when no explicit furniture is supplied; legends and context remain opt-in.
Family legend plans, magnitude-legend appearance and footer coordinates
resolve through the same authority. Shared product parser
defaults and generated filename extensions use its product values. Canonical
export starts with its bounding-box, metadata and padding settings, then
retains the existing derived mode DPI/transparency, circular transparency,
and canvas face color. Explicit furniture, CLI product selections, output
paths, and chart export options still win.

Ordinary `draw_chart_view()` and `ChartRequest` omission now also resolves
style, mode, language, and title through `[products.default]`. Direct typed
constructors retain their historical default arguments for source
compatibility; canonical named composition, view, drawing, furniture,
product, and export gateways no longer consult those literals as runtime
authority.

`load_configuration(path=None)` returns a fresh complete effective mapping.
With no path it is equivalent to the packaged authority; with a path it loads
a partial user TOML document, recursively merges only documented keys over a
fresh packaged mapping, and validates the complete result.
`parse_configuration_overlay()`, `validate_configuration_overlay()`, and
`merge_configuration_overlay()` expose the same strict boundary for callers
that already own text or mappings. Every overlay must declare
`schema_version = 1`.

`load_configuration_defaults(path=None)` and
`translate_configuration_defaults()` return one frozen
`ConfigurationDefaults` aggregate containing the existing style/mode,
geometry/detail, and furniture/product/export translations. These functions
do not install global process state. Ordinary runtime and CLI activation
remains the following Milestone 46D.5 slice.

The ordinary runtime accepts that aggregate directly:

```python
from wenu import get_chart_view
from wenu.configuration import load_configuration_defaults

configuration = load_configuration_defaults("my-wenu.toml")
view = get_chart_view(
    sky,
    observer,
    family="binocular",
    target="M13",
    configuration=configuration,
)
```

`draw_chart_view()` automatically carries `view.configuration` through named
style/mode composition, detail, footer and magnitude-legend appearance, and
export. Explicit view and drawing arguments retain final precedence. The six
canonical examples expose the same path as `--config PATH`; the adapter loads
and validates it before generating a maximal sphere. Omitted `--style`,
`--mode`, and `--all-products` values resolve from the effective TOML, while
arguments explicitly present on the command line override it.

## 9. Installed unified chart command

Installing Wenu provides one command over the ordinary Python facade:

```text
wenu_chart all-sky ...
wenu_chart planisphere ...
wenu_chart regional --constellations Cen,Cru,Mus ...
wenu_chart circumpolar ...
wenu_chart binocular --target M13 ...
wenu_chart defaults
```

Every chart subcommand accepts the shared product, content, grid, horizon,
furniture, appearance, output, observer, title, language, and `--config`
controls. Observer controls use the unambiguous `--observer-location`,
`--observer-time`, `--observer-latitude`, `--observer-longitude`,
`--observer-height`, and `--observer-timezone` names because `--location`
already selects location context furniture. Ephemeris and data-directory
overrides are also available.

The command loads and translates one effective configuration, constructs an
`Observer`, calls `generate_celestial_sphere()`, passes the result to
`get_chart_view()`, and finally calls `draw_chart_view_from_arguments()`.
It prints the resulting output paths and closes the observer in a `finally`
boundary. `src/wenu/cli/chart.py` does not import or execute example scripts.
The examples and installed command are separate adapters over the same
library interfaces.

`wenu_chart defaults` writes the installed commented `defaults.toml` to
standard output without loading an observer or astronomical catalogues.
`wenu_chart defaults --write PATH` copies those exact UTF-8 bytes to an
editable file and prints its path. The destination parent must exist; an
existing file is deterministically replaced. This deliberately preserves
comments and formatting from the authority rather than serializing translated
Python contracts.

Configuration line styles use the complete public vocabulary `solid`,
`dashed`, `dotted`, `dash_dot`, and `none`. Named publication, presentation,
outreach, location, and observing profiles are separate version-1 TOML files
passed through `--config`. One invocation accepts one overlay. Version 1 has
no profile inheritance or multi-file composition; that feature remains
deferred until ordinary single-file use demonstrates a concrete requirement.

The canonical examples and `wenu_chart` are independently maintained
front-end adapters over this same interface. Their parity contract resolves
omitted geometry from the same effective configuration before comparing the
observer-bound view request; syntactic differences such as an example
spelling out `projection="stereographic"` while the command accepts the
configured default are therefore not treated as behavioral differences.

The installed-command drawing contract is likewise resolved by
`draw_chart_view_from_arguments()`, not by a command-specific translation.
Its tested vocabulary includes content detail, grids and labels, horizon
reference and mask, furniture and legends, post-mode appearance, product,
title, language, and destination. Selecting `--all-products` yields the
canonical atlas/cartoon by print/presentation matrix in deterministic order.

Each `wenu_chart` invocation loads and translates a fresh effective document;
it does not install active configuration globally. Partial overlays therefore
affect only their named values, a later command may safely use another overlay
or packaged defaults, and a reused maximal sphere acquires no configuration
state. Explicit command observer, subject, geometry, product, title, language,
and output arguments retain final precedence. Invalid documents raise
`ConfigurationError` before observer or astronomical construction.

## 10. Package imports

Internal implementation imports use responsibility-based packages:

```python
from wenu.geometry.spherical import SphericalCurves, SphericalGrid
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.charts.composition import ChartComposition, compose_chart
```

Pre-v0.4 singular top-level geometry modules and the old `wenu.renderers`,
`wenu.regional`, and `wenu.styles` packages do not exist.

## 11. Extension procedure

- Add a chart type only when geometry or framing differs.
- Add a style by composing visual components; do not add projection or export
  behavior to it.
- Add an output mode by implementing `resolve(context)` and preserving chart
  geometry and content.
- Add a detail policy by returning `ResolvedDetail`.
- Extend legends from resolved content and semantic render metadata, never by
  querying catalogues directly.

Every extension must continue through `CelestialSphere.draw_chart()`.

## Polar common-year calendar model

`CommonYearCalendarRequest` resolves the neutral civil-date geometry used by
future polar-planisphere furniture. Its defaults calibrate La Ligua/Papudo
with longitude `-71.230289`, standard UTC offset `-4`, and common reference
year 2026. The returned `CommonYearCalendarScale` contains 365 frozen day
records, 12 true month arcs, 12 month-boundary records, semantic month label
keys, and numeric labels only for days 5, 10, 15, 20, 25, and 30 when that
date exists. It deliberately excludes leap days, daylight-saving rules,
localized month text, face handedness, and renderer policy.

`PolarCalendarFurnitureRequest.resolve(pair)` converts that neutral scale into
one matched `PolarCalendarPairFurniture`. Each face contains 365 tick segments
in physical millimetres, 12 strengthened month boundaries, 71 numeric day
labels, and 12 semantic month-label anchors. The default central star-disk
radius is 80 percent of the physical disk radius; tick lengths and day/month
label radii are separately configurable fractions. An explicit paired
`calendar_radius_mm` overrides the fractional star-disk default and is rejected
if it leaves insufficient room. All calendar geometry stays between that
reserved radius and the physical edge. Text rotations encode
typographic bases outward and never mirror glyphs. A date direction is exactly
opposite the projected direction of its midnight RA, deriving reversed face
handedness from the selected equidistant or stereographic projection.

## Polar classroom-disk content

`PolarPlanisphereDetailPolicy` is the packaged atlas-detail authority for a
`polar_planisphere` composition. Its canonical configuration selects stars
through magnitude 5.5 and enables exactly `stars`, `constellation_lines`,
`constellation_labels`, `milky_way`, and `magellanic_clouds`.
`constellation_star_mode="none"`
ensures that faint constellation vertices do not bypass the stellar ceiling.
Constellation boundaries, coordinate grids, galaxies, clusters, planetary
nebulae, and supernova remnants remain disabled. Because the policy ignores
face context and output-mode scaling, north and south
compositions produce identical render-local catalogue geometry options before
their different projections clip the common sky.

## Polar physical-print appearance

For named atlas-print composition, `polar_planisphere_chart_style()` adapts the
resolved atlas style using the packaged `PolarPlanisphereStylePalette`. The
initial values use white paper, provisional configurable blue stars, ordinary
circular markers at reduced area, pale translucent Milky Way fill, zero Milky
Way edge and contour realization, subordinate constellation figures and
labels, a restrained circular boundary, and no legend. The adapter does not
change detail, chart geometry, projection, output scale, or other chart
families. Atlas presentation retains its established screen palette.

Run `python tools/render_48e2_polar_preview.py` for the canonical equidistant
north/south diagnostic. The tool may also render `--projection stereographic`
for comparison. It writes only below `output/` and saves each face once.

For Milestone 48E.3, `PolarPlanispherePairRequest` defaults to symmetric
limits of +20 and -20 degrees. A default stereographic pair selects its
unmirrored south-face convention automatically; an explicit `south_flip_ew`
still overrides it. Polar reference composition opts into the ordinary
equatorial-grid layer, realized as meridians at 0, 90, 180, and 270 degrees.
Short declination ticks every 20 degrees are projected disk furniture, not
spherical parallels. After conversion to equatorial coordinates, polar points,
curves, and grids are clipped to the face's declination cap before projection.
This prevents exterior constellation endpoints from becoming false planar
chords in the equidistant view. The established reference sky
owns the equator, ecliptic, Galactic plane, ecliptic cardinal points, and pole
annotations, and converts its canonical AltAz geometry back to ICRS before
the polar projection. Both physical poles may be requested normally; the same
declination-cap preparation suppresses out-of-face markers and labels. Pole
selection also accepts explicit `north` and
`south` values. The polar physical palette owns a
single neutral reference color and a configurable principal-label size. The
diagnostic uses the canonical footer, whose application version comes from
installed package metadata. `PolarCalendarTick.labeled_day` allows stronger
stroke weight without changing tick length.

Automatic equator, ecliptic, and Galactic-plane labels share a render-local
collision registry. Reservations use normalized chart coordinates so the
policy is independent of projection scale and output size. Later labels search
their visible curve for a separated interior candidate; explicit anchors are
never displaced.

For `polar_planisphere` only, automatic and explicit principal-reference
labels choose between the two equivalent tangent directions by requiring the
typographic down normal to point toward projected disk center. Other chart
families retain the ordinary page-readable tangent convention.

Polar constellation labels use the corresponding circular tangent at their
point anchor and the same inward-down convention. The renderer resolves their
rotation callback per projected point without changing non-polar label style.
Polar ecliptic keypoints use small `x` symbols, celestial poles use `+`, and
ecliptic and Galactic poles use `x`.

## 12. Compatibility and deprecation

The legacy `cartoon_output_mode()` and `compose_cartoon_chart()` wrappers
remain functional but emit `DeprecationWarning`. Their replacements and the
v0.5 compatibility policy are recorded in `deprecations_v0.5.md`.

## 13. User documentation and reference image

The v0.7 user guide begins at `docs/user_guide/index.md` and contains one page
for each canonical family plus a shared styles, modes, detail, and furniture
reference and the unified-command/configuration profile guide.
`docs/user_guide.md` remains only as a compatibility link.

The README planisphere is the sole checked-in generated chart. Its generating
script, exact arguments, source commit, dimensions, SHA-256 checksum,
destination, and visual approval are recorded in
`docs/user_guide/planisphere.md`. All other generated products remain below
`output/` and outside version control.

For the Milestone 46D.8 visual handoff, run:

```bash
python tools/render_46d8_visual_matrix.py
```

The runner invokes the real command module once per product and writes 18
PNGs plus `manifest.json` below `output/46d8-visual-matrix/`. Use `--list` to
inspect the matrix or repeated `--entry NAME` options to rerender selected
products. The review and approval contract is
`docs/developer/visual_acceptance_46d8.md`.

The matrix intentionally assigns one independently visible role to each mask
diagnostic. Outside-mask openings compose by union, so a constellation opening
and the above-horizon opening must not be used together to judge the opacity
or completeness of either one. A horizon reference is claimed only where the
chosen family geometry demonstrates a crossing.

The canonical equatorial formatter emits right ascension as `hh:mm` and signed
declination as `dd:mm`. Regional fields through 60 degrees use 15-degree grid
sampling; circumpolar charts use 30-degree, two-hour meridians. All-sky grids
include zero latitude, place latitude labels on the central longitude, and
label only principal longitudes. These are shared chart policies rather than
example arguments.

### Sgr-Sco-Oph-Ser regional product

`examples/regional_constellation_group.py --constellations Sgr,Sco,Oph,Ser`
selects the
Sagittarius, Scorpius, Ophiuchus, and two-part Serpens region. It does not
enable any non-equatorial grid by default. Every canonical family exposes `--altaz-grid`,
`--equatorial-grid`, `--ecliptic-grid`, and `--galactic-grid` plus the
corresponding label switches, and the ordinary CLI defaults to a labeled
equatorial grid. The AltAz grid has a black semantic base color, realized
as gray `#707070` for both lines and labels in print modes so it remains
subordinate to black stars. It excludes its altitude-zero circle so it does
not duplicate the chart-owned horizon.
`--mask` enables the canonical outside-region mask explicitly.
