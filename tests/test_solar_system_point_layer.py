"""Shared symbolic Solar-System point-layer contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor
from wenu.sky.solar_system_points import (
    EphemerisSourceBinding,
    SolarSystemPointDescriptor,
    SolarSystemPointLayer,
    _provider_gas_tail_position_angle,
)
from wenu.solar_system_directions import ApparentCorrectionPolicy


def context():
    observation = ObservationContext(
        longitude_deg=-71.0,
        latitude_deg=-33.0,
        elevation_m=52.0,
        instant="2026-08-30T00:00:00.000",
        time_scale="utc",
    )
    return LayerRealizationContext(
        product_coordinate_spec=CoordinateSpec(
            frame="altaz",
            origin="observer",
            position_status=PositionStatus.APPARENT,
            instant=observation.instant,
            time_scale=observation.time_scale,
        ),
        observation=observation,
        evaluation_instant=observation.instant,
        evaluation_time_scale=observation.time_scale,
    )


def test_descriptor_freezes_body_identity_centre_and_correction_policy():
    descriptor = SolarSystemPointDescriptor(
        target="moon",
        entity_key="moon",
        display_name="Moon",
        selection_key="moon",
    )

    assert descriptor.target == "moon"
    assert descriptor.entity_key == "moon"
    assert descriptor.display_name == "Moon"
    assert descriptor.selection_key == "moon"
    assert descriptor.centre == "solar system barycenter"
    assert isinstance(
        descriptor.correction_policy,
        ApparentCorrectionPolicy,
    )
    with pytest.raises(AttributeError):
        descriptor.target = "venus"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("target", "", ValueError),
        ("entity_key", 301, TypeError),
        ("display_name", " ", ValueError),
        ("selection_key", None, TypeError),
        ("centre", "", ValueError),
    ),
)
def test_descriptor_rejects_missing_or_untyped_identity(field, value, error):
    values = {
        "target": "moon",
        "entity_key": "moon",
        "display_name": "Moon",
        "selection_key": "moon",
        "centre": "solar system barycenter",
    }
    values[field] = value
    with pytest.raises(error):
        SolarSystemPointDescriptor(**values)


def test_shared_layer_realizes_a_body_without_projection_or_rendering():
    descriptor = SolarSystemBodyDescriptor(
        target="venus",
        entity_key="venus",
        display_name="Venus",
        selection_key="venus",
        astronomical_symbol="♀",
    )
    calls = []
    source = SimpleNamespace(
        resource=SimpleNamespace(sha256="b" * 64)
    )
    observer_state = object()
    astrometric = object()
    apparent = SimpleNamespace(
        geometry=SphericalPoints(
            np.asarray((358.0,)),
            np.asarray((2.0,)),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="observer",
                position_status=PositionStatus.APPARENT,
                instant="2026-08-30T00:00:00.000",
                time_scale="utc",
                provenance=("accepted apparent Venus",),
            ),
        )
    )
    transformed = object()

    class Astrometric:
        def direction(self, actual_source, request, actual_state):
            calls.append("astrometric")
            assert actual_source is source
            assert actual_state is observer_state
            assert request.target == "venus"
            assert request.centre == "solar system barycenter"
            return astrometric

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            calls.append("apparent")
            assert value is astrometric
            assert policy is descriptor.correction_policy
            return apparent

    class Coordinates:
        def transform(self, geometry, target, observation):
            calls.append("transform")
            assert geometry.ids.tolist() == ["venus"]
            assert geometry.labels.tolist() == ["♀"]
            assert geometry.names.tolist() == ["Venus"]
            assert geometry.metadata["semantic_entity_keys"].tolist() == [
                "venus"
            ]
            assert geometry.metadata[
                "semantic_entity_display_names"
            ].tolist() == ["Venus"]
            assert geometry.metadata["ephemeris_sha256"] == "b" * 64
            assert geometry.metadata["apparent_provenance"] == (
                "accepted apparent Venus",
            )
            assert target is realization.product_coordinate_spec
            assert observation is realization.observation
            return transformed

    realization = context()
    observer = object()
    layer = SolarSystemPointLayer(
        descriptor,
        source_factory=lambda value: source,
        observer_state_factory=lambda value, *, source: observer_state,
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )

    assert layer.realize(
        realization,
        observer,
        selected={"mercury", "venus"},
    ) is transformed
    assert calls == ["astrometric", "apparent", "transform"]


def test_shared_layer_validates_selection_context_and_geometry_options():
    descriptor = SolarSystemPointDescriptor(
        target="moon",
        entity_key="moon",
        display_name="Moon",
        selection_key="moon",
    )
    layer = SolarSystemPointLayer(descriptor)

    with pytest.raises(TypeError, match="typed LayerRealizationContext"):
        layer.spherical_geometry(object())
    with pytest.raises(TypeError, match="LayerRealizationContext"):
        layer.realize(object(), object())
    with pytest.raises(ValueError, match="contain moon"):
        layer.realize(context(), object(), selected={"venus"})
    with pytest.raises(TypeError, match="accepts no geometry options"):
        layer.realize(context(), object(), unexpected=True)


def test_shared_layer_accepts_distinct_target_and_observer_sources():
    descriptor = SolarSystemBodyDescriptor(
        target="ceres",
        entity_key="ceres",
        display_name="Ceres",
        selection_key="ceres",
        canonical_designation="(1) Ceres",
    )
    target_source = SimpleNamespace(
        resource=SimpleNamespace(primary=SimpleNamespace(sha256="c" * 64))
    )
    observer_source = SimpleNamespace(resource=object())
    astrometric = object()
    apparent = SimpleNamespace(
        geometry=SphericalPoints(
            np.asarray((10.0,)),
            np.asarray((20.0,)),
            coordinate_spec=CoordinateSpec(
                frame="icrs", origin="observer",
                position_status=PositionStatus.APPARENT,
            ),
        )
    )

    class Astrometric:
        def direction(self, source, request, observer_state):
            assert source is target_source
            assert observer_state == "observer-state"
            return astrometric

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            assert value is astrometric
            assert source is observer_source
            return apparent

    class Coordinates:
        def transform(self, geometry, target, observation):
            assert geometry.labels.tolist() == ["(1) Ceres"]
            assert geometry.metadata["ephemeris_sha256"] == "c" * 64
            return geometry

    layer = SolarSystemPointLayer(
        descriptor,
        source_resolver=lambda body, observer: EphemerisSourceBinding(
            target_source, observer_source
        ),
        observer_state_factory=lambda observer, *, source: (
            "observer-state" if source is observer_source else None
        ),
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )
    result = layer.realize(context(), object(), selected={"ceres"})
    assert result.labels.tolist() == ["(1) Ceres"]


def test_comet_layer_realizes_simultaneous_sun_and_tail_reference():
    descriptor = SolarSystemBodyDescriptor(
        target="2p",
        entity_key="comet_2p",
        display_name="2P/Encke",
        selection_key="2p",
        body_class="comet",
        canonical_designation="2P/Encke",
        iau_number=2,
    )
    target_source = SimpleNamespace(
        resource=SimpleNamespace(primary=SimpleNamespace(sha256="d" * 64))
    )
    observer_source = object()
    coordinate_spec = CoordinateSpec(
        frame="icrs", origin="observer",
        position_status=PositionStatus.APPARENT,
        provenance=("test apparent",),
    )

    class Astrometric:
        def direction(self, source, request, observer_state):
            assert observer_state == "observer-state"
            if request.target == "sun":
                assert source is observer_source
            else:
                assert source is target_source
            return request.target

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            del observer, policy
            assert source is observer_source
            coordinates = {
                "2p": (347.16284728400217, 11.5633172622082),
                "sun": (227.79603677620744, -17.8009756969018),
            }[value]
            return SimpleNamespace(
                geometry=SphericalPoints(
                    [coordinates[0]], [coordinates[1]],
                    coordinate_spec=coordinate_spec,
                )
            )

    class Coordinates:
        def transform(self, geometry, target, observation):
            del target, observation
            return geometry

    layer = SolarSystemPointLayer(
        descriptor,
        source_resolver=lambda body, observer: EphemerisSourceBinding(
            target_source, observer_source
        ),
        observer_state_factory=lambda observer, *, source: "observer-state",
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )

    result = layer.realize(context(), object(), selected={"2p"})

    assert len(result) == 2
    assert result.ids.tolist() == [
        "comet_2p", "comet_2p__antisolar_reference",
    ]
    assert result.labels.tolist() == ["2P/Encke", None]
    assert result.metadata["comet_symbol_orientation_reference_index"] == 1
    assert result.metadata["antisolar_position_angle_deg"] == pytest.approx(
        76.06332619563693
    )
    assert result.metadata["comet_tail_orientation_source"] == (
        "Wenu apparent Sun-comet fallback"
    )


def test_provider_psang_is_typed_and_has_precedence_contract():
    class Source:
        def apparent_gas_tail_position_angle_deg(
            self, *, request, observer_state
        ):
            assert request == "request"
            assert observer_state == "observer-state"
            return 248.649

    assert _provider_gas_tail_position_angle(
        Source(), "request", "observer-state"
    ) == pytest.approx(248.649)
    assert _provider_gas_tail_position_angle(
        object(), "request", "observer-state"
    ) is None

    class InvalidSource:
        def apparent_gas_tail_position_angle_deg(self, **kwargs):
            del kwargs
            return 360.0

    with pytest.raises(ValueError, match=r"\[0, 360\)"):
        _provider_gas_tail_position_angle(
            InvalidSource(), "request", "observer-state"
        )


@pytest.mark.parametrize('consumer', ['point','symbol'])
@pytest.mark.parametrize('mode', ['fallback','provider','suppressed'])
def test_antisolar_consumers_use_returned_sun_and_retain_reference_provenance(monkeypatch, tmp_path, consumer, mode):
    """Synthetic geometry/backend inputs with actual kernel and light-time services."""
    from dataclasses import replace
    import numpy as np
    from astropy.time import Time
    from wenu.ephemeris import EphemerisResourceChain, EphemerisState
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.sky.ceres import CERES_BODY
    from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer
    from wenu.sky.solar_system_track_layer import SolarSystemTrackRealization, CometTrackSymbolLayer
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability
    from test_solar_system_tracks import RESOURCE, CONTEXT, ApparentRealizer, observer_state, sample_observer, request
    descriptor=replace(CERES_BODY,target='2p',selection_key='2p',entity_key='comet_2p',
        display_name='2P/Encke',body_class='comet',physical_body_id='1000025',canonical_designation='2P')
    primary=replace(RESOURCE,filename='synthetic-comet.bsp',sha256='c'*64)
    class Comet:
        resource=EphemerisResourceChain(primary,(RESOURCE,))
        def state(self, query):
            return EphemerisState(query,(1.,0.,.1),(0.,0.,0.),'au','au/day',self.resource,'1000025','0')
        def apparent_gas_tail_position_angle_deg(self, **kwargs):
            return 65.412 if mode=='provider' else None
    comet=Comet()
    sun=object.__new__(SkyfieldEphemerisStateSource);sun.resource=RESOURCE
    sun.state=lambda q:EphemerisState(q,(1.,0.,.1) if mode=='suppressed' else (0.,1.,.2),
        (0.,0.,0.),'au','au/day',RESOURCE,'10','0')
    protocol=SimpleNamespace(resource=RESOURCE,state=sun.state)
    context=replace(CONTEXT,evaluation_instant='2026-08-30T00:00:00',evaluation_time_scale='utc')
    observer=SimpleNamespace(t_astropy=Time(context.evaluation_instant,scale='utc'))
    def make(source):
        options=dict(source_resolver=lambda d,o:EphemerisSourceBinding(comet,source),
            observer_state_factory=observer_state,apparent_realizer=ApparentRealizer())
        if consumer=='point':
            return SolarSystemPointLayer(descriptor,**options)
        realizer=SolarSystemTrackRealizer(sample_observer_factory=sample_observer,**options)
        shared=SolarSystemTrackRealization(request(descriptor=descriptor),realizer=realizer)
        return CometTrackSymbolLayer(shared,1)
    baseline=make(protocol).realize(context,observer)
    owner=make(sun);queries=[];original=KernelSession.evaluate
    def evaluated(session,query):
        queries.append(query)
        return original(session,query)
    monkeypatch.setattr(KernelSession,'evaluate',evaluated)
    actual=owner.realize(context,observer)
    np.testing.assert_allclose(actual.lon_deg,baseline.lon_deg,rtol=0,atol=1e-11)
    np.testing.assert_allclose(actual.lat_deg,baseline.lat_deg,rtol=0,atol=1e-11)
    if mode=='provider':
        assert queries==[]
    else:
        assert queries and all(q.objects[0].value=='ephemeris:sun' for q in queries)
    receipt=actual.metadata['antisolar_reference_provenance']
    assert receipt.kind=='comet-tail-axis'
    assert receipt.observation.instant==('2026-08-30T00:00:00' if consumer=='point'
        else owner.track_realization._result.sample_instants[owner.track_realization._result.tick_sample_indices[1]])
    assert receipt.observation.time_scale=='utc'
    assert receipt.source_resource==(comet.resource if mode=='provider' else RESOURCE)
    assert receipt.observer_resource==RESOURCE
    assert receipt.available==(mode!='suppressed')
    assert len(actual.lon_deg)==(1 if mode=='suppressed' else 2)
    if mode=='fallback':
        # Actual canonical rendering, with a deliberately synthetic apparent backend.
        import matplotlib.pyplot as plt
        from matplotlib.image import imread
        from wenu.sky.celestial_sphere import CelestialSphere
        from wenu.charts.detail_application import composition_layer_options
        from wenu.charts.styles import PublicationStyle
        from wenu.charts.detail import ResolvedDetail
        from wenu.charts.context import Viewport, BoundaryKind
        from wenu.projections import StereographicProjection
        from wenu.rendering import MatplotlibRenderer
        viewport=Viewport(-2.,2.,-2.,2.)
        composition=SimpleNamespace(style=PublicationStyle(),detail=ResolvedDetail(),
            context=SimpleNamespace(boundary_kind=BoundaryKind.RECTANGULAR,viewport=viewport))
        images=[]
        for index,layer in enumerate((make(protocol),owner)):
            sky=CelestialSphere(None);sky.add(layer)
            if consumer=='point':
                sky.solar_system_bodies[descriptor.selection_key]=layer
            options=composition_layer_options(composition,sky,reload_catalogues=False)
            figure,axes=plt.subplots(figsize=(4,3),dpi=90)
            try:
                sky.draw_chart(observer=observer,realization_context=context,
                    projection=StereographicProjection(),renderer=MatplotlibRenderer(axes),
                    layer_options=options.layer_options,viewport=viewport)
                axes.set_axis_off()
                output=tmp_path/f'fallback-{consumer}-{index}.png';figure.savefig(output)
                images.append(imread(output))
            finally:
                plt.close(figure)
        np.testing.assert_array_equal(images[0],images[1])
        assert np.any(images[0][:,:,:3]<.5)
        def changed(session,query):
            batch=evaluated(session,query);row=batch.states[0];x,y,z=row.position_m
            return replace(batch,states=(replace(row,position_m=(-y,x,z)),))
        monkeypatch.setattr(KernelSession,'evaluate',changed)
        moved=owner.realize(context,observer)
        np.testing.assert_allclose(moved.lon_deg[:1],actual.lon_deg[:1],rtol=0,atol=1e-11)
        assert not np.allclose(moved.lon_deg[1:],actual.lon_deg[1:],rtol=0,atol=1e-10)
        def refused(*args,**kwargs):
            raise UnsupportedCapability('antisolar Sun query refused')
        monkeypatch.setattr(KernelSession,'evaluate',refused)
        with pytest.raises(UnsupportedCapability,match='Sun query refused'):
            owner.realize(context,observer)


def test_point_kernel_opt_in_preserves_existing_track_and_other_family_binding(monkeypatch):
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu.sky.solar_system_points import skyfield_source_binding
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.ephemeris_state import KernelEphemerisStateSource
    source = SimpleNamespace(resource=object())
    monkeypatch.setattr(SkyfieldEphemerisStateSource, 'from_observer',
                        classmethod(lambda cls, observer: source))
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve('moon')
    retained = skyfield_source_binding(descriptor, object())
    assert retained.target_source is retained.observer_source is source
    selected = skyfield_source_binding(descriptor, object(), kernel_states=True)
    assert isinstance(selected.target_source, KernelEphemerisStateSource)
    assert selected.observer_source is source
    assert selected.target_source.source is source
    other = skyfield_source_binding(SolarSystemPointDescriptor(
        'sun', 'sun', 'Sun', 'sun'), object(), kernel_states=True)
    assert other.target_source is other.observer_source is source
