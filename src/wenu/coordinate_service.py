"""Central astronomical transformations for typed spherical geometry."""

from __future__ import annotations

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricMeanEcliptic,
    BarycentricTrueEcliptic,
    EarthLocation,
    FK4,
    FK5,
    GCRS,
    Galactic,
    ICRS,
    SkyCoord,
)
from astropy.time import Time

from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    observation_context,
    observer_celestial_spec,
)
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

    def orient_geometry(self, geometry, orientation, *, inverse=False):
        """Re-express geometry on admitted mean axes; never propagate a source.

        The inverse solves the actual near-orthogonal matrix, rather than
        assuming its transpose is exact. NaN slots and ragged topology survive.
        Source specifications remain separately available in copied metadata.
        """
        from dataclasses import replace
        from wenu.astrometric_coordinates import LongTermFrame
        from wenu.coordinates import PositionStatus
        if type(orientation) is not LongTermFrame or type(inverse) is not bool:
            raise TypeError('An admitted LongTermFrame and boolean inverse are required.')
        if not isinstance(geometry, (SphericalPoints, SphericalCurves, SphericalPolygons, SphericalGrid)):
            raise TypeError('Unsupported spherical geometry.')
        source = geometry.coordinate_spec
        self._validate_spec(source)
        identity = orientation.model.configuration_digest
        expected = orientation.axes if inverse else 'icrs'
        if (source.frame != expected or source.origin != 'solar-system-barycenter'
                or source.position_status != PositionStatus.ASTROMETRIC
                or source.corrections or (inverse and identity not in source.provenance)):
            raise ValueError('Mean-axis geometry requires matching barycentric astrometric axes.')
        target = replace(source, frame='icrs' if inverse else orientation.axes,
            equinox=None if inverse else f'JD({orientation.equinox.jd1},{orientation.equinox.jd2.hex()}) TT',
            provenance=source.provenance + (identity,))
        metadata = dict(geometry.metadata)
        metadata['source_coordinate_spec'] = source
        metadata['view_frame_sha256'] = identity
        if isinstance(geometry, SphericalGrid):
            return replace(geometry, components={name:self.orient_geometry(curve, orientation, inverse=inverse)
                for name,curve in geometry.components.items()}, coordinate_spec=target, metadata=metadata)
        matrix = np.asarray(orientation.matrix)
        def coordinates(lon, lat):
            lon,lat=np.asarray(lon,dtype=float),np.asarray(lat,dtype=float)
            if lon.shape != lat.shape or np.any(np.isinf(lon)) or np.any(np.isinf(lat)):
                raise ValueError('Malformed spherical direction arrays.')
            valid=np.isfinite(lon) & np.isfinite(lat)
            if np.any(np.abs(lat[valid])>90):
                raise ValueError('Latitude outside the sphere.')
            longitude,latitude=np.full(lon.shape,np.nan),np.full(lat.shape,np.nan)
            a,b=np.deg2rad(lon[valid]),np.deg2rad(lat[valid])
            xyz=np.array((np.cos(b)*np.cos(a),np.cos(b)*np.sin(a),np.sin(b)))
            xyz=np.linalg.solve(matrix,xyz) if inverse else matrix @ xyz
            norms=np.linalg.norm(xyz,axis=0)
            if np.any(~np.isfinite(norms)) or np.any(norms==0):
                raise ValueError('Invalid mean-axis direction.')
            xyz=xyz/norms
            longitude[valid]=np.rad2deg(np.arctan2(xyz[1],xyz[0]))%360
            latitude[valid]=np.rad2deg(np.arctan2(xyz[2],np.hypot(xyz[0],xyz[1])))
            return longitude,latitude
        if isinstance(geometry,SphericalPoints):
            lon,lat=coordinates(geometry.lon_deg,geometry.lat_deg)
        else:
            pairs=[coordinates(a,b) for a,b in zip(geometry.lon_deg,geometry.lat_deg)]
            lon,lat=tuple(a for a,b in pairs),tuple(b for a,b in pairs)
        fields=dict(lon_deg=lon,lat_deg=lat,coordinate_spec=target,metadata=metadata,
            ids=_copy(geometry.ids),names=_copy(geometry.names),labels=_copy(geometry.labels))
        if isinstance(geometry,SphericalCurves):
            fields['closed']=geometry.closed.copy()
        return replace(geometry,**fields)

    def transform_observer_geometry(
        self,
        geometry: SphericalGeometry,
        observer,
        target_frame: str,
        *,
        coordinate_system: str | None = None,
    ) -> SphericalGeometry:
        """Transform observer-local geometry through the governed service."""
        frame = str(target_frame).strip().lower()
        system = (
            "equatorial" if frame == "icrs" else frame
            if coordinate_system is None else str(coordinate_system)
        )
        transformed = self.transform(
            geometry,
            observer_celestial_spec(
                observer,
                frame,
                model=f"Astropy AltAz to {system}",
            ),
            observation_context(observer),
        )
        _annotate_coordinate_system(transformed, system)
        return transformed

    def transform_skycoord(
        self,
        coordinate: SkyCoord,
        target_spec: CoordinateSpec,
        observation: ObservationContext | None = None,
    ) -> SphericalPoints:
        """Adapt an external Astropy coordinate at the service boundary."""
        if not isinstance(coordinate, SkyCoord):
            raise TypeError("coordinate must be an Astropy SkyCoord.")
        self._validate_spec(target_spec)
        target_frame = self._frame(target_spec, observation)
        transformed = coordinate.transform_to(target_frame).spherical
        return SphericalPoints(
            lon_deg=np.atleast_1d(
                np.asarray(transformed.lon.to_value(u.deg), dtype=float)
            ),
            lat_deg=np.atleast_1d(
                np.asarray(transformed.lat.to_value(u.deg), dtype=float)
            ),
            coordinate_spec=target_spec,
            metadata={"source": "external Astropy SkyCoord"},
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
        if frame == "gcrs-axes":
            # Geometric direction components in the fixed GCRS/ICRS axis
            # orientation; no geocentric state or collection instant implied.
            return ICRS()
        if frame == "icrs":
            return ICRS()
        if frame == "galactic":
            return Galactic()
        if frame == "gcrs":
            if spec.instant is None:
                raise ValueError("GCRS coordinates require an instant.")
            return GCRS(
                obstime=Time(spec.instant, scale=spec.time_scale)
            )
        if frame == "fk4":
            return FK4(equinox=Time(spec.equinox or "B1950.0"))
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


def _annotate_coordinate_system(geometry, coordinate_system):
    geometry.metadata = {
        **dict(geometry.metadata),
        "source_coordinate_system": "altaz",
        "coordinate_system": coordinate_system,
    }
    if isinstance(geometry, SphericalGrid):
        for component in geometry.components.values():
            _annotate_coordinate_system(component, coordinate_system)


def mean_reference_frame(orientation, axes):
    """Paired mean reference at the same explicit TT event/domain/policy."""
    from wenu.astrometric_coordinates import LongTermFrame, LONG_TERM_FRAME_POLICY
    if type(orientation) is not LongTermFrame:
        raise TypeError('Expected admitted LongTermFrame.')
    return orientation if orientation.axes == axes else LongTermFrame(
        equinox=orientation.equinox, validity=orientation.validity,
        axes=axes, model_policy=LONG_TERM_FRAME_POLICY)


def mean_frame_spec(orientation):
    """Reference coordinates used to construct dated grids, never source states."""
    from wenu.coordinates import PositionStatus
    return CoordinateSpec(frame=orientation.axes, origin='solar-system-barycenter',
        position_status=PositionStatus.ASTROMETRIC,
        equinox=f'JD({orientation.equinox.jd1},{orientation.equinox.jd2.hex()}) TT',
        provider='wenu mean reference geometry',
        provenance=(orientation.model.configuration_digest,))
