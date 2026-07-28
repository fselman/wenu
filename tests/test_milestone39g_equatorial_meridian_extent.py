"""Tests for bounded equatorial meridians."""

import numpy as np
import pytest

from wenu.sky.coordinate_grids import EquatorialGrid


def grid_with_identity_altaz(**kwargs):
    grid = EquatorialGrid(
        object(),
        samples=9,
        equinox="J2000",
        **kwargs,
    )
    grid._native_to_altaz = (
        lambda longitude, latitude, observer:
        (np.asarray(latitude), np.asarray(longitude))
    )
    return grid


def test_equatorial_meridian_honors_configured_declination_extent():
    grid = grid_with_identity_altaz(
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )
    meridian = grid.meridian(0.0)
    assert meridian.lat_deg[0][0] == pytest.approx(-75.0)
    assert meridian.lat_deg[0][-1] == pytest.approx(90.0)


def test_equatorial_grid_meridians_use_configured_extent():
    grid = grid_with_identity_altaz(
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
