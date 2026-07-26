"""Observer-time equatorial, ecliptic, and Galactic grid geometry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import astropy.units as u
import numpy as np
from astropy.coordinates import (
    BarycentricTrueEcliptic,
    FK5,
    Galactic,
    ICRS,
    SkyCoord,
)
from astropy.time import Time

from wenu.coordinates import radec_to_altaz
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalCurves, SphericalGrid


class CoordinatesGrid(GeometricalObject, ABC):
    """Base geometrical layer for spherical coordinate grids."""

    layer_name = "coordinates_grid"
    coordinate_system = "spherical"

    def __init__(self, observer, *, samples: int = 721) -> None:
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
    ) -> SphericalCurves:
        latitude_deg = float(latitude_deg)
        if not -90.0 <= latitude_deg <= 90.0:
            raise ValueError(
                "latitude_deg must lie between -90 and 90 degrees."
            )
        longitude = np.linspace(
            0.0, 360.0, self.samples, endpoint=False
        )
        latitude = np.full_like(longitude, latitude_deg)
        return self._make_curves(
            longitude_deg=(longitude,),
            latitude_deg=(latitude,),
            names=(
                f"latitude_{latitude_deg:g}" if name is None else name,
            ),
            closed=(True,),
            styles=(style,),
        )

    def meridian(
        self,
        longitude_deg: float,
        *,
        name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> SphericalCurves:
        longitude_deg = float(longitude_deg) % 360.0
        latitude = np.linspace(-90.0, 90.0, self.samples)
        longitude = np.full_like(latitude, longitude_deg)
        return self._make_curves(
            longitude_deg=(longitude,),
            latitude_deg=(latitude,),
            names=(
                f"longitude_{longitude_deg:g}"
                if name is None
                else name,
            ),
            closed=(False,),
            styles=(style,),
        )

    def grid(
        self,
        *,
        longitudes=None,
        latitudes=None,
        meridian_style=None,
        parallel_style=None,
    ) -> SphericalGrid:
        components = {}
        if longitudes is not None:
            components["meridians"] = self._combine(
                [
                    self.meridian(
                        float(longitude),
                        style=meridian_style,
                    )
                    for longitude in longitudes
                ]
            )
        if latitudes is not None:
            components["parallels"] = self._combine(
                [
                    self.parallel(
                        float(latitude),
                        style=parallel_style,
                    )
                    for latitude in latitudes
                ]
            )
        return SphericalGrid(
            components=components,
            metadata=self._grid_metadata(),
        )

    def spherical_geometry(self, observer) -> SphericalGrid:
        """Return the unconfigured grid as an empty semantic collection.

        Concrete grid selections are produced by ``grid()``, ``parallel()``,
        and ``meridian()``. This method completes the SkyLayer contract while
        keeping selection explicit at the public drawing entry points.
        """
        self._resolve_observer(observer)
        return SphericalGrid(
            components={},
            metadata=self._grid_metadata(),
        )

    def _make_curves(
        self,
        *,
        longitude_deg,
        latitude_deg,
        names,
        closed,
        styles,
        observer=None,
    ) -> SphericalCurves:
        resolved_observer = self._resolve_observer(observer)
        azimuths = []
        altitudes = []
        for longitude, latitude in zip(
            longitude_deg, latitude_deg
        ):
            altitude, azimuth = self._native_to_altaz(
                np.asarray(longitude, dtype=float),
                np.asarray(latitude, dtype=float),
                observer=resolved_observer,
            )
            azimuths.append(np.asarray(azimuth, dtype=float))
            altitudes.append(np.asarray(altitude, dtype=float))
        return SphericalCurves(
            lon_deg=tuple(azimuths),
            lat_deg=tuple(altitudes),
            names=names,
            closed=closed,
            metadata={
                **self._grid_metadata(),
                "styles": tuple(
                    {} if style is None else dict(style)
                    for style in styles
                ),
            },
        )

    @staticmethod
    def _combine(collections) -> SphericalCurves:
        if not collections:
            return SphericalCurves(lon_deg=(), lat_deg=())
        lon_deg = []
        lat_deg = []
        names = []
        closed = []
        styles = []
        for collection in collections:
            lon_deg.extend(collection.lon_deg)
            lat_deg.extend(collection.lat_deg)
            names.extend(collection.names)
            closed.extend(collection.closed)
            styles.extend(collection.metadata.get("styles", ({},)))
        metadata = dict(collections[0].metadata)
        metadata["styles"] = tuple(styles)
        return SphericalCurves(
            lon_deg=tuple(lon_deg),
            lat_deg=tuple(lat_deg),
            names=names,
            closed=closed,
            metadata=metadata,
        )

    def _native_to_altaz(
        self,
        longitude_deg,
        latitude_deg,
        *,
        observer,
    ):
        ra_deg, dec_deg = self._native_to_icrs(
            longitude_deg,
            latitude_deg,
        )
        alt_deg, az_deg = radec_to_altaz(
            ra_deg,
            dec_deg,
            observer.t,
            observer.lat_deg,
            observer.lon_deg,
        )
        return np.asarray(alt_deg), np.asarray(az_deg)

    def _resolve_observer(self, observer):
        resolved = self.observer if observer is None else observer
        if resolved is None:
            raise RuntimeError(
                "An Observer is required for coordinate-grid geometry."
            )
        return resolved

    def _grid_metadata(self):
        return {
            "coordinate_system": self.coordinate_system,
            "output_coordinate_system": "altaz",
        }

    @abstractmethod
    def _native_to_icrs(self, longitude_deg, latitude_deg):
        raise NotImplementedError


# Compatibility name retained while callers migrate.
SphericalCoordinatesGrid = CoordinatesGrid


class EquatorialGrid(CoordinatesGrid):
    coordinate_system = "equatorial"

    def __init__(
        self,
        observer,
        *,
        frame: str = "fk5",
        equinox: str | Time = "of_date",
        samples: int = 721,
        ra=None,
        dec=None,
        include_equator=False,
    ):
        super().__init__(observer, samples=samples)
        self.frame = frame.lower()
        self.equinox = equinox
        self.ra = None if ra is None else tuple(ra)
        self.dec = None if dec is None else tuple(dec)
        self.include_equator = bool(include_equator)
        if self.frame not in {"icrs", "fk5"}:
            raise ValueError(
                "frame must currently be either 'icrs' or 'fk5'."
            )

    def equator(self, *, style=None):
        return super().parallel(
            0.0,
            name="celestial_equator",
            style=style,
        )

    def parallel(self, declination_deg, *, style=None):
        value = float(declination_deg)
        return super().parallel(
            value,
            name=f"declination_{value:g}",
            style=style,
        )

    def meridian(self, right_ascension_deg, *, style=None):
        value = float(right_ascension_deg) % 360.0
        return super().meridian(
            value,
            name=f"right_ascension_{value:g}",
            style=style,
        )

    def grid(
        self,
        *,
        ra=None,
        dec=None,
        meridian_style=None,
        parallel_style=None,
    ):
        return super().grid(
            longitudes=ra,
            latitudes=dec,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def spherical_geometry(self, observer) -> SphericalGrid:
        resolved = self._resolve_observer(observer)
        if resolved is not self.observer:
            return type(self)(
                resolved,
                frame=self.frame,
                equinox=self.equinox,
                samples=self.samples,
                ra=self.ra,
                dec=self.dec,
                include_equator=self.include_equator,
            ).spherical_geometry(resolved)
        geometry = self.grid(ra=self.ra, dec=self.dec)
        components = dict(geometry.components)
        if self.include_equator:
            components["reference"] = self.equator()
        return SphericalGrid(
            components=components,
            metadata=geometry.metadata,
        )

    def _native_to_icrs(self, longitude_deg, latitude_deg):
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
        return np.asarray(icrs.ra.deg), np.asarray(icrs.dec.deg)

    def _equinox_time(self):
        if isinstance(self.equinox, Time):
            return self.equinox
        if str(self.equinox).lower() == "of_date":
            return self.observer.t_astropy
        return Time(self.equinox)

    def _grid_metadata(self):
        metadata = {
            **super()._grid_metadata(),
            "frame": self.frame,
        }
        if self.frame == "fk5":
            metadata["equinox"] = str(self._equinox_time())
        return metadata


class EclipticGrid(CoordinatesGrid):
    coordinate_system = "ecliptic"

    def __init__(
        self,
        observer,
        *,
        equinox: str | Time = "of_date",
        samples: int = 721,
        longitude=None,
        latitude=None,
        include_ecliptic=False,
    ):
        super().__init__(observer, samples=samples)
        self.equinox = equinox
        self.longitude = (
            None if longitude is None else tuple(longitude)
        )
        self.latitude = (
            None if latitude is None else tuple(latitude)
        )
        self.include_ecliptic = bool(include_ecliptic)

    def ecliptic(self, *, style=None):
        return super().parallel(
            0.0,
            name="ecliptic",
            style=style,
        )

    def parallel(
        self,
        ecliptic_latitude_deg=None,
        *,
        latitude_deg=None,
        style=None,
    ):
        value = (
            ecliptic_latitude_deg
            if latitude_deg is None
            else latitude_deg
        )
        value = float(value)
        return super().parallel(
            value,
            name=f"ecliptic_latitude_{value:g}",
            style=style,
        )

    def meridian(
        self,
        ecliptic_longitude_deg=None,
        *,
        longitude_deg=None,
        style=None,
    ):
        value = (
            ecliptic_longitude_deg
            if longitude_deg is None
            else longitude_deg
        )
        value = float(value) % 360.0
        return super().meridian(
            value,
            name=f"ecliptic_longitude_{value:g}",
            style=style,
        )

    def grid(
        self,
        *,
        longitude=None,
        latitude=None,
        meridian_style=None,
        parallel_style=None,
    ):
        return super().grid(
            longitudes=longitude,
            latitudes=latitude,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def spherical_geometry(self, observer) -> SphericalGrid:
        resolved = self._resolve_observer(observer)
        if resolved is not self.observer:
            return type(self)(
                resolved,
                equinox=self.equinox,
                samples=self.samples,
                longitude=self.longitude,
                latitude=self.latitude,
                include_ecliptic=self.include_ecliptic,
            ).spherical_geometry(resolved)
        geometry = self.grid(
            longitude=self.longitude,
            latitude=self.latitude,
        )
        components = dict(geometry.components)
        if self.include_ecliptic:
            components["reference"] = self.ecliptic()
        return SphericalGrid(
            components=components,
            metadata=geometry.metadata,
        )

    def _native_to_icrs(self, longitude_deg, latitude_deg):
        coordinates = SkyCoord(
            lon=longitude_deg * u.deg,
            lat=latitude_deg * u.deg,
            frame=BarycentricTrueEcliptic(
                equinox=self._equinox_time()
            ),
        )
        icrs = coordinates.icrs
        return np.asarray(icrs.ra.deg), np.asarray(icrs.dec.deg)

    def _equinox_time(self):
        if isinstance(self.equinox, Time):
            return self.equinox
        if str(self.equinox).lower() == "of_date":
            return self.observer.t_astropy
        return Time(self.equinox)

    def _grid_metadata(self):
        return {
            **super()._grid_metadata(),
            "equinox": str(self._equinox_time()),
        }


class GalacticGrid(CoordinatesGrid):
    coordinate_system = "galactic"

    def __init__(
        self,
        observer,
        *,
        samples=721,
        longitude=None,
        latitude=None,
        include_plane=False,
    ):
        super().__init__(observer, samples=samples)
        self.longitude = (
            None if longitude is None else tuple(longitude)
        )
        self.latitude = (
            None if latitude is None else tuple(latitude)
        )
        self.include_plane = bool(include_plane)

    def spherical_geometry(self, observer) -> SphericalGrid:
        resolved = self._resolve_observer(observer)
        if resolved is not self.observer:
            return type(self)(
                resolved,
                samples=self.samples,
                longitude=self.longitude,
                latitude=self.latitude,
                include_plane=self.include_plane,
            ).spherical_geometry(resolved)
        geometry = self.grid(
            longitude=self.longitude,
            latitude=self.latitude,
        )
        components = dict(geometry.components)
        if self.include_plane:
            components["reference"] = self.galactic_plane()
        return SphericalGrid(
            components=components,
            metadata=geometry.metadata,
        )

    def galactic_plane(self, *, style=None):
        return super().parallel(
            0.0,
            name="galactic_plane",
            style=style,
        )

    def parallel(
        self,
        galactic_latitude_deg=None,
        *,
        latitude_deg=None,
        style=None,
    ):
        value = (
            galactic_latitude_deg
            if latitude_deg is None
            else latitude_deg
        )
        value = float(value)
        return super().parallel(
            value,
            name=f"galactic_latitude_{value:g}",
            style=style,
        )

    def meridian(
        self,
        galactic_longitude_deg=None,
        *,
        longitude_deg=None,
        style=None,
    ):
        value = (
            galactic_longitude_deg
            if longitude_deg is None
            else longitude_deg
        )
        value = float(value) % 360.0
        return super().meridian(
            value,
            name=f"galactic_longitude_{value:g}",
            style=style,
        )

    def grid(
        self,
        *,
        longitude=None,
        latitude=None,
        meridian_style=None,
        parallel_style=None,
    ):
        return super().grid(
            longitudes=longitude,
            latitudes=latitude,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def _native_to_icrs(self, longitude_deg, latitude_deg):
        coordinates = SkyCoord(
            l=longitude_deg * u.deg,
            b=latitude_deg * u.deg,
            frame=Galactic(),
        )
        icrs = coordinates.icrs
        return np.asarray(icrs.ra.deg), np.asarray(icrs.dec.deg)
