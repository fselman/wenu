"""Canonical physical-print appearance for polar planisphere disks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from .presets import AtlasChartStyle


@dataclass(frozen=True)
class PolarPlanisphereStylePalette:
    """Provisional configurable colors and hierarchy for paper disks."""

    paper_color: str = "#FFFFFF"
    foreground_color: str = "#244C64"
    star_color: str = "#005B8F"
    star_area_scale: float = 0.55
    milky_way_color: str = "#C9DFE8"
    milky_way_opacity: float = 0.32
    constellation_line_color: str = "#66899B"
    constellation_linewidth: float = 0.35
    constellation_line_opacity: float = 0.68
    constellation_label_color: str = "#365F78"
    constellation_label_fontsize: float = 7.5
    constellation_label_opacity: float = 0.90
    boundary_color: str = "#6F8795"
    boundary_linewidth: float = 0.45
    boundary_opacity: float = 0.80

    def __post_init__(self):
        positive = (
            "star_area_scale",
            "constellation_label_fontsize",
        )
        nonnegative = (
            "constellation_linewidth",
            "boundary_linewidth",
        )
        opacities = (
            "milky_way_opacity",
            "constellation_line_opacity",
            "constellation_label_opacity",
            "boundary_opacity",
        )
        for name in positive:
            value = float(getattr(self, name))
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be positive and finite.")
            object.__setattr__(self, name, value)
        for name in nonnegative:
            value = float(getattr(self, name))
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be non-negative and finite.")
            object.__setattr__(self, name, value)
        for name in opacities:
            value = float(getattr(self, name))
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")
            object.__setattr__(self, name, value)


def polar_planisphere_chart_style(base, palette):
    """Return the sparse physical-paper realization of an atlas style."""
    if not isinstance(base, AtlasChartStyle):
        raise TypeError("base must be an AtlasChartStyle.")
    if not isinstance(palette, PolarPlanisphereStylePalette):
        raise TypeError("palette must be a PolarPlanisphereStylePalette.")
    return replace(
        base,
        canvas=replace(
            base.canvas,
            sky_color=palette.paper_color,
            foreground_color=palette.foreground_color,
            label_fontsize=palette.constellation_label_fontsize,
        ),
        stars=replace(
            base.stars,
            color=palette.star_color,
            area_scale=palette.star_area_scale,
            draw_variable_symbols=False,
            draw_multiple_symbols=False,
        ),
        isophotes=replace(
            base.isophotes,
            milky_way_color=palette.milky_way_color,
            milky_way_alpha=palette.milky_way_opacity,
            milky_way_edge_color=None,
            milky_way_edge_alpha=0.0,
            milky_way_linewidth=0.0,
            milky_way_contour_color=None,
            milky_way_contour_linestyle="None",
            milky_way_contour_linewidth=0.0,
            milky_way_contour_alpha=0.0,
        ),
        grids=replace(
            base.grids,
            boundary_color=palette.boundary_color,
            boundary_linewidth=palette.boundary_linewidth,
            boundary_linestyle="-",
            boundary_alpha=palette.boundary_opacity,
            constellation_line_color=palette.constellation_line_color,
            constellation_linewidth=palette.constellation_linewidth,
            constellation_line_alpha=palette.constellation_line_opacity,
            constellation_label_color=palette.constellation_label_color,
            constellation_label_alpha=palette.constellation_label_opacity,
            draw_coordinate_labels=False,
        ),
        mask=replace(base.mask, color=palette.paper_color),
        legend=replace(base.legend, visible=False),
    )
