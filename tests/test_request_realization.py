"""Ordinary chart-request layer-realization context contracts."""

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from astropy.time import Time

from wenu.charts.product_options import ChartProductOptions
from wenu.charts.reference_policy import CelestialReferencePolicy
from wenu.charts.request import ChartObserverRequest, ChartRequest
from wenu.charts.request_realization import chart_request_realization_context
from wenu.coordinates import PositionStatus


class Observer:
    lat_deg = -33.0
    lon_deg = -71.0
    elevation_m = 100.0
    t_astropy = Time("2026-08-30T00:00:00", scale="utc")


def request(frame, *, equinox="J2000"):
    projection = "mollweide" if frame == "galactic" else "stereographic"
    return ChartRequest(
        observer=ChartObserverRequest(
            lat_deg=-33.0,
            lon_deg=-71.0,
            elevation_m=100.0,
            time="2026-08-30T00:00:00Z",
        ),
        family="all_sky" if frame == "galactic" else "planisphere",
        projection=projection,
        coordinate_frame=frame,
        product=ChartProductOptions(output=Path("chart.svg")),
        reference_policy=CelestialReferencePolicy(equinox),
    )


@pytest.mark.parametrize(
    ("frame", "expected"),
    (("horizontal", "altaz"), ("galactic", "galactic")),
)
def test_request_context_maps_product_frame_without_conflating_equinox(
    monkeypatch, frame, expected
):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )

    context = chart_request_realization_context(request(frame), Observer())
    spec = context.product_coordinate_spec

    assert spec.frame == expected
    assert spec.origin == "observer"
    assert spec.position_status is PositionStatus.APPARENT
    assert spec.epoch is None
    assert spec.equinox is None
    assert spec.instant == "2026-08-30T00:00:00.000"
    assert spec.time_scale == "utc"
    assert context.reference_equinox == "J2000"
    assert context.evaluation_instant == spec.instant
    assert context.evaluation_time_scale == "utc"
    assert context.observation.instant == spec.instant


def test_of_date_reference_is_separate_from_product_frame(monkeypatch):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )

    context = chart_request_realization_context(
        request("horizontal", equinox="of_date"), Observer()
    )

    assert context.product_coordinate_spec.frame == "altaz"
    assert context.product_coordinate_spec.equinox is None
    assert "2026-08-30" in context.reference_equinox


def test_request_context_rejects_an_unmatched_observer(monkeypatch):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: False
    )

    with pytest.raises(ValueError, match="does not match"):
        chart_request_realization_context(request("horizontal"), Observer())


def test_request_context_accepts_the_chart_view_utc_datetime_contract(
    monkeypatch,
):
    monkeypatch.setattr(
        ChartObserverRequest, "matches", lambda self, observer: True
    )
    observer = SimpleNamespace(
        utc_datetime=datetime(
            2026, 8, 30, 0, 0, tzinfo=timezone.utc
        ),
        lat_deg=-33.0,
        lon_deg=-71.0,
        elevation_m=100.0,
    )

    context = chart_request_realization_context(
        request("horizontal"), observer
    )

    assert context.observation.instant == "2026-08-30T00:00:00.000"
    assert context.observation.time_scale == "utc"


def _explicit_cluster_request():
    """Real locally installed resource bytes, explicit finite nominal domains."""
    from hashlib import sha256
    from astropy.utils import iers
    from astropy.coordinates import EarthLocation, AltAz
    from astropy import units as u
    from wenu.astrometric_observation import reception_backend_identity
    from wenu.charts.request import ClusterMotionRequest
    observer = SimpleNamespace(lat_deg=-32.44,lon_deg=-71.23,elevation_m=52.,
        utc_datetime=datetime(2017,1,2,tzinfo=timezone.utc),
        t_astropy=Time('2017-01-02T00:00:00',scale='utc'),timezone_name='UTC')
    observer.altaz_frame = AltAz(obstime=observer.t_astropy,
        location=EarthLocation.from_geodetic(-71.23*u.deg,-32.44*u.deg,52*u.m),pressure=0*u.hPa)
    selection = ClusterMotionRequest(model='nominal-observed',identifiers=('hunt:1',),
        leap_seconds_path=iers.IERS_LEAP_SECOND_FILE,
        leap_seconds_sha256=sha256(Path(iers.IERS_LEAP_SECOND_FILE).read_bytes()).hexdigest(),
        eop_path=iers.IERS_B_FILE,eop_sha256=sha256(Path(iers.IERS_B_FILE).read_bytes()).hexdigest(),
        backend_identity=reception_backend_identity(),start_jd_tt=2456300.,stop_jd_tt=2458000.,
        start_jd_tcb=2400000.,stop_jd_tcb=2500000.,height_wgs84_m=52.)
    request = ChartRequest(observer=ChartObserverRequest(time='2017-01-02T00:00:00Z',
        lat_deg=-32.44,lon_deg=-71.23,elevation_m=52.,timezone_name='UTC'),
        family='planisphere',product=ChartProductOptions(output=Path('chart.svg')),
        cluster_motion=selection)
    return request, observer


def test_cluster_selection_request_real_kernel_mixed_chart_and_refusal(tmp_path, monkeypatch):
    # Closest ordinary realization context tests; protect layer-scoped receipt
    # admission, dropped options, lookup pre-culling and hidden fallback.
    from dataclasses import replace
    import numpy as np
    from wenu.charts.request_realization import chart_cluster_motion_options
    from wenu.objects.open_clusters import OpenClusters
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.horizon import HorizonReference
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    from wenu_kernel import KernelSession
    from wenu_kernel.errors import ResourceMismatch, UnsupportedCapability
    import matplotlib.pyplot as plt
    request, observer = _explicit_cluster_request()
    options = chart_cluster_motion_options(request,observer)
    motion = options['open_clusters']['geometry']['motion']
    ids = tuple(row.identifier for row in motion.rows if row.unavailable_reason is None)[:2]
    request = replace(request, cluster_motion=replace(request.cluster_motion,identifiers=ids))
    options = chart_cluster_motion_options(request,observer)
    from wenu.charts.detail import SkyContentSelection
    subset=replace(request,content=SkyContentSelection(open_clusters=frozenset(ids[:1])))
    assert chart_cluster_motion_options(subset,observer)['open_clusters']['geometry']['selected']==ids[:1]
    empty=replace(request,content=SkyContentSelection(open_clusters=frozenset()))
    assert chart_cluster_motion_options(empty,observer)=={'open_clusters':{'enabled':False}}
    context = chart_request_realization_context(request,observer)
    layer=OpenClusters(None);layer.load()
    native=layer.position()
    before=layer.catalogue_metadata_for(layer.catalog)
    def forbidden(*args,**kwargs):
        raise AssertionError('Explicit cluster route must not pre-cull/observe lookup positions')
    monkeypatch.setattr(layer,'spherical_geometry',forbidden)
    result=layer.realize(context,observer,**options['open_clusters']['geometry'])
    assert result.ids.tolist()==list(ids) and result.coordinate_spec.frame=='altaz'
    sphere=CelestialSphere(observer);sphere.add(layer);sphere.add(HorizonReference())
    figure,ax=plt.subplots(figsize=(3,3),dpi=90)
    try:
        drawn=sphere.draw_chart(projection=StereographicProjection(),renderer=MatplotlibRenderer(ax),
            realization_context=context,layer_options=options)
        assert len(drawn.layers)==2
        output=tmp_path/'mixed.svg';figure.savefig(output)
        assert output.stat().st_size>1000
    finally:plt.close(figure)
    for bad in (replace(request.cluster_motion,height_wgs84_m=50.),
                replace(request.cluster_motion,eop_sha256='0'*64),
                replace(request.cluster_motion,backend_identity=('bad',)*3+('0'*64,))):
        with pytest.raises((ValueError,ResourceMismatch)):
            chart_cluster_motion_options(replace(request,cluster_motion=bad),observer)
    wrong=replace(context,observation=replace(context.observation,longitude_deg=0.))
    with pytest.raises(ValueError,match='match the chart'):
        layer.realize(wrong,observer,**options['open_clusters']['geometry'])
    def refused(*args,**kwargs):raise UnsupportedCapability('injected selected request refusal')
    with monkeypatch.context() as patch:
        patch.setattr(KernelSession,'evaluate',refused)
        with pytest.raises(UnsupportedCapability,match='injected selected'):
            layer.realize(context,observer,**options['open_clusters']['geometry'])
    assert layer.catalogue_metadata_for(layer.catalog)==before
    np.testing.assert_array_equal(layer.position().lon_deg,native.lon_deg)



def test_cluster_model_rejects_unsupported_frame_and_unqualified_height():
    from dataclasses import replace
    request, _ = _explicit_cluster_request()
    with pytest.raises(ValueError,match='horizontal'):
        replace(request, family='all_sky',coordinate_frame='galactic',projection='mollweide')
    with pytest.raises(ValueError,match='height_wgs84_m'):
        replace(request.cluster_motion,height_wgs84_m=None)
