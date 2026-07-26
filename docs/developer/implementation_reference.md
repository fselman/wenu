# Wenu implementation reference

Status: as implemented on `feature/regional-stereographic-charts` at commit
`8c8abeb` (Milestone 16).

This reference complements `current_architecture.md`. It records the current
modules, contracts, data flow, and extension points. It intentionally avoids
future design commitments.

## 1. Package map

| Module or package | Role |
|---|---|
| `wenu.observer` | observing time, location, and coordinate-frame context |
| `wenu.objects` | astronomical-object abstractions and `Stars` |
| `wenu.sky` | `SkyLayer` implementations and `CelestialSphere` |
| `wenu.spherical` | spherical geometry value objects |
| `wenu.spherical_frame` | tangent-frame rotation |
| `wenu.projection` | stereographic projection and geometry dispatch |
| `wenu.projected` | projected Cartesian geometry value objects |
| `wenu.viewport` | rectangular projected viewport |
| `wenu.clipping` | low-level curve and polygon clipping algorithms |
| `wenu.rendering` | generic preparation functions |
| `wenu.renderers.matplotlib` | Matplotlib renderer and low-level artist functions |
| `wenu.chart` | rendering-result records |
| `wenu.regional` | regional chart configuration and export |
| `wenu.styles` | reusable publication style |
| `wenu.geometry` | coordinate-conversion compatibility utilities |

## 2. Canonical rendering call

The central call is:

```python
result = sky.draw_chart(
    projection=projection,
    renderer=renderer,
    viewport=viewport,
    layer_options=layer_options,
)
```

The equivalent production-level call for a regional chart is:

```python
result = chart.render(
    sky,
    renderer,
    style=style,
    layer_options=overrides,
)
```

`RegionalChart.render()` constructs its projection and viewport, merges style
options and explicit overrides, and delegates to `CelestialSphere.draw_chart()`.

## 3. Layer contract

Every drawable sky layer implements:

```python
class SkyLayer(ABC):
    @abstractmethod
    def spherical_geometry(self, observer, **options):
        ...
```

Concrete signatures may expose layer-specific selection parameters. Those
parameters belong in the `geometry` section of that layer's options.

A layer implementation should:

1. read or hold source data;
2. transform it to the observer's current horizontal frame when required;
3. return a spherical geometry value;
4. preserve identifiers, names, labels, styles, and other non-coordinate data
   in explicit fields or metadata.

A layer implementation must not:

- instantiate a renderer;
- create Matplotlib artists;
- project coordinates;
- cache projected or rendered state as part of normal chart drawing.

## 4. `CelestialSphere`

`CelestialSphere(observer)` is the composition root for a sky.

It provides convenience methods that create and register standard layers,
including stars, celestial points, constellations, labels, and coordinate
grids. Registration order is rendering order.

### 4.1 `draw_chart`

For each registered layer, `draw_chart()` performs:

```python
spherical = layer.spherical_geometry(observer, **geometry_options)
projected = projection.project_geometry(spherical)
prepared = prepare(spherical, projected) if prepare else projected
artists = renderer.draw(prepared, **render_options)
```

When a viewport is supplied, it is applied before layer drawing.

The precise option entry forms are:

```python
# Structured form
layer_options[layer] = {
    "geometry": {"selected": ("Cru", "Cen")},
    "prepare": prepare_callable,
    "render": {"color": "white"},
}

# Dynamic renderer options
layer_options[layer] = {
    "render": lambda spherical, projected: {
        "sizes": ...,
    },
}

# Compatibility flat form: treated as renderer options
layer_options[layer] = {
    "color": "white",
}
```

An explicit layer mapping is preferable to mutation of a shared layer when a
choice varies by chart.

### 4.2 Results

`wenu.chart` defines:

```python
LayerRenderingResult(
    layer,
    spherical,
    projected,
    artists,
)

ChartRenderingResult(
    projection,
    renderer,
    viewport,
    layers,
)
```

The `projected` field contains the value actually sent to the renderer after
optional preparation.

## 5. Spherical geometry

### 5.1 Points

`SphericalPoint` represents one point. `SphericalPoints` represents a
vectorized point set and can carry:

- longitude and latitude arrays;
- identifiers;
- labels;
- names;
- metadata.

Use `SphericalPoints` for catalogue-sized data. Do not construct thousands of
singular point objects for stars.

### 5.2 Curves

`SphericalCurve` holds one sampled curve, its closure flag, identity fields,
and metadata. `SphericalCurves` is the semantic collection wrapper.

Sampling belongs to the layer that knows the native geometry. For example,
constellation boundaries are sampled in their B1875 native frame before being
transformed to observer-time coordinates. Sampling only after precession would
require unnecessary density and would distort the intended construction.

### 5.3 Grids

`SphericalGrid` maps component names to `SphericalCurves`. Typical component
names distinguish meridians, parallels, and reference curves. Component
grouping is preserved through projection so styles can be assigned by semantic
role.

### 5.4 Polygons

`SphericalPolygon` and `SphericalPolygons` represent closed areas and their
collections. Boundary code handles the right-ascension seam and polar
degeneracies before projection.

## 6. Projection

Create an ordinary full-sky stereographic projection with:

```python
projection = StereographicProjection(
    radius=2.0,
    flip_ew=True,
)
```

Create a regional tangent projection with:

```python
projection = StereographicProjection(
    radius=2.0,
    flip_ew=True,
    frame=SphericalFrame(
        pole_lon_deg=center_az_deg,
        pole_lat_deg=center_alt_deg,
        position_angle_deg=position_angle_deg,
    ),
)
```

`project_geometry()` dispatches to the corresponding point, curve, grid, or
polygon projection method. It preserves semantic fields and metadata.

`project_spherical(lon_deg, lat_deg)` is the vectorized numerical projection.
`projected_radius(angle_deg)` converts angular separation from the tangent
point into projected distance and is used to construct regional viewports.

## 7. Projected geometry

The projected containers mirror their spherical sources:

| Spherical input | Projected output |
|---|---|
| `SphericalPoint` | `ProjectedPoint` |
| `SphericalPoints` | `ProjectedPoints` |
| `SphericalCurve` | `ProjectedCurve` |
| `SphericalCurves` | `ProjectedCurves` |
| `SphericalGrid` | `ProjectedGrid` |
| `SphericalPolygon` | `ProjectedPolygon` |
| `SphericalPolygons` | `ProjectedPolygons` |

Collection invariants are validated at construction. Coordinate arrays are
normalized to NumPy arrays. Identity and style data travel with the geometry
rather than through side channels.

## 8. Generic preparation

Use `wenu.rendering` for transformations that depend on geometry and display
policy but do not create artists.

### 8.1 Magnitude sizes

`magnitude_sizes(...)` maps astronomical magnitudes to marker areas. Star
catalogue filtering remains a `Stars` geometry concern; marker sizing is
preparation/render policy.

### 8.2 Point styles

`point_styles(...)` derives entity-level styles for projected point
collections.

### 8.3 Label offsets

`radial_label_offset(distance)` returns an offset callable that moves a label
radially from its projected anchor.

### 8.4 Latitude clipping

`clip_to_latitude(...)` clips supported points, curves, grids, and polygon
boundaries using the original spherical latitude and the projected geometry.
It is suitable for a horizon or another spherical latitude limit.

This clip is distinct from viewport clipping:

- latitude clipping is a geometry-preparation decision;
- viewport clipping is a final renderer/axes decision.

For regional equatorial grids, leaving the grid minimum altitude unset allows
the grid to fill the rectangular viewport. Setting it to `0.0` clips the grid
at the astronomical horizon.

## 9. Matplotlib renderer

Construct the renderer with:

```python
renderer = MatplotlibRenderer(ax)
```

Apply a viewport directly when not using the chart orchestrator:

```python
renderer.apply_viewport(viewport)
```

Draw projected geometry with:

```python
artists = renderer.draw(
    projected,
    **renderer_options,
)
```

The dispatcher supports projected points, curves, grids, polygons, and their
collections. Renderer options can include:

- common style values;
- styles associated with individual entities;
- styles associated with grid components;
- labels and label offsets.

Curve and text artists are explicitly assigned the axes patch as clip path.
The same final clipping principle applies to the other supported artist types.
This is what makes curves generated beyond a regional field terminate cleanly
at the rectangular chart edge.

Do not put observer-time conversion or sky-layer selection in renderer
options.

## 10. Standard layer behavior

### 10.1 `Stars`

`Stars.spherical_geometry()` returns apparent observer-time Alt/Az positions
as `SphericalPoints`. HIP numbers are identifiers and magnitude is retained in
metadata. The geometry call can filter by altitude and magnitude.

Rendering size is derived later by `magnitude_sizes`.

### 10.2 `CelestialPoints`

This layer stores named coordinates and transforms them for the observer. It
returns points with label and style metadata. It is used for reference
locations such as celestial and ecliptic poles.

### 10.3 `ConstellationLines`

Constellation line figures are stored as HIP endpoint edges. Their coordinates
are obtained from the observer-time star geometry, then grouped as spherical
curves. Selection of constellations is a geometry option.

### 10.4 `ConstellationBoundaries`

The official polygons are defined in B1875/FK4. Polygon assembly, seam
handling, polar handling, and sampling occur in that native representation
before conversion to the observer's current Alt/Az frame.

The implementation includes special handling required by the two-part Serpens
constellation and avoids artificial line segments to a celestial pole.

### 10.5 `ConstellationLabels`

Label anchors are spherical and projection-independent. They are computed from
visible stars, with boundary information used where a single label rule is
insufficient. `selected` and `min_stars` can be supplied for each render.

Supplying `selected=()` intentionally suppresses IAU labels, which is useful
when a chart contains a different cultural constellation overlay.

### 10.6 Coordinate grids

The three concrete grid classes share a common `CoordinatesGrid` base. Each
returns a `SphericalGrid`, transforming its native meridians and parallels into
the observer's horizontal frame.

Reference components are optional:

- equator;
- ecliptic;
- galactic plane.

The grid layer does not trim to a rectangular viewport. It generates adequate
curves; projection and the Matplotlib axes patch complete the visible crop.

## 11. `RegionalChart`

### 11.1 Direct construction

```python
chart = RegionalChart(
    center_alt_deg=35.0,
    center_az_deg=210.0,
    field_width_deg=30.0,
    field_height_deg=20.0,
    position_angle_deg=0.0,
    projection_radius=2.0,
    flip_ew=True,
    crop_x=0.0,
    crop_y=0.0,
)
```

All numeric values must be finite. Center altitude is constrained to
`[-90, 90]`; field dimensions must be positive and smaller than 360 degrees;
projection radius must be positive.

### 11.2 Radius constructor

```python
chart = RegionalChart.from_angular_radius(
    center_alt_deg=...,
    center_az_deg=...,
    angular_radius_deg=...,
    aspect_ratio=...,
)
```

The angular radius is the vertical half-field. Width is the vertical diameter
multiplied by `aspect_ratio`.

### 11.3 Coordinate constructor

```python
chart = RegionalChart.from_coordinate(
    observer,
    coordinate,
    field_width_deg=...,
    field_height_deg=...,
    north_up=True,
)
```

The coordinate is transformed through `observer.altaz_frame`. `north_up=True`
computes the celestial-north position angle at the chart center. It is mutually
exclusive with a nonzero explicit position angle.

### 11.4 Constellation constructor

```python
chart = RegionalChart.from_constellations(
    sky,
    ("Cru", "Cen"),
    angular_radius_deg=...,
    aspect_ratio=...,
    north_up=True,
)
```

This requires stars and constellation lines to have been added to the sky. The
center is the spherical mean of unique catalogue endpoints in the selected
figures. By default the same names become the label selection.

### 11.5 Figure sizing

```python
figsize = chart.figure_size(width_inches=7.0)
```

The returned height matches the projected viewport aspect ratio. Use it when
creating the Matplotlib figure; otherwise an apparently small chart inside a
large white canvas can result.

### 11.6 Rendering and export

```python
result = chart.render(
    sky,
    renderer,
    style=PublicationStyle(),
    layer_options=overrides,
)

result, output_path = chart.export(
    sky,
    renderer,
    "chart.png",
    style=PublicationStyle(),
    export_options=ExportOptions(dpi=300),
)
```

Explicit `layer_options` are merged after style-derived options and therefore
act as overrides.

## 12. `PublicationStyle`

`PublicationStyle` centralizes repeatable axes and layer defaults for regional
charts. It controls such concerns as:

- background, foreground, grid, boundary, and reference colors;
- line widths and alpha values;
- star magnitude limit and marker-size mapping;
- layer visibility and selections;
- minimum altitude for stars or grids;
- label styling.

The style:

1. configures a Matplotlib axes;
2. builds the layer-option mapping consumed by the canonical chart pipeline.

`grid_minimum_altitude_deg=None` means no spherical horizon clip for grids, so
they span the regional viewport and are clipped by the axes patch.

## 13. Export

`ExportOptions` fixes:

- DPI;
- `bbox_inches`;
- transparency;
- optional face color;
- image metadata.

`save()` creates the output parent directory and delegates to
`figure.savefig()`. Chart dimensions and DPI are independent:

- use `figure_size()` to control physical size and aspect ratio;
- use `dpi` to control raster resolution;
- do not multiply Matplotlib marker sizes or font sizes merely because DPI is
  increased.

## 14. Adding a new layer

The normal implementation sequence is:

1. subclass the appropriate `SkyLayer` category;
2. implement observer-aware `spherical_geometry()`;
3. choose an existing spherical geometry type;
4. attach stable identifiers and metadata required downstream;
5. register the layer with `CelestialSphere`;
6. configure preparation and renderer options through layer options or a
   style;
7. add geometry, projection, rendering, and dependency tests as appropriate.

Add a new geometry type only when the existing point, curve, grid, and polygon
semantics cannot represent the data.

## 15. Adding a renderer backend

The current backend is Matplotlib. Another renderer should consume projected
geometry and a Cartesian viewport. It must not call sky-layer astronomy or
perform stereographic projection.

Backend-independent preparation should remain in `wenu.rendering`; backend
artist construction belongs in the backend package.

## 16. Tests that define the current contracts

The implementation is covered by focused milestone tests and regression tests.
The most important architectural contract groups are:

| Test area | Contract |
|---|---|
| spherical/projected geometry tests | container validation and metadata preservation |
| projection geometry tests | type dispatch and group preservation |
| Milestone 4 tests | arbitrary tangent-point projection |
| Milestones 6–12 tests | layer geometry contracts |
| Milestones 13–14 tests | renderer and canonical orchestration |
| Milestone 15A tests | preparation and canonical rendering path |
| Milestone 15B dependency tests | removal of reverse and parallel dependencies |
| Milestone 16 tests | regional production API, orientation, sizing, render, and export |
| projection/regional examples | visual regression and end-to-end behavior |

Run the full suite before accepting architectural changes:

```bash
pytest
```

Run the regional examples for visual validation:

```bash
python examples/milestone16_regional_charts.py
```

Generated output directories are build artifacts and should remain untracked.

## 17. Source-of-truth rule

When this reference conflicts with code, the code and tests at the documented
baseline commit are authoritative. Update this document in the same change
that alters a public contract or dependency boundary.
