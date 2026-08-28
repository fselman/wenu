"""Observer-time AltAz, equatorial, ecliptic, and Galactic grid geometry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from astropy.time import Time

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    PositionStatus,
    observation_context,
    observer_altaz_spec,
)
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
        latitude_min_deg: float = -90.0,
        latitude_max_deg: float = 90.0,
        name: str | None = None,
        style: dict[str, Any] | None = None,
    ) -> SphericalCurves:
        longitude_deg = float(longitude_deg) % 360.0
        latitude_min_deg = float(latitude_min_deg)
        latitude_max_deg = float(latitude_max_deg)
        if not (
            -90.0 <= latitude_min_deg < latitude_max_deg <= 90.0
        ):
            raise ValueError(
                "Meridian latitude limits must satisfy "
                "-90 <= minimum < maximum <= 90 degrees."
            )
        latitude = np.linspace(
            latitude_min_deg,
            latitude_max_deg,
            self.samples,
        )
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
            coordinate_spec=self._coordinate_spec(),
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
            coordinate_spec=self._coordinate_spec(),
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
        source_spec = self._native_coordinate_spec()
        target_spec = observer_altaz_spec(
            resolved_observer,
            provider="wenu coordinate grid",
            model=f"{self.coordinate_system} to AltAz",
        )
        native = SphericalCurves(
            lon_deg=tuple(
                np.asarray(value, dtype=float) for value in longitude_deg
            ),
            lat_deg=tuple(
                np.asarray(value, dtype=float) for value in latitude_deg
            ),
            coordinate_spec=source_spec,
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
        if source_spec == target_spec:
            return native
        return CoordinateService().transform(
            native,
            target_spec,
            observation=observation_context(resolved_observer),
        )

    def _combine(self, collections) -> SphericalCurves:
        if not collections:
            return SphericalCurves(
                lon_deg=(),
                lat_deg=(),
                coordinate_spec=self._coordinate_spec(),
            )
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
            coordinate_spec=collections[0].coordinate_spec,
            names=names,
            closed=closed,
            metadata=metadata,
        )

    def _coordinate_spec(self):
        return observer_altaz_spec(
            self._resolve_observer(None),
            provider="wenu coordinate grid",
            model=f"{self.coordinate_system} to AltAz",
        )

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
    def _native_coordinate_spec(self) -> CoordinateSpec:
        raise NotImplementedError


class AltAzGrid(CoordinatesGrid):
    """Observer-local horizontal coordinate grid.

    Azimuth meridians and altitude parallels are already expressed in the
    canonical spherical AltAz geometry used downstream, so their construction
    deliberately avoids a horizontal-to-ICRS-to-horizontal round trip.
    """

    coordinate_system = "altaz"

    def __init__(
        self,
        observer,
        *,
        samples=721,
        azimuth=None,
        altitude=None,
        include_horizon=False,
    ):
        super().__init__(observer, samples=samples)
        self.azimuth = None if azimuth is None else tuple(azimuth)
        self.altitude = None if altitude is None else tuple(altitude)
        self.include_horizon = bool(include_horizon)

    def horizon(self, *, style=None):
        return self.parallel(0.0, style=style, name="horizon")

    def parallel(self, altitude_deg, *, style=None, name=None):
        value = float(altitude_deg)
        return super().parallel(
            value,
            name=(f"altitude_{value:g}" if name is None else name),
            style=style,
        )

    def meridian(self, azimuth_deg, *, style=None):
        value = float(azimuth_deg) % 360.0
        return super().meridian(
            value,
            name=f"azimuth_{value:g}",
            style=style,
        )

    def grid(
        self,
        *,
        azimuth=None,
        altitude=None,
        meridian_style=None,
        parallel_style=None,
    ):
        return super().grid(
            longitudes=azimuth,
            latitudes=altitude,
            meridian_style=meridian_style,
            parallel_style=parallel_style,
        )

    def spherical_geometry(self, observer) -> SphericalGrid:
        resolved = self._resolve_observer(observer)
        if resolved is not self.observer:
            return type(self)(
                resolved,
                samples=self.samples,
                azimuth=self.azimuth,
                altitude=self.altitude,
                include_horizon=self.include_horizon,
            ).spherical_geometry(resolved)
        geometry = self.grid(
            azimuth=self.azimuth,
            altitude=self.altitude,
        )
        components = dict(geometry.components)
        if self.include_horizon:
            components["reference"] = self.horizon()
        return SphericalGrid(
            components=components,
            coordinate_spec=geometry.coordinate_spec,
            metadata=geometry.metadata,
        )

    def _native_coordinate_spec(self):
        return self._coordinate_spec()


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
        meridian_dec_min=-90.0,
        meridian_dec_max=90.0,
    ):
        super().__init__(observer, samples=samples)
        self.frame = frame.lower()
        self.equinox = equinox
        self.ra = None if ra is None else tuple(ra)
        self.dec = None if dec is None else tuple(dec)
        self.include_equator = bool(include_equator)
        self.meridian_dec_min = float(meridian_dec_min)
        self.meridian_dec_max = float(meridian_dec_max)
        if not (
            -90.0
            <= self.meridian_dec_min
            < self.meridian_dec_max
            <= 90.0
        ):
            raise ValueError(
                "meridian_dec_min and meridian_dec_max must satisfy "
                "-90 <= minimum < maximum <= 90 degrees."
            )
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

    def meridian(
        self,
        right_ascension_deg,
        *,
        dec_min=None,
        dec_max=None,
        style=None,
    ):
        value = float(right_ascension_deg) % 360.0
        return super().meridian(
            value,
            latitude_min_deg=(
                self.meridian_dec_min
                if dec_min is None
                else float(dec_min)
            ),
            latitude_max_deg=(
                self.meridian_dec_max
                if dec_max is None
                else float(dec_max)
            ),
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
        components = {}
        if ra is not None:
            components["meridians"] = self._combine(
                [
                    self.meridian(
                        value,
                        style=meridian_style,
                    )
                    for value in ra
                ]
            )
        if dec is not None:
            components["parallels"] = self._combine(
                [
                    self.parallel(
                        value,
                        style=parallel_style,
                    )
                    for value in dec
                ]
            )
        return SphericalGrid(
            components=components,
            coordinate_spec=self._coordinate_spec(),
            metadata=self._grid_metadata(),
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
                meridian_dec_min=self.meridian_dec_min,
                meridian_dec_max=self.meridian_dec_max,
            ).spherical_geometry(resolved)
        geometry = self.grid(ra=self.ra, dec=self.dec)
        components = dict(geometry.components)
        if self.include_equator:
            components["reference"] = self.equator()
        return SphericalGrid(
            components=components,
            coordinate_spec=geometry.coordinate_spec,
            metadata=geometry.metadata,
        )

    def _native_coordinate_spec(self):
        if self.frame == "icrs":
            return CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                provider="wenu equatorial grid",
            )
        return CoordinateSpec(
            frame="fk5",
            origin="solar-system-barycenter",
            position_status=PositionStatus.ASTROMETRIC,
            equinox=str(self._equinox_time()),
            provider="wenu equatorial grid",
        )

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
            coordinate_spec=geometry.coordinate_spec,
            metadata=geometry.metadata,
        )

    def _native_coordinate_spec(self):
        return CoordinateSpec(
            frame="barycentric-true-ecliptic",
            origin="solar-system-barycenter",
            position_status=PositionStatus.ASTROMETRIC,
            equinox=str(self._equinox_time()),
            provider="wenu ecliptic grid",
        )

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
            coordinate_spec=geometry.coordinate_spec,
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

    def _native_coordinate_spec(self):
        return CoordinateSpec(
            frame="galactic",
            origin="galactic-center",
            position_status=PositionStatus.ASTROMETRIC,
            provider="wenu galactic grid",
        )