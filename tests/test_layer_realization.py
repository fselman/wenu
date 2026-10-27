"""Minimal layer-realization context and controlled-provider contracts."""

from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    PositionStatus,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.positions import PositionProvider
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer


class IdentityProjection:
    def project_geometry(self, geometry):
        return geometry


class RecordingRenderer:
    def __init__(self):
        self.drawn = []

    def draw(self, geometry, **options):
        self.drawn.append((geometry, options))
        return (object(),)


class LegacyLayer(SkyLayer):
    layer_name = "legacy"

    def __init__(self):
        self.calls = []

    def spherical_geometry(self, observer, **options):
        self.calls.append((observer, options))
        return SphericalPoints(
            lon_deg=np.asarray([1.0]),
            lat_deg=np.asarray([2.0]),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                provider="legacy test layer",
            ),
        )


class ControlledProvider:
    def __init__(self):
        self.instants = []

    def position(self, instant=None):
        self.instants.append(instant)
        return SphericalPoints(
            lon_deg=np.asarray([10.0]),
            lat_deg=np.asarray([20.0]),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                position_status=PositionStatus.GEOMETRIC,
                instant=instant,
                time_scale="tt",
                provider="controlled test provider",
                provenance=("deterministic test state",),
            ),
            ids=np.asarray(["controlled-body"], dtype=object),
        )


class ControlledDynamicLayer(SkyLayer):
    layer_name = "controlled_dynamic"

    def __init__(self, provider):
        self.provider = provider
        self.realizations = []

    def spherical_geometry(self, observer, **options):
        raise AssertionError(
            "explicit dynamic realization must not use the legacy call"
        )

    def realize(self, context, observer, **geometry_options):
        self.realizations.append(
            (context, observer, dict(geometry_options))
        )
        native = self.provider.position(context.evaluation_instant)
        return CoordinateService().transform(
            native,
            context.product_coordinate_spec,
            observation=context.observation,
        )


def _context():
    instant = "2026-08-29T21:00:00"
    return LayerRealizationContext(
        product_coordinate_spec=CoordinateSpec(
            frame="galactic",
            origin="galactic-center",
            position_status=PositionStatus.GEOMETRIC,
            instant=instant,
            time_scale="tt",
            provider="controlled test provider",
            provenance=("deterministic test state",),
        ),
        observation=ObservationContext(
            longitude_deg=-71.0,
            latitude_deg=-32.0,
            elevation_m=100.0,
            instant=instant,
            time_scale="tt",
        ),
        evaluation_instant=instant,
        evaluation_time_scale="TT",
        reference_equinox="J2000.0",
    )


def _draw(sphere, *, observer, realization_context=None, layer_options=None):
    return sphere.draw_chart(
        projection=IdentityProjection(),
        renderer=RecordingRenderer(),
        observer=observer,
        realization_context=realization_context,
        layer_options=layer_options,
    )


def test_realization_context_is_immutable_and_normalized():
    context = _context()

    assert context.evaluation_time_scale == "tt"
    assert context.reference_equinox == "J2000.0"
    with pytest.raises(FrozenInstanceError):
        context.evaluation_instant = "later"


def test_only_explicit_static_icrs_context_allows_absent_observer():
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    assert context.is_native_icrs
    # Explicit native epoch directions now share the observer-free ICRS axes.
    epoch = replace(context, evaluation_instant="2026-01-01", evaluation_time_scale="tt")
    assert epoch.is_native_icrs
    _draw(CelestialSphere(None), observer=None, realization_context=epoch)
    for altered in (replace(context, reference_equinox="J2000.0"),
                    replace(context, product_coordinate_spec=replace(NATIVE_ICRS_SPEC, frame="galactic")),
                    _context()):
        assert not altered.is_native_icrs
        with pytest.raises(TypeError, match="requires an observer"):
            _draw(CelestialSphere(None), observer=None, realization_context=altered)
    with pytest.raises(TypeError, match="requires an observer"):
        _draw(CelestialSphere(None), observer=None)
    legacy = LegacyLayer()
    sphere = CelestialSphere(None); sphere.add(legacy)
    with pytest.raises(TypeError, match="does not support native ICRS"):
        _draw(sphere, observer=None, realization_context=context)
    assert legacy.calls == []


def test_native_icrs_rejects_misidentified_geometry_before_projection():
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    class IncorrectLayer(LegacyLayer):
        def realize(self, context, observer, **options):
            return self.spherical_geometry(observer, **options)
    sphere = CelestialSphere(None); sphere.add(IncorrectLayer())
    with pytest.raises(ValueError, match="matching barycentric astrometry"):
        _draw(sphere, observer=None, realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC))


@pytest.mark.parametrize(
    ("values", "error", "message"),
    [
        (
            {"product_coordinate_spec": object()},
            TypeError,
            "product_coordinate_spec",
        ),
        (
            {
                "product_coordinate_spec": CoordinateSpec(
                    frame="icrs",
                    origin="solar-system-barycenter",
                ),
                "observation": object(),
            },
            TypeError,
            "observation",
        ),
        (
            {
                "product_coordinate_spec": CoordinateSpec(
                    frame="icrs",
                    origin="solar-system-barycenter",
                ),
                "evaluation_instant": "2026-08-29T21:00:00",
            },
            ValueError,
            "supplied together",
        ),
    ],
)
def test_realization_context_rejects_incomplete_scientific_identity(
    values, error, message,
):
    with pytest.raises(error, match=message):
        LayerRealizationContext(**values)


def test_draw_chart_without_context_keeps_the_exact_legacy_layer_call():
    observer = object()
    layer = LegacyLayer()
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        layer_options={"legacy": {"geometry": {"sample": 7}}},
    )

    assert layer.calls == [(observer, {"sample": 7})]
    assert result.layers[0].spherical.lon_deg.tolist() == [1.0]


def test_default_realization_adapter_preserves_unmigrated_layers():
    observer = object()
    context = _context()
    layer = LegacyLayer()
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        realization_context=context,
        layer_options={"legacy": {"geometry": {"sample": 11}}},
    )

    assert layer.calls == [(observer, {"sample": 11})]
    assert result.layers[0].spherical.coordinate_spec.frame == "icrs"


def test_controlled_provider_enters_before_projection_through_service():
    observer = object()
    context = _context()
    provider = ControlledProvider()
    layer = ControlledDynamicLayer(provider)
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        realization_context=context,
        layer_options={
            "controlled_dynamic": {"geometry": {"selected": "body"}}
        },
    )

    assert isinstance(provider, PositionProvider)
    assert provider.instants == [context.evaluation_instant]
    assert layer.realizations == [
        (context, observer, {"selected": "body"})
    ]
    spherical = result.layers[0].spherical
    assert spherical.coordinate_spec == context.product_coordinate_spec
    assert spherical.ids.tolist() == ["controlled-body"]
    assert np.isfinite(spherical.lon_deg).all()
    assert np.isfinite(spherical.lat_deg).all()


def test_draw_chart_rejects_an_untyped_realization_context():
    sphere = CelestialSphere(None)
    sphere.add(LegacyLayer())

    with pytest.raises(TypeError, match="LayerRealizationContext"):
        _draw(
            sphere,
            observer=object(),
            realization_context=object(),
        )


@pytest.mark.parametrize('instant,scale', [('wrong', 'tcb'), ('J2050.0', 'tt'), (None, None)])
def test_native_epoch_guard_rejects_mismatched_layer_time_before_projection(instant, scale):
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    context = LayerRealizationContext(NATIVE_ICRS_SPEC,
        evaluation_instant='J2050.0', evaluation_time_scale='tcb')
    class EpochLayer(LegacyLayer):
        def realize(self, context, observer, **options):
            return SphericalPoints(lon_deg=[1.], lat_deg=[2.], coordinate_spec=CoordinateSpec(
                frame='icrs', origin='solar-system-barycenter', position_status=PositionStatus.ASTROMETRIC,
                instant=instant, time_scale=scale))
    sphere = CelestialSphere(None); sphere.add(EpochLayer())
    if instant is None:
        # Static sources are retained without pretending they were propagated.
        _draw(sphere, observer=None, realization_context=context)
    else:
        with pytest.raises(ValueError, match='matching barycentric'):
            _draw(sphere, observer=None, realization_context=context)


def test_mean_view_is_applied_once_before_guard_prepare_and_render(monkeypatch):
    from wenu.astrometric_coordinates import LongTermFrame,LONG_TERM_FRAME_POLICY
    from wenu_kernel.records import TimePoint,TimeSpan
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    from wenu.coordinates import ICRS_ASTROMETRIC_SPEC
    frame=LongTermFrame(equinox=TimePoint(-1200955,0.,'tt'),
        validity=TimeSpan(TimePoint(-1200956,0.,'tt'),TimePoint(2451546,0.,'tt')),
        axes='mean-equator-equinox',model_policy=LONG_TERM_FRAME_POLICY)
    source=SphericalPoints([12.],[34.],coordinate_spec=ICRS_ASTROMETRIC_SPEC)
    class Native(SkyLayer):
        def realize(self,context,observer,**options):return source
        def spherical_geometry(self,observer):raise AssertionError('No observer fallback')
    sphere=CelestialSphere(None);layer=sphere.add(Native());seen=[]
    expected=CoordinateService().orient_geometry(source,frame)
    def guard(g):
        seen.append('guard')
        assert g.coordinate_spec.frame==frame.axes
        np.testing.assert_allclose(g.lon_deg,expected.lon_deg,atol=1e-12)
        return g
    def prepare(g,p):
        seen.append('prepare');assert g is p
        return p
    result=sphere.draw_chart(projection=IdentityProjection(),renderer=RecordingRenderer(),
        realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC,orientation=frame),
        project_geometry=guard,layer_options={layer:dict(prepare=prepare)})
    assert seen==['guard','prepare']
    assert result.layers[0].spherical is not source
    assert source.coordinate_spec.frame=='icrs'
    # An omitted view is visible to the independent guard/preparation contract.
    monkeypatch.setattr(CoordinateService,'orient_geometry',lambda self,g,f:g)
    with pytest.raises(AssertionError):
        sphere.draw_chart(projection=IdentityProjection(),renderer=RecordingRenderer(),
            realization_context=LayerRealizationContext(NATIVE_ICRS_SPEC,orientation=frame),project_geometry=guard)


def test_dated_label_region_preparation_uses_the_common_view_seam(monkeypatch):
    from types import SimpleNamespace
    from wenu.astrometric_coordinates import LongTermFrame,LONG_TERM_FRAME_POLICY
    from wenu_kernel.records import TimePoint,TimeSpan
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    from wenu.coordinates import ICRS_ASTROMETRIC_SPEC
    from wenu.geometry.spherical import SphericalPolygons
    from wenu.geometry.projected import ProjectedCurve,ProjectedPoints
    from wenu.geometry.viewport import Viewport
    from wenu.projections import StereographicProjection
    from wenu.charts import constellation_label_placement as placement
    frame=LongTermFrame(equinox=TimePoint(-1200955,0.,'tt'),
        validity=TimeSpan(TimePoint(-1200956,0.,'tt'),TimePoint(2451546,0.,'tt')),
        axes='mean-equator-equinox',model_policy=LONG_TERM_FRAME_POLICY)
    native=SphericalPolygons(([0.,10.,10.,0.],),([0.,0.,10.,10.],),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,names=['ORI'])
    expected=CoordinateService().orient_geometry(native,frame)
    class Regions:
        def realize(self,*args,**kwargs):return native
    labels=object();sky=SimpleNamespace(constellation_labels=labels,constellation_boundaries=Regions(),observer=None)
    context=LayerRealizationContext(NATIVE_ICRS_SPEC,orientation=frame)
    seen=[];project=placement.project_geometry_for_viewport
    def guarded(g,**kwargs):
        assert g.coordinate_spec.frame==frame.axes
        np.testing.assert_allclose(g.lon_deg[0],expected.lon_deg[0],atol=1e-12)
        seen.append(g)
        return project(g,**kwargs)
    monkeypatch.setattr(placement,'project_geometry_for_viewport',guarded)
    options=placement.apply_visible_constellation_label_anchors({},sky=sky,
        projection=StereographicProjection(),viewport=Viewport.centered(width=4,height=4),
        boundary=ProjectedCurve([-2,2,2,-2],[-2,-2,2,2],closed=True),realization_context=context)
    prepared=options[labels]['prepare'](None,ProjectedPoints([0.],[0.],labels=['ORI']))
    assert seen and prepared.metadata['visible_region_anchors']
    import wenu.sky.realization as owner
    monkeypatch.setattr(owner,'realize_layer_geometry',lambda layer,context,observer,**k:layer.realize(context,observer,**k))
    with pytest.raises(AssertionError):options[labels]['prepare'](None,ProjectedPoints([0.],[0.],labels=['ORI']))
