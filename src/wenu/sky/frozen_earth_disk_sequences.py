"""Frozen-Earth geometric planet-disk sequence state."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import asin, atan2, cos, degrees, hypot, isfinite, pi, radians, sin
from operator import index

import numpy as np
from astropy.time import Time, TimeDelta

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.ephemeris import EphemerisState, EphemerisStateRequest
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
from wenu.solar_system_appearance import AU_KM


FROZEN_EARTH_DISTANCE_ORIGIN = "frozen-earth"
FROZEN_EARTH_DISTANCE_UNIT = "au"
FROZEN_EARTH_POSITION_ANGLE_CONVENTION = (
    "frozen-Earth geometric fixed-ecliptic tangent plane; "
    "zero at ecliptic north; positive toward increasing ecliptic longitude"
)


def _text(value, *, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    result = value.strip()
    if not result:
        raise ValueError(f"{name} must be non-empty.")
    return result


def _positive(value, *, name):
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be positive and finite.")
    return result


def _count(value):
    if isinstance(value, bool):
        raise TypeError("n_steps must be an integer.")
    try:
        result = index(value)
    except TypeError as error:
        raise TypeError("n_steps must be an integer.") from error
    if result < 0:
        raise ValueError("n_steps cannot be negative.")
    return result


def _isot(value):
    result = value.copy()
    result.precision = 9
    return result.isot


def _vector(value, *, name):
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain three finite components.")
    return result


def _length(value, *, name):
    result = float(np.linalg.norm(value))
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must have positive finite length.")
    return result


def _angle(left, right):
    left_length = _length(left, name="left phase vector")
    right_length = _length(right, name="right phase vector")
    return degrees(atan2(
        float(np.linalg.norm(np.cross(left, right))),
        float(np.dot(left, right)),
    ))


def _lon_lat(vector):
    length = _length(vector, name="direction vector")
    unit = vector / length
    return (
        degrees(atan2(unit[1], unit[0])) % 360.0,
        degrees(asin(float(np.clip(unit[2], -1.0, 1.0)))),
    )


def _position_angle(target, sun):
    target_lon = radians(float(target.lon_deg[0]))
    target_lat = radians(float(target.lat_deg[0]))
    sun_lon = radians(float(sun.lon_deg[0]))
    sun_lat = radians(float(sun.lat_deg[0]))
    delta = sun_lon - target_lon
    numerator = cos(sun_lat) * sin(delta)
    denominator = (
        sin(sun_lat) * cos(target_lat)
        - cos(sun_lat) * sin(target_lat) * cos(delta)
    )
    if hypot(numerator, denominator) <= 1.0e-15:
        raise ValueError("bright-limb direction is undefined.")
    return degrees(atan2(numerator, denominator)) % 360.0


@dataclass(frozen=True)
class FrozenEarthDiskSequenceRequest:
    """Exact major epochs for one frozen-Earth geometric construction."""

    descriptor: SolarSystemPointDescriptor
    start_instant: str
    start_time_scale: str
    step_days: float
    n_steps: int
    display_name: str
    physical_radius_km: float
    radius_model: str
    ecliptic_equinox: str = "J2000.0"

    def __post_init__(self):
        if not isinstance(self.descriptor, SolarSystemPointDescriptor):
            raise TypeError("descriptor must be a SolarSystemPointDescriptor.")
        scale = _text(self.start_time_scale, name="start_time_scale").lower()
        try:
            start = Time(
                _text(self.start_instant, name="start_instant"),
                scale=scale,
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "start_instant must be valid in start_time_scale."
            ) from error
        object.__setattr__(self, "start_instant", _isot(start))
        object.__setattr__(self, "start_time_scale", start.scale)
        object.__setattr__(
            self,
            "step_days",
            _positive(self.step_days, name="step_days"),
        )
        object.__setattr__(self, "n_steps", _count(self.n_steps))
        object.__setattr__(
            self,
            "display_name",
            _text(self.display_name, name="display_name"),
        )
        object.__setattr__(
            self, "physical_radius_km",
            _positive(self.physical_radius_km, name="physical_radius_km"),
        )
        object.__setattr__(
            self,
            "radius_model",
            _text(self.radius_model, name="radius_model"),
        )
        object.__setattr__(
            self, "ecliptic_equinox",
            _text(self.ecliptic_equinox, name="ecliptic_equinox"),
        )

    @property
    def sample_count(self):
        return self.n_steps + 1

    @property
    def sample_offsets_days(self):
        """Exact major-step offsets, including the start."""
        return tuple(
            sample * self.step_days
            for sample in range(self.sample_count)
        )


@dataclass(frozen=True)
class FrozenEarthGeometricDirection:
    """One target direction from the fixed start-time Earth position."""

    target: str
    instant: str
    time_scale: str
    geometry: SphericalPoints
    vector_icrf_au: tuple[float, float, float]
    distance_au: float
    frozen_earth_heliocentric_icrf_au: tuple[float, float, float]

    def __post_init__(self):
        if (
            not isinstance(self.geometry, SphericalPoints)
            or len(self.geometry) != 1
        ):
            raise TypeError(
                "geometry must contain one SphericalPoints direction."
            )
        spec = self.geometry.coordinate_spec
        if spec.position_status is not PositionStatus.GEOMETRIC:
            raise ValueError("frozen-Earth direction must be geometric.")
        if spec.origin != FROZEN_EARTH_DISTANCE_ORIGIN:
            raise ValueError(
                "frozen-Earth direction must declare frozen-earth origin."
            )
        vector = _vector(self.vector_icrf_au, name="vector_icrf_au")
        earth = _vector(
            self.frozen_earth_heliocentric_icrf_au,
            name="frozen_earth_heliocentric_icrf_au",
        )
        distance = _positive(self.distance_au, name="distance_au")
        if abs(distance - _length(vector, name="vector_icrf_au")) > 1.0e-13:
            raise ValueError(
                "distance_au must equal the geometric vector length."
            )
        object.__setattr__(self, "target", _text(self.target, name="target"))
        object.__setattr__(
            self,
            "instant",
            _text(self.instant, name="instant"),
        )
        object.__setattr__(
            self,
            "time_scale",
            _text(self.time_scale, name="time_scale").lower(),
        )
        object.__setattr__(self, "vector_icrf_au", tuple(vector))
        object.__setattr__(self, "distance_au", distance)
        object.__setattr__(
            self,
            "frozen_earth_heliocentric_icrf_au",
            tuple(earth),
        )


@dataclass(frozen=True)
class FrozenEarthGeometricDisk:
    """Physical disk state from frozen-observer geometric vectors."""

    direction: FrozenEarthGeometricDirection
    sun_direction: SphericalPoints
    display_name: str
    physical_radius_km: float
    radius_model: str
    angular_diameter_arcsec: float
    phase_angle_deg: float
    illuminated_fraction: float
    bright_limb_position_angle_deg: float
    position_angle_convention: str = FROZEN_EARTH_POSITION_ANGLE_CONVENTION

    def __post_init__(self):
        if not isinstance(self.direction, FrozenEarthGeometricDirection):
            raise TypeError(
                "direction must be a FrozenEarthGeometricDirection."
            )
        if not isinstance(self.sun_direction, SphericalPoints):
            raise TypeError("sun_direction must be SphericalPoints.")
        if len(self.sun_direction) != 1:
            raise ValueError("sun_direction must contain one direction.")
        sun_spec = self.sun_direction.coordinate_spec
        if (
            sun_spec.position_status is not PositionStatus.GEOMETRIC
            or sun_spec.origin != FROZEN_EARTH_DISTANCE_ORIGIN
        ):
            raise ValueError(
                "sun_direction must be frozen-Earth geometric."
            )
        if sun_spec != self.direction.geometry.coordinate_spec:
            raise ValueError(
                "target and Sun directions must share one coordinate spec."
            )
        object.__setattr__(
            self,
            "display_name",
            _text(self.display_name, name="display_name"),
        )
        object.__setattr__(
            self,
            "physical_radius_km",
            _positive(self.physical_radius_km, name="physical_radius_km"),
        )
        object.__setattr__(
            self,
            "radius_model",
            _text(self.radius_model, name="radius_model"),
        )
        object.__setattr__(
            self,
            "angular_diameter_arcsec",
            _positive(
                self.angular_diameter_arcsec,
                name="angular_diameter_arcsec",
            ),
        )
        phase = float(self.phase_angle_deg)
        fraction = float(self.illuminated_fraction)
        position_angle = float(self.bright_limb_position_angle_deg)
        if not isfinite(phase) or not 0.0 <= phase <= 180.0:
            raise ValueError("phase_angle_deg must lie in [0, 180].")
        if not isfinite(fraction) or not 0.0 <= fraction <= 1.0:
            raise ValueError("illuminated_fraction must lie in [0, 1].")
        expected = 0.5 * (1.0 + cos(radians(phase)))
        if abs(fraction - expected) > 1.0e-12:
            raise ValueError(
                "illuminated_fraction must agree with phase_angle_deg."
            )
        if not isfinite(position_angle) or not 0.0 <= position_angle < 360.0:
            raise ValueError(
                "bright_limb_position_angle_deg must lie in [0, 360)."
            )
        object.__setattr__(self, "phase_angle_deg", phase)
        object.__setattr__(self, "illuminated_fraction", fraction)
        object.__setattr__(
            self,
            "bright_limb_position_angle_deg",
            position_angle,
        )
        object.__setattr__(
            self,
            "position_angle_convention",
            _text(
                self.position_angle_convention,
                name="position_angle_convention",
            ),
        )

    @property
    def target(self):
        return self.direction.target


@dataclass(frozen=True)
class FrozenEarthDiskSequence:
    """Frozen Earth, fixed Sun direction, and same-epoch Venus states."""

    request: FrozenEarthDiskSequenceRequest
    frozen_earth_state: EphemerisState
    sun_direction: SphericalPoints
    sample_instants: tuple[str, ...]
    disks: tuple[FrozenEarthGeometricDisk, ...]
    distance_origin: str = FROZEN_EARTH_DISTANCE_ORIGIN
    distance_unit: str = FROZEN_EARTH_DISTANCE_UNIT
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.request, FrozenEarthDiskSequenceRequest):
            raise TypeError(
                "request must be a FrozenEarthDiskSequenceRequest."
            )
        if not isinstance(self.frozen_earth_state, EphemerisState):
            raise TypeError("frozen_earth_state must be an EphemerisState.")
        if not isinstance(self.sun_direction, SphericalPoints):
            raise TypeError("sun_direction must be SphericalPoints.")
        if len(self.sun_direction) != 1:
            raise ValueError("sun_direction must contain one direction.")
        instants = tuple(
            _text(value, name="sample instant")
            for value in self.sample_instants
        )
        disks = tuple(self.disks)
        if (
            len(instants) != self.request.sample_count
            or len(disks) != self.request.sample_count
        ):
            raise ValueError("sequence must contain n_steps + 1 samples.")
        if not all(
            isinstance(disk, FrozenEarthGeometricDisk) for disk in disks
        ):
            raise TypeError(
                "disks must contain FrozenEarthGeometricDisk values."
            )
        if tuple(disk.direction.instant for disk in disks) != instants:
            raise ValueError("disk instants must equal sample_instants.")
        frozen = tuple(self.frozen_earth_state.position)
        if any(
            disk.direction.frozen_earth_heliocentric_icrf_au != frozen
            for disk in disks
        ):
            raise ValueError("all disks must retain the frozen Earth vector.")
        if (
            self.distance_origin != FROZEN_EARTH_DISTANCE_ORIGIN
            or self.distance_unit != FROZEN_EARTH_DISTANCE_UNIT
        ):
            raise ValueError(
                "frozen sequence distance must use frozen-earth/au."
            )
        object.__setattr__(self, "sample_instants", instants)
        object.__setattr__(self, "disks", disks)
        object.__setattr__(
            self,
            "provenance",
            tuple(
                _text(value, name="provenance entry")
                for value in self.provenance
            ),
        )


class FrozenEarthDiskSequenceRealizer:
    """Realize a geometric Venus sequence from one frozen Earth vector."""

    def __init__(
        self,
        *,
        source_factory=SkyfieldEphemerisStateSource.from_observer,
        coordinate_service=None,
    ):
        self.source_factory = source_factory
        self.coordinate_service = coordinate_service or CoordinateService()

    def sequence(self, request, *, observer):
        if not isinstance(request, FrozenEarthDiskSequenceRequest):
            raise TypeError(
                "request must be a FrozenEarthDiskSequenceRequest."
            )
        source = self.source_factory(observer)
        start = Time(request.start_instant, scale=request.start_time_scale)
        earth_request = EphemerisStateRequest(
            target="earth", centre="sun", frame="icrf",
            instant=_isot(start), time_scale=start.scale,
        )
        earth_state = source.state(earth_request)
        self._validate_state(earth_state, earth_request, source.resource)
        earth = _vector(earth_state.position, name="frozen Earth position")
        sun_vector = -earth
        disks = []
        instants = []
        fixed_sun = None
        for sample in range(request.sample_count):
            instant = start + TimeDelta(
                sample * request.step_days,
                format="jd",
            )
            isot = _isot(instant)
            planet_request = EphemerisStateRequest(
                target=request.descriptor.target, centre="sun", frame="icrf",
                instant=isot, time_scale=instant.scale,
            )
            planet_state = source.state(planet_request)
            self._validate_state(
                planet_state,
                planet_request,
                source.resource,
            )
            planet = _vector(planet_state.position, name="planet position")
            direction_vector = planet - earth
            direction = self._direction(
                request, source, direction_vector, earth, isot, instant.scale
            )
            sun = self._spherical(
                request, source, sun_vector, "sun", isot, instant.scale
            )
            if fixed_sun is None:
                fixed_sun = sun
            phase = _angle(direction_vector, planet)
            fraction = 0.5 * (1.0 + cos(radians(phase)))
            radius_au = request.physical_radius_km / AU_KM
            if radius_au >= direction.distance_au:
                raise ValueError(
                    "physical radius must be smaller than distance."
                )
            diameter = (
                2.0
                * asin(radius_au / direction.distance_au)
                * 180.0
                / pi
                * 3600.0
            )
            disks.append(FrozenEarthGeometricDisk(
                direction=direction,
                sun_direction=sun,
                display_name=request.display_name,
                physical_radius_km=request.physical_radius_km,
                radius_model=request.radius_model,
                angular_diameter_arcsec=diameter,
                phase_angle_deg=phase,
                illuminated_fraction=fraction,
                bright_limb_position_angle_deg=_position_angle(
                    direction.geometry,
                    sun,
                ),
            ))
            instants.append(isot)
        return FrozenEarthDiskSequence(
            request=request,
            frozen_earth_state=earth_state,
            sun_direction=fixed_sun,
            sample_instants=tuple(instants),
            disks=tuple(disks),
            provenance=(
                "Earth heliocentric ICRF position frozen at sequence start",
                "planet heliocentric geometric state evaluated at every epoch",
                "directions are frozen-observer geometric, not apparent sky",
                f"ephemeris model: {source.resource.model}",
                f"ephemeris sha256: {source.resource.sha256}",
            ),
        )

    def _direction(self, request, source, vector, earth, instant, scale):
        geometry = self._spherical(
            request, source, vector, request.descriptor.target, instant, scale
        )
        return FrozenEarthGeometricDirection(
            target=request.descriptor.target,
            instant=instant,
            time_scale=scale,
            geometry=geometry,
            vector_icrf_au=tuple(vector),
            distance_au=_length(vector, name="frozen-Earth target vector"),
            frozen_earth_heliocentric_icrf_au=tuple(earth),
        )

    def _spherical(self, request, source, vector, target, instant, scale):
        lon, lat = _lon_lat(vector)
        source_spec = CoordinateSpec(
            frame="icrs", origin=FROZEN_EARTH_DISTANCE_ORIGIN,
            position_status=PositionStatus.GEOMETRIC,
            instant=instant, time_scale=scale,
            provider=source.resource.provider, model=source.resource.model,
        )
        target_spec = CoordinateSpec(
            frame="barycentric-mean-ecliptic",
            origin=FROZEN_EARTH_DISTANCE_ORIGIN,
            position_status=PositionStatus.GEOMETRIC,
            equinox=request.ecliptic_equinox,
            instant=instant, time_scale=scale,
            provider=source.resource.provider, model=source.resource.model,
            provenance=("fixed ecliptic axes", "frozen Earth origin"),
        )
        return self.coordinate_service.transform(
            SphericalPoints(
                np.asarray((lon,)), np.asarray((lat,)),
                coordinate_spec=source_spec,
                ids=np.asarray((target,), dtype=object),
            ),
            target_spec,
        )

    @staticmethod
    def _validate_state(state, request, resource):
        if not isinstance(state, EphemerisState) or state.request != request:
            raise ValueError("source returned a mismatched ephemeris state.")
        if state.resource != resource:
            raise ValueError(
                "source returned a mismatched ephemeris resource."
            )
        if state.position_unit != "au":
            raise ValueError(
                "frozen-Earth construction requires AU positions."
            )
