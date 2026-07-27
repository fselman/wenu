"""Reusable publication styles for Wenu charts."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.rendering import layers
from wenu.rendering.symbols import DEFAULT_SYMBOLS
from wenu.rendering.preparation import (
    clip_polygons_to_latitude,
    clip_to_latitude,
    magnitude_sizes,
    point_styles,
    radial_label_offset,
)
from wenu.sky.coordinate_grids import CoordinatesGrid


@dataclass(frozen=True)
class PublicationStyle:
    """Explicit renderer options for publication sky charts."""

    sky_color: str = "midnightblue"
    foreground_color: str = "white"
    star_color: str = "white"
    milky_way_color: str = "deepskyblue"
    milky_way_alpha: float = 0.10
    milky_way_edge_color: str | None = None
    milky_way_edge_alpha: float = 0.0
    milky_way_linewidth: float = 0.0
    lmc_color: str = "deepskyblue"
    lmc_alpha: float = 0.08
    lmc_edge_color: str | None = None
    lmc_edge_alpha: float = 0.0
    lmc_linewidth: float = 0.0
    smc_color: str = "deepskyblue"
    smc_alpha: float = 0.06
    smc_edge_color: str | None = None
    smc_edge_alpha: float = 0.0
    smc_linewidth: float = 0.0
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
    boundary_color: str = "white"
    equatorial_color: str = "deepskyblue"
    ecliptic_color: str = "gold"
    galactic_color: str = "white"
    star_area_scale: float = 1.0
    horizon_altitude_deg: float = 0.0
    grid_minimum_altitude_deg: float | None = None
    label_fontsize: float = 10.0
    outside_mask_color: str = "black"
    outside_mask_alpha: float = 0.35
    outside_mask_zorder: float = 20.0

    def configure_axes(self, ax, *, title=None):
        """Apply chart-level axes styling."""
        ax.set_facecolor(self.sky_color)
        ax.figure.set_facecolor("white")
        if title is not None:
            ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
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
        if sky.stars is not None:
            options[sky.stars] = {
                "geometry": {
                    "alt_min": minimum,
                },
                "render": lambda spherical, projected: {
                    "style": {
                        "s": magnitude_sizes(
                            spherical.metadata["magnitude"]
                        ) * self.star_area_scale,
                        "c": self.star_color,
                        "linewidths": 0,
                        "zorder": layers.STARS,
                    }
                },
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
            else:
                color = self.smc_color
                alpha = self.smc_alpha
                edge_color = self.smc_edge_color
                edge_alpha = self.smc_edge_alpha
                linewidth = self.smc_linewidth

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
                        "color": self.foreground_color,
                        "linewidth": 0.4,
                        "alpha": 0.7,
                        "zorder": 2,
                    }
                },
            }
        if sky.constellation_labels is not None:
            options[sky.constellation_labels] = {
                "prepare": clip,
                "render": {
                    "style": {"s": 0.0},
                    "draw_labels": True,
                    "label_style": {
                        "color": self.foreground_color,
                        "fontsize": self.label_fontsize,
                        "ha": "center",
                        "va": "center",
                        "alpha": 0.85,
                        "zorder": 5,
                    },
                    "label_offset": radial_label_offset(0.04),
                },
            }
        if sky.constellation_boundaries is not None:
            options[sky.constellation_boundaries] = {
                "prepare": clip,
                "render": {
                    "style": {
                        "color": self.boundary_color,
                        "linewidth": 0.3,
                        "alpha": 0.4,
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
        return options

    def _grid_options(self, layer, *, minimum=None):
        system = layer.coordinate_system
        if system == "equatorial":
            color = self.equatorial_color
            linestyle = "-"
        elif system == "ecliptic":
            color = self.ecliptic_color
            linestyle = "-"
        else:
            color = self.galactic_color
            linestyle = "--"
        options = {
            "render": {
                "style": {
                    "color": color,
                    "linewidth": 0.7,
                    "linestyle": linestyle,
                    "alpha": 0.75,
                    "zorder": 3,
                }
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
