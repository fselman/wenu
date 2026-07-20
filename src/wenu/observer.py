# src/wenu/observer.py

from astropy.time import Time
from skyfield.api import wgs84

from astropy.coordinates import (
    AltAz,
    BarycentricMeanEcliptic,
    EarthLocation,
    Galactic,
    ICRS,
)
from astropy import units as u
from astropy.time import Time
from skyfield.api import wgs84


class Observer:
    """
    Observation context shared by Wenu components.
    """

    def __init__(
        self,
        earth,
        t,
        lat_deg,
        lon_deg,
        elevation_m=0.0,
    ):
        self.earth = earth
        self.t = t

        self.lat_deg = float(lat_deg)
        self.lon_deg = float(lon_deg)
        self.elevation_m = float(elevation_m)

        self.location = wgs84.latlon(
            latitude_degrees=self.lat_deg,
            longitude_degrees=self.lon_deg,
            elevation_m=self.elevation_m,
        )

        self.skyfield = self.earth + self.location

    @property
    def t_astropy(self):
        return Time(
            self.t.utc_datetime(),
            scale="utc",
        )

    @property
    def earth_location(self):
        return EarthLocation.from_geodetic(
            lon=self.lon_deg * u.deg,
            lat=self.lat_deg * u.deg,
            height=self.elevation_m * u.m,
        )

    @property
    def icrs_frame(self):
        return ICRS()

    @property
    def galactic_frame(self):
        return Galactic()

    @property
    def ecliptic_frame(self):
        """
        Barycentric mean ecliptic of the observation date.
        """
        return BarycentricMeanEcliptic(
            equinox=self.t_astropy,
        )

    @property
    def altaz_frame(self):
        return AltAz(
            obstime=self.t_astropy,
            location=self.earth_location,
        )

