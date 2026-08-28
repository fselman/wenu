from types import SimpleNamespace

import numpy as np

from wenu.sky.coordinate_grids import CoordinatesGrid
from wenu.geometry.spherical import SphericalCurves


class StubGrid(CoordinatesGrid):
    def _native_to_icrs(
        self,
        longitude_deg,
        latitude_deg,
    ):
        return (
            np.asarray(longitude_deg) + 10.0,
            np.asarray(latitude_deg) - 5.0,
        )


def test_make_curves_preserves_native_to_horizontal_conversion(
    monkeypatch,
):
    observer = SimpleNamespace(
        t=object(),
        lat_deg=-33.0,
        lon_deg=-71.5,
    )
    grid = StubGrid(observer, samples=5)

    def fake_radec_to_altaz(
        ra_deg,
        dec_deg,
        t,
        lat_deg,
        lon_deg,
    ):
        np.testing.assert_allclose(
            ra_deg,
            [10.0, 30.0, 50.0],
        )
        np.testing.assert_allclose(
            dec_deg,
            [5.0, 10.0, 15.0],
        )
        assert t is observer.t
        assert lat_deg == observer.lat_deg
        assert lon_deg == observer.lon_deg
        return (
            np.array([20.0, 30.0, 40.0]),
            np.array([100.0, 110.0, 120.0]),
        )

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.radec_to_altaz",
        fake_radec_to_altaz,
    )
    curves = grid._make_curves(
        longitude_deg=(np.array([0.0, 20.0, 40.0]),),
        latitude_deg=(np.array([10.0, 15.0, 20.0]),),
        names=("test_grid_curve",),
        closed=(True,),
        styles=({"linewidth": 1.5},),
    )

    assert isinstance(curves, SphericalCurves)
    np.testing.assert_allclose(
        curves.lat_deg[0],
        [20.0, 30.0, 40.0],
    )
    np.testing.assert_allclose(
        curves.lon_deg[0],
        [100.0, 110.0, 120.0],
    )
    assert curves.names.tolist() == ["test_grid_curve"]
    assert curves.closed.tolist() == [True]
    assert curves.metadata["styles"] == ({"linewidth": 1.5},)