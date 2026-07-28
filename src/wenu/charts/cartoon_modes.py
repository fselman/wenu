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


CARTOON_PRINT_PALETTE = CartoonModePalette(
    sky="white",
    foreground="#1A1A1A",
    stars="#111111",
    constellation_lines="#252525",
    constellation_labels="#252525",
    frame="#555555",
    milky_way="#DCE7EB",
)

CARTOON_PRESENTATION_PALETTE = CartoonModePalette(
    sky="#1677A6",
    foreground="#F7FBFD",
    stars="#FFF4CC",
    constellation_lines="#FFE066",
    constellation_labels="#FFF0A6",
    frame="#BFE7F5",
    milky_way="#69B9D6",
)


@dataclass(frozen=True)
class CartoonModeChartStyle(CartoonChartStyle):
    """Cartoon style with explicit constellation-label clearance."""

    constellation_label_offset: tuple[float, float] = (0.18, 0.14)
    constellation_label_halo_alpha: float = 0.78

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
    constellation_label_positions=None,
    constellation_label_offsets=None,
    constellation_label_clearance=(0.24, 0.20),
):
    """Return a complete cartoon style for print or presentation."""
    name = _mode_name(mode)
    palette = (
        CARTOON_PRESENTATION_PALETTE
        if name == "presentation"
        else CARTOON_PRINT_PALETTE
    )
    font_scale, line_scale, symbol_scale = _scales(mode, name)
    base = CartoonModeChartStyle()
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
        base.canvas,
        sky_color=palette.sky,
        foreground_color=palette.foreground,
        label_fontsize=base.canvas.label_fontsize * font_scale,
    )
    stars = replace(
        base.stars,
        color=palette.stars,
        area_scale=base.stars.area_scale * symbol_scale,
        draw_variable_symbols=False,
        draw_multiple_symbols=False,
    )
    grids = replace(
        base.grids,
        boundary_color=palette.frame,
        boundary_linewidth=(
            base.grids.boundary_linewidth * line_scale
        ),
        constellation_line_color=palette.constellation_lines,
        constellation_linewidth=(
            base.grids.constellation_linewidth * line_scale
        ),
        constellation_label_color=palette.constellation_labels,
        constellation_label_offset=(0.18, 0.14),
        constellation_label_offsets=resolved_label_offsets,
        constellation_label_ha=(
            "center" if positioned_labels else "left"
        ),
        constellation_label_va=(
            "center" if positioned_labels else "bottom"
        ),
        coordinate_label_color=palette.foreground,
        coordinate_label_fontsize=(
            base.grids.coordinate_label_fontsize * font_scale
        ),
    )
    isophotes = replace(
        base.isophotes,
        milky_way_color=palette.milky_way,
        milky_way_contour_color=palette.frame,
    )
    legend = replace(
        base.legend,
        fontsize=base.legend.fontsize * font_scale,
        title_fontsize=base.legend.title_fontsize * font_scale,
    )
    mask = replace(base.mask, color=palette.sky)
    return replace(
        base,
        canvas=canvas,
        stars=stars,
        grids=grids,
        isophotes=isophotes,
        legend=legend,
        mask=mask,
    )
