# Wenu implementation reference

**Baseline:** `feature/regional-stereographic-charts` at commit `c7feaf7`  
**Architecture version:** 0.4  
**Date:** 2026-07-26

This reference records implemented imports, contracts, and normal usage.

## 1. Public imports

```python
from wenu import (
    CelestialSphere,
    ChartRenderingResult,
    ExportOptions,
    FullSkyChart,
    LayerRenderingResult,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
    SphericalFrame,
    StereographicProjection,
    Viewport,
)
```

Package-level implementation imports use:

```python
from wenu.geometry.spherical import SphericalCurves, SphericalGrid
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering.preparation import clip_to_latitude
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.charts.regional import RegionalChart, ExportOptions
from wenu.charts.full_sky import FullSkyChart
from wenu.charts.styles import PublicationStyle
```

Pre-v0.4 paths such as singular top-level geometry modules, `wenu.renderers`,
`wenu.regional`, and `wenu.styles` no longer exist.

## 2. Constructing the sky

```python
observer = Observer(
    location="La Ligua",
    time="2026-08-15 21:00",
)
sky = CelestialSphere(observer)
sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
sky.add_constellations(system="western")
sky.add_constellation_boundaries(boundaries="iau")

points = sky.add_points()
points.add_equatorial_pole(pole="visible")
points.add_ecliptic_pole(pole="visible")
points.add_galactic_center()
points.add_ecliptic_keypoints()

sky.add_equatorial_grid(include_equator=True)
sky.add_ecliptic_grid(include_ecliptic=True)
sky.add_galactic_grid(include_plane=True)
```

Registration order determines drawing order.

## 3. Canonical low-level call

```python
result = sky.draw_chart(
    projection=projection,
    renderer=renderer,
    viewport=viewport,
    layer_options=layer_options,
)
```

For each registered layer, the method:

1. resolves geometry, preparation, and renderer options;
2. requests spherical geometry;
3. projects it;
4. optionally prepares it;
5. renders it;
6. records all observable results.

## 4. Layer contract

Every drawable layer implements:

```python
class SkyLayer(ABC):
    @abstractmethod
    def spherical_geometry(self, observer, **options):
        ...
```

Concrete geometry options belong in the `geometry` section of the per-layer
configuration.

## 5. Geometry correspondence

| Spherical | Projected |
|---|---|
| `SphericalPoint` | `ProjectedPoint` |
| `SphericalPoints` | `ProjectedPoints` |
| `SphericalCurve` | `ProjectedCurve` |
| `SphericalCurves` | `ProjectedCurves` |
| `SphericalGrid` | `ProjectedGrid` |
| `SphericalPolygon` | `ProjectedPolygon` |
| `SphericalPolygons` | `ProjectedPolygons` |

Use vectorized point collections for catalogues. Curve and polygon
collections wrap a manageable number of singular values.

## 6. Projection

Create an arbitrary tangent-point stereographic projection with:

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

`project_spherical()` handles arrays. `project_geometry()` preserves semantic
geometry and component grouping.

## 7. Preparation

Available helpers include:

```python
magnitude_sizes(...)
point_styles(...)
radial_label_offset(...)
clip_to_latitude(spherical, projected, minimum=0.0)
```

`clip_to_latitude()`:

- masks hidden points;
- splits visible curve runs;
- interpolates entry and exit intersections;
- handles grids component by component;
- returns visible polygon-boundary fragments.

It is a spherical semantic clip. It is distinct from final graphical clipping
to a viewport or projected boundary.

## 8. Rendering

```python
renderer = MatplotlibRenderer(ax)
renderer.apply_viewport(viewport)
artists = renderer.draw(projected, **render_options)
```

A full-sky chart additionally configures:

```python
renderer.set_clip_boundary(
    projected_closed_curve,
    style={
        "facecolor": "none",
        "edgecolor": "white",
    },
)
```

All subsequently created artists use that projected boundary as their clip
path.

## 9. Structured layer options

```python
layer_options[layer] = {
    "geometry": {
        "selected": ("Cru", "Cen"),
    },
    "prepare": prepare_callable,
    "render": {
        "style": {
            "color": "white",
        },
    },
}
```

`render` may also be a callable receiving spherical and projected values.
Explicit chart overrides are merged after style-derived options.

## 10. Regional charts

Direct construction:

```python
chart = RegionalChart(
    center_alt_deg=35.0,
    center_az_deg=210.0,
    field_width_deg=30.0,
    field_height_deg=20.0,
)
```

Alternative constructors:

```python
RegionalChart.from_angular_radius(...)
RegionalChart.from_coordinate(...)
RegionalChart.from_constellations(...)
```

Render:

```python
figure, ax = plt.subplots(
    figsize=chart.figure_size(width_inches=7.0)
)
style = PublicationStyle()
style.configure_axes(ax, title="Regional chart")
result = chart.render(
    sky,
    MatplotlibRenderer(ax),
    style=style,
)
```

`north_up=True` is available in coordinate- and constellation-based
constructors.

## 11. Full-sky charts

Zenith-centered:

```python
chart = FullSkyChart()
```

Independent tangent point:

```python
chart = FullSkyChart(
    center_alt_deg=tangent_altitude,
    center_az_deg=tangent_azimuth,
    horizon_altitude_deg=0.0,
    position_angle_deg=0.0,
)
```

The observer defines the horizontal coordinates and horizon. The configured
center defines the projection tangent point.

The retained region must exclude the stereographic antipode. The implemented
validation requires:

```python
center_alt_deg > -horizon_altitude_deg
```

Render and export:

```python
figure, ax = plt.subplots(
    figsize=chart.figure_size(width_inches=7.0)
)
style = PublicationStyle(star_area_scale=0.25)
style.configure_axes(ax, title="Full-sky chart")

result, path = chart.export(
    sky,
    MatplotlibRenderer(ax),
    "full-sky.png",
    style=style,
    export_options=ExportOptions(dpi=300),
)
```

The projected horizon determines both the graphical clip boundary and the
viewport bounds.

## 12. Publication style

`PublicationStyle` supplies:

- sky, foreground, star, boundary, and grid colors;
- marker-size scale;
- label size;
- horizon and grid clipping defaults;
- structured options for all registered standard layers.

For `FullSkyChart`, the chart passes its horizon altitude to the style so that
stars, curves, boundaries, labels, and grids share one limit.

For regional charts, `grid_minimum_altitude_deg=None` lets grids fill the
rectangular viewport.

## 13. Export

```python
ExportOptions(
    dpi=300,
    bbox_inches="tight",
    transparent=False,
    facecolor=None,
    metadata={},
)
```

Use chart `figure_size()` for physical dimensions. DPI controls raster
resolution and must not be used to rescale markers, lines, or text.

## 14. Adding a layer

1. Implement `SkyLayer`.
2. Produce an existing spherical geometry type when possible.
3. Preserve identities and semantic metadata.
4. Register the layer with `CelestialSphere`.
5. Configure chart variation through structured options.
6. Add geometry, projection, rendering, and dependency tests as appropriate.

Do not add a direct draw or projection method to the layer.

## 15. Adding a projection

A projection consumes spherical geometry and returns standard projected
geometry. It must not import observers, sky layers, charts, or renderers.

## 16. Adding a backend

A backend consumes prepared projected geometry and Cartesian framing. It must
not load astronomical resources, transform celestial coordinates, or perform
projection.

## 17. Contract tests

Key suites:

| Tests | Contract |
|---|---|
| spherical/projected tests | geometry validation and preservation |
| Milestone 4 | arbitrary tangent-point projection |
| Milestones 6–12 | sky-layer geometry |
| Milestones 13–15 | rendering and canonical pipeline |
| Milestone 16 | regional production API |
| Milestone 22 | package boundaries and obsolete paths |
| Milestone 23 | full-sky API and projected horizon |

Run:

```bash
pytest
python examples/full_sky_chart.py
python examples/milestone16_regional_charts.py
```

Generated output directories are build artifacts and remain untracked.
