"""Temporary rendering adapter for constellation-boundary geometry."""

from __future__ import annotations

import numpy as np

from wenu.projected import ProjectedCurve
from wenu.renderers import render_curve


class ConstellationBoundaryRenderingAdapter:
    """Render boundary outlines while their consumers are migrated."""

    def __init__(
        self,
        boundaries,
        observer,
        *,
        color="white",
        linewidth=0.3,
        alpha=0.4,
        zorder=1,
        horizon_altitude=0.0,
    ):
        self.boundaries = boundaries
        self.observer = observer
        self.color = color
        self.linewidth = linewidth
        self.alpha = alpha
        self.zorder = zorder
        self.horizon_altitude = float(horizon_altitude)
        self.geometry = None
        self.projected = None
        self.artists = []

    def draw(self, ax, projection, **style):
        self.geometry = self.boundaries.spherical_geometry(
            self.observer
        )
        self.projected = projection.project_geometry(self.geometry)
        resolved_style = {
            "color": self.color,
            "linewidth": self.linewidth,
            "alpha": self.alpha,
            "zorder": self.zorder,
            **style,
        }
        self.artists = []

        for spherical, projected in zip(
            self.geometry.lat_deg,
            self.projected,
        ):
            for segment_x, segment_y in self._visible_segments(
                x=projected.x,
                y=projected.y,
                altitude=spherical,
            ):
                self.artists.append(
                    render_curve(
                        ax,
                        ProjectedCurve(
                            x=segment_x,
                            y=segment_y,
                        ),
                        **resolved_style,
                    )
                )

        return self.artists

    def _visible_segments(self, x, y, altitude):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        altitude = np.asarray(altitude, dtype=float)
        visible = (
            np.isfinite(x)
            & np.isfinite(y)
            & np.isfinite(altitude)
            & (altitude >= self.horizon_altitude)
        )
        segments = []
        start = None

        for index, is_visible in enumerate(visible):
            if is_visible and start is None:
                start = index
            if not is_visible and start is not None:
                if index - start >= 2:
                    segments.append((x[start:index], y[start:index]))
                start = None

        if start is not None and len(x) - start >= 2:
            segments.append((x[start:], y[start:]))
        return segments
