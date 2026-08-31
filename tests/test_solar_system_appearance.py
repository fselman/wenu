"""Physical Solar-System appearance contracts and Venus-first geometry."""

from dataclasses import FrozenInstanceError, replace
from math import asin, degrees

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.solar_system_appearance import (
    AU_KM,
    BRIGHT_LIMB_POSITION_ANGLE_CONVENTION,
    SolarSystemAppearanceGeometryError,
    SolarSystemAppearanceIdentityError,
    SolarSystemAppearanceRealizer,
    VENUS_MEAN_RADIUS_KM,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
    ApparentDirection,
    AstrometricDirection,
    AstrometricDirectionRequest,
    ObserverBarycentricState,
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
INSTANT = "2026-08-30T00:00:00.000"
OBSERVER = ObserverBarycentricState(
    observer_id="La Ligua",
    centre="solar system barycenter",
    frame="icrf",
    instant=INSTANT,
    time_scale="tdb",
    position=(0.0, 0.0, 0.0),
    velocity=(0.0, 0.0, 0.0),
    position_unit="au",
    velocity_unit="au/day",
    resource=RESOURCE,
    provider_observer_id="test site",
    provider_centre_id="0",
)


def _spec(status):
    return CoordinateSpec(
        frame="icrs",
        origin="observer",
        position_status=status,
        instant=INSTANT,
        time_scale="tdb",
        provider=RESOURCE.provider,
        model=RESOURCE.model,
        corrections=(
            frozenset(("one-way-light-time",))
            if status is PositionStatus.ASTROMETRIC
            else frozenset(
                (
                    "one-way-light-time",
                    "aberration",
                    "gravitational-deflection",
                    "earth-gravitational-deflection",
                )
            )
        ),
    )


def apparent(target, *, longitude, latitude=0.0, distance=1.0):
    request = AstrometricDirectionRequest(
        target=target,
        centre="solar system barycenter",
        reception_instant=INSTANT,
        reception_time_scale="tdb",
    )
    astrometric = AstrometricDirection(
        request=request,
        observer_state=OBSERVER,
        geometry=SphericalPoints(
            np.asarray((longitude,)),
            np.asarray((latitude,)),
            coordinate_spec=_spec(PositionStatus.ASTROMETRIC),
            ids=np.asarray((target,), dtype=object),
        ),
        distance_au=distance,
        relative_velocity_au_per_day=(0.0, 0.0, 0.0),
        light_time_days=distance / 173.1446326846693,
        emission_instant="2026-08-29T23:51:40.995",
        emission_time_scale="tdb",
        iterations=2,
        target_provider_id="10" if target == "sun" else "299",
    )
    return ApparentDirection(
        astrometric=astrometric,
        policy=ApparentCorrectionPolicy(),
        geometry=SphericalPoints(
            np.asarray((longitude,)),
            np.asarray((latitude,)),
            coordinate_spec=_spec(PositionStatus.APPARENT),
            ids=np.asarray((target,), dtype=object),
        ),
    )


class SunSource:
    def __init__(
        self,
        *,
        position=(1.0, 1.0, 0.0),
        resource=RESOURCE,
        provider_target_id="10",
    ):
        self.position = position
        self.resource = resource
        self.provider_target_id = provider_target_id
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        return EphemerisState(
            request=request,
            position=self.position,
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=self.resource,
            provider_target_id=self.provider_target_id,
            provider_centre_id="0",
        )


def realized(**overrides):
    values = dict(
        source=SunSource(),
        apparent_direction=apparent("venus", longitude=0.0),
        sun_apparent_direction=apparent("sun", longitude=90.0),
        display_name="Venus",
        physical_radius_km=0.1 * AU_KM,
        radius_model="deterministic spherical Venus",
    )
    values.update(overrides)
    return SolarSystemAppearanceRealizer().appearance(**values)


def test_realizer_retains_physical_state_and_explicit_conventions():
    source = SunSource()
    result = realized(source=source)

    assert result.target == "venus"
    assert result.display_name == "Venus"
    assert result.physical_radius_km == pytest.approx(0.1 * AU_KM)
    assert result.radius_model == "deterministic spherical Venus"
    assert result.angular_diameter_arcsec == pytest.approx(
        2.0 * degrees(asin(0.1)) * 3600.0
    )
    assert result.phase_angle_deg == pytest.approx(90.0)
    assert result.illuminated_fraction == pytest.approx(0.5)
    assert result.bright_limb_position_angle_deg == pytest.approx(90.0)
    assert (
        result.position_angle_convention
        == BRIGHT_LIMB_POSITION_ANGLE_CONVENTION
    )
    assert source.requests[0].target == "sun"
    assert source.requests[0].instant == INSTANT
    assert "target distance from accepted retarded" in result.provenance[0]
    assert result.apparent_direction.astrometric.request.target == "venus"

    with pytest.raises(FrozenInstanceError):
        result.phase_angle_deg = 0.0


def test_venus_radius_constant_uses_jpl_mean_radius():
    assert VENUS_MEAN_RADIUS_KM == 6051.8
    result = realized(
        physical_radius_km=VENUS_MEAN_RADIUS_KM,
        radius_model="JPL planetary physical parameters mean radius",
    )
    assert result.physical_radius_km == VENUS_MEAN_RADIUS_KM
    assert result.angular_diameter_arcsec > 0.0


def test_bright_limb_position_angle_is_north_through_east():
    east = realized(
        sun_apparent_direction=apparent("sun", longitude=90.0),
    )
    west = realized(
        source=SunSource(position=(1.0, -1.0, 0.0)),
        sun_apparent_direction=apparent("sun", longitude=270.0),
    )

    assert east.bright_limb_position_angle_deg == pytest.approx(90.0)
    assert west.bright_limb_position_angle_deg == pytest.approx(270.0)


def test_realizer_rejects_inconsistent_sun_direction_or_resource():
    with pytest.raises(
        SolarSystemAppearanceIdentityError,
        match="target='sun'",
    ):
        realized(
            sun_apparent_direction=apparent("mars", longitude=90.0),
        )

    other = replace(RESOURCE, sha256="b" * 64)
    with pytest.raises(
        SolarSystemAppearanceIdentityError,
        match="same resource",
    ):
        realized(source=SunSource(resource=other))


def test_realizer_rejects_undefined_orientation_and_impossible_radius():
    with pytest.raises(
        SolarSystemAppearanceGeometryError,
        match="coincident",
    ):
        realized(
            sun_apparent_direction=apparent("sun", longitude=0.0),
        )

    with pytest.raises(
        SolarSystemAppearanceGeometryError,
        match="smaller",
    ):
        realized(physical_radius_km=AU_KM)


@pytest.mark.parametrize(
    ("changes", "message"),
    (
        ({"angular_diameter_arcsec": 0.0}, "angular_diameter_arcsec"),
        ({"phase_angle_deg": -1.0}, "phase_angle_deg"),
        ({"illuminated_fraction": 1.1}, "illuminated_fraction"),
        (
            {"bright_limb_position_angle_deg": 360.0},
            "bright_limb_position_angle_deg",
        ),
    ),
)
def test_physical_state_rejects_invalid_scalar_values(changes, message):
    result = realized()
    with pytest.raises(ValueError, match=message):
        replace(result, **changes)
