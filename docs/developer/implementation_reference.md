# Wenu Implementation Reference

**Branch:** `feature/regional-stereographic-charts`  
**Scope:** current implementation only  
**Purpose:** session-to-session implementation handoff

This document records the current classes, data objects, public calls, principal
arguments, return values, ownership relationships, call sequences, coordinate
conventions, and tests of Wenu. It is intended to make it possible to resume
development without first rediscovering the package structure.

The source code remains authoritative. Update this document whenever a class,
public interface, data contract, ownership relationship, or principal call
sequence changes.

---

# 1. Source tree

```text
src/wenu/
├── __init__.py
├── clipping.py
├── geometry.py
├── observer.py
├── projected.py
├── projection.py
├── resources.py
├── spherical_frame.py
├── viewport.py
├── visibility.py
├── objects/
│   ├── __init__.py
│   └── stars.py
├── sky/
│   ├── __init__.py
│   ├── celestial_sphere.py
│   ├── constellation_boundaries.py
│   ├── constellation_lines.py
│   ├── constellations.py
│   ├── coordinate_grids.py
│   ├── curves.py
│   └── points.py
├── renderers/
│   ├── __init__.py
│   ├── layers.py
│   └── matplotlib_viewport.py
├── data/
└── notebooks/
    ├── en/
    └── es/
```

Principal runtime relationship:

```text
Observer
   │
   ▼
CelestialSphere
   ├── Stars
   ├── Constellations
   │     ├── ConstellationLines
   │     └── ConstellationBoundaries
   ├── CelestialPoints
   ├── CelestialCurve
   └── SphericalCoordinatesGrid subclasses
             │
             ▼
      StereographicProjection
             │
             ▼
 ProjectedPoint / ProjectedCurve / ProjectedPolygon
             │
             ▼
 Matplotlib renderer functions + Viewport
```

---

# 2. `Observer`

**Module:** `wenu.observer`

## Role

Defines the observing location and time. It supplies the astronomical context
used by stellar catalogues, celestial points, constellation boundaries, and
coordinate transformations.

## Construction used by the notebook

```python
observer = Observer(
    location="La Ligua",
    time="2026-08-15 21:00",
)
```

## State consumed elsewhere

| Attribute | Meaning | Main consumers |
|---|---|---|
| `t` | Skyfield time | `Stars`, notebook diagnostics |
| `t_astropy` | Astropy `Time` | boundary and Astropy transformations |
| `lat_deg` | geodetic latitude in degrees | geometry and visibility code |
| `lon_deg` | geodetic longitude in degrees | horizontal conversion |
| `elevation_m` | elevation in metres | observer construction |
| `icrs_frame` | Astropy ICRS frame | `CelestialPoints` |
| `galactic_frame` | Astropy Galactic frame | `CelestialPoints` |
| ecliptic frame | ecliptic coordinate construction | points and grids |
| topocentric/Skyfield observer | apparent positions | `Stars` |

`Observer` produces no projected geometry. It is created by user code and
referenced by `CelestialSphere` and observer-dependent layers.

---

# 3. `CelestialSphere`

**Module:** `wenu.sky.celestial_sphere`

## Role

Central orchestration object for the current celestial scene. It stores the
observer and references to the astronomical layers associated with it. It does
not implement projection mathematics.

## Constructor

```python
CelestialSphere(observer) -> CelestialSphere
```

## Stored state

```python
self.observer
self.stars = None
self.points = None
self.constellations = None
self.constellation_boundaries = None
self.constellation_lines = None
self._layers = []
```

## `layers`

```python
@property
def layers(self) -> tuple[Any, ...]
```

Returns an immutable tuple view of `_layers`.

## `add`

```python
add(layer: Any) -> Any
```

Requires the object to define `draw()`. Raises `TypeError` otherwise. Appends
the object to `_layers` and returns the same object.

## `extend`

```python
extend(layers: Iterable[Any]) -> None
```

Calls `add()` for every supplied layer.

## `remove`

```python
remove(layer: Any) -> None
```

Removes the exact object from `_layers`.

## `clear`

```python
clear() -> None
```

Clears `_layers`. It does not necessarily reset the named attributes.

## `add_stars`

```python
add_stars(
    catalog="hipparcos",
    magnitude_limit=5.5,
) -> Stars
```

Call path:

```text
Stars(
    observer=self.observer,
    catalog=catalog,
    magnitude_limit=magnitude_limit,
)
    │
    ├── Stars.load()
    ├── self.stars = stars
    └── return stars
```

The reviewed implementation stores the object in `self.stars`; convenience
construction and registration in `_layers` are not uniformly coupled.

## `add_points`

```python
add_points(**kwargs: Any) -> CelestialPoints
```

Creates `CelestialPoints(obs=self.observer)`, stores it in `self.points`, and
returns it. In the reviewed version the accepted `**kwargs` are not forwarded.

## `add_constellations`

```python
add_constellations(
    system="western",
    lines_file=None,
    selected=None,
) -> Constellations
```

Precondition: `self.stars is not None`. Otherwise raises:

```python
RuntimeError("Stars must be added before constellations.")
```

Call path:

```text
Constellations(
    stars=self.stars,
    system=system,
    lines_file=lines_file,
    selected=selected,
)
    │
    ├── self.constellations = object
    ├── if boundaries already exist:
    │       object.set_boundaries(self.constellation_boundaries)
    └── return object
```

## `add_constellation_boundaries`

Notebook usage:

```python
boundaries = sky.add_constellation_boundaries(
    boundaries="iau",
    constellations=SELECTED_CONSTELLATIONS,
)
```

Creates a `ConstellationBoundaries` tied to `self.observer`, stores it, and
connects it to an existing `Constellations` object through `set_boundaries()`.

## Grid creation

`celestial_sphere.py` imports `EquatorialGrid`, `EclipticGrid`, and
`GalacticGrid`. Sphere convenience methods construct these current grid
classes. The grids eventually draw through `CelestialCurve` and the projection
subsystem.

---

# 4. `Stars`

**Module:** `wenu.objects.stars`

## Role

Loads and manages a stellar catalogue for one observer. It currently also
computes apparent positions, converts them to horizontal coordinates, projects
them, and renders them.

## Constructor

```python
Stars(
    observer,
    catalog="hipparcos",
    magnitude_limit=5.5,
)
```

## Principal state

| State | Meaning |
|---|---|
| `observer` | shared `Observer` |
| `catalog` | logical catalogue name |
| `magnitude_limit` | limiting magnitude |
| catalogue table/rows | Hipparcos source data |
| HIP identifiers/index | identity and lookup |
| magnitudes | numeric array |
| apparent RA/Dec | observer-time positions |
| altitude/azimuth | horizontal arrays in degrees |
| projected x/y | planar arrays |
| visibility selection | draw mask |
| artist(s) | Matplotlib output |

## `load`

```python
load()
```

Consumes the logical catalogue name, packaged resource, observer, and magnitude
limit. Produces/stores selected rows, HIP indexing, magnitudes, apparent
positions, and horizontal coordinates.

`CelestialSphere.add_stars()` calls `load()` immediately.

## Projection

The current star path is vectorized:

```text
Alt/Az arrays
    │
    ▼
projection.project(...)
    │
    ▼
projection.project_spherical(...)
    │
    ▼
x/y NumPy arrays
```

There is no `project_points()` method in the reviewed implementation.

## Drawing

```text
Stars.draw(ax, projection, ...)
    ├── project arrays
    ├── apply visibility and magnitude selection
    ├── calculate marker sizes
    └── render vectorized points / Matplotlib scatter
```

## Contract with constellation code

`ConstellationLines` and constellation label placement expect `Stars` to have:

1. loaded the catalogue;
2. built HIP lookup/indexing;
3. computed endpoint altitudes;
4. computed projected x/y before code that reads projected state.

This is a current direct coupling.

---

# 5. `CelestialPoints`

**Module:** `wenu.sky.points`

## Internal data object

```python
@dataclass
class _CelestialPoint:
    coord: SkyCoord
    label: Optional[str] = None
    marker: str = "x"
    size: float = 30.0
    color: Any = "white"
    zorder: float = layers.POINTS
    style: dict = field(default_factory=dict)
```

## Constructor

```python
CelestialPoints(obs)
```

State:

```python
self.obs = obs
self._points = []
```

## `clear`

```python
clear() -> CelestialPoints
```

Clears the collection and returns `self`.

## `__len__`

```python
len(points) -> int
```

## `add_equatorial_point`

```python
add_equatorial_point(
    ra_deg,
    dec_deg,
    label=None,
    marker="x",
    size=30.0,
    color="white",
    zorder=layers.POINTS,
    **style,
) -> CelestialPoints
```

Creates:

```python
SkyCoord(
    ra=float(ra_deg) * u.deg,
    dec=float(dec_deg) * u.deg,
    frame=self.obs.icrs_frame,
)
```

Appends an internal point and returns `self`.

## `add_galactic_point`

```python
add_galactic_point(
    lon_deg,
    lat_deg,
    label=None,
    marker="x",
    size=30.0,
    color="white",
    zorder=layers.POINTS,
    **style,
) -> CelestialPoints
```

Creates:

```python
SkyCoord(
    l=float(lon_deg) * u.deg,
    b=float(lat_deg) * u.deg,
    frame=self.obs.galactic_frame,
)
```

The class also contains the corresponding ecliptic-coordinate method.

## Convenience additions

Current convenience methods cover:

- equatorial north, south, or visible pole;
- Galactic poles;
- ecliptic poles;
- Galactic centre and anticentre;
- ecliptic cardinal points;
- other reference points implemented in the file.

They build native-frame `SkyCoord` values and delegate to the common append
mechanism.

## `draw`

```python
draw(ax, projection) -> list[matplotlib.artist.Artist]
```

Per-point path:

```text
stored SkyCoord
    ├── transform to ICRS when required
    ├── radec_to_altaz(...)
    ├── reject hidden point
    ├── projection.project_point(
    │       lon_deg=azimuth,
    │       lat_deg=altitude,
    │       name=label,
    │   )
    ├── render_point(...)
    └── render_text(...) when labeled
```

The collection currently projects points individually. Tests confirm that a
hidden point returns no artists and a labeled visible point returns a point
artist plus a `Text` artist.

---

# 6. `CelestialCurve`

**Module:** `wenu.sky.curves`

## Role and state

Represents one sampled apparent/horizontal curve:

```python
alt_deg: np.ndarray
az_deg: np.ndarray
name: str | None
closed: bool
style: dict
```

## `from_spherical`

```python
@classmethod
from_spherical(
    lon_deg,
    lat_deg,
    frame,
    name=None,
    closed=False,
    style=None,
) -> CelestialCurve
```

Path:

```text
frame.transform(lon_deg, lat_deg)
    ├── result.lon_deg -> azimuth
    └── result.lat_deg -> altitude
```

The frame contract is structural: it needs `transform()` returning an object
with `.lon_deg` and `.lat_deg`.

## `draw`

```python
draw(ax, projection, **style_overrides)
```

Delegates projection, clipping, segmentation, and plotting to
`projection.draw_curve(...)`.

For closed curves, sample ordering is adjusted so a visible segment is not
needlessly split at the array seam.

---

# 7. Coordinate grids

**Module:** `wenu.sky.coordinate_grids`

## Classes

```python
SphericalCoordinatesGrid
EquatorialGrid
EclipticGrid
GalacticGrid
```

## Role

Build families of meridians and parallels. A grid:

1. samples source longitude/latitude arrays;
2. transforms them through a compatible spherical frame;
3. constructs `CelestialCurve` objects;
4. draws those curves through the projection subsystem.

## Inputs

Typical inputs include selected constant longitudes, selected constant
latitudes, sample density, a source-to-horizontal frame, and line style.

## Output

A collection of `CelestialCurve` objects or the artists returned by drawing
those curves.

---

# 8. `ConstellationLines`

**Module:** `wenu.sky.constellation_lines`

## Constructor

```python
ConstellationLines(
    stars,
    system="western",
    filename=None,
    constellations=None,
    *,
    color="white",
    linewidth=0.4,
    alpha=0.7,
    zorder=2,
    horizon_altitude=0.0,
    max_segment_length=None,
)
```

## State

```python
self.stars
self.system
self.filename
self.constellations
self.color
self.linewidth
self.alpha
self.zorder
self.horizon_altitude
self.max_segment_length
self.edges = []
self.edges_by_constellation = {}
self.artists = []
```

The constructor calls `load()`.

## `.fab` format

```text
CONSTELLATION  N  hip1 hip2 hip3 ...
```

Consecutive HIP identifiers define edges.

## `load`

```python
load() -> list[tuple[int, int]]
```

If `filename` is explicit, it validates and reads that path. Otherwise it calls
`constellation_lines_path(self.system)` and uses
`importlib.resources.as_file()`. Parsing is delegated to `_load_file(path)`.

## Drawing contract

For each edge the object reads HIP-indexed altitude and projected x/y from
`Stars`. It draws only resolvable, finite, visible segments and optionally
rejects segments longer than `max_segment_length`.

---

# 9. `ConstellationBoundaries`

**Module:** `wenu.sky.constellation_boundaries`

## Constructor

```python
ConstellationBoundaries(
    observer,
    boundaries="iau",
    filename=None,
    constellations=None,
    *,
    sampling_step_deg=0.5,
    color="white",
    linewidth=0.3,
    alpha=0.4,
    zorder=1,
    horizon_altitude=0.0,
)
```

## State

```python
self.observer
self.boundaries_name
self.filename
self.constellations
self.sampling_step_deg
self.color
self.linewidth
self.alpha
self.zorder
self.horizon_altitude
self.vertices = OrderedDict()
self.sampled_vertices = OrderedDict()
self.altaz = OrderedDict()
self.projected = OrderedDict()
self.artists = []
```

Requires `sampling_step_deg > 0`; constructor calls `load()`.

## Input

Davenhall `bound_18.dat`:

```text
RA_hours  Dec_degrees  constellation_code  boundary_type
```

The vertices for each constellation are contiguous. Closure is internal.

## Serpens

Boundary selection recognizes the two catalogue components `SER1` and `SER2`
and expands user-facing Serpens selection accordingly.

## Principal path

```text
load()
    └── parse FK4/B1875 vertices

sample()
    └── densify long meridian/parallel segments

transform
    └── FK4/B1875 -> observer-time coordinates -> Alt/Az

project(projection)
    └── store projected arrays

draw(ax, projection, ...)
    └── return Matplotlib artists
```

The first-chart notebook explicitly calls `boundaries.sample()`.

---

# 10. `Constellations`

**Module:** `wenu.sky.constellations`

## Role

High-level façade for lines, labels, and boundaries.

## Constructor used by `CelestialSphere`

```python
Constellations(
    stars,
    system="western",
    lines_file=None,
    selected=None,
)
```

## State

```python
self.stars
self.system
self.selected
self.lines
self.boundaries
self.line_artists
self.label_artists
self.boundary_artists
```

## Label overrides

```python
LABEL_OVERRIDES = {
    "SER1": "SerCap",
    "SER2": "SerCau",
}
```

## `draw`

```python
draw(
    ax,
    projection,
    *,
    draw_lines=True,
    draw_labels=True,
    draw_boundaries=False,
    line_kwargs=None,
    label_kwargs=None,
    boundary_kwargs=None,
) -> dict
```

Possible result keys:

```text
"boundaries"
"lines"
"labels"
```

Present call order: boundaries, lines, labels.

## `draw_lines`

Delegates to `ConstellationLines`.

## `draw_labels`

Uses projected star coordinates already stored on `Stars`; therefore stars must
have been projected before label placement.

## `set_boundaries`

Associates a `ConstellationBoundaries` object.

## `draw_boundaries`

Delegates to the associated boundary object when present.

---

# 11. `SphericalCoordinates`

**Module:** `wenu.spherical_frame`

```python
@dataclass(frozen=True)
class SphericalCoordinates:
    lon_deg: np.ndarray
    lat_deg: np.ndarray
```

Coordinate-neutral return object. Longitude and latitude may represent rotated
ICRS, Galactic, ecliptic, horizontal, or another spherical frame.

---

# 12. `SphericalFrame`

**Module:** `wenu.spherical_frame`

```python
@dataclass(frozen=True)
class SphericalFrame:
    pole_lon_deg: float
    pole_lat_deg: float
    position_angle_deg: float = 0.0
```

## Role

Performs spherical rotation only. It does not project or clip.

## `transform`

```python
transform(lon_deg, lat_deg) -> SphericalCoordinates
```

Accepts scalar or array-like values in degrees. Inputs are converted to float
arrays and broadcast to a common shape.

Path:

```text
spherical -> Cartesian unit vectors
    │
rotation_matrix × vectors
    │
Cartesian -> spherical
    │
SphericalCoordinates
```

Output longitude is normalized to `[-180, 180)`.

## `inverse_transform`

```python
inverse_transform(lon_deg, lat_deg) -> SphericalCoordinates
```

Uses the transposed rotation matrix to return coordinates to the source frame.

---

# 13. `StereographicProjection`

**Module:** `wenu.projection`

## Constructor used by tests/notebooks

```python
StereographicProjection(
    radius=2.0,
    flip_ew=False,
)
```

Charts commonly use `flip_ew=True`.

## `project_spherical`

```python
project_spherical(
    lon_deg,
    lat_deg,
) -> tuple[np.ndarray, np.ndarray]
```

Vectorized coordinate-neutral mathematical interface. Latitude `+90°` is the
default tangent point and projects to `(0, 0)`.

## `project`

```python
project(
    alt_deg,
    az_deg,
) -> tuple[np.ndarray, np.ndarray]
```

Horizontal-coordinate compatibility wrapper around `project_spherical()`.
Azimuth corresponds to spherical longitude; altitude to spherical latitude.

## `visible`

```python
visible(alt_deg, az_deg=None)
```

Returns a Boolean scalar or mask. Visibility is primarily altitude/latitude
based; `az_deg` is retained for compatibility.

## `project_point`

```python
project_point(
    lon_deg,
    lat_deg,
    *,
    name=None,
) -> ProjectedPoint
```

Requires scalar coordinates; array inputs raise `ValueError`.

## `project_curve`

```python
project_curve(
    lon_deg,
    lat_deg,
    *,
    name=None,
    closed=False,
) -> ProjectedCurve
```

Accepts one-dimensional arrays and returns a `ProjectedCurve`.

## `project_polygon`

```python
project_polygon(
    lon_deg,
    lat_deg,
    *,
    name=None,
) -> ProjectedPolygon
```

Returns a `ProjectedPolygon`.

## `draw_point`

Compatibility helper that projects and draws one point on Matplotlib axes.

## `draw_curve`

```python
draw_curve(
    ax,
    alt_deg,
    az_deg,
    *,
    closed=False,
    min_altitude=...,
    **style,
)
```

Responsibilities:

1. convert inputs to arrays;
2. determine visible samples;
3. project arrays;
4. split into contiguous visible segments;
5. handle closed-curve seam;
6. plot and return line artists.

It uses `wenu.visibility.visible_segments` and helpers in `wenu.clipping`.

---

# 14. Projected geometry

**Module:** `wenu.projected`

## `ProjectedPoint`

```python
ProjectedPoint(x, y, name=None)
```

Fields: `x: float`, `y: float`, optional `name`.

```python
@property
finite -> bool
```

True only when both coordinates are finite.

## `ProjectedCurve`

```python
ProjectedCurve(
    x,
    y,
    name=None,
    closed=False,
)
```

Validation:

- x and y are one-dimensional;
- shapes match;
- at least two samples.

```python
@property
finite -> np.ndarray[bool]

@property
bounds -> tuple[float, float, float, float] | None
```

Bounds are `(x_min, x_max, y_min, y_max)` over finite coordinate pairs.

## `ProjectedPolygon`

```python
ProjectedPolygon(x, y, name=None)
```

Same shape rules, but requires at least three vertices. Provides `finite` and
`bounds`.

---

# 15. `Viewport`

**Module:** `wenu.viewport`

## Role

Describes the visible chart extent in projected Cartesian coordinates. It does
not transform astronomical coordinates.

The data contract is equivalent to:

```text
x_min, x_max, y_min, y_max
```

Derived values include width, height, centre, and bounds. Tests cover
constructor validation, containment, intersection, padding/expansion, geometry
bounds, and equal-aspect behavior.

## `apply_viewport`

**Module:** `wenu.renderers.matplotlib_viewport`

```python
apply_viewport(ax, viewport, ...)
```

Applies x/y limits and display properties to Matplotlib axes.

---

# 16. Renderer API

**Package:** `wenu.renderers`

Exports currently used:

```python
render_point
render_points
render_curve
render_polygon
render_text
```

## `render_point`

```python
render_point(ax, point: ProjectedPoint, **scatter_style)
```

Returns a Matplotlib `PathCollection`.

## `render_points`

Vectorized point renderer used by `Stars`.

## `render_curve`

Consumes `ProjectedCurve`; returns line artist(s).

## `render_polygon`

Consumes `ProjectedPolygon`; returns polygon/path artist.

## `render_text`

```python
render_text(ax, x, y, text, **text_style)
```

Returns Matplotlib `Text`.

`wenu.renderers.layers` supplies common z-order constants, including
`layers.POINTS`.

---

# 17. Helpers and resources

## `radec_to_altaz`

**Module:** `wenu.geometry`

Converts RA/Dec to observer-relative altitude and azimuth. Public astronomical
angles are degrees.

## `wenu.clipping`

Contains curve clipping, visibility-boundary intersection, and segmentation
helpers.

## `visible_segments`

**Module:** `wenu.visibility`

Used by `StereographicProjection.draw_curve()` to turn a visibility mask into
contiguous drawable segments.

## Resource helpers

**Module:** `wenu.resources`

Confirmed logical accessors:

```python
catalog_path("hipparcos")
constellation_lines_path("western")
boundary_path("iau")
```

An explicit caller-supplied filename overrides a packaged resource.

---

# 18. Principal call sequences

## Standard chart

```python
observer = Observer(
    location="La Ligua",
    time="2026-08-15 21:00",
)

sky = CelestialSphere(observer)

stars = sky.add_stars(
    catalog="hipparcos",
    magnitude_limit=5.5,
)

constellations = sky.add_constellations(
    system="western",
    selected=None,
)

boundaries = sky.add_constellation_boundaries(
    boundaries="iau",
    constellations=None,
)
boundaries.sample()

points = sky.add_points()

projection = StereographicProjection(
    radius=2.0,
    flip_ew=True,
)
```

## Stars

```text
CelestialSphere.add_stars()
    ├── Stars.__init__()
    └── Stars.load()
            ├── locate catalogue
            ├── read/filter catalogue
            ├── compute apparent positions
            ├── compute Alt/Az
            └── build HIP lookup

Stars.draw(ax, projection)
    ├── projection.project(alt_array, az_array)
    │       └── project_spherical(...)
    ├── calculate visibility/size
    └── render_points(...)
```

## Constellations

```text
CelestialSphere.add_constellations()
    ├── require Stars
    └── Constellations(stars=...)

Constellations.draw(...)
    ├── ConstellationBoundaries.draw(...)
    ├── ConstellationLines reads HIP/x/y/alt from Stars
    └── labels derive positions from projected Stars
```

## Points

```text
CelestialPoints.add_*()
    └── store native-frame SkyCoord + style

CelestialPoints.draw(...)
    ├── native frame -> ICRS
    ├── RA/Dec -> Alt/Az
    ├── reject hidden
    ├── projection.project_point(az, alt)
    ├── render_point(...)
    └── render_text(...)
```

## Grid/curve

```text
SphericalCoordinatesGrid
    ├── sample source curve
    ├── SphericalFrame.transform(...)
    └── CelestialCurve

CelestialCurve.draw(...)
    └── projection.draw_curve(...)
            ├── visibility
            ├── clipping/segments
            ├── projection
            └── Matplotlib artists
```

---

# 19. Ownership and dependencies

```text
Notebook
├── owns Observer
├── owns Matplotlib Figure/Axes
├── owns StereographicProjection
├── owns Viewport
└── owns CelestialSphere
      ├── references Observer
      ├── references Stars
      ├── references CelestialPoints
      ├── references Constellations
      ├── references ConstellationBoundaries
      └── owns generic _layers registry

Stars
├── references Observer
├── owns loaded catalogue/index
├── owns apparent and horizontal positions
└── exposes projected state to constellation code

Constellations
├── references Stars
├── owns/references ConstellationLines
└── references ConstellationBoundaries

ConstellationLines ── references Stars
ConstellationBoundaries ── references Observer
CelestialPoints ── references Observer
Grid ── uses SphericalFrame and owns curves

Projection
├── produces ProjectedPoint
├── produces ProjectedCurve
├── produces ProjectedPolygon
├── uses clipping
└── uses visible_segments

Renderer
├── consumes projected geometry
└── produces Matplotlib artists

Viewport ── controls projected Matplotlib extent
```

---

# 20. Reverse call index

| Call | Principal callers | Principal callees/output |
|---|---|---|
| `SphericalFrame.transform` | grids, `CelestialCurve.from_spherical` | `SphericalCoordinates` |
| `project_spherical` | `project`, point/curve/polygon projection | x/y arrays |
| `project` | `Stars`, Alt/Az compatibility code | `project_spherical` |
| `project_point` | `CelestialPoints.draw` | `ProjectedPoint` |
| `draw_curve` | `CelestialCurve.draw` | visibility, clipping, Matplotlib |
| `Stars.load` | `CelestialSphere.add_stars` | catalogue and position state |
| `ConstellationLines.load` | constructor, explicit reload | resource lookup, edge tables |
| `ConstellationBoundaries.load` | constructor, explicit reload | raw B1875 vertices |
| `CelestialPoints.draw` | user/layer drawing | conversion, projection, renderer |

---

# 21. Units and array conventions

- Public astronomical angles are degrees unless explicitly stated otherwise.
- Boundary-file RA is in hours.
- Astropy coordinates carry explicit units.
- Internal trigonometry uses radians.
- Horizontal compatibility maps longitude to azimuth and latitude to altitude.
- `SphericalFrame.transform()` normalizes longitude to `[-180°, 180°)`.
- `SphericalFrame` broadcasts coordinate inputs.
- `project_spherical()` is vectorized.
- `project_point()` requires scalars.
- `ProjectedCurve` and `ProjectedPolygon` require matching 1-D arrays.
- Stellar projection is vectorized.
- `CelestialPoints` currently iterates over points.
- Projected coordinates are Cartesian chart coordinates scaled by projection
  radius.
- `flip_ew=True` mirrors east-west orientation in the projection.
- Curves are clipped/split at the visibility boundary.
- Constellation lines require visible endpoint stars.
- Charts use observer-time apparent/horizontal positions before projection.

---

# 22. Current couplings and transitional interfaces

These are present implementation facts.

1. `Stars` combines catalogue loading, astronomical calculations, projection,
   and rendering.
2. Constellation lines and labels read projected state from `Stars`.
3. `project_spherical(lon, lat)` and compatibility `project(alt, az)` coexist.
4. Explicit projected-geometry rendering and older direct drawing paths coexist.
5. `CelestialSphere._layers` and named layer attributes coexist; convenience
   construction does not uniformly imply registration.
6. `SphericalFrame` centralizes coordinate-neutral rotation, while some layers
   still perform Astropy/Skyfield transformations directly.

---

# 23. Tests

Last recorded complete run:

```text
79 passed
```

| Test module | Coverage |
|---|---|
| `test_celestial_curve.py` | curve/frame transformation contract |
| `test_clipping.py` | clipping and segmentation |
| `test_coordinate_grids.py` | coordinate grids |
| `test_projected.py` | projected value objects |
| `test_projected_geometry_projection.py` | projection return objects |
| `test_projection_regression.py` | stereographic regression behavior |
| `test_spherical_frame.py` | forward/inverse rotations |
| `test_stars_regression.py` | stellar compatibility |
| `test_version.py` | package import/version |
| `test_viewport.py` | viewport geometry |
| `test_viewport_rendering.py` | Matplotlib viewport application |

A temporary mismatch in which `projection.py` imported `visible_segments` but
`visibility.py` did not expose it caused collection failures. Restoring the
helper restored the passing suite.

---

# 24. Maintenance rule

Update this document in the same commit whenever:

- a module or class is added, removed, renamed, or moved;
- a public constructor or method signature changes;
- an input unit, accepted shape, return type, or side effect changes;
- ownership or a principal call path changes;
- a layer begins or ceases to register with `CelestialSphere`;
- a compatibility wrapper is added or removed;
- a test module is added, removed, or renamed.

Do not place planned classes or APIs here. Those belong in
`target_architecture.md` or the roadmap.
