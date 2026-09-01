"""Output-neutral Mercury frozen-Earth sequence contracts."""

from dataclasses import FrozenInstanceError
from math import asin, degrees

import pytest

from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.sky.frozen_earth_disk_sequences import (
    FROZEN_EARTH_DISTANCE_ORIGIN,
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.mercury import (
    MERCURY_NAIF_BODY_ID,
    MERCURY_POINT,
    MERCURY_RADIUS_MODEL,
)
from wenu.solar_system_appearance import AU_KM, MERCURY_MEAN_RADIUS_KM


RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="DE440-test",
    filename="deterministic.bsp",
    sha256="b" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)


class MercurySource:
    resource = RESOURCE

    def __init__(self):
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        if request.target == "earth":
            position = (1.0, 0.0, 0.0)
            provider_target_id = "399"
        else:
            sample = sum(item.target == "mercury" for item in self.requests)
            position = (1.0, float(sample), 0.0)
            provider_target_id = "1"
        return EphemerisState(
            request=request,
            position=position,
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id=provider_target_id,
            provider_centre_id="10",
        )


class IdentityCoordinates:
    def transform(self, geometry, target_spec):
        return type(geometry)(
            geometry.lon_deg.copy(),
            geometry.lat_deg.copy(),
            coordinate_spec=target_spec,
            ids=geometry.ids.copy(),
        )


def test_mercury_identity_and_adopted_radius_are_stable_and_immutable():
    assert MERCURY_POINT.target == "mercury"
    assert MERCURY_POINT.entity_key == "mercury"
    assert MERCURY_POINT.display_name == "Mercury"
    assert MERCURY_POINT.selection_key == "mercury"
    assert MERCURY_NAIF_BODY_ID == "199"
    assert MERCURY_MEAN_RADIUS_KM == 2439.4
    assert MERCURY_MEAN_RADIUS_KM != 2440.53
    assert "equal-volume mean radius" in MERCURY_RADIUS_MODEL
    with pytest.raises(FrozenInstanceError):
        MERCURY_POINT.target = "venus"


def test_generic_sequence_retains_mercury_state_and_physical_distance():
    source = MercurySource()
    request = FrozenEarthDiskSequenceRequest(
        descriptor=MERCURY_POINT,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        step_days=2.0,
        n_steps=2,
        display_name=MERCURY_POINT.display_name,
        physical_radius_km=MERCURY_MEAN_RADIUS_KM,
        radius_model=MERCURY_RADIUS_MODEL,
    )
    result = FrozenEarthDiskSequenceRealizer(
        source_factory=lambda observer: source,
        coordinate_service=IdentityCoordinates(),
    ).sequence(request, observer=object())

    assert [item.target for item in source.requests] == [
        "earth", "mercury", "mercury", "mercury",
    ]
    assert result.request.descriptor is MERCURY_POINT
    assert result.distance_origin == FROZEN_EARTH_DISTANCE_ORIGIN
    assert result.distance_unit == "au"
    assert result.sample_instants == (
        "2026-08-30T00:00:00.000000000",
        "2026-09-01T00:00:00.000000000",
        "2026-09-03T00:00:00.000000000",
    )
    for distance, disk in enumerate(result.disks, start=1):
        assert disk.target == "mercury"
        assert disk.display_name == "Mercury"
        assert disk.physical_radius_km == MERCURY_MEAN_RADIUS_KM
        assert disk.radius_model == MERCURY_RADIUS_MODEL
        assert disk.direction.provider_target_id == "1"
        assert disk.direction.provider_centre_id == "10"
        assert disk.direction.distance_au == float(distance)
        assert disk.direction.vector_icrf_au == (0.0, float(distance), 0.0)
        expected = 2.0 * degrees(asin(
            (MERCURY_MEAN_RADIUS_KM / AU_KM) / distance
        )) * 3600.0
        assert disk.angular_diameter_arcsec == pytest.approx(expected)
    assert (
        result.disks[0].angular_diameter_arcsec
        > result.disks[-1].angular_diameter_arcsec
    )
    provenance = " ".join(result.provenance)
    assert "DE440-test" in provenance
    assert RESOURCE.sha256 in provenance
    assert "not apparent" in provenance
    assert "target: mercury" in provenance
