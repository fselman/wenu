# src/wenu/observer.py

from __future__ import annotations

import hashlib
import json
import unicodedata
import weakref
from datetime import datetime, timezone
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo

from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
from skyfield.api import Loader, wgs84

from wenu.coordinates import observation_context


DEFAULT_EPHEMERIS = "de440s.bsp"
DEFAULT_DATA_DIRECTORY = Path.home() / ".cache" / "wenu"


# Retained two-site compatibility constant; named lookup uses the versioned
# packaged catalogue below, whose legacy entries are regression-checked.
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


def _location_token(value):
    """Normalize spelling without weakening administrative qualification."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(
        "".join(
            character for character in decomposed
            if not unicodedata.combining(character)
        ).replace("’", "'").split()
    )


@lru_cache(maxsize=1)
def _registered_locations():
    """Load the digest-verified, immutable, offline location snapshot."""
    resource = files("wenu.data")
    payload = resource.joinpath("chile_locations_v1.json").read_bytes()
    manifest = json.loads(
        resource.joinpath("chile_locations_manifest_v1.json").read_text(
            encoding="utf-8"
        )
    )
    if hashlib.sha256(payload).hexdigest() != manifest["catalogue_sha256"]:
        raise ValueError("Packaged Chile location catalogue digest mismatch.")
    catalogue = json.loads(payload)
    if catalogue.get("schema_version") != 1:
        raise ValueError("Unsupported Chile location catalogue schema.")
    records = []
    identifiers = set()
    for source in catalogue["locations"]:
        record = dict(source)
        if record["id"] in identifiers:
            raise ValueError("Duplicate packaged location identifier.")
        identifiers.add(record["id"])
        record["aliases"] = tuple(record.get("aliases", ()))
        record["region_aliases"] = tuple(record.get("region_aliases", ()))
        record["qualified_name"] = ":".join(
            record[field]
            for field in ("country", "region", "province", "commune", "name")
        )
        records.append(MappingProxyType(record))
    return tuple(records)


def _resolve_registered_location(value):
    """Resolve a unique name, stable ID or administrative suffix."""
    tokens = tuple(_location_token(part) for part in value.split(":"))
    if not 1 <= len(tokens) <= 5 or not all(tokens):
        raise ValueError(
            "Location must be a name or Country:Region:Province:Comune:City "
            "(a unique shorter suffix is also accepted)."
        )
    matches = []
    for site in _registered_locations():
        names = (site["name"], *site["aliases"])
        if len(tokens) == 1:
            match = tokens[0] in {
                _location_token(name) for name in (*names, site["id"])
            }
        else:
            hierarchy = (
                site["country"], site["region"],
                site["province"], site["commune"]
            )
            prefixes = [hierarchy]
            if len(tokens) >= 4:
                prefixes.extend(
                    (site["country"], region, site["province"], site["commune"])
                    for region in site["region_aliases"]
                )
            match = any(
                tokens == tuple(
                    _location_token(part)
                    for part in (*prefix, name)[-len(tokens):]
                )
                for prefix in prefixes for name in names
            )
        if match:
            matches.append(site)
    if not matches:
        raise ValueError(
            f"Unknown location {value!r}. See the versioned Chile "
            "location table or use explicit latitude and longitude."
        )
    if len(matches) > 1:
        alternatives = "; ".join(
            sorted(site["qualified_name"] for site in matches)
        )
        raise ValueError(
            f"Ambiguous location {value!r}. Use one of: {alternatives}"
        )
    return matches[0]


class Observer:
    """
    Observation context shared by Wenu components.

    An observer can be created from either:

    - a named location, such as ``"La Ligua"``; or
    - explicit latitude, longitude, and elevation.

    A named location may receive explicit elevation and timezone overrides;
    its registered latitude, longitude, and display name remain unchanged.

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
        self._ephemeris_finalizer = weakref.finalize(
            self,
            self.ephemeris.close,
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

    def close(self) -> None:
        """Close the loaded ephemeris resource, if it is still open."""
        self._ephemeris_finalizer()

    @classmethod
    def resolve_scientific_identity(
        cls,
        *,
        location=None,
        time="now",
        lat_deg=None,
        lon_deg=None,
        elevation_m=None,
        timezone_name=None,
    ):
        """Normalize observer inputs without loading an ephemeris."""
        latitude, longitude, elevation, timezone_name, _ = (
            cls._resolve_location(
                location=location,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                elevation_m=elevation_m,
                timezone_name=timezone_name,
            )
        )
        instant = cls._resolve_time(time, timezone_name=timezone_name)
        return (latitude, longitude, elevation, instant)

    def __enter__(self) -> Observer:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

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
            if lat_deg is not None or lon_deg is not None:
                raise ValueError(
                    "Specify either location=... or explicit latitude and "
                    "longitude, not both."
                )

            site = _resolve_registered_location(location)
            if elevation_m is None and site["elevation_m"] is None:
                raise ValueError(
                    f"No usable height for {site['qualified_name']!r}; "
                    "provide elevation_m or --observer-height explicitly."
                )

            return (
                float(site["lat_deg"]),
                float(site["lon_deg"]),
                float(
                    site.get("elevation_m", 0.0)
                    if elevation_m is None else elevation_m
                ),
                str(
                    site["timezone"]
                    if timezone_name is None else timezone_name
                ),
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
    def observation_context(self):
        """Return the immutable coordinate-service context for this observer."""
        return observation_context(self)

    @property
    def altaz_frame(self) -> AltAz:
        return AltAz(
            obstime=self.t_astropy,
            location=self.earth_location,
        )
