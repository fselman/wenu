"""Earth-orientation and observer transformation for satellite TEME states."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from importlib.metadata import version
from math import asin, cos, degrees, isfinite, radians, sin
from pathlib import Path
import warnings

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    CartesianDifferential,
    CartesianRepresentation,
    EarthLocation,
    GCRS,
    ITRS,
    TEME,
)
from astropy.time import Time
from astropy.utils import iers
from astropy_iers_data import IERS_A_FILE

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.satellite_crossings import (
    SatelliteFieldOfView,
    SatelliteObserver,
)
from wenu.satellites.sgp4 import SatelliteTemeState


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


def _vector(value, *, name):
    try:
        result = tuple(_finite(item, name=f"{name} entry") for item in value)
    except TypeError as error:
        raise TypeError(f"{name} must contain three finite values.") from error
    if len(result) != 3:
        raise ValueError(f"{name} must contain three finite values.")
    return result


def _status(value):
    return int(np.asarray(value).reshape(()))


def _quantity(value, unit):
    return float(np.asarray(value.to_value(unit)).reshape(()))


def _coverage_value(value):
    quantity = getattr(value, "quantity", value)
    if hasattr(quantity, "to_value"):
        return float(np.asarray(quantity.to_value(u.d)).reshape(()))
    return float(value)


class SatelliteEarthOrientationError(ValueError):
    """Raised when the declared local Earth-orientation resource is unusable."""


@dataclass(frozen=True)
class SatelliteEarthOrientationEvidence:
    """Exact installed Earth-orientation resource and interpolated values."""

    table_class: str
    source_path: str
    source_sha256: str
    astropy_version: str
    astropy_iers_data_version: str
    coverage_start_mjd: float
    coverage_stop_mjd: float
    ut1_minus_utc_s: float
    polar_motion_x_arcsec: float
    polar_motion_y_arcsec: float
    ut1_status: int
    polar_motion_status: int

    def __post_init__(self):
        for name in (
            "table_class",
            "source_path",
            "source_sha256",
            "astropy_version",
            "astropy_iers_data_version",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        if len(self.source_sha256) != 64:
            raise ValueError("source_sha256 must be a SHA-256 hexadecimal digest.")
        for name in (
            "coverage_start_mjd",
            "coverage_stop_mjd",
            "ut1_minus_utc_s",
            "polar_motion_x_arcsec",
            "polar_motion_y_arcsec",
        ):
            object.__setattr__(
                self,
                name,
                _finite(getattr(self, name), name=name),
            )
        if self.coverage_stop_mjd < self.coverage_start_mjd:
            raise ValueError("Earth-orientation coverage is reversed.")
        for name in ("ut1_status", "polar_motion_status"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")


@dataclass(frozen=True)
class SatelliteTopocentricState:
    """Immutable geometric state for one observer and one TEME evaluation."""

    teme_state: SatelliteTemeState
    observer: SatelliteObserver
    earth_orientation: SatelliteEarthOrientationEvidence
    satellite_itrs_position_km: tuple[float, float, float]
    satellite_itrs_velocity_km_per_s: tuple[float, float, float]
    observer_itrs_position_km: tuple[float, float, float]
    topocentric_itrs_position_km: tuple[float, float, float]
    topocentric_itrs_velocity_km_per_s: tuple[float, float, float]
    range_km: float
    azimuth_deg: float
    altitude_deg: float
    gcrs_axis_longitude_deg: float
    gcrs_axis_latitude_deg: float
    horizontal_coordinate_spec: CoordinateSpec
    celestial_axis_coordinate_spec: CoordinateSpec
    provenance: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not isinstance(self.teme_state, SatelliteTemeState):
            raise TypeError("teme_state must be a SatelliteTemeState.")
        if not isinstance(self.observer, SatelliteObserver):
            raise TypeError("observer must be a SatelliteObserver.")
        if not isinstance(
            self.earth_orientation, SatelliteEarthOrientationEvidence
        ):
            raise TypeError(
                "earth_orientation must be SatelliteEarthOrientationEvidence."
            )
        for name in (
            "satellite_itrs_position_km",
            "satellite_itrs_velocity_km_per_s",
            "observer_itrs_position_km",
            "topocentric_itrs_position_km",
            "topocentric_itrs_velocity_km_per_s",
        ):
            object.__setattr__(
                self,
                name,
                _vector(getattr(self, name), name=name),
            )
        for name in (
            "range_km",
            "azimuth_deg",
            "altitude_deg",
            "gcrs_axis_longitude_deg",
            "gcrs_axis_latitude_deg",
        ):
            object.__setattr__(
                self,
                name,
                _finite(getattr(self, name), name=name),
            )
        if self.range_km <= 0.0:
            raise ValueError("range_km must be positive.")
        if not 0.0 <= self.azimuth_deg < 360.0:
            raise ValueError("azimuth_deg must lie in [0, 360).")
        if not -90.0 <= self.altitude_deg <= 90.0:
            raise ValueError("altitude_deg must lie in [-90, 90].")
        if not 0.0 <= self.gcrs_axis_longitude_deg < 360.0:
            raise ValueError(
                "gcrs_axis_longitude_deg must lie in [0, 360)."
            )
        if not -90.0 <= self.gcrs_axis_latitude_deg <= 90.0:
            raise ValueError(
                "gcrs_axis_latitude_deg must lie in [-90, 90]."
            )
        for name in (
            "horizontal_coordinate_spec",
            "celestial_axis_coordinate_spec",
        ):
            if not isinstance(getattr(self, name), CoordinateSpec):
                raise TypeError(f"{name} must be a CoordinateSpec.")
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))


def _earth_orientation(time):
    source = Path(IERS_A_FILE)
    digest = sha256(source.read_bytes()).hexdigest()
    table = iers.IERS_A.open(str(source))
    with warnings.catch_warnings():
        warnings.simplefilter("error", iers.IERSWarning)
        try:
            ut1, ut1_status = table.ut1_utc(time, return_status=True)
            pm_x, pm_y, pm_status = table.pm_xy(time, return_status=True)
        except (ValueError, iers.IERSRangeError, iers.IERSWarning) as error:
            raise SatelliteEarthOrientationError(
                "The installed IERS-A resource cannot evaluate this instant."
            ) from error
    ut1_status = _status(ut1_status)
    pm_status = _status(pm_status)
    if ut1_status < 0 or pm_status < 0:
        raise SatelliteEarthOrientationError(
            "The evaluation instant lies outside installed IERS-A coverage."
        )
    return table, SatelliteEarthOrientationEvidence(
        table_class=f"{type(table).__module__}.{type(table).__name__}",
        source_path=str(source),
        source_sha256=digest,
        astropy_version=version("astropy"),
        astropy_iers_data_version=version("astropy-iers-data"),
        coverage_start_mjd=_coverage_value(table["MJD"][0]),
        coverage_stop_mjd=_coverage_value(table["MJD"][-1]),
        ut1_minus_utc_s=_quantity(ut1, u.s),
        polar_motion_x_arcsec=_quantity(pm_x, u.arcsec),
        polar_motion_y_arcsec=_quantity(pm_y, u.arcsec),
        ut1_status=ut1_status,
        polar_motion_status=pm_status,
    )


def _cartesian_tuple(representation, unit):
    return tuple(
        float(value)
        for value in np.asarray(representation.xyz.to_value(unit), dtype=float)
    )


def _differential_tuple(differential, unit):
    return tuple(
        float(value)
        for value in np.asarray(differential.d_xyz.to_value(unit), dtype=float)
    )


class SatelliteTopocentricTransformer:
    """Apply the governed TEME-to-observer geometric transformation chain."""

    def transform(
        self,
        state: SatelliteTemeState,
        observer: SatelliteObserver,
    ) -> SatelliteTopocentricState:
        if not isinstance(state, SatelliteTemeState):
            raise TypeError("state must be a SatelliteTemeState.")
        if not isinstance(observer, SatelliteObserver):
            raise TypeError("observer must be a SatelliteObserver.")
        if observer.refraction_policy != "vacuum":
            raise ValueError("Satellite topocentric state requires vacuum.")
        if observer.earth_orientation_policy not in {
            "astropy",
            "iers-a-bundled",
        }:
            raise ValueError(
                "Unsupported satellite Earth-orientation policy."
            )

        time = Time(state.evaluation_utc, scale="utc")
        table, evidence = _earth_orientation(time)
        location = EarthLocation.from_geodetic(
            lon=observer.longitude_deg * u.deg,
            lat=observer.latitude_deg * u.deg,
            height=observer.elevation_m * u.m,
            ellipsoid="WGS84",
        )
        position = CartesianRepresentation(
            np.asarray(state.position_km, dtype=float) * u.km
        )
        velocity = CartesianDifferential(
            np.asarray(state.velocity_km_per_s, dtype=float) * u.km / u.s
        )
        teme = TEME(
            position.with_differentials(velocity),
            obstime=time,
        )

        with iers.conf.set_temp("auto_download", False):
            with iers.conf.set_temp("iers_degraded_accuracy", "error"):
                with iers.earth_orientation_table.set(table):
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", iers.IERSWarning)
                        try:
                            itrs_geo = teme.transform_to(ITRS(obstime=time))
                            observer_itrs = location.get_itrs(obstime=time)
                            satellite_position = (
                                itrs_geo.cartesian.without_differentials()
                            )
                            satellite_velocity = (
                                itrs_geo.cartesian.differentials["s"]
                            )
                            topocentric_position = (
                                satellite_position
                                - observer_itrs.cartesian
                            )
                            topocentric_representation = (
                                topocentric_position.with_differentials(
                                    satellite_velocity
                                )
                            )
                            itrs_topocentric = ITRS(
                                topocentric_representation,
                                obstime=time,
                                location=location,
                            )
                            horizontal = itrs_topocentric.transform_to(
                                AltAz(
                                    obstime=time,
                                    location=location,
                                    pressure=0.0 * u.hPa,
                                )
                            )
                            gcrs_axis = ITRS(
                                topocentric_position,
                                obstime=time,
                            ).transform_to(GCRS(obstime=time))
                        except (
                            ValueError,
                            iers.IERSRangeError,
                            iers.IERSWarning,
                        ) as error:
                            raise SatelliteEarthOrientationError(
                                "Satellite topocentric transformation failed "
                                "with the installed Earth-orientation resource."
                            ) from error

        instant = state.evaluation_utc
        common_provenance = (
            "Astropy TEME to ITRS with explicit installed IERS-A table.",
            "WGS-84 observer subtracted in ITRS before angular conversion.",
            f"IERS-A SHA-256 {evidence.source_sha256}.",
        )
        horizontal_spec = CoordinateSpec(
            frame="altaz",
            origin="observer",
            position_status=PositionStatus.GEOMETRIC,
            instant=instant,
            time_scale="utc",
            provider="astropy",
            model="TEME to ITRS to topocentric vacuum AltAz",
            provenance=common_provenance,
            corrections=frozenset(
                {"earth-orientation", "polar-motion", "observer-parallax"}
            ),
        )
        celestial_spec = CoordinateSpec(
            frame="gcrs-axes",
            origin="topocentric-direction",
            position_status=PositionStatus.GEOMETRIC,
            instant=instant,
            time_scale="utc",
            provider="astropy",
            model="topocentric ITRS vector rotated into GCRS axes",
            provenance=common_provenance,
            corrections=frozenset(
                {"earth-orientation", "polar-motion", "observer-parallax"}
            ),
        )
        gcrs_spherical = gcrs_axis.spherical
        return SatelliteTopocentricState(
            teme_state=state,
            observer=observer,
            earth_orientation=evidence,
            satellite_itrs_position_km=_cartesian_tuple(
                satellite_position, u.km
            ),
            satellite_itrs_velocity_km_per_s=_differential_tuple(
                satellite_velocity, u.km / u.s
            ),
            observer_itrs_position_km=_cartesian_tuple(
                observer_itrs.cartesian, u.km
            ),
            topocentric_itrs_position_km=_cartesian_tuple(
                topocentric_position, u.km
            ),
            topocentric_itrs_velocity_km_per_s=_differential_tuple(
                satellite_velocity, u.km / u.s
            ),
            range_km=_quantity(horizontal.distance, u.km),
            azimuth_deg=_quantity(horizontal.az, u.deg) % 360.0,
            altitude_deg=_quantity(horizontal.alt, u.deg),
            gcrs_axis_longitude_deg=(
                _quantity(gcrs_spherical.lon, u.deg) % 360.0
            ),
            gcrs_axis_latitude_deg=_quantity(
                gcrs_spherical.lat, u.deg
            ),
            horizontal_coordinate_spec=horizontal_spec,
            celestial_axis_coordinate_spec=celestial_spec,
            provenance=common_provenance,
            warnings=(
                "Geometric vacuum direction; no atmospheric refraction.",
                "GCRS-axis values are a rotated topocentric geometric vector, "
                "not an ICRS/GCRS astrometric or apparent coordinate.",
            ),
        )


class SatelliteFieldCenterAltitudeEvaluator:
    """Evaluate one fixed GCRS-axis field centre in geometric vacuum AltAz."""

    def evaluate(
        self,
        field: SatelliteFieldOfView,
        observer: SatelliteObserver,
        instant: str,
    ) -> tuple[float, SatelliteEarthOrientationEvidence]:
        if not isinstance(field, SatelliteFieldOfView):
            raise TypeError("field must be a SatelliteFieldOfView.")
        if not isinstance(observer, SatelliteObserver):
            raise TypeError("observer must be a SatelliteObserver.")
        spec = field.coordinate_spec
        if (
            spec.frame != "gcrs-axes"
            or spec.origin != "topocentric-direction"
            or spec.position_status is not PositionStatus.GEOMETRIC
            or spec.time_scale != "utc"
        ):
            raise ValueError(
                "field must be a geometric topocentric direction in GCRS axes."
            )
        if observer.refraction_policy != "vacuum":
            raise ValueError("Field-centre altitude requires vacuum.")
        if observer.earth_orientation_policy not in {
            "astropy",
            "iers-a-bundled",
        }:
            raise ValueError(
                "Unsupported satellite Earth-orientation policy."
            )

        time = Time(instant, scale="utc")
        table, evidence = _earth_orientation(time)
        longitude = radians(field.center_longitude_deg)
        latitude = radians(field.center_latitude_deg)
        vector = np.asarray(
            (
                cos(latitude) * cos(longitude),
                cos(latitude) * sin(longitude),
                sin(latitude),
            ),
            dtype=float,
        )
        direction = GCRS(
            CartesianRepresentation(vector),
            obstime=time,
        )
        with iers.conf.set_temp("auto_download", False):
            with iers.conf.set_temp("iers_degraded_accuracy", "error"):
                with iers.earth_orientation_table.set(table):
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", iers.IERSWarning)
                        try:
                            itrs = direction.transform_to(ITRS(obstime=time))
                        except (
                            ValueError,
                            iers.IERSRangeError,
                            iers.IERSWarning,
                        ) as error:
                            raise SatelliteEarthOrientationError(
                                "Field-centre altitude transformation failed "
                                "with the installed Earth-orientation resource."
                            ) from error

        itrs_vector = np.asarray(itrs.cartesian.xyz.value, dtype=float)
        itrs_vector /= np.linalg.norm(itrs_vector)
        site_longitude = radians(observer.longitude_deg)
        site_latitude = radians(observer.latitude_deg)
        geodetic_up = np.asarray(
            (
                cos(site_latitude) * cos(site_longitude),
                cos(site_latitude) * sin(site_longitude),
                sin(site_latitude),
            ),
            dtype=float,
        )
        altitude = degrees(
            asin(float(np.clip(np.dot(itrs_vector, geodetic_up), -1.0, 1.0)))
        )
        return altitude, evidence
