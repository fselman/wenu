"""Named, complete visual presets for Wenu charts."""

from __future__ import annotations

from dataclasses import dataclass, field

from .style_components import (
    CanvasStyle,
    ChartStyle,
    DeepSkyStyle,
    GridStyle,
    IsophoteStyle,
    LegendStyle,
    MaskStyle,
    StellarStyle,
)


@dataclass(frozen=True)
class AtlasChartStyle(ChartStyle):
    """White-background classroom astronomical-atlas presentation."""

    canvas: CanvasStyle = field(
        default_factory=lambda: CanvasStyle(
            sky_color="white",
            foreground_color="#505050",
            label_fontsize=8.5,
        )
    )
    stars: StellarStyle = field(
        default_factory=lambda: StellarStyle(
            color="#151515",
            area_scale=0.85,
            draw_variable_symbols=False,
            draw_multiple_symbols=False,
        )
    )
    isophotes: IsophoteStyle = field(
        default_factory=lambda: IsophoteStyle(
            milky_way_color="#b9d3da",
            milky_way_alpha=0.28,
            milky_way_contour_color="#555555",
            milky_way_contour_linestyle=":",
            milky_way_contour_linewidth=0.35,
            milky_way_contour_alpha=0.28,
            lmc_color="#b9d3da",
            lmc_alpha=0.22,
            smc_color="#b9d3da",
            smc_alpha=0.18,
        )
    )
    deep_sky: DeepSkyStyle = field(
        default_factory=lambda: DeepSkyStyle(
            nonstellar_color="#c5a000",
            galaxy_edge_color="#b43b37",
            supernova_remnant_color="#5f844c",
            supernova_remnant_linestyle="-",
            supernova_remnant_linewidth=0.55,
            globular_cluster_color="#c5a000",
            planetary_nebula_color="#6f8e4d",
            open_cluster_color="#d2b321",
            open_cluster_symbol_size=18.0,
            open_cluster_linewidth=0.45,
            planetary_nebula_symbol_size=18.0,
            planetary_nebula_linewidth=0.45,
        )
    )
    grids: GridStyle = field(
        default_factory=lambda: GridStyle(
            boundary_color="#777777",
            boundary_linewidth=0.35,
            boundary_linestyle=":",
            boundary_alpha=0.65,
            constellation_line_color="#686868",
            constellation_linewidth=0.35,
            constellation_line_alpha=0.58,
            constellation_label_color="#5b5b5b",
            constellation_label_alpha=0.90,
            altaz_color="#707070",
            equatorial_color="black",
            equatorial_linestyle="-",
            ecliptic_color="orange",
            ecliptic_linestyle="--",
            galactic_color="blue",
            galactic_linestyle="--",
            coordinate_linewidth=0.45,
            coordinate_alpha=0.65,
            draw_coordinate_labels=True,
            coordinate_label_color=None,
            coordinate_label_fontsize=6.0,
            coordinate_label_alpha=0.85,
        )
    )
    mask: MaskStyle = field(
        default_factory=lambda: MaskStyle(
            color="#d8d8d8",
            alpha=0.42,
            zorder=20.0,
        )
    )
    legend: LegendStyle = field(
        default_factory=lambda: LegendStyle(
            visible=True,
            location="upper right",
            fontsize=5.7,
            title_fontsize=6.2,
        )
    )


@dataclass(frozen=True)
class CartoonChartStyle(ChartStyle):
    """Original, sparse classroom-chart visual language.

    This preset controls appearance only.  Chart geometry belongs to the
    chart type, output sizing belongs to the chart mode, and layer/star
    selection belongs to a detail policy such as ``CartoonDetailPolicy``.
    """

    canvas: CanvasStyle = field(
        default_factory=lambda: CanvasStyle(
            sky_color="#fffdf7",
            foreground_color="#172238",
            label_fontsize=13.0,
        )
    )
    stars: StellarStyle = field(
        default_factory=lambda: StellarStyle(
            color="#172238",
            area_scale=1.30,
            draw_variable_symbols=False,
            draw_multiple_symbols=False,
        )
    )
    isophotes: IsophoteStyle = field(
        default_factory=lambda: IsophoteStyle(
            milky_way_color="#dbe8ef",
            milky_way_alpha=0.20,
            milky_way_contour_color="#8aa6b6",
            milky_way_contour_linestyle=":",
            milky_way_contour_linewidth=0.45,
            milky_way_contour_alpha=0.35,
            lmc_color="#dbe8ef",
            lmc_alpha=0.18,
            smc_color="#dbe8ef",
            smc_alpha=0.16,
        )
    )
    deep_sky: DeepSkyStyle = field(
        default_factory=lambda: DeepSkyStyle(
            nonstellar_color="#b07a17",
            galaxy_edge_color="#a84940",
            supernova_remnant_color="#66865d",
            globular_cluster_color="#b07a17",
            planetary_nebula_color="#66865d",
            open_cluster_color="#b89028",
            open_cluster_symbol_size=16.0,
            open_cluster_linewidth=0.55,
            planetary_nebula_symbol_size=16.0,
            planetary_nebula_linewidth=0.55,
        )
    )
    grids: GridStyle = field(
        default_factory=lambda: GridStyle(
            boundary_color="#9aa0a6",
            boundary_linewidth=0.30,
            boundary_linestyle=":",
            boundary_alpha=0.45,
            constellation_line_color="#304f78",
            constellation_linewidth=1.15,
            constellation_line_alpha=0.95,
            constellation_label_color="#203958",
            constellation_label_alpha=1.0,
            equatorial_color="black",
            equatorial_linestyle="-",
            ecliptic_color="orange",
            ecliptic_linestyle="--",
            galactic_color="blue",
            galactic_linestyle="--",
            coordinate_linewidth=0.40,
            coordinate_alpha=0.45,
            draw_coordinate_labels=False,
            coordinate_label_color=None,
            coordinate_label_fontsize=7.0,
            coordinate_label_alpha=0.75,
        )
    )
    mask: MaskStyle = field(
        default_factory=lambda: MaskStyle(
            color="#d8dde2",
            alpha=0.25,
            zorder=20.0,
        )
    )
    legend: LegendStyle = field(
        default_factory=lambda: LegendStyle(
            visible=False,
            location="upper right",
            fontsize=7.0,
            title_fontsize=7.5,
        )
    )
