# src/wenu/sky/curves.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from wenu.renderers import render_curve
from wenu.visibility import visibility_mask

@dataclass
class CelestialCurve:
    """
    A sampled curve on the apparent celestial sphere.

    The curve stores horizontal coordinates and delegates projection to the
    projection object and drawing to the renderer.

    Parameters
    ----------
    alt_deg, az_deg
        One-dimensional arrays of altitude and azimuth in degrees.
    name
        Optional curve identifier.
    closed
        Whether the curve is geometrically closed.
    style
        Default keyword arguments passed to ``render_curve``.
    """

    alt_deg: np.ndarray
    az_deg: np.ndarray
    name: str | None = None
    closed: bool = False
    style: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.alt_deg = np.asarray(self.alt_deg, dtype=float)
        self.az_deg = np.asarray(self.az_deg, dtype=float)

        if self.alt_deg.ndim != 1 or self.az_deg.ndim != 1:
            raise ValueError(
                "alt_deg and az_deg must be one-dimensional arrays."
            )

        if self.alt_deg.shape != self.az_deg.shape:
            raise ValueError(
                "alt_deg and az_deg must have the same shape."
            )

        if self.alt_deg.size < 2:
            raise ValueError(
                "A celestial curve requires at least two samples."
            )

    @classmethod
    def from_spherical(
        cls,
        lon_deg,
        lat_deg,
        *,
        frame,
        name: str | None = None,
        closed: bool = False,
        style: dict[str, Any] | None = None,
    ) -> "CelestialCurve":
        """
        Build a horizontal celestial curve from generic spherical coordinates.

        The supplied frame converts generic spherical longitude and latitude
        into the horizontal longitude/latitude convention used by Wenu:

        - transformed longitude becomes azimuth
        - transformed latitude becomes altitude
        """
        coordinates = frame.transform(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
        )

        return cls(
            alt_deg=coordinates.lat_deg,
            az_deg=coordinates.lon_deg,
            name=name,
            closed=closed,
            style={} if style is None else style,
        )

    def draw(
        self,
        ax,
        projection,
        *,
        min_altitude: float = 0.0,
        **style: Any,
    ):
        """
        Project and render the visible portions of the curve.

        The projection performs the Cartesian transformation and visibility
        segmentation. The renderer creates the Matplotlib artists.

        Styles supplied here override the defaults stored in ``self.style``.
        """
        alt_deg, az_deg = self._drawing_samples(
            min_altitude=min_altitude
        )

        projected_curves = projection.project_curve(
            lon_deg=az_deg,
            lat_deg=alt_deg,
            closed=False,
            name=self.name,
            min_altitude=min_altitude,
        )

        plot_style = {
            **self.style,
            **style,
        }

        return [
            render_curve(
                ax,
                projected_curve,
                **plot_style,
            )
            for projected_curve in projected_curves
        ]


    def _drawing_samples(
        self,
        *,
        min_altitude: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Arrange samples of a closed curve so that a visible arc is not split
        between the beginning and end of the arrays.

        This method only reorders the samples. It does not clip or segment
        the curve.
        """
        alt_deg = self.alt_deg
        az_deg = self.az_deg

        if not self.closed:
            return alt_deg, az_deg

        visible = visibility_mask(
            alt_deg,
            min_altitude=min_altitude,
        )

        if not np.any(visible):
            return alt_deg, az_deg

        if np.all(visible):
            return (
                np.append(alt_deg, alt_deg[0]),
                np.append(az_deg, az_deg[0]),
            )

        # Start inside an invisible part of the curve. This prevents a
        # visible segment from being divided between the beginning and end
        # of the sample arrays.
        invisible_indices = np.flatnonzero(~visible)
        start = int(invisible_indices[0])

        return (
            np.roll(alt_deg, -start),
            np.roll(az_deg, -start),
        )
