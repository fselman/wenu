"""Chart-owned transformations between astronomical spherical frames."""

from __future__ import annotations

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def horizontal_to_galactic(geometry, observer):
    """Transform canonical AltAz geometry to Galactic longitude/latitude."""
    source_frame = getattr(observer, "altaz_frame", None)
    target_frame = getattr(observer, "galactic_frame", None)
    if source_frame is None or target_frame is None:
        raise TypeError(
            "observer must provide altaz_frame and galactic_frame."
        )
    if isinstance(geometry, SphericalPoints):
        longitude, latitude = _transform(
            geometry.lon_deg,
            geometry.lat_deg,
            source_frame=source_frame,
            target_frame=target_frame,
        )
        return SphericalPoints(
            lon_deg=longitude,
            lat_deg=latitude,
            ids=_copy(geometry.ids),
            labels=_copy(geometry.labels),
            names=_copy(geometry.names),
            metadata=_metadata(geometry.metadata),
        )
    if isinstance(geometry, SphericalCurves):
        longitude, latitude = _transform_collections(
            geometry.lon_deg,
            geometry.lat_deg,
            source_frame=source_frame,
            target_frame=target_frame,
        )
        return SphericalCurves(
            lon_deg=longitude,
            lat_deg=latitude,
            closed=geometry.closed.copy(),
            ids=_copy(geometry.ids),
            labels=_copy(geometry.labels),
            names=_copy(geometry.names),
            metadata=_metadata(geometry.metadata),
        )
    if isinstance(geometry, SphericalPolygons):
        longitude, latitude = _transform_collections(
            geometry.lon_deg,
            geometry.lat_deg,
            source_frame=source_frame,
            target_frame=target_frame,
        )
        return SphericalPolygons(
            lon_deg=longitude,
            lat_deg=latitude,
            ids=_copy(geometry.ids),
            labels=_copy(geometry.labels),
            names=_copy(geometry.names),
            metadata=_metadata(geometry.metadata),
        )
    if isinstance(geometry, SphericalGrid):
        return SphericalGrid(
            components={
                name: horizontal_to_galactic(curves, observer)
                for name, curves in geometry.components.items()
            },
            metadata=_metadata(geometry.metadata),
        )
    raise TypeError(
        "Unsupported spherical geometry type: "
        f"{type(geometry).__name__}."
    )


def _transform(longitude, latitude, *, source_frame, target_frame):
    horizontal = SkyCoord(
        az=np.asarray(longitude, dtype=float) * u.deg,
        alt=np.asarray(latitude, dtype=float) * u.deg,
        frame=source_frame,
    )
    galactic = horizontal.transform_to(target_frame)
    return (
        np.asarray(galactic.l.to_value(u.deg), dtype=float),
        np.asarray(galactic.b.to_value(u.deg), dtype=float),
    )


def _transform_collections(
    longitudes,
    latitudes,
    *,
    source_frame,
    target_frame,
):
    lengths = tuple(len(value) for value in longitudes)
    if not lengths:
        return (), ()
    longitude, latitude = _transform(
        np.concatenate(longitudes),
        np.concatenate(latitudes),
        source_frame=source_frame,
        target_frame=target_frame,
    )
    splits = np.cumsum(lengths)[:-1]
    return tuple(np.split(longitude, splits)), tuple(np.split(latitude, splits))


def _copy(values):
    return None if values is None else values.copy()


def _metadata(metadata):
    return {
        **dict(metadata),
        "source_coordinate_system": "altaz",
        "coordinate_system": "galactic",
    }
