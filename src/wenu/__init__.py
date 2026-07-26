"""Wenu: publication-quality astronomical chart generation."""

from importlib.metadata import PackageNotFoundError, version
try:
    __version__ = version("wenu")
except PackageNotFoundError:
    # The source tree is being imported without installing the package.
    __version__ = "0+unknown"

from .sky.rendering_results import ChartRenderingResult, LayerRenderingResult
from .observer import Observer
from .charts.full_sky import FullSkyChart
from .charts.regional import ExportOptions, RegionalChart
from .charts.styles import PublicationStyle
from .rendering import MatplotlibRenderer
from .projections import StereographicProjection
from .sky import CelestialSphere
from .geometry.frame import (
    SphericalCoordinates,
    SphericalFrame,
)
from .geometry.viewport import Viewport

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedPoint,
    ProjectedPolygon,
)

__all__ = [
    "ChartRenderingResult",
    "LayerRenderingResult",
    "Observer",
    "ExportOptions",
    "FullSkyChart",
    "RegionalChart",
    "PublicationStyle",
    "MatplotlibRenderer",
    "StereographicProjection",
    "CelestialSphere",
    "SphericalCoordinates",
    "SphericalFrame",
    "Viewport",
    "ProjectedCurve",
    "ProjectedPoint",
    "ProjectedPolygon",
]

