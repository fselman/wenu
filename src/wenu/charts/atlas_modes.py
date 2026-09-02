"""Print and presentation realizations of the atlas chart style."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .modes import PresentationMode, PrintMode, ResolvedMode
from .presets import AtlasChartStyle


@dataclass(frozen=True)
class AtlasPresentationPalette:
    """High-contrast colors for atlas charts shown on a screen."""

    sky: str = "#0262AD"
    foreground: str = "#F7FBFD"
    stars: str = "#FFF4CC"
    structure: str = "#FFE066"
    labels: str = "#FFF0A6"
    frame: str = "#BFE7F5"
    milky_way: str = "#69B9D6"
    deep_sky: str = "#FFE08A"


ATLAS_PRESENTATION_PALETTE = AtlasPresentationPalette()


def _mode_name(mode) -> str:
    if isinstance(mode, str):
        name = mode.strip().lower()
        if name == "paper":
            name = "print"
    elif isinstance(mode, PresentationMode):
        name = "presentation"
    elif isinstance(mode, PrintMode):
        name = "print"
    else:
        name = str(getattr(mode, "name", "")).strip().lower()
    if name not in {"print", "presentation"}:
        raise ValueError("Atlas output mode must be print or presentation.")
    return name


def _scales(mode, name):
    if isinstance(mode, ResolvedMode):
        return mode.font_scale, mode.line_scale, mode.symbol_scale
    if not isinstance(mode, str):
        return (
            float(getattr(mode, "font_scale", 1.0)),
            float(getattr(mode, "line_scale", 1.0)),
            float(getattr(mode, "symbol_scale", 1.0)),
        )
    defaults = PresentationMode() if name == "presentation" else PrintMode()
    return defaults.font_scale, defaults.line_scale, defaults.symbol_scale


def atlas_chart_style(
    mode="print",
    *,
    base=None,
    mode_name=None,
    presentation_palette=None,
):
    """Return an immutable atlas style adapted to one output medium.

    Print deliberately preserves the established atlas preset. Presentation
    changes only visual values; chart geometry and astronomical selection
    remain owned by the chart type and detail policy.
    """
    name = _mode_name(mode if mode_name is None else mode_name)
    style = AtlasChartStyle() if base is None else base
    if not isinstance(style, AtlasChartStyle):
        raise TypeError("base must be an AtlasChartStyle.")
    if name == "print":
        return style

    font_scale, line_scale, symbol_scale = _scales(mode, name)
    palette = (
        ATLAS_PRESENTATION_PALETTE
        if presentation_palette is None
        else presentation_palette
    )
    if not isinstance(palette, AtlasPresentationPalette):
        raise TypeError(
            "presentation_palette must be an AtlasPresentationPalette."
        )
    canvas = replace(
        style.canvas,
        sky_color=palette.sky,
        foreground_color=palette.foreground,
        label_fontsize=style.canvas.label_fontsize * font_scale,
    )
    stars = replace(
        style.stars,
        color=palette.stars,
        area_scale=style.stars.area_scale * symbol_scale,
        variable_color=palette.stars,
        variable_symbol_size=(
            style.stars.variable_symbol_size * symbol_scale
        ),
        variable_linewidth=(
            style.stars.variable_linewidth * line_scale
        ),
        multiple_color=palette.stars,
        multiple_symbol_size=(
            style.stars.multiple_symbol_size * symbol_scale
        ),
        multiple_linewidth=(
            style.stars.multiple_linewidth * line_scale
        ),
    )
    isophotes = replace(
        style.isophotes,
        milky_way_color=palette.milky_way,
        milky_way_contour_color=palette.frame,
        milky_way_contour_linewidth=(
            style.isophotes.milky_way_contour_linewidth * line_scale
        ),
        lmc_color=palette.milky_way,
        smc_color=palette.milky_way,
    )
    deep_sky = replace(
        style.deep_sky,
        nonstellar_color=palette.deep_sky,
        nonstellar_linewidth=style.deep_sky.nonstellar_linewidth * line_scale,
        nonstellar_label_fontsize=(
            style.deep_sky.nonstellar_label_fontsize * font_scale
        ),
        nonstellar_dot_markersize=(
            style.deep_sky.nonstellar_dot_markersize * symbol_scale
        ),
        galaxy_edge_color=palette.foreground,
        galaxy_linewidth=style.deep_sky.galaxy_linewidth * line_scale,
        galaxy_label_color=palette.foreground,
        galaxy_label_fontsize=(
            style.deep_sky.galaxy_label_fontsize * font_scale
        ),
        supernova_remnant_color=palette.structure,
        supernova_remnant_linewidth=(
            style.deep_sky.supernova_remnant_linewidth * line_scale
        ),
        supernova_remnant_label_color=palette.labels,
        supernova_remnant_label_fontsize=(
            style.deep_sky.supernova_remnant_label_fontsize * font_scale
        ),
        globular_cluster_color=palette.deep_sky,
        globular_cluster_linewidth=(
            style.deep_sky.globular_cluster_linewidth * line_scale
        ),
        globular_cluster_label_color=palette.labels,
        globular_cluster_label_fontsize=(
            style.deep_sky.globular_cluster_label_fontsize * font_scale
        ),
        planetary_nebula_color=palette.structure,
        planetary_nebula_symbol_size=(
            style.deep_sky.planetary_nebula_symbol_size * symbol_scale
        ),
        planetary_nebula_linewidth=(
            style.deep_sky.planetary_nebula_linewidth * line_scale
        ),
        planetary_nebula_label_color=palette.labels,
        planetary_nebula_label_fontsize=(
            style.deep_sky.planetary_nebula_label_fontsize * font_scale
        ),
        open_cluster_color=palette.deep_sky,
        open_cluster_symbol_size=(
            style.deep_sky.open_cluster_symbol_size * symbol_scale
        ),
        open_cluster_linewidth=(
            style.deep_sky.open_cluster_linewidth * line_scale
        ),
        open_cluster_label_color=palette.labels,
        open_cluster_label_fontsize=(
            style.deep_sky.open_cluster_label_fontsize * font_scale
        ),
    )
    solar_system = replace(
        style.solar_system,
        venus_color="#FFE6A3",
        venus_symbol_size=(
            style.solar_system.venus_symbol_size * symbol_scale
        ),
        venus_linewidth=style.solar_system.venus_linewidth * line_scale,
        venus_label_fontsize=(
            style.solar_system.venus_label_fontsize * font_scale
        ),
        moon_color="#E6E1D3",
        moon_symbol_size=(
            style.solar_system.moon_symbol_size * symbol_scale
        ),
        moon_linewidth=style.solar_system.moon_linewidth * line_scale,
        moon_label_fontsize=(
            style.solar_system.moon_label_fontsize * font_scale
        ),
        moon_disk_sequence_label_fontsize=(
            style.solar_system.moon_disk_sequence_label_fontsize * font_scale
        ),
    )
    grids = replace(
        style.grids,
        boundary_color=palette.frame,
        boundary_linewidth=style.grids.boundary_linewidth * line_scale,
        constellation_line_color=palette.structure,
        constellation_linewidth=(
            style.grids.constellation_linewidth * line_scale
        ),
        constellation_label_color=palette.labels,
        altaz_color=palette.frame,
        horizon_color=palette.frame,
        horizon_linewidth=style.grids.horizon_linewidth * line_scale,
        equatorial_color=palette.frame,
        ecliptic_color=palette.structure,
        galactic_color=palette.foreground,
        coordinate_linewidth=style.grids.coordinate_linewidth * line_scale,
        coordinate_label_color=None,
        coordinate_label_fontsize=(
            style.grids.coordinate_label_fontsize * font_scale
        ),
    )
    legend = replace(
        style.legend,
        fontsize=style.legend.fontsize * font_scale,
        title_fontsize=style.legend.title_fontsize * font_scale,
        facecolor=palette.sky,
        edgecolor=palette.frame,
    )
    mask = replace(style.mask, color=palette.sky)
    return replace(
        style,
        canvas=canvas,
        stars=stars,
        isophotes=isophotes,
        deep_sky=deep_sky,
        solar_system=solar_system,
        grids=grids,
        legend=legend,
        mask=mask,
    )
