from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Viewport:
    """
    Rectangular visible region in projected Cartesian coordinates.

    A viewport has no knowledge of astronomical coordinate systems,
    spherical rotations, map projections, observers, or rendering
    libraries. It only describes a rectangular region in the projected
    plane.

    Parameters
    ----------
    x_min, x_max
        Horizontal bounds in projected coordinates.

    y_min, y_max
        Vertical bounds in projected coordinates.
    """

    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def __post_init__(self) -> None:
        bounds = np.asarray(
            [
                self.x_min,
                self.x_max,
                self.y_min,
                self.y_max,
            ],
            dtype=float,
        )

        if not np.all(np.isfinite(bounds)):
            raise ValueError(
                "Viewport bounds must be finite."
            )

        if self.x_min >= self.x_max:
            raise ValueError(
                "x_min must be smaller than x_max."
            )

        if self.y_min >= self.y_max:
            raise ValueError(
                "y_min must be smaller than y_max."
            )

    @classmethod
    def centered(
        cls,
        *,
        width: float,
        height: float,
        center_x: float = 0.0,
        center_y: float = 0.0,
    ) -> "Viewport":
        """
        Construct a viewport from its center, width, and height.
        """
        width = float(width)
        height = float(height)
        center_x = float(center_x)
        center_y = float(center_y)

        if not np.isfinite(width) or width <= 0.0:
            raise ValueError(
                "width must be a positive finite number."
            )

        if not np.isfinite(height) or height <= 0.0:
            raise ValueError(
                "height must be a positive finite number."
            )

        if not np.isfinite(center_x):
            raise ValueError(
                "center_x must be finite."
            )

        if not np.isfinite(center_y):
            raise ValueError(
                "center_y must be finite."
            )

        half_width = width / 2.0
        half_height = height / 2.0

        return cls(
            x_min=center_x - half_width,
            x_max=center_x + half_width,
            y_min=center_y - half_height,
            y_max=center_y + half_height,
        )

    @property
    def width(self) -> float:
        """
        Width of the viewport in projected coordinates.
        """
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """
        Height of the viewport in projected coordinates.
        """
        return self.y_max - self.y_min

    @property
    def center_x(self) -> float:
        """
        Horizontal center of the viewport.
        """
        return (self.x_min + self.x_max) / 2.0

    @property
    def center_y(self) -> float:
        """
        Vertical center of the viewport.
        """
        return (self.y_min + self.y_max) / 2.0

    @property
    def center(self) -> tuple[float, float]:
        """
        Viewport center as ``(x, y)``.
        """
        return self.center_x, self.center_y

    @property
    def aspect_ratio(self) -> float:
        """
        Width divided by height.
        """
        return self.width / self.height

    @property
    def xlim(self) -> tuple[float, float]:
        """
        Horizontal plotting limits.
        """
        return self.x_min, self.x_max

    @property
    def ylim(self) -> tuple[float, float]:
        """
        Vertical plotting limits.
        """
        return self.y_min, self.y_max

    def contains(
        self,
        x,
        y,
        *,
        include_boundary: bool = True,
    ) -> np.ndarray:
        """
        Return whether projected points lie inside the viewport.

        Parameters
        ----------
        x, y
            Scalar or array-like projected coordinates. Inputs are
            broadcast using NumPy broadcasting rules.

        include_boundary
            Whether points on the viewport boundary are considered
            inside.

        Returns
        -------
        numpy.ndarray
            Boolean scalar or array matching the broadcast input shape.
        """
        x, y = np.broadcast_arrays(
            np.asarray(x, dtype=float),
            np.asarray(y, dtype=float),
        )

        finite = np.isfinite(x) & np.isfinite(y)

        if include_boundary:
            inside = (
                (x >= self.x_min)
                & (x <= self.x_max)
                & (y >= self.y_min)
                & (y <= self.y_max)
            )
        else:
            inside = (
                (x > self.x_min)
                & (x < self.x_max)
                & (y > self.y_min)
                & (y < self.y_max)
            )

        return finite & inside


