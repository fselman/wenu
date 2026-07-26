"""Reusable publication styles for Wenu charts."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.rendering import layers
from wenu.rendering.preparation import (
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
    nonstellar_color: str = "white"
    nonstellar_linewidth: float = 0.8
    nonstellar_alpha: float = 0.9
    nonstellar_minimum_size_arcmin: float | None = 30.0
    nonstellar_draw_labels: bool = False
    nonstellar_label_fontsize: float = 7.0
    nonstellar_symbol_dots: int = 12
    nonstellar_dot_markersize: float = 2.0
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
