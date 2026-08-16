"""Accepted astronomical baseline for the classroom polar disks."""

import numpy as np
import pytest

from wenu import (
    POLAR_PLANISPHERE_CONTENT_LAYERS,
    PolarCalendarFurnitureRequest,
    PolarPlanisphereDetailPolicy,
    PolarPlanispherePairRequest,
    compose_chart,
)


ACCEPTED_CLASSROOM_DISK_COMMIT = "09a2afd"
SAMPLE_RIGHT_ASCENSIONS_DEG = np.asarray((0.0, 37.0, 123.0, 271.0))
SAMPLE_DECLINATIONS_DEG = np.asarray((-80.0, -20.0, 0.0, 20.0, 80.0))


def _astronomical_signature(pair):
    """Return only paired celestial geometry, excluding page furniture."""
    signature = []
    for chart in pair.faces:
        right_ascension, declination = np.meshgrid(
            SAMPLE_RIGHT_ASCENSIONS_DEG,
            SAMPLE_DECLINATIONS_DEG,
        )
        x, y = chart.projection.project_spherical(
            right_ascension.ravel(), declination.ravel()
        )
        signature.append(
            {
                "pole": chart.pole,
                "limiting_declination_deg": chart.limiting_declination_deg,
                "projection_name": chart.projection_name,
                "position_angle_deg": chart.position_angle_deg,
                "projection_radius": chart.projection_radius,
                "physical_diameter_mm": chart.physical_diameter_mm,
                "flip_ew": chart.flip_ew,
                "boundary_radius": chart.boundary_radius,
                "boundary_x": chart.boundary.x.copy(),
                "boundary_y": chart.boundary.y.copy(),
                "sample_x": np.asarray(x).copy(),
                "sample_y": np.asarray(y).copy(),
            }
        )
    return tuple(signature)


def _assert_signatures_equal(before, after):
    assert len(before) == len(after)
    for original, decorated in zip(before, after, strict=True):
        assert original.keys() == decorated.keys()
        for key in original:
            if isinstance(original[key], np.ndarray):
                np.testing.assert_allclose(
                    decorated[key],
                    original[key],
                    atol=1.0e-12,
                    equal_nan=True,
                )
            elif isinstance(original[key], float):
                assert decorated[key] == pytest.approx(original[key])
            else:
                assert decorated[key] == original[key]


def test_accepted_classroom_pair_defaults_are_explicitly_frozen():
    request = PolarPlanispherePairRequest()
    pair = request.resolve()

    assert ACCEPTED_CLASSROOM_DISK_COMMIT == "09a2afd"
    assert request.projection_name == "polar_azimuthal_equidistant"
    assert request.south_limiting_declination_deg == pytest.approx(20.0)
    assert request.north_limiting_declination_deg == pytest.approx(-20.0)
    assert request.physical_diameter_mm == pytest.approx(195.0)
    assert request.calendar_radius_mm is None
    assert request.position_angle_deg == pytest.approx(0.0)
    assert request.projection_radius == pytest.approx(2.0)
    assert request.resolved_south_flip_ew is True
    assert request.north_flip_ew is False
    assert pair.south.angular_radius_deg == pytest.approx(110.0)
    assert pair.north.angular_radius_deg == pytest.approx(110.0)


def test_resolving_physical_furniture_cannot_change_celestial_geometry():
    request = PolarPlanispherePairRequest()
    pair = request.resolve()
    before = _astronomical_signature(pair)

    furniture = PolarCalendarFurnitureRequest().resolve(pair)
    after = _astronomical_signature(pair)

    _assert_signatures_equal(before, after)
    assert furniture.south.center == pair.south_registration.center
    assert furniture.north.center == pair.north_registration.center


def test_classroom_content_selection_is_face_neutral_and_frozen():
    pair = PolarPlanispherePairRequest().resolve()
    expected = PolarPlanisphereDetailPolicy().resolve(object(), object())

    south = compose_chart(pair.south, style="atlas", mode="print")
    north = compose_chart(pair.north, style="atlas", mode="print")

    assert south.detail == expected
    assert north.detail == expected
    assert expected.star_magnitude_limit == pytest.approx(5.5)
    assert expected.enabled_layers == POLAR_PLANISPHERE_CONTENT_LAYERS
    assert expected.enabled_layers == frozenset(
        {
            "stars",
            "constellation_lines",
            "constellation_labels",
            "milky_way",
            "magellanic_clouds",
        }
    )
