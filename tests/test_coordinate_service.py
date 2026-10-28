from __future__ import annotations

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricTrueEcliptic,
    EarthLocation,
    FK4,
    FK5,
    Galactic,
    ICRS,
    SkyCoord,
)
from astropy.time import Time

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    ICRS_ASTROMETRIC_SPEC,
    ObservationContext,
    PositionStatus,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


GALACTIC_SPEC = CoordinateSpec(
    frame="galactic",
    origin="galactic-center",
    position_status=PositionStatus.ASTROMETRIC,
    provider="astropy",
)


def _zodiac_tool():
    import importlib.util
    from pathlib import Path
    path = Path(__file__).parents[1] / "tools/render_zodiac_constellations.py"
    spec = importlib.util.spec_from_file_location("zodiac_coordinate_consumer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _zodiac_observer():
    from types import SimpleNamespace
    location = EarthLocation.from_geodetic(-71 * u.deg, -33 * u.deg, 52 * u.m)
    instant = Time("2026-08-16T01:00:00", scale="utc")
    return SimpleNamespace(altaz_frame=AltAz(location=location, obstime=instant, pressure=0*u.hPa),
                           t_astropy=instant, lon_deg=-71., lat_deg=-33., elevation_m=52.)


def test_zodiac_maintenance_coordinates_match_retained_astropy_frames():
    from types import SimpleNamespace
    from astropy.coordinates import BarycentricMeanEcliptic
    module, observer = _zodiac_tool(), _zodiac_observer()
    expected = SkyCoord(lon=0*u.deg, lat=90*u.deg,
        frame=BarycentricMeanEcliptic(equinox=Time("J2000"))).transform_to(observer.altaz_frame)
    actual = module._north_ecliptic_pole(observer)
    assert actual.separation(expected).to_value(u.arcsec) < 1e-7
    view = SimpleNamespace(chart=SimpleNamespace(center_alt_deg=35., center_az_deg=123.), observer=observer)
    expected = SkyCoord(alt=35*u.deg, az=123*u.deg, frame=observer.altaz_frame).transform_to(FK5(equinox=Time("J2000")))
    actual = module._center_coordinate(view)
    assert actual.separation(expected).to_value(u.arcsec) < 1e-7


@pytest.mark.parametrize("route", ("pole", "title"))
def test_zodiac_maintenance_consumes_returned_coordinates_and_warm_refusal(route, monkeypatch):
    from types import SimpleNamespace
    from wenu.charts.regional import target_up_position_angle
    module, observer = _zodiac_tool(), _zodiac_observer()
    returned = (112., 25.) if route == "pole" else (234.5, -12.25)
    calls, views = [], []
    refuse = False
    def transform(self, source, target, observation=None):
        calls.append((source, target, observation))
        assert target.frame == ("altaz" if route == "pole" else "fk5")
        assert observation.instant == observer.t_astropy.utc.isot
        assert target.instant == observation.instant and target.time_scale == observation.time_scale
        if refuse: raise RuntimeError("maintenance coordinate refusal")
        return SphericalPoints(lon_deg=np.array([returned[0]]), lat_deg=np.array([returned[1]]), coordinate_spec=target)
    monkeypatch.setattr(CoordinateService, "transform_skycoord", transform)
    view = SimpleNamespace(chart=SimpleNamespace(center_alt_deg=35., center_az_deg=123.), observer=observer)
    def get_view(*args, **kwargs):
        views.append(kwargs)
        return view
    monkeypatch.setattr(module, "get_chart_view", get_view)
    def consume():
        return (module._chart_view(object(), observer, None, "Ari", False) if route == "pole"
                else module._title(view, "Ari"))
    result = consume()
    if route == "pole":
        expected = target_up_position_angle(center_alt_deg=35., center_az_deg=123.,
                    target_alt_deg=returned[1], target_az_deg=returned[0])
        assert views[-1]["position_angle_deg"] == pytest.approx(expected)
        assert result is view
    else:
        assert result == "Aries — RA 15:38, Dec -12:15"
    assert len(calls) == 1
    refuse = True
    with pytest.raises(RuntimeError, match="maintenance coordinate refusal"):
        consume()


@pytest.mark.parametrize("refusal_at", (None, 1, 2))
def test_zodiac_review_request_consumes_service_angle_title_and_closes_on_refusal(tmp_path, monkeypatch, refusal_at):
    from types import SimpleNamespace
    module, observer = _zodiac_tool(), _zodiac_observer()
    closed, views, drawings, calls = [], [], [], []
    observer.close = lambda: closed.append(True)
    monkeypatch.setattr(module, "Observer", lambda **options: observer)
    monkeypatch.setattr(module, "generate_celestial_sphere", object)
    def transform(self, source, target, observation=None):
        calls.append(target.frame)
        if len(calls) == refusal_at: raise RuntimeError("review service refusal")
        lon, lat = (112., 25.) if target.frame == "altaz" else (234.5, -12.25)
        return SphericalPoints(lon_deg=np.array([lon]), lat_deg=np.array([lat]), coordinate_spec=target)
    monkeypatch.setattr(CoordinateService, "transform_skycoord", transform)
    def get_view(sky, active, **options):
        assert active is observer
        views.append(options)
        return SimpleNamespace(observer=active, family="regional",
            chart=SimpleNamespace(center_alt_deg=35., center_az_deg=123.))
    monkeypatch.setattr(module, "get_chart_view", get_view)
    def draw(view, arguments, **options):
        drawings.append((arguments, options))
        return (SimpleNamespace(output=arguments.output),)
    monkeypatch.setattr(module, "draw_chart_view_from_arguments", draw)
    arguments = module.parser().parse_args(["--constellations", "Ari", "--output", str(tmp_path)])
    if refusal_at:
        with pytest.raises(RuntimeError, match="review service refusal"):
            module.render_zodiac(arguments)
        assert drawings == []
    else:
        assert module.render_zodiac(arguments) == (tmp_path / "01-ari.png",)
        assert calls == ["altaz", "fk5"]
        assert drawings[0][1]["title"] == "Aries — RA 15:38, Dec -12:15"
        assert views[-1]["position_angle_deg"] == pytest.approx(module.target_up_position_angle(
            center_alt_deg=35., center_az_deg=123., target_alt_deg=25., target_az_deg=112.))
    assert closed == [True]


def test_points_match_astropy_and_preserve_semantics():
    points = SphericalPoints(
        lon_deg=np.array([0.0, 83.6331]),
        lat_deg=np.array([0.0, 22.0145]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        ids=np.array(["origin", "crab"], dtype=object),
        labels=np.array(["O", "M1"], dtype=object),
        names=np.array(["Origin", "Crab"], dtype=object),
        metadata={"family": "test"},
    )

    transformed = CoordinateService().transform(points, GALACTIC_SPEC)
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=ICRS(),
    ).transform_to(Galactic()).spherical

    assert isinstance(transformed, SphericalPoints)
    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )
    assert transformed.coordinate_spec is GALACTIC_SPEC
    np.testing.assert_array_equal(transformed.ids, points.ids)
    np.testing.assert_array_equal(transformed.labels, points.labels)
    np.testing.assert_array_equal(transformed.names, points.names)
    assert transformed.metadata == points.metadata
    assert transformed.ids is not points.ids
    assert transformed.metadata is not points.metadata


def test_icrs_galactic_round_trip_is_coincident():
    points = SphericalPoints(
        lon_deg=np.array([12.0, 120.0, 310.0]),
        lat_deg=np.array([-60.0, 0.0, 75.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )
    service = CoordinateService()

    galactic = service.transform(points, GALACTIC_SPEC)
    restored = service.transform(galactic, ICRS_ASTROMETRIC_SPEC)

    np.testing.assert_allclose(restored.lon_deg, points.lon_deg, atol=1e-10)
    np.testing.assert_allclose(restored.lat_deg, points.lat_deg, atol=1e-10)


def test_curves_preserve_segmentation_closure_and_semantics():
    curves = SphericalCurves(
        lon_deg=(np.array([0.0, 1.0]), np.array([10.0, 20.0, 30.0])),
        lat_deg=(np.array([2.0, 3.0]), np.array([-5.0, 0.0, 5.0])),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        closed=np.array([False, True]),
        ids=np.array(["a", "b"], dtype=object),
        names=np.array(["first", "second"], dtype=object),
        metadata={"role": "grid"},
    )

    transformed = CoordinateService().transform(curves, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalCurves)
    assert tuple(map(len, transformed.lon_deg)) == (2, 3)
    np.testing.assert_array_equal(transformed.closed, curves.closed)
    np.testing.assert_array_equal(transformed.ids, curves.ids)
    np.testing.assert_array_equal(transformed.names, curves.names)
    assert transformed.metadata == curves.metadata


def test_polygons_preserve_ring_topology():
    polygons = SphericalPolygons(
        lon_deg=(np.array([0.0, 1.0, 0.0]), np.array([20.0, 21.0, 21.0, 20.0])),
        lat_deg=(np.array([0.0, 0.0, 1.0]), np.array([5.0, 5.0, 6.0, 6.0])),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        ids=np.array(["triangle", "box"], dtype=object),
    )

    transformed = CoordinateService().transform(polygons, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalPolygons)
    assert tuple(map(len, transformed.lon_deg)) == (3, 4)
    np.testing.assert_array_equal(transformed.ids, polygons.ids)


def test_grid_preserves_component_names_and_component_semantics():
    component = SphericalCurves(
        lon_deg=(np.array([0.0, 10.0]),),
        lat_deg=(np.array([0.0, 5.0]),),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        names=np.array(["meridian"], dtype=object),
    )
    grid = SphericalGrid(
        components={"meridians": component},
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        metadata={"grid": "reference"},
    )

    transformed = CoordinateService().transform(grid, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalGrid)
    assert tuple(transformed.components) == ("meridians",)
    assert transformed.coordinate_spec is GALACTIC_SPEC
    assert transformed["meridians"].coordinate_spec is GALACTIC_SPEC
    np.testing.assert_array_equal(
        transformed["meridians"].names, component.names
    )
    assert transformed.metadata == grid.metadata


def test_altaz_requires_explicit_observation_context():
    points = SphericalPoints(
        lon_deg=np.array([10.0]),
        lat_deg=np.array([20.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )
    altaz_spec = CoordinateSpec(
        frame="altaz",
        origin="observer",
        position_status=PositionStatus.APPARENT,
        instant="2026-08-28T00:00:00",
        time_scale="utc",
    )

    with pytest.raises(ValueError, match="ObservationContext"):
        CoordinateService().transform(points, altaz_spec)


def test_altaz_matches_astropy_for_explicit_observation():
    context = ObservationContext(
        longitude_deg=-71.5,
        latitude_deg=-33.0,
        elevation_m=100.0,
        instant="2026-08-28T00:00:00",
    )
    altaz_spec = CoordinateSpec(
        frame="altaz",
        origin="observer",
        position_status=PositionStatus.APPARENT,
        instant=context.instant,
        time_scale=context.time_scale,
    )
    points = SphericalPoints(
        lon_deg=np.array([83.6331]),
        lat_deg=np.array([22.0145]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )

    transformed = CoordinateService().transform(
        points, altaz_spec, observation=context
    )
    frame = AltAz(
        obstime=Time(context.instant, scale=context.time_scale),
        location=EarthLocation.from_geodetic(
            context.longitude_deg * u.deg,
            context.latitude_deg * u.deg,
            context.elevation_m * u.m,
        ),
        pressure=0.0 * u.hPa,
    )
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=ICRS(),
    ).transform_to(frame).spherical

    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )


@pytest.mark.parametrize(
    "spec, message",
    [
        (
            CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                longitude_unit="rad",
            ),
            "degree",
        ),
        (
            CoordinateSpec(
                frame="unsupported",
                origin="unknown",
            ),
            "Unsupported astronomical frame",
        ),
    ],
)
def test_unsupported_coordinate_contracts_fail_explicitly(spec, message):
    points = SphericalPoints(
        lon_deg=np.array([0.0]),
        lat_deg=np.array([0.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )

    with pytest.raises(ValueError, match=message):
        CoordinateService().transform(points, spec)


@pytest.mark.parametrize(
    "source_spec, source_frame",
    [
        (
            CoordinateSpec(
                frame="fk4",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="B1875.0",
            ),
            FK4(equinox=Time("B1875.0")),
        ),
        (
            CoordinateSpec(
                frame="fk5",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="J2050.0",
            ),
            FK5(equinox=Time("J2050.0")),
        ),
        (
            CoordinateSpec(
                frame="barycentric-true-ecliptic",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="J2050.0",
            ),
            BarycentricTrueEcliptic(equinox=Time("J2050.0")),
        ),
    ],
)
def test_reference_frames_match_astropy(source_spec, source_frame):
    points = SphericalPoints(
        lon_deg=np.array([15.0, 120.0]),
        lat_deg=np.array([-20.0, 35.0]),
        coordinate_spec=source_spec,
    )

    transformed = CoordinateService().transform(
        points, ICRS_ASTROMETRIC_SPEC
    )
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=source_frame,
    ).transform_to(ICRS()).spherical

    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )



@pytest.mark.parametrize('axes',['mean-equator-equinox','mean-ecliptic-equinox'])
@pytest.mark.parametrize('kind',['points','curves','polygons','grid'])
def test_mean_axis_geometry_preserves_native_semantics_and_matches_admitted_vectors(axes,kind):
    """Protect the common geometry seam, not a new frame-model qualification."""
    from dataclasses import replace
    from wenu.astrometric_coordinates import LongTermFrame,LONG_TERM_FRAME_POLICY
    from wenu_kernel.records import TimePoint,TimeSpan
    frame=LongTermFrame(equinox=TimePoint(-1200955,0.,'tt'),
        validity=TimeSpan(TimePoint(-1200956,0.,'tt'),TimePoint(2451546,0.,'tt')),
        axes=axes,model_policy=LONG_TERM_FRAME_POLICY)
    spec=replace(ICRS_ASTROMETRIC_SPEC,instant='independent-TCB-event',time_scale='tcb',epoch='source epoch')
    lon=np.array([359.9,17.,np.nan,0.]);lat=np.array([10.,-30.,np.nan,90.])
    common=dict(coordinate_spec=spec,ids=['a','b'],labels=['A','B'],metadata={'retained':'source'})
    if kind=='points':
        g=SphericalPoints(lon,lat,coordinate_spec=spec,ids=['a','b','c','d'],metadata=common['metadata'])
    else:
        owner=SphericalPolygons if kind=='polygons' else SphericalCurves
        g=owner((lon,lon[[0,1,3]] if kind=='polygons' else lon[:2]),
            (lat,lat[[0,1,3]] if kind=='polygons' else lat[:2]),**common)
        if kind=='grid':g=SphericalGrid({'reference':g},coordinate_spec=spec,metadata={'grid':'retained'})
    service=CoordinateService();result=service.orient_geometry(g,frame)
    item=result['reference'] if kind=='grid' else result
    original=g['reference'] if kind=='grid' else g
    actual_lon=item.lon_deg if kind=='points' else item.lon_deg[0]
    actual_lat=item.lat_deg if kind=='points' else item.lat_deg[0]
    def xyz(a,b):
        a,b=np.deg2rad(a),np.deg2rad(b)
        return np.array([np.cos(b)*np.cos(a),np.cos(b)*np.sin(a),np.sin(b)]).T
    valid=np.isfinite(lon)
    expected=np.array([frame.rotate(tuple(map(float,v))) for v in xyz(lon[valid],lat[valid])])
    np.testing.assert_allclose(xyz(actual_lon[valid],actual_lat[valid]),expected,atol=6e-16)
    assert np.isnan(actual_lon[2]) and np.isnan(actual_lat[2])
    assert item.coordinate_spec.instant==spec.instant and item.coordinate_spec.time_scale=='tcb'
    assert item.coordinate_spec.equinox.endswith(' TT') and item.coordinate_spec.epoch=='source epoch'
    assert item.metadata['source_coordinate_spec']==spec and item.metadata['retained']=='source'
    np.testing.assert_array_equal(item.ids,original.ids)
    assert result is not g and item.metadata is not original.metadata
    back=service.orient_geometry(result,frame,inverse=True)
    restored=back['reference'] if kind=='grid' else back
    a=restored.lon_deg if kind=='points' else restored.lon_deg[0]
    b=restored.lat_deg if kind=='points' else restored.lat_deg[0]
    np.testing.assert_allclose(xyz(a[valid],b[valid]),xyz(lon[valid],lat[valid]),atol=7e-16)
    with pytest.raises(ValueError,match='matching barycentric'):
        service.orient_geometry(result,frame)
    np.testing.assert_array_equal(original.lon_deg if kind=='points' else original.lon_deg[0],lon)
