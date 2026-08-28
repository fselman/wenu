import numpy as np
import pytest

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import (
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoints,
    ProjectedPolygons,
)
from wenu.projections.stereographic import StereographicProjection
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


@pytest.fixture
def projection():
    return StereographicProjection(radius=2.0, flip_ew=False)


def test_projects_points_vectorially_and_preserves_attributes(projection):
    points = SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=[0.0, 90.0],
        lat_deg=[90.0, 0.0],
        ids=[101, 102],
        labels=["A", "B"],
        names=["Alpha", "Beta"],
        metadata={"magnitude": [1.0, 2.0]},
    )

    projected = projection.project_geometry(points)

    assert isinstance(projected, ProjectedPoints)
    np.testing.assert_allclose(projected.x, [0.0, 2.0], atol=1e-12)
    np.testing.assert_allclose(projected.y, [0.0, 0.0], atol=1e-12)
    np.testing.assert_array_equal(projected.ids, [101, 102])
    np.testing.assert_array_equal(projected.labels, ["A", "B"])
    np.testing.assert_array_equal(projected.names, ["Alpha", "Beta"])
    assert projected.metadata == {"magnitude": [1.0, 2.0]}


def test_projects_curves_and_preserves_structure(projection):
    curves = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 90.0], [180.0, 270.0]),
        lat_deg=([0.0, 0.0], [0.0, 0.0]),
        closed=[False, True],
        ids=["c1", "c2"],
        labels=["C1", "C2"],
        names=["First", "Second"],
        metadata={"family": "test"},
    )

    projected = projection.project_geometry(curves)

    assert isinstance(projected, ProjectedCurves)
    assert len(projected) == 2
    assert projected[0].name == "First"
    assert projected[1].closed
    assert projected.metadata["family"] == "test"
    np.testing.assert_array_equal(projected.metadata["ids"], ["c1", "c2"])
    np.testing.assert_array_equal(
        projected.metadata["labels"], ["C1", "C2"]
    )


def test_projects_grid_without_losing_component_groups(projection):
    meridians = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 0.0],),
        lat_deg=([0.0, 45.0],),
    )
    parallels = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 90.0],),
        lat_deg=([30.0, 30.0],),
    )
    grid = SphericalGrid(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        components={
            "meridians": meridians,
            "parallels": parallels,
        },
        metadata={"frame": "equatorial"},
    )

    projected = projection.project_geometry(grid)

    assert isinstance(projected, ProjectedGrid)
    assert set(projected.components) == {"meridians", "parallels"}
    assert isinstance(projected["meridians"], ProjectedCurves)
    assert projected.metadata == {"frame": "equatorial"}


def test_projects_polygons_and_preserves_metadata(projection):
    polygons = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 90.0, 180.0],),
        lat_deg=([0.0, 0.0, 0.0],),
        ids=["p1"],
        labels=["P1"],
        names=["Region"],
        metadata={"source": "iau"},
    )

    projected = projection.project_geometry(polygons)

    assert isinstance(projected, ProjectedPolygons)
    assert projected[0].name == "Region"
    assert projected.metadata["source"] == "iau"
    np.testing.assert_array_equal(projected.metadata["ids"], ["p1"])


def test_project_geometry_rejects_unknown_types(projection):
    with pytest.raises(TypeError, match="Unsupported spherical geometry"):
        projection.project_geometry(object())


def test_legacy_altaz_projection_remains_available(projection):
    x, y = projection.project(alt_deg=90.0, az_deg=0.0)
    assert x == pytest.approx(0.0, abs=1e-12)
    assert y == pytest.approx(0.0, abs=1e-12)
