# src/wenu/projected.py

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _coordinate_array(values, *, name: str) -> np.ndarray:
    """
    Convert Cartesian coordinate values to a one-dimensional float array.
    """
    array = np.asarray(values, dtype=float)

    if array.ndim != 1:
        raise ValueError(
            f"{name} must be a one-dimensional array."
        )

    return array


@dataclass
class ProjectedPoint:
    """
    A point in projected Cartesian coordinates.

    This class contains no information about the spherical coordinate
    system, observer, projection, or renderer that produced the point.
    """

    x: float
    y: float
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = float(self.x)
        self.y = float(self.y)

    @property
    def finite(self) -> bool:
        """
        Whether both projected coordinates are finite.
        """
        return bool(
            np.isfinite(self.x)
            and np.isfinite(self.y)
        )


@dataclass
class ProjectedCurve:
    """
    A sampled curve in projected Cartesian coordinates.

    Parameters
    ----------
    x, y
        One-dimensional Cartesian coordinate arrays.
    closed
        Whether the curve is geometrically closed.
    name
        Optional curve identifier.
    style
        Default rendering style associated with the curve.
    """

    x: np.ndarray
    y: np.ndarray
    closed: bool = False
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = _coordinate_array(
            self.x,
            name="x",
        )
        self.y = _coordinate_array(
            self.y,
            name="y",
        )

        if self.x.shape != self.y.shape:
            raise ValueError(
                "x and y must have the same shape."
            )

        if self.x.size < 2:
            raise ValueError(
                "A projected curve requires at least two samples."
            )

        self.closed = bool(self.closed)

    def __len__(self) -> int:
        return self.x.size

    @property
    def finite(self) -> np.ndarray:
        """
        Boolean mask selecting samples with finite x and y coordinates.
        """
        return (
            np.isfinite(self.x)
            & np.isfinite(self.y)
        )

    @property
    def bounds(
        self,
    ) -> tuple[float, float, float, float] | None:
        """
        Bounds of the finite projected samples.

        Returns
        -------
        tuple or None
            ``(x_min, x_max, y_min, y_max)``, or ``None`` when the curve
            contains no finite samples.
        """
        finite = self.finite

        if not np.any(finite):
            return None

        return (
            float(np.min(self.x[finite])),
            float(np.max(self.x[finite])),
            float(np.min(self.y[finite])),
            float(np.max(self.y[finite])),
        )


@dataclass
class ProjectedPolygon:
    """
    A polygon in projected Cartesian coordinates.

    The polygon boundary is implicitly closed. The first coordinate does
    not need to be repeated at the end.
    """

    x: np.ndarray
    y: np.ndarray
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = _coordinate_array(
            self.x,
            name="x",
        )
        self.y = _coordinate_array(
            self.y,
            name="y",
        )

        if self.x.shape != self.y.shape:
            raise ValueError(
                "x and y must have the same shape."
            )

        if self.x.size < 3:
            raise ValueError(
                "A projected polygon requires at least three vertices."
            )


    def __len__(self) -> int:
        return self.x.size

    @property
    def finite(self) -> np.ndarray:
        return (
            np.isfinite(self.x)
            & np.isfinite(self.y)
        )

    @property
    def bounds(
        self,
    ) -> tuple[float, float, float, float] | None:
        finite = self.finite

        if not np.any(finite):
            return None

        return (
            float(np.min(self.x[finite])),
            float(np.max(self.x[finite])),
            float(np.min(self.y[finite])),
            float(np.max(self.y[finite])),
        )


