"""Transitional rendering adapter for celestial reference points."""

from __future__ import annotations

import numpy as np

from wenu.projected import ProjectedPoint
from wenu.renderers import layers, render_point, render_text


class CelestialPointsRenderingAdapter:
    def __init__(self, points, observer):
        self.points = points
        self.observer = observer
        self.geometry = None
        self.projected = None
        self.artists = []

    def draw(self, ax, projection):
        self.geometry = self.points.spherical_geometry(self.observer)
        self.projected = projection.project_geometry(self.geometry)
        metadata = self.geometry.metadata
        self.artists = []

        for index in range(len(self.geometry)):
            if (
                self.geometry.lat_deg[index] < 0.0
                or not np.isfinite(self.projected.x[index])
                or not np.isfinite(self.projected.y[index])
            ):
                continue

            style = dict(metadata["style"][index])
            label_offset = style.pop("label_offset", (0.03, 0.03))
            fontsize = style.pop("fontsize", 9)
            zorder = metadata["zorder"][index]
            if zorder is None:
                zorder = layers.POINTS

            projected_point = ProjectedPoint(
                x=self.projected.x[index],
                y=self.projected.y[index],
                name=(
                    None
                    if self.geometry.labels is None
                    else self.geometry.labels[index]
                ),
            )
            self.artists.append(
                render_point(
                    ax,
                    projected_point,
                    marker=metadata["marker"][index],
                    s=metadata["size"][index],
                    color=metadata["color"][index],
                    zorder=zorder,
                    **style,
                )
            )

            label = projected_point.name
            if label is not None:
                dx, dy = label_offset
                self.artists.append(
                    render_text(
                        ax,
                        projected_point.x + dx,
                        projected_point.y + dy,
                        label,
                        fontsize=fontsize,
                        color=metadata["color"][index],
                        ha="left",
                        va="bottom",
                        zorder=zorder,
                    )
                )

        return self.artists
