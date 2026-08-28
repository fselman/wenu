# src/wenu/spherical.py

# TODO:
# Curves and polygons intentionally duplicate validation logic.
# Common functionality may be factored after the geometry API
# stabilizes.

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import Any, Mapping, Sequence, TypeAlias

import numpy as np

from wenu.coordinates import CoordinateSpec


def _coordinate_array(values: Any, *, name: str) -> np.ndarray:
    """
    Convert spherical coordinate values to a one-dimensional float array.
    """
    array = np.asarray(values, dtype=float)

    if array.ndim != 1:
        raise ValueError(
            f"{name} must be a one-dimensional array."
        )

    return array


def _coordinate_collection(
    values: Sequence[Any],
    *,
    name: str,
) -> tuple[np.ndarray, ...]:
    """
    Convert a sequence of coordinate arrays to a tuple of 1-D float arrays.
    """
    return tuple(
        _coordinate_array(
            value,
            name=f"{name}[{index}]",
        )
        for index, value in enumerate(values)
    )


def _optional_entity_array(
    values: Any | None,
    *,
    name: str,
    length: int,
) -> np.ndarray | None:
    """
    Convert optional per-entity data to a one-dimensional object array.
    """
    if values is None:
        return None

    array = np.asarray(values, dtype=object)

    if array.ndim != 1:
        raise ValueError(
            f"{name} must be a one-dimensional array."
        )

    if array.size != length:
        raise ValueError(
            f"{name} must contain one value per entity."
        )

    return array


@dataclass
class SphericalPoints:
    """
    A collection of points in generic spherical coordinates.

    Parameters
    ----------
    lon_deg, lat_deg
        One-dimensional longitude and latitude arrays in degrees.
    ids
        Optional identifier for each point.
    labels
        Optional display label for each point.
    names
        Optional name for each point.
    metadata
        Additional semantic data associated with the collection.

    Notes
    -----
    This class does not assign a physical meaning to longitude or latitude.
    Their coordinate system is determined by the layer that creates the
    geometry and by the transformation pipeline that consumes it.
    """

    lon_deg: np.ndarray
    lat_deg: np.ndarray
    _: KW_ONLY
    coordinate_spec: CoordinateSpec
    ids: np.ndarray | None = None
    labels: np.ndarray | None = None
    names: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_coordinate_spec(self.coordinate_spec)
        self.lon_deg = _coordinate_array(
            self.lon_deg,
            name="lon_deg",
        )
        self.lat_deg = _coordinate_array(
            self.lat_deg,
            name="lat_deg",
        )

        if self.lon_deg.shape != self.lat_deg.shape:
            raise ValueError(
                "lon_deg and lat_deg must have the same shape."
            )

        length = self.lon_deg.size

        self.ids = _optional_entity_array(
            self.ids,
            name="ids",
            length=length,
        )
        self.labels = _optional_entity_array(
            self.labels,
            name="labels",
            length=length,
        )
        self.names = _optional_entity_array(
            self.names,
            name="names",
            length=length,
        )

        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return self.lon_deg.size

    @property
    def finite(self) -> np.ndarray:
        """
        Mask selecting points whose two coordinates are finite.
        """
        return (
            np.isfinite(self.lon_deg)
            & np.isfinite(self.lat_deg)
        )


@dataclass
class SphericalCurves:
    """
    A collection of sampled curves in generic spherical coordinates.

    Each item in ``lon_deg`` and ``lat_deg`` describes one curve. A single
    curve is represented by collections of length one.
    """

    lon_deg: tuple[np.ndarray, ...]
    lat_deg: tuple[np.ndarray, ...]
    _: KW_ONLY
    coordinate_spec: CoordinateSpec
    closed: np.ndarray | None = None
    ids: np.ndarray | None = None
    labels: np.ndarray | None = None
    names: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_coordinate_spec(self.coordinate_spec)
        self.lon_deg = _coordinate_collection(
            self.lon_deg,
            name="lon_deg",
        )
        self.lat_deg = _coordinate_collection(
            self.lat_deg,
            name="lat_deg",
        )

        if len(self.lon_deg) != len(self.lat_deg):
            raise ValueError(
                "lon_deg and lat_deg must contain the same number of curves."
            )

        for index, (lon, lat) in enumerate(
            zip(self.lon_deg, self.lat_deg)
        ):
            if lon.shape != lat.shape:
                raise ValueError(
                    "Longitude and latitude arrays for curve "
                    f"{index} must have the same shape."
                )

            if lon.size < 2:
                raise ValueError(
                    f"Curve {index} requires at least two samples."
                )

        length = len(self.lon_deg)

        if self.closed is None:
            self.closed = np.zeros(length, dtype=bool)
        else:
            closed = np.asarray(self.closed, dtype=bool)

            if closed.ndim != 1:
                raise ValueError(
                    "closed must be a one-dimensional array."
                )

            if closed.size != length:
                raise ValueError(
                    "closed must contain one value per curve."
                )

            self.closed = closed

        self.ids = _optional_entity_array(
            self.ids,
            name="ids",
            length=length,
        )
        self.labels = _optional_entity_array(
            self.labels,
            name="labels",
            length=length,
        )
        self.names = _optional_entity_array(
            self.names,
            name="names",
            length=length,
        )

        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.lon_deg)

    @property
    def finite(self) -> tuple[np.ndarray, ...]:
        """
        One finite-coordinate mask for each curve.
        """
        return tuple(
            np.isfinite(lon) & np.isfinite(lat)
            for lon, lat in zip(self.lon_deg, self.lat_deg)
        )


@dataclass
class SphericalPolygons:
    """
    A collection of polygons in generic spherical coordinates.

    Polygon boundaries are implicitly closed. The first vertex need not be
    repeated at the end.
    """

    lon_deg: tuple[np.ndarray, ...]
    lat_deg: tuple[np.ndarray, ...]
    _: KW_ONLY
    coordinate_spec: CoordinateSpec
    ids: np.ndarray | None = None
    labels: np.ndarray | None = None
    names: np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_coordinate_spec(self.coordinate_spec)
        self.lon_deg = _coordinate_collection(
            self.lon_deg,
            name="lon_deg",
        )
        self.lat_deg = _coordinate_collection(
            self.lat_deg,
            name="lat_deg",
        )

        if len(self.lon_deg) != len(self.lat_deg):
            raise ValueError(
                "lon_deg and lat_deg must contain the same number of polygons."
            )

        for index, (lon, lat) in enumerate(
            zip(self.lon_deg, self.lat_deg)
        ):
            if lon.shape != lat.shape:
                raise ValueError(
                    "Longitude and latitude arrays for polygon "
                    f"{index} must have the same shape."
                )

            if lon.size < 3:
                raise ValueError(
                    f"Polygon {index} requires at least three vertices."
                )

        length = len(self.lon_deg)

        self.ids = _optional_entity_array(
            self.ids,
            name="ids",
            length=length,
        )
        self.labels = _optional_entity_array(
            self.labels,
            name="labels",
            length=length,
        )
        self.names = _optional_entity_array(
            self.names,
            name="names",
            length=length,
        )

        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.lon_deg)

    @property
    def finite(self) -> tuple[np.ndarray, ...]:
        """
        One finite-coordinate mask for each polygon.
        """
        return tuple(
            np.isfinite(lon) & np.isfinite(lat)
            for lon, lat in zip(self.lon_deg, self.lat_deg)
        )


@dataclass
class SphericalGrid:
    """
    A named collection of related spherical-curve groups.

    Examples of components include meridians, parallels, emphasized
    reference curves, or other logically grouped grid curves.
    """

    components: Mapping[str, SphericalCurves]
    _: KW_ONLY
    coordinate_spec: CoordinateSpec
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_coordinate_spec(self.coordinate_spec)
        components = dict(self.components)

        for name, curves in components.items():
            if not isinstance(name, str):
                raise TypeError(
                    "Grid component names must be strings."
                )

            if not isinstance(curves, SphericalCurves):
                raise TypeError(
                    "Every grid component must be a SphericalCurves instance."
                )

            if curves.coordinate_spec != self.coordinate_spec:
                raise ValueError(
                    f"Grid component {name!r} has a different coordinate spec."
                )

        self.components = components
        self.metadata = dict(self.metadata)

    def __len__(self) -> int:
        return len(self.components)

    def __getitem__(self, name: str) -> SphericalCurves:
        return self.components[name]


def _validate_coordinate_spec(value: CoordinateSpec) -> None:
    if not isinstance(value, CoordinateSpec):
        raise TypeError("coordinate_spec must be a CoordinateSpec instance.")

SphericalGeometry: TypeAlias = (
    SphericalPoints
    | SphericalCurves
    | SphericalPolygons
    | SphericalGrid
)
