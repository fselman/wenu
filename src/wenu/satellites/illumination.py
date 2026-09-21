"""Direct-Sun occultation and observer-night geometry for satellites."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from math import asin, atan, cos, degrees, isfinite, radians, sin
from typing import Final

import numpy as np

from wenu.ephemeris import (
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
)
from wenu.satellites.topocentric import (
    SatelliteEarthOrientationError,
    SatelliteTopocentricState,
    geocentric_gcrs_axis_position_to_itrs,
)


AU_KM: Final = 149_597_870.7
IAU_NOMINAL_SOLAR_RADIUS_KM: Final = 695_700.0
WGS84_EQUATORIAL_RADIUS_KM: Final = 6_378.137
WGS84_POLAR_RADIUS_KM: Final = 6_356.752314245


def _finite(value, *, name):
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite number.")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"{name} must be a finite number.") from error
    if not isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _positive_integer(value, *, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


def _vector3(value, *, name):
    try:
        vector = np.asarray(tuple(value), dtype=float)
    except (TypeError, ValueError) as error:
        raise TypeError(
            f"{name} must contain three finite numbers."
        ) from error
    if vector.shape != (3,):
        raise ValueError(f"{name} must contain exactly three values.")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values.")
    return vector


class SolarOccultationClass(str, Enum):
    """Finite-Sun state under the declared Earth-occultation model."""

    SUNLIT = "sunlit"
    PENUMBRA = "penumbra"
    UMBRA = "umbra"
    ANTUMBRA = "antumbra"


class ObserverTwilightClass(str, Enum):
    """Geometric vacuum twilight class from the Sun-centre altitude."""

    DAY = "day"
    CIVIL_TWILIGHT = "civil_twilight"
    NAUTICAL_TWILIGHT = "nautical_twilight"
    ASTRONOMICAL_TWILIGHT = "astronomical_twilight"
    ASTRONOMICAL_NIGHT = "astronomical_night"


class LunarOccultorStatus(str, Enum):
    """Status of the reserved lunar solar-occultor contribution."""

    NOT_EVALUATED = "not_evaluated"


class SatelliteIlluminationFailureCode(str, Enum):
    """Stable failure vocabulary reserved by the accepted 50S.7 audit."""

    PROPAGATION_FAILURE = "propagation_failure"
    EARTH_ORIENTATION_UNAVAILABLE = "earth_orientation_unavailable"
    EPHEMERIS_COVERAGE_UNAVAILABLE = "ephemeris_coverage_unavailable"
    FRAME_MISMATCH = "frame_mismatch"
    NON_FINITE_GEOMETRY = "non_finite_geometry"
    UNSUPPORTED_SHADOW_MODEL = "unsupported_shadow_model"
    UNSUPPORTED_SOURCE_MODEL = "unsupported_source_model"
    SOURCE_NOT_EVALUATED = "source_not_evaluated"
    QUADRATURE_NOT_CONVERGED = "quadrature_not_converged"
    TRANSITION_SEARCH_EXHAUSTED = "transition_search_exhausted"


class SatelliteIlluminationGeometryError(ValueError):
    """Typed terminal failure owned by satellite illumination geometry."""

    def __init__(self, code, message):
        if not isinstance(code, SatelliteIlluminationFailureCode):
            raise TypeError(
                "code must be a SatelliteIlluminationFailureCode."
            )
        super().__init__(str(message))
        self.code = code


@dataclass(frozen=True)
class SolarOccultationPolicy:
    """Immutable finite-source and Earth-shape numerical policy."""

    model: str = "uniform-solar-disk-wgs84-vacuum-ray-quadrature-v1"
    earth_shape_model: str = "WGS-84 ellipsoid"
    solar_radius_model: str = "IAU 2015 nominal solar radius"
    earth_equatorial_radius_km: float = WGS84_EQUATORIAL_RADIUS_KM
    earth_polar_radius_km: float = WGS84_POLAR_RADIUS_KM
    solar_radius_km: float = IAU_NOMINAL_SOLAR_RADIUS_KM
    radial_samples: int = 48
    azimuth_samples: int = 192
    refinement_factor: int = 2
    maximum_refinements: int = 3
    fraction_convergence_tolerance: float = 7.5e-4
    contact_relative_tolerance: float = 1.0e-12
    provenance: tuple[str, ...] = (
        "Uniform-radiance finite solar disk.",
        "Vacuum WGS-84 oblate Earth; no atmosphere, terrain, or refraction.",
        "Equal-solid-angle midpoint ray quadrature over the solar disk.",
    )

    def __post_init__(self):
        for name in ("model", "earth_shape_model", "solar_radius_model"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        for name in (
            "earth_equatorial_radius_km",
            "earth_polar_radius_km",
            "solar_radius_km",
            "fraction_convergence_tolerance",
            "contact_relative_tolerance",
        ):
            object.__setattr__(
                self,
                name,
                _finite(getattr(self, name), name=name),
            )
        if self.earth_equatorial_radius_km <= 0.0:
            raise ValueError("earth_equatorial_radius_km must be positive.")
        if not 0.0 < self.earth_polar_radius_km <= (
            self.earth_equatorial_radius_km
        ):
            raise ValueError(
                "earth_polar_radius_km must be positive and no larger "
                "than earth_equatorial_radius_km."
            )
        if self.solar_radius_km <= 0.0:
            raise ValueError("solar_radius_km must be positive.")
        if not 0.0 < self.fraction_convergence_tolerance < 1.0:
            raise ValueError(
                "fraction_convergence_tolerance must lie strictly "
                "between 0 and 1."
            )
        if not 0.0 < self.contact_relative_tolerance < 1.0:
            raise ValueError(
                "contact_relative_tolerance must lie strictly between 0 and 1."
            )
        object.__setattr__(
            self,
            "radial_samples",
            _positive_integer(self.radial_samples, name="radial_samples"),
        )
        object.__setattr__(
            self,
            "azimuth_samples",
            _positive_integer(
                self.azimuth_samples,
                name="azimuth_samples",
            ),
        )
        object.__setattr__(
            self,
            "refinement_factor",
            _positive_integer(
                self.refinement_factor,
                name="refinement_factor",
            ),
        )
        if self.refinement_factor < 2:
            raise ValueError("refinement_factor must be at least 2.")
        object.__setattr__(
            self,
            "maximum_refinements",
            _positive_integer(
                self.maximum_refinements,
                name="maximum_refinements",
            ),
        )
        if self.radial_samples < 8 or self.azimuth_samples < 32:
            raise ValueError(
                "solar-disk quadrature requires at least 8 radial and "
                "32 azimuth samples."
            )
        object.__setattr__(
            self,
            "provenance",
            tuple(str(item) for item in self.provenance),
        )


@dataclass(frozen=True)
class SolarOccultationGeometry:
    """One finite-Sun/WGS-84 occultation evaluation in ITRS."""

    visible_disk_fraction: float
    coarse_visible_disk_fraction: float
    quadrature_absolute_difference: float
    occultation_class: SolarOccultationClass
    satellite_to_sun_distance_km: float
    solar_angular_radius_deg: float
    evaluated_ray_count: int
    blocked_ray_count: int

    def __post_init__(self):
        fraction = _finite(
            self.visible_disk_fraction,
            name="visible_disk_fraction",
        )
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("visible_disk_fraction must lie in [0, 1].")
        object.__setattr__(self, "visible_disk_fraction", fraction)
        coarse = _finite(
            self.coarse_visible_disk_fraction,
            name="coarse_visible_disk_fraction",
        )
        if not 0.0 <= coarse <= 1.0:
            raise ValueError(
                "coarse_visible_disk_fraction must lie in [0, 1]."
            )
        object.__setattr__(
            self,
            "coarse_visible_disk_fraction",
            coarse,
        )
        difference = _finite(
            self.quadrature_absolute_difference,
            name="quadrature_absolute_difference",
        )
        if difference < 0.0:
            raise ValueError(
                "quadrature_absolute_difference must be non-negative."
            )
        object.__setattr__(
            self,
            "quadrature_absolute_difference",
            difference,
        )
        if not isinstance(self.occultation_class, SolarOccultationClass):
            raise TypeError(
                "occultation_class must be a SolarOccultationClass."
            )
        distance = _finite(
            self.satellite_to_sun_distance_km,
            name="satellite_to_sun_distance_km",
        )
        if distance <= 0.0:
            raise ValueError("satellite_to_sun_distance_km must be positive.")
        object.__setattr__(self, "satellite_to_sun_distance_km", distance)
        radius = _finite(
            self.solar_angular_radius_deg,
            name="solar_angular_radius_deg",
        )
        if not 0.0 < radius < 90.0:
            raise ValueError("solar_angular_radius_deg must lie in (0, 90).")
        object.__setattr__(self, "solar_angular_radius_deg", radius)
        total = _positive_integer(
            self.evaluated_ray_count,
            name="evaluated_ray_count",
        )
        if (
            isinstance(self.blocked_ray_count, bool)
            or not isinstance(self.blocked_ray_count, int)
        ):
            raise TypeError("blocked_ray_count must be an integer.")
        if not 0 <= self.blocked_ray_count <= total:
            raise ValueError(
                "blocked_ray_count must lie between zero and "
                "evaluated_ray_count."
            )


@dataclass(frozen=True)
class SatelliteIlluminationGeometry:
    """Immutable output-neutral direct-Sun and observer-night geometry."""

    topocentric_state: SatelliteTopocentricState
    sun_ephemeris_state: EphemerisState
    evaluation_utc: str
    common_frame: str
    earth_to_sun_itrs_km: tuple[float, float, float]
    satellite_to_sun_itrs_km: tuple[float, float, float]
    solar_occultation: SolarOccultationGeometry
    observer_sun_altitude_deg: float
    observer_twilight_class: ObserverTwilightClass
    lunar_occultor_status: LunarOccultorStatus
    policy: SolarOccultationPolicy
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.topocentric_state, SatelliteTopocentricState):
            raise TypeError(
                "topocentric_state must be a SatelliteTopocentricState."
            )
        if not isinstance(self.sun_ephemeris_state, EphemerisState):
            raise TypeError("sun_ephemeris_state must be an EphemerisState.")
        if (
            not isinstance(self.evaluation_utc, str)
            or not self.evaluation_utc.strip()
        ):
            raise ValueError("evaluation_utc must be non-empty.")
        if self.common_frame != "itrs":
            raise ValueError("common_frame must be 'itrs'.")
        for name in (
            "earth_to_sun_itrs_km",
            "satellite_to_sun_itrs_km",
        ):
            object.__setattr__(
                self,
                name,
                tuple(_vector3(getattr(self, name), name=name)),
            )
        if not isinstance(self.solar_occultation, SolarOccultationGeometry):
            raise TypeError(
                "solar_occultation must be a SolarOccultationGeometry."
            )
        altitude = _finite(
            self.observer_sun_altitude_deg,
            name="observer_sun_altitude_deg",
        )
        if not -90.0 <= altitude <= 90.0:
            raise ValueError(
                "observer_sun_altitude_deg must lie in [-90, 90]."
            )
        object.__setattr__(self, "observer_sun_altitude_deg", altitude)
        if not isinstance(
            self.observer_twilight_class,
            ObserverTwilightClass,
        ):
            raise TypeError(
                "observer_twilight_class must be an ObserverTwilightClass."
            )
        if not isinstance(self.lunar_occultor_status, LunarOccultorStatus):
            raise TypeError(
                "lunar_occultor_status must be a LunarOccultorStatus."
            )
        if not isinstance(self.policy, SolarOccultationPolicy):
            raise TypeError("policy must be a SolarOccultationPolicy.")
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))


def classify_observer_twilight(sun_altitude_deg):
    """Classify geometric vacuum Sun-centre altitude at accepted boundaries."""
    altitude = _finite(sun_altitude_deg, name="sun_altitude_deg")
    if not -90.0 <= altitude <= 90.0:
        raise ValueError("sun_altitude_deg must lie in [-90, 90].")
    if altitude >= 0.0:
        return ObserverTwilightClass.DAY
    if altitude >= -6.0:
        return ObserverTwilightClass.CIVIL_TWILIGHT
    if altitude >= -12.0:
        return ObserverTwilightClass.NAUTICAL_TWILIGHT
    if altitude >= -18.0:
        return ObserverTwilightClass.ASTRONOMICAL_TWILIGHT
    return ObserverTwilightClass.ASTRONOMICAL_NIGHT


def _tangent_basis(direction):
    axis = np.zeros(3)
    axis[int(np.argmin(np.abs(direction)))] = 1.0
    east = np.cross(direction, axis)
    east /= np.linalg.norm(east)
    north = np.cross(east, direction)
    return east, north


def _solar_disk_rays(center, angular_radius, policy):
    east, north = _tangent_basis(center)
    radial_index = np.arange(policy.radial_samples, dtype=float)
    azimuth_index = np.arange(policy.azimuth_samples, dtype=float)
    one_minus_cos_radius = 1.0 - cos(angular_radius)
    cos_theta = (
        1.0
        - ((radial_index + 0.5) / policy.radial_samples)
        * one_minus_cos_radius
    )
    sin_theta = np.sqrt(np.maximum(0.0, 1.0 - cos_theta * cos_theta))
    phi = (
        2.0 * np.pi * (azimuth_index + 0.5)
        / policy.azimuth_samples
    )
    rim = (
        np.cos(phi)[:, None] * east[None, :]
        + np.sin(phi)[:, None] * north[None, :]
    )
    rays = (
        cos_theta[:, None, None] * center[None, None, :]
        + sin_theta[:, None, None] * rim[None, :, :]
    )
    return rays.reshape((-1, 3)), east, north


def _rays_intersect_ellipsoid(satellite, rays, policy):
    axes = np.asarray(
        (
            policy.earth_equatorial_radius_km,
            policy.earth_equatorial_radius_km,
            policy.earth_polar_radius_km,
        ),
        dtype=float,
    )
    scaled_satellite = satellite / axes
    scaled_rays = rays / axes[None, :]
    a = np.einsum("ij,ij->i", scaled_rays, scaled_rays)
    b = scaled_rays @ scaled_satellite
    c = float(scaled_satellite @ scaled_satellite - 1.0)
    discriminant = b * b - a * c
    scale = np.maximum(b * b + np.abs(a * c), np.finfo(float).tiny)
    contact = discriminant >= (
        -policy.contact_relative_tolerance * scale
    )
    root = np.sqrt(np.maximum(discriminant, 0.0))
    near_distance = (-b - root) / a
    return contact & (near_distance >= 0.0)


def _earth_silhouette_inside_solar_disk(
    satellite,
    center,
    east,
    north,
    angular_radius,
    policy,
):
    """Return whether the complete forward WGS-84 limb is inside the Sun."""
    inv_axes_squared = np.diag(
        (
            1.0 / policy.earth_equatorial_radius_km**2,
            1.0 / policy.earth_equatorial_radius_km**2,
            1.0 / policy.earth_polar_radius_km**2,
        )
    )
    basis = np.column_stack((east, north))
    ps = inv_axes_squared @ satellite
    k = float(satellite @ ps - 1.0)
    m0 = float(satellite @ inv_axes_squared @ center)
    m = basis.T @ ps
    n0 = float(center @ inv_axes_squared @ center)
    n = basis.T @ inv_axes_squared @ center
    matrix_n = basis.T @ inv_axes_squared @ basis
    hessian = np.outer(m, m) - k * matrix_n
    linear = 2.0 * (m0 * m - k * n)
    constant = m0 * m0 - k * n0
    ellipse_matrix = -hessian
    try:
        center_2d = -0.5 * np.linalg.solve(hessian, linear)
        peak = float(
            constant
            + linear @ center_2d
            + center_2d @ hessian @ center_2d
        )
        eigenvalues, eigenvectors = np.linalg.eigh(ellipse_matrix)
    except np.linalg.LinAlgError:
        return False
    if peak <= 0.0 or np.any(eigenvalues <= 0.0):
        return False
    angles = 2.0 * np.pi * np.arange(4096, dtype=float) / 4096.0
    unit_circle = np.vstack((np.cos(angles), np.sin(angles)))
    transform = (
        eigenvectors
        @ np.diag(np.sqrt(peak / eigenvalues))
    )
    limb = center_2d[:, None] + transform @ unit_circle
    radius = np.linalg.norm(limb, axis=0)
    tolerance = policy.contact_relative_tolerance
    if float(np.max(np.arctan(radius))) > angular_radius + tolerance:
        return False
    limb_vectors = center[:, None] + basis @ limb
    forward = satellite @ inv_axes_squared @ limb_vectors
    return bool(np.all(forward <= tolerance))


def evaluate_solar_occultation(
    satellite_itrs_position_km,
    earth_to_sun_itrs_km,
    *,
    policy=None,
):
    """Evaluate the finite uniform solar disk occulted by the WGS-84 Earth."""
    resolved_policy = SolarOccultationPolicy() if policy is None else policy
    if not isinstance(resolved_policy, SolarOccultationPolicy):
        raise TypeError("policy must be a SolarOccultationPolicy.")
    satellite = _vector3(
        satellite_itrs_position_km,
        name="satellite_itrs_position_km",
    )
    earth_to_sun = _vector3(
        earth_to_sun_itrs_km,
        name="earth_to_sun_itrs_km",
    )
    axes = np.asarray(
        (
            resolved_policy.earth_equatorial_radius_km,
            resolved_policy.earth_equatorial_radius_km,
            resolved_policy.earth_polar_radius_km,
        )
    )
    if float(np.sum((satellite / axes) ** 2)) <= 1.0:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY,
            "satellite position must lie outside the WGS-84 ellipsoid.",
        )
    satellite_to_sun = earth_to_sun - satellite
    distance = float(np.linalg.norm(satellite_to_sun))
    if distance <= resolved_policy.solar_radius_km:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY,
            "satellite-to-Sun distance must exceed the modeled solar radius.",
        )
    center = satellite_to_sun / distance
    angular_radius = asin(resolved_policy.solar_radius_km / distance)
    coarse_rays, _, _ = _solar_disk_rays(
        center,
        angular_radius,
        resolved_policy,
    )
    coarse_blocked = _rays_intersect_ellipsoid(
        satellite,
        coarse_rays,
        resolved_policy,
    )
    coarse_fraction = float(
        np.clip(
            1.0
            - np.count_nonzero(coarse_blocked) / coarse_blocked.size,
            0.0,
            1.0,
        )
    )
    current_policy = resolved_policy
    for _ in range(resolved_policy.maximum_refinements):
        refined_policy = replace(
            current_policy,
            radial_samples=(
                current_policy.radial_samples
                * resolved_policy.refinement_factor
            ),
            azimuth_samples=(
                current_policy.azimuth_samples
                * resolved_policy.refinement_factor
            ),
        )
        rays, east, north = _solar_disk_rays(
            center,
            angular_radius,
            refined_policy,
        )
        blocked = _rays_intersect_ellipsoid(
            satellite,
            rays,
            refined_policy,
        )
        blocked_count = int(np.count_nonzero(blocked))
        ray_count = int(blocked.size)
        visible_fraction = float(
            np.clip(1.0 - blocked_count / ray_count, 0.0, 1.0)
        )
        difference = abs(visible_fraction - coarse_fraction)
        if difference <= (
            resolved_policy.fraction_convergence_tolerance
        ):
            break
        coarse_fraction = visible_fraction
        current_policy = refined_policy
    else:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.QUADRATURE_NOT_CONVERGED,
            "solar-disk quadrature did not meet the declared absolute "
            "fraction tolerance within the bounded refinement budget.",
        )
    if blocked_count == 0:
        occultation_class = SolarOccultationClass.SUNLIT
    elif blocked_count == ray_count:
        occultation_class = SolarOccultationClass.UMBRA
    elif _earth_silhouette_inside_solar_disk(
        satellite,
        center,
        east,
        north,
        angular_radius,
        refined_policy,
    ):
        occultation_class = SolarOccultationClass.ANTUMBRA
    else:
        occultation_class = SolarOccultationClass.PENUMBRA
    return SolarOccultationGeometry(
        visible_disk_fraction=visible_fraction,
        coarse_visible_disk_fraction=coarse_fraction,
        quadrature_absolute_difference=difference,
        occultation_class=occultation_class,
        satellite_to_sun_distance_km=distance,
        solar_angular_radius_deg=degrees(angular_radius),
        evaluated_ray_count=ray_count,
        blocked_ray_count=blocked_count,
    )


def _observer_sun_altitude(topocentric_state, earth_to_sun_itrs):
    observer_to_sun = (
        earth_to_sun_itrs
        - np.asarray(
            topocentric_state.observer_itrs_position_km,
            dtype=float,
        )
    )
    observer_to_sun /= np.linalg.norm(observer_to_sun)
    observer = topocentric_state.observer
    longitude = radians(observer.longitude_deg)
    latitude = radians(observer.latitude_deg)
    geodetic_up = np.asarray(
        (
            cos(latitude) * cos(longitude),
            cos(latitude) * sin(longitude),
            sin(latitude),
        )
    )
    return degrees(
        asin(
            float(
                np.clip(
                    observer_to_sun @ geodetic_up,
                    -1.0,
                    1.0,
                )
            )
        )
    )


class SatelliteIlluminationGeometryEvaluator:
    """Compose accepted satellite, ephemeris, and Earth-orientation owners."""

    def __init__(self, source, *, policy=None):
        if not isinstance(source, EphemerisStateSource):
            raise TypeError("source must implement EphemerisStateSource.")
        resolved_policy = (
            SolarOccultationPolicy() if policy is None else policy
        )
        if not isinstance(resolved_policy, SolarOccultationPolicy):
            raise TypeError("policy must be a SolarOccultationPolicy.")
        self.source = source
        self.policy = resolved_policy

    def evaluate(self, topocentric_state):
        """Return one same-instant direct-Sun and observer-night state."""
        if not isinstance(topocentric_state, SatelliteTopocentricState):
            raise TypeError(
                "topocentric_state must be a SatelliteTopocentricState."
            )
        instant = topocentric_state.teme_state.evaluation_utc
        request = EphemerisStateRequest(
            target="sun",
            centre="earth",
            frame="icrf",
            instant=instant,
            time_scale="utc",
        )
        sun_state = self.source.state(request)
        if not isinstance(sun_state, EphemerisState):
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.SOURCE_NOT_EVALUATED,
                "ephemeris source did not return an EphemerisState.",
            )
        if sun_state.request != request:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.FRAME_MISMATCH,
                "Sun ephemeris result does not match the exact request.",
            )
        if (
            sun_state.position_unit.lower() != "au"
            or sun_state.request.frame != "icrf"
        ):
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.FRAME_MISMATCH,
                "Sun ephemeris state must use Earth-centred ICRF axes and AU.",
            )
        earth_to_sun_gcrs_axis_km = (
            np.asarray(sun_state.position, dtype=float) * AU_KM
        )
        try:
            earth_to_sun_itrs = np.asarray(
                geocentric_gcrs_axis_position_to_itrs(
                    earth_to_sun_gcrs_axis_km,
                    instant,
                    expected_earth_orientation=(
                        topocentric_state.earth_orientation
                    ),
                ),
                dtype=float,
            )
        except SatelliteEarthOrientationError as error:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.EARTH_ORIENTATION_UNAVAILABLE,
                str(error),
            ) from error
        solar_occultation = evaluate_solar_occultation(
            topocentric_state.satellite_itrs_position_km,
            earth_to_sun_itrs,
            policy=self.policy,
        )
        satellite_to_sun = (
            earth_to_sun_itrs
            - np.asarray(
                topocentric_state.satellite_itrs_position_km,
                dtype=float,
            )
        )
        altitude = _observer_sun_altitude(
            topocentric_state,
            earth_to_sun_itrs,
        )
        return SatelliteIlluminationGeometry(
            topocentric_state=topocentric_state,
            sun_ephemeris_state=sun_state,
            evaluation_utc=instant,
            common_frame="itrs",
            earth_to_sun_itrs_km=tuple(earth_to_sun_itrs),
            satellite_to_sun_itrs_km=tuple(satellite_to_sun),
            solar_occultation=solar_occultation,
            observer_sun_altitude_deg=altitude,
            observer_twilight_class=classify_observer_twilight(altitude),
            lunar_occultor_status=LunarOccultorStatus.NOT_EVALUATED,
            policy=self.policy,
            provenance=(
                "Same physical instant retained as canonical UTC.",
                "DE geometric Earth-to-Sun state evaluated in ICRF axes.",
                "ICRF/GCRS-compatible axes rotated into ITRS with accepted "
                "installed-IERS-A evidence.",
                *self.policy.provenance,
            ),
            warnings=(
                "Geometric vacuum result; not a brightness or visibility "
                "claim.",
                "Lunar solar occultation is explicitly not evaluated.",
            ),
        )
