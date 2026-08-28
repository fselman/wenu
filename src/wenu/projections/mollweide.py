"""Coordinate-neutral Mollweide projection with longitude-seam topology."""

from __future__ import annotations

import numpy as np

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedGrid,
    ProjectedPoint,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


class MollweideProjection:
    """Equal-area projection centered on a configurable longitude."""

    def __init__(
        self,
        *,
        central_longitude_deg=0.0,
        flip_ew=True,
        radius=1.0,
    ):
        central = float(central_longitude_deg)
        radius = float(radius)
        if not np.isfinite(central):
            raise ValueError("central_longitude_deg must be finite.")
        if not np.isfinite(radius) or radius <= 0.0:
            raise ValueError("radius must be positive and finite.")
        self.central_longitude_deg = central % 360.0
        self.flip_ew = bool(flip_ew)
        self.radius = radius

    @property
    def x_limit(self):
        """Return the positive horizontal extent of the map ellipse."""
        return 2.0 * np.sqrt(2.0) * self.radius

    @property
    def y_limit(self):
        """Return the positive vertical extent of the map ellipse."""
        return np.sqrt(2.0) * self.radius

    def normalized_longitude(self, longitude_deg):
        """Return longitude relative to the center in [-180, 180)."""
        longitude = np.asarray(longitude_deg, dtype=float)
        return (
            longitude - self.central_longitude_deg + 180.0
        ) % 360.0 - 180.0

    def project_spherical(self, lon_deg, lat_deg):
        """Project longitude and latitude arrays without topology changes."""
        return self._project_normalized(
            self.normalized_longitude(lon_deg), lat_deg
        )

    def _project_normalized(self, lon_deg, lat_deg):
        """Project seam-prepared longitudes in the closed map interval."""
        longitude, latitude = np.broadcast_arrays(
            np.asarray(lon_deg, dtype=float),
            np.asarray(lat_deg, dtype=float),
        )
        if np.any(np.isfinite(longitude) & (np.abs(longitude) > 180.0)):
            raise ValueError(
                "normalized longitude must be between -180 and 180 degrees."
            )
        if np.any(np.isfinite(latitude) & (np.abs(latitude) > 90.0)):
            raise ValueError("latitude must be between -90 and 90 degrees.")
        theta = _auxiliary_angle(np.radians(latitude))
        x = (
            2.0
            * np.sqrt(2.0)
            * self.radius
            / np.pi
            * np.radians(longitude)
            * np.cos(theta)
        )
        y = np.sqrt(2.0) * self.radius * np.sin(theta)
        if self.flip_ew:
            x = -x
        return x, y

    def project_geometry(self, geometry):
        """Project supported spherical geometry with seam-safe topology."""
        if isinstance(geometry, SphericalPoints):
            return self.project_points(geometry)
        if isinstance(geometry, SphericalCurves):
            return self.project_curves(geometry)
        if isinstance(geometry, SphericalGrid):
            return self.project_grid(geometry)
        if isinstance(geometry, SphericalPolygons):
            return self.project_polygons(geometry)
        raise TypeError(
            "Unsupported spherical geometry type: "
            f"{type(geometry).__name__}."
        )

    def project_point(self, lon_deg, lat_deg, *, name=None):
        x, y = self.project_spherical(lon_deg, lat_deg)
        if np.asarray(x).ndim != 0 or np.asarray(y).ndim != 0:
            raise ValueError(
                "project_point requires scalar longitude and latitude."
            )
        return ProjectedPoint(float(x), float(y), name=name)

    def project_points(self, points):
        x, y = self.project_spherical(points.lon_deg, points.lat_deg)
        return ProjectedPoints(
            x=x,
            y=y,
            ids=points.ids,
            labels=points.labels,
            names=points.names,
            metadata=dict(points.metadata),
        )

    def project_curves(self, curves):
        items = []
        source_indices = []
        for index, (longitude, latitude, closed) in enumerate(
            zip(curves.lon_deg, curves.lat_deg, curves.closed)
        ):
            name = None if curves.names is None else curves.names[index]
            segments = _split_curve_at_seam(
                self.normalized_longitude(longitude),
                latitude,
                closed=bool(closed),
            )
            seam_split = len(segments) != 1
            for segment_longitude, segment_latitude in segments:
                x, y = self._project_normalized(
                    segment_longitude, segment_latitude
                )
                items.append(
                    ProjectedCurve(
                        x=x,
                        y=y,
                        closed=bool(closed) and not seam_split,
                        name=name,
                    )
                )
                source_indices.append(index)
        return ProjectedCurves(
            items=items,
            metadata=_expanded_metadata(curves, source_indices),
        )

    def project_grid(self, grid):
        return ProjectedGrid(
            components={
                name: self.project_curves(curves)
                for name, curves in grid.components.items()
            },
            metadata=dict(grid.metadata),
        )

    def project_polygons(self, polygons):
        items = []
        source_indices = []
        source_latitudes = []
        for index, (longitude, latitude) in enumerate(
            zip(polygons.lon_deg, polygons.lat_deg)
        ):
            name = None if polygons.names is None else polygons.names[index]
            for ring_longitude, ring_latitude in _split_polygon_at_seam(
                self.normalized_longitude(longitude), latitude
            ):
                x, y = self._project_normalized(
                    ring_longitude, ring_latitude
                )
                items.append(ProjectedPolygon(x=x, y=y, name=name))
                source_indices.append(index)
                source_latitudes.append(ring_latitude)
        metadata = _expanded_metadata(polygons, source_indices)
        metadata["projection_source_latitudes"] = tuple(
            source_latitudes
        )
        return ProjectedPolygons(
            items=items,
            metadata=metadata,
        )


def _auxiliary_angle(latitude_rad):
    latitude = np.asarray(latitude_rad, dtype=float)
    theta = np.full_like(latitude, np.nan)
    poles = np.isfinite(latitude) & np.isclose(
        np.abs(latitude), np.pi / 2.0, atol=1.0e-14
    )
    theta[poles] = np.sign(latitude[poles]) * np.pi / 2.0
    active = np.isfinite(latitude) & ~poles
    target = np.pi * np.sin(latitude[active])
    lower = np.full(target.shape, -np.pi / 2.0)
    upper = np.full(target.shape, np.pi / 2.0)
    for _ in range(60):
        middle = 0.5 * (lower + upper)
        value = 2.0 * middle + np.sin(2.0 * middle)
        below = value < target
        lower = np.where(below, middle, lower)
        upper = np.where(below, upper, middle)
    theta[active] = 0.5 * (lower + upper)
    return theta


def _unwrap(longitude):
    values = np.asarray(longitude, dtype=float)
    return np.degrees(np.unwrap(np.radians(values), discont=np.pi))


def _slab_indices(longitude):
    minimum = float(np.nanmin(longitude))
    maximum = float(np.nanmax(longitude))
    first = int(np.floor((minimum + 180.0) / 360.0))
    last = int(np.floor((maximum + 180.0) / 360.0))
    return range(first, last + 1)


def _split_curve_at_seam(longitude, latitude, *, closed):
    longitude = np.asarray(longitude, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    finite = np.isfinite(longitude) & np.isfinite(latitude)
    if np.all(finite):
        return _split_finite_curve(
            longitude, latitude, closed=closed
        )
    segments = []
    for start, stop in _finite_runs(finite):
        if stop - start >= 2:
            segments.extend(_split_finite_curve(
                longitude[start:stop],
                latitude[start:stop],
                closed=False,
            ))
    return segments


def _split_finite_curve(longitude, latitude, *, closed):
    longitude = _unwrap(longitude)
    latitude = np.asarray(latitude, dtype=float)
    if closed:
        closing = longitude[0] + 360.0 * np.round(
            (longitude[-1] - longitude[0]) / 360.0
        )
        longitude = np.concatenate((longitude, [closing]))
        latitude = np.concatenate((latitude, latitude[:1]))
    segments = []
    for slab in _slab_indices(longitude):
        low = -180.0 + 360.0 * slab
        high = 180.0 + 360.0 * slab
        for segment_lon, segment_lat in _clip_polyline_to_slab(
            longitude, latitude, low=low, high=high
        ):
            if len(segment_lon) >= 2:
                segments.append(
                    (segment_lon - 360.0 * slab, segment_lat)
                )
    return segments


def _finite_runs(finite):
    padded = np.concatenate(([False], finite, [False])).astype(int)
    transitions = np.diff(padded)
    starts = np.flatnonzero(transitions == 1)
    stops = np.flatnonzero(transitions == -1)
    return zip(starts, stops)


def _clip_polyline_to_slab(longitude, latitude, *, low, high):
    segments = []
    current_lon = []
    current_lat = []
    for index in range(len(longitude) - 1):
        clipped = _clip_segment_to_slab(
            longitude[index],
            latitude[index],
            longitude[index + 1],
            latitude[index + 1],
            low=low,
            high=high,
        )
        if clipped is None:
            if len(current_lon) >= 2:
                segments.append(
                    (np.asarray(current_lon), np.asarray(current_lat))
                )
            current_lon, current_lat = [], []
            continue
        start_lon, start_lat, end_lon, end_lat = clipped
        if not current_lon or not np.allclose(
            (current_lon[-1], current_lat[-1]),
            (start_lon, start_lat),
        ):
            if len(current_lon) >= 2:
                segments.append(
                    (np.asarray(current_lon), np.asarray(current_lat))
                )
            current_lon = [start_lon]
            current_lat = [start_lat]
        current_lon.append(end_lon)
        current_lat.append(end_lat)
    if len(current_lon) >= 2:
        segments.append((np.asarray(current_lon), np.asarray(current_lat)))
    return segments


def _clip_segment_to_slab(x0, y0, x1, y1, *, low, high):
    if not np.all(np.isfinite((x0, y0, x1, y1))):
        return None
    delta = x1 - x0
    if np.isclose(delta, 0.0):
        if low <= x0 <= high:
            return x0, y0, x1, y1
        return None
    first = (low - x0) / delta
    last = (high - x0) / delta
    start = max(0.0, min(first, last))
    end = min(1.0, max(first, last))
    if start > end:
        return None
    return (
        x0 + start * delta,
        y0 + start * (y1 - y0),
        x0 + end * delta,
        y0 + end * (y1 - y0),
    )


def _split_polygon_at_seam(longitude, latitude):
    longitude = np.asarray(longitude, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    finite = np.isfinite(longitude) & np.isfinite(latitude)
    longitude = longitude[finite]
    latitude = latitude[finite]
    if len(longitude) < 3:
        return []
    longitude = _unwrap(longitude)
    rings = []
    for slab in _slab_indices(longitude):
        low = -180.0 + 360.0 * slab
        high = 180.0 + 360.0 * slab
        ring_lon, ring_lat = _clip_polygon_vertical(
            longitude, latitude, boundary=low, keep_greater=True
        )
        ring_lon, ring_lat = _clip_polygon_vertical(
            ring_lon, ring_lat, boundary=high, keep_greater=False
        )
        ring_lon, ring_lat = _clean_ring(ring_lon, ring_lat)
        if len(ring_lon) >= 3 and abs(_ring_area(
            ring_lon, ring_lat
        )) > 1.0e-12:
            rings.append((ring_lon - 360.0 * slab, ring_lat))
    return rings


def _clip_polygon_vertical(
    longitude,
    latitude,
    *,
    boundary,
    keep_greater,
):
    longitude = np.asarray(longitude, dtype=float)
    latitude = np.asarray(latitude, dtype=float)
    if longitude.size == 0:
        return longitude, latitude
    output_lon = []
    output_lat = []

    def inside(value):
        return value >= boundary if keep_greater else value <= boundary

    previous_lon = longitude[-1]
    previous_lat = latitude[-1]
    previous_inside = inside(previous_lon)
    for current_lon, current_lat in zip(longitude, latitude):
        current_inside = inside(current_lon)
        if current_inside != previous_inside:
            fraction = (
                (boundary - previous_lon)
                / (current_lon - previous_lon)
            )
            output_lon.append(boundary)
            output_lat.append(
                previous_lat + fraction * (current_lat - previous_lat)
            )
        if current_inside:
            output_lon.append(current_lon)
            output_lat.append(current_lat)
        previous_lon = current_lon
        previous_lat = current_lat
        previous_inside = current_inside
    return np.asarray(output_lon), np.asarray(output_lat)


def _clean_ring(longitude, latitude):
    if len(longitude) == 0:
        return longitude, latitude
    keep = np.ones(len(longitude), dtype=bool)
    keep[1:] = ~(
        np.isclose(longitude[1:], longitude[:-1])
        & np.isclose(latitude[1:], latitude[:-1])
    )
    longitude = longitude[keep]
    latitude = latitude[keep]
    if len(longitude) > 1 and np.allclose(
        (longitude[0], latitude[0]),
        (longitude[-1], latitude[-1]),
    ):
        longitude = longitude[:-1]
        latitude = latitude[:-1]
    return longitude, latitude


def _ring_area(longitude, latitude):
    return 0.5 * np.sum(
        longitude * np.roll(latitude, -1)
        - np.roll(longitude, -1) * latitude
    )


def _expanded_metadata(geometry, source_indices):
    metadata = dict(geometry.metadata)
    for name in ("ids", "labels", "names"):
        values = getattr(geometry, name, None)
        if values is not None:
            metadata[name] = values.copy()
    expanded = {}
    source_length = len(geometry)
    indices = np.asarray(source_indices, dtype=int)
    for name, value in metadata.items():
        if isinstance(value, np.ndarray) and value.ndim >= 1:
            if len(value) == source_length:
                expanded[name] = value[indices]
                continue
        if (
            isinstance(value, (list, tuple))
            and not isinstance(value, (str, bytes))
            and len(value) == source_length
        ):
            selected = [value[index] for index in source_indices]
            expanded[name] = (
                tuple(selected) if isinstance(value, tuple) else selected
            )
            continue
        expanded[name] = value
    return expanded