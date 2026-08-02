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
from .charts.legend_plan import LegendOptions, ResolvedLegendOptions
from .charts.furniture import (
    ChartFurnitureOptions,
    FooterOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    ResolvedChartFurnitureOptions,
)
from .charts.reference_furniture import (
    BoundaryAwareReferenceAnchor,
    CelestialReferenceRendering,
    build_celestial_reference_sky,
    draw_celestial_reference_furniture,
)
from .charts.chart_legend_workflow import draw_resolved_chart_legends
from .charts.context import BoundaryKind, ChartContext
from .charts.detail import (
    CartoonDetailPolicy,
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
    CircularGridLabelAnchor,
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
from .charts.export_workflow import ChartExportResult
from .charts.styles import PublicationStyle
from .charts.style_components import ChartStyle
from .charts.presets import AtlasChartStyle, CartoonChartStyle
from .charts.atlas_modes import (
    AtlasPresentationPalette,
    ATLAS_PRESENTATION_PALETTE,
    atlas_chart_style,
)
from .charts.cartoon import CartoonChartPreset
from .charts.label_placement import (
    LABEL_POSITION_VECTORS,
    resolve_constellation_label_offsets,
)
from .charts.legend import draw_chart_legend
from .charts.legend_metadata import (
    LegendMetadata,
    active_coordinate_grid,
    resolve_legend_metadata,
    observer_context_lines,
)
from .charts.legend_symbols import (
    LegendSymbolDescriptor,
    legend_symbol_descriptors,
)
from .charts.magnitude_legend import (
    StellarMagnitudeEntry,
    StellarMagnitudeScale,
    VisibleStarStatistics,
    integer_magnitude_range,
    stellar_magnitude_scale,
    visible_star_mask,
    visible_star_statistics,
)
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
    "resolve_constellation_label_offsets",
    "LABEL_POSITION_VECTORS",
    "BoundaryKind",
    "ChartComposition",
    "LegendOptions",
    "ResolvedLegendOptions",
    "ChartFurnitureOptions",
    "ResolvedChartFurnitureOptions",
    "ReferencePlaneAnnotation",
    "ReferenceAnnotations",
    "PoleAnnotations",
    "FooterOptions",
    "BoundaryAwareReferenceAnchor",
    "CelestialReferenceRendering",
    "build_celestial_reference_sky",
    "draw_celestial_reference_furniture",
    "draw_resolved_chart_legends",
    "ChartContext",
    "CartoonDetailPolicy",
    "CartoonChartStyle",
    "CartoonChartPreset",
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
    "ChartExportResult",
    "BinocularChart",
    "CircularLabelAnchor",
    "CircularGridLabelAnchor",
    "CircumpolarChart",
    "RectangularLabelAnchor",
    "FullSkyChart",
    "RegionalChart",
    "PublicationStyle",
    "ChartStyle",
    "AtlasChartStyle",
    "AtlasPresentationPalette",
    "ATLAS_PRESENTATION_PALETTE",
    "atlas_chart_style",
    "draw_chart_legend",
    "LegendMetadata",
    "active_coordinate_grid",
    "resolve_legend_metadata",
    "observer_context_lines",
    "LegendSymbolDescriptor",
    "legend_symbol_descriptors",
    "StellarMagnitudeEntry",
    "StellarMagnitudeScale",
    "VisibleStarStatistics",
    "visible_star_mask",
    "visible_star_statistics",
    "integer_magnitude_range",
    "stellar_magnitude_scale",
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

from .charts.magnitude_legend_matplotlib import (
    draw_stellar_magnitude_legend,
    stellar_magnitude_handles,
)

from .charts.magnitude_legend_workflow import (
    StellarMagnitudeLegendResult,
    draw_visible_stellar_magnitude_legend,
)

from .charts.magnitude_legend_style import (
    StellarMagnitudeLegendStyle,
    draw_styled_stellar_magnitude_legend,
)

from .charts.legend_plan import (
    ChartLegendPlan,
    LegendPlacement,
    default_chart_legend_plan,
)

from .charts.legend_composition import (
    ComposedChartLegends,
    apply_legend_placement,
    draw_planned_chart_legends,
)

from .charts.legend_geometry import (
    RenderedStarGeometry,
    RenderedStarsNotFoundError,
    rendered_star_geometry,
)
from .charts.rendered_legend_composition import (
    draw_rendered_chart_legends,
)

from .charts.legend_inputs import (
    ResolvedStellarLegendInputs,
    resolve_stellar_legend_inputs,
)

from .charts.automatic_legends import (
    AutomaticChartLegends,
    chart_type_name,
    draw_automatic_chart_legends,
)

from .charts.chart_legend_workflow import (
    RenderedChartWithLegends,
    render_chart_with_legends,
)

from .charts.cartoon_modes import (
    CartoonModePalette,
    CARTOON_PRINT_PALETTE,
    CARTOON_PRESENTATION_PALETTE,
    cartoon_chart_style,
)

_DEPRECATED_CARTOON_EXPORTS = frozenset(
    {"cartoon_output_mode", "compose_cartoon_chart"}
)


def __getattr__(name):
    """Load deprecated compatibility exports only when requested."""
    if name in _DEPRECATED_CARTOON_EXPORTS:
        from .charts import cartoon_composition

        return getattr(cartoon_composition, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | _DEPRECATED_CARTOON_EXPORTS)
