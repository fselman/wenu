"""Tests for spherical-cap preparation of regional filled polygons."""

import numpy as np
import pytest

from wenu.geometry.projected import ProjectedPolygons
from wenu.geometry.spherical import SphericalPolygons
from wenu.projections import StereographicProjection
from wenu.rendering import clip_polygons_to_projection_cap


def polygons():
    return SphericalPolygons(
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
