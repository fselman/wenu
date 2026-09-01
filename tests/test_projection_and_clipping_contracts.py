"""Current projection and clipping contracts contracts."""

# Contracts consolidated from test_milestone4_projection.py.
import numpy as np
import pytest

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.clipping import (
    clip_curve_to_viewport,
    clip_polygon_to_viewport,
)
from wenu.geometry.projected import ProjectedCurve, ProjectedPolygon
from wenu.projections.stereographic import StereographicProjection
from wenu.geometry.spherical import SphericalPoints
from wenu.geometry.frame import SphericalFrame


def test_default_frame_preserves_existing_projection_exactly():
    lon_deg = np.array([0.0, 30.0, 90.0, 180.0])
    lat_deg = np.array([90.0, 60.0, 30.0, 0.0])

    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
    )

    actual_x, actual_y = projection.project_spherical(
        lon_deg,
        lat_deg,
    )

    radius = 2.0 * np.tan(
        (np.pi / 2.0 - np.radians(lat_deg)) / 2.0
    )
    expected_x = -radius * np.sin(np.radians(lon_deg))
    expected_y = radius * np.cos(np.radians(lon_deg))

    np.testing.assert_array_equal(actual_x, expected_x)
    np.testing.assert_array_equal(actual_y, expected_y)


def test_arbitrary_tangent_point_maps_to_origin():
    frame = SphericalFrame(
        pole_lon_deg=123.0,
        pole_lat_deg=-37.0,
    )
    projection = StereographicProjection(
        flip_ew=False,
        frame=frame,
    )

    point = projection.project_point(123.0, -37.0)

    assert point.x == pytest.approx(0.0, abs=1e-7)
    assert point.y == pytest.approx(0.0, abs=1e-7)


def test_arbitrary_frame_applies_to_geometry_collections():
    frame = SphericalFrame(
        pole_lon_deg=45.0,
        pole_lat_deg=20.0,
    )
    projection = StereographicProjection(
        flip_ew=False,
        frame=frame,
    )
    points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=[45.0],
        lat_deg=[20.0],
        ids=["center"],
    )

    projected = projection.project_geometry(points)

    assert projected.x[0] == pytest.approx(0.0, abs=1e-7)
    assert projected.y[0] == pytest.approx(0.0, abs=1e-7)
    assert projected.ids[0] == "center"


def test_zero_position_angle_places_source_north_on_positive_y():
    frame = SphericalFrame(
        pole_lon_deg=0.0,
        pole_lat_deg=0.0,
        position_angle_deg=0.0,
    )
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=frame,
    )

    x, y = projection.project_spherical(0.0, 30.0)

    assert x == pytest.approx(0.0, abs=1e-14)
    assert y > 0.0


def test_positive_position_angle_rotates_north_toward_negative_x():
    zero = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=SphericalFrame(
            pole_lon_deg=0.0,
            pole_lat_deg=0.0,
            position_angle_deg=0.0,
        ),
    )
    rotated = StereographicProjection(
        radius=2.0,
        flip_ew=False,
        frame=SphericalFrame(
            pole_lon_deg=0.0,
            pole_lat_deg=0.0,
            position_angle_deg=90.0,
        ),
    )

    zero_x, zero_y = zero.project_spherical(0.0, 30.0)
    rotated_x, rotated_y = rotated.project_spherical(0.0, 30.0)

    assert zero_x == pytest.approx(0.0, abs=1e-14)
    assert zero_y > 0.0
    assert rotated_x == pytest.approx(-zero_y, abs=1e-14)
    assert rotated_y == pytest.approx(0.0, abs=1e-14)
    assert np.hypot(rotated_x, rotated_y) == pytest.approx(
        np.hypot(zero_x, zero_y)
    )


def test_angular_radius_conversion_and_viewport():
    projection = StereographicProjection(radius=3.0)

    assert projection.projected_radius(90.0) == pytest.approx(3.0)

    viewport = projection.viewport_for_angular_radius(60.0)
    expected_radius = 3.0 * np.tan(np.radians(30.0))

    assert viewport.xlim == pytest.approx(
        (-expected_radius, expected_radius)
    )
    assert viewport.ylim == pytest.approx(
        (-expected_radius, expected_radius)
    )


@pytest.mark.parametrize(
    "angular_radius_deg",
    [0.0, -1.0, 180.0, 181.0, np.nan, np.inf],
)
def test_invalid_angular_radius_is_rejected(angular_radius_deg):
    projection = StereographicProjection()

    with pytest.raises(ValueError, match="between 0 and 180"):
        projection.projected_radius(angular_radius_deg)


def test_regional_viewport_clips_crossing_curve_and_polygon():
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=False,
    )
    viewport = projection.viewport_for_angular_radius(30.0)
    limit = projection.projected_radius(30.0)

    curve = ProjectedCurve(
        x=[-2.0 * limit, 2.0 * limit],
        y=[0.0, 0.0],
        name="crossing",
    )
    polygon = ProjectedPolygon(
        x=[-2.0 * limit, 2.0 * limit, 2.0 * limit, -2.0 * limit],
        y=[-0.5 * limit, -0.5 * limit, 0.5 * limit, 0.5 * limit],
        name="crossing",
    )

    clipped_curves = clip_curve_to_viewport(curve, viewport)
    clipped_polygon = clip_polygon_to_viewport(polygon, viewport)

    assert len(clipped_curves) == 1
    assert clipped_curves[0].bounds == pytest.approx(
        (-limit, limit, 0.0, 0.0)
    )
    assert clipped_curves[0].name == "crossing"
    assert clipped_polygon is not None
    assert clipped_polygon.bounds == pytest.approx(
        (-limit, limit, -0.5 * limit, 0.5 * limit)
    )
    assert clipped_polygon.name == "crossing"


def test_frame_argument_validation():
    with pytest.raises(TypeError, match="SphericalFrame"):
        StereographicProjection(frame=object())

# Contracts consolidated from test_milestone39g_equatorial_meridian_extent.py.
"""Tests for bounded equatorial meridians."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.geometry.spherical import SphericalCurves
from wenu.sky.coordinate_grids import EquatorialGrid


def grid_with_identity_altaz(monkeypatch, **kwargs):
    observer = SimpleNamespace(
        t_astropy=SimpleNamespace(
            isot="2026-08-28T00:00:00.000", scale="utc"
        ),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=0.0,
    )

    def identity_transform(self, geometry, target_spec, observation=None):
        return SphericalCurves(
            lon_deg=geometry.lon_deg,
            lat_deg=geometry.lat_deg,
            coordinate_spec=target_spec,
            names=geometry.names,
            closed=geometry.closed,
            metadata=geometry.metadata,
        )

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.CoordinateService.transform",
        identity_transform,
    )
    return EquatorialGrid(
        observer,
        samples=9,
        equinox="J2000",
        **kwargs,
    )


def test_equatorial_meridian_honors_configured_declination_extent(
    monkeypatch,
):
    grid = grid_with_identity_altaz(
        monkeypatch,
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )
    meridian = grid.meridian(0.0)
    assert meridian.lat_deg[0][0] == pytest.approx(-75.0)
    assert meridian.lat_deg[0][-1] == pytest.approx(90.0)


def test_equatorial_grid_meridians_use_configured_extent(monkeypatch):
    grid = grid_with_identity_altaz(
        monkeypatch,
        ra=(0.0, 30.0),
        dec=(-75.0,),
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )
    geometry = grid.spherical_geometry(grid.observer)
    assert len(geometry.components["meridians"]) == 2
    for latitude in geometry.components["meridians"].lat_deg:
        assert latitude[0] == pytest.approx(-75.0)
        assert latitude[-1] == pytest.approx(90.0)


@pytest.mark.parametrize(
    "minimum, maximum",
    ((-91.0, 90.0), (-75.0, -75.0), (-75.0, 91.0)),
)
def test_invalid_meridian_declination_extent_is_rejected(
    minimum,
    maximum,
):
    with pytest.raises(ValueError):
        EquatorialGrid(
            object(),
            meridian_dec_min=minimum,
            meridian_dec_max=maximum,
        )

# Contracts consolidated from test_milestone39i_projection_cap_polygons.py.
"""Tests for spherical-cap preparation of regional filled polygons."""

import numpy as np
import pytest

from wenu.geometry.projected import ProjectedPolygons
from wenu.geometry.spherical import SphericalPolygons
from wenu.projections import StereographicProjection
from wenu.rendering import clip_polygons_to_projection_cap


def polygons():
    return SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(
            [-10.0, 10.0, 10.0, -10.0],
            [-10.0, 10.0, 10.0, -10.0],
            [-10.0, 10.0, 10.0, -10.0],
        ),
        lat_deg=(
            [60.0, 60.0, 50.0, 50.0],
            [-30.0, -30.0, -45.0, -45.0],
            [40.0, 40.0, 20.0, 20.0],
        ),
        names=["near", "far", "crossing"],
        metadata={
            "level": np.asarray([1, 2, 3]),
            "collection": "isophotes",
        },
    )


def test_cap_clipping_discards_far_side_and_preserves_near_side():
    projection = StereographicProjection()
    spherical = polygons()
    projected = projection.project_polygons(spherical)

    clipped = clip_polygons_to_projection_cap(
        spherical,
        projected,
        projection=projection,
        angular_radius_deg=60.0,
    )

    assert isinstance(clipped, ProjectedPolygons)
    assert [polygon.name for polygon in clipped] == [
        "near",
        "crossing",
    ]
    assert clipped.metadata["level"].tolist() == [1, 3]
    assert clipped.metadata["collection"] == "isophotes"


def test_crossing_polygon_ends_at_cap_without_projection_wrap():
    projection = StereographicProjection()
    spherical = polygons()
    projected = projection.project_polygons(spherical)

    clipped = clip_polygons_to_projection_cap(
        spherical,
        projected,
        projection=projection,
        angular_radius_deg=60.0,
    )
    crossing = clipped[1]
    cap_radius = projection.projected_radius(60.0)
    radii = np.hypot(crossing.x, crossing.y)

    assert np.all(np.isfinite(radii))
    assert np.max(radii) <= cap_radius + 1.0e-10
    assert np.any(np.isclose(radii, cap_radius, atol=1.0e-10))


@pytest.mark.parametrize("radius", [-1.0, 0.0, 90.0, 180.0, np.nan])
def test_cap_radius_must_be_on_near_hemisphere(radius):
    projection = StereographicProjection()
    spherical = polygons()
    projected = projection.project_polygons(spherical)

    with pytest.raises(ValueError):
        clip_polygons_to_projection_cap(
            spherical,
            projected,
            projection=projection,
            angular_radius_deg=radius,
        )


def test_cap_clipping_requires_matching_polygon_collections():
    projection = StereographicProjection()
    spherical = polygons()

    with pytest.raises(ValueError):
        clip_polygons_to_projection_cap(
            spherical,
            ProjectedPolygons([]),
            projection=projection,
        )

# Contracts consolidated from test_milestone42c_canonical_polygon_clipping.py.
"""Regression tests for canonical pre-projection polygon clipping."""

from pathlib import Path

import numpy as np

from wenu.geometry.projected import ProjectedPolygons
from wenu.geometry.spherical import SphericalPolygons
from wenu.geometry.viewport import Viewport
from wenu.charts.regional import RegionalChart
from wenu.projections import StereographicProjection
from wenu.rendering import (
    clip_polygons_to_latitude,
    project_geometry_for_viewport,
    project_polygons_to_projection_cap,
    projection_cap_for_viewport,
)
from wenu.sky import CelestialSphere
from wenu.sky.sky_layer import SkyLayer


class PolygonLayer(SkyLayer):
    def spherical_geometry(self, observer):
        return SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
            lon_deg=(
                [-10.0, 10.0, 10.0, -10.0],
                [-10.0, 10.0, 10.0, -10.0],
            ),
            lat_deg=(
                [80.0, 80.0, 60.0, 60.0],
                [-50.0, -50.0, -70.0, -70.0],
            ),
            names=("near", "far"),
            metadata={"level": np.asarray([1, 2])},
        )


class RecordingRenderer:
    def __init__(self):
        self.viewport = None
        self.geometry = None

    def apply_viewport(self, viewport):
        self.viewport = viewport

    def draw(self, geometry, **style):
        self.geometry = geometry
        return ()


def test_viewport_cap_contains_all_four_corners():
    projection = StereographicProjection(radius=2.0)
    viewport = Viewport(-0.5, 0.75, -0.25, 0.6)
    cap = projection_cap_for_viewport(projection, viewport)
    corner_radius = max(
        np.hypot(x, y)
        for x in (viewport.x_min, viewport.x_max)
        for y in (viewport.y_min, viewport.y_max)
    )
    corner_angle = projection.angular_radius_for_projected_radius(
        corner_radius
    )
    assert cap > corner_angle
    assert cap < 90.0


def test_polygons_are_clipped_before_the_unsafe_full_projection():
    projection = StereographicProjection()
    viewport = Viewport(-0.6, 0.6, -0.6, 0.6)
    projected = project_geometry_for_viewport(
        PolygonLayer().spherical_geometry(object()),
        projection=projection,
        viewport=viewport,
    )
    assert isinstance(projected, ProjectedPolygons)
    assert [polygon.name for polygon in projected] == ["near"]
    assert projected.metadata["level"].tolist() == [1]
    assert projected.metadata["projection_domain_clipped"]
    assert np.all(np.isfinite(projected[0].x))
    assert np.all(np.isfinite(projected[0].y))


def test_regional_chart_uses_canonical_projection_before_prepare():
    sky = CelestialSphere(object())
    layer = sky.add(PolygonLayer())
    renderer = RecordingRenderer()
    observed = {}

    def prepare(spherical, projected):
        observed["names"] = [item.name for item in projected]
        return projected

    chart = RegionalChart(
        center_alt_deg=90.0,
        center_az_deg=0.0,
        field_width_deg=34.0,
        field_height_deg=34.0,
    )
    chart.render(
        sky,
        renderer=renderer,
        layer_options={
            layer: {
                "prepare": prepare,
            }
        },
    )
    assert renderer.viewport == chart.viewport
    assert observed["names"] == ["near"]
    assert [item.name for item in renderer.geometry] == ["near"]


def test_projection_domain_and_horizon_clipping_remain_composable():
    spherical = PolygonLayer().spherical_geometry(object())
    projected = project_polygons_to_projection_cap(
        spherical,
        projection=StereographicProjection(),
        angular_radius_deg=45.0,
    )
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=70.0,
    )
    assert [polygon.name for polygon in clipped] == ["near"]
    assert np.all(np.isfinite(clipped[0].x))
    assert np.all(np.isfinite(clipped[0].y))


def test_complete_sphere_latitude_floor_preserves_seam_topology():
    spherical = PolygonLayer().spherical_geometry(object())
    projected = ProjectedPolygons([])

    assert clip_polygons_to_latitude(
        spherical, projected, minimum=-90.0
    ) is projected


def test_inverted_cap_ring_closes_along_planisphere_horizon():
    angles = np.radians((-150.0, -90.0, -30.0, 30.0, 90.0, 150.0))
    latitude = np.asarray((-10.0, -10.0, 10.0, 10.0, -10.0, -10.0))
    radii = np.where(latitude >= 0.0, 0.8, 1.2)
    ring = ProjectedPolygon(
        x=radii * np.cos(angles),
        y=radii * np.sin(angles),
        name="ol1",
    )
    boundary_angles = np.linspace(0.0, 2.0 * np.pi, 1441, endpoint=False)
    boundary = ProjectedPolygon(
        x=np.cos(boundary_angles),
        y=np.sin(boundary_angles),
        name="projection_cap",
    )
    projected = ProjectedPolygons(
        (ring, boundary),
        metadata={
            "projection_source_latitudes": (
                latitude,
                np.full(len(boundary_angles), 0.001),
            ),
            "projection_cap_topology_inversion": np.asarray((True, False)),
        },
    )
    spherical = SphericalPolygons(
        coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(np.degrees(angles), np.degrees(boundary_angles)),
        lat_deg=(latitude, np.full(len(boundary_angles), 0.001)),
    )

    clipped = clip_polygons_to_latitude(spherical, projected, minimum=0.0)

    clipped_radii = np.hypot(clipped[0].x, clipped[0].y)
    assert np.count_nonzero(np.isclose(clipped_radii, 1.0)) > 500
    on_horizon = np.isclose(clipped_radii, 1.0)
    horizon = np.column_stack(
        (clipped[0].x[on_horizon], clipped[0].y[on_horizon])
    )
    assert np.max(np.linalg.norm(np.diff(horizon, axis=0), axis=1)) < 0.02


def test_opposite_winding_boundaries_are_stitched_into_one_band():
    spherical = SphericalPolygons(
        coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(
            np.asarray((-160.0, -80.0, 0.0, 80.0, 160.0)),
            np.asarray((170.0, 90.0, 10.0, -70.0, -150.0)),
        ),
        lat_deg=(
            np.asarray((-10.0, 10.0, 20.0, 10.0, -10.0)),
            np.asarray((-10.0, 10.0, 20.0, 10.0, -10.0)),
        ),
        metadata={
            "compound_id": np.asarray(("ol1", "ol1"), dtype=object),
            "is_hole": np.asarray((False, True)),
            "projection_cap_topology_inversion": np.asarray((True, True)),
        },
    )

    projected = project_polygons_to_projection_cap(
        spherical,
        projection=StereographicProjection(),
        angular_radius_deg=90.0,
    )

    assert len(projected) == 1
    assert projected.metadata["is_hole"].tolist() == [False]
    assert projected.metadata[
        "projection_cap_topology_inversion"
    ].tolist() == [False]
    assert projected[0].name != "projection_cap"
    assert len(projected.metadata["projection_source_latitudes"][0]) == len(
        projected[0].x
    )


def test_summer_triangle_is_part_of_chart_regression_suite():
    source = Path("tests/fixtures/example_regressions/atlas_summer_triangle.py").read_text(
        encoding="utf-8"
    )
    assert "RegionalChart.from_constellations(" in source
    assert "sky.add_milky_way_isophotes()" in source
    assert "clip_polygons_to_projection_cap" not in source


@pytest.mark.integration
def test_circumpolar_lmc_boundary_crosses_projected_lmc():
    namespace = {}
    source = Path("tests/fixtures/example_regressions/circumpolar_atlas.py").read_text(
        encoding="utf-8"
    )
    exec(compile(source, "circumpolar_atlas.py", "exec"), namespace)
    sky, chart = namespace["build_chart"]()
    lmc = sky.magellanic_cloud_isophotes["lmc"]
    spherical = lmc.spherical_geometry(sky.observer)
    projected = chart.projection.project_polygons(spherical)
    field_radius = chart.projection.projected_radius(
        chart.angular_radius_deg
    )
    radii = np.concatenate(
        [np.hypot(polygon.x, polygon.y) for polygon in projected]
    )
    assert np.any(radii < field_radius)
    assert np.any(radii > field_radius)
