"""Canonical physical-print appearance for polar planisphere disks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from .presets import AtlasChartStyle


@dataclass(frozen=True)
class PolarPlanisphereStylePalette:
    """Provisional configurable colors and hierarchy for paper disks."""

    paper_color: str = "#FFFFFF"
    foreground_color: str = "#16394D"
    star_color: str = "#003F66"
    star_area_scale: float = 0.55
    star_magnitude_scale: float = 2.2727272727272725
    star_magnitude_exponent: float = 0.30488598388546717
    star_minimum_area: float = 1.25
    bright_star_magnitude_limit: float = 0.18
    bright_star_magnitude_scale: float = 0.617283950617284
    bright_star_magnitude_offset: float = -0.1111111111111111
    bright_star_symbol_area_scale: float = 1.0 / 0.38**2
    ordinary_star_magnitude_scale: float = 0.7518796992481203
    ordinary_star_magnitude_offset: float = -0.13533834586466165
    milky_way_color: str = "#A8C8D6"
    milky_way_opacity: float = 0.45
    magellanic_cloud_color: str = "#A8C8D6"
    lmc_opacity: float = 0.32
    smc_opacity: float = 0.28
    constellation_line_color: str = "#456B7D"
    constellation_linewidth: float = 0.675
    constellation_line_opacity: float = 0.85
    constellation_label_color: str = "#23495D"
    constellation_label_fontsize: float = 7.5
    constellation_label_opacity: float = 1.0
    reference_color: str = "#456B7D"
    reference_linewidth: float = 0.75
    reference_opacity: float = 0.65
    reference_label_fontsize: float = 5.25
    deep_sky_color: str = "#23495D"
    deep_sky_label_fontsize: float = 4.5
    deep_sky_outline_minimum_size_arcmin: float = 40.0
    globular_cluster_minimum_size_arcmin: float = 80.0
    boundary_color: str = "#456B7D"
    boundary_linewidth: float = 0.55
    boundary_opacity: float = 0.95
    calendar_day_label_fontsize: float = 6.45
    calendar_day_label_fontweight: str = "semibold"
    calendar_month_label_fontsize: float = 11.5
    calendar_month_label_fontweight: str = "semibold"

    def __post_init__(self):
        positive = (
            "star_area_scale",
            "star_magnitude_scale",
            "star_magnitude_exponent",
            "star_minimum_area",
            "bright_star_magnitude_scale",
            "bright_star_symbol_area_scale",
            "ordinary_star_magnitude_scale",
            "constellation_label_fontsize",
            "reference_label_fontsize",
            "deep_sky_label_fontsize",
            "calendar_day_label_fontsize",
            "calendar_month_label_fontsize",
            "deep_sky_outline_minimum_size_arcmin",
            "globular_cluster_minimum_size_arcmin",
        )
        nonnegative = (
            "constellation_linewidth",
            "reference_linewidth",
            "boundary_linewidth",
        )
        opacities = (
            "milky_way_opacity",
            "lmc_opacity",
            "smc_opacity",
            "constellation_line_opacity",
            "constellation_label_opacity",
            "reference_opacity",
            "boundary_opacity",
        )
        finite_values = (
            "bright_star_magnitude_limit",
            "bright_star_magnitude_offset",
            "ordinary_star_magnitude_offset",
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
        for name in finite_values:
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")
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
            magnitude_sizing=replace(
                base.stars.magnitude_sizing,
                scale=palette.star_magnitude_scale,
                exponent=palette.star_magnitude_exponent,
                minimum_area=(
                    palette.star_minimum_area / palette.star_area_scale
                ),
            ),
            draw_bright_symbols=True,
            bright_magnitude_limit=palette.bright_star_magnitude_limit,
            bright_magnitude_scale=palette.bright_star_magnitude_scale,
            bright_magnitude_offset=palette.bright_star_magnitude_offset,
            bright_symbol_area_scale=(
                palette.bright_star_symbol_area_scale
            ),
            ordinary_magnitude_scale=(
                palette.ordinary_star_magnitude_scale
            ),
            ordinary_magnitude_offset=(
                palette.ordinary_star_magnitude_offset
            ),
            bright_color=palette.star_color,
            bright_alpha=1.0,
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
            lmc_color=palette.magellanic_cloud_color,
            lmc_alpha=palette.lmc_opacity,
            smc_color=palette.magellanic_cloud_color,
            smc_alpha=palette.smc_opacity,
        ),
        deep_sky=replace(
            base.deep_sky,
            nonstellar_color=palette.deep_sky_color,
            nonstellar_minimum_size_arcmin=(
                palette.deep_sky_outline_minimum_size_arcmin
            ),
            nonstellar_draw_labels=True,
            nonstellar_label_fontsize=palette.deep_sky_label_fontsize,
            galaxy_edge_color=palette.deep_sky_color,
            galaxy_minimum_size_arcmin=(
                palette.deep_sky_outline_minimum_size_arcmin
            ),
            galaxy_draw_labels=True,
            galaxy_label_color=palette.deep_sky_color,
            galaxy_label_fontsize=palette.deep_sky_label_fontsize,
            globular_cluster_color=palette.deep_sky_color,
            globular_cluster_minimum_size_arcmin=(
                palette.globular_cluster_minimum_size_arcmin
            ),
            globular_cluster_draw_labels=True,
            globular_cluster_label_color=palette.deep_sky_color,
            globular_cluster_label_fontsize=(
                palette.deep_sky_label_fontsize
            ),
            planetary_nebula_color=palette.deep_sky_color,
            planetary_nebula_draw_labels=True,
            planetary_nebula_label_color=palette.deep_sky_color,
            planetary_nebula_label_fontsize=(
                palette.deep_sky_label_fontsize
            ),
            open_cluster_color=palette.deep_sky_color,
            open_cluster_draw_labels=True,
            open_cluster_label_color=palette.deep_sky_color,
            open_cluster_label_fontsize=palette.deep_sky_label_fontsize,
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
            equatorial_color=palette.reference_color,
            ecliptic_color=palette.reference_color,
            galactic_color=palette.reference_color,
            coordinate_linewidth=palette.reference_linewidth,
            coordinate_alpha=palette.reference_opacity,
            coordinate_label_color=palette.reference_color,
            coordinate_label_fontsize=palette.reference_label_fontsize,
            draw_coordinate_labels=False,
        ),
        mask=replace(base.mask, color=palette.paper_color),
        legend=replace(base.legend, visible=False),
        calendar=replace(
            base.calendar,
            day_label_fontsize=palette.calendar_day_label_fontsize,
            day_label_fontweight=palette.calendar_day_label_fontweight,
            month_label_fontsize=palette.calendar_month_label_fontsize,
            month_label_fontweight=palette.calendar_month_label_fontweight,
        ),
    )
