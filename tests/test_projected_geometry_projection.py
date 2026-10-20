import numpy as np
import pytest

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)
from wenu.projections.stereographic import StereographicProjection


@pytest.fixture
def projection():
    return StereographicProjection(
        radius=2.0,
        flip_ew=False,
    )


def test_project_point_returns_projected_point(
    projection,
):
    point = projection.project_point(
        lon_deg=0.0,
        lat_deg=90.0,
        name="tangent point",
    )

    assert isinstance(
        point,
        ProjectedPoint,
    )

    assert point.name == "tangent point"

    np.testing.assert_allclose(
        [point.x, point.y],
        [0.0, 0.0],
        atol=1.0e-12,
    )


def test_project_point_rejects_arrays(
    projection,
):
    with pytest.raises(
        ValueError,
        match="scalar",
    ):
        projection.project_point(
            lon_deg=[0.0, 10.0],
            lat_deg=[45.0, 45.0],
        )


def test_project_curve_returns_projected_curve(
    projection,
):
    curve = projection.project_curve(
        lon_deg=[0.0, 90.0, 180.0],
        lat_deg=[45.0, 45.0, 45.0],
        closed=False,
        name="test curve",
    )

    assert isinstance(
        curve,
        ProjectedCurve,
    )

    assert curve.name == "test curve"
    assert not curve.closed
    assert len(curve) == 3


def test_project_curve_matches_project_spherical(
    projection,
):
    lon_deg = np.array(
        [0.0, 45.0, 90.0]
    )

    lat_deg = np.array(
        [30.0, 45.0, 60.0]
    )

    expected_x, expected_y = (
        projection.project_spherical(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )
    )

    curve = projection.project_curve(
        lon_deg=lon_deg,
        lat_deg=lat_deg,
    )

    np.testing.assert_allclose(
        curve.x,
        expected_x,
    )

    np.testing.assert_allclose(
        curve.y,
        expected_y,
    )


def test_project_curve_validates_matching_shapes(
    projection,
):
    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        projection.project_curve(
            lon_deg=[0.0, 1.0],
            lat_deg=[0.0],
        )


def test_project_curve_validates_dimensions(
    projection,
):
    with pytest.raises(
        ValueError,
        match="one-dimensional",
    ):
        projection.project_curve(
            lon_deg=[[0.0, 1.0]],
            lat_deg=[[0.0, 1.0]],
        )


def test_project_polygon_returns_projected_polygon(
    projection,
):
    polygon = projection.project_polygon(
        lon_deg=[0.0, 120.0, 240.0],
        lat_deg=[45.0, 45.0, 45.0],
        name="triangle",
    )

    assert isinstance(
        polygon,
        ProjectedPolygon,
    )

    assert polygon.name == "triangle"
    assert len(polygon) == 3


def test_project_polygon_requires_three_vertices(
    projection,
):
    with pytest.raises(
        ValueError,
        match="at least three",
    ):
        projection.project_polygon(
            lon_deg=[0.0, 90.0],
            lat_deg=[45.0, 45.0],
        )




@pytest.mark.parametrize('kind', ('stereographic', 'north', 'south'))
@pytest.mark.parametrize('flip', (False, True))
def test_point_batches_preserve_missing_rows_identity_and_source(kind, flip):
    from wenu_kernel.coordinates import GENERIC_SPHERICAL_SPEC
    from wenu_kernel.geometry import SphericalPoints, SphericalFrame
    from wenu_kernel.projections import PolarAzimuthalEquidistantProjection
    if kind == 'stereographic':
        projection = StereographicProjection(frame=SphericalFrame(13., 42., 17.), flip_ew=flip)
    else:
        projection = PolarAzimuthalEquidistantProjection(pole=kind, position_angle_deg=17., flip_ew=flip)
    lon = np.array([20., np.nan, 60., np.inf, 110.])
    lat = np.array([45., 30., -10., 20., np.nan])
    before = (lon.copy(), lat.copy())
    lon.setflags(write=False); lat.setflags(write=False)
    values = np.array([3., 2., 1., 0., -1.]); values.setflags(write=False)
    points = SphericalPoints(lon, lat, coordinate_spec=GENERIC_SPHERICAL_SPEC,
        ids=['a', 'missing-a', 'a', 'missing-b', 'missing-c'],
        names=['A', 'B', 'C', 'D', 'E'], labels=['one', '', 'three', '', ''],
        metadata={'weight': values, 'catalogue_note': 'synthetic missing positions'})
    result = projection.project_geometry(points)
    valid = np.array([True, False, True, False, False])
    expected = projection.project_spherical(lon[valid], lat[valid])
    np.testing.assert_array_equal(result.x[valid], expected[0])
    np.testing.assert_array_equal(result.y[valid], expected[1])
    if kind == 'stereographic':
        # The old stereographic batch sent missing rows through the numeric
        # operation. Its surviving finite coordinates must stay identical.
        with np.errstate(invalid='ignore'):
            legacy_x, legacy_y = projection.project_spherical(lon, lat)
        np.testing.assert_array_equal(result.x[valid], legacy_x[valid])
        np.testing.assert_array_equal(result.y[valid], legacy_y[valid])
    assert np.all(np.isnan(result.x[~valid])) and np.all(np.isnan(result.y[~valid]))
    np.testing.assert_array_equal(result.finite, valid)
    for name in ('ids', 'labels', 'names'):
        np.testing.assert_array_equal(getattr(result, name), getattr(points, name))
    assert result.metadata['catalogue_note'] == points.metadata['catalogue_note']
    np.testing.assert_array_equal(result.metadata['weight'], values)
    np.testing.assert_array_equal(lon, before[0]); np.testing.assert_array_equal(lat, before[1])
    assert not lon.flags.writeable and not lat.flags.writeable and not values.flags.writeable


@pytest.mark.parametrize('pole', ('south', 'north'))
@pytest.mark.parametrize('longitude,latitude', (([], []), ([np.nan, np.inf], [0., np.nan])))
def test_equidistant_empty_and_missing_point_batches(pole, longitude, latitude):
    from wenu_kernel.coordinates import GENERIC_SPHERICAL_SPEC
    from wenu_kernel.geometry import SphericalPoints
    from wenu_kernel.projections import PolarAzimuthalEquidistantProjection
    points = SphericalPoints(longitude, latitude, coordinate_spec=GENERIC_SPHERICAL_SPEC,
        ids=[f'row-{i}' for i in range(len(longitude))], metadata={'source': 'synthetic'})
    result = PolarAzimuthalEquidistantProjection(pole=pole).project_geometry(points)
    assert len(result) == len(points)
    assert np.all(np.isnan(result.x)) and np.all(np.isnan(result.y))
    np.testing.assert_array_equal(result.ids, points.ids)
    assert result.metadata == points.metadata


@pytest.mark.parametrize('pole', ('south', 'north'))
@pytest.mark.parametrize('invalid', ('latitude', 'opposite-pole'))
def test_missing_point_row_does_not_hide_invalid_finite_domain(pole, invalid):
    from wenu_kernel.coordinates import GENERIC_SPHERICAL_SPEC
    from wenu_kernel.geometry import SphericalPoints
    from wenu_kernel.projections import PolarAzimuthalEquidistantProjection
    latitude = 91. if invalid == 'latitude' else (-90. if pole == 'north' else 90.)
    points = SphericalPoints([np.nan, 20.], [0., latitude], coordinate_spec=GENERIC_SPHERICAL_SPEC)
    with pytest.raises(ValueError, match='latitude must|opposite pole'):
        PolarAzimuthalEquidistantProjection(pole=pole).project_geometry(points)
