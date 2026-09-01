"""Coordinate-neutral Mollweide mathematics and seam topology."""

import numpy as np
import pytest

from wenu import MollweideProjection
from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import (
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoints,
    ProjectedPolygons,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def projection(**kwargs):
    return MollweideProjection(flip_ew=False, **kwargs)


def test_known_center_equator_seam_and_pole_coordinates():
    value = projection()
    x, y = value.project_spherical(
        [0.0, -180.0, 179.999999, 45.0, 45.0],
        [0.0, 0.0, 0.0, 90.0, -90.0],
    )

    assert (x[0], y[0]) == pytest.approx((0.0, 0.0))
    assert x[1] == pytest.approx(-2.0 * np.sqrt(2.0))
    assert x[2] == pytest.approx(2.0 * np.sqrt(2.0), rel=1.0e-7)
    assert (x[3], y[3]) == pytest.approx((0.0, np.sqrt(2.0)))
    assert (x[4], y[4]) == pytest.approx((0.0, -np.sqrt(2.0)))
    assert value.x_limit == pytest.approx(2.0 * np.sqrt(2.0))
    assert value.y_limit == pytest.approx(np.sqrt(2.0))


def test_center_longitude_orientation_radius_and_validation():
    centered = MollweideProjection(
        central_longitude_deg=30.0, flip_ew=True, radius=2.0
    )
    x, y = centered.project_spherical([30.0, 60.0], [0.0, 0.0])

    assert (x[0], y[0]) == pytest.approx((0.0, 0.0))
    assert x[1] < 0.0
    assert centered.central_longitude_deg == pytest.approx(30.0)
    assert centered.x_limit == pytest.approx(4.0 * np.sqrt(2.0))
    with pytest.raises(ValueError, match="positive"):
        MollweideProjection(radius=0.0)
    with pytest.raises(ValueError, match="finite"):
        MollweideProjection(central_longitude_deg=np.nan)
    with pytest.raises(ValueError, match="latitude"):
        centered.project_spherical(0.0, 91.0)


def test_seam_preparation_tolerates_only_floating_point_boundary_noise():
    value = projection()
    x, y = value._project_normalized(
        np.asarray((-180.0 - 5.0e-12, 180.0 + 5.0e-12)),
        np.asarray((0.0, 0.0)),
    )
    assert x.tolist() == pytest.approx(
        (-2.0 * np.sqrt(2.0), 2.0 * np.sqrt(2.0))
    )
    assert y.tolist() == pytest.approx((0.0, 0.0))
    with pytest.raises(ValueError, match="normalized longitude"):
        value._project_normalized(180.0 + 1.0e-6, 0.0)


def test_projection_converges_smoothly_close_to_poles():
    x, y = projection().project_spherical(
        45.0, [89.999, 89.9999999]
    )

    assert np.all(np.abs(x) < 0.001)
    assert np.all(y <= np.sqrt(2.0))
    assert np.all(y > 1.414)


def test_small_cells_have_equal_area_scale():
    value = projection()

    def cell_area(latitude):
        half = 0.005
        longitude = np.array([-half, half, half, -half])
        latitudes = latitude + np.array([-half, -half, half, half])
        x, y = value.project_spherical(longitude, latitudes)
        return 0.5 * abs(np.sum(
            x * np.roll(y, -1) - np.roll(x, -1) * y
        ))

    equator_scale = cell_area(0.0)
    high_latitude_scale = cell_area(60.0) / np.cos(np.radians(60.0))

    assert high_latitude_scale == pytest.approx(
        equator_scale, rel=2.0e-6
    )


def test_points_are_vectorized_and_preserve_identity():
    points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=[0.0, 90.0],
        lat_deg=[0.0, 30.0],
        ids=[1, 2],
        labels=["A", "B"],
        names=["alpha", "beta"],
        metadata={"catalogue": "test"},
    )

    projected = projection().project_geometry(points)

    assert isinstance(projected, ProjectedPoints)
    np.testing.assert_array_equal(projected.ids, [1, 2])
    np.testing.assert_array_equal(projected.labels, ["A", "B"])
    np.testing.assert_array_equal(projected.names, ["alpha", "beta"])
    assert projected.metadata == {"catalogue": "test"}


def test_curve_crossing_seam_becomes_two_short_segments():
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([170.0, -170.0], [10.0, 20.0]),
        lat_deg=([5.0, 15.0], [0.0, 0.0]),
        ids=("cross", "plain"),
        names=("Crossing", "Plain"),
        metadata={"styles": ({"color": "red"}, {"color": "blue"})},
    )

    projected = projection().project_geometry(curves)

    assert isinstance(projected, ProjectedCurves)
    assert len(projected) == 3
    np.testing.assert_array_equal(
        projected.metadata["ids"], ["cross", "cross", "plain"]
    )
    np.testing.assert_array_equal(
        projected.metadata["names"], ["Crossing", "Crossing", "Plain"]
    )
    assert projected.metadata["styles"] == (
        {"color": "red"}, {"color": "red"}, {"color": "blue"}
    )
    assert all(np.ptp(curve.x) < 0.5 for curve in projected)


def test_closed_seam_crossing_curve_opens_only_its_split_pieces():
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([170.0, -170.0, -175.0], [10.0, 20.0, 15.0]),
        lat_deg=([0.0, 5.0, -5.0], [0.0, 5.0, -5.0]),
        closed=(True, True),
    )

    projected = projection().project_geometry(curves)

    assert len(projected) == 4
    assert [curve.closed for curve in projected] == [
        False, False, False, True
    ]


def test_nonfinite_curve_breaks_remain_disconnected():
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([10.0, 20.0, np.nan, 170.0, -170.0],),
        lat_deg=([0.0, 0.0, np.nan, 5.0, 5.0],),
        ids=("broken",),
    )

    projected = projection().project_geometry(curves)

    assert len(projected) == 3
    np.testing.assert_array_equal(
        projected.metadata["ids"], ["broken", "broken", "broken"]
    )


def test_grid_components_retain_separate_split_collections():
    grid = SphericalGrid(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        components={
            "meridians": SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([170.0, -170.0],),
                lat_deg=([0.0, 0.0],),
            ),
            "parallels": SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
                lon_deg=([0.0, 20.0],),
                lat_deg=([30.0, 30.0],),
            ),
        },
        metadata={"coordinate_system": "galactic"},
    )

    projected = projection().project_geometry(grid)

    assert isinstance(projected, ProjectedGrid)
    assert len(projected["meridians"]) == 2
    assert len(projected["parallels"]) == 1
    assert projected.metadata == {"coordinate_system": "galactic"}


def test_seam_crossing_polygon_becomes_valid_closed_pieces():
    polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([170.0, -170.0, -170.0, 170.0],),
        lat_deg=([-10.0, -10.0, 10.0, 10.0],),
        ids=("region",),
        names=("Region",),
        metadata={
            "group_id": ("g1",),
            "is_hole": np.array([False]),
        },
    )

    projected = projection().project_geometry(polygons)

    assert isinstance(projected, ProjectedPolygons)
    assert len(projected) == 2
    assert all(len(polygon) >= 4 for polygon in projected)
    assert all(np.all(np.isfinite(polygon.x)) for polygon in projected)
    assert all(np.ptp(polygon.x) < 0.5 for polygon in projected)
    np.testing.assert_array_equal(
        projected.metadata["ids"], ["region", "region"]
    )
    np.testing.assert_array_equal(
        projected.metadata["names"], ["Region", "Region"]
    )
    assert projected.metadata["group_id"] == ("g1", "g1")
    np.testing.assert_array_equal(
        projected.metadata["is_hole"], [False, False]
    )
    assert len(projected.metadata["projection_source_latitudes"]) == 2
    for latitude, polygon in zip(
        projected.metadata["projection_source_latitudes"], projected
    ):
        assert len(latitude) == len(polygon)


def test_longitude_winding_polygon_closes_along_map_edge_not_across_map():
    longitude = np.linspace(179.5, -180.0, 720)
    latitude = 11.0 + np.sin(np.radians(longitude))
    polygons = SphericalPolygons(
        coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(np.append(longitude, longitude[0]),),
        lat_deg=(np.append(latitude, latitude[0]),),
        ids=("winding",),
    )

    projected = projection().project_geometry(polygons)

    assert len(projected) == 1
    polygon = projected[0]
    closed_x = np.append(polygon.x, polygon.x[0])
    closed_y = np.append(polygon.y, polygon.y[0])
    steps = np.hypot(np.diff(closed_x), np.diff(closed_y))
    assert np.max(steps) < 0.11
    assert np.min(closed_y) == pytest.approx(
        -np.sqrt(2.0), abs=1.0e-12
    )


def test_unknown_geometry_and_nonscalar_point_are_rejected():
    value = projection()

    with pytest.raises(TypeError, match="Unsupported spherical geometry"):
        value.project_geometry(object())
    with pytest.raises(ValueError, match="scalar"):
        value.project_point([0.0, 1.0], [0.0, 1.0])
