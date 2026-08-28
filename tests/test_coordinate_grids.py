from types import SimpleNamespace

import numpy as np

from wenu.coordinates import ICRS_ASTROMETRIC_SPEC
from wenu.geometry.spherical import SphericalCurves
from wenu.sky.coordinate_grids import CoordinatesGrid


class StubGrid(CoordinatesGrid):
    def _native_coordinate_spec(self):
        return ICRS_ASTROMETRIC_SPEC


def test_make_curves_routes_native_geometry_through_coordinate_service(
    monkeypatch,
):
    observer = SimpleNamespace(
        t_astropy=SimpleNamespace(
            isot="2026-08-28T00:00:00.000",
            scale="utc",
        ),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=100.0,
    )
    grid = StubGrid(observer, samples=5)

    def fake_transform(self, geometry, target_spec, observation=None):
        assert geometry.coordinate_spec is ICRS_ASTROMETRIC_SPEC
        np.testing.assert_allclose(geometry.lon_deg[0], [0.0, 20.0, 40.0])
        np.testing.assert_allclose(geometry.lat_deg[0], [10.0, 15.0, 20.0])
        assert target_spec.frame == "altaz"
        assert observation.longitude_deg == observer.lon_deg
        assert observation.latitude_deg == observer.lat_deg
        assert observation.elevation_m == observer.elevation_m
        return SphericalCurves(
            lon_deg=(np.array([100.0, 110.0, 120.0]),),
            lat_deg=(np.array([20.0, 30.0, 40.0]),),
            coordinate_spec=target_spec,
            names=geometry.names,
            closed=geometry.closed,
            metadata=geometry.metadata,
        )

    monkeypatch.setattr(
        "wenu.sky.coordinate_grids.CoordinateService.transform",
        fake_transform,
    )
    curves = grid._make_curves(
        longitude_deg=(np.array([0.0, 20.0, 40.0]),),
        latitude_deg=(np.array([10.0, 15.0, 20.0]),),
        names=("test_grid_curve",),
        closed=(True,),
        styles=({"linewidth": 1.5},),
    )

    assert isinstance(curves, SphericalCurves)
    np.testing.assert_allclose(curves.lat_deg[0], [20.0, 30.0, 40.0])
    np.testing.assert_allclose(curves.lon_deg[0], [100.0, 110.0, 120.0])
    assert curves.names.tolist() == ["test_grid_curve"]
    assert curves.closed.tolist() == [True]
    assert curves.metadata["styles"] == ({"linewidth": 1.5},)
