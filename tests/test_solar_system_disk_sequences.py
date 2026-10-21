"""Observed multi-epoch resolved-disk scientific contracts."""

from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.solar_system_appearance import VENUS_MEAN_RADIUS_KM
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    ApparentDirection,
    AstrometricDirection,
    ObserverBarycentricState,
)
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequence,
    ObservedSolarSystemDiskSequenceRealizer,
    ObservedSolarSystemDiskSequenceRequest,
)


RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="DE440-test",
    filename="deterministic.bsp",
    sha256="a" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)
DESCRIPTOR = SolarSystemPointDescriptor(
    target="venus",
    centre="solar system barycenter",
    selection_key="venus",
    entity_key="solar_system.planets.venus",
    display_name="Venus",
    correction_policy=ApparentCorrectionPolicy(),
)
RADIUS_MODEL = "JPL mean Venus radius"


def request(**changes):
    values = dict(
        descriptor=DESCRIPTOR,
        start_instant="2026-08-30T00:00:00",
        start_time_scale="utc",
        step_days=7.0,
        n_steps=2,
        display_name="Venus",
        physical_radius_km=VENUS_MEAN_RADIUS_KM,
        radius_model=RADIUS_MODEL,
    )
    values.update(changes)
    return ObservedSolarSystemDiskSequenceRequest(**values)


def _spec(instant, status):
    return CoordinateSpec(
        frame="icrs",
        origin="observer",
        position_status=status,
        instant=instant,
        time_scale="utc",
        provider=RESOURCE.provider,
        model=RESOURCE.model,
        corrections=(
            frozenset(("one-way-light-time",))
            if status is PositionStatus.ASTROMETRIC
            else frozenset((
                "one-way-light-time",
                "aberration",
                "gravitational-deflection",
                "earth-gravitational-deflection",
            ))
        ),
    )


class Source:
    resource = RESOURCE

    def __init__(self):
        self.requests = []

    def state(self, state_request):
        self.requests.append(state_request)
        return EphemerisState(
            request=state_request,
            position=(1.0, 1.0, 0.0),
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="10",
            provider_centre_id="0",
        )


class Astrometric:
    def __init__(self):
        self.target_requests = []
        self.sun_requests = []

    def direction(self, source, direction_request, observer_state):
        del source
        if direction_request.target == "sun":
            self.sun_requests.append(direction_request)
            longitude = 90.0
            distance = 1.0
            provider_id = "10"
        else:
            self.target_requests.append(direction_request)
            sample = len(self.target_requests) - 1
            longitude = 5.0 * sample
            distance = 1.0 - 0.1 * sample
            provider_id = "299"
        geometry = SphericalPoints(
            np.asarray((longitude,)),
            np.asarray((0.0,)),
            coordinate_spec=_spec(
                direction_request.reception_instant,
                PositionStatus.ASTROMETRIC,
            ),
            ids=np.asarray((direction_request.target,), dtype=object),
        )
        return AstrometricDirection(
            request=direction_request,
            observer_state=observer_state,
            geometry=geometry,
            distance_au=distance,
            relative_velocity_au_per_day=(0.0, 0.0, 0.0),
            light_time_days=distance / 173.1446326846693,
            emission_instant=direction_request.reception_instant,
            emission_time_scale=direction_request.reception_time_scale,
            iterations=2,
            target_provider_id=provider_id,
        )


class Apparent:
    def direction(self, astrometric, **options):
        del options
        geometry = SphericalPoints(
            astrometric.geometry.lon_deg.copy(),
            astrometric.geometry.lat_deg.copy(),
            coordinate_spec=_spec(
                astrometric.request.reception_instant,
                PositionStatus.APPARENT,
            ),
            ids=astrometric.geometry.ids.copy(),
        )
        return ApparentDirection(
            astrometric=astrometric,
            policy=ApparentCorrectionPolicy(),
            geometry=geometry,
        )


def observer_state(sample_observer, *, source):
    del source
    precise = sample_observer.t_astropy.copy()
    precise.precision = 9
    instant = precise.isot
    return ObserverBarycentricState(
        observer_id="La Ligua",
        centre="solar system barycenter",
        frame="icrf",
        instant=instant,
        time_scale=sample_observer.t_astropy.scale,
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, 0.0),
        position_unit="au",
        velocity_unit="au/day",
        resource=RESOURCE,
        provider_observer_id="test site",
        provider_centre_id="0",
    )


def sample_observer(base, instant):
    del base
    return SimpleNamespace(t_astropy=instant)


def realized(sequence_request=None):
    source = Source()
    astrometric = Astrometric()
    realizer = ObservedSolarSystemDiskSequenceRealizer(
        source_factory=lambda observer: source,
        sample_observer_factory=sample_observer,
        observer_state_factory=observer_state,
        astrometric_realizer=astrometric,
        apparent_realizer=Apparent(),
    )
    result = realizer.sequence(
        request() if sequence_request is None else sequence_request,
        observer=object(),
    )
    return result, source, astrometric


def test_request_uses_major_intervals_and_includes_start():
    value = request(n_steps=8, step_days=7)

    assert value.sample_count == 9
    assert value.sample_offsets_days == (
        0.0, 7.0, 14.0, 21.0, 28.0, 35.0, 42.0, 49.0, 56.0
    )
    assert value.start_instant == "2026-08-30T00:00:00.000000000"
    assert value.start_time_scale == "utc"

    with pytest.raises(FrozenInstanceError):
        value.n_steps = 1


@pytest.mark.parametrize(
    ("changes", "error"),
    (
        ({"step_days": 0.0}, ValueError),
        ({"step_days": float("nan")}, ValueError),
        ({"n_steps": -1}, ValueError),
        ({"n_steps": True}, TypeError),
        ({"n_steps": 1.5}, TypeError),
        ({"physical_radius_km": 0.0}, ValueError),
        ({"display_name": ""}, ValueError),
        ({"radius_model": ""}, ValueError),
    ),
)
def test_request_rejects_invalid_scientific_values(changes, error):
    with pytest.raises(error):
        request(**changes)


def test_realizer_evaluates_every_epoch_and_retains_distances():
    result, source, astrometric = realized()

    assert isinstance(result, ObservedSolarSystemDiskSequence)
    assert result.sample_instants == (
        "2026-08-30T00:00:00.000000000",
        "2026-09-06T00:00:00.000000000",
        "2026-09-13T00:00:00.000000000",
    )
    assert result.sample_time_scale == "utc"
    assert result.distances == pytest.approx((1.0, 0.9, 0.8))
    assert result.distance_origin == "observer"
    assert result.distance_unit == "au"
    assert len(result.appearances) == len(result.geometries) == 3
    assert tuple(
        geometry.appearance for geometry in result.geometries
    ) == result.appearances
    assert tuple(
        appearance.apparent_direction.geometry.lon_deg[0]
        for appearance in result.appearances
    ) == pytest.approx((0.0, 5.0, 10.0))
    assert len(astrometric.target_requests) == 3
    assert len(astrometric.sun_requests) == 3
    assert len(source.requests) == 3
    assert all(value.target == "sun" for value in source.requests)
    assert "full observer-target distances retained" in result.provenance[3]


def test_zero_intervals_produces_exactly_one_observed_disk():
    result, _, astrometric = realized(request(n_steps=0))

    assert len(result.sample_instants) == 1
    assert result.distances == (1.0,)
    assert len(astrometric.target_requests) == 1
    assert len(astrometric.sun_requests) == 1


def test_result_rejects_distance_reconstruction_or_geometry_mismatch():
    result, _, _ = realized()

    with pytest.raises(ValueError, match="astrometric distance"):
        replace(result, distances=(1.0, 0.9, 9.0))
    with pytest.raises(ValueError, match="exact appearance"):
        replace(
            result,
            geometries=(
                result.geometries[1],
                result.geometries[0],
                result.geometries[2],
            ),
        )
    with pytest.raises(ValueError, match="distance_origin"):
        replace(result, distance_origin="sun")
    with pytest.raises(ValueError, match="distance_unit"):
        replace(result, distance_unit="km")


def test_realizer_requires_typed_request():
    with pytest.raises(
        TypeError,
        match="ObservedSolarSystemDiskSequenceRequest",
    ):
        ObservedSolarSystemDiskSequenceRealizer().sequence(
            object(),
            observer=object(),
        )


def _kernel_disk_dependencies(monkeypatch):
    """Constructed moving targets and apparent seam; never a physical oracle."""
    from astropy.time import Time
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.solar_system_directions import AstrometricDirectionRealizer

    class GeometricSource:
        resource = RESOURCE
        def __init__(self):
            self.requests = []
        def state(self, query):
            self.requests.append(query)
            vectors = dict(sun=(0., 0., 0.), earth=(1., 0., 0.),
                           venus=(.4, .5, .1), mercury=(.3, .3, .02),
                           moon=(1.001, .004, .0003))
            ids = dict(sun='10', earth='399', venus='299', mercury='199', moon='301')
            days = float((Time(query.instant, scale=query.time_scale).tdb
                          - Time('2026-08-30T00:00:00', scale='tdb')).to_value('day'))
            position = vectors[query.target]
            velocity = (0., 0., 0.)
            if query.target not in ('sun', 'earth'):
                velocity = (.001, .002, 0.)
                position = tuple(x + days * v for x, v in zip(position, velocity))
            return EphemerisState(query, position, velocity, 'au', 'au/day', RESOURCE,
                                  ids[query.target], '10' if query.centre == 'sun' else '0')
        def close(self):
            pytest.fail('borrowed source must not be closed')

    source = GeometricSource()
    monkeypatch.setattr(SkyfieldEphemerisStateSource, 'from_observer',
                        classmethod(lambda cls, observer: source))
    observer = SimpleNamespace(t_astropy=Time('2026-08-30T00:00:00', scale='tdb'),
        geometry_resource_identity=lambda: ('constructed', RESOURCE.sha256))
    events = []
    def reception(value, *, source):
        events.append(value.t_astropy.copy())
        precise = value.t_astropy.copy(); precise.precision = 9
        return ObserverBarycentricState('synthetic site', 'solar system barycenter',
            'icrf', precise.isot, precise.scale, (1., 0., 0.), (0., 0., 0.),
            'au', 'au/day', RESOURCE, provider_centre_id='0')
    def at_time(base, instant):
        return SimpleNamespace(t_astropy=instant)
    class ApparentSeam:
        def direction(self, astrometric, *, observer, source, policy):
            assert source is not None
            assert astrometric.light_time_days > 0
            return ApparentDirection(astrometric, policy,
                SphericalPoints(astrometric.geometry.lon_deg.copy(),
                                astrometric.geometry.lat_deg.copy(),
                    coordinate_spec=replace(astrometric.geometry.coordinate_spec,
                        position_status=PositionStatus.APPARENT),
                    ids=astrometric.geometry.ids.copy()),
                provenance=('constructed apparent seam',))
    return source, observer, events, dict(
        observer_state_factory=reception, sample_observer_factory=at_time,
        astrometric_realizer=AstrometricDirectionRealizer(), apparent_realizer=ApparentSeam())


@pytest.mark.parametrize('body', ('venus', 'moon'))
def test_default_observed_disks_consume_kernel_states_at_every_epoch(monkeypatch, body):
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability

    source, observer, events, dependencies = _kernel_disk_dependencies(monkeypatch)
    descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
    value = request(descriptor=descriptor, display_name=descriptor.display_name,
        physical_radius_km=descriptor.physical_radius_km, radius_model=descriptor.radius_model,
        start_time_scale='tdb', step_days=1., n_steps=2)
    baseline = ObservedSolarSystemDiskSequenceRealizer(
        source_factory=lambda observer: source, **dependencies).sequence(value, observer=observer)
    queries = []
    evaluate = KernelSession.evaluate
    def record(session, query):
        queries.append(query)
        return evaluate(session, query)
    monkeypatch.setattr(KernelSession, 'evaluate', record)
    owner = ObservedSolarSystemDiskSequenceRealizer(**dependencies)
    routed = owner.sequence(value, observer=observer)
    assert routed.sample_instants == baseline.sample_instants
    assert routed.distances == pytest.approx(baseline.distances, rel=1e-13, abs=1e-15)
    for actual, expected in zip(routed.appearances, baseline.appearances):
        assert actual.angular_diameter_arcsec == pytest.approx(expected.angular_diameter_arcsec, rel=1e-12)
        assert actual.phase_angle_deg == pytest.approx(expected.phase_angle_deg, abs=1e-11)
        assert actual.bright_limb_position_angle_deg == pytest.approx(expected.bright_limb_position_angle_deg, abs=1e-11)
    assert queries
    assert {q.objects[0].value for q in queries} == {'ephemeris:sun', 'ephemeris:' + descriptor.target}
    assert all(q.times[0].scale == 'tdb' for q in queries)
    assert all(q.reference.origin_id == descriptor.centre for q in queries)
    assert len(events) == 6
    for epoch in range(3):
        assert events[epoch] == events[epoch + 3]
    def changed(session, query):
        batch = record(session, query)
        row = batch.states[0]
        if query.objects[0].value == 'ephemeris:' + descriptor.target:
            x, y, z = row.position_m
            row = replace(row, position_m=(x, y * 1.5, z))
        return replace(batch, states=(row,))
    monkeypatch.setattr(KernelSession, 'evaluate', changed)
    moved = owner.sequence(value, observer=observer)
    assert not np.allclose(moved.distances, routed.distances, rtol=1e-5, atol=0)
    def refused(session, query):
        raise UnsupportedCapability('observed state refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refused)
    with pytest.raises(UnsupportedCapability, match='observed state refusal'):
        owner.sequence(value, observer=observer)


def test_real_offline_disk_routes_match_retained_raw_appearance_and_sequences():
    """DE440s acceptance for admitted Venus/Moon displays and Venus/Mercury frozen states."""
    from pathlib import Path
    from wenu.observer import Observer, DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
    from wenu.sky.venus_disk import SolarSystemDiskRealization
    from wenu.sky.frozen_earth_disk_sequences import FrozenEarthDiskSequenceRealizer, FrozenEarthDiskSequenceRequest
    from wenu.sky.realization import LayerRealizationContext
    from wenu.coordinates import ObservationContext
    resource = Path(DEFAULT_DATA_DIRECTORY) / DEFAULT_EPHEMERIS
    if not resource.is_file():
        raise FileNotFoundError(f'Offline disk acceptance requires {resource}')
    observer = Observer(lat_deg=-33., lon_deg=-71., elevation_m=52.,
        timezone_name='UTC', time='2026-08-30T00:00:00')
    def compare(actual, expected):
        for name in ('angular_diameter_arcsec', 'phase_angle_deg',
                     'illuminated_fraction', 'bright_limb_position_angle_deg'):
            assert getattr(actual, name) == pytest.approx(getattr(expected, name), rel=1e-11, abs=1e-9)
        assert actual.physical_radius_km == expected.physical_radius_km
        assert actual.radius_model == expected.radius_model
    try:
        raw = SkyfieldEphemerisStateSource.from_observer(observer)
        instant = '2026-08-30T00:00:00.000000000'
        observation = ObservationContext(longitude_deg=-71., latitude_deg=-33., elevation_m=52.,
                                        instant=instant, time_scale='utc')
        context = LayerRealizationContext(product_coordinate_spec=CoordinateSpec(
            frame='icrs', origin='observer', position_status=PositionStatus.APPARENT,
            instant=instant, time_scale='utc'), observation=observation,
            evaluation_instant=instant, evaluation_time_scale='utc')
        for body in ('venus', 'moon'):
            descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
            baseline = SolarSystemDiskRealization(descriptor, source_factory=lambda observer: raw).realize(context, observer)
            actual = SolarSystemDiskRealization(descriptor).realize(context, observer)
            compare(actual.physical.appearance, baseline.physical.appearance)
            value = request(descriptor=descriptor, display_name=descriptor.display_name,
                physical_radius_km=descriptor.physical_radius_km, radius_model=descriptor.radius_model,
                step_days=1., n_steps=1)
            baseline_sequence = ObservedSolarSystemDiskSequenceRealizer(
                source_factory=lambda observer: raw).sequence(value, observer=observer)
            actual_sequence = ObservedSolarSystemDiskSequenceRealizer().sequence(value, observer=observer)
            assert actual_sequence.sample_instants == baseline_sequence.sample_instants
            assert actual_sequence.distances == pytest.approx(baseline_sequence.distances, rel=1e-12, abs=1e-15)
            for actual_disk, expected_disk in zip(actual_sequence.appearances, baseline_sequence.appearances):
                compare(actual_disk, expected_disk)
        for body in ('venus', 'mercury'):
            descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(body)
            value = FrozenEarthDiskSequenceRequest(descriptor, instant, 'utc', 1., 1,
                descriptor.display_name, descriptor.physical_radius_km, descriptor.radius_model)
            baseline = FrozenEarthDiskSequenceRealizer(source_factory=lambda observer: raw).sequence(value, observer=observer)
            actual = FrozenEarthDiskSequenceRealizer().sequence(value, observer=observer)
            assert actual.sample_instants == baseline.sample_instants
            assert actual.frozen_earth_state.position == pytest.approx(baseline.frozen_earth_state.position, abs=1e-15)
            for actual_disk, expected_disk in zip(actual.disks, baseline.disks):
                compare(actual_disk, expected_disk)
                assert actual_disk.direction.vector_icrf_au == pytest.approx(expected_disk.direction.vector_icrf_au, abs=1e-15)
    finally:
        observer.close()
