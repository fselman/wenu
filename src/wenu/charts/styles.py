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
    boundary_color: str = "white"
    equatorial_color: str = "deepskyblue"
    ecliptic_color: str = "gold"
    galactic_color: str = "white"
    star_area_scale: float = 1.0
    horizon_altitude_deg: float = 0.0
    grid_minimum_altitude_deg: float | None = None
    label_fontsize: float = 10.0

    def configure_axes(self, ax, *, title=None):
        """Apply chart-level axes styling."""
        ax.set_facecolor(self.sky_color)
        ax.figure.set_facecolor("white")
        if title is not None:
            ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        return ax

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
