"""Matched back-to-back polar-planisphere disk geometry."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu import (
    PolarPlanispherePair,
    PolarPlanispherePairRequest,
)


@pytest.mark.parametrize(
    "projection_name",
    ("polar_azimuthal_equidistant", "stereographic"),
)
def test_default_pair_resolves_matching_faces_with_opposite_ra_direction(
    projection_name,
):
    request = PolarPlanispherePairRequest(
        projection_name=projection_name
    )

    pair = request.resolve()

    assert isinstance(pair, PolarPlanispherePair)
    assert pair.faces == (pair.south, pair.north)
    assert pair.south.pole == "south"
    assert pair.north.pole == "north"
    assert pair.south.projection_name == projection_name
    assert pair.north.projection_name == projection_name
    assert request.overlap_deg == pytest.approx(40.0)
    assert _ra_direction(pair.south) == -_ra_direction(pair.north)


def test_shared_scale_center_and_physical_radii_are_exactly_paired():
    request = PolarPlanispherePairRequest(
        calendar_radius_mm=92.0,
        pivot_radius_mm=1.0,
    )

    pair = request.resolve()

    assert pair.south.projection_radius == pair.north.projection_radius
    assert pair.south.boundary_radius == pytest.approx(
        pair.north.boundary_radius
    )
    np.testing.assert_allclose(pair.south.viewport.center, (0.0, 0.0))
    np.testing.assert_allclose(pair.north.viewport.center, (0.0, 0.0))
    for registration in (
        pair.south_registration,
        pair.north_registration,
    ):
        assert registration.center == (0.0, 0.0)
        assert registration.outer_radius_mm == pytest.approx(97.5)
        assert registration.calendar_radius_mm == pytest.approx(92.0)
        assert registration.pivot_radius_mm == pytest.approx(1.0)
        assert registration.text_mirrored is False


@pytest.mark.parametrize(
    "projection_name",
    ("polar_azimuthal_equidistant", "stereographic"),
)
def test_equatorial_paper_samples_fold_across_the_back_to_back_axis(
    projection_name,
):
    pair = PolarPlanispherePairRequest(
        projection_name=projection_name
    ).resolve()
    right_ascension = np.asarray((0.0, 35.0, 123.0, 270.0))
    declination = np.zeros_like(right_ascension)

    south_x, south_y = pair.south.projection.project_spherical(
        right_ascension, declination
    )
    north_x, north_y = pair.north.projection.project_spherical(
        right_ascension, declination
    )

    np.testing.assert_allclose(north_x, -south_x, atol=1.0e-12)
    np.testing.assert_allclose(north_y, south_y, atol=1.0e-12)


def test_default_stereographic_pair_uses_correct_unmirrored_south_face():
    request = PolarPlanispherePairRequest(projection_name="stereographic")
    pair = request.resolve()

    assert request.resolved_south_flip_ew is False
    assert pair.south.flip_ew is False
    assert pair.north.flip_ew is False


def test_explicit_stereographic_handedness_override_is_preserved():
    request = PolarPlanispherePairRequest(
        projection_name="stereographic",
        south_flip_ew=True,
    )
    pair = request.resolve()

    assert pair.south.flip_ew is True
    assert pair.north.flip_ew is True


def test_registration_marks_fold_together_but_are_not_rotationally_symmetric():
    request = PolarPlanispherePairRequest()
    pair = request.resolve()

    south = pair.south_registration.marks
    north = pair.north_registration.marks

    assert tuple(value[0] for value in south) == tuple(
        value[0] for value in north
    )
    for south_mark, north_mark in zip(south, north, strict=True):
        assert south_mark[1] == north_mark[1]
        assert north_mark[2] == pytest.approx((-south_mark[2]) % 360.0)
    angles = np.asarray([value[2] for value in south])
    gaps = np.diff(np.append(angles, angles[0] + 360.0))
    assert len(set(gaps)) == len(gaps)


def test_symmetric_custom_overlap_is_allowed_without_rescaling_faces():
    request = PolarPlanispherePairRequest(
        south_limiting_declination_deg=15.0,
        north_limiting_declination_deg=-15.0,
        physical_diameter_mm=200.0,
    )

    pair = request.resolve()

    assert request.overlap_deg == pytest.approx(30.0)
    assert pair.south.angular_radius_deg == pytest.approx(105.0)
    assert pair.north.angular_radius_deg == pytest.approx(105.0)
    assert pair.south_registration.outer_radius_mm == pytest.approx(100.0)


def test_request_is_immutable_and_resolution_does_not_share_mutable_state():
    request = PolarPlanispherePairRequest()
    first = request.resolve()
    second = request.resolve()

    assert first == second
    assert first is not second
    assert first.south is not second.south
    with pytest.raises(FrozenInstanceError):
        request.projection_name = "stereographic"


@pytest.mark.parametrize(
    "options, message",
    (
        (
            {
                "south_limiting_declination_deg": 15.0,
                "north_limiting_declination_deg": -10.0,
            },
            "same polar radius",
        ),
        ({"projection_name": "mollweide"}, "projection_name"),
        ({"physical_diameter_mm": 0.0}, "physical_diameter_mm"),
        ({"projection_radius": 0.0}, "projection_radius"),
        ({"calendar_radius_mm": 98.0}, "calendar_radius_mm"),
        ({"pivot_radius_mm": 98.0}, "pivot_radius_mm"),
        (
            {"registration_radius_fraction": 1.0},
            "registration_radius_fraction",
        ),
        (
            {"registration_angles_deg": (0.0, 90.0)},
            "registration_angles_deg",
        ),
        (
            {"registration_angles_deg": (0.0, 90.0, 360.0)},
            "registration_angles_deg",
        ),
        (
            {"registration_angles_deg": (0.0, 120.0, 240.0)},
            "asymmetric",
        ),
        (
            {
                "south_limiting_declination_deg": -10.0,
                "north_limiting_declination_deg": 10.0,
            },
            "cover the celestial equator",
        ),
        (
            {"calendar_radius_mm": 1.0, "pivot_radius_mm": 2.0},
            "pivot_radius_mm",
        ),
    ),
)
def test_incompatible_pair_geometry_is_rejected(options, message):
    with pytest.raises(ValueError, match=message):
        PolarPlanispherePairRequest(**options)


def test_pair_types_are_public():
    import wenu

    for name in (
        "PolarFaceRegistration",
        "PolarPlanispherePair",
        "PolarPlanispherePairRequest",
        "PolarRegistrationMark",
    ):
        assert name in wenu.__all__


def _ra_direction(chart):
    x, y = chart.projection.project_spherical(
        np.asarray((0.0, 1.0)), np.asarray((0.0, 0.0))
    )
    angle = np.degrees(np.arctan2(x, y))
    difference = (angle[1] - angle[0] + 180.0) % 360.0 - 180.0
    return int(np.sign(difference))
