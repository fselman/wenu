"""Output-neutral lunar physical-appearance contracts for 49I.3E.1."""

from dataclasses import FrozenInstanceError
from math import asin, degrees

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.earth import EARTH_BODY, EARTH_NAIF_BODY_ID
from wenu.sky.moon import (
    MOON_BODY,
    MOON_MEAN_RADIUS_KM,
    MOON_NAIF_BODY_ID,
    MOON_RADIUS_MODEL,
)
from wenu.sky.solar_system_bodies import (
    OBSERVED_DISK_SEQUENCE,
    RESOLVED_SPHERICAL_DISK,
    SPHERICAL_PHYSICAL_APPEARANCE,
    SYMBOLIC_POINT,
)
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG
from wenu.solar_system_appearance import (
    AU_KM,
    BRIGHT_LIMB_POSITION_ANGLE_CONVENTION,
    SolarSystemAppearanceRealizer,
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
    sha256="c" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)
INSTANT = "2026-08-30T00:00:00.000"
OBSERVER = ObserverBarycentricState(
    observer_id="La Ligua 52 m",
    centre="solar system barycenter",
    frame="icrf",
    instant=INSTANT,
    time_scale="tdb",
    position=(0.0, 0.0, 0.0),
    velocity=(0.0, 0.0, 0.0),
    position_unit="au",
    velocity_unit="au/day",
    resource=RESOURCE,
    provider_observer_id="WGS84 site",
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
        corrections=frozenset(("one-way-light-time",)),
    )


def _apparent(target, longitude, *, distance, provider_id):
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
            np.asarray((0.0,)),
            coordinate_spec=_spec(PositionStatus.ASTROMETRIC),
            ids=np.asarray((target,), dtype=object),
        ),
        distance_au=distance,
        relative_velocity_au_per_day=(0.0, 0.0, 0.0),
        light_time_days=distance / 173.1446326846693,
        emission_instant="2026-08-29T23:59:58.700",
        emission_time_scale="tdb",
        iterations=2,
        target_provider_id=provider_id,
    )
    return ApparentDirection(
        astrometric=astrometric,
        policy=ApparentCorrectionPolicy(),
        geometry=SphericalPoints(
            np.asarray((longitude,)),
            np.asarray((0.0,)),
            coordinate_spec=_spec(PositionStatus.APPARENT),
            ids=np.asarray((target,), dtype=object),
        ),
    )


class SunSource:
    resource = RESOURCE

    def state(self, request):
        return EphemerisState(
            request=request,
            position=(0.00257, 1.0, 0.0),
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="10",
            provider_centre_id="0",
        )


def test_moon_and_earth_share_one_catalog_relationship_and_identity():
    assert SOLAR_SYSTEM_BODY_CATALOG.resolve("earth") is EARTH_BODY
    assert SOLAR_SYSTEM_BODY_CATALOG.resolve("moon") is MOON_BODY
    assert SOLAR_SYSTEM_BODY_CATALOG.children_of("earth") == (MOON_BODY,)
    assert EARTH_BODY.physical_body_id == EARTH_NAIF_BODY_ID == "399"
    assert MOON_BODY.physical_body_id == MOON_NAIF_BODY_ID == "301"
    assert MOON_BODY.parent_body_key == "earth"
    assert MOON_BODY.body_class == "natural_satellite"
    assert MOON_BODY.display_name_for("es") == "Luna"
    assert MOON_BODY.supports(SYMBOLIC_POINT)
    assert MOON_BODY.supports(SPHERICAL_PHYSICAL_APPEARANCE)
    assert MOON_BODY.supports(RESOLVED_SPHERICAL_DISK)
    assert not MOON_BODY.supports(OBSERVED_DISK_SEQUENCE)
    with pytest.raises(FrozenInstanceError):
        MOON_BODY.physical_radius_km = 1.0


def test_moon_uses_jpl_equal_volume_mean_radius():
    assert MOON_MEAN_RADIUS_KM == 1737.4
    assert "equal-volume mean radius" in MOON_RADIUS_MODEL
    assert "1737.4 km" in MOON_RADIUS_MODEL


def test_generic_appearance_realizer_produces_immutable_lunar_state():
    distance = 0.00257
    moon = _apparent(
        "moon", 0.0, distance=distance, provider_id=MOON_NAIF_BODY_ID
    )
    sun = _apparent("sun", 90.0, distance=1.0, provider_id="10")
    result = SolarSystemAppearanceRealizer().appearance(
        SunSource(),
        moon,
        sun,
        display_name=MOON_BODY.display_name,
        physical_radius_km=MOON_BODY.physical_radius_km,
        radius_model=MOON_BODY.radius_model,
    )

    expected = 2.0 * degrees(asin(
        (MOON_MEAN_RADIUS_KM / AU_KM) / distance
    )) * 3600.0
    assert result.target == "moon"
    assert result.apparent_direction is moon
    assert result.sun_apparent_direction is sun
    assert result.physical_radius_km == MOON_MEAN_RADIUS_KM
    assert result.radius_model == MOON_RADIUS_MODEL
    assert result.angular_diameter_arcsec == pytest.approx(expected)
    assert result.phase_angle_deg == pytest.approx(90.0)
    assert result.illuminated_fraction == pytest.approx(0.5)
    assert result.bright_limb_position_angle_deg == pytest.approx(90.0)
    assert (
        result.position_angle_convention
        == BRIGHT_LIMB_POSITION_ANGLE_CONVENTION
    )
    assert not hasattr(result, "display_magnification")
    with pytest.raises(FrozenInstanceError):
        result.illuminated_fraction = 0.0
