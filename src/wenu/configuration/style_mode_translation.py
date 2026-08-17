"""Translate validated TOML values into existing style and mode contracts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from wenu.charts.atlas_modes import AtlasPresentationPalette
from wenu.charts.cartoon_modes import CartoonModePalette
from wenu.charts.modes import PresentationMode, PrintMode
from wenu.charts.presets import AtlasChartStyle, CartoonChartStyle
from wenu.charts.polar_planisphere_style import (
    PolarPlanisphereStylePalette,
)
from wenu.charts.style_components import (
    CanvasStyle,
    DeepSkyStyle,
    GridStyle,
    IsophoteStyle,
    LegendStyle,
    MaskStyle,
    StellarMagnitudeSizing,
    StellarStyle,
)

from .validation import (
    ConfigurationError,
    load_packaged_defaults,
    validate_configuration,
)


_LINE_STYLES = {
    "solid": "-",
    "dashed": "--",
    "dotted": ":",
    "dash_dot": "-.",
    "none": "None",
}


@dataclass(frozen=True)
class StyleModeDefaults:
    """Existing immutable style and mode contracts translated from TOML."""

    atlas: AtlasChartStyle
    cartoon: CartoonChartStyle
    polar_planisphere_palette: PolarPlanisphereStylePalette
    print_mode: PrintMode
    presentation_mode: PresentationMode
    atlas_presentation_palette: AtlasPresentationPalette
    cartoon_print_palette: CartoonModePalette
    cartoon_presentation_palette: CartoonModePalette
    cartoon_label_offset: tuple[float, float]
    cartoon_label_clearance: tuple[float, float]
    cartoon_label_halo_opacity: float


def _optional(value):
    return None if value == "none" else value


def _line_style(value: str) -> str:
    return _LINE_STYLES[value]


def _equal_line_values(
    style: Mapping[str, Any],
    name: str,
    *,
    style_name: str,
):
    values = {
        style[key][name]
        for key in (
            "equatorial_grid",
            "ecliptic_grid",
            "galactic_grid",
            "altaz_grid",
        )
    }
    if len(values) != 1:
        raise ConfigurationError(
            f"styles.{style_name}.coordinate_grids.{name}: independent "
            "values cannot translate until Milestone 46D.4 separates "
            "their runtime fields"
        )
    return values.pop()


def _stellar(table: Mapping[str, Any]) -> StellarStyle:
    variable = table["variable_symbol"]
    multiple = table["multiple_symbol"]
    return StellarStyle(
        color=table["color"],
        area_scale=table["area_scale"],
        magnitude_sizing=StellarMagnitudeSizing(
            reference=table["magnitude_reference"],
            reference_magnitude=table["reference_magnitude"],
            scale=table["magnitude_scale"],
            exponent=table["magnitude_exponent"],
            minimum_area=table["minimum_area"],
            maximum_area=_optional(table["maximum_area"]),
        ),
        draw_variable_symbols=variable["enabled"],
        variable_color=_optional(variable["color"]),
        variable_symbol_size=variable["size"],
        variable_linewidth=variable["edge_width"],
        variable_alpha=variable["opacity"],
        draw_multiple_symbols=multiple["enabled"],
        multiple_color=_optional(multiple["color"]),
        multiple_symbol_size=multiple["size"],
        multiple_linewidth=multiple["edge_width"],
        multiple_alpha=multiple["opacity"],
    )


def _isophotes(style: Mapping[str, Any]) -> IsophoteStyle:
    milky_way = style["milky_way"]
    lmc = style["lmc"]
    smc = style["smc"]
    return IsophoteStyle(
        milky_way_color=milky_way["fill"]["color"],
        milky_way_alpha=milky_way["fill"]["opacity"],
        milky_way_edge_color=_optional(milky_way["edge"]["color"]),
        milky_way_edge_alpha=milky_way["edge"]["opacity"],
        milky_way_linewidth=milky_way["edge"]["line_width"],
        milky_way_contour_color=_optional(
            milky_way["contour"]["color"]
        ),
        milky_way_contour_linestyle=_line_style(
            milky_way["contour"]["line_style"]
        ),
        milky_way_contour_linewidth=(
            milky_way["contour"]["line_width"]
        ),
        milky_way_contour_alpha=milky_way["contour"]["opacity"],
        lmc_color=lmc["fill"]["color"],
        lmc_alpha=lmc["fill"]["opacity"],
        lmc_edge_color=_optional(lmc["edge"]["color"]),
        lmc_edge_alpha=lmc["edge"]["opacity"],
        lmc_linewidth=lmc["edge"]["line_width"],
        lmc_linestyle=_line_style(lmc["edge"]["line_style"]),
        smc_color=smc["fill"]["color"],
        smc_alpha=smc["fill"]["opacity"],
        smc_edge_color=_optional(smc["edge"]["color"]),
        smc_edge_alpha=smc["edge"]["opacity"],
        smc_linewidth=smc["edge"]["line_width"],
        smc_linestyle=_line_style(smc["edge"]["line_style"]),
    )


def _deep_sky(style: Mapping[str, Any]) -> DeepSkyStyle:
    nonstellar = style["nonstellar"]
    galaxy = style["galaxy"]
    supernova = style["supernova_remnant"]
    globular = style["globular_cluster"]
    planetary = style["planetary_nebula"]
    open_cluster = style["open_cluster"]
    return DeepSkyStyle(
        nonstellar_color=nonstellar["color"],
        nonstellar_linewidth=nonstellar["line_width"],
        nonstellar_alpha=nonstellar["opacity"],
        nonstellar_minimum_size_arcmin=(
            nonstellar["minimum_size_arcmin"]
        ),
        nonstellar_draw_labels=nonstellar["draw_labels"],
        nonstellar_label_fontsize=nonstellar["label_font_size"],
        nonstellar_symbol_dots=nonstellar["symbol_dots"],
        nonstellar_dot_markersize=nonstellar["symbol_dot_size"],
        galaxy_edge_color=galaxy["edge"]["color"],
        galaxy_linewidth=galaxy["edge"]["line_width"],
        galaxy_edge_alpha=galaxy["edge"]["opacity"],
        galaxy_face_color=_optional(galaxy["face_color"]),
        galaxy_face_alpha=galaxy["face_opacity"],
        galaxy_minimum_size_arcmin=galaxy["minimum_size_arcmin"],
        galaxy_draw_labels=galaxy["draw_labels"],
        galaxy_label_color=_optional(galaxy["label_color"]),
        galaxy_label_fontsize=galaxy["label_font_size"],
        supernova_remnant_color=supernova["color"],
        supernova_remnant_linewidth=supernova["line_width"],
        supernova_remnant_linestyle=_line_style(
            supernova["line_style"]
        ),
        supernova_remnant_alpha=supernova["opacity"],
        supernova_remnant_minimum_size_arcmin=(
            supernova["minimum_size_arcmin"]
        ),
        supernova_remnant_draw_labels=supernova["draw_labels"],
        supernova_remnant_label_color=_optional(supernova["label_color"]),
        supernova_remnant_label_fontsize=supernova["label_font_size"],
        globular_cluster_color=globular["color"],
        globular_cluster_linewidth=globular["line_width"],
        globular_cluster_alpha=globular["opacity"],
        globular_cluster_minimum_size_arcmin=(
            globular["minimum_size_arcmin"]
        ),
        globular_cluster_draw_labels=globular["draw_labels"],
        globular_cluster_label_color=_optional(globular["label_color"]),
        globular_cluster_label_fontsize=globular["label_font_size"],
        planetary_nebula_color=planetary["color"],
        planetary_nebula_face_color=planetary["face_color"],
        planetary_nebula_symbol_size=planetary["symbol_size"],
        planetary_nebula_linewidth=planetary["line_width"],
        planetary_nebula_alpha=planetary["opacity"],
        planetary_nebula_draw_labels=planetary["draw_labels"],
        planetary_nebula_label_color=_optional(planetary["label_color"]),
        planetary_nebula_label_fontsize=planetary["label_font_size"],
        open_cluster_color=open_cluster["color"],
        open_cluster_symbol_size=open_cluster["symbol_size"],
        open_cluster_linewidth=open_cluster["line_width"],
        open_cluster_alpha=open_cluster["opacity"],
        open_cluster_draw_labels=open_cluster["draw_labels"],
        open_cluster_label_color=_optional(open_cluster["label_color"]),
        open_cluster_label_fontsize=open_cluster["label_font_size"],
    )


def _grids(style: Mapping[str, Any], *, style_name: str) -> GridStyle:
    boundary = style["constellation_boundaries"]
    figures = style["constellation_figures"]
    labels = style["constellation_labels"]
    equatorial = style["equatorial_grid"]
    ecliptic = style["ecliptic_grid"]
    galactic = style["galactic_grid"]
    altaz = style["altaz_grid"]
    coordinate_labels = style["coordinate_labels"]
    horizon = style["horizon"]
    chart_boundary = style["chart_boundary"]
    for name in ("color", "line_width", "line_style", "opacity"):
        if chart_boundary[name] != boundary[name]:
            raise ConfigurationError(
                f"styles.{style_name}.chart_boundary.{name}: cannot differ "
                "from constellation_boundaries until Milestone 46D.4 "
                "separates their runtime fields"
            )
    return GridStyle(
        boundary_color=boundary["color"],
        boundary_linewidth=boundary["line_width"],
        boundary_linestyle=_line_style(boundary["line_style"]),
        boundary_alpha=boundary["opacity"],
        constellation_line_color=figures["color"],
        constellation_linewidth=figures["line_width"],
        constellation_line_alpha=figures["opacity"],
        constellation_label_color=labels["color"],
        constellation_label_alpha=labels["opacity"],
        constellation_label_offset=tuple(labels["offset"]),
        constellation_label_ha=labels["horizontal_alignment"],
        constellation_label_va=labels["vertical_alignment"],
        equatorial_color=equatorial["color"],
        equatorial_linestyle=_line_style(equatorial["line_style"]),
        ecliptic_color=ecliptic["color"],
        ecliptic_linestyle=_line_style(ecliptic["line_style"]),
        galactic_color=galactic["color"],
        galactic_linestyle=_line_style(galactic["line_style"]),
        altaz_color=altaz["color"],
        altaz_linestyle=_line_style(altaz["line_style"]),
        coordinate_linewidth=_equal_line_values(
            style,
            "line_width",
            style_name=style_name,
        ),
        coordinate_alpha=_equal_line_values(
            style,
            "opacity",
            style_name=style_name,
        ),
        draw_coordinate_labels=coordinate_labels["enabled"],
        coordinate_label_color=_optional(coordinate_labels["color"]),
        coordinate_label_fontsize=coordinate_labels["font_size"],
        coordinate_label_alpha=coordinate_labels["opacity"],
        horizon_altitude_deg=horizon["altitude"],
        minimum_altitude_deg=_optional(horizon["minimum_altitude"]),
        horizon_color=horizon["color"],
        horizon_linewidth=horizon["line_width"],
        horizon_linestyle=_line_style(horizon["line_style"]),
        horizon_alpha=horizon["opacity"],
        horizon_zorder=horizon["z_order"],
    )


def _style(table: Mapping[str, Any], style_type, *, style_name: str):
    canvas = table["canvas"]
    mask = table["mask"]
    legend = table["legend"]
    labels = table["constellation_labels"]
    if labels["font_size"] != canvas["label_font_size"]:
        raise ConfigurationError(
            f"styles.{style_name}.constellation_labels.font_size: cannot "
            "differ from canvas.label_font_size until Milestone 46D.4 "
            "separates their runtime fields"
        )
    return style_type(
        canvas=CanvasStyle(
            sky_color=canvas["background"],
            foreground_color=canvas["foreground"],
            label_fontsize=canvas["label_font_size"],
            footer_color=_optional(canvas["footer_color"]),
        ),
        stars=_stellar(table["stars"]),
        isophotes=_isophotes(table),
        deep_sky=_deep_sky(table),
        grids=_grids(table, style_name=style_name),
        mask=MaskStyle(
            color=mask["color"],
            alpha=mask["opacity"],
            zorder=mask["z_order"],
        ),
        legend=LegendStyle(
            visible=legend["visible"],
            location=legend["location"],
            fontsize=legend["font_size"],
            title_fontsize=legend["title_font_size"],
            frame=legend["frame"],
            facecolor=legend["face_color"],
            edgecolor=legend["edge_color"],
            alpha=legend["opacity"],
            columns=legend["columns"],
            text_color=_optional(legend["text_color"]),
        ),
    )


def _modes(configuration: Mapping[str, Any]):
    base = configuration["modes"]["base"]
    print_values = configuration["modes"]["print"]
    presentation = configuration["modes"]["presentation"]
    common = {
        "width_inches": base["width"],
        "height_inches": _optional(base["height"]),
        "transparent": base["transparent"],
    }
    return (
        PrintMode(
            **common,
            dpi=print_values["dpi"],
            font_scale=print_values["font_scale"],
            line_scale=print_values["line_scale"],
            symbol_scale=print_values["symbol_scale"],
            contrast_scale=print_values["contrast_scale"],
            prefer_vector=print_values["prefer_vector"],
        ),
        PresentationMode(
            **common,
            dpi=presentation["dpi"],
            font_scale=presentation["font_scale"],
            line_scale=presentation["line_scale"],
            symbol_scale=presentation["symbol_scale"],
            contrast_scale=presentation["contrast_scale"],
            prefer_vector=presentation["prefer_vector"],
        ),
    )


def _atlas_palette(table: Mapping[str, Any]) -> AtlasPresentationPalette:
    return AtlasPresentationPalette(**table)


def _cartoon_palette(table: Mapping[str, Any]) -> CartoonModePalette:
    return CartoonModePalette(
        sky=table["sky"],
        foreground=table["foreground"],
        stars=table["stars"],
        constellation_lines=table["figures"],
        constellation_labels=table["labels"],
        frame=table["frame"],
        milky_way=table["milky_way"],
        equatorial_grid=table["equatorial"],
        ecliptic_grid=table["ecliptic"],
        galactic_grid=table["galactic"],
        altaz_grid=table["altaz"],
        footer=table["footer"],
    )


def translate_style_mode_defaults(
    configuration: Mapping[str, Any] | None = None,
) -> StyleModeDefaults:
    """Translate validated values into immutable style/mode contracts."""
    values = (
        load_packaged_defaults()
        if configuration is None
        else validate_configuration(configuration)
    )
    styles = values["styles"]
    palettes = styles["palettes"]
    print_mode, presentation_mode = _modes(values)
    cartoon_mode = values["modes"]["cartoon"]
    return StyleModeDefaults(
        atlas=_style(
            styles["atlas"],
            AtlasChartStyle,
            style_name="atlas",
        ),
        cartoon=_style(
            styles["cartoon"],
            CartoonChartStyle,
            style_name="cartoon",
        ),
        polar_planisphere_palette=PolarPlanisphereStylePalette(
            paper_color=styles["polar_planisphere"]["paper_color"],
            foreground_color=(
                styles["polar_planisphere"]["foreground_color"]
            ),
            star_color=styles["polar_planisphere"]["star_color"],
            star_area_scale=(
                styles["polar_planisphere"]["star_area_scale"]
            ),
            star_magnitude_scale=(
                styles["polar_planisphere"]["star_magnitude_scale"]
            ),
            star_magnitude_exponent=(
                styles["polar_planisphere"]["star_magnitude_exponent"]
            ),
            star_minimum_area=(
                styles["polar_planisphere"]["star_minimum_area"]
            ),
            bright_star_magnitude_limit=(
                styles["polar_planisphere"][
                    "bright_star_magnitude_limit"
                ]
            ),
            bright_star_magnitude_offset=(
                styles["polar_planisphere"][
                    "bright_star_magnitude_offset"
                ]
            ),
            ordinary_star_magnitude_offset=(
                styles["polar_planisphere"][
                    "ordinary_star_magnitude_offset"
                ]
            ),
            milky_way_color=(
                styles["polar_planisphere"]["milky_way_color"]
            ),
            milky_way_opacity=(
                styles["polar_planisphere"]["milky_way_opacity"]
            ),
            magellanic_cloud_color=(
                styles["polar_planisphere"]["magellanic_cloud_color"]
            ),
            lmc_opacity=styles["polar_planisphere"]["lmc_opacity"],
            smc_opacity=styles["polar_planisphere"]["smc_opacity"],
            constellation_line_color=(
                styles["polar_planisphere"][
                    "constellation_line_color"
                ]
            ),
            constellation_linewidth=(
                styles["polar_planisphere"][
                    "constellation_line_width"
                ]
            ),
            constellation_line_opacity=(
                styles["polar_planisphere"][
                    "constellation_line_opacity"
                ]
            ),
            constellation_label_color=(
                styles["polar_planisphere"][
                    "constellation_label_color"
                ]
            ),
            constellation_label_fontsize=(
                styles["polar_planisphere"][
                    "constellation_label_font_size"
                ]
            ),
            constellation_label_opacity=(
                styles["polar_planisphere"][
                    "constellation_label_opacity"
                ]
            ),
            reference_color=(
                styles["polar_planisphere"]["reference_color"]
            ),
            reference_linewidth=(
                styles["polar_planisphere"]["reference_line_width"]
            ),
            reference_opacity=(
                styles["polar_planisphere"]["reference_opacity"]
            ),
            reference_label_fontsize=(
                styles["polar_planisphere"][
                    "reference_label_font_size"
                ]
            ),
            deep_sky_color=(
                styles["polar_planisphere"]["deep_sky_color"]
            ),
            deep_sky_label_fontsize=(
                styles["polar_planisphere"][
                    "deep_sky_label_font_size"
                ]
            ),
            deep_sky_outline_minimum_size_arcmin=(
                styles["polar_planisphere"][
                    "deep_sky_outline_minimum_size_arcmin"
                ]
            ),
            globular_cluster_minimum_size_arcmin=(
                styles["polar_planisphere"][
                    "globular_cluster_minimum_size_arcmin"
                ]
            ),
            boundary_color=(
                styles["polar_planisphere"]["boundary_color"]
            ),
            boundary_linewidth=(
                styles["polar_planisphere"]["boundary_line_width"]
            ),
            boundary_opacity=(
                styles["polar_planisphere"]["boundary_opacity"]
            ),
            calendar_day_label_fontsize=(
                styles["polar_planisphere"][
                    "calendar_day_label_font_size"
                ]
            ),
            calendar_day_label_fontweight=(
                styles["polar_planisphere"][
                    "calendar_day_label_font_weight"
                ]
            ),
            calendar_month_label_fontsize=(
                styles["polar_planisphere"][
                    "calendar_month_label_font_size"
                ]
            ),
            calendar_month_label_fontweight=(
                styles["polar_planisphere"][
                    "calendar_month_label_font_weight"
                ]
            ),
        ),
        print_mode=print_mode,
        presentation_mode=presentation_mode,
        atlas_presentation_palette=_atlas_palette(
            palettes["atlas_presentation"]
        ),
        cartoon_print_palette=_cartoon_palette(palettes["cartoon_print"]),
        cartoon_presentation_palette=_cartoon_palette(
            palettes["cartoon_presentation"]
        ),
        cartoon_label_offset=tuple(cartoon_mode["label_offset"]),
        cartoon_label_clearance=tuple(cartoon_mode["clearance"]),
        cartoon_label_halo_opacity=cartoon_mode["halo_opacity"],
    )


@lru_cache(maxsize=1)
def packaged_style_mode_defaults() -> StyleModeDefaults:
    """Return the immutable packaged style/mode authority once per process."""
    return translate_style_mode_defaults()
