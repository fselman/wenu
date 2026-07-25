"""Wenu: publication-quality astronomical chart generation."""

from importlib.metadata import PackageNotFoundError, version
try:
    __version__ = version("wenu")
except PackageNotFoundError:
    # The source tree is being imported without installing the package.
    __version__ = "0+unknown"

from .chart import ChartRenderingResult, LayerRenderingResult
from .observer import Observer
from .projection import StereographicProjection
from .sky import CelestialSphere
from .spherical_frame import (
    SphericalCoordinates,
    SphericalFrame,
)
from .viewport import Viewport

from wenu.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)

__all__ = [
    "ChartRenderingResult",
    "LayerRenderingResult",
    "Observer",
    "StereographicProjection",
    "CelestialSphere",
    "SphericalCoordinates",
    "SphericalFrame",
    "Viewport",
    "ProjectedCurve",
    "ProjectedPoint",
    "ProjectedPolygon",
]

