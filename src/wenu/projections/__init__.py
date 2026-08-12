"""Coordinate-neutral map projections."""

from .mollweide import MollweideProjection
from .stereographic import StereographicProjection

__all__ = [
    "MollweideProjection",
    "StereographicProjection",
]
