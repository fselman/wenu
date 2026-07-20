# src/wenu/sky/curves.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CelestialCurve:
    """
    A sampled curve on the apparent celestial sphere.

    The curve stores horizontal coordinates but delegates projection,
    clipping, segmentation, and Matplotlib drawing to the projection.

    Parameters
    ----------
    alt_deg, az_deg
        One-dimensional arrays of altitude and azimuth in degrees.
    name
        Optional curve identifier.
    closed
        Whether the curve is geometrically closed.
    style
        Default keyword arguments passed to ``projection.draw_curve``.
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

    def draw(
        self,
        ax,
        projection,
        *,
        min_altitude: float = 0.0,
        **style: Any,
    ):
        """
        Draw the curve using the supplied projection.

        Styles supplied here override the defaults stored in ``self.style``.
        """
        alt_deg, az_deg = self._drawing_samples(
            min_altitude=min_altitude
        )

        plot_style = {
            **self.style,
            **style,
        }

        return projection.draw_curve(
            ax=ax,
            alt_deg=alt_deg,
            az_deg=az_deg,
            min_altitude=min_altitude,
            **plot_style,
        )

    def _drawing_samples(
        self,
        *,
        min_altitude: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Arrange samples so a closed curve does not break unnecessarily
        at the array boundary.

        Actual visibility clipping remains the projection's responsibility.
        """
        alt_deg = self.alt_deg
        az_deg = self.az_deg

        if not self.closed:
            return alt_deg, az_deg

        visible = alt_deg > min_altitude

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
