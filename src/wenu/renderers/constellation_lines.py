"""Transitional renderer for constellation-line spherical geometry."""

from __future__ import annotations

import numpy as np

from wenu.renderers import render_curve


class ConstellationLinesRenderingAdapter:
    """Project and render observer-time constellation-line geometry."""

    def __init__(
        self,
        lines,
        observer,
        *,
        color="white",
        linewidth=0.4,
        alpha=0.7,
        zorder=2,
        horizon_altitude=0.0,
        max_segment_length=None,
    ):
        self.lines = lines
        self.observer = observer
        self.color = color
        self.linewidth = linewidth
        self.alpha = alpha
        self.zorder = zorder
        self.horizon_altitude = float(horizon_altitude)
        self.max_segment_length = max_segment_length
        self.geometry = None
        self.projected = None
        self.artists = []

    def draw(self, ax, projection, **style):
        """Generate geometry, project the collection once, and render it."""
        self.geometry = self.lines.spherical_geometry(self.observer)
        self.projected = projection.project_geometry(self.geometry)
        resolved_style = {
            "color": self.color,
            "linewidth": self.linewidth,
            "alpha": self.alpha,
            "zorder": self.zorder,
            **style,
        }
        max_segment_length = resolved_style.pop(
            "max_segment_length",
            self.max_segment_length,
        )
        horizon_altitude = float(
            resolved_style.pop(
                "horizon_altitude",
                self.horizon_altitude,
            )
        )
        self.artists = []

        for altitude, projected in zip(
            self.geometry.lat_deg,
            self.projected,
        ):
            altitude = np.asarray(altitude, dtype=float)
            if (
                altitude.size != 2
                or np.any(altitude <= horizon_altitude)
                or not np.all(
                    np.isfinite(
                        [
                            projected.x[0],
                            projected.y[0],
                            projected.x[1],
                            projected.y[1],
                        ]
                    )
                )
            ):
                continue

            if max_segment_length is not None:
                length = np.hypot(
                    projected.x[1] - projected.x[0],
                    projected.y[1] - projected.y[0],
                )
                if length > max_segment_length:
                    continue

            self.artists.append(
                render_curve(ax, projected, **resolved_style)
            )

        return self.artists

