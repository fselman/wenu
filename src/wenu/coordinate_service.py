"""Central astronomical transformations for typed spherical geometry."""

from __future__ import annotations

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricMeanEcliptic,
    BarycentricTrueEcliptic,
    EarthLocation,
    FK5,
    Galactic,
    ICRS,
    SkyCoord,
)
from astropy.time import Time

from wenu.coordinates import CoordinateSpec, ObservationContext
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGeometry,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


class CoordinateService:
    """Transform typed astronomical geometry through Astropy.

    Position generation is deliberately outside this boundary.  The service
    changes only the coordinate representation of geometry whose source
    identity is already explicit.
    """

    def transform(
        self,
        geometry: SphericalGeometry,
        target_spec: CoordinateSpec,
        observation: ObservationContext | None = None,
    ) -> SphericalGeometry:
        """Return *geometry* in *target_spec*, preserving its concrete kind."""
        if not isinstance(target_spec, CoordinateSpec):
            raise TypeError("target_spec must be a CoordinateSpec instance.")
        if not isinstance(
            geometry,
            (SphericalPoints, SphericalCurves, SphericalPolygons, SphericalGrid),
        ):
            raise TypeError(
                "geometry must be a supported SphericalGeometry instance."
            )

        self._validate_spec(geometry.coordinate_spec)
        self._validate_spec(target_spec)
        source_frame = self._frame(geometry.coordinate_spec, observation)
        target_frame = self._frame(target_spec, observation)

        if isinstance(geometry, SphericalPoints):
            lon_deg, lat_deg = self._coordinates(
                geometry.lon_deg,
                geometry.lat_deg,
                source_frame,
                target_frame,
            )
            return SphericalPoints(
                lon_deg=lon_deg,
                lat_deg=lat_deg,
                coordinate_spec=target_spec,
                ids=_copy(geometry.ids),
                labels=_copy(geometry.labels),
                names=_copy(geometry.names),
                metadata=dict(geometry.metadata),
            )

        if isinstance(geometry, SphericalCurves):
            lon_deg, lat_deg = self._collections(
                geometry.lon_deg,
                geometry.lat_deg,
                source_frame,
                target_frame,
            )
            return SphericalCurves(
                lon_deg=lon_deg,
                lat_deg=lat_deg,
                coordinate_spec=target_spec,
                closed=geometry.closed.copy(),
                ids=_copy(geometry.ids),
                labels=_copy(geometry.labels),
                names=_copy(geometry.names),
                metadata=dict(geometry.metadata),
            )

        if isinstance(geometry, SphericalPolygons):
            lon_deg, lat_deg = self._collections(
                geometry.lon_deg,
                geometry.lat_deg,
                source_frame,
                target_frame,
            )
            return SphericalPolygons(
                lon_deg=lon_deg,
                lat_deg=lat_deg,
                coordinate_spec=target_spec,
                ids=_copy(geometry.ids),
                labels=_copy(geometry.labels),
                names=_copy(geometry.names),
                metadata=dict(geometry.metadata),
            )

        components = {
            name: self.transform(curves, target_spec, observation)
            for name, curves in geometry.components.items()
        }
        return SphericalGrid(
            components=components,
            coordinate_spec=target_spec,
            metadata=dict(geometry.metadata),
        )

    @staticmethod
    def _validate_spec(spec: CoordinateSpec) -> None:
        if spec.longitude_unit != "deg" or spec.latitude_unit != "deg":
            raise ValueError(
                "CoordinateService currently requires degree coordinates."
            )
        if spec.representation != "spherical":
            raise ValueError(
                "CoordinateService currently requires spherical representation."
            )

    @staticmethod
    def _frame(
        spec: CoordinateSpec,
        observation: ObservationContext | None,
    ):
        frame = spec.frame.replace("_", "-")
        if frame == "icrs":
            return ICRS()
        if frame == "galactic":
            return Galactic()
        if frame == "fk5":
            return FK5(equinox=Time(spec.equinox or "J2000.0"))
        if frame in {
            "true-ecliptic",
            "barycentric-true-ecliptic",
            "barycentrictrueecliptic",
        }:
            equinox = spec.equinox or spec.instant
            if equinox is None and observation is not None:
                equinox = observation.instant
            return BarycentricTrueEcliptic(
                equinox=Time(equinox or "J2000.0")
            )
        if frame in {
            "ecliptic",
            "barycentric-mean-ecliptic",
            "barycentricmeanecliptic",
        }:
            equinox = spec.equinox or spec.instant
            if equinox is None and observation is not None:
                equinox = observation.instant
            return BarycentricMeanEcliptic(
                equinox=Time(equinox or "J2000.0")
            )
        if frame == "altaz":
            if observation is None:
                raise ValueError(
                    "AltAz transformations require an ObservationContext."
                )
            if observation.refraction_policy != "vacuum":
                raise ValueError(
                    "Only the vacuum refraction policy is supported."
                )
            if observation.earth_orientation_policy != "astropy":
                raise ValueError(
                    "Only the Astropy Earth-orientation policy is supported."
                )
            obstime = Time(
                observation.instant,
                scale=observation.time_scale,
            )
            location = EarthLocation.from_geodetic(
                lon=observation.longitude_deg * u.deg,
                lat=observation.latitude_deg * u.deg,
                height=observation.elevation_m * u.m,
            )
            return AltAz(
                obstime=obstime,
                location=location,
                pressure=0.0 * u.hPa,
            )
        raise ValueError(f"Unsupported astronomical frame: {spec.frame!r}.")

    @staticmethod
    def _coordinates(longitude, latitude, source_frame, target_frame):
        longitude = np.asarray(longitude, dtype=float)
        latitude = np.asarray(latitude, dtype=float)
        if longitude.size == 0:
            return longitude.copy(), latitude.copy()
        source = SkyCoord(
            longitude * u.deg,
            latitude * u.deg,
            frame=source_frame,
        )
        transformed = source.transform_to(target_frame).spherical
        return (
            np.asarray(transformed.lon.to_value(u.deg), dtype=float),
            np.asarray(transformed.lat.to_value(u.deg), dtype=float),
        )

    @classmethod
    def _collections(
        cls,
        longitudes,
        latitudes,
        source_frame,
        target_frame,
    ):
        lengths = tuple(len(values) for values in longitudes)
        if not lengths:
            return (), ()
        longitude, latitude = cls._coordinates(
            np.concatenate(longitudes),
            np.concatenate(latitudes),
            source_frame,
            target_frame,
        )
        splits = np.cumsum(lengths)[:-1]
        return (
            tuple(np.split(longitude, splits)),
            tuple(np.split(latitude, splits)),
        )


def _copy(values):
    return None if values is None else values.copy()
