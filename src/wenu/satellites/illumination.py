"""Direct-Sun occultation and observer-night geometry for satellites."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from math import acos, asin, atan, cos, degrees, isfinite, pi, radians, sin, sqrt
from typing import Final

import numpy as np

from wenu.ephemeris import (
    EphemerisResourceChain,
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
)
from wenu.satellite_crossings import InclusiveTimeInterval
from wenu.satellites.elements import SatelliteElementRecord
from wenu.satellites.sgp4 import (
    SatellitePropagationError,
    Sgp4TemePropagator,
)
from wenu.satellites.snapshots import SatelliteElementSnapshot
from wenu.satellites.topocentric import (
    SatelliteEarthOrientationError,
    SatelliteEarthOrientationEvidence,
    SatelliteGeocentricItrsState,
    SatelliteGeocentricItrsTransformer,
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
    INVALID_TRANSITION_QUERY = "invalid_transition_query"
    UNSUPPORTED_TRANSITION_DOMAIN = "unsupported_transition_domain"
    DEGENERATE_SHADOW_TOPOLOGY = "degenerate_shadow_topology"
    CONTACT_BRACKET_INCONSISTENT = "contact_bracket_inconsistent"


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
        sun_state, earth_to_sun_itrs = _sun_state_and_itrs(
            self.source,
            instant,
            topocentric_state.earth_orientation,
        )
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

SHADOW_TRANSITION_IMPLEMENTATION: Final = (
    "wenu complete bounded continuous shadow contact search v1"
)


class ShadowTransitionKind(str, Enum):
    """Directed finite-source shadow-class boundary."""

    SUNLIT_TO_PENUMBRA = "sunlit_to_penumbra"
    PENUMBRA_TO_SUNLIT = "penumbra_to_sunlit"
    PENUMBRA_TO_UMBRA = "penumbra_to_umbra"
    UMBRA_TO_PENUMBRA = "umbra_to_penumbra"
    PENUMBRA_TO_ANTUMBRA = "penumbra_to_antumbra"
    ANTUMBRA_TO_PENUMBRA = "antumbra_to_penumbra"


_TRANSITION_KIND = {
    (
        SolarOccultationClass.SUNLIT,
        SolarOccultationClass.PENUMBRA,
    ): ShadowTransitionKind.SUNLIT_TO_PENUMBRA,
    (
        SolarOccultationClass.PENUMBRA,
        SolarOccultationClass.SUNLIT,
    ): ShadowTransitionKind.PENUMBRA_TO_SUNLIT,
    (
        SolarOccultationClass.PENUMBRA,
        SolarOccultationClass.UMBRA,
    ): ShadowTransitionKind.PENUMBRA_TO_UMBRA,
    (
        SolarOccultationClass.UMBRA,
        SolarOccultationClass.PENUMBRA,
    ): ShadowTransitionKind.UMBRA_TO_PENUMBRA,
    (
        SolarOccultationClass.PENUMBRA,
        SolarOccultationClass.ANTUMBRA,
    ): ShadowTransitionKind.PENUMBRA_TO_ANTUMBRA,
    (
        SolarOccultationClass.ANTUMBRA,
        SolarOccultationClass.PENUMBRA,
    ): ShadowTransitionKind.ANTUMBRA_TO_PENUMBRA,
}


def _positive_finite(value, *, name):
    result = _finite(value, name=name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _utc_datetime(value, *, name):
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{name} must be a non-empty UTC string.")
    candidate = value.strip()
    parsed_text = (
        candidate[:-1] + "+00:00"
        if candidate.endswith("Z")
        else candidate
    )
    try:
        parsed = datetime.fromisoformat(parsed_text)
    except ValueError as error:
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be an ISO-8601 UTC instant.")
    return parsed.astimezone(timezone.utc)


def _utc_instant(value):
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")


@dataclass(frozen=True)
class ShadowTransitionSearchPolicy:
    """Finite limits and completeness assumptions for one transition search."""

    model: str = "complete-bounded-continuous-contact-v1"
    time_tolerance_seconds: float = 0.05
    contact_tolerance_rad: float = 1.0e-10
    maximum_interval_seconds: float = 600.0
    maximum_subdivision_depth: int = 40
    maximum_evaluations: int = 20000
    maximum_events: int = 16
    minimum_altitude_km: float = 200.0
    maximum_speed_km_per_s: float = 12.0
    contact_rate_bound_rad_per_s: float = 0.125
    limb_extremum_samples: int = 128
    limb_extremum_iterations: int = 48

    def __post_init__(self):
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be non-empty.")
        for name in (
            "time_tolerance_seconds",
            "contact_tolerance_rad",
            "maximum_interval_seconds",
            "minimum_altitude_km",
            "maximum_speed_km_per_s",
            "contact_rate_bound_rad_per_s",
        ):
            object.__setattr__(
                self,
                name,
                _positive_finite(getattr(self, name), name=name),
            )
        for name in (
            "maximum_subdivision_depth",
            "maximum_evaluations",
            "maximum_events",
            "limb_extremum_samples",
            "limb_extremum_iterations",
        ):
            object.__setattr__(
                self,
                name,
                _positive_integer(getattr(self, name), name=name),
            )
        if self.maximum_subdivision_depth > 64:
            raise ValueError("maximum_subdivision_depth must not exceed 64.")
        if self.maximum_evaluations < 3:
            raise ValueError("maximum_evaluations must be at least 3.")
        if self.limb_extremum_samples < 32:
            raise ValueError("limb_extremum_samples must be at least 32.")
        if self.limb_extremum_iterations < 24:
            raise ValueError("limb_extremum_iterations must be at least 24.")
        required_rate = (
            2.0
            * self.maximum_speed_km_per_s
            / self.minimum_altitude_km
            + 1.0e-3
        )
        if self.contact_rate_bound_rad_per_s < required_rate:
            raise ValueError(
                "contact_rate_bound_rad_per_s is smaller than the declared "
                "conservative speed/altitude envelope."
            )


@dataclass(frozen=True)
class SatelliteShadowTransitionQuery:
    """One observer-independent bounded shadow-transition request."""

    snapshot: SatelliteElementSnapshot
    norad_catalog_id: int
    interval: InclusiveTimeInterval
    occultation_policy: SolarOccultationPolicy = field(
        default_factory=SolarOccultationPolicy
    )
    search_policy: ShadowTransitionSearchPolicy = field(
        default_factory=ShadowTransitionSearchPolicy
    )

    def __post_init__(self):
        if not isinstance(self.snapshot, SatelliteElementSnapshot):
            raise TypeError("snapshot must be a SatelliteElementSnapshot.")
        if (
            isinstance(self.norad_catalog_id, bool)
            or not isinstance(self.norad_catalog_id, int)
        ):
            raise TypeError("norad_catalog_id must be a positive integer.")
        if self.norad_catalog_id <= 0:
            raise ValueError("norad_catalog_id must be a positive integer.")
        if not isinstance(self.interval, InclusiveTimeInterval):
            raise TypeError("interval must be an InclusiveTimeInterval.")
        if not isinstance(self.occultation_policy, SolarOccultationPolicy):
            raise TypeError(
                "occultation_policy must be a SolarOccultationPolicy."
            )
        if not isinstance(
            self.search_policy,
            ShadowTransitionSearchPolicy,
        ):
            raise TypeError(
                "search_policy must be a ShadowTransitionSearchPolicy."
            )
        if self.norad_catalog_id not in self.snapshot.by_norad_catalog_id:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.INVALID_TRANSITION_QUERY,
                "snapshot does not contain the requested full NORAD "
                "catalogue identifier.",
            )
        start = _utc_datetime(self.interval.start, name="interval.start")
        stop = _utc_datetime(self.interval.stop, name="interval.stop")
        duration = (stop - start).total_seconds()
        if duration <= 0.0:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.INVALID_TRANSITION_QUERY,
                "shadow-transition interval must be non-empty.",
            )
        if duration > self.search_policy.maximum_interval_seconds:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.UNSUPPORTED_TRANSITION_DOMAIN,
                "shadow-transition interval exceeds the declared maximum.",
            )


@dataclass(frozen=True)
class SolarOccultationContactGeometry:
    """Continuous ellipsoid-limb contact evidence at one instant."""

    occultation_class: SolarOccultationClass
    nearest_limb_contact_margin_rad: float
    solar_contains_earth_margin_rad: float
    minimum_limb_separation_rad: float
    maximum_limb_separation_rad: float
    solar_angular_radius_rad: float
    central_ray_blocked: bool

    def __post_init__(self):
        if not isinstance(self.occultation_class, SolarOccultationClass):
            raise TypeError(
                "occultation_class must be a SolarOccultationClass."
            )
        for name in (
            "nearest_limb_contact_margin_rad",
            "solar_contains_earth_margin_rad",
            "minimum_limb_separation_rad",
            "maximum_limb_separation_rad",
            "solar_angular_radius_rad",
        ):
            object.__setattr__(
                self,
                name,
                _finite(getattr(self, name), name=name),
            )
        if not (
            0.0
            <= self.minimum_limb_separation_rad
            <= self.maximum_limb_separation_rad
            <= pi
        ):
            raise ValueError("limb separations must be ordered in [0, pi].")
        if not 0.0 < self.solar_angular_radius_rad < pi / 2.0:
            raise ValueError(
                "solar_angular_radius_rad must lie in (0, pi/2)."
            )
        if not isinstance(self.central_ray_blocked, bool):
            raise TypeError("central_ray_blocked must be Boolean.")


@dataclass(frozen=True)
class SatelliteShadowTransition:
    """One certified directed finite-source shadow boundary."""

    record: SatelliteElementRecord
    snapshot_id: str
    snapshot_sha256: str
    query_interval: InclusiveTimeInterval
    left_class: SolarOccultationClass
    right_class: SolarOccultationClass
    kind: ShadowTransitionKind
    event_utc: str
    bracket_start_utc: str
    bracket_stop_utc: str
    time_tolerance_seconds: float
    achieved_bracket_width_seconds: float
    evaluation_count: int
    occultation_policy: SolarOccultationPolicy
    search_policy: ShadowTransitionSearchPolicy
    left_earth_orientation: SatelliteEarthOrientationEvidence
    right_earth_orientation: SatelliteEarthOrientationEvidence
    sun_ephemeris_resource: EphemerisResourceIdentity | EphemerisResourceChain
    implementation: str = SHADOW_TRANSITION_IMPLEMENTATION
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.record, SatelliteElementRecord):
            raise TypeError("record must be a SatelliteElementRecord.")
        for name in ("snapshot_id", "snapshot_sha256", "implementation"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        if len(self.snapshot_sha256) != 64:
            raise ValueError("snapshot_sha256 must be a SHA-256 digest.")
        if not isinstance(self.query_interval, InclusiveTimeInterval):
            raise TypeError(
                "query_interval must be an InclusiveTimeInterval."
            )
        if not isinstance(self.left_class, SolarOccultationClass):
            raise TypeError("left_class must be SolarOccultationClass.")
        if not isinstance(self.right_class, SolarOccultationClass):
            raise TypeError("right_class must be SolarOccultationClass.")
        if not isinstance(self.kind, ShadowTransitionKind):
            raise TypeError("kind must be a ShadowTransitionKind.")
        if _TRANSITION_KIND.get(
            (self.left_class, self.right_class)
        ) is not self.kind:
            raise ValueError("transition classes do not match kind.")
        start = _utc_datetime(
            self.bracket_start_utc,
            name="bracket_start_utc",
        )
        stop = _utc_datetime(
            self.bracket_stop_utc,
            name="bracket_stop_utc",
        )
        event = _utc_datetime(self.event_utc, name="event_utc")
        if not start <= event <= stop:
            raise ValueError("event_utc must lie inside the bracket.")
        query_start = _utc_datetime(
            self.query_interval.start,
            name="query_interval.start",
        )
        query_stop = _utc_datetime(
            self.query_interval.stop,
            name="query_interval.stop",
        )
        if not query_start <= start <= stop <= query_stop:
            raise ValueError(
                "transition bracket must lie inside query_interval."
            )
        width = (stop - start).total_seconds()
        tolerance = _positive_finite(
            self.time_tolerance_seconds,
            name="time_tolerance_seconds",
        )
        achieved = _finite(
            self.achieved_bracket_width_seconds,
            name="achieved_bracket_width_seconds",
        )
        if achieved < 0.0 or abs(achieved - width) > 5.0e-7:
            raise ValueError(
                "achieved_bracket_width_seconds must match the bracket."
            )
        if width > tolerance + 5.0e-7:
            raise ValueError("transition bracket exceeds time tolerance.")
        object.__setattr__(self, "time_tolerance_seconds", tolerance)
        if (
            isinstance(self.evaluation_count, bool)
            or not isinstance(self.evaluation_count, int)
            or self.evaluation_count <= 0
        ):
            raise ValueError("evaluation_count must be a positive integer.")
        if not isinstance(self.occultation_policy, SolarOccultationPolicy):
            raise TypeError(
                "occultation_policy must be SolarOccultationPolicy."
            )
        if not isinstance(
            self.search_policy,
            ShadowTransitionSearchPolicy,
        ):
            raise TypeError(
                "search_policy must be ShadowTransitionSearchPolicy."
            )
        for name in (
            "left_earth_orientation",
            "right_earth_orientation",
        ):
            if not isinstance(
                getattr(self, name),
                SatelliteEarthOrientationEvidence,
            ):
                raise TypeError(
                    f"{name} must be SatelliteEarthOrientationEvidence."
                )
        if not isinstance(
            self.sun_ephemeris_resource,
            (EphemerisResourceIdentity, EphemerisResourceChain),
        ):
            raise TypeError(
                "sun_ephemeris_resource must be an immutable ephemeris "
                "resource identity."
            )
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    @property
    def identity(self):
        """Return the complete immutable transition identity tuple."""
        return (
            self.record,
            self.snapshot_id,
            self.snapshot_sha256,
            self.query_interval,
            self.left_class,
            self.right_class,
            self.kind,
            self.event_utc,
            self.bracket_start_utc,
            self.bracket_stop_utc,
            self.occultation_policy,
            self.search_policy,
            self.left_earth_orientation,
            self.right_earth_orientation,
            self.sun_ephemeris_resource,
            self.implementation,
            self.evaluation_count,
        )


def _unit_vector3(value, *, name):
    vector = _vector3(value, name=name)
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY,
            f"{name} must be non-zero.",
        )
    return vector / norm


def _golden_extreme(function, left, right, *, maximize, iterations):
    ratio = (sqrt(5.0) - 1.0) / 2.0
    one = right - ratio * (right - left)
    two = left + ratio * (right - left)
    value_one = function(one)
    value_two = function(two)
    for _ in range(iterations):
        if (value_one >= value_two) is maximize:
            right = two
            two = one
            value_two = value_one
            one = right - ratio * (right - left)
            value_one = function(one)
        else:
            left = one
            one = two
            value_one = value_two
            two = left + ratio * (right - left)
            value_two = function(two)
    values = (
        (value_one, one),
        (value_two, two),
        (function((left + right) / 2.0), (left + right) / 2.0),
    )
    selector = max if maximize else min
    return selector(values, key=lambda item: item[0])


def _ellipsoid_limb_separation_extrema(
    satellite,
    solar_direction,
    occultation_policy,
    search_policy,
):
    axes = np.asarray(
        (
            occultation_policy.earth_equatorial_radius_km,
            occultation_policy.earth_equatorial_radius_km,
            occultation_policy.earth_polar_radius_km,
        ),
        dtype=float,
    )
    scaled_satellite = satellite / axes
    squared_distance = float(scaled_satellite @ scaled_satellite)
    if squared_distance <= 1.0:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY,
            "satellite position must lie outside the WGS-84 ellipsoid.",
        )
    normal = scaled_satellite / sqrt(squared_distance)
    helper = np.zeros(3)
    helper[int(np.argmin(np.abs(normal)))] = 1.0
    first = np.cross(normal, helper)
    first /= np.linalg.norm(first)
    second = np.cross(normal, first)
    center = scaled_satellite / squared_distance
    radius = sqrt(1.0 - 1.0 / squared_distance)

    def limb_dot(theta):
        scaled_point = center + radius * (
            cos(theta) * first + sin(theta) * second
        )
        earth_point = axes * scaled_point
        direction = earth_point - satellite
        direction /= np.linalg.norm(direction)
        return float(
            np.clip(direction @ solar_direction, -1.0, 1.0)
        )

    count = search_policy.limb_extremum_samples
    step = 2.0 * pi / count
    angles = np.arange(count, dtype=float) * step
    values = np.asarray([limb_dot(angle) for angle in angles])
    maximum_values = [float(np.max(values))]
    minimum_values = [float(np.min(values))]
    for index, value in enumerate(values):
        previous = values[(index - 1) % count]
        following = values[(index + 1) % count]
        center_angle = angles[index]
        if value >= previous and value >= following:
            maximum_values.append(
                _golden_extreme(
                    limb_dot,
                    center_angle - step,
                    center_angle + step,
                    maximize=True,
                    iterations=search_policy.limb_extremum_iterations,
                )[0]
            )
        if value <= previous and value <= following:
            minimum_values.append(
                _golden_extreme(
                    limb_dot,
                    center_angle - step,
                    center_angle + step,
                    maximize=False,
                    iterations=search_policy.limb_extremum_iterations,
                )[0]
            )
    minimum_separation = acos(
        float(np.clip(max(maximum_values), -1.0, 1.0))
    )
    maximum_separation = acos(
        float(np.clip(min(minimum_values), -1.0, 1.0))
    )
    return minimum_separation, maximum_separation


def evaluate_solar_occultation_contact(
    satellite_itrs_position_km,
    earth_to_sun_itrs_km,
    *,
    occultation_policy=None,
    search_policy=None,
):
    """Return continuous finite-Sun/WGS-84 limb-contact evidence."""
    resolved_occultation = (
        SolarOccultationPolicy()
        if occultation_policy is None
        else occultation_policy
    )
    resolved_search = (
        ShadowTransitionSearchPolicy()
        if search_policy is None
        else search_policy
    )
    if not isinstance(resolved_occultation, SolarOccultationPolicy):
        raise TypeError(
            "occultation_policy must be a SolarOccultationPolicy."
        )
    if not isinstance(resolved_search, ShadowTransitionSearchPolicy):
        raise TypeError(
            "search_policy must be a ShadowTransitionSearchPolicy."
        )
    satellite = _vector3(
        satellite_itrs_position_km,
        name="satellite_itrs_position_km",
    )
    earth_to_sun = _vector3(
        earth_to_sun_itrs_km,
        name="earth_to_sun_itrs_km",
    )
    satellite_to_sun = earth_to_sun - satellite
    distance = float(np.linalg.norm(satellite_to_sun))
    if distance <= resolved_occultation.solar_radius_km:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.NON_FINITE_GEOMETRY,
            "satellite-to-Sun distance must exceed the modeled solar radius.",
        )
    solar_direction = satellite_to_sun / distance
    solar_radius = asin(resolved_occultation.solar_radius_km / distance)
    minimum, maximum = _ellipsoid_limb_separation_extrema(
        satellite,
        solar_direction,
        resolved_occultation,
        resolved_search,
    )
    central_blocked = bool(
        _rays_intersect_ellipsoid(
            satellite,
            solar_direction[None, :],
            resolved_occultation,
        )[0]
    )
    nearest_margin = minimum - solar_radius
    contains_margin = solar_radius - maximum
    tolerance = resolved_search.contact_tolerance_rad
    if contains_margin > tolerance:
        occultation_class = SolarOccultationClass.ANTUMBRA
    elif nearest_margin > tolerance:
        occultation_class = (
            SolarOccultationClass.UMBRA
            if central_blocked
            else SolarOccultationClass.SUNLIT
        )
    else:
        occultation_class = SolarOccultationClass.PENUMBRA
    return SolarOccultationContactGeometry(
        occultation_class=occultation_class,
        nearest_limb_contact_margin_rad=nearest_margin,
        solar_contains_earth_margin_rad=contains_margin,
        minimum_limb_separation_rad=minimum,
        maximum_limb_separation_rad=maximum,
        solar_angular_radius_rad=solar_radius,
        central_ray_blocked=central_blocked,
    )


@dataclass(frozen=True)
class _ShadowSample:
    instant: datetime
    contact: SolarOccultationContactGeometry
    geocentric_state: SatelliteGeocentricItrsState | None = field(
        default=None,
        compare=False,
    )
    sun_ephemeris_state: EphemerisState | None = field(
        default=None,
        compare=False,
    )

    def __post_init__(self):
        if (
            self.instant.tzinfo is None
            or self.instant.utcoffset() != timedelta(0)
        ):
            raise ValueError("shadow sample instant must be UTC-aware.")
        if not isinstance(
            self.contact,
            SolarOccultationContactGeometry,
        ):
            raise TypeError(
                "contact must be SolarOccultationContactGeometry."
            )


class _ShadowEvaluationCache:
    def __init__(self, evaluator, policy, norad_catalog_id):
        self._evaluator = evaluator
        self._policy = policy
        self._norad_catalog_id = norad_catalog_id
        self._values = {}

    def __call__(self, instant):
        instant = instant.astimezone(timezone.utc)
        if instant in self._values:
            return self._values[instant]
        if len(self._values) >= self._policy.maximum_evaluations:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.TRANSITION_SEARCH_EXHAUSTED,
                "shadow-transition evaluation budget was exhausted for "
                f"NORAD {self._norad_catalog_id}.",
            )
        result = self._evaluator(instant)
        if not isinstance(result, _ShadowSample):
            raise TypeError("shadow evaluator must return _ShadowSample.")
        self._values[instant] = result
        return result

    @property
    def evaluation_count(self):
        return len(self._values)


def _contact_clearance(sample):
    return min(
        abs(sample.contact.nearest_limb_contact_margin_rad),
        abs(sample.contact.solar_contains_earth_margin_rad),
    )


def _at_contact(sample, policy):
    return _contact_clearance(sample) <= policy.contact_tolerance_rad


def _certified_without_contact(left, middle, right, width, policy):
    classes = {
        left.contact.occultation_class,
        middle.contact.occultation_class,
        right.contact.occultation_class,
    }
    if len(classes) != 1:
        return False
    required = (
        policy.contact_rate_bound_rad_per_s * width / 4.0
        + policy.contact_tolerance_rad
    )
    return min(
        _contact_clearance(left),
        _contact_clearance(middle),
        _contact_clearance(right),
    ) > required


def _transition_kind(left, right):
    kind = _TRANSITION_KIND.get(
        (
            left.contact.occultation_class,
            right.contact.occultation_class,
        )
    )
    if kind is None:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.DEGENERATE_SHADOW_TOPOLOGY,
            "shadow search encountered a non-adjacent or unsupported "
            "class transition.",
        )
    return kind


def _collect_transition_brackets(
    cache,
    start,
    stop,
    policy,
    *,
    depth=0,
):
    left = cache(start)
    right = cache(stop)
    middle_time = start + (stop - start) / 2
    middle = cache(middle_time)
    width = (stop - start).total_seconds()
    if _certified_without_contact(
        left,
        middle,
        right,
        width,
        policy,
    ):
        return ()
    if depth >= policy.maximum_subdivision_depth:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.TRANSITION_SEARCH_EXHAUSTED,
            "shadow-transition subdivision depth was exhausted.",
        )
    if width <= policy.time_tolerance_seconds:
        if left.contact.occultation_class != right.contact.occultation_class:
            if _at_contact(left, policy) or _at_contact(right, policy):
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.CONTACT_BRACKET_INCONSISTENT,
                    "transition bracket side lies inside contact tolerance.",
                )
            return ((left, right, _transition_kind(left, right)),)
        if (
            left.contact.occultation_class
            != middle.contact.occultation_class
        ):
            if any(
                _at_contact(item, policy)
                for item in (left, middle, right)
            ):
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.DEGENERATE_SHADOW_TOPOLOGY,
                    "unresolved tangent or simultaneous contact.",
                )
            return (
                (left, middle, _transition_kind(left, middle)),
                (middle, right, _transition_kind(middle, right)),
            )
        # Event time tolerance bounds returned brackets.  A nearby
        # same-class interval may still require finer subdivision before the
        # conservative clearance envelope can certify it contact-free.
    return _collect_transition_brackets(
        cache,
        start,
        middle_time,
        policy,
        depth=depth + 1,
    ) + _collect_transition_brackets(
        cache,
        middle_time,
        stop,
        policy,
        depth=depth + 1,
    )


def _radial_altitude_km(position, policy):
    position = np.asarray(position, dtype=float)
    radius = float(np.linalg.norm(position))
    direction = position / radius
    axes = np.asarray(
        (
            policy.earth_equatorial_radius_km,
            policy.earth_equatorial_radius_km,
            policy.earth_polar_radius_km,
        )
    )
    surface_radius = 1.0 / sqrt(
        float(np.sum((direction / axes) ** 2))
    )
    return radius - surface_radius


def _sun_state_and_itrs(source, instant, earth_orientation):
    request = EphemerisStateRequest(
        target="sun",
        centre="earth",
        frame="icrf",
        instant=instant,
        time_scale="utc",
    )
    try:
        sun_state = source.state(request)
    except Exception as error:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.EPHEMERIS_COVERAGE_UNAVAILABLE,
            f"Sun ephemeris evaluation failed: {error}",
        ) from error
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
                expected_earth_orientation=earth_orientation,
            ),
            dtype=float,
        )
    except SatelliteEarthOrientationError as error:
        raise SatelliteIlluminationGeometryError(
            SatelliteIlluminationFailureCode.EARTH_ORIENTATION_UNAVAILABLE,
            str(error),
        ) from error
    return sun_state, earth_to_sun_itrs


class SatelliteShadowTransitionFinder:
    """Find every admitted direct-solar shadow boundary or fail closed."""

    def __init__(self, source):
        if not isinstance(source, EphemerisStateSource):
            raise TypeError("source must implement EphemerisStateSource.")
        self.source = source

    def find(self, query):
        if not isinstance(query, SatelliteShadowTransitionQuery):
            raise TypeError(
                "query must be a SatelliteShadowTransitionQuery."
            )
        record = query.snapshot.by_norad_catalog_id[
            query.norad_catalog_id
        ]
        propagator = Sgp4TemePropagator(
            record,
            snapshot_sha256=query.snapshot.manifest.content_sha256,
        )
        transformer = SatelliteGeocentricItrsTransformer()

        def evaluate(instant):
            instant_utc = _utc_instant(instant)
            try:
                teme = propagator.propagate(instant_utc)
            except SatellitePropagationError as error:
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.PROPAGATION_FAILURE,
                    str(error),
                ) from error
            try:
                geocentric = transformer.transform(teme)
            except SatelliteEarthOrientationError as error:
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.EARTH_ORIENTATION_UNAVAILABLE,
                    str(error),
                ) from error
            altitude = _radial_altitude_km(
                geocentric.satellite_itrs_position_km,
                query.occultation_policy,
            )
            speed = float(
                np.linalg.norm(
                    geocentric.satellite_itrs_velocity_km_per_s
                )
            )
            if (
                altitude < query.search_policy.minimum_altitude_km
                or speed > query.search_policy.maximum_speed_km_per_s
            ):
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.UNSUPPORTED_TRANSITION_DOMAIN,
                    "state lies outside the declared altitude/speed "
                    "transition-search envelope.",
                )
            sun_state, earth_to_sun = _sun_state_and_itrs(
                self.source,
                instant_utc,
                geocentric.earth_orientation,
            )
            contact = evaluate_solar_occultation_contact(
                geocentric.satellite_itrs_position_km,
                earth_to_sun,
                occultation_policy=query.occultation_policy,
                search_policy=query.search_policy,
            )
            return _ShadowSample(
                instant=instant,
                contact=contact,
                geocentric_state=geocentric,
                sun_ephemeris_state=sun_state,
            )

        start = _utc_datetime(
            query.interval.start,
            name="interval.start",
        )
        stop = _utc_datetime(query.interval.stop, name="interval.stop")
        cache = _ShadowEvaluationCache(
            evaluate,
            query.search_policy,
            query.norad_catalog_id,
        )
        start_sample = cache(start)
        stop_sample = cache(stop)
        if _at_contact(start_sample, query.search_policy) or _at_contact(
            stop_sample,
            query.search_policy,
        ):
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.CONTACT_BRACKET_INCONSISTENT,
                "query endpoint lies within contact tolerance.",
            )
        brackets = _collect_transition_brackets(
            cache,
            start,
            stop,
            query.search_policy,
        )
        if len(brackets) > query.search_policy.maximum_events:
            raise SatelliteIlluminationGeometryError(
                SatelliteIlluminationFailureCode.TRANSITION_SEARCH_EXHAUSTED,
                "shadow-transition event limit was exceeded.",
            )
        ordered = tuple(
            sorted(
                brackets,
                key=lambda item: (
                    item[0].instant,
                    item[1].instant,
                    item[2].value,
                ),
            )
        )
        for previous, current in zip(ordered, ordered[1:]):
            if previous[1].instant > current[0].instant:
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.CONTACT_BRACKET_INCONSISTENT,
                    "transition brackets overlap.",
                )
        results = []
        for left, right, kind in ordered:
            if (
                left.geocentric_state is None
                or right.geocentric_state is None
                or left.sun_ephemeris_state is None
                or right.sun_ephemeris_state is None
            ):
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.CONTACT_BRACKET_INCONSISTENT,
                    "production transition bracket lacks resource evidence.",
                )
            if (
                left.sun_ephemeris_state.resource
                != right.sun_ephemeris_state.resource
            ):
                raise SatelliteIlluminationGeometryError(
                    SatelliteIlluminationFailureCode.FRAME_MISMATCH,
                    "transition sides use different Sun ephemeris resources.",
                )
            width = (
                right.instant - left.instant
            ).total_seconds()
            event = left.instant + (right.instant - left.instant) / 2
            results.append(
                SatelliteShadowTransition(
                    record=record,
                    snapshot_id=query.snapshot.manifest.snapshot_id,
                    snapshot_sha256=(
                        query.snapshot.manifest.content_sha256
                    ),
                    query_interval=query.interval,
                    left_class=left.contact.occultation_class,
                    right_class=right.contact.occultation_class,
                    kind=kind,
                    event_utc=_utc_instant(event),
                    bracket_start_utc=_utc_instant(left.instant),
                    bracket_stop_utc=_utc_instant(right.instant),
                    time_tolerance_seconds=(
                        query.search_policy.time_tolerance_seconds
                    ),
                    achieved_bracket_width_seconds=width,
                    evaluation_count=cache.evaluation_count,
                    occultation_policy=query.occultation_policy,
                    search_policy=query.search_policy,
                    left_earth_orientation=(
                        left.geocentric_state.earth_orientation
                    ),
                    right_earth_orientation=(
                        right.geocentric_state.earth_orientation
                    ),
                    sun_ephemeris_resource=(
                        left.sun_ephemeris_state.resource
                    ),
                    provenance=(
                        SHADOW_TRANSITION_IMPLEMENTATION,
                        "Observer-independent event geometry.",
                        "Continuous ellipsoid-limb contact margins; "
                        "visible-fraction quadrature is not a root function.",
                        "Complete closed-interval subdivision under the "
                        "declared conservative contact-rate envelope.",
                    ),
                    warnings=(
                        "Geometric vacuum contact; not a brightness or "
                        "visibility claim.",
                    ),
                )
            )
        return tuple(results)
