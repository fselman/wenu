"""Transitional renderer for coordinate-grid geometry."""

from __future__ import annotations

import numpy as np

from wenu.projected import ProjectedCurve
from wenu.renderers import render_curve


class CoordinatesGridRenderingAdapter:
    """Project coordinate collections once, clip them, and render curves."""

    def __init__(self, observer):
        self.observer = observer
        self.geometry = None
        self.projected = None
        self.artists = []

    def draw_curves(
        self,
        ax,
        projection,
        geometry,
        *,
        min_altitude=0.0,
        **style,
    ):
        self.geometry = geometry
        self.projected = projection.project_geometry(geometry)
        self.artists = self._render_curves(
            ax,
            geometry,
            self.projected,
            min_altitude=min_altitude,
            common_style=style,
        )
        return self.artists

    def draw_grid(
        self,
        ax,
        projection,
        geometry,
        *,
        min_altitude=0.0,
        **style,
    ):
        self.geometry = geometry
        self.projected = projection.project_geometry(geometry)
        self.artists = []
        for name, spherical in geometry.components.items():
            self.artists.extend(
                self._render_curves(
                    ax,
                    spherical,
                    self.projected[name],
                    min_altitude=min_altitude,
                    common_style=style,
                )
            )
        return self.artists

    def _render_curves(
        self,
        ax,
        spherical,
        projected,
        *,
        min_altitude,
        common_style,
    ):
        artists = []
        styles = spherical.metadata.get(
            "styles",
            tuple({} for _ in range(len(spherical))),
        )
        for index, (altitude, curve) in enumerate(
            zip(spherical.lat_deg, projected)
        ):
            resolved_style = {
                **common_style,
                **dict(styles[index]),
            }
            for x, y in self._visible_segments(
                curve.x,
                curve.y,
                altitude,
                closed=bool(spherical.closed[index]),
                min_altitude=min_altitude,
            ):
                artists.append(
                    render_curve(
                        ax,
                        ProjectedCurve(x=x, y=y),
                        **resolved_style,
                    )
                )
        return artists

    @staticmethod
    def _visible_segments(
        x,
        y,
        altitude,
        *,
        closed,
        min_altitude,
    ):
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)
        altitude = np.asarray(altitude, dtype=float)
        visible = (
            np.isfinite(x)
            & np.isfinite(y)
            & np.isfinite(altitude)
            & (altitude >= float(min_altitude))
        )
        if not np.any(visible):
            return []

        if closed:
            if np.all(visible):
                return [
                    (
                        np.append(x, x[0]),
                        np.append(y, y[0]),
                    )
                ]
            # Rotate immediately after an invisible sample so a visible run
            # crossing the array seam remains contiguous.
            first_hidden = int(np.flatnonzero(~visible)[0])
            order = (
                np.arange(len(x), dtype=int) + first_hidden + 1
            ) % len(x)
            x = x[order]
            y = y[order]
            visible = visible[order]

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

