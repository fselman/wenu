import numpy as np
import pytest

from wenu.projections.stereographic import StereographicProjection

def test_projection_rejects_nonpositive_radius():
    with pytest.raises(
        ValueError,
        match="radius must be positive",
    ):
        StereographicProjection(radius=0.0)

    with pytest.raises(
        ValueError,
        match="radius must be positive",
    ):
        StereographicProjection(radius=-1.0)

def current_projection_formula(
    alt_deg,
    az_deg,
    *,
    radius,
    flip_ew,
):
    """
    Independent expression of the current projection behavior.

    This deliberately duplicates the established mathematical formula so
    that future refactoring of StereographicProjection can be checked
    against the current implementation.
    """
    alt = np.radians(alt_deg)
    az = np.radians(az_deg)

    r = radius * np.tan(
        (np.pi / 2.0 - alt) / 2.0
    )

    x = r * np.sin(az)
    y = r * np.cos(az)

    if flip_ew:
        x = -x

    return x, y


def test_project_preserves_current_formula():
    altitudes = np.array(
        [-10.0, 0.0, 15.0, 45.0, 75.0, 90.0]
    )
    azimuths = np.array(
        [0.0, 30.0, 90.0, 180.0, 270.0, 359.0]
    )

    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
    )

    expected_x, expected_y = current_projection_formula(
        altitudes,
        azimuths,
        radius=2.0,
        flip_ew=True,
    )

    actual_x, actual_y = projection.project(
        altitudes,
        azimuths,
    )

    np.testing.assert_allclose(
        actual_x,
        expected_x,
        rtol=0.0,
        atol=0.0,
    )
    np.testing.assert_allclose(
        actual_y,
        expected_y,
        rtol=0.0,
        atol=0.0,
    )


def test_zenith_maps_to_origin():
    projection = StereographicProjection()

    x, y = projection.project(
        alt_deg=90.0,
        az_deg=123.0,
    )

    np.testing.assert_allclose(
        [x, y],
        [0.0, 0.0],
        atol=1.0e-15,
    )


def test_horizon_maps_to_projection_radius():
    projection = StereographicProjection(
        radius=3.0,
        flip_ew=False,
    )

    azimuths = np.array(
        [0.0, 90.0, 180.0, 270.0]
    )

    x, y = projection.project(
        alt_deg=np.zeros_like(azimuths),
        az_deg=azimuths,
    )

    np.testing.assert_allclose(
        np.hypot(x, y),
        np.full_like(azimuths, 3.0),
        atol=1.0e-14,
    )


def test_flip_ew_changes_only_x_sign():
    altitudes = np.array(
        [10.0, 30.0, 60.0]
    )
    azimuths = np.array(
        [45.0, 120.0, 300.0]
    )

    normal = StereographicProjection(
        flip_ew=False,
    )
    flipped = StereographicProjection(
        flip_ew=True,
    )

    normal_x, normal_y = normal.project(
        altitudes,
        azimuths,
    )
    flipped_x, flipped_y = flipped.project(
        altitudes,
        azimuths,
    )

    np.testing.assert_allclose(
        flipped_x,
        -normal_x,
    )
    np.testing.assert_allclose(
        flipped_y,
        normal_y,
    )


def test_project_spherical_matches_existing_altaz_projection():
    projection = StereographicProjection(
        radius=2.0,
        flip_ew=True,
    )

    lon_deg = np.array(
        [0.0, 30.0, 90.0, 180.0, 270.0]
    )
    lat_deg = np.array(
        [90.0, 60.0, 30.0, 10.0, 0.0]
    )

    expected_x, expected_y = projection.project(
        alt_deg=lat_deg,
        az_deg=lon_deg,
    )

    actual_x, actual_y = projection.project_spherical(
        lon_deg=lon_deg,
        lat_deg=lat_deg,
    )

    np.testing.assert_allclose(
        actual_x,
        expected_x,
    )
    np.testing.assert_allclose(
        actual_y,
        expected_y,
    )
