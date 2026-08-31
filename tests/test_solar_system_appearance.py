"""Physical Solar-System appearance contracts and Venus-first geometry."""

from dataclasses import FrozenInstanceError, replace
from math import asin, atan2, cos, degrees, radians, sin

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalPoints,
    SphericalPolygons,
)
from wenu.solar_system_disk_geometry import (
    DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES,
    SOLAR_SYSTEM_DISK_GEOMETRY_MODEL,
    SolarSystemDiskGeometry,
    SolarSystemDiskGeometryRealizer,
)
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


def _vector(longitude_deg, latitude_deg):
    longitude = np.radians(np.asarray(longitude_deg, dtype=float))
    latitude = np.radians(np.asarray(latitude_deg, dtype=float))
    cos_latitude = np.cos(latitude)
    return np.column_stack((
        cos_latitude * np.cos(longitude),
        cos_latitude * np.sin(longitude),
        np.sin(latitude),
    ))


def _disk_coordinates(longitude_deg, latitude_deg, appearance):
    centre_longitude = float(
        appearance.apparent_direction.geometry.lon_deg[0]
    )
    centre_latitude = float(
        appearance.apparent_direction.geometry.lat_deg[0]
    )
    longitude = radians(centre_longitude)
    latitude = radians(centre_latitude)
    centre = np.asarray((
        cos(latitude) * cos(longitude),
        cos(latitude) * sin(longitude),
        sin(latitude),
    ))
    north = np.asarray((
        -sin(latitude) * cos(longitude),
        -sin(latitude) * sin(longitude),
        cos(latitude),
    ))
    east = np.asarray((-sin(longitude), cos(longitude), 0.0))
    angle = radians(appearance.bright_limb_position_angle_deg)
    bright = cos(angle) * north + sin(angle) * east
    perpendicular = -sin(angle) * north + cos(angle) * east
    vectors = _vector(longitude_deg, latitude_deg)
    dot = np.clip(vectors @ centre, -1.0, 1.0)
    radial = np.arccos(dot)
    tangent = vectors - dot[:, np.newaxis] * centre
    length = np.linalg.norm(tangent, axis=1)
    unit = np.zeros_like(tangent)
    nonzero = length > 1.0e-14
    unit[nonzero] = tangent[nonzero] / length[nonzero, np.newaxis]
    radius = radians(appearance.angular_diameter_arcsec / 7200.0)
    fraction = radial / radius
    return (
        fraction * (unit @ bright),
        fraction * (unit @ perpendicular),
    )


def _polygon_area(x, y):
    return 0.5 * abs(
        np.dot(x, np.roll(y, -1))
        - np.dot(y, np.roll(x, -1))
    )


def test_disk_geometry_builds_physical_semantic_records():
    appearance = realized()
    result = SolarSystemDiskGeometryRealizer().geometry(appearance)

    assert isinstance(result, SolarSystemDiskGeometry)
    assert result.appearance is appearance
    assert isinstance(result.centre, SphericalPoints)
    assert isinstance(result.limb, SphericalCurves)
    assert isinstance(result.terminator, SphericalCurves)
    assert isinstance(result.illuminated_face, SphericalPolygons)
    assert result.samples == DEFAULT_SOLAR_SYSTEM_DISK_SAMPLES
    assert len(result.limb.lon_deg[0]) == result.samples
    assert len(result.terminator.lon_deg[0]) == result.samples // 2 + 1
    assert len(result.illuminated_face.lon_deg[0]) == result.samples
    assert result.limb.closed.tolist() == [True]
    assert result.terminator.closed.tolist() == [False]
    assert result.limb.coordinate_spec == (
        appearance.apparent_direction.geometry.coordinate_spec
    )
    assert result.terminator.coordinate_spec == result.limb.coordinate_spec
    assert (
        result.illuminated_face.coordinate_spec
        == result.limb.coordinate_spec
    )
    assert result.centre.metadata["component"] == "centre"
    assert result.limb.metadata["component"] == "limb"
    assert result.terminator.metadata["component"] == "terminator"
    assert (
        result.illuminated_face.metadata["component"]
        == "illuminated_face"
    )
    assert (
        result.limb.metadata["geometry_model"]
        == SOLAR_SYSTEM_DISK_GEOMETRY_MODEL
    )
    assert result.limb.metadata["angular_radius_arcsec"] == pytest.approx(
        0.5 * appearance.angular_diameter_arcsec
    )


def test_limb_has_constant_physical_angular_radius():
    appearance = realized()
    result = SolarSystemDiskGeometryRealizer().geometry(
        appearance,
        samples=120,
    )
    x, y = _disk_coordinates(
        result.limb.lon_deg[0],
        result.limb.lat_deg[0],
        appearance,
    )

    assert np.hypot(x, y) == pytest.approx(
        np.ones(120),
        abs=2.0e-13,
    )


def test_quarter_phase_terminator_is_a_diameter_with_limb_endpoints():
    appearance = realized()
    result = SolarSystemDiskGeometryRealizer().geometry(
        appearance,
        samples=120,
    )
    x, y = _disk_coordinates(
        result.terminator.lon_deg[0],
        result.terminator.lat_deg[0],
        appearance,
    )

    assert x == pytest.approx(np.zeros(61), abs=2.0e-13)
    assert y[0] == pytest.approx(1.0)
    assert y[-1] == pytest.approx(-1.0)
    assert np.min(np.hypot(x, y)) == pytest.approx(0.0, abs=2.0e-13)
    face_vectors = _vector(
        result.illuminated_face.lon_deg[0],
        result.illuminated_face.lat_deg[0],
    )
    terminator_vectors = _vector(
        result.terminator.lon_deg[0],
        result.terminator.lat_deg[0],
    )
    assert terminator_vectors[0] == pytest.approx(face_vectors[60])
    assert terminator_vectors[-1] == pytest.approx(face_vectors[0])


@pytest.mark.parametrize(
    ("phase_angle_deg", "expected_fraction"),
    ((0.0, 1.0), (60.0, 0.75), (90.0, 0.5),
     (120.0, 0.25), (180.0, 0.0)),
)
def test_illuminated_polygon_has_spherical_phase_area(
    phase_angle_deg,
    expected_fraction,
):
    appearance = replace(
        realized(),
        phase_angle_deg=phase_angle_deg,
        illuminated_fraction=expected_fraction,
    )
    result = SolarSystemDiskGeometryRealizer().geometry(
        appearance,
        samples=720,
    )
    x, y = _disk_coordinates(
        result.illuminated_face.lon_deg[0],
        result.illuminated_face.lat_deg[0],
        appearance,
    )

    assert _polygon_area(x, y) / np.pi == pytest.approx(
        expected_fraction,
        abs=1.5e-5,
    )


@pytest.mark.parametrize("position_angle_deg", (0.0, 37.0, 90.0, 295.0))
def test_bright_limb_midpoint_follows_accepted_position_angle(
    position_angle_deg,
):
    appearance = replace(
        realized(),
        phase_angle_deg=120.0,
        illuminated_fraction=0.25,
        bright_limb_position_angle_deg=position_angle_deg,
    )
    result = SolarSystemDiskGeometryRealizer().geometry(
        appearance,
        samples=120,
    )
    midpoint = 30
    centre_ra = radians(float(result.centre.lon_deg[0]))
    centre_dec = radians(float(result.centre.lat_deg[0]))
    point_ra = radians(
        float(result.illuminated_face.lon_deg[0][midpoint])
    )
    point_dec = radians(
        float(result.illuminated_face.lat_deg[0][midpoint])
    )
    delta_ra = point_ra - centre_ra
    measured = degrees(atan2(
        np.cos(point_dec) * np.sin(delta_ra),
        (
            np.sin(point_dec) * np.cos(centre_dec)
            - np.cos(point_dec) * np.sin(centre_dec)
            * np.cos(delta_ra)
        ),
    )) % 360.0

    assert measured == pytest.approx(position_angle_deg, abs=2.0e-12)


def test_disk_geometry_preserves_centre_identity_and_provenance():
    appearance = realized()
    result = SolarSystemDiskGeometryRealizer().geometry(
        appearance,
        samples=120,
    )

    assert result.centre.lon_deg.tolist() == (
        appearance.apparent_direction.geometry.lon_deg.tolist()
    )
    assert result.centre.lat_deg.tolist() == (
        appearance.apparent_direction.geometry.lat_deg.tolist()
    )
    assert result.centre.ids.tolist() == ["venus"]
    assert result.centre.labels.tolist() == ["Venus"]
    for geometry in (
        result.centre,
        result.limb,
        result.terminator,
        result.illuminated_face,
    ):
        assert geometry.metadata["target"] == "venus"
        assert geometry.metadata["samples"] == 120
        assert geometry.metadata["provenance"] == appearance.provenance


@pytest.mark.parametrize("samples", (0, 14, 17))
def test_disk_geometry_rejects_invalid_sample_counts(samples):
    with pytest.raises(ValueError):
        SolarSystemDiskGeometryRealizer().geometry(
            realized(),
            samples=samples,
        )


@pytest.mark.parametrize("samples", (True, 16.0, "16"))
def test_disk_geometry_requires_integer_sample_count(samples):
    with pytest.raises(TypeError):
        SolarSystemDiskGeometryRealizer().geometry(
            realized(),
            samples=samples,
        )


def test_disk_geometry_requires_appearance_state_and_is_frozen():
    realizer = SolarSystemDiskGeometryRealizer()
    with pytest.raises(TypeError):
        realizer.geometry(object())

    result = realizer.geometry(realized(), samples=16)
    with pytest.raises(FrozenInstanceError):
        result.samples = 18
