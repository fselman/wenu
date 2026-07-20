# src/wenu/sky/coordinate_grids.py

from __future__ import annotations

from typing import Any
from abc import ABC, abstractmethod

import numpy as np
from astropy.coordinates import (
        BarycentricTrueEcliptic,
        FK5, 
        Galactic,
        ICRS, 
        SkyCoord,
        )

from astropy.time import Time
import astropy.units as u

from wenu.geometry import radec_to_altaz
from wenu.sky.curves import CelestialCurve


class SphericalCoordinatesGrid(ABC):
    """
    Base class for grids defined by spherical longitude and latitude.

    Subclasses define how their native longitude and latitude coordinates
    are transformed into ICRS right ascension and declination.
    """

    def __init__(
        self,
        observer,
        *,
        samples: int = 721,
    ) -> None:
        if samples < 4:
            raise ValueError("samples must be at least 4.")

        self.observer = observer
        self.samples = int(samples)

    def parallel(
        self,
        latitude_deg: float,
        *,
        name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-latitude parallel.
        """
        latitude_deg = float(latitude_deg)

        if not -90.0 <= latitude_deg <= 90.0:
            raise ValueError(
                "latitude_deg must lie between -90 and 90 degrees."
            )

        longitude_deg = np.linspace(
            0.0,
            360.0,
            self.samples,
            endpoint=False,
        )

        latitude = np.full_like(
            longitude_deg,
            latitude_deg,
        )

        return self._make_curve(
            longitude_deg=longitude_deg,
            latitude_deg=latitude,
            name=(
                f"latitude_{latitude_deg:g}"
                if name is None
                else name
            ),
            closed=True,
            style=style,
        )

    def meridian(
        self,
        longitude_deg: float,
        *,
        name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-longitude meridian.
        """
        longitude_deg = float(longitude_deg) % 360.0

        latitude_deg = np.linspace(
            -90.0,
            90.0,
            self.samples,
        )

        longitude = np.full_like(
            latitude_deg,
            longitude_deg,
        )

        return self._make_curve(
            longitude_deg=longitude,
            latitude_deg=latitude_deg,
            name=(
                f"longitude_{longitude_deg:g}"
                if name is None
                else name
            ),
            closed=False,
            style=style,
        )

    def grid(
        self,
        *,
        longitudes=None,
        latitudes=None,
        meridian_style=None,
        parallel_style=None,
    ) -> list[CelestialCurve]:
        """
        Construct a complete coordinate grid.

        Coordinate values are passed positionally so subclasses may expose
        frame-specific parameter names, such as ``right_ascension_deg`` and
        ``declination_deg``.
        """
        curves: list[CelestialCurve] = []

        if longitudes is not None:
            for longitude_deg in longitudes:
                curves.append(
                    self.meridian(
                        float(longitude_deg),
                        style=meridian_style,
                    )
                )

        if latitudes is not None:
            for latitude_deg in latitudes:
                curves.append(
                    self.parallel(
                        float(latitude_deg),
                        style=parallel_style,
                    )
                )

        return curves

    def _make_curve(
        self,
        *,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
        name: str,
        closed: bool,
        style: dict[str, Any] | None,
    ) -> CelestialCurve:
        """
        Transform native grid coordinates and construct a CelestialCurve.
        """
        alt_deg, az_deg = self._native_to_altaz(
            longitude_deg,
            latitude_deg,
        )

        return CelestialCurve(
            alt_deg=alt_deg,
            az_deg=az_deg,
            name=name,
            closed=closed,
            style={} if style is None else dict(style),
        )

    def _native_to_altaz(
        self,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert native spherical coordinates to apparent altitude and azimuth.

        The default transformation passes through ICRS. Subclasses define
        how their native longitude and latitude coordinates map to ICRS.
        """
        ra_deg, dec_deg = self._native_to_icrs(
            longitude_deg,
            latitude_deg,
        )

        alt_deg, az_deg = radec_to_altaz(
            ra_deg,
            dec_deg,
            self.observer.t,
            self.observer.lat_deg,
            self.observer.lon_deg,
        )

        return (
            np.asarray(alt_deg),
            np.asarray(az_deg),
        )

    @abstractmethod
    def _native_to_icrs(
        self,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert native longitude and latitude to ICRS RA and Dec.
        """
        raise NotImplementedError

class EquatorialGrid(SphericalCoordinatesGrid):
    """
    Curves belonging to an equatorial coordinate system.

    This class performs astronomical coordinate calculations but has no
    knowledge of Matplotlib or map projections.

    Parameters
    ----------
    observer
        Wenu observer supplying time and geographic location.
    frame
        Equatorial reference frame. Currently ``"icrs"`` or ``"fk5"``.
    equinox
        Equinox used for FK5 coordinates. It may be an Astropy ``Time``,
        a value accepted by ``Time``, or ``"of_date"``.
    samples
        Number of samples used for complete circles.
    """

    def __init__(
        self,
        observer,
        *,
        frame: str = "fk5",
        equinox: str | Time = "of_date",
        samples: int = 721,
    ) -> None:
        super().__init__(
            observer,
            samples=samples,
        )

        self.frame = frame.lower()
        self.equinox = equinox

        if self.frame not in {"icrs", "fk5"}:
            raise ValueError(
                "frame must currently be either 'icrs' or 'fk5'."
            )

    def equator(
        self,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return the celestial equator as a closed apparent-sky curve.
        """
        return super().parallel(
            0.0,
            name="celestial_equator",
            style=style,
        )

    def parallel(
        self,
        declination_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-declination parallel.
        """
        declination_deg = float(declination_deg)

        return super().parallel(
            declination_deg,
            name=f"declination_{declination_deg:g}",
            style=style,
        )

    def meridian(
        self,
        right_ascension_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-right-ascension meridian.
        """
        right_ascension_deg = float(right_ascension_deg) % 360.0

        return super().meridian(
            right_ascension_deg,
            name=f"right_ascension_{right_ascension_deg:g}",
            style=style,
        )


    def grid(
        self,
        *,
        ra=None,
        dec=None,
        meridian_style: dict[str, Any] | None = None,
        parallel_style: dict[str, Any] | None = None,
    ) -> list[CelestialCurve]:
        """
        Construct an equatorial coordinate grid.

        Parameters
        ----------
        ra
            Right ascensions of meridians, in degrees.
        dec
            Declinations of parallels, in degrees.
        meridian_style
            Style stored in each right-ascension meridian.
        parallel_style
            Style stored in each declination parallel.
        """
        return super().grid(
            longitudes=ra,
            latitudes=dec,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )


    def _native_to_icrs(
        self,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert coordinates in this grid's frame to ICRS RA and Dec.
        """
        if self.frame == "icrs":
            coordinates = SkyCoord(
                ra=longitude_deg * u.deg,
                dec=latitude_deg * u.deg,
                frame=ICRS(),
            )
        else:
            coordinates = SkyCoord(
                ra=longitude_deg * u.deg,
                dec=latitude_deg * u.deg,
                frame=FK5(equinox=self._equinox_time()),
            )

        icrs = coordinates.icrs

        return (
            np.asarray(icrs.ra.deg),
            np.asarray(icrs.dec.deg),
        )

    def _equinox_time(self) -> Time:
        """
        Resolve the requested FK5 equinox.
        """
        if isinstance(self.equinox, Time):
            return self.equinox

        if str(self.equinox).lower() == "of_date":
            try:
                return self.observer.t_astropy
            except AttributeError as exc:
                raise AttributeError(
                    "The observer must define t_astropy when "
                    "equinox='of_date'."
                ) from exc

        return Time(self.equinox)

class EclipticGrid(SphericalCoordinatesGrid):
    """
    Curves belonging to an ecliptic coordinate system.

    Parameters
    ----------
    observer
        Wenu observer supplying time and geographic location.
    equinox
        Equinox of the ecliptic frame. It may be an Astropy ``Time``,
        a value accepted by ``Time``, or ``"of_date"``.
    samples
        Number of samples used for complete circles.
    """

    def __init__(
        self,
        observer,
        *,
        equinox: str | Time = "of_date",
        samples: int = 721,
    ) -> None:
        super().__init__(
            observer,
            samples=samples,
        )

        self.equinox = equinox

    def ecliptic(
        self,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return the ecliptic as a closed apparent-sky curve.
        """
        return super().parallel(
            0.0,
            name="ecliptic",
            style=style,
        )

    def parallel(
        self,
        ecliptic_latitude_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-ecliptic-latitude parallel.
        """
        ecliptic_latitude_deg = float(ecliptic_latitude_deg)

        return super().parallel(
            ecliptic_latitude_deg,
            name=f"ecliptic_latitude_{ecliptic_latitude_deg:g}",
            style=style,
        )

    def meridian(
        self,
        ecliptic_longitude_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-ecliptic-longitude meridian.
        """
        ecliptic_longitude_deg = float(ecliptic_longitude_deg) % 360.0

        return super().meridian(
            ecliptic_longitude_deg,
            name=f"ecliptic_longitude_{ecliptic_longitude_deg:g}",
            style=style,
        )

    def grid(
        self,
        *,
        longitude=None,
        latitude=None,
        meridian_style: dict[str, Any] | None = None,
        parallel_style: dict[str, Any] | None = None,
    ) -> list[CelestialCurve]:
        """
        Construct an ecliptic coordinate grid.

        Parameters
        ----------
        longitude
            Ecliptic longitudes of meridians, in degrees.
        latitude
            Ecliptic latitudes of parallels, in degrees.
        meridian_style
            Style stored in each ecliptic meridian.
        parallel_style
            Style stored in each ecliptic parallel.
        """
        return super().grid(
            longitudes=longitude,
            latitudes=latitude,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def _native_to_icrs(
        self,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert ecliptic longitude and latitude to ICRS RA and Dec.
        """
        coordinates = SkyCoord(
            lon=longitude_deg * u.deg,
            lat=latitude_deg * u.deg,
            frame=BarycentricTrueEcliptic(
                equinox=self._equinox_time(),
            ),
        )

        icrs = coordinates.icrs

        return (
            np.asarray(icrs.ra.deg),
            np.asarray(icrs.dec.deg),
        )

    def _equinox_time(self) -> Time:
        """
        Resolve the requested ecliptic equinox.
        """
        if isinstance(self.equinox, Time):
            return self.equinox

        if str(self.equinox).lower() == "of_date":
            try:
                return self.observer.t_astropy
            except AttributeError as exc:
                raise AttributeError(
                    "The observer must define t_astropy when "
                    "equinox='of_date'."
                ) from exc

        return Time(self.equinox)

class GalacticGrid(SphericalCoordinatesGrid):
    """
    Curves belonging to the IAU Galactic coordinate system.

    Parameters
    ----------
    observer
        Wenu observer supplying time and geographic location.
    samples
        Number of samples used for complete circles.
    """

    def galactic_plane(
        self,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return the Galactic plane as a closed apparent-sky curve.
        """
        return super().parallel(
            0.0,
            name="galactic_plane",
            style=style,
        )

    def parallel(
        self,
        galactic_latitude_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-Galactic-latitude parallel.
        """
        galactic_latitude_deg = float(galactic_latitude_deg)

        return super().parallel(
            galactic_latitude_deg,
            name=f"galactic_latitude_{galactic_latitude_deg:g}",
            style=style,
        )

    def meridian(
        self,
        galactic_longitude_deg: float,
        *,
        style: dict[str, Any] | None = None,
    ) -> CelestialCurve:
        """
        Return a constant-Galactic-longitude meridian.
        """
        galactic_longitude_deg = float(galactic_longitude_deg) % 360.0

        return super().meridian(
            galactic_longitude_deg,
            name=f"galactic_longitude_{galactic_longitude_deg:g}",
            style=style,
        )

    def grid(
        self,
        *,
        longitude=None,
        latitude=None,
        meridian_style: dict[str, Any] | None = None,
        parallel_style: dict[str, Any] | None = None,
    ) -> list[CelestialCurve]:
        """
        Construct a Galactic coordinate grid.

        Parameters
        ----------
        longitude
            Galactic longitudes of meridians, in degrees.
        latitude
            Galactic latitudes of parallels, in degrees.
        meridian_style
            Style stored in each Galactic meridian.
        parallel_style
            Style stored in each Galactic parallel.
        """
        return super().grid(
            longitudes=longitude,
            latitudes=latitude,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def _native_to_icrs(
        self,
        longitude_deg: np.ndarray,
        latitude_deg: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert Galactic longitude and latitude to ICRS RA and Dec.
        """
        coordinates = SkyCoord(
            l=longitude_deg * u.deg,
            b=latitude_deg * u.deg,
            frame=Galactic(),
        )

        icrs = coordinates.icrs

        return (
            np.asarray(icrs.ra.deg),
            np.asarray(icrs.dec.deg),
        )

