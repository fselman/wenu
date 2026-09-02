# Wenu implementation reference

**Architecture version:** 0.9
**Status:** Implemented
**Date:** 2026-08-28

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
`LegendOptions.stellar_reference_magnitude` may restrict that same canonical
legend to one representative integer magnitude without introducing a second
marker-size calculation. `stellar_label_suffix` supplies compact unit text
such as ` mag` while preserving the ordinary full-scale default.
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

- `all_sky.py`;
- `planisphere.py`;
- `regional_constellation_group.py`;
- `regional_constellation.py`;
- `circumpolar.py`;
- `binocular_object.py`.

An installed Wenu distribution provides the `wenu_examples` command. Running
it creates `wenu_examples/` in the current directory and installs these six
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
Resolved chart requests use `ol2` through `ol5` when no Milky Way levels are
supplied. Comparative Mollweide and stereographic renders established that
the D3-Celestial `ol1` geometry itself produces a very broad, nearly
Galactic-latitude-bounded faint envelope; no distant vertex, projection jump,
or clipping closure creates it. `ol1` remains available as explicit catalogue
content, but is not a governed display default. Explicit level requests retain
precedence. The public CLI exposes this nested selection as
`--mw-contour OL1[,OL2,...]|all`; a comma-separated numbered selection draws
exactly those isophotes, while `all` draws all five instead of the governed
default set.
The runtime catalogue is mechanically exported into five independent,
plain-text GeoJSON resources, `milky_way_ol1.geojson` through
`milky_way_ol5.geojson`. Explicit selection sends only rings from the chosen
file into coordinate transformation and projection; the combined pinned
snapshot remains provenance authority.

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

The physical polar-planisphere detail policy loads its reviewed binocular
selection from `data/polar_binocular_targets.json`. Selection remains keyed by
canonical catalogue identifier. Independent per-family display-label
overrides prefer Messier designations or concise common names and may return
`None` to omit one label in a close pair while retaining both objects. Detail
application supplies those overrides through the renderer's generic
`label_formatter` option. The polar atlas-print palette alone raises the
minimum displayed outline diameter to 40 arcminutes and the globular-cluster
floor to 80 arcminutes; it does not filter catalogue objects or alter their
recorded angular dimensions. The polar chart owner applies readable tangent
rotation to enabled deep-sky labels after composition: each text baseline is
perpendicular to the radius and its typographic down faces the disk center.

`ChartRequest` is the immutable input shared by the Python facade and future
command-line adapter. `ChartObserverRequest` defines the actual observing
location and instant; `ChartSubjectRequest` accepts one target, explicit ICRS
coordinate, constellation set, or packaged group; and `ChartFrameRequest`
holds optional framing overrides. Existing `SkyContentSelection`,
`DetailOverrides`, `ChartFurnitureOptions`, and `ChartProductOptions` remain
the corresponding content, detail, furniture, and output contracts.
For regional and binocular views, a named `orientation` is explicit and
mutually exclusive with a literal `position_angle_deg`; zero therefore remains
an ordinary angle. Regional framing may also carry a paired fixed horizontal
altitude/azimuth centre, which requires explicit width and height and remains
independent of constellation content selection.
`ChartContentExclusions` names deep-sky catalogue identifiers that must be
omitted after field selection; it does not mutate loaded catalogue content.
`ChartProductCompositionOptions` optionally assigns a detail policy and
`ChartStyleOverrides` to one exact selected `ChartProduct`. These values are
resolved only at composition time. They cannot carry framing, projection,
masking, or other chart geometry, and duplicate or unselected product entries
are rejected when the request is constructed.
Semantic style overrides may strengthen the ecliptic independently of the
coordinate-grid baseline and enlarge coordinate labels without changing other
products. `ChartStyleOverrides.constellation_label_offsets` carries validated
finite per-label projected displacements into the existing grid-style owner;
it adjusts one render without changing spherical catalogue anchors. The
shared `--sky-color` option follows the same path: it becomes a
`ChartStyleOverrides.sky_color` value and replaces
`ChartCanvasStyle.sky_color` after style and mode resolution. Chart entry
points must not bypass that semantic owner by setting a Matplotlib axes color
directly.
`ChartFurnitureOptions.context` may carry `ChartContextOptions` selecting
chart-center coordinates, the active coordinate-grid description, observer
location, date, and local time. These are declarative booleans rather than
precomputed strings. The request exporter resolves them after both the chart
and sky exist, appends any caller-supplied context lines, and passes the result
through the established immutable legend furniture. The contract is shared by
all four chart families.
`ReferenceAnnotations.ecliptic_keypoints` independently selects `none`,
`markers`, or `labeled`. The reference-furniture owner delegates the four
equinox/solstice positions to `CelestialPoints.add_ecliptic_keypoints()` and
supplies the same barycentric true-ecliptic J2000 frame used by the rendered
ecliptic curve. The FK5 equatorial grid and celestial equator use the matching
J2000 policy, so the March and September markers are genuine intersections. Celestial-reference layers use the same composition-resolved
horizon altitude as ordinary layers: rectangular regional charts resolve to
-90 degrees, so seasonal points are not discarded merely because they are
below the observer's physical horizon. Ordinary projection and viewport
clipping still decide which of the four points are present in a field.
`ecliptic_keypoint_legend` requests a compact lower-left name key. The
reference rendering inspects its already-projected point result and adds only
the canonical points inside the final viewport. Each entry identifies the
symbol's localized zodiac sign before its localized seasonal explanation;
both sets of four names are carried by the immutable annotation request.
`LegendOptions.stellar_reference_range` requests a fixed inclusive integer
magnitude scale while retaining the chart's canonical magnitude-to-area law.
`stellar_background="sky"` resolves the legend frame from the composed canvas
sky and foreground colors and forces an opaque frame; it is not a backend
color literal.
`ChartStyleOverrides.equatorial_reference_linewidth` strengthens only the
celestial-equator reference prepared by canonical furniture. It does not
change the linewidth of the ordinary right-ascension and declination grid;
the existing `ecliptic_linewidth` remains the corresponding semantic control
for ecliptic layers.

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
`local_orientation_at()` resolves the pointwise signed parallactic angle and
the tangent directions toward celestial north and the local zenith. The chart
retains the centre result in `ResolvedChartOrientation`; rendering does not
recompute it and this milestone draws no orientation line.

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

### Celestial-scene dependencies (Milestone 49D.1)

Observer-independent loading is not yet observer-independent spherical
realization. `CelestialSphere.draw_chart()` still resolves one observer and
calls `layer.spherical_geometry(observer, ...)` for every enabled layer.
Hipparcos stars, constellation geometry, catalogue objects, Milky Way
isophotes, and Magellanic Cloud isophotes therefore use their established
observer-bound realization paths during ordinary rendering.

`docs/developer/celestial_scene_dependency_audit_49d1.md` classifies three
scientific realization groups: celestial background, dynamic astronomical
objects, and observer-local geometry. All three must converge in one explicit
spherical product frame before the existing projection and preparation path.
A future planet enters after provider evaluation and
`CoordinateService` transformation as an ordinary semantic sky layer; it
does not enter through the renderer, furniture, command, or a parallel scene
graph.

49D.1 added no runtime type and changed no geometry.

### Minimal layer-realization context (Milestone 49D.2)

`LayerRealizationContext(product_coordinate_spec, observation=None,
evaluation_instant=None, evaluation_time_scale=None,
reference_equinox=None)` is the frozen scientific input available to a layer
before projection. Evaluation instant and time scale must be supplied together.
The value contains no projection, viewport, renderer, style, furniture, output,
or cache policy.

`SkyLayer.realize(context, observer, **geometry_options)` is a concrete
compatibility adapter that delegates to the layer's established
`spherical_geometry(observer, **geometry_options)`. Supplying no
`realization_context` to `CelestialSphere.draw_chart()` calls
`spherical_geometry()` directly, preserving the pre-49D.2 route exactly.
Supplying a typed context selects `realize()`; an untyped value is rejected.

No ordinary chart facade supplies this context yet. The only specialized
dynamic layer is test-local: it evaluates a deterministic structural
`PositionProvider`, transforms its native point once through
`CoordinateService`, and then uses the existing projection and renderer path.
Caching, real ephemeris selection, installed moving-object layers, public
request exposure, and the first planet remain later milestones.

Future Sun, Moon, and planet layers must attach renderer-neutral
`SemanticLayerIdentity` before projection and then use the same canonical
projection, preparation, Matplotlib rendering, and single export path as every
other layer. For SVG, the downstream annotator serializes the reserved
`solar-system/sun`, `solar-system/moon`, and `solar-system/planets`
hierarchy; it does not evaluate ephemerides, transform positions, infer object
identity, or add a post-export overlay.

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

`CoordinateService.transform_observer_geometry()` is the single AltAz-to-celestial service entry point used by all-sky, polar, horizon, and reference-furniture consumers. It preserves geometry kind, topology, semantic arrays, and metadata while recording the AltAz source and requested celestial result. The former chart-owned `coordinate_frames.py` adapters are removed in 49C.3.

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
`CelestialSphere.draw_chart()` execution it requests a Galactic transformation from `CoordinateService` before projection, retains catalogue centers
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
regional and binocular policies explicitly use celestial-north-up; the other
families use literal position angle 0 degrees. Every policy uses no mask.
Explicit arguments to
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
`--declination-step DEGREES` replaces only the equatorial parallel interval
through `DetailOverrides` and canonical request-grid configuration. It leaves
right-ascension meridian density and every non-equatorial grid unchanged;
omission preserves the established family policy.

Constellation-family adapters may add the shared subject contract with
`add_constellation_subject_arguments(...)`. It accepts mutually exclusive
`--constellations IAU,...` and `--group ALIAS` forms.
The underlying public `parse_constellation_list()` adapter is available to
specialized tools that need the same comma-separated IAU normalization but
do not support packaged groups; they must not implement a second list parser.
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

### Proposed ephemeris-provider boundary (Milestone 49E.1)

The current `positions.py::PositionProvider.position(instant)` returns native
`SphericalPoints` and remains unchanged. It is not sufficient as the sole
solar-system ephemeris boundary because a raw provider product must retain
Cartesian position and velocity, target, centre, frame, evaluation instant/time
scale, units, kernel identity, coverage, and provenance.

The proposed design separates an ephemeris state source from a solar-system
direction realizer. The realizer owns retarded emission-time evaluation and the
declared light-time/apparent-place correction policy. It creates typed
spherical geometry only after observer-relative direction and position status
are defined. `CoordinateService` then owns the final coordinate representation
transformation. 49E.1 installs no runtime classes, provider, kernel adapter, or
moving-object layer.

The accepted next-step contract requires six-component states and a resolved
resource identity containing provider/model, filename, SHA-256 content digest,
coverage, and provenance. SHA-256 is calculated once per resolved kernel
resource. 49E.2 will atomically remove the unreleased
`PositionStatus.TOPOCENTRIC` member and migrate its single helper default and
two focused tests, representing topocentricity through origin instead. The
first later vertical slice is Venus, followed by the Moon.

### Minimal ephemeris runtime contracts (Milestone 49E.2)

`src/wenu/ephemeris.py` owns frozen `EphemerisResourceIdentity`,
`EphemerisStateRequest`, and `EphemerisState` values and the structural
`EphemerisStateSource` protocol. A state requires typed request/resource,
three finite position components, three finite velocity components, explicit
units, and optional provider-native identifiers and provenance. The resource
identity validates a 64-hex SHA-256 and explicit coverage scale but performs no
file I/O.

`PositionStatus.TOPOCENTRIC` is removed. `observer_altaz_spec()` retains
`origin="observer"` and requires an explicit `position_status`. Astropy/Skyfield
observer-transformed celestial products declare `APPARENT`; native horizon,
cardinal/zenith, polar-horizon, and AltAz-grid products declare `GEOMETRIC`. The deterministic source remains
in `tests/test_ephemeris.py`; no real provider, kernel adapter, direction
realizer, or moving-body layer is installed.

### Borrowed Skyfield ephemeris adapter (Milestone 49E.3)

`src/wenu/skyfield_ephemeris.py::SkyfieldEphemerisStateSource` borrows the
already-open `Observer.ephemeris` and `Observer.timescale`. Its factory
calculates SHA-256 once, infers a conventional DE model separately from the BSP
filename, and records the common SPK-segment coverage interval in TDB.
`state()` supports explicit geometric ICRF target-minus-centre states and
returns AU, AU/day, NAIF identifiers, and immutable resource provenance.

The adapter has no `close()`: `Observer` owns resource lifetime. It performs
no kernel load or network operation. `tools/validate_49e3_skyfield_adapter.py`
refuses to download a missing kernel and compares the six-component Venus/SSB
state with direct Skyfield evaluation. Direction realization and any Venus
layer remain later milestones.

### Solar-System direction-realizer audit (Milestone 49E.4)

`docs/developer/solar_system_direction_realizer_49e4.md` defines the proposed
handoff from geometric Cartesian states to observer-relative directions. The
astrometric stage owns the observer state at reception, iterative target state
at retarded emission time, one-way light time, distance, convergence policy,
and immutable resource provenance. A subsequent apparent stage adds declared
aberration and gravitational deflection.

49E.4 installs no runtime class. The proposed 49E.5 result surrounds one
ICRS-oriented `SphericalPoints` value with distance and timing metadata before
`CoordinateService` transforms it into the product frame. Neither reception
nor emission instant is stored as a position reference epoch or equinox.

### Astrometric direction runtime (Milestone 49E.5)

`src/wenu/solar_system_directions.py` owns frozen
`ObserverBarycentricState`, `AstrometricDirectionRequest`, and
`AstrometricDirection`, plus `AstrometricDirectionRealizer`. The realizer
evaluates the observer once at reception, requests ICRF/AU target states at
iterated emission instants, and returns observer-origin ICRS spherical geometry
with only `one-way-light-time` declared as a correction.

`src/wenu/skyfield_ephemeris.py::skyfield_observer_barycentric_state()`
borrows `Observer.skyfield` and accepts only a state source using the same open
kernel. `tools/validate_49e5_astrometric_direction.py` is the explicit
no-download Venus comparison with direct Skyfield `observe()`. No installed
layer consumes the result in 49E.5.

### Apparent direction runtime (Milestone 49E.6)

`src/wenu/solar_system_directions.py` owns frozen
`ApparentCorrectionPolicy` and `ApparentDirection`. The accepted astrometric
result also retains relative target-minus-observer velocity in AU/day.

`src/wenu/skyfield_ephemeris.py::SkyfieldApparentDirectionRealizer` rebuilds a
Skyfield astrometric value from that retained result and calls only
`apparent()`. It verifies kernel, resource, observer state, and reception
instant identity; it does not call `observe()` or repeat light-time iteration.
The result is observer-origin apparent ICRS `SphericalPoints` with explicit
deflection, aberration, and resource provenance. No production layer consumes
it in 49E.6.

### Ordinary realization-context handoff (Milestone 49I.1A)

`charts/request_realization.py::chart_request_realization_context(request,
observer)` returns the immutable pre-projection `LayerRealizationContext` for
one matching ordinary request and observer. Horizontal products receive an
observer-local apparent AltAz specification; all-sky receives an
observer-origin apparent Galactic specification. The reference equinox remains
separate from both product specifications.

`export_prepared_chart()` constructs the context once and forwards it through
the shared composition/export boundary and chart facade. Existing layers
continue through `SkyLayer.realize()` to their unchanged
`spherical_geometry()` method. Direct low-level calls may still omit the
context. 49I.1A installs no moving-body layer.

Fernando accepted this output-neutral handoff on 2026-08-30 after 166 focused,
1,859 routine, and 1,890 complete tests passed. The complete suite verifies
that observer instants supplied as `utc_datetime`, `t_astropy`, or AltAz
`obstime` normalize through the same scientific context boundary.

### First drawable Venus layer (Milestone 49I.1B)

`sky/venus.py::VenusLayer.realize()` is the first production consumer of
`LayerRealizationContext`. `SkyContentSelection.planets` and CLI
`--planet venus` own opt-in selection. The layer returns ordinary
`SphericalPoints` in the product specification; style owns its symbolic marker
and label, and the existing renderer/exporter owns all output formats.

Fernando scientifically and visually accepted the slice on 2026-08-30. The
installed-DE440 regional Venus agreed with Stellarium at the declared La Ligua
instant, and PNG, PDF, and semantic SVG looked the same. Acceptance evidence is
148 implementation-review tests, 35 focused post-correction tests, and all
1,898 tests in 82.01 seconds.

### Proposed Moon and shared-body boundary (Milestone 49I.2)

`moon_shared_body_pipeline_audit_49i2.md` identifies the invariant path from a
typed state source through observer-relative astrometric and apparent
direction, one product-frame transformation, and ordinary rendering/export.
It keeps provider-specific orbit evaluation and body-specific physical
appearance behind separate contracts. No shared runtime layer or Moon is
installed by the audit.

### Numerical Moon-direction validation (Milestone 49I.2A)

`tools/validate_49i2a_moon_direction.py` composes the existing state source,
observer-state adapter, astrometric realizer, and apparent realizer for
`moon`/NAIF 301. It compares against direct Skyfield and reports parallax and
observer-height evidence. `tests/test_moon_direction_validation.py` supplies
the deterministic provider-neutral contract proof. Neither owns chart content
or production geometry.

### Shared Solar-System point layer (Milestone 49I.2B)

`sky/solar_system_points.py` defines frozen `SolarSystemPointDescriptor` body
data and `SolarSystemPointLayer` orchestration from typed realization context
through one product-frame transformation. `sky/venus.py::VenusLayer` is the
first thin specialization. The shared layer attaches stable point identity and
provenance; projection, visibility, appearance, semantic scene placement,
rendering, and export remain in their established owners. 49I.2B itself
installed no Moon chart layer; 49I.2C below adds the first.

### First drawable Moon point (Milestone 49I.2C)

`sky/moon.py` defines frozen `MOON_POINT` data and the thin
`MoonLayer(SolarSystemPointLayer)` specialization. Public `--moon` and
`--planet venus` controls adapt into
`SkyContentSelection.solar_system_objects`; detail application keeps both
layers default-off and forwards exact selection. The maximal sphere registers
Moon once, style owns its provisional hollow marker and label, and semantic
identity owns `sky/solar_system/natural_satellites/moon`.


### Accepted Solar-System track contract (Milestone 49I.2D)

`solar_system_track_audit_49i2d.md` proposes one renderer-neutral request
containing body identity, start instant, sample cadence, tick cadence, and tick
count. Body and observer states are reevaluated at every sample instant. Their
apparent ICRS-oriented directions are assembled into one `SphericalCurves`
record and transformed into the static chart's single product frame before the
ordinary projection path.

The current scalar direction realizer remains the correctness path; later
batching is only an optimization. Existing curve transformation, projection,
clipping, renderer, and export contracts require no parallel implementation.
Exact tick anchors and per-sample instants are scientific metadata. Visible
perpendicular ticks, line appearance, start glyph, and date-label appearance
remain projected/style concerns. Fernando accepted this documentation-only
boundary after all 1,919 tests passed. The audit installs no runtime API or
output.

### Scientific Solar-System track curve (Milestone 49I.2D.1)

`sky/solar_system_tracks.py` defines frozen
`SolarSystemTrackRequest` and `SolarSystemTrackResult` contracts plus
`SolarSystemTrackRealizer.curve()`. The request normalizes one start instant,
positive sample/tick steps in days, and a positive tick count. Its sample
sequence includes both endpoints and every exact major-time anchor.

The realizer borrows one source, reevaluates the observer and accepted scalar
direction chain per vertex, retains every `ApparentDirection`, assembles one
open native `SphericalCurves`, and calls `CoordinateService.transform()`
once for the fixed product frame. The result retains sample instants, exact tick
indices, resource identity, and scalar evidence. No installed layer or public
chart request consumes it in 49I.2D.1. Fernando accepted the scientific
contract and installed-DE440 validation after all 1,929 tests passed.

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
The canonical footer interprets its configured coordinates as outer limits,
anchors left and right credit text to the chart axes when those axes are more
inset, and reserves at most a typography-sized strip below the chart. Tight
export therefore grows only downward for credits instead of exposing unused
canvas on the top and sides.

Generated reference labels resolve through `data/translations.json` and
`wenu.translations.translate_label()`. The shared command-line furniture uses
the selected product language before applying any explicit caller overrides;
unknown labels pass through unchanged, while unsupported language identifiers
are rejected.

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

`PolarPageFurnitureRequest(source_revision=...)` resolves the paired disk into
one `PolarPagePairFurniture` expressed entirely in physical A4 paper
coordinates. The default page is 210 by 297 mm with a 5 mm safe margin and the
195 mm disk centred at `(105, 148.5)` mm. Each face carries a 1 mm centre-punch
radius, the reflected registration metadata positioned in millimetres, a
triangle/circle/square glyph sequence whose triangle is the unambiguous
orientation cue, and an exact 50 mm scale ruler with 10 mm major intervals.
The south and north pages share one request and remain individually readable;
their completed text is never mirrored.

The page request also owns local semantic information for the classroom
edition: `SOUTH / SUR` or `NORTH / NORTE`, La Ligua/Papudo identity, La Ligua
coordinates, UTC-4 standard time, the explicit daylight-saving disclaimer,
projection and declination coverage, magnitude limit 5.0, disk diameter,
actual-size printing, minimal cutting/gluing/face-use instructions, product
identifier, and source revision. `source_revision` is mandatory at resolution
so a printable page cannot silently omit provenance. This object contains no
artists or saving code; renderer realization and the single final save per
page belong to the following export milestone.

`draw_polar_page_furniture(...)` is the single Matplotlib realization of one
resolved calendar face and page face. It runs only as additional furniture
after the canonical sky, reference, legend, and footer stages. The chart axes
are expanded from the stellar aperture to the physical date-ring radius; daily
ticks, Spanish month names, and all paper marks are then drawn from immutable
millimetre records. A transparent full-page axes uses coordinates from
`(0, 0)` to `(210, 297)` mm, while `polar_disk_axes_bounds(face)` locates the
195 mm outer disk exactly on the physical A4 figure. The function saves
nothing and returns an inspectable `PolarFacePageRendering` artist record.

`PolarMagnitudeScaleRequest` resolves the polar-only classroom scale at the
packaged magnitude-0.5 bright cutoff and magnitude-5.0 catalogue ceiling. The
four five-point intervals (`-1.5..-1.0` through `0.0..0.5`) and five circular
intervals (`0.5..1.0` through `4.0..5.0`) use interval midpoints as samples of
`configured_stellar_symbol_sizes(...)`. The resulting immutable scale object
is passed unchanged to both `PolarPageFurnitureRequest.resolve(...)` and
`PolarPouchFurnitureRequest.resolve(...)`; their placement records are in
millimetres. `draw_polar_magnitude_scale(...)` realizes those stored point
areas without introducing an independent legend sizing law.

`export_polar_planisphere_pages(...)` accepts one resolved pair, calendar, and
page-furniture pair plus explicit north and south destinations. Each face uses
an A4 `PrintMode`, the accepted polar composition, and a non-tight opaque
`ExportOptions`; `bbox_inches=None` is essential because tight bounding boxes
would destroy actual-size page dimensions. It calls
`PolarPlanisphereChart.export()` exactly once per face. That method delegates
to `export_composed_chart()`, whose optional callable additional-furniture
stage now runs immediately before its existing sole `save()`. The returned
`PolarPagePairExportResult` retains both ordinary `ChartExportResult` values,
including the new `additional_furniture_rendering` record.

`tools/render_48e4_polar_pages.py --source-revision REVISION` is the review
entry point. It writes `polar-planisphere-south-a4.pdf`,
`polar-planisphere-north-a4.pdf`, and `manifest.json`; source revision is
required rather than guessed from a working directory. The PDFs contain A4
media boxes, one 195 mm disk each, embedded product/source metadata, and no
implicit crop-to-content operation.

## Polar folded-pouch furniture

`PolarHorizonOverlayRequest.resolve(pair, pages, observer)` retains only
astronomical altitude-zero geometry: paired clipped horizon segments, the
shared observer latitude, physical disk scale, and the face-specific meridian
horizon reference. It deliberately exposes no E, W, N, or S label anchors.
Those printed letters tell the user how to hold the fixed pouch; they are not
derived from the rotating disk's current projected orientation.

`PolarPouchFurnitureRequest.resolve(overlays)` maps that immutable horizon pair
onto one 210 by 297 mm folded construction. With the 195 mm classroom disk and
5 mm safe margin, the fold is at 97 mm and the disk centre is `(105, 194.5)`
mm, so the complete disk lies between the fold and the upper safe margin. The
fold therefore supplies vertical registration when the disk rests on it.

Each resolved face owns three identical annular date windows. Every window
spans 37.5 degrees, adjacent windows are separated by 5 degrees, and the full
group is centred on the bottom of the disk. The hour furniture covers 19:00
through 05:00 at one-hour/15-degree intervals. On the south face it runs from
right to left; on the north face it runs from left to right. Bold numerals lie
just inside the hour circle with upright tangent bases, and each short radial
tick begins on that circle and extends outward. The windows run from 0.83 to
0.95 disk radius: they expose calendar ticks, day numbers, and month names
while retaining a continuous outer strip over the disk's white margin.

Fixed paper labels are E-S-W, two bold `HORIZONTE` labels, and `Muchos cielos,
un firmamento` on the south face, and bold W-N-E plus two bold `HORIZONTE`
labels on the north face. Cardinal labels share a seven-millimetre vertical
clearance below the local resolved horizon. Horizon text positions and
rotations follow the resolved curve and remain just below it on retained
paper. Geographic letters remain manual pouch furniture, not rotating-disk
sky anchors.

`PolarPouchSheetRequest.resolve(pouches)` imposes both accepted faces on one
portrait A4 sheet. A one-millimetre central spine separates fold lines at 148
and 149 mm. The south face occupies the upper 148 mm panel; the north face is
rotated 180 degrees into the lower panel. Each panel is clipped without
recalculating face geometry. The 195 mm disk therefore protrudes 47 mm from
the open edge after folding and is inserted after the side seams are glued.

`PolarPouchFaceFurniture.sky_window_boundary_mm` first joins all resolved
horizon segments from E to W, then closes them with the physical upper disk
arc. This is the complete
cuttable visible-sky window path; the renderer never infers which side of the
horizon is visible. The original horizon segments remain separately available
so the astronomical horizon can be printed more strongly than the remaining
cut arc.

`draw_polar_pouch_face(face, figure=...)` realizes one resolved face on an A4
axes expressed directly in millimetres. All cut, fold, hour, label, and glue
marks are black for inspection through paper. The function returns
`PolarPouchFaceRendering`, calculates no astronomy or furniture positions, and
saves nothing.

`draw_polar_pouch_sheet(sheet, pouches, figure=...)` applies the two resolved
affine placements to those same vector artists on one axes. It clips each face
to its 148 mm panel and preserves the distinct fold lines around the spine.
North text artists receive the additional 180-degree glyph rotation required
to read upright after the lower panel is folded; rotating coordinates alone
does not rotate Matplotlib text glyphs.
`export_polar_pouch_sheet(...)` owns the one-save actual-size A4 boundary.

`export_polar_pouch_pages(...)` creates one 210 by 297 mm figure per face,
calls the pouch renderer once, and delegates exactly one final save per output
to the established `ExportOptions` boundary with `bbox_inches=None`. Explicit
source revision is mandatory and embedded in PDF metadata. The review tool
`tools/render_48g2_polar_pouch.py` writes one clean single-sheet fabrication
PDF, one faded canonical-disk PNG diagnostic, and a checksum manifest. The
diagnostic composer registers and clips both disks at their imposed panel
positions and rotates 15 August to the 21-hour mark on both faces; it does not
affect the fabrication PDF. Printing is one-sided at
100 percent / Actual Size. The review command's `--title` option supplies the
south title before furniture resolution; its default is `Muchos cielos, un
firmamento`.

Diagnostic center registration is an explicit two-step mapping. The canonical
disk-page center `(105, 148.5)` mm first maps to the pouch-face disk center
`(105, 194.5)` mm; the panel affine then maps that center to the imposed A4
sheet. Rotation and circular clipping use the pouch-face center, preventing
the 46 mm vertical offset that would result from applying the panel affine
directly to the canonical page center.

## Polar classroom-disk content

`PolarPlanisphereDetailPolicy` is the packaged atlas-detail authority for a
`polar_planisphere` composition. Its canonical configuration selects stars
through magnitude 5.0 and enables exactly `stars`, `constellation_lines`,
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
printer-calibrated values use white paper, darker configurable blue stars, a
curve that promotes intermediate magnitudes while reaching its 1.25 pt² floor
at magnitude 5, darker filled Milky Way and Cloud features with zero Milky Way
edge and contour realization, stronger but subordinate constellation and
reference structure, a restrained circular boundary, and no legend. The
same palette owns 6.45 pt day labels and 11.5 pt month labels, with their
weights, and `CalendarStyle` carries those resolved values to physical-page
realization. The adapter does not
change detail, chart geometry, projection, output scale, or other chart
families. Atlas presentation retains its established screen palette.

The optional bright-star overlay uses `StellarStyle` values for its magnitude
cutoff, color, opacity, and affine magnitude scale and offset.
`PublicationStyle` emits one vectorized five-point overlay, and the renderer
masks vector-valued overlay areas with the same point mask. The corrected polar
configuration uses a 0.5 cutoff, retaining the established bright affine law
through that endpoint and the established ordinary 0.18..5.5 affine law,
then multiplies five-point areas by `0.70^2 / 0.38^2` so the inner pentagon has
70 percent of the mapped linear size, and suppresses the ordinary circle under
each selected overlay. These are
appearance-only operations over the existing Hipparcos points.

The canonical actual-size page and pouch tools pass an 86 mm calendar radius
to the paired disk request. This is the stellar-aperture boundary inside the
unchanged 97.5 mm outer radius. `PolarCalendarFurnitureRequest` places day and
month labels at 0.957 of the outer radius in the remaining annulus; its
rendered-font regression verifies
that the complete Spanish month names remain inside the cut line.

Run `python tools/render_48e2_polar_preview.py` for the canonical equidistant
north/south diagnostic. The tool may also render `--projection stereographic`
for comparison and accepts `--dpi 540` for three-times-linear-resolution
inspection. It routes its ecliptic label anchors through `CoordinateService`,
writes only below the requested output directory, and saves each face once.

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
The physical disk suppresses their inline labels and renders all pole and
ecliptic-keypoint markers at the same small, light weight. Their meanings are
reserved for later external product furniture or documentation.
The ecliptic cardinal keypoints retain their zodiac labels. Packaged polar
label directions place the celestial-equator and ecliptic names in opposite,
comparatively sparse 3h/15h sectors rather than near their crossings. The
configuration stores equatorial right ascension and ecliptic longitude so the
anchors remain independent of page size and projection scale.
Ecliptic anchors and cardinal keypoints share the reference grid's barycentric
true-ecliptic J2000 frame. The equatorial grid and celestial equator are FK5
J2000, so the equinox markers coincide with both curves. A future explicit
`of_date` product policy must change the whole reference set together.

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
`docs/developer/archive/acceptance_history/visual_acceptance_46d8.md`.

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


## SVG output contract (Milestone 49F.3)

The shared chart product arguments accept `--format png`, `--format pdf`,
and `--format svg`. Public format resolution is owned by
`wenu.output_policy.OutputFormat`; backend-specific Matplotlib font terms are
not public API.

`ChartProductOptions.output_format` carries an optional explicit format into
deterministic naming. A single-file output suffix that contradicts an explicit
format raises `ValueError`. Commands that omit the option retain established
configuration and suffix behavior.

The canonical SVG final-save path retains genuine text elements and then
annotates Wenu-owned semantic artist groups through
`wenu.svg_document.annotate_semantic_svg()`. Those groups expose stable IDs,
semantic layer and paint metadata, and `data-wenu-edit` classification without
reordering the XML tree or changing geometry, clipping, or appearance.

SVG is the editable vector product; PDF is the portable publication and
printing product. Ordinary SVG names font families and fallbacks but does not
embed font files. The supported external-editing rules and safe Inkscape
workflow are documented in `docs/user_guide/svg_output.md`.

## Temporal sequence vocabulary (Milestone 49G.1)

`src/wenu/temporal.py` defines renderer-neutral immutable time contracts.

`TemporalTimeline` owns strictly increasing, offset-aware physical instants.
It normalizes them to UTC, keeps an IANA civil/display time zone separate, and
reports simulation duration, frame count, uniform sampling interval when
present, sampling kind, civil representations, and deterministic frame names.
`TemporalTimeline.uniform()` creates an inclusive uniform sample; direct
construction permits explicitly irregular samples.

`PlaybackSpec` owns only playback duration and frames per second. Its implied
frame count may be checked against a timeline, but playback never determines
the meaning of a simulation instant or sampling interval.

`tools/render_circumpolar_movie.py` is the reference consumer. It resolves
these contracts and still performs complete canonical `wenu_chart` renders
before invoking external FFmpeg. No package sequence renderer, alternate
astronomical path, CLI sequence request, or temporal cache exists yet.

### Observer-time chart sequence (Milestone 49G.2)

`ObserverTimeChartSequenceRequest` pairs one immutable `ChartRequest` with
one `TemporalTimeline`. It currently accepts one explicitly formatted
product whose configured output is a directory. Planning preserves the chart
definition and replaces only observer time and the deterministic frame output
path.

`generate_observer_time_chart_sequence()` has no injectable production
executor: it calls `generate_chart_request()` for every frame and validates
the returned static output against its plan. The ordered
`ObserverTimeChartSequenceGeneration` retains per-frame UTC simulation time,
civil display time, complete static generation, and output path.

This API is intentionally observer-time-specific. Proper motion and
precession require a future celestial-realization epoch plus catalogue
reference epoch, time scale, astrometric propagation, frame, and provenance
policy. Moving-object providers likewise require their own explicit evaluation
instant. Neither role is represented by relabelling observer time.



### Deterministic sequence manifests (Milestone 49G.3)

`ObserverTimeSequenceManifest.from_sequence()` creates the schema-versioned
portable identity of an `ObserverTimeChartSequenceRequest`. The canonical
identity includes chart/product choices, timeline, display timezone, playback,
and ordered frames while excluding only the base observer time and output
directory owned by the sequence plan.

`write_observer_time_sequence_manifest()` writes a fresh manifest atomically;
`read_observer_time_sequence_manifest()` validates schema and identity;
`update_observer_time_sequence_manifest()` atomically persists verified frame
byte counts and SHA-256 values without changing plan identity.

`generate_observer_time_chart_sequence(..., restart_policy="restart")`
renders all frames. With `restart_policy="resume"`, it rejects incompatible
plans and reuses only outputs whose complete file bytes match their manifest
record. Missing or changed outputs return to canonical static generation.


## Temporal sequence CLI and configuration (Milestone 49G.4)

The installed `wenu_chart` family commands optionally accept an inclusive
observer-time stop, uniform frame count, civil display timezone, playback
metadata, and restart/resume policy. Omission preserves the existing static
path. Static and sequence commands resolve through one shared CLI product
plan and `chart_view_request()`; sequence frames then use only
`generate_observer_time_chart_sequence()` and `generate_chart_request()`.

`ConfigurationDefaults.sequence` carries the immutable translated
schema-version-1 `[sequence]` table. Packaged values disable sequence output.
User overlays may provide a complete sequence, and explicit CLI values take
precedence. The effective configuration reaches every frame and participates
in deterministic manifest identity.

## Fixed-sky rotating-horizon planning

`FixedSkyRotatingHorizonSequenceRequest` plans an Earth-rotation presentation
with one explicit aware `celestial_anchor_time` and a
`TemporalTimeline` of observer-local instants. Its frames keep the celestial
request and camera time fixed while exposing a separate local observer for
horizon, cardinal, AltAz, visibility, and mask realization.

This is a planning boundary only. The accepted implementation continues to use
complete observer-time renders as its oracle; optimized canonical rendering
and scientifically keyed reuse are later 49H increments. The celestial anchor
is not a catalogue reference epoch and does not replace future provider-owned
proper-motion realization.

The 49H.2 independent current-behavior baseline is
`generate_fixed_sky_complete_render_baseline()`, which produces complete canonical circumpolar observer-time renders in a
separate directory. Visual acceptance showed that celestial content rotates,
so these frames are not the fixed-sky pixel oracle.
`compare_png_frames()` reports explicit RGBA difference metrics evaluated
against `PngFrameComparisonTolerance`; exact equality is the default.
Other chart families remain outside this oracle until stable-camera
equivalence is proved.



## Fixed-sky reference rendering (Milestone 49H.3)

`fixed_sky_circumpolar_orientation()` derives one anchor-relative
circumpolar position angle from the actual celestial-to-horizontal
transformation at the anchor and frame instants. It keeps a fixed celestial
reference at identical projected coordinates while rotating local horizon and
AltAz geometry. It does not use a 15-degree-per-hour approximation.

`resolve_fixed_sky_rotating_horizon_frame()` preserves dual-time ownership
while producing an ordinary frame-local `ChartRequest` whose only projection
change is `position_angle_deg`.

`generate_fixed_sky_rotating_horizon_sequence()` is the accepted uncached
reference executor. It sends every resolved frame through
`generate_chart_request()`; no alternate sphere, projection, renderer,
furniture, or export path exists. Scientifically keyed reuse and
restart/resume support remain future work.

## Typed coordinate vocabulary, providers, and service (Milestones 49B.1–49C.1)

`wenu.coordinates.CoordinateSpec` is the immutable scientific identity
vocabulary for a represented coordinate set. It records frame, origin,
position status, optional epoch/equinox and instant/time-scale pairs,
representation and units, provider/model provenance, and declared correction
policies. It does not transform coordinates.

`wenu.coordinates.ObservationContext` is the immutable observer-local input
vocabulary. It records normalized terrestrial longitude, latitude, elevation,
physical instant/time scale, refraction policy, and Earth-orientation policy.
It is not yet constructed by `Observer` in 49B.1.

`wenu.positions.PositionProvider` is a runtime-checkable structural protocol
for native astronomical position generation. Milestone 49B.3 adapts `Stars`, `NonStellar`, and `OpenClusters` as native
ICRS point providers; all `NonStellar` subclasses inherit the centre provider.
`wenu.geometry.SphericalGeometry` names the existing point,
curve, polygon, and grid record union.

Milestone 49B.2 makes `CoordinateSpec` a required keyword-only member of all
four spherical geometry records. Production layers declare the coordinate
identity at construction, transformations declare their target identity,
selection and relative-longitude operations preserve identity, and
`SphericalGrid` rejects components with a different specification. Synthetic
projection tests use an explicitly named generic spherical specification;
there is no implicit or inferred fallback. Coordinate values and equations remain unchanged.

The provider boundary returns native catalogue centres only. Galaxy outlines,
isophotes, constellation geometry, coordinate grids, and horizon geometry are
morphology or constructed references and deliberately do not become position
providers.

## Central coordinate service (Milestone 49C.1)

`wenu.coordinate_service.CoordinateService` is the single new Astropy-backed
transformation boundary for typed spherical geometry. Its `transform()` method
accepts points, curves, polygons, or grids and returns the same concrete kind
in an explicit target `CoordinateSpec`. Identifiers, labels, names, metadata,
curve segmentation, polygon rings, grid component names, and closure flags are
preserved.

ICRS, Galactic, barycentric mean ecliptic, and observer-local AltAz frames are
supported. AltAz requires an explicit `ObservationContext`; vacuum refraction
and Astropy Earth-orientation policy are currently the only accepted local
policies. Existing charts and layers do not call the service until 49C.2, so
49C.1 changes no production rendering path.


## Coordinate ownership during architecture 0.9.5

The accepted 49C.1 `CoordinateService` is the single Astropy-backed owner of
astronomical frame transformations. The merged 49C.2 milestone routes reference
points and grids, chart compatibility conversions, deep-sky geometry,
constellation references, observer caches, and chart-orientation reference
directions through that service while preserving concrete `Spherical*` kinds,
topology, semantic arrays, metadata, and provenance.

Position generation remains separate. `Stars.position()` supplies native
Hipparcos ICRS catalogue positions. Skyfield continues to generate the one
apparent topocentric stellar realization, and constellation lines reuse those
same cached arrays. Native AltAz horizon construction likewise remains
reference geometry; a service call is required only when a product requests
that geometry in another astronomical frame.

The 49C.3 candidate removes `charts/coordinate_frames.py` and the handwritten `coordinates.py::radec_to_altaz()`. Every production Astropy transformation now occurs inside `CoordinateService`. `Observer` supplies immutable `observation_context` and retains only the time, location, Skyfield, and AltAz compatibility state required by providers and public Astropy-coordinate entry points.

# Public celestial reference policy

`CelestialReferencePolicy(equinox="J2000")` is the immutable public contract
for coupled FK5 equatorial and barycentric true-ecliptic reference geometry.
`J2000` is the compatibility default; `of_date` resolves from the chart
observer's declared Astropy time. `ChartRequest.reference_policy` carries the
resolved request through ordinary grid and furniture construction.

The installed command exposes `--reference-equinox EQUINOX`. The corresponding
schema-version-1 overlay is `[coordinates.references] equinox = "..."`, with
the explicit command value taking precedence.

Reusable view drawing passes `ChartView.observer` explicitly to
`configure_chart_request_grids(..., observer=...)`. Direct library callers
may continue to rely on `sky.observer` as the fallback. This distinction is
required for `of_date`, which always resolves from the declared chart
observer's `t_astropy` and never from the computer clock.

Scientific acceptance compared default J2000, explicit J2000.0, J2016.0, and
of-date SVGs. The coupled references moved coherently while apparent stars
remained fixed. Final verification passed 1,786 routine tests with 30
deselected and 1,816 complete tests.

## Accepted drawable Venus track (Milestone 49I.2D.2)

Regional and binocular `wenu_chart` requests accept
`--planet-track venus`, `--track-start`, `--track-sample-step`,
`--track-tick-step`, `--track-tick-count`, and optional
`--track-tick-labels`. The track request is independent of `--planet venus`.

`SolarSystemTrackLayer` realizes the scientific curve.
`solar_system_track_annotations.py` prepares its projected path,
perpendicular ticks, start label, and two-pass perpendicular date layout.
Appearance is owned by `PublicationStyle`; PNG, PDF, and semantic SVG use the
ordinary renderer and exporter.


## Accepted physical apparent-disk boundary (Milestone 49I.3A)

`physical_apparent_disk_audit_49i3a.md` is the active accepted contract for
future resolved Venus and Moon appearance. It separates apparent centre,
physical angular diameter, illumination, tangent-plane orientation,
body-specific orientation, photometry, and object-specific display
magnification.

No runtime API is installed by 49I.3A. Existing Venus and Moon layers continue
to return symbolic `SphericalPoints`, and their current fixed hollow markers
remain unchanged. Future resolved disks must become ordinary semantic geometry
before the canonical projection and shared PNG/PDF/SVG path.


## Venus physical-appearance state (Milestone 49I.3B)

`solar_system_appearance.py::SolarSystemApparentDisk` is the frozen
renderer-neutral physical state. `SolarSystemAppearanceRealizer.appearance()`
accepts one ephemeris source, accepted target and Sun apparent directions,
display identity, physical radius, and radius-model identity.

The result records angular diameter, Sun–target–observer phase angle,
spherical illuminated fraction, and bright-limb position angle measured from
apparent celestial north toward east. `VENUS_MEAN_RADIUS_KM` is 6051.8 km.
No chart request or layer consumes this API in 49I.3B.


## Accepted resolved Venus disk boundary (Milestone 49I.3C)

`resolved_venus_disk_audit_49i3c.md` accepts three ordinary semantic
geometries: illuminated face, limb, and terminator. They are sampled at the
physical angular radius, transformed, and projected ordinarily. Chart
preparation then scales projected offsets around the projected physical centre.

The accepted physical angular diameter remains in
`SolarSystemApparentDisk`; future request/detail policy owns a separate
Venus-specific display magnification. Multiple epochs use independently
realized states in one fixed chart frame. This audit installs no runtime API.


## Venus spherical disk geometry (Milestone 49I.3C.1)

`solar_system_disk_geometry.py::SolarSystemDiskGeometryRealizer.geometry()`
accepts one `SolarSystemApparentDisk` and an optional even sample count of at
least 16. It returns a frozen `SolarSystemDiskGeometry` containing ordinary
`SphericalPoints`, `SphericalCurves`, and `SphericalPolygons` records for
the centre, limb, terminator, and illuminated face.

The default is 720 physical limb samples. Geometry preserves the appearance
coordinate specification, physical angular radius, phase, bright-limb
orientation, model identity, and provenance. It applies no display
magnification and owns no chart or rendering policy.


## Drawable resolved Venus disk (Milestone 49I.3C.2)

`sky/venus_disk.py::VenusDiskRealization` realizes one accepted Venus
appearance and physical disk geometry, transforms all components into the
product frame, and shares that state across the illuminated-face, limb, and
terminator layers.

`charts/request_disks.py::SolarSystemDiskDisplayRequest` owns the explicit
target and governed magnification. `charts/solar_system_disk_preparation.py`
projects the separately transformed physical centre through the chart's exact
projector and scales only projected component offsets about it. Factor 1 is
physical angular scale. The accepted public controls are
`--planet-appearance venus=resolved` and
`--planet-disk-magnification venus=FACTOR`.


## Lunar physical-appearance state (Milestone 49I.3E.1)

`sky/moon.py::MOON_BODY` is the immutable catalog identity shared by the
accepted symbolic Moon layer and future physical appearance. It records NAIF
body ID `301`, Earth parent key, equal-volume mean radius `1737.4 km`, and the
output-neutral `spherical_physical_appearance` capability.

`sky/earth.py::EARTH_BODY` supplies non-drawable NAIF body identity `399` so
catalog relationship queries are complete. `SolarSystemAppearanceRealizer`
uses the accepted topocentric Moon and Sun apparent directions with
descriptor-owned radius data to return `SolarSystemApparentDisk`. No chart
request consumes this state in 49I.3E.1.

Fernando scientifically accepted the eight-case installed-DE440 validation
on 2026-09-02. The maximum apparent-centre residual was `1.338e-07 deg`, the
maximum physical angular-diameter residual was `2.994e-06 arcsec`, and the
minimum explicit topocentric parallax was `0.272607 deg`. The accepted state
remains output-neutral. Final verification passed 73 documentation tests, 124
focused tests, 2,051 routine tests with 30 deselected, and all 2,081 tests;
integration remains.


## Frozen-Earth Venus sequence state (Milestone 49I.3C.3.2A)

`FrozenEarthDiskSequenceRequest` declares exact start-inclusive major samples
and a fixed ecliptic equinox. `FrozenEarthDiskSequenceRealizer.sequence()`
evaluates one start-time Earth heliocentric state and one same-epoch planet
heliocentric state per sample. It returns `FrozenEarthDiskSequence` containing
`FrozenEarthGeometricDisk` values, complete ICRF vectors, frozen-earth/AU
distances, fixed Sun direction, physical appearance, and provenance.

All directions declare geometric status in fixed J2000 mean-ecliptic axes;
none use the apparent-direction pipeline. The API is output-neutral. Drawable
restricted-scene integration remains 49I.3C.3.2B.


## Drawable frozen-Earth Venus sequence (Milestone 49I.3C.3.2B)

`FrozenEarthSolarSystemDiskSequenceDisplayRequest` combines the accepted
scientific request with governed magnification and optional dates.
`FrozenEarthVenusDiskSequenceRealization` exposes shared illuminated-face,
limb, terminator, centre, and fixed-Sun spherical geometry in the frozen-Earth
product frame.

Regional drawing restricts content to those layers, an optional
`FrozenEarthEquatorialGrid`, and an explicitly requested
`FrozenEarthEclipticReference`. `MagnifyProjectedDiskSequence` magnifies every
Venus disk around its own projected physical centre. Public controls use
`--planet-disk-sequence venus`, `--disk-sequence-model
frozen-earth-ecliptic`, `--disk-sequence-start`, `--disk-sequence-step`,
`--disk-sequence-n-steps`, optional `--disk-sequence-labels`, and
`--planet-disk-magnification venus=FACTOR`.


## Accepted multi-epoch planet-disk sequence (Milestone 49I.3C.3)

`planet_disk_sequence_audit_49i3c3.md` defines a proposed immutable sequence
request and result for exact major instants, with no minor curve cadence. The
candidate has two model policies: independently observed topocentric states in
one fixed ordinary chart frame, and frozen-Earth geometric states in one fixed
ecliptic construction. Each sample preserves full physical distance and provenance for possible
future 3D use. Runtime types, CLI names, and 3D visualization are not yet
installed.


## Observed Venus disk sequence (Milestone 49I.3C.3.1A)

`ObservedSolarSystemDiskSequenceRequest` declares a start instant, major step,
interval count, body descriptor, physical radius, and radius model.
`ObservedSolarSystemDiskSequenceRealizer.sequence()` returns
`ObservedSolarSystemDiskSequence` with `n_steps + 1` exact per-epoch
appearances, physical spherical disk geometries, and explicit observer/AU
distances. The API is output-neutral; drawable request integration remains
49I.3C.3.1B.


## Drawable observed Venus disk sequence (Milestone 49I.3C.3.1B)

`ObservedSolarSystemDiskSequenceDisplayRequest` combines the accepted
scientific sequence with one magnification and optional date labels.
`ObservedVenusDiskSequenceRealization` independently transforms each physical
epoch into the fixed product frame and exposes combined centres, limbs,
terminators, and illuminated faces.

`MagnifyProjectedDiskSequence` projects every physical centre and magnifies
each corresponding projected component around that centre. Public controls
are `--planet-disk-sequence venus`, `--disk-sequence-model observed`,
`--disk-sequence-start`, `--disk-sequence-step`,
`--disk-sequence-n-steps`, optional `--disk-sequence-labels`, and
`--planet-disk-magnification venus=FACTOR`.
