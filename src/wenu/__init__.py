"""Wenu: publication-quality astronomical chart generation."""

from importlib.metadata import PackageNotFoundError, version
try:
    __version__ = version("wenu")
except PackageNotFoundError:
    # The source tree is being imported without installing the package.
    __version__ = "0+unknown"

from .sky.rendering_results import ChartRenderingResult, LayerRenderingResult
from .observer import Observer
from .objects.nonstellar import NonStellar
from .objects.galaxies import Galaxies
from .objects.globular_clusters import GlobularClusters
from .objects.open_clusters import OpenClusters
from .objects.supernova_remnants import SupernovaRemnants
from .objects.planetary_nebulae import PlanetaryNebulae
from .sky.milky_way import MilkyWayIsophotes
from .sky.magellanic_clouds import MagellanicCloudIsophotes
from .charts.composition import ChartComposition, compose_chart
from .charts.context import BoundaryKind, ChartContext
from .charts.detail import (
    AdaptiveDetailPolicy,
    DetailOverrides,
    DetailPolicy,
    FieldDetailLevel,
    FixedDetailPolicy,
    ResolvedDetail,
)
from .charts.modes import (
    ChartMode,
    PresentationMode,
    PrintMode,
    ResolvedMode,
)
from .charts.binocular import BinocularChart
from .charts.boundaries import (
    CircularLabelAnchor,
    RectangularLabelAnchor,
)
from .charts.circumpolar import CircumpolarChart
from .charts.detail_application import (
    DetailApplication,
    apply_resolved_detail,
    composition_layer_options,
    merge_layer_options,
)
from .charts.full_sky import FullSkyChart
from .charts.regional import ExportOptions, RegionalChart
from .charts.styles import PublicationStyle
from .charts.style_components import ChartStyle
from .charts.presets import AtlasChartStyle
from .charts.legend import draw_chart_legend
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
    "BoundaryKind",
    "ChartComposition",
    "ChartContext",
    "ChartMode",
    "AdaptiveDetailPolicy",
    "DetailApplication",
    "apply_resolved_detail",
    "composition_layer_options",
    "merge_layer_options",
    "DetailOverrides",
    "DetailPolicy",
    "FieldDetailLevel",
    "FixedDetailPolicy",
    "PresentationMode",
    "PrintMode",
    "ResolvedDetail",
    "ResolvedMode",
    "compose_chart",
    "ChartRenderingResult",
    "LayerRenderingResult",
    "Observer",
    "NonStellar",
    "PlanetaryNebulae",
    "Galaxies",
    "GlobularClusters",
    "OpenClusters",
    "SupernovaRemnants",
    "MilkyWayIsophotes",
    "MagellanicCloudIsophotes",
    "ExportOptions",
    "BinocularChart",
    "CircularLabelAnchor",
    "CircumpolarChart",
    "RectangularLabelAnchor",
    "FullSkyChart",
    "RegionalChart",
    "PublicationStyle",
    "ChartStyle",
    "AtlasChartStyle",
    "draw_chart_legend",
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
