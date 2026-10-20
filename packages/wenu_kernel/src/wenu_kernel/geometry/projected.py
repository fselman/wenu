from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Mapping

import numpy as np


def _coordinate_array(values, *, name: str) -> np.ndarray:
    """Convert Cartesian coordinates to a one-dimensional float array."""
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional array.")
    return array


def _bounds(x: np.ndarray, y: np.ndarray):
    finite = np.isfinite(x) & np.isfinite(y)
    if not np.any(finite):
        return None
    return (
        float(np.min(x[finite])),
        float(np.max(x[finite])),
        float(np.min(y[finite])),
        float(np.max(y[finite])),
    )


def _optional_entity_array(values, *, name: str, length: int):
    if values is None:
        return None
    array = np.asarray(values, dtype=object)
    if array.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional array.")
    if array.size != length:
        raise ValueError(f"{name} must contain one value per entity.")
    return array


@dataclass
class ProjectedPoint:
    """A point in projected Cartesian coordinates."""

    x: float
    y: float
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = float(self.x)
        self.y = float(self.y)

    @property
    def finite(self) -> bool:
        return bool(np.isfinite(self.x) and np.isfinite(self.y))


@dataclass
class ProjectedPoints:
    """A vectorized collection of projected points.

    Unlike the other projected collections, this class stores coordinate
    arrays directly instead of wrapping many ``ProjectedPoint`` instances.
    """

    x: np.ndarray
    y: np.ndarray
    metadata: dict[str, object] = field(default_factory=dict)
    ids: np.ndarray | None = None
    labels: np.ndarray | None = None
    names: np.ndarray | None = None

    def __post_init__(self) -> None:
        self.x = _coordinate_array(self.x, name="x")
        self.y = _coordinate_array(self.y, name="y")
        if self.x.shape != self.y.shape:
            raise ValueError("x and y must have the same shape.")
        length = self.x.size
        self.ids = _optional_entity_array(
            self.ids, name="ids", length=length
        )
        self.labels = _optional_entity_array(
            self.labels, name="labels", length=length
        )
        self.names = _optional_entity_array(
            self.names, name="names", length=length
        )
        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return self.x.size

    @property
    def finite(self) -> np.ndarray:
        return np.isfinite(self.x) & np.isfinite(self.y)

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:
        return _bounds(self.x, self.y)


@dataclass
class ProjectedCurve:
    """A sampled curve in projected Cartesian coordinates."""

    x: np.ndarray
    y: np.ndarray
    closed: bool = False
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = _coordinate_array(self.x, name="x")
        self.y = _coordinate_array(self.y, name="y")
        if self.x.shape != self.y.shape:
            raise ValueError("x and y must have the same shape.")
        if self.x.size < 2:
            raise ValueError(
                "A projected curve requires at least two samples."
            )
        self.closed = bool(self.closed)

    def __len__(self) -> int:
        return self.x.size

    @property
    def finite(self) -> np.ndarray:
        return np.isfinite(self.x) & np.isfinite(self.y)

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:
        return _bounds(self.x, self.y)


@dataclass
class ProjectedCurves:
    """A small collection of projected curves."""

    items: list[ProjectedCurve]
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.items = list(self.items)
        if not all(isinstance(item, ProjectedCurve) for item in self.items):
            raise TypeError(
                "items must contain only ProjectedCurve instances."
            )
        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[ProjectedCurve]:
        return iter(self.items)

    def __getitem__(self, index):
        return self.items[index]


@dataclass
class ProjectedGrid:
    """Named groups of curves representing a projected grid."""

    components: Mapping[str, ProjectedCurves]
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        components = dict(self.components)
        for name, curves in components.items():
            if not isinstance(name, str):
                raise TypeError("Grid component names must be strings.")
            if not isinstance(curves, ProjectedCurves):
                raise TypeError(
                    "Every grid component must be a "
                    "ProjectedCurves instance."
                )
        self.components = components
        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.components)

    def __getitem__(self, name: str) -> ProjectedCurves:
        return self.components[name]


@dataclass
class ProjectedPolygon:
    """A polygon in projected Cartesian coordinates."""

    x: np.ndarray
    y: np.ndarray
    name: str | None = None

    def __post_init__(self) -> None:
        self.x = _coordinate_array(self.x, name="x")
        self.y = _coordinate_array(self.y, name="y")
        if self.x.shape != self.y.shape:
            raise ValueError("x and y must have the same shape.")
        if self.x.size < 3:
            raise ValueError(
                "A projected polygon requires at least three vertices."
            )

    def __len__(self) -> int:
        return self.x.size

    @property
    def finite(self) -> np.ndarray:
        return np.isfinite(self.x) & np.isfinite(self.y)

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:
        return _bounds(self.x, self.y)


@dataclass
class ProjectedPolygons:
    """A small collection of projected polygons."""

    items: list[ProjectedPolygon]
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.items = list(self.items)
        if not all(isinstance(item, ProjectedPolygon) for item in self.items):
            raise TypeError(
                "items must contain only ProjectedPolygon instances."
            )
        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[ProjectedPolygon]:
        return iter(self.items)

    def __getitem__(self, index):
        return self.items[index]
