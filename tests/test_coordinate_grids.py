from types import SimpleNamespace

import numpy as np

from wenu.sky.coordinate_grids import SphericalCoordinatesGrid


class StubGrid(SphericalCoordinatesGrid):
    def _native_to_icrs(
        self,
        longitude_deg,
        latitude_deg,
    ):
        return (
            np.asarray(longitude_deg) + 10.0,
            np.asarray(latitude_deg) - 5.0,
        )


def test_make_curve_preserves_native_to_horizontal_conversion(
    monkeypatch,
):
    observer = SimpleNamespace(
        t=object(),
        lat_deg=-33.0,
        lon_deg=-71.5,
    )

    grid = StubGrid(
        observer,
        samples=5,
    )

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

    curve = grid._make_curve(
        longitude_deg=np.array([0.0, 20.0, 40.0]),
        latitude_deg=np.array([10.0, 15.0, 20.0]),
        name="test_grid_curve",
        closed=True,
        style={"linewidth": 1.5},
    )

    np.testing.assert_allclose(
        curve.alt_deg,
        [20.0, 30.0, 40.0],
    )
    np.testing.assert_allclose(
        curve.az_deg,
        [100.0, 110.0, 120.0],
    )

    assert curve.name == "test_grid_curve"
    assert curve.closed is True
    assert curve.style == {"linewidth": 1.5}

