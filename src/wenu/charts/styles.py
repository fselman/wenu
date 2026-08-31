"""Reusable publication styles for Wenu charts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.rendering import layers
from wenu.rendering.label_placement import CurveLabelPlacement
from wenu.rendering.symbols import DEFAULT_SYMBOLS
from wenu.rendering.preparation import (
    clip_polygons_to_latitude,
    clip_to_latitude,
    magnitude_sizes,
    point_styles,
    radial_label_offset,
)
from wenu.sky.coordinate_grids import CoordinatesGrid


def resolved_outside_mask_style(style=None):
    """Return the one resolved appearance shared by every chart mask."""
    if style is None:
        style = PublicationStyle()
    converter = getattr(style, "as_publication_style", None)
    if callable(converter):
        style = converter()
    factory = getattr(style, "outside_mask_style", None)
    if not callable(factory):
        raise TypeError("style must provide outside_mask_style().")
    return factory()


@dataclass(frozen=True)
class PublicationStyle:
    """Explicit renderer options for publication sky charts."""

    sky_color: str = "midnightblue"
    foreground_color: str = "white"
    star_color: str = "white"
    draw_bright_star_symbols: bool = False
    bright_star_magnitude_limit: float = 0.18
    bright_star_color: str | None = None
    bright_star_alpha: float = 1.0
    draw_variable_star_symbols: bool = False
    variable_star_color: str | None = None
    variable_star_symbol_size: float = 28.0
    variable_star_linewidth: float = 0.7
    variable_star_alpha: float = 0.95
    draw_multiple_star_symbols: bool = False
    multiple_star_color: str | None = None
    multiple_star_symbol_size: float = 28.0
    multiple_star_linewidth: float = 0.7
    multiple_star_alpha: float = 0.95
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
    venus_color: str = "#8c5a00"
    venus_marker: str = "o"
    venus_symbol_size: float = 42.0
    venus_linewidth: float = 0.8
    venus_alpha: float = 1.0
    venus_draw_label: bool = True
    venus_label_fontsize: float = 7.0
    solar_system_track_color: str = "#FFB000"
    solar_system_track_linewidth: float = 1.2
    solar_system_track_linestyle: str = "-"
    solar_system_track_tick_linewidth: float = 1.0
    solar_system_track_label_fontsize: float = 9.0
    moon_color: str = "#6f6f6f"
    moon_marker: str = "o"
    moon_symbol_size: float = 42.0
    moon_linewidth: float = 0.8
    moon_alpha: float = 1.0
    moon_draw_label: bool = True
    moon_label_fontsize: float = 7.0
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
    grid_linewidth: float = 0.7
    grid_alpha: float = 0.75
    grid_draw_labels: bool = False
    grid_label_color: str | None = None
    grid_label_fontsize: float = 6.0
    grid_label_alpha: float = 0.8
    star_area_scale: float = 1.0
    horizon_altitude_deg: float = 0.0
    grid_minimum_altitude_deg: float | None = None
    label_fontsize: float = 10.0
    outside_mask_color: str = "black"
    outside_mask_alpha: float = 0.35
    outside_mask_zorder: float = 20.0
    horizon_color: str = "black"
    horizon_linewidth: float = 0.7
    horizon_linestyle: str = "--"
    horizon_alpha: float = 0.8
    horizon_zorder: float = 3.5
    equatorial_reference_linewidth: float | None = None

    def configure_axes(self, ax, *, title=None):
        """Apply chart-level axes styling."""
        ax.set_facecolor(self.sky_color)
        ax.figure.set_facecolor("white")
        if title is not None:
            ax.set_title(title)
            title_artist = getattr(ax, "title", None)
            set_color = getattr(title_artist, "set_color", None)
            if callable(set_color):
                set_color(self.foreground_color)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        return ax

    def outside_mask_style(self):
        """Return presentation options for an outside-region mask."""
        alpha = float(self.outside_mask_alpha)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(
                "outside_mask_alpha must be between 0 and 1."
            )
        return {
            "facecolor": self.outside_mask_color,
            "edgecolor": "none",
            "alpha": alpha,
            "zorder": float(self.outside_mask_zorder),
        }

    def horizon_reference_style(self):
        """Return presentation options for the semantic horizon."""
        alpha = float(self.horizon_alpha)
        if not 0.0 <= alpha <= 1.0:
            raise ValueError(
                "horizon_alpha must be between 0 and 1."
            )
        return {
            "color": self.horizon_color,
            "linewidth": float(self.horizon_linewidth),
            "linestyle": self.horizon_linestyle,
            "alpha": alpha,
            "zorder": float(self.horizon_zorder),
        }

    def _clip(self, spherical, projected):
        return clip_to_latitude(
            spherical,
            projected,
            minimum=self.horizon_altitude_deg,
        )

    def layer_options(
        self,
        sky,
        *,
        horizon_altitude_deg=None,
    ):
        """Build explicit options for the layers registered in ``sky``."""
        minimum = (
            self.horizon_altitude_deg
            if horizon_altitude_deg is None
            else float(horizon_altitude_deg)
        )
        clip = lambda spherical, projected: clip_to_latitude(
            spherical,
            projected,
            minimum=minimum,
        )
        options = {}
        if getattr(sky, "venus", None) is not None:
            options[sky.venus] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "marker": self.venus_marker,
                        "s": self.venus_symbol_size,
                        "facecolors": "none",
                        "edgecolors": self.venus_color,
                        "linewidths": self.venus_linewidth,
                        "alpha": self.venus_alpha,
                        "zorder": layers.POINTS,
                    },
                    "draw_labels": self.venus_draw_label,
                    "label_style": {
                        "color": self.venus_color,
                        "fontsize": self.venus_label_fontsize,
                        "ha": "center",
                        "va": "bottom",
                        "zorder": layers.LABELS,
                    },
                    "label_offset": (0.0, 0.02),
                },
            }
        if getattr(sky, "moon", None) is not None:
            options[sky.moon] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "marker": self.moon_marker,
                        "s": self.moon_symbol_size,
                        "facecolors": "none",
                        "edgecolors": self.moon_color,
                        "linewidths": self.moon_linewidth,
                        "alpha": self.moon_alpha,
                        "zorder": layers.POINTS,
                    },
                    "draw_labels": self.moon_draw_label,
                    "label_style": {
                        "color": self.moon_color,
                        "fontsize": self.moon_label_fontsize,
                        "ha": "center",
                        "va": "bottom",
                        "zorder": layers.LABELS,
                    },
                    "label_offset": (0.0, 0.02),
                },
            }
        if sky.stars is not None:
            options[sky.stars] = {
                "geometry": {
                    "alt_min": minimum,
                },
                "render": self._star_render_options,
            }
        if sky.nonstellar is not None:
            symbol_dots = int(self.nonstellar_symbol_dots)
            if symbol_dots < 8:
                raise ValueError(
                    "nonstellar_symbol_dots must be at least 8."
                )
            markevery = max(
                1,
                int(sky.nonstellar.samples) // symbol_dots,
            )
            options[sky.nonstellar] = {
                "geometry": {
                    "minimum_size_arcmin": (
                        self.nonstellar_minimum_size_arcmin
                    ),
                },
                "prepare": clip,
                "render": {
                    "style": {
                        "color": self.nonstellar_color,
                        "linewidth": self.nonstellar_linewidth,
                        "linestyle": "None",
                        "marker": ".",
                        "markersize": self.nonstellar_dot_markersize,
                        "markeredgewidth": 0.0,
                        "markevery": markevery,
                        "alpha": self.nonstellar_alpha,
                        "zorder": layers.POINTS,
                    },
                    "draw_labels": self.nonstellar_draw_labels,
                    "label_style": {
                        "color": self.nonstellar_color,
                        "fontsize": (
                            self.nonstellar_label_fontsize
                        ),
                        "ha": "center",
                        "va": "bottom",
                    },
                    "label_offset": (0.0, 0.02),
                },
            }
        if getattr(sky, "milky_way_isophotes", None) is not None:
            milky_way_render = {
                "compound_by": "compound_id",
                "polygon_fill_style": {
                    "facecolor": self.milky_way_color,
                    "face_alpha": self.milky_way_alpha,
                    "edgecolor": "none",
                    "zorder": layers.MILKY_WAY,
                },
            }
            if (
                self.milky_way_edge_color is not None
                and self.milky_way_linewidth > 0.0
            ):
                milky_way_render["polygon_outline_style"] = {
                    "edgecolor": self.milky_way_edge_color,
                    "edge_alpha": self.milky_way_edge_alpha,
                    "linewidth": self.milky_way_linewidth,
                    "zorder": layers.MILKY_WAY,
                }
            if self.milky_way_contour_color is not None:
                milky_way_render["polygon_marker_style"] = {
                    "color": self.milky_way_contour_color,
                    "linestyle": self.milky_way_contour_linestyle,
                    "linewidth": self.milky_way_contour_linewidth,
                    "alpha": self.milky_way_contour_alpha,
                    "zorder": layers.MILKY_WAY + 0.1,
                }
            options[sky.milky_way_isophotes] = {
                "prepare": (
                    lambda spherical, projected:
                    clip_polygons_to_latitude(
                        spherical,
                        projected,
                        minimum=minimum,
                    )
                ),
                "render": milky_way_render,
            }
        for cloud, cloud_layer in getattr(
            sky,
            "magellanic_cloud_isophotes",
            {},
        ).items():
            if cloud == "lmc":
                color = self.lmc_color
                alpha = self.lmc_alpha
                edge_color = self.lmc_edge_color
                edge_alpha = self.lmc_edge_alpha
                linewidth = self.lmc_linewidth
                linestyle = self.lmc_linestyle
            else:
                color = self.smc_color
                alpha = self.smc_alpha
                edge_color = self.smc_edge_color
                edge_alpha = self.smc_edge_alpha
                linewidth = self.smc_linewidth
                linestyle = self.smc_linestyle

            cloud_render = {
                "compound_by": "compound_id",
                "polygon_fill_style": {
                    "facecolor": color,
                    "face_alpha": alpha,
                    "edgecolor": "none",
                    "zorder": layers.MAGELLANIC_CLOUDS,
                },
            }
            if edge_color is not None and linewidth > 0.0:
                cloud_render["polygon_outline_style"] = {
                    "edgecolor": edge_color,
                    "edge_alpha": edge_alpha,
                    "linewidth": linewidth,
                    "linestyle": linestyle,
                    "zorder": layers.MAGELLANIC_CLOUDS,
                }
            options[cloud_layer] = {
                "prepare": (
                    lambda spherical, projected:
                    clip_polygons_to_latitude(
                        spherical,
                        projected,
                        minimum=minimum,
                    )
                ),
                "render": cloud_render,
            }
        if getattr(sky, "galaxies", None) is not None:
            galaxy_render = {
                "polygon_outline_style": {
                    "edgecolor": self.galaxy_edge_color,
                    "edge_alpha": self.galaxy_edge_alpha,
                    "linewidth": self.galaxy_linewidth,
                    "linestyle": "-",
                    "zorder": layers.GALAXIES,
                },
                "draw_labels": self.galaxy_draw_labels,
                "label_style": {
                    "color": (
                        self.galaxy_edge_color
                        if self.galaxy_label_color is None
                        else self.galaxy_label_color
                    ),
                    "fontsize": self.galaxy_label_fontsize,
                    "ha": "center",
                    "va": "bottom",
                    "zorder": layers.GALAXY_LABELS,
                },
                "label_offset": (0.0, 0.015),
            }
            if self.galaxy_face_color is not None:
                galaxy_render["polygon_fill_style"] = {
                    "facecolor": self.galaxy_face_color,
                    "face_alpha": self.galaxy_face_alpha,
                    "zorder": layers.GALAXY_FILLS,
                }
            options[sky.galaxies] = {
                "geometry": {
                    "minimum_size_arcmin": (
                        self.galaxy_minimum_size_arcmin
                    ),
                },
                "prepare": (
                    lambda spherical, projected:
                    clip_polygons_to_latitude(
                        spherical,
                        projected,
                        minimum=minimum,
                    )
                ),
                "render": galaxy_render,
            }


        if getattr(sky, "open_clusters", None) is not None:
            options[sky.open_clusters] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "marker": DEFAULT_SYMBOLS.open_cluster,
                        "s": self.open_cluster_symbol_size,
                        "facecolors": self.open_cluster_color,
                        "edgecolors": self.open_cluster_color,
                        "linewidths": self.open_cluster_linewidth,
                        "alpha": self.open_cluster_alpha,
                        "zorder": layers.OPEN_CLUSTERS,
                    },
                    "draw_labels": self.open_cluster_draw_labels,
                    "label_style": {
                        "color": (
                            self.open_cluster_color
                            if self.open_cluster_label_color is None
                            else self.open_cluster_label_color
                        ),
                        "fontsize": self.open_cluster_label_fontsize,
                        "ha": "center",
                        "va": "bottom",
                        "zorder": layers.OPEN_CLUSTER_LABELS,
                    },
                    "label_offset": (0.0, 0.015),
                },
            }

        if getattr(sky, "planetary_nebulae", None) is not None:
            options[sky.planetary_nebulae] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "marker": DEFAULT_SYMBOLS.planetary_nebula,
                        "s": self.planetary_nebula_symbol_size,
                        "facecolors": self.planetary_nebula_face_color,
                        "edgecolors": self.planetary_nebula_color,
                        "linewidths": self.planetary_nebula_linewidth,
                        "alpha": self.planetary_nebula_alpha,
                        "zorder": layers.PLANETARY_NEBULAE,
                    },
                    "draw_labels": self.planetary_nebula_draw_labels,
                    "label_style": {
                        "color": (
                            self.planetary_nebula_color
                            if self.planetary_nebula_label_color is None
                            else self.planetary_nebula_label_color
                        ),
                        "fontsize": (
                            self.planetary_nebula_label_fontsize
                        ),
                        "ha": "center",
                        "va": "bottom",
                        "zorder": layers.PLANETARY_NEBULA_LABELS,
                    },
                    "label_offset": (0.0, 0.015),
                },
            }
        if getattr(
            sky,
            "supernova_remnants",
            None,
        ) is not None:
            options[sky.supernova_remnants] = {
                "geometry": {
                    "minimum_size_arcmin": (
                        self.supernova_remnant_minimum_size_arcmin
                    ),
                },
                "prepare": clip,
                "render": {
                    "style": {
                        "color": self.supernova_remnant_color,
                        "linewidth": (
                            self.supernova_remnant_linewidth
                        ),
                        "linestyle": (
                            self.supernova_remnant_linestyle
                        ),
                        "alpha": self.supernova_remnant_alpha,
                        "zorder": layers.SUPERNOVA_REMNANTS,
                    },
                    "draw_labels": (
                        self.supernova_remnant_draw_labels
                    ),
                    "label_style": {
                        "color": (
                            self.supernova_remnant_color
                            if self.supernova_remnant_label_color
                            is None
                            else self.supernova_remnant_label_color
                        ),
                        "fontsize": (
                            self.supernova_remnant_label_fontsize
                        ),
                        "ha": "center",
                        "va": "bottom",
                        "zorder": (
                            layers.SUPERNOVA_REMNANT_LABELS
                        ),
                    },
                    "label_offset": (0.0, 0.015),
                },
            }
        if getattr(sky, "globular_clusters", None) is not None:
            options[sky.globular_clusters] = {
                "geometry": {
                    "minimum_size_arcmin": (
                        self.globular_cluster_minimum_size_arcmin
                    ),
                },
                "prepare": clip,
                "render": {
                    "style": {
                        "color": self.globular_cluster_color,
                        "linewidth": (
                            self.globular_cluster_linewidth
                        ),
                        "linestyle": "-",
                        "alpha": self.globular_cluster_alpha,
                        "zorder": layers.GLOBULAR_CLUSTERS,
                    },
                    "draw_labels": (
                        self.globular_cluster_draw_labels
                    ),
                    "label_style": {
                        "color": (
                            self.globular_cluster_color
                            if self.globular_cluster_label_color
                            is None
                            else self.globular_cluster_label_color
                        ),
                        "fontsize": (
                            self.globular_cluster_label_fontsize
                        ),
                        "ha": "center",
                        "va": "bottom",
                        "zorder": (
                            layers.GLOBULAR_CLUSTER_LABELS
                        ),
                    },
                    "label_offset": (0.0, 0.015),
                },
            }
        if sky.constellation_lines is not None:
            options[sky.constellation_lines] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "color": (
                            self.foreground_color
                            if self.constellation_line_color is None
                            else self.constellation_line_color
                        ),
                        "linewidth": self.constellation_linewidth,
                        "alpha": self.constellation_line_alpha,
                        "zorder": 2,
                    }
                },
            }
        if sky.constellation_labels is not None:
            options[sky.constellation_labels] = {
                "prepare": clip,
                "render": {
                    "draw_markers": False,
                    "draw_labels": True,
                    "label_style": {
                        "color": (
                            self.foreground_color
                            if self.constellation_label_color is None
                            else self.constellation_label_color
                        ),
                        "fontsize": self.label_fontsize,
                        "ha": self.constellation_label_ha,
                        "va": self.constellation_label_va,
                        "alpha": self.constellation_label_alpha,
                        "zorder": 5,
                    },
                    "label_offset": {
                        "__default__": self.constellation_label_offset,
                        **dict(self.constellation_label_offsets or {}),
                    },
                },
            }
        if sky.constellation_boundaries is not None:
            options[sky.constellation_boundaries] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "color": self.boundary_color,
                        "linewidth": self.boundary_linewidth,
                        "linestyle": self.boundary_linestyle,
                        "alpha": self.boundary_alpha,
                        "zorder": 1,
                    }
                },
            }
        if sky.points is not None:
            options[sky.points] = {
                "prepare": clip,
                "render": lambda spherical, projected: {
                    "styles": point_styles(
                        spherical.metadata,
                        default_zorder=layers.POINTS,
                    ),
                    "draw_labels": True,
                    "label_style": {
                        "fontsize": 9,
                        "ha": "left",
                        "va": "bottom",
                    },
                    "label_offset": (0.03, 0.03),
                },
            }
        for layer in sky.layers:
            if isinstance(layer, CoordinatesGrid):
                options[layer] = self._grid_options(
                    layer,
                    minimum=horizon_altitude_deg,
                )
        horizon = getattr(sky, "horizon_reference", None)
        if horizon is not None:
            options[horizon] = {
                "render": {
                    "style": self.horizon_reference_style(),
                },
            }
        return options

    def _star_render_options(
        self,
        spherical,
        projected,
        *,
        star_sizes=None,
        bright_star_sizes=None,
    ):
        """Return one base scatter plus optional vectorized overlays."""
        overlays = []
        if self.draw_bright_star_symbols:
            bright = (
                np.asarray(spherical.metadata["magnitude"], dtype=float)
                <= self.bright_star_magnitude_limit
            )
            overlays.append(
                {
                    "mask": bright,
                    "style": {
                        "marker": DEFAULT_SYMBOLS.filled_five_point_star,
                        "s": (
                            magnitude_sizes(
                                spherical.metadata["magnitude"]
                            )
                            if bright_star_sizes is None
                            else bright_star_sizes
                        ),
                        "facecolors": (
                            self.star_color
                            if self.bright_star_color is None
                            else self.bright_star_color
                        ),
                        "edgecolors": "none",
                        "alpha": self.bright_star_alpha,
                        "zorder": layers.BRIGHT_STARS,
                    },
                }
            )
        if self.draw_multiple_star_symbols:
            overlays.append(
                {
                    "mask": spherical.metadata["is_multiple"],
                    "style": {
                        "marker": DEFAULT_SYMBOLS.multiple_star,
                        "s": self.multiple_star_symbol_size,
                        "facecolors": "none",
                        "edgecolors": (
                            self.star_color
                            if self.multiple_star_color is None
                            else self.multiple_star_color
                        ),
                        "linewidths": self.multiple_star_linewidth,
                        "alpha": self.multiple_star_alpha,
                        "zorder": layers.MULTIPLE_STARS,
                    },
                }
            )
        if self.draw_variable_star_symbols:
            overlays.append(
                {
                    "mask": spherical.metadata["is_variable"],
                    "style": {
                        "marker": DEFAULT_SYMBOLS.variable_star,
                        "s": self.variable_star_symbol_size,
                        "facecolors": "none",
                        "edgecolors": (
                            self.star_color
                            if self.variable_star_color is None
                            else self.variable_star_color
                        ),
                        "linewidths": self.variable_star_linewidth,
                        "alpha": self.variable_star_alpha,
                        "zorder": layers.VARIABLE_STARS,
                    },
                }
            )
        return {
            "style": {
                "s": (
                    magnitude_sizes(spherical.metadata["magnitude"])
                    * self.star_area_scale
                    if star_sizes is None
                    else star_sizes
                ),
                "c": self.star_color,
                "linewidths": 0,
                "zorder": layers.STARS,
            },
            "point_overlays": overlays,
        }

    def _grid_options(self, layer, *, minimum=None):
        system = layer.coordinate_system
        if system == "altaz":
            color = self.altaz_color
            linestyle = self.altaz_linestyle
        elif system == "equatorial":
            color = self.equatorial_color
            linestyle = self.equatorial_linestyle
        elif system == "ecliptic":
            color = self.ecliptic_color
            linestyle = self.ecliptic_linestyle
        else:
            color = self.galactic_color
            linestyle = self.galactic_linestyle
        linewidth = (
            self.grid_linewidth
            if system != "ecliptic" or self.ecliptic_linewidth is None
            else self.ecliptic_linewidth
        )
        options = {
            "render": {
                "style": {
                    "color": color,
                    "linewidth": linewidth,
                    "linestyle": linestyle,
                    "alpha": self.grid_alpha,
                    "zorder": 3,
                },
                "draw_labels": self.grid_draw_labels,
                "label_style": {
                    "color": (
                        color
                        if self.grid_label_color is None
                        else self.grid_label_color
                    ),
                    "fontsize": self.grid_label_fontsize,
                    "alpha": self.grid_label_alpha,
                    "ha": "center",
                    "va": "center",
                    "zorder": 4,
                },
                "label_formatter": self._coordinate_label,
                "label_anchor": self._coordinate_label_anchor,
            },
        }
        if minimum is None:
            minimum = self.grid_minimum_altitude_deg
        if minimum is not None:
            minimum = float(minimum)
            options["prepare"] = (
                lambda spherical, projected: clip_to_latitude(
                    spherical,
                    projected,
                    minimum=minimum,
                )
            )
        return options

    @staticmethod
    def _coordinate_label(name):
        if name.startswith("right_ascension_"):
            degrees = float(name.removeprefix("right_ascension_"))
            total_minutes = round((degrees % 360.0) * 4.0) % (24 * 60)
            hours, minutes = divmod(total_minutes, 60)
            return f"{hours:02d}:{minutes:02d}"
        if name.startswith("declination_"):
            degrees = float(name.removeprefix("declination_"))
            total_minutes = round(abs(degrees) * 60.0)
            whole_degrees, minutes = divmod(total_minutes, 60)
            sign = "+" if degrees >= 0.0 else "-"
            return f"{sign}{whole_degrees:02d}:{minutes:02d}"
        for prefix in (
            "azimuth_",
            "ecliptic_longitude_",
            "galactic_longitude_",
        ):
            if name.startswith(prefix):
                degrees = float(name.removeprefix(prefix)) % 360.0
                return f"{degrees:g}°"
        for prefix in (
            "altitude_",
            "ecliptic_latitude_",
            "galactic_latitude_",
        ):
            if name.startswith(prefix):
                degrees = float(name.removeprefix(prefix))
                return f"{degrees:+g}°"
        return name

    @staticmethod
    def _coordinate_label_anchor(curve, ax):
        finite = curve.finite
        if not np.any(finite):
            return None
        x = curve.x[finite]
        y = curve.y[finite]
        x_min, x_max = sorted(ax.get_xlim())
        y_min, y_max = sorted(ax.get_ylim())
        inside = (
            (x >= x_min)
            & (x <= x_max)
            & (y >= y_min)
            & (y <= y_max)
        )
        if not np.any(inside):
            return None
        x = x[inside]
        y = y[inside]
        meridian_prefixes = (
            "azimuth_",
            "right_ascension_",
            "ecliptic_longitude_",
            "galactic_longitude_",
        )
        if curve.name.startswith(meridian_prefixes):
            index = int(np.argmin(np.abs(y - y_min)))
            return x[index], y_min + 0.018 * (y_max - y_min)
        index = int(np.argmin(np.abs(x - x_min)))
        return CurveLabelPlacement(
            x_min + 0.012 * (x_max - x_min),
            y[index],
            rotation_deg=0.0,
            normal_offset_em=0.65,
        )
