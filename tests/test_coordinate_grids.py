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



def test_constructed_native_planes_consume_shared_results_and_refusals(monkeypatch):
    import pytest
    from wenu.coordinate_service import CoordinateService
    from wenu.sky.coordinate_grids import EquatorialGrid, EclipticGrid, GalacticGrid
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel.geometry.spherical import SphericalGrid
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    grids = (EquatorialGrid(None, frame='fk5', equinox='J2000', samples=13, include_equator=True),
             EclipticGrid(None, equinox='J2000', samples=13, include_ecliptic=True),
             GalacticGrid(None, samples=13, include_plane=True))
    baseline = [grid.realize(context, None) for grid in grids]
    original = CoordinateService.transform
    calls = []
    def changed(service, source, target, observation=None):
        calls.append((source.coordinate_spec, target, observation))
        result = original(service, source, target, observation)
        result.lon_deg = tuple((a + 0.125) % 360 for a in result.lon_deg)
        return result
    monkeypatch.setattr(CoordinateService, 'transform', changed)
    for grid, previous in zip(grids, baseline, strict=True):
        geometry = grid.realize(context, None)
        assert isinstance(geometry, SphericalGrid)
        assert not hasattr(grid, '_native_realization')
        for name, curves in geometry.components.items():
            old = previous.components[name]
            for actual, expected in zip(curves.lon_deg, old.lon_deg, strict=True):
                np.testing.assert_array_equal(actual, (expected + 0.125) % 360)
            for actual, expected in zip(curves.lat_deg, old.lat_deg, strict=True):
                np.testing.assert_array_equal(actual, expected)
            np.testing.assert_array_equal(curves.names, old.names)
            np.testing.assert_array_equal(curves.closed, old.closed)
            assert curves.metadata == old.metadata
    assert {source.frame for source, _, _ in calls} == {'fk5', 'barycentric-true-ecliptic', 'galactic'}
    assert all(target.frame == 'icrs' and observation is None for _, target, observation in calls)
    def refused(*args, **kwargs):
        raise RuntimeError('constructed reference service refused')
    monkeypatch.setattr(CoordinateService, 'transform', refused)
    for grid in grids:
        with pytest.raises(RuntimeError, match='service refused'):
            grid.realize(context, None)



def test_dated_mean_grids_poles_and_cardinals_share_tt_without_mutating_fixed_sources():
    from dataclasses import replace
    from wenu.astrometric_coordinates import LongTermFrame,LONG_TERM_FRAME_POLICY
    from wenu_kernel.records import TimePoint,TimeSpan
    from wenu.coordinate_service import CoordinateService,mean_reference_frame
    from wenu.sky.realization import LayerRealizationContext,NATIVE_ICRS_SPEC
    from wenu.sky.coordinate_grids import EquatorialGrid,EclipticGrid
    from wenu.sky.points import CelestialPoints
    from astropy.coordinates import BarycentricMeanEcliptic
    from astropy.time import Time
    import pytest
    f=LongTermFrame(equinox=TimePoint(-1200955,0.,'tt'),
        validity=TimeSpan(TimePoint(-1200956,0.,'tt'),TimePoint(2451546,0.,'tt')),
        axes='mean-ecliptic-equinox',model_policy=LONG_TERM_FRAME_POLICY)
    context=LayerRealizationContext(NATIVE_ICRS_SPEC,orientation=f)
    service=CoordinateService()
    for grid,axes,kwargs in (
        (EquatorialGrid(None,frame='icrs',equinox='J2000',samples=13),
            'mean-equator-equinox',dict(ra=[0,90],dec=[0,45],ra_ticks=[15],dec_ticks=[10])),
        (EclipticGrid(None,equinox='J2000',samples=13),'mean-ecliptic-equinox',
            dict(longitude=[0,90],latitude=[0,45],longitude_ticks=[15],latitude_ticks=[10]))):
        source=grid.realize(context,None,**kwargs)
        reference=mean_reference_frame(f,axes)
        result=service.orient_geometry(source,reference)
        np.testing.assert_allclose((result['meridians'].lon_deg[0][1:-1]+180)%360-180,0,atol=1e-11)
        np.testing.assert_allclose(result['parallels'].lat_deg[0],0,atol=1e-12)
        assert len(result['tick_meridians'])==len(result['tick_parallels'])==1
        assert not hasattr(grid,'_mean_reference')
    points=CelestialPoints(None)
    points.add_equatorial_pole('north').add_ecliptic_pole('north',frame=BarycentricMeanEcliptic(equinox=Time('J2000')))
    points.add_ecliptic_cardinal_points(frame=BarycentricMeanEcliptic(equinox=Time('J2000')))
    originals=tuple(p.coord for p in points._points)
    geometry=points.realize(context,None)
    result=service.orient_geometry(geometry,f)
    np.testing.assert_allclose(result.lat_deg[1],90,atol=1e-12)
    np.testing.assert_allclose(result.lat_deg[2:],0,atol=1e-12)
    np.testing.assert_allclose((result.lon_deg[2:]-[0,90,180,270]+180)%360-180,0,atol=1e-11)
    assert tuple(p.coord for p in points._points)==originals
    fixed=CelestialPoints(None)
    fixed.add_ecliptic_pole('north',frame=BarycentricMeanEcliptic(equinox=Time('J2050')))
    with pytest.raises(ValueError,match='canonical poles/cardinals'):
        fixed.realize(context,None)
    with pytest.raises(ValueError,match='canonical source grid'):
        EquatorialGrid(None,frame='fk5',equinox='B1950').realize(context,None)
    points.add_equatorial_point(12,34)
    with pytest.raises(ValueError,match='canonical poles/cardinals'):
        points.realize(context,None)
