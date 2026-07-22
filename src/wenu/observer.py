# src/wenu/observer.py

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricMeanEcliptic,
    EarthLocation,
    Galactic,
    ICRS,
)
from astropy.time import Time
from skyfield.api import Loader, wgs84


DEFAULT_EPHEMERIS = "de440s.bsp"
DEFAULT_DATA_DIRECTORY = Path.home() / ".cache" / "wenu"


LOCATIONS = {
    "la ligua": {
        "name": "La Ligua",
        "lat_deg": -32.443342,
        "lon_deg": -71.230289,
        "elevation_m": 52.0,
        "timezone": "America/Santiago",
    },
    "papudo": {
        "name": "Papudo",
        "lat_deg": -32.5078,
        "lon_deg": -71.4411,
        "elevation_m": 15.0,
        "timezone": "America/Santiago",
    },
}


class Observer:
    """
    Observation context shared by Wenu components.

    An observer can be created from either:

    - a named location, such as ``"La Ligua"``; or
    - explicit latitude, longitude, and elevation.

    Time can be supplied as:

    - ``"now"``;
    - an ISO-format string;
    - a timezone-aware or naive datetime.

    Naive local times require a named location or ``timezone_name``.
    """

    def __init__(
        self,
        *,
        location: str | None = None,
        time: str | datetime = "now",
        lat_deg: float | None = None,
        lon_deg: float | None = None,
        elevation_m: float | None = None,
        timezone_name: str | None = None,
        ephemeris_name: str = DEFAULT_EPHEMERIS,
        data_directory: str | Path = DEFAULT_DATA_DIRECTORY,
    ) -> None:
        (
            self.lat_deg,
            self.lon_deg,
            self.elevation_m,
            self.timezone_name,
            self.location_name,
        ) = self._resolve_location(
            location=location,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            elevation_m=elevation_m,
            timezone_name=timezone_name,
        )

        self.utc_datetime = self._resolve_time(
            time,
            timezone_name=self.timezone_name,
        )

        self.data_directory = Path(data_directory).expanduser()
        self.data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.loader = Loader(str(self.data_directory))
        self.timescale = self.loader.timescale()

        self.t = self.timescale.from_datetime(
            self.utc_datetime
        )

        self.ephemeris_name = ephemeris_name
        self.ephemeris = self.loader(
            self.ephemeris_name
        )

        self.earth = self.ephemeris["earth"]

        self.location = wgs84.latlon(
            latitude_degrees=self.lat_deg,
            longitude_degrees=self.lon_deg,
            elevation_m=self.elevation_m,
        )

        # Preserve the existing Wenu public attribute.
        self.skyfield = self.earth + self.location

        # Optional descriptive alias.
        self.topos = self.skyfield

    @staticmethod
    def _resolve_location(
        *,
        location: str | None,
        lat_deg: float | None,
        lon_deg: float | None,
        elevation_m: float | None,
        timezone_name: str | None,
    ) -> tuple[
        float,
        float,
        float,
        str | None,
        str | None,
    ]:
        if location is not None:
            if any(
                value is not None
                for value in (
                    lat_deg,
                    lon_deg,
                    elevation_m,
                    timezone_name,
                )
            ):
                raise ValueError(
                    "Specify either location=... or explicit "
                    "coordinates, not both."
                )

            key = location.strip().casefold()

            try:
                site = LOCATIONS[key]
            except KeyError as exc:
                available = ", ".join(
                    site["name"]
                    for site in LOCATIONS.values()
                )

                raise ValueError(
                    f"Unknown location {location!r}. "
                    f"Available locations: {available}"
                ) from exc

            return (
                float(site["lat_deg"]),
                float(site["lon_deg"]),
                float(site.get("elevation_m", 0.0)),
                str(site["timezone"]),
                str(site["name"]),
            )

        if lat_deg is None or lon_deg is None:
            raise ValueError(
                "Provide either location=... or both "
                "lat_deg and lon_deg."
            )

        return (
            float(lat_deg),
            float(lon_deg),
            float(
                0.0 if elevation_m is None
                else elevation_m
            ),
            timezone_name,
            None,
        )

    @staticmethod
    def _resolve_time(
        value: str | datetime,
        *,
        timezone_name: str | None,
    ) -> datetime:
        if isinstance(value, datetime):
            resolved = value

        elif isinstance(value, str):
            text = value.strip()

            if text.casefold() == "now":
                return datetime.now(timezone.utc)

            try:
                resolved = datetime.fromisoformat(
                    text.replace("Z", "+00:00")
                )
            except ValueError as exc:
                raise ValueError(
                    "time must be 'now' or an ISO-format "
                    "date and time, for example "
                    "'2026-08-15 21:00' or "
                    "'2026-08-16T01:00:00Z'."
                ) from exc

        else:
            raise TypeError(
                "time must be a datetime object or string."
            )

        if resolved.tzinfo is None:
            if timezone_name is None:
                raise ValueError(
                    "A time without a UTC offset requires "
                    "a named location or timezone_name=..."
                )

            resolved = resolved.replace(
                tzinfo=ZoneInfo(timezone_name)
            )

        return resolved.astimezone(timezone.utc)

    @property
    def t_astropy(self) -> Time:
        return Time(
            self.utc_datetime,
            scale="utc",
        )

    @property
    def earth_location(self) -> EarthLocation:
        return EarthLocation.from_geodetic(
            lon=self.lon_deg * u.deg,
            lat=self.lat_deg * u.deg,
            height=self.elevation_m * u.m,
        )

    @property
    def icrs_frame(self) -> ICRS:
        return ICRS()

    @property
    def galactic_frame(self) -> Galactic:
        return Galactic()

    @property
    def ecliptic_frame(
        self,
    ) -> BarycentricMeanEcliptic:
        """
        Barycentric mean ecliptic of the observation date.
        """
        return BarycentricMeanEcliptic(
            equinox=self.t_astropy,
        )

    @property
    def altaz_frame(self) -> AltAz:
        return AltAz(
            obstime=self.t_astropy,
            location=self.earth_location,
        )


