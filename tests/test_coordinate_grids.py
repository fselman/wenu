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


def test_fixed_native_reference_grids_are_local_and_reject_observer_choices():
    import pytest
    from wenu.sky.coordinate_grids import EquatorialGrid, EclipticGrid, GalacticGrid, AltAzGrid
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    grids = (EquatorialGrid(None, frame="icrs", equinox="J2000", include_equator=True, samples=13),
             EclipticGrid(None, equinox="J2000", include_ecliptic=True, samples=13),
             GalacticGrid(None, include_plane=True, samples=13))
    for grid in grids:
        geometry = grid.realize(context, None)
        assert geometry.coordinate_spec.frame == "icrs"
        assert geometry.metadata["output_coordinate_system"] == "icrs"
        assert "reference" in geometry.components
        assert not hasattr(grid, "_native_realization")
    with pytest.raises(ValueError, match="explicit fixed equinox"):
        EclipticGrid(None).realize(context, None)
    with pytest.raises(ValueError, match="observer-local"):
        AltAzGrid(None).realize(context, None)

def test_native_equatorial_tick_curves_keep_exact_cadence_and_local_state():
    import numpy as np
    from wenu.sky.coordinate_grids import EquatorialGrid
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    grid = EquatorialGrid(None, frame="icrs", equinox="J2000", samples=37, include_equator=True)
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    geometry = grid.realize(context, None, ra=tuple(range(0,360,30)),
        dec=tuple(range(-60,61,30)), ra_ticks=tuple(i*2.5 for i in range(144)),
        dec_ticks=tuple(range(-80,81,10)))
    assert set(geometry.components) == {"meridians", "parallels", "tick_meridians", "tick_parallels"}
    assert len(geometry.components["meridians"]) == 12
    assert len(geometry.components["parallels"]) == 5
    assert len(geometry.components["tick_meridians"]) == 144
    assert len(geometry.components["tick_parallels"]) == 17
    for index, longitude in enumerate(geometry.components["tick_meridians"].lon_deg):
        np.testing.assert_array_equal(longitude, np.full(37,index*2.5))
    assert grid.ra is None and grid.dec is None and not hasattr(grid,"_native_realization")
    assert set(grid.realize(context,None).components) == {"reference"}

