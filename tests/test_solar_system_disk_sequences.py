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
from wenu.solar_system_disk_sequences import (
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
    instant = sample_observer.t_astropy.isot
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
