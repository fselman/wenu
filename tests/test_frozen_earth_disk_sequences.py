"""Frozen-Earth geometric disk-sequence scientific contracts."""

from dataclasses import FrozenInstanceError, replace
from math import asin, cos, degrees, radians

import numpy as np
import pytest

from wenu.coordinates import PositionStatus
from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.sky.frozen_earth_disk_sequences import (
    FROZEN_EARTH_DISTANCE_ORIGIN,
    FROZEN_EARTH_DISTANCE_UNIT,
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.solar_system_appearance import AU_KM, VENUS_MEAN_RADIUS_KM


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
    entity_key="solar_system.planets.venus",
    display_name="Venus",
    selection_key="venus",
)


def request(**changes):
    values = dict(
        descriptor=DESCRIPTOR,
        start_instant="2026-08-30T00:00:00",
        start_time_scale="utc",
        step_days=7.0,
        n_steps=2,
        display_name="Venus",
        physical_radius_km=VENUS_MEAN_RADIUS_KM,
        radius_model="JPL mean Venus radius",
    )
    values.update(changes)
    return FrozenEarthDiskSequenceRequest(**values)


class Source:
    resource = RESOURCE

    def __init__(self, *, position_unit="au", mismatch=False):
        self.position_unit = position_unit
        self.mismatch = mismatch
        self.requests = []

    def state(self, state_request):
        self.requests.append(state_request)
        if state_request.target == "earth":
            position = (1.0, 0.0, 0.0)
            target_id = "399"
        else:
            sample = len(
                [item for item in self.requests if item.target == "venus"]
            )
            position = (1.0, float(sample), 0.0)
            target_id = "299"
        returned_request = (
            replace(state_request, target="mars")
            if self.mismatch
            else state_request
        )
        return EphemerisState(
            request=returned_request,
            position=position,
            velocity=(0.0, 0.0, 0.0),
            position_unit=self.position_unit,
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id=target_id,
            provider_centre_id="10",
        )


class CoordinateServiceStub:
    def __init__(self):
        self.calls = []

    def transform(self, geometry, target_spec):
        self.calls.append((geometry, target_spec))
        return type(geometry)(
            geometry.lon_deg.copy(),
            geometry.lat_deg.copy(),
            coordinate_spec=target_spec,
            ids=geometry.ids.copy(),
        )


def realize(value=None, *, source=None):
    source = Source() if source is None else source
    coordinates = CoordinateServiceStub()
    result = FrozenEarthDiskSequenceRealizer(
        source_factory=lambda observer: source,
        coordinate_service=coordinates,
    ).sequence(request() if value is None else value, observer=object())
    return result, source, coordinates


def test_request_is_start_inclusive_and_strictly_validated():
    value = request(n_steps=0)
    assert value.sample_count == 1
    assert request().sample_offsets_days == (0.0, 7.0, 14.0)
    assert value.start_instant == "2026-08-30T00:00:00.000000000"
    assert value.start_time_scale == "utc"
    with pytest.raises(ValueError, match="step_days"):
        request(step_days=0.0)
    with pytest.raises(ValueError, match="n_steps"):
        request(n_steps=-1)
    with pytest.raises(TypeError, match="n_steps"):
        request(n_steps=True)


def test_sequence_freezes_earth_once_and_samples_only_major_epochs():
    result, source, _ = realize()
    assert len(result.disks) == len(result.sample_instants) == 3
    assert [item.target for item in source.requests] == [
        "earth",
        "venus",
        "venus",
        "venus",
    ]
    assert source.requests[0].instant == result.sample_instants[0]
    assert result.sample_instants == (
        "2026-08-30T00:00:00.000000000",
        "2026-09-06T00:00:00.000000000",
        "2026-09-13T00:00:00.000000000",
    )


def test_sequence_retains_vectors_distances_and_fixed_sun():
    result, _, _ = realize()
    assert result.frozen_earth_state.position == (1.0, 0.0, 0.0)
    assert result.distance_origin == FROZEN_EARTH_DISTANCE_ORIGIN
    assert result.distance_unit == FROZEN_EARTH_DISTANCE_UNIT
    for sample, disk in enumerate(result.disks, start=1):
        assert disk.direction.vector_icrf_au == (0.0, float(sample), 0.0)
        assert disk.direction.distance_au == float(sample)
        assert disk.direction.provider_target_id == "299"
        assert disk.direction.provider_centre_id == "10"
        assert disk.direction.frozen_earth_heliocentric_icrf_au == (
            1.0,
            0.0,
            0.0,
        )
        assert np.allclose(disk.sun_direction.lon_deg, (180.0,))
        assert np.allclose(disk.sun_direction.lat_deg, (0.0,))
    assert np.allclose(result.sun_direction.lon_deg, (180.0,))


def test_disk_physics_uses_frozen_observer_geometry():
    result, _, _ = realize()
    first = result.disks[0]
    expected_phase = 45.0
    expected_fraction = 0.5 * (1.0 + cos(radians(expected_phase)))
    radius_au = VENUS_MEAN_RADIUS_KM / AU_KM
    expected_diameter = 2.0 * degrees(asin(radius_au)) * 3600.0
    assert first.phase_angle_deg == pytest.approx(expected_phase)
    assert first.illuminated_fraction == pytest.approx(expected_fraction)
    assert first.angular_diameter_arcsec == pytest.approx(expected_diameter)
    assert first.bright_limb_position_angle_deg == pytest.approx(90.0)


def test_all_directions_use_fixed_geometric_ecliptic_contract():
    result, _, coordinates = realize()
    assert len(coordinates.calls) == 6
    for disk in result.disks:
        for geometry in (disk.direction.geometry, disk.sun_direction):
            spec = geometry.coordinate_spec
            assert spec.frame == "barycentric-mean-ecliptic"
            assert spec.origin == "frozen-earth"
            assert spec.position_status is PositionStatus.GEOMETRIC
            assert spec.equinox == "J2000.0"
            assert spec.corrections == frozenset()


def test_sequence_is_immutable_and_records_reproducibility():
    result, _, _ = realize()
    with pytest.raises(FrozenInstanceError):
        result.distance_unit = "km"
    joined = " ".join(result.provenance)
    assert "not apparent" in joined
    assert RESOURCE.model in joined
    assert RESOURCE.sha256 in joined


def test_source_state_identity_and_units_are_enforced():
    with pytest.raises(ValueError, match="mismatched"):
        realize(source=Source(mismatch=True))
    with pytest.raises(ValueError, match="AU positions"):
        realize(source=Source(position_unit="km"))


def test_realizer_rejects_wrong_request_type():
    with pytest.raises(TypeError, match="FrozenEarthDiskSequenceRequest"):
        FrozenEarthDiskSequenceRealizer(
            source_factory=lambda observer: Source(),
            coordinate_service=CoordinateServiceStub(),
        ).sequence(object(), observer=object())
