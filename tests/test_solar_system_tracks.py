"""Scientific contract tests for sampled Solar-System trajectories."""

from dataclasses import FrozenInstanceError, replace
from math import cos, radians, sin
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.time import Time

from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    PositionStatus,
)
from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_points import (
    EphemerisSourceBinding,
    SolarSystemPointDescriptor,
)
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
)
from wenu.sky.solar_system_track_layer import (
    CometTrackSymbolLayer,
    SolarSystemTrackLayer,
    SolarSystemTrackRealization,
    SolarSystemTrackSymbolLayer,
)
from wenu.sky.ceres import CERES_BODY
from wenu.solar_system_directions import (
    ApparentDirection,
    ObserverBarycentricState,
)

RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="track-test",
    filename="track.bsp",
    sha256="b" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)
DESCRIPTOR = SolarSystemPointDescriptor(
    target="venus",
    entity_key="venus",
    display_name="Venus",
    selection_key="venus",
)
PRODUCT_SPEC = CoordinateSpec(
    frame="icrs",
    origin="observer",
    position_status=PositionStatus.APPARENT,
    provider="test product",
)
OBSERVATION = ObservationContext(
    longitude_deg=-71.230289,
    latitude_deg=-32.443342,
    elevation_m=52.0,
    instant="2026-08-30T00:00:00.000",
    time_scale="utc",
)
CONTEXT = LayerRealizationContext(
    product_coordinate_spec=PRODUCT_SPEC,
    observation=OBSERVATION,
)


class TrackSource:
    resource = RESOURCE

    def __init__(self):
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        offset = float(
            (
                Time(request.instant, scale=request.time_scale)
                - Time("2026-08-30T00:00:00", scale="utc")
            ).to_value("day")
        )
        angle = radians(offset)
        return EphemerisState(
            request=request,
            position=(cos(angle), sin(angle), 0.1),
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="299",
            provider_centre_id="0",
        )


class ApparentRealizer:
    def __init__(self):
        self.receptions = []

    def direction(self, astrometric, *, observer, source, policy):
        del observer, source
        self.receptions.append(astrometric.request.reception_instant)
        native = astrometric.geometry
        geometry = SphericalPoints(
            native.lon_deg.copy(),
            native.lat_deg.copy(),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="observer",
                position_status=PositionStatus.APPARENT,
                instant=astrometric.request.reception_instant,
                time_scale=astrometric.request.reception_time_scale,
                provider=RESOURCE.provider,
                model=policy.model,
                provenance=("deterministic apparent direction",),
                corrections=frozenset(
                    (
                        "one-way-light-time",
                        "aberration",
                        "gravitational-deflection",
                    )
                ),
            ),
            ids=np.asarray(("venus",), dtype=object),
        )
        return ApparentDirection(
            astrometric=astrometric,
            policy=policy,
            geometry=geometry,
        )


def precise_isot(value):
    precise = value.copy()
    precise.precision = 9
    return precise.isot


def observer_state(sample_observer, *, source):
    instant = sample_observer.t_astropy
    return ObserverBarycentricState(
        observer_id="La Ligua",
        centre="solar system barycenter",
        frame="icrf",
        instant=precise_isot(instant),
        time_scale=instant.scale,
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, 0.0),
        position_unit="au",
        velocity_unit="au/day",
        resource=source.resource,
        provider_observer_id="WGS84 site",
        provider_centre_id="0",
    )


def sample_observer(observer, instant):
    del observer
    return SimpleNamespace(t_astropy=instant)


def request(**overrides):
    values = {
        "descriptor": DESCRIPTOR,
        "start_instant": "2026-08-30T00:00:00Z",
        "start_time_scale": "utc",
        "sample_step_days": 0.4,
        "tick_step_days": 0.75,
        "tick_count": 2,
    }
    values.update(overrides)
    return SolarSystemTrackRequest(**values)


def test_request_is_frozen_and_inserts_exact_tick_instants():
    value = request()

    assert value.start_instant == "2026-08-30T00:00:00.000000000"
    assert value.duration_days == pytest.approx(1.5)
    assert value.sample_offsets_days == pytest.approx(
        (0.0, 0.4, 0.75, 0.8, 1.2, 1.5)
    )
    assert value.tick_offsets_days == pytest.approx((0.0, 0.75, 1.5))
    with pytest.raises(FrozenInstanceError):
        value.tick_count = 3


@pytest.mark.parametrize(
    ("name", "value", "error"),
    (
        ("sample_step_days", 0.0, ValueError),
        ("tick_step_days", float("nan"), ValueError),
        ("tick_count", 0, ValueError),
        ("tick_count", True, TypeError),
        ("start_time_scale", "", ValueError),
    ),
)
def test_request_rejects_invalid_time_sampling(name, value, error):
    with pytest.raises(error):
        request(**{name: value})


def test_realizer_assembles_one_curve_and_transforms_only_after_sampling():
    source = TrackSource()
    apparent = ApparentRealizer()
    calls = []

    class CoordinateService:
        def transform(self, geometry, target_spec, observation):
            calls.append((geometry, target_spec, observation))
            return SphericalCurves(
                lon_deg=tuple(value.copy() for value in geometry.lon_deg),
                lat_deg=tuple(value.copy() for value in geometry.lat_deg),
                coordinate_spec=target_spec,
                closed=geometry.closed.copy(),
                ids=geometry.ids.copy(),
                labels=geometry.labels.copy(),
                names=geometry.names.copy(),
                metadata=dict(geometry.metadata),
            )

    result = SolarSystemTrackRealizer(
        source_factory=lambda observer: source,
        sample_observer_factory=sample_observer,
        observer_state_factory=observer_state,
        apparent_realizer=apparent,
        coordinate_service=CoordinateService(),
    ).curve(
        request(),
        context=CONTEXT,
        observer=object(),
    )

    assert len(calls) == 1
    native, target_spec, observation = calls[0]
    assert isinstance(native, SphericalCurves)
    assert native.coordinate_spec.frame == "icrs"
    assert native.coordinate_spec.position_status is PositionStatus.APPARENT
    assert native.coordinate_spec.instant is None
    assert target_spec is PRODUCT_SPEC
    assert observation is OBSERVATION

    assert result.geometry.coordinate_spec is PRODUCT_SPEC
    assert result.geometry.ids.tolist() == ["venus.track"]
    assert result.geometry.names.tolist() == ["Venus"]
    assert len(result.geometry.lon_deg[0]) == 6
    assert result.tick_sample_indices == (0, 2, 5)
    assert result.sample_instants[0] == "2026-08-30T00:00:00.000000000"
    assert result.sample_instants[-1] == "2026-08-31T12:00:00.000000000"
    assert result.sample_time_scale == "utc"
    assert len(result.apparent_directions) == 6
    assert len(apparent.receptions) == 6
    assert result.geometry.metadata["ephemeris_sha256"] == "b" * 64
    assert result.geometry.metadata["tick_offsets_days"] == pytest.approx(
        (0.0, 0.75, 1.5)
    )
    assert "chart product frame held fixed" in result.provenance[-1]


def test_realizer_uses_one_source_and_reevaluates_observer_for_each_sample():
    source = TrackSource()
    source_calls = []
    observer_instants = []

    def source_factory(observer):
        source_calls.append(observer)
        return source

    def state_factory(sample, *, source):
        observer_instants.append(precise_isot(sample.t_astropy))
        return observer_state(sample, source=source)

    result = SolarSystemTrackRealizer(
        source_factory=source_factory,
        sample_observer_factory=sample_observer,
        observer_state_factory=state_factory,
        apparent_realizer=ApparentRealizer(),
    ).curve(
        request(
            sample_step_days=0.75,
            tick_step_days=0.75,
            tick_count=2,
        ),
        context=CONTEXT,
        observer="base observer",
    )

    assert source_calls == ["base observer"]
    assert observer_instants == list(result.sample_instants)
    assert len(observer_instants) == 3
    assert all(
        direction.astrometric.observer_state.instant == instant
        for direction, instant in zip(
            result.apparent_directions,
            result.sample_instants,
        )
    )


def test_realizer_keeps_target_and_observer_source_roles_distinct():
    target_source = TrackSource()
    observer_source = SimpleNamespace(resource=RESOURCE)
    observer_sources = []

    def state_factory(sample, *, source):
        observer_sources.append(source)
        return observer_state(sample, source=source)

    SolarSystemTrackRealizer(
        source_resolver=lambda descriptor, observer: EphemerisSourceBinding(
            target_source=target_source,
            observer_source=observer_source,
        ),
        sample_observer_factory=sample_observer,
        observer_state_factory=state_factory,
        apparent_realizer=ApparentRealizer(),
    ).curve(
        request(sample_step_days=0.75, tick_step_days=0.75, tick_count=2),
        context=CONTEXT,
        observer="base observer",
    )

    assert len(target_source.requests) == 6
    assert observer_sources == [observer_source] * 3


def test_path_and_major_symbols_reuse_one_realized_target_trajectory():
    source = TrackSource()
    realizer = SolarSystemTrackRealizer(
        source_factory=lambda observer: source,
        sample_observer_factory=sample_observer,
        observer_state_factory=observer_state,
        apparent_realizer=ApparentRealizer(),
    )
    track_request = request(
        sample_step_days=0.75, tick_step_days=0.75, tick_count=2
    )
    shared = SolarSystemTrackRealization(track_request, realizer=realizer)
    path = SolarSystemTrackLayer(track_request, realization=shared)
    symbols = tuple(
        SolarSystemTrackSymbolLayer(shared, index)
        for index in range(track_request.tick_count + 1)
    )
    observer = object()

    curve = path.realize(CONTEXT, observer)
    request_count = len(source.requests)
    points = tuple(
        symbol.realize(CONTEXT, observer, selected=frozenset())
        for symbol in symbols
    )

    assert len(source.requests) == request_count
    assert tuple(float(point.lon_deg[0]) for point in points) == pytest.approx(
        tuple(curve.lon_deg[0][index] for index in (0, 1, 2))
    )


def test_comet_symbol_adds_provider_orientation_without_reevaluating_target():
    class CometSource(TrackSource):
        def apparent_gas_tail_position_angle_deg(self, **options):
            del options
            return 76.0

    descriptor = replace(
        CERES_BODY,
        target="2p", entity_key="comet_2p", display_name="2P/Encke",
        selection_key="2p", body_class="comet", physical_body_id="1000025",
        canonical_designation="2P/Encke", iau_number=2,
    )
    track_request = request(
        descriptor=descriptor, sample_step_days=0.75,
        tick_step_days=0.75, tick_count=2,
    )
    source = CometSource()
    realizer = SolarSystemTrackRealizer(
        source_factory=lambda observer: source,
        sample_observer_factory=sample_observer,
        observer_state_factory=observer_state,
        apparent_realizer=ApparentRealizer(),
    )
    shared = SolarSystemTrackRealization(track_request, realizer=realizer)
    observer = object()
    shared.realize(CONTEXT, observer)
    request_count = len(source.requests)

    symbol = CometTrackSymbolLayer(shared, 1).realize(CONTEXT, observer)

    assert len(source.requests) == request_count
    assert len(symbol) == 2
    assert symbol.metadata["antisolar_position_angle_deg"] == 76.0
    assert symbol.metadata["comet_tail_orientation_source"] == "provider PsAng"


def test_realizer_requires_typed_context_with_observation():
    realizer = SolarSystemTrackRealizer()

    with pytest.raises(TypeError, match="LayerRealizationContext"):
        realizer.curve(request(), context=object(), observer=object())

    without_observation = LayerRealizationContext(
        product_coordinate_spec=PRODUCT_SPEC,
    )
    with pytest.raises(ValueError, match="observation context"):
        realizer.curve(
            request(),
            context=without_observation,
            observer=object(),
        )


def test_track_component_sharing_checks_resource_and_fresh_context_before_reuse():
    source = TrackSource()
    calls = []
    def acquire(observer):
        calls.append(observer)
        return source
    shared = SolarSystemTrackRealization(request(), realizer=SolarSystemTrackRealizer(
        source_factory=acquire, sample_observer_factory=sample_observer,
        observer_state_factory=observer_state, apparent_realizer=ApparentRealizer()))
    generation = [0]
    def identity():
        if generation[0] == 'closed':
            raise RuntimeError('track ephemeris closed')
        return generation[0]
    observer = SimpleNamespace(geometry_resource_identity=identity)
    first = shared.realize(CONTEXT, observer)
    assert shared.realize(CONTEXT, observer) is first
    assert len(calls) == 1
    generation[0] = 'closed'
    with pytest.raises(RuntimeError, match='ephemeris closed'):
        shared.realize(CONTEXT, observer)
    generation[0] = 1
    assert shared.realize(CONTEXT, observer) is not first
    assert len(calls) == 2
    def refused(observer):
        raise RuntimeError('fresh track admission refused')
    shared.realizer.source_factory = refused
    with pytest.raises(RuntimeError, match='fresh track admission refused'):
        shared.realize(replace(CONTEXT), observer)


NATURAL_TARGET_IDS = {
    'mercury': '199', 'venus': '299', 'mars barycenter': '4',
    'jupiter barycenter': '5', 'saturn barycenter': '6',
    'uranus barycenter': '7', 'neptune barycenter': '8', 'moon': '301',
}


def _kernel_track_backend(monkeypatch):
    """Synthetic ephemeris implementing the existing Skyfield adapter boundary."""
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    raw = TrackSource()
    state = raw.state
    raw.state = lambda query: replace(state(query), provider_target_id=NATURAL_TARGET_IDS[query.target])
    backend = object.__new__(SkyfieldEphemerisStateSource)
    backend.resource = raw.resource
    backend.state = raw.state
    monkeypatch.setattr(SkyfieldEphemerisStateSource, 'from_observer',
                        classmethod(lambda cls, observer: backend))
    return raw, backend


@pytest.mark.parametrize('body', ('mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'moon'))
@pytest.mark.parametrize('binding_kind', ('default', 'mixed'))
def test_natural_track_default_and_mixed_bindings_consume_kernel_samples(monkeypatch, body, binding_kind):
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability
    raw, backend = _kernel_track_backend(monkeypatch)
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
    value = request(descriptor=descriptor)
    options = dict(sample_observer_factory=sample_observer, observer_state_factory=observer_state,
                   apparent_realizer=ApparentRealizer())
    baseline = SolarSystemTrackRealizer(source_factory=lambda observer: raw, **options).curve(
        value, context=CONTEXT, observer=object())
    inputs = {}
    base_observer = object()
    resource_session = None
    if binding_kind == 'mixed':
        from wenu.minor_body_resources import MinorBodyResourceSession
        resource_session = object.__new__(MinorBodyResourceSession)
        resource_session._closed = False
        resource_session.observer = base_observer
        resource_session.planetary_source = backend
        inputs['source_resolver'] = resource_session.source_binding
    calls = []
    transforms = []
    class FixedAxes:
        def transform(self, geometry, target, observation):
            transforms.append((target, observation))
            return SphericalCurves(geometry.lon_deg, geometry.lat_deg,
                coordinate_spec=target, ids=geometry.ids, labels=geometry.labels,
                names=geometry.names, closed=geometry.closed, metadata=dict(geometry.metadata))
    original = KernelSession.evaluate
    def record(session, query):
        calls.append(query)
        return original(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', record)
    owner = SolarSystemTrackRealizer(**inputs, coordinate_service=FixedAxes(), **options)
    result = owner.curve(value, context=CONTEXT, observer=base_observer)
    assert calls
    assert all(q.objects[0].value == 'ephemeris:' + descriptor.target for q in calls)
    assert all(q.times[0].scale == 'tdb' and q.reference.origin_id == descriptor.centre for q in calls)
    assert isinstance(result.source_binding.target_source, KernelEphemerisStateSource)
    assert result.source_binding.observer_source is backend
    assert result.tick_sample_indices == baseline.tick_sample_indices == (0, 2, 5)
    assert result.sample_instants == baseline.sample_instants
    np.testing.assert_allclose(result.geometry.lon_deg[0], baseline.geometry.lon_deg[0], rtol=0, atol=1e-11)
    assert transforms == [(PRODUCT_SPEC, OBSERVATION)]
    assert result.geometry.coordinate_spec is PRODUCT_SPEC
    assert all(d.target_provider_id == NATURAL_TARGET_IDS[descriptor.target]
               for d in (a.astrometric for a in result.apparent_directions))
    def changed(session, query):
        batch = record(session, query)
        row = batch.states[0]
        x, y, z = row.position_m
        return replace(batch, states=(replace(row, position_m=(-y, x, z)),))
    monkeypatch.setattr(KernelSession, 'evaluate', changed)
    moved = owner.curve(value, context=CONTEXT, observer=base_observer)
    np.testing.assert_allclose(moved.geometry.lon_deg[0], (result.geometry.lon_deg[0] + 90) % 360,
                               rtol=0, atol=1e-10)
    def refuse(session, query):
        raise UnsupportedCapability('track state refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(UnsupportedCapability, match='track state refusal'):
        owner.curve(value, context=CONTEXT, observer=base_observer)

    if resource_session is not None:
        resource_session._closed = True
        with pytest.raises(ValueError, match='resource session is closed'):
            owner.curve(value, context=CONTEXT, observer=base_observer)


def test_real_offline_natural_tracks_match_retained_raw_direction_chain():
    from pathlib import Path
    from wenu.observer import Observer, DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    path = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not path.is_file():
        raise FileNotFoundError(f'Offline track acceptance requires {path}')
    observer = Observer(lat_deg=OBSERVATION.latitude_deg, lon_deg=OBSERVATION.longitude_deg, elevation_m=52.,
                        timezone_name='UTC', time='2026-08-30T00:00:00')
    try:
        raw = SkyfieldEphemerisStateSource.from_observer(observer)
        protocol = SimpleNamespace(resource=raw.resource, state=raw.state)
        for body in ('mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'moon'):
            descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
            value = request(descriptor=descriptor, sample_step_days=.5, tick_step_days=.75, tick_count=1)
            # Explicit generic protocol injection preserves the pre-migration raw target route.
            expected = SolarSystemTrackRealizer(source_resolver=lambda descriptor, observer:
                EphemerisSourceBinding(protocol, raw)).curve(value, context=CONTEXT, observer=observer)
            actual = SolarSystemTrackRealizer().curve(value, context=CONTEXT, observer=observer)
            assert actual.sample_instants == expected.sample_instants
            assert actual.tick_sample_indices == expected.tick_sample_indices
            np.testing.assert_allclose(actual.geometry.lon_deg[0], expected.geometry.lon_deg[0], rtol=0, atol=1e-10)
            np.testing.assert_allclose(actual.geometry.lat_deg[0], expected.geometry.lat_deg[0], rtol=0, atol=1e-10)
            for a, b in zip(actual.apparent_directions, expected.apparent_directions):
                assert a.astrometric.target_provider_id == b.astrometric.target_provider_id == NATURAL_TARGET_IDS[descriptor.target]
                assert a.astrometric.distance_au == pytest.approx(b.astrometric.distance_au, rel=1e-12, abs=1e-15)
                assert a.astrometric.light_time_days == pytest.approx(b.astrometric.light_time_days, rel=1e-12, abs=1e-15)
    finally:
        observer.close()
