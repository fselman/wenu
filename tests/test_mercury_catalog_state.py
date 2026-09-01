"""Output-neutral Mercury registration and frozen-state contracts."""

from dataclasses import FrozenInstanceError
from math import asin, degrees

import pytest

from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.sky.frozen_earth_disk_sequences import (
    FrozenEarthDiskSequenceRealizer,
    FrozenEarthDiskSequenceRequest,
)
from wenu.sky.mercury import (
    MERCURY_BODY,
    MERCURY_MEAN_RADIUS_KM,
    MERCURY_NAIF_BODY_ID,
    MERCURY_RADIUS_MODEL,
)
from wenu.sky.solar_system_bodies import (
    FROZEN_EARTH_DISK_SEQUENCE,
    OBSERVED_DISK_SEQUENCE,
    RESOLVED_SPHERICAL_DISK,
    SYMBOLIC_POINT,
)
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
from wenu.solar_system_appearance import AU_KM


RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="DE440-test",
    filename="deterministic.bsp",
    sha256="b" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)


class Source:
    resource = RESOURCE

    def __init__(self):
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        if request.target == "earth":
            position = (1.0, 0.0, 0.0)
            target_id = "399"
        else:
            sample = sum(item.target == "mercury" for item in self.requests)
            position = (1.0, float(sample), 0.0)
            target_id = "1"
        return EphemerisState(
            request=request,
            position=position,
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id=target_id,
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


def request():
    return FrozenEarthDiskSequenceRequest(
        descriptor=MERCURY_BODY,
        start_instant="2026-08-30T00:00:00Z",
        start_time_scale="utc",
        step_days=2.0,
        n_steps=2,
        display_name=MERCURY_BODY.display_name,
        physical_radius_km=MERCURY_BODY.physical_radius_km,
        radius_model=MERCURY_BODY.radius_model,
    )


def test_mercury_is_one_immutable_output_neutral_catalog_registration():
    assert SOLAR_SYSTEM_BODY_CATALOG.resolve("mercury") is MERCURY_BODY
    assert MERCURY_BODY.physical_body_id == MERCURY_NAIF_BODY_ID == "199"
    assert MERCURY_BODY.physical_radius_km == MERCURY_MEAN_RADIUS_KM == 2439.4
    assert MERCURY_MEAN_RADIUS_KM != 2440.53
    assert "equal-volume mean radius" in MERCURY_RADIUS_MODEL
    assert MERCURY_BODY.supports(FROZEN_EARTH_DISK_SEQUENCE)
    assert MERCURY_BODY.supports(SYMBOLIC_POINT)
    for capability in (
        RESOLVED_SPHERICAL_DISK,
        OBSERVED_DISK_SEQUENCE,
    ):
        assert not MERCURY_BODY.supports(capability)
    with pytest.raises(FrozenInstanceError):
        MERCURY_BODY.target = "venus"


def test_generic_frozen_state_retains_mercury_identity_and_provider_ids():
    source = Source()
    result = FrozenEarthDiskSequenceRealizer(
        source_factory=lambda observer: source,
        coordinate_service=IdentityCoordinates(),
    ).sequence(request(), observer=object())

    assert [item.target for item in source.requests] == [
        "earth", "mercury", "mercury", "mercury",
    ]
    assert result.request.descriptor is MERCURY_BODY
    for distance, disk in enumerate(result.disks, start=1):
        assert disk.target == "mercury"
        assert disk.physical_radius_km == MERCURY_MEAN_RADIUS_KM
        assert disk.radius_model == MERCURY_RADIUS_MODEL
        assert disk.direction.provider_target_id == "1"
        assert disk.direction.provider_centre_id == "10"
        assert disk.direction.distance_au == float(distance)
        expected = 2.0 * degrees(asin(
            (MERCURY_MEAN_RADIUS_KM / AU_KM) / distance
        )) * 3600.0
        assert disk.angular_diameter_arcsec == pytest.approx(expected)
    assert "target: mercury" in " ".join(result.provenance)
