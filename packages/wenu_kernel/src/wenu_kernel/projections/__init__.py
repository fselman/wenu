"""Coordinate-neutral map projections."""

from .mollweide import MollweideProjection
from .polar_azimuthal_equidistant import (
    PolarAzimuthalEquidistantProjection,
)
from .stereographic import StereographicProjection

__all__ = [
    "MollweideProjection",
    "PolarAzimuthalEquidistantProjection",
    "StereographicProjection",
]
