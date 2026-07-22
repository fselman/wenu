"""Wenu: publication-quality astronomical chart generation."""
from importlib.metadata import PackageNotFoundError, version
try:
    __version__ = version("wenu")
except PackageNotFoundError:
    # The source tree is being imported without installing the package.
    __version__ = "0+unknown"

from .observer import Observer
from .projection import StereographicProjection
from .sky import CelestialSphere
from .spherical_frame import (
    SphericalCoordinates,
    SphericalFrame,
)

__all__ = [
    "Observer",
    "StereographicProjection",
    "CelestialSphere",
    "SphericalCoordinates",
    "SphericalFrame",
]

