"""Compatibility wrappers for chart-requested astronomical transforms."""

from __future__ import annotations

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import observation_context, observer_celestial_spec
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


def horizontal_to_galactic(geometry, observer):
    """Transform canonical AltAz geometry to Galactic longitude/latitude."""
    return _horizontal_to_frame(
        geometry,
        observer,
        target_attribute="galactic_frame",
        coordinate_system="galactic",
    )


def horizontal_to_equatorial(geometry, observer):
    """Transform canonical AltAz geometry to ICRS right ascension/declination."""
    return _horizontal_to_frame(
        geometry,
        observer,
        target_attribute="icrs_frame",
        coordinate_system="equatorial",
    )


def _horizontal_to_frame(
    geometry,
    observer,
    *,
    target_attribute,
    coordinate_system,
):
    source_frame = getattr(observer, "altaz_frame", None)
    target_frame = getattr(observer, target_attribute, None)
    if source_frame is None or target_frame is None:
        raise TypeError(
            f"observer must provide altaz_frame and {target_attribute}."
        )
    if not isinstance(
        geometry,
        (SphericalPoints, SphericalCurves, SphericalPolygons, SphericalGrid),
    ):
        raise TypeError(
            "Unsupported spherical geometry type: "
            f"{type(geometry).__name__}."
        )

    target_spec = observer_celestial_spec(
        observer,
        "icrs" if coordinate_system == "equatorial" else coordinate_system,
        model=f"Astropy AltAz to {coordinate_system}",
    )
    transformed = CoordinateService().transform(
        geometry,
        target_spec,
        observation=observation_context(observer),
    )
    _annotate(transformed, coordinate_system)
    return transformed


def _annotate(geometry, coordinate_system):
    geometry.metadata = {
        **dict(geometry.metadata),
        "source_coordinate_system": "altaz",
        "coordinate_system": coordinate_system,
    }
    if isinstance(geometry, SphericalGrid):
        for component in geometry.components.values():
            _annotate(component, coordinate_system)
