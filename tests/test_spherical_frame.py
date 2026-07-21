import numpy as np

from wenu.spherical_frame import (
    SphericalCoordinates,
    SphericalFrame,
)


def test_returns_spherical_coordinates():
    frame = SphericalFrame(
        pole_lon_deg=0.0,
        pole_lat_deg=90.0,
    )

    coords = frame.transform(
        [10.0],
        [20.0],
    )

    assert isinstance(
        coords,
        SphericalCoordinates,
    )


def test_identity_frame_is_identity():
    frame = SphericalFrame(
        pole_lon_deg=0.0,
        pole_lat_deg=90.0,
        position_angle_deg=0.0,
    )

    lon = np.array(
        [-170.0, -30.0, 0.0, 75.0, 179.0]
    )

    lat = np.array(
        [-60.0, -10.0, 0.0, 40.0, 80.0]
    )

    result = frame.transform(
        lon,
        lat,
    )

    np.testing.assert_allclose(
        result.lon_deg,
        lon,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.lat_deg,
        lat,
        atol=1e-12,
    )


def test_inverse_transform_restores_coordinates():
    frame = SphericalFrame(
        pole_lon_deg=35.0,
        pole_lat_deg=52.0,
        position_angle_deg=17.0,
    )

    lon = np.array(
        [-120.0, -40.0, 25.0, 110.0]
    )

    lat = np.array(
        [-50.0, -10.0, 35.0, 70.0]
    )

    transformed = frame.transform(
        lon,
        lat,
    )

    restored = frame.inverse_transform(
        transformed.lon_deg,
        transformed.lat_deg,
    )

    np.testing.assert_allclose(
        restored.lon_deg,
        lon,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        restored.lat_deg,
        lat,
        atol=1e-12,
    )


def test_rotation_matrix_is_orthogonal():
    frame = SphericalFrame(
        pole_lon_deg=12.0,
        pole_lat_deg=48.0,
        position_angle_deg=23.0,
    )

    R = frame.rotation_matrix

    np.testing.assert_allclose(
        R @ R.T,
        np.eye(3),
        atol=1e-12,
    )


def test_scalar_input_is_supported():
    frame = SphericalFrame(
        pole_lon_deg=0.0,
        pole_lat_deg=90.0,
    )

    coords = frame.transform(
        10.0,
        20.0,
    )

    assert np.ndim(coords.lon_deg) == 0
    assert np.ndim(coords.lat_deg) == 0

def test_spherical_frame_is_public_api():
    from wenu import (
        SphericalCoordinates as PublicSphericalCoordinates,
        SphericalFrame as PublicSphericalFrame,
    )

    assert PublicSphericalCoordinates is SphericalCoordinates
    assert PublicSphericalFrame is SphericalFrame

def test_frame_can_be_constructed_from_rotation_matrix():
    rotation_matrix = np.array(
        [
            [0.0, -1.0, 0.0],
            [1.0,  0.0, 0.0],
            [0.0,  0.0, 1.0],
        ]
    )

    frame = SphericalFrame.from_rotation_matrix(
        rotation_matrix
    )

    result = frame.transform(
        lon_deg=0.0,
        lat_deg=0.0,
    )

    np.testing.assert_allclose(
        result.lon_deg,
        90.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        result.lat_deg,
        0.0,
        atol=1e-12,
    )


