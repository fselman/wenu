"""Typed, composable configuration for complete chart styles."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite


@dataclass(frozen=True)
class StellarMagnitudeSizing:
    """Configuration of the magnitude-to-scatter-area relation."""

    reference: str = "fixed"
    reference_magnitude: float = 5.0
    scale: float = 1.5
    exponent: float = 0.35
    minimum_area: float = 1.0
    maximum_area: float | None = None

    def __post_init__(self):
        if self.reference not in {"fixed", "limiting_magnitude"}:
            raise ValueError(
                "reference must be 'fixed' or 'limiting_magnitude'."
            )
        for name in (
            "reference_magnitude", "scale", "exponent", "minimum_area"
        ):
            value = float(getattr(self, name))
            if not isfinite(value):
                raise ValueError(f"{name} must be finite.")
        if self.scale <= 0.0 or self.exponent < 0.0:
            raise ValueError(
                "scale must be positive and exponent non-negative."
            )
        if self.minimum_area <= 0.0:
            raise ValueError("minimum_area must be positive.")
        if self.maximum_area is not None:
            maximum = float(self.maximum_area)
            if not isfinite(maximum) or maximum < self.minimum_area:
                raise ValueError(
                    "maximum_area must be finite and at least minimum_area."
                )


@dataclass(frozen=True)
class CanvasStyle:
    """Canvas, foreground, and general label presentation."""

    sky_color: str = "midnightblue"
    foreground_color: str = "white"
    label_fontsize: float = 10.0
    footer_color: str | None = None


@dataclass(frozen=True)
class StellarStyle:
    """Base stars and optional stellar-classification overlays."""

    color: str = "white"
    area_scale: float = 1.0
    magnitude_sizing: StellarMagnitudeSizing = field(
        default_factory=StellarMagnitudeSizing
    )
    draw_bright_symbols: bool = False
    bright_magnitude_limit: float = 0.18
    bright_magnitude_scale: float = 1.0
    bright_magnitude_offset: float = 0.0
    bright_symbol_area_scale: float = 1.0
    ordinary_magnitude_scale: float = 1.0
    ordinary_magnitude_offset: float = 0.0
    bright_color: str | None = None
    bright_alpha: float = 1.0
    draw_variable_symbols: bool = False
    variable_color: str | None = None
    variable_symbol_size: float = 28.0
    variable_linewidth: float = 0.7
    variable_alpha: float = 0.95
    draw_multiple_symbols: bool = False
    multiple_color: str | None = None
    multiple_symbol_size: float = 28.0
    multiple_linewidth: float = 0.7
    multiple_alpha: float = 0.95


@dataclass(frozen=True)
class IsophoteStyle:
    """Milky Way and Magellanic Cloud isophote presentation."""

    milky_way_color: str = "deepskyblue"
    milky_way_alpha: float = 0.10
    milky_way_edge_color: str | None = None
    milky_way_edge_alpha: float = 0.0
    milky_way_linewidth: float = 0.0
    milky_way_contour_color: str | None = None
    milky_way_contour_linestyle: str = ":"
    milky_way_contour_linewidth: float = 0.35
    milky_way_contour_alpha: float = 0.30
    lmc_color: str = "deepskyblue"
    lmc_alpha: float = 0.08
    lmc_edge_color: str | None = None
    lmc_edge_alpha: float = 0.0
    lmc_linewidth: float = 0.0
    lmc_linestyle: str = "-"
    smc_color: str = "deepskyblue"
    smc_alpha: float = 0.06
    smc_edge_color: str | None = None
    smc_edge_alpha: float = 0.0
    smc_linewidth: float = 0.0
    smc_linestyle: str = "-"


@dataclass(frozen=True)
class DeepSkyStyle:
    """Presentation of catalogued nonstellar objects."""

    nonstellar_color: str = "white"
    nonstellar_linewidth: float = 0.8
    nonstellar_alpha: float = 0.9
    nonstellar_minimum_size_arcmin: float | None = 30.0
    nonstellar_draw_labels: bool = False
    nonstellar_label_fontsize: float = 7.0
    nonstellar_symbol_dots: int = 12
    nonstellar_dot_markersize: float = 2.0
    galaxy_edge_color: str = "white"
    galaxy_linewidth: float = 0.7
    galaxy_edge_alpha: float = 0.9
    galaxy_face_color: str | None = None
    galaxy_face_alpha: float = 0.0
    galaxy_minimum_size_arcmin: float | None = 6.0
    galaxy_draw_labels: bool = False
    galaxy_label_color: str | None = None
    galaxy_label_fontsize: float = 6.0
    supernova_remnant_color: str = "orange"
    supernova_remnant_linewidth: float = 0.8
    supernova_remnant_linestyle: str = "--"
    supernova_remnant_alpha: float = 0.9
    supernova_remnant_minimum_size_arcmin: float | None = 10.0
    supernova_remnant_draw_labels: bool = False
    supernova_remnant_label_color: str | None = None
    supernova_remnant_label_fontsize: float = 6.0
    globular_cluster_color: str = "white"
    globular_cluster_linewidth: float = 0.8
    globular_cluster_alpha: float = 0.9
    globular_cluster_minimum_size_arcmin: float | None = 10.0
    globular_cluster_draw_labels: bool = False
    globular_cluster_label_color: str | None = None
    globular_cluster_label_fontsize: float = 6.0
    planetary_nebula_color: str = "white"
    planetary_nebula_face_color: str = "none"
    planetary_nebula_symbol_size: float = 64.0
    planetary_nebula_linewidth: float = 0.8
    planetary_nebula_alpha: float = 0.95
    planetary_nebula_draw_labels: bool = False
    planetary_nebula_label_color: str | None = None
    planetary_nebula_label_fontsize: float = 6.0
    open_cluster_color: str = "white"
    open_cluster_symbol_size: float = 64.0
    open_cluster_linewidth: float = 0.6
    open_cluster_alpha: float = 0.9
    open_cluster_draw_labels: bool = False
    open_cluster_label_color: str | None = None
    open_cluster_label_fontsize: float = 6.0


@dataclass(frozen=True)
class SolarSystemStyle:
    """Symbolic appearance for moving Solar-System objects."""

    venus_color: str = "#8c5a00"
    venus_marker: str = "o"
    venus_symbol_size: float = 10.5
    venus_linewidth: float = 0.8
    venus_alpha: float = 1.0
    venus_draw_label: bool = True
    venus_label_fontsize: float = 7.0
    moon_color: str = "#6f6f6f"
    moon_marker: str = "o"
    moon_symbol_size: float = 42.0
    moon_linewidth: float = 0.8
    moon_alpha: float = 1.0
    moon_draw_label: bool = True
    moon_label_fontsize: float = 7.0
    moon_disk_sequence_label_fontsize: float = 4.5


@dataclass(frozen=True)
class GridStyle:
    """Coordinate grids, celestial references, and boundaries."""

    boundary_color: str = "white"
    boundary_linewidth: float = 0.3
    boundary_linestyle: str = "-"
    boundary_alpha: float = 0.4
    constellation_line_color: str | None = None
    constellation_linewidth: float = 0.4
    constellation_line_alpha: float = 0.7
    constellation_label_color: str | None = None
    constellation_label_alpha: float = 0.85
    constellation_label_offset: tuple[float, float] = (0.0, 0.0)
    constellation_label_offsets: dict[
        str, tuple[float, float]
    ] | None = None
    constellation_label_ha: str = "center"
    constellation_label_va: str = "center"
    equatorial_color: str = "black"
    equatorial_linestyle: str = "-"
    ecliptic_color: str = "orange"
    ecliptic_linestyle: str = "-"
    ecliptic_linewidth: float | None = None
    galactic_color: str = "blue"
    galactic_linestyle: str = "--"
    altaz_color: str = "black"
    altaz_linestyle: str = "-"
    coordinate_linewidth: float = 0.7
    coordinate_alpha: float = 0.75
    draw_coordinate_labels: bool = False
    coordinate_label_color: str | None = None
    coordinate_label_fontsize: float = 6.0
    coordinate_label_alpha: float = 0.8
    horizon_altitude_deg: float = 0.0
    minimum_altitude_deg: float | None = None
    horizon_color: str = "black"
    horizon_linewidth: float = 0.7
    horizon_linestyle: str = "--"
    horizon_alpha: float = 0.8
    horizon_zorder: float = 3.5
    equatorial_reference_linewidth: float | None = None


@dataclass(frozen=True)
class MaskStyle:
    """Outside-region mask presentation."""

    color: str = "black"
    alpha: float = 0.35
    zorder: float = 20.0


@dataclass(frozen=True)
class LegendStyle:
    """Chart legend placement and typography."""

    visible: bool = False
    location: str = "upper right"
    fontsize: float = 6.0
    title_fontsize: float = 6.5
    frame: bool = True
    facecolor: str = "white"
    edgecolor: str = "#777777"
    alpha: float = 0.90
    columns: int = 1
    text_color: str | None = None


@dataclass(frozen=True)
class CalendarStyle:
    """Physical calendar-ring typography for products that draw one."""

    day_label_fontsize: float = 4.3
    day_label_fontweight: str = "normal"
    month_label_fontsize: float = 8.6
    month_label_fontweight: str = "medium"


@dataclass(frozen=True)
class ChartStyle:
    """Complete chart style assembled from focused immutable sections.

    Rendering currently delegates to :class:`PublicationStyle`. This preserves
    the established output while presets migrate to the composed model.
    """

    canvas: CanvasStyle = field(default_factory=CanvasStyle)
    stars: StellarStyle = field(default_factory=StellarStyle)
    isophotes: IsophoteStyle = field(default_factory=IsophoteStyle)
    deep_sky: DeepSkyStyle = field(default_factory=DeepSkyStyle)
    solar_system: SolarSystemStyle = field(default_factory=SolarSystemStyle)
    grids: GridStyle = field(default_factory=GridStyle)
    mask: MaskStyle = field(default_factory=MaskStyle)
    legend: LegendStyle = field(default_factory=LegendStyle)
    calendar: CalendarStyle = field(default_factory=CalendarStyle)

    def as_publication_style(self):
        """Return the equivalent proven flat rendering implementation."""
        from .styles import PublicationStyle

        canvas = self.canvas
        stars = self.stars
        iso = self.isophotes
        deep = self.deep_sky
        solar = self.solar_system
        grids = self.grids
        mask = self.mask
        return PublicationStyle(
            sky_color=canvas.sky_color,
            foreground_color=canvas.foreground_color,
            star_color=stars.color,
            draw_bright_star_symbols=stars.draw_bright_symbols,
            bright_star_magnitude_limit=stars.bright_magnitude_limit,
            bright_star_color=stars.bright_color,
            bright_star_alpha=stars.bright_alpha,
            draw_variable_star_symbols=stars.draw_variable_symbols,
            variable_star_color=stars.variable_color,
            variable_star_symbol_size=stars.variable_symbol_size,
            variable_star_linewidth=stars.variable_linewidth,
            variable_star_alpha=stars.variable_alpha,
            draw_multiple_star_symbols=stars.draw_multiple_symbols,
            multiple_star_color=stars.multiple_color,
            multiple_star_symbol_size=stars.multiple_symbol_size,
            multiple_star_linewidth=stars.multiple_linewidth,
            multiple_star_alpha=stars.multiple_alpha,
            milky_way_color=iso.milky_way_color,
            milky_way_alpha=iso.milky_way_alpha,
            milky_way_edge_color=iso.milky_way_edge_color,
            milky_way_edge_alpha=iso.milky_way_edge_alpha,
            milky_way_linewidth=iso.milky_way_linewidth,
            milky_way_contour_color=iso.milky_way_contour_color,
            milky_way_contour_linestyle=(
                iso.milky_way_contour_linestyle
            ),
            milky_way_contour_linewidth=(
                iso.milky_way_contour_linewidth
            ),
            milky_way_contour_alpha=iso.milky_way_contour_alpha,
            lmc_color=iso.lmc_color,
            lmc_alpha=iso.lmc_alpha,
            lmc_edge_color=iso.lmc_edge_color,
            lmc_edge_alpha=iso.lmc_edge_alpha,
            lmc_linewidth=iso.lmc_linewidth,
            lmc_linestyle=iso.lmc_linestyle,
            smc_color=iso.smc_color,
            smc_alpha=iso.smc_alpha,
            smc_edge_color=iso.smc_edge_color,
            smc_edge_alpha=iso.smc_edge_alpha,
            smc_linewidth=iso.smc_linewidth,
            smc_linestyle=iso.smc_linestyle,
            nonstellar_color=deep.nonstellar_color,
            nonstellar_linewidth=deep.nonstellar_linewidth,
            nonstellar_alpha=deep.nonstellar_alpha,
            nonstellar_minimum_size_arcmin=(
                deep.nonstellar_minimum_size_arcmin
            ),
            nonstellar_draw_labels=deep.nonstellar_draw_labels,
            nonstellar_label_fontsize=deep.nonstellar_label_fontsize,
            nonstellar_symbol_dots=deep.nonstellar_symbol_dots,
            nonstellar_dot_markersize=deep.nonstellar_dot_markersize,
            galaxy_edge_color=deep.galaxy_edge_color,
            galaxy_linewidth=deep.galaxy_linewidth,
            galaxy_edge_alpha=deep.galaxy_edge_alpha,
            galaxy_face_color=deep.galaxy_face_color,
            galaxy_face_alpha=deep.galaxy_face_alpha,
            galaxy_minimum_size_arcmin=deep.galaxy_minimum_size_arcmin,
            galaxy_draw_labels=deep.galaxy_draw_labels,
            galaxy_label_color=deep.galaxy_label_color,
            galaxy_label_fontsize=deep.galaxy_label_fontsize,
            supernova_remnant_color=deep.supernova_remnant_color,
            supernova_remnant_linewidth=(
                deep.supernova_remnant_linewidth
            ),
            supernova_remnant_linestyle=(
                deep.supernova_remnant_linestyle
            ),
            supernova_remnant_alpha=deep.supernova_remnant_alpha,
            supernova_remnant_minimum_size_arcmin=(
                deep.supernova_remnant_minimum_size_arcmin
            ),
            supernova_remnant_draw_labels=(
                deep.supernova_remnant_draw_labels
            ),
            supernova_remnant_label_color=(
                deep.supernova_remnant_label_color
            ),
            supernova_remnant_label_fontsize=(
                deep.supernova_remnant_label_fontsize
            ),
            globular_cluster_color=deep.globular_cluster_color,
            globular_cluster_linewidth=deep.globular_cluster_linewidth,
            globular_cluster_alpha=deep.globular_cluster_alpha,
            globular_cluster_minimum_size_arcmin=(
                deep.globular_cluster_minimum_size_arcmin
            ),
            globular_cluster_draw_labels=(
                deep.globular_cluster_draw_labels
            ),
            globular_cluster_label_color=(
                deep.globular_cluster_label_color
            ),
            globular_cluster_label_fontsize=(
                deep.globular_cluster_label_fontsize
            ),
            planetary_nebula_color=deep.planetary_nebula_color,
            planetary_nebula_face_color=(
                deep.planetary_nebula_face_color
            ),
            planetary_nebula_symbol_size=(
                deep.planetary_nebula_symbol_size
            ),
            planetary_nebula_linewidth=deep.planetary_nebula_linewidth,
            planetary_nebula_alpha=deep.planetary_nebula_alpha,
            planetary_nebula_draw_labels=(
                deep.planetary_nebula_draw_labels
            ),
            planetary_nebula_label_color=(
                deep.planetary_nebula_label_color
            ),
            planetary_nebula_label_fontsize=(
                deep.planetary_nebula_label_fontsize
            ),
            open_cluster_color=deep.open_cluster_color,
            open_cluster_symbol_size=deep.open_cluster_symbol_size,
            open_cluster_linewidth=deep.open_cluster_linewidth,
            open_cluster_alpha=deep.open_cluster_alpha,
            open_cluster_draw_labels=deep.open_cluster_draw_labels,
            open_cluster_label_color=deep.open_cluster_label_color,
            open_cluster_label_fontsize=deep.open_cluster_label_fontsize,
            venus_color=solar.venus_color,
            venus_marker=solar.venus_marker,
            venus_symbol_size=solar.venus_symbol_size,
            venus_linewidth=solar.venus_linewidth,
            venus_alpha=solar.venus_alpha,
            venus_draw_label=solar.venus_draw_label,
            venus_label_fontsize=solar.venus_label_fontsize,
            moon_color=solar.moon_color,
            moon_marker=solar.moon_marker,
            moon_symbol_size=solar.moon_symbol_size,
            moon_linewidth=solar.moon_linewidth,
            moon_alpha=solar.moon_alpha,
            moon_draw_label=solar.moon_draw_label,
            moon_label_fontsize=solar.moon_label_fontsize,
            moon_disk_sequence_label_fontsize=(
                solar.moon_disk_sequence_label_fontsize
            ),
            boundary_color=grids.boundary_color,
            boundary_linewidth=grids.boundary_linewidth,
            boundary_linestyle=grids.boundary_linestyle,
            boundary_alpha=grids.boundary_alpha,
            constellation_line_color=(
                grids.constellation_line_color
            ),
            constellation_linewidth=(
                grids.constellation_linewidth
            ),
            constellation_line_alpha=(
                grids.constellation_line_alpha
            ),
            constellation_label_color=(
                grids.constellation_label_color
            ),
            constellation_label_alpha=(
                grids.constellation_label_alpha
            ),
            constellation_label_offset=(
                grids.constellation_label_offset
            ),
            constellation_label_offsets=(
                grids.constellation_label_offsets
            ),
            constellation_label_ha=grids.constellation_label_ha,
            constellation_label_va=grids.constellation_label_va,
            equatorial_color=grids.equatorial_color,
            equatorial_linestyle=grids.equatorial_linestyle,
            equatorial_reference_linewidth=(
                grids.equatorial_reference_linewidth
            ),
            altaz_color=grids.altaz_color,
            altaz_linestyle=grids.altaz_linestyle,
            horizon_color=grids.horizon_color,
            horizon_linewidth=grids.horizon_linewidth,
            horizon_linestyle=grids.horizon_linestyle,
            horizon_alpha=grids.horizon_alpha,
            horizon_zorder=grids.horizon_zorder,
            ecliptic_color=grids.ecliptic_color,
            ecliptic_linestyle=grids.ecliptic_linestyle,
            ecliptic_linewidth=grids.ecliptic_linewidth,
            galactic_color=grids.galactic_color,
            galactic_linestyle=grids.galactic_linestyle,
            grid_linewidth=grids.coordinate_linewidth,
            grid_alpha=grids.coordinate_alpha,
            grid_draw_labels=grids.draw_coordinate_labels,
            grid_label_color=grids.coordinate_label_color,
            grid_label_fontsize=grids.coordinate_label_fontsize,
            grid_label_alpha=grids.coordinate_label_alpha,
            star_area_scale=stars.area_scale,
            horizon_altitude_deg=grids.horizon_altitude_deg,
            grid_minimum_altitude_deg=grids.minimum_altitude_deg,
            label_fontsize=canvas.label_fontsize,
            outside_mask_color=mask.color,
            outside_mask_alpha=mask.alpha,
            outside_mask_zorder=mask.zorder,
        )

    def configure_axes(self, ax, *, title=None):
        """Apply chart-level axes styling."""
        return self.as_publication_style().configure_axes(
            ax,
            title=title,
        )

    def outside_mask_style(self):
        """Return presentation options for an outside-region mask."""
        return self.as_publication_style().outside_mask_style()

    def horizon_reference_style(self):
        """Return presentation options for the semantic horizon."""
        return self.as_publication_style().horizon_reference_style()

    def layer_options(self, sky, *, horizon_altitude_deg=None):
        """Build renderer options for layers registered in ``sky``."""
        return self.as_publication_style().layer_options(
            sky,
            horizon_altitude_deg=horizon_altitude_deg,
        )
