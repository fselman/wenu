"""Print and presentation realizations of the cartoon chart style."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .label_placement import resolve_constellation_label_offsets
from .modes import PresentationMode, PrintMode, ResolvedMode
from .presets import CartoonChartStyle


@dataclass(frozen=True)
class CartoonModePalette:
    """Colors used by one cartoon output realization."""

    sky: str
    foreground: str
    stars: str
    constellation_lines: str
    constellation_labels: str
    frame: str
    milky_way: str
    equatorial_grid: str
    ecliptic_grid: str
    galactic_grid: str
    altaz_grid: str
    footer: str = "black"


CARTOON_PRINT_PALETTE = CartoonModePalette(
    sky="white",
    foreground="#000000",
    stars="#000000",
    constellation_lines="#000000",
    constellation_labels="#000000",
    frame="#000000",
    milky_way="#000000",
    altaz_grid="#707070",
    equatorial_grid="#667788",
    ecliptic_grid="orange",
    galactic_grid="blue",
    footer="#000000",
)

CARTOON_PRESENTATION_PALETTE = CartoonModePalette(
    sky="#1677A6",
    foreground="#FFE066",
    stars="#FFE066",
    constellation_lines="#FFE066",
    constellation_labels="#FFE066",
    frame="#FFE066",
    milky_way="#FFE066",
    altaz_grid="#FFFFFF",
    equatorial_grid="#FFFFFF",
    ecliptic_grid="#FFA500",
    galactic_grid="#66CCFF",
    footer="#FFFFFF",
)


@dataclass(frozen=True)
class CartoonModeChartStyle(CartoonChartStyle):
    """Cartoon style with explicit constellation-label clearance."""

    output_mode_name: str = "print"
    constellation_label_offset: tuple[float, float] = (0.18, 0.14)
    constellation_label_halo_alpha: float = 0.78

    def configure_axes(self, ax, *, title=None):
        """Apply the trichromatic cartoon canvas and context color."""
        configured = super().configure_axes(ax, title=title)
        color = self.canvas.foreground_color
        configured.title.set_color(color)
        for spine in configured.spines.values():
            spine.set_color(color)
            spine.set_linewidth(self.grids.boundary_linewidth)
        return configured

    def chart_boundary_style(self):
        """Return mode-resolved appearance for a circular chart boundary."""
        return {
            "edgecolor": self.grids.boundary_color,
            "linewidth": self.grids.constellation_linewidth,
        }

    def layer_options(self, sky, *, horizon_altitude_deg=None):
        options = super().layer_options(
            sky,
            horizon_altitude_deg=horizon_altitude_deg,
        )
        layer = getattr(sky, "constellation_labels", None)
        if layer is None or layer not in options:
            return options
        render = options[layer]["render"]
        render["label_offset"] = self.constellation_label_offset
        label_style = render["label_style"]
        label_style["ha"] = "left"
        label_style["va"] = "bottom"
        label_style["bbox"] = {
            "boxstyle": "round,pad=0.10",
            "facecolor": self.canvas.sky_color,
            "edgecolor": "none",
            "alpha": self.constellation_label_halo_alpha,
        }
        return options


def _mode_name(mode) -> str:
    if isinstance(mode, str):
        name = mode.strip().lower()
    elif isinstance(mode, PresentationMode):
        name = "presentation"
    elif isinstance(mode, PrintMode):
        name = "print"
    else:
        name = getattr(mode, "name", "")
        name = str(name).strip().lower()
    if name not in {"print", "presentation"}:
        raise ValueError("Cartoon output mode must be print or presentation.")
    return name


def _scales(mode, name):
    if isinstance(mode, ResolvedMode):
        return (
            mode.font_scale,
            mode.line_scale,
            mode.symbol_scale,
        )
    if not isinstance(mode, str):
        return (
            float(getattr(mode, "font_scale", 1.0)),
            float(getattr(mode, "line_scale", 1.0)),
            float(getattr(mode, "symbol_scale", 1.0)),
        )
    defaults = PresentationMode() if name == "presentation" else PrintMode()
    return (
        defaults.font_scale,
        defaults.line_scale,
        defaults.symbol_scale,
    )


def cartoon_chart_style(
    mode="print",
    *,
    base=None,
    mode_name=None,
    constellation_label_positions=None,
    constellation_label_offsets=None,
    constellation_label_clearance=(0.24, 0.20),
    palette=None,
    constellation_label_offset=None,
    constellation_label_halo_opacity=None,
):
    """Return a complete cartoon style for print or presentation."""
    name = _mode_name(mode if mode_name is None else mode_name)
    if palette is None:
        palette = (
            CARTOON_PRESENTATION_PALETTE
            if name == "presentation"
            else CARTOON_PRINT_PALETTE
        )
    if not isinstance(palette, CartoonModePalette):
        raise TypeError("palette must be a CartoonModePalette.")
    font_scale, line_scale, symbol_scale = _scales(mode, name)
    transform = {}
    if constellation_label_offset is not None:
        transform["constellation_label_offset"] = tuple(
            constellation_label_offset
        )
    if constellation_label_halo_opacity is not None:
        transform["constellation_label_halo_alpha"] = float(
            constellation_label_halo_opacity
        )
    if base is None:
        style = CartoonModeChartStyle(**transform)
    elif isinstance(base, CartoonModeChartStyle):
        style = replace(base, **transform) if transform else base
    elif isinstance(base, CartoonChartStyle):
        style = CartoonModeChartStyle(
            canvas=base.canvas,
            stars=base.stars,
            isophotes=base.isophotes,
            deep_sky=base.deep_sky,
            grids=base.grids,
            mask=base.mask,
            legend=base.legend,
            **transform,
        )
    else:
        raise TypeError("base must be a CartoonChartStyle.")
    positioned_labels = constellation_label_positions is not None
    resolved_label_offsets = (
        resolve_constellation_label_offsets(
            constellation_label_positions,
            constellation_label_offsets,
            clearance=constellation_label_clearance,
        )
        if positioned_labels
        else (
            None
            if constellation_label_offsets is None
            else dict(constellation_label_offsets)
        )
    )

    canvas = replace(
        style.canvas,
        sky_color=palette.sky,
        foreground_color=palette.foreground,
        footer_color=palette.footer,
        label_fontsize=style.canvas.label_fontsize * font_scale,
    )
    stars = replace(
        style.stars,
        color=palette.stars,
        area_scale=style.stars.area_scale * symbol_scale,
        draw_variable_symbols=False,
        draw_multiple_symbols=False,
    )
    grids = replace(
        style.grids,
        boundary_color=palette.frame,
        boundary_linewidth=(
            style.grids.boundary_linewidth * line_scale
        ),
        constellation_line_color=palette.constellation_lines,
        constellation_linewidth=(
            style.grids.constellation_linewidth * line_scale
        ),
        constellation_label_color=palette.constellation_labels,
        constellation_label_offset=style.constellation_label_offset,
        constellation_label_offsets=resolved_label_offsets,
        constellation_label_ha=(
            "center" if positioned_labels else "left"
        ),
        constellation_label_va=(
            "center" if positioned_labels else "bottom"
        ),
        coordinate_label_color=None,
        altaz_color=palette.altaz_grid,
        horizon_color=palette.frame,
        horizon_linewidth=(
            style.grids.horizon_linewidth * line_scale
        ),
        equatorial_color=palette.equatorial_grid,
        ecliptic_color=palette.ecliptic_grid,
        galactic_color=palette.galactic_grid,
        coordinate_label_fontsize=(
            style.grids.coordinate_label_fontsize * font_scale
        ),
    )
    isophotes = replace(
        style.isophotes,
        milky_way_color=palette.milky_way,
        milky_way_alpha=0.0,
        milky_way_contour_color=palette.frame,
        milky_way_contour_linestyle=":",
        milky_way_contour_alpha=1.0,
        lmc_color=palette.milky_way,
        lmc_alpha=0.0,
        lmc_edge_color=palette.frame,
        lmc_edge_alpha=1.0,
        lmc_linewidth=(
            style.isophotes.milky_way_contour_linewidth * line_scale
        ),
        lmc_linestyle=":",
        smc_color=palette.milky_way,
        smc_alpha=0.0,
        smc_edge_color=palette.frame,
        smc_edge_alpha=1.0,
        smc_linewidth=(
            style.isophotes.milky_way_contour_linewidth * line_scale
        ),
        smc_linestyle=":",
    )
    deep_sky = replace(
        style.deep_sky,
        nonstellar_color=palette.foreground,
        galaxy_edge_color=palette.foreground,
        galaxy_label_color=palette.foreground,
        supernova_remnant_color=palette.foreground,
        supernova_remnant_label_color=palette.foreground,
        globular_cluster_color=palette.foreground,
        globular_cluster_label_color=palette.foreground,
        planetary_nebula_color=palette.foreground,
        planetary_nebula_label_color=palette.foreground,
        open_cluster_color=palette.foreground,
        open_cluster_label_color=palette.foreground,
    )
    legend = replace(
        style.legend,
        fontsize=style.legend.fontsize * font_scale,
        title_fontsize=style.legend.title_fontsize * font_scale,
        facecolor=palette.sky,
        edgecolor=palette.foreground,
        text_color=palette.foreground,
    )
    replacements = {
        "canvas": canvas,
        "stars": stars,
        "grids": grids,
        "isophotes": isophotes,
        "deep_sky": deep_sky,
        "legend": legend,
    }
    replacements["output_mode_name"] = name
    return replace(
        style,
        **replacements,
    )
