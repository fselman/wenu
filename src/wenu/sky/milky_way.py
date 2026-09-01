"""Milky Way surface-brightness isophote layer."""

from __future__ import annotations

import json

import numpy as np

from wenu.coordinates import PositionStatus
from wenu.coordinates import observer_altaz_spec

from wenu.geometry.spherical import SphericalPolygons
from wenu.resources import milky_way_isophotes_path
from wenu.sky.observed_cache import (
    icrs_curve_arrays_to_altaz,
    observed_polygon_arrays,
)
from wenu.sky.sky_layer import SkyLayer


class MilkyWayIsophotes(SkyLayer):
    """Nested Milky Way isophotes with GeoJSON ring topology preserved."""

    layer_name = "milky_way_isophotes"
    available_levels = ("ol1", "ol2", "ol3", "ol4", "ol5")
    default_levels = available_levels

    def __init__(self, observer, *, levels=None):
        self.observer = observer
        self.levels = self._validate_levels(levels)
        self.features = None
        self.source = None
        self._source_revision = 0
        self._observed_polygon_cache = {}

    @classmethod
    def _validate_levels(cls, levels):
        if levels is None:
            return cls.default_levels
        levels = tuple(str(level) for level in levels)
        unknown = set(levels).difference(cls.available_levels)
        if unknown:
            raise ValueError(
                "Unknown Milky Way isophote level(s): "
                + ", ".join(sorted(unknown))
            )
        if len(set(levels)) != len(levels):
            raise ValueError("Milky Way isophote levels must be unique.")
        return tuple(
            level for level in cls.available_levels if level in levels
        )

    def load(self, filename=None):
        """Load and validate the canonical GeoJSON snapshot."""
        path = milky_way_isophotes_path() if filename is None else filename
        with open(path, encoding="utf-8") as stream:
            document = json.load(stream)
        if document.get("type") != "FeatureCollection":
            raise ValueError("Milky Way data must be a FeatureCollection.")

        features = {}
        for feature in document.get("features", ()):
            level = str(
                feature.get("id")
                or feature.get("properties", {}).get("id")
            )
            geometry = feature.get("geometry", {})
            if level not in self.available_levels:
                raise ValueError(f"Unexpected isophote level: {level!r}.")
            if geometry.get("type") != "MultiPolygon":
                raise ValueError(
                    f"{level} must use GeoJSON MultiPolygon geometry."
                )
            features[level] = geometry["coordinates"]
        if tuple(level for level in self.available_levels if level in features) != self.available_levels:
            raise ValueError("Milky Way data must contain ol1 through ol5.")
        self.features = features
        self.source = str(path)
        self._source_revision += 1
        self._observed_polygon_cache.clear()
        return self

    def spherical_geometry(self, observer, *, levels=None):
        """Transform the selected ICRS isophote rings to observer Alt/Az."""
        if self.features is None:
            raise RuntimeError(
                "The isophotes have not been loaded. Call load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError("An observer with an altaz_frame is required.")

        native_rings = []
        ids = []
        level_values = []
        compounds = []
        ring_indices = []
        holes = []

        selected_levels = (
            self.levels
            if levels is None
            else self._validate_levels(levels)
        )
        for level in self.available_levels:
            for polygon_index, polygon in enumerate(self.features[level]):
                compound = f"{level}:{polygon_index}"
                for ring_index, ring in enumerate(polygon):
                    coordinates = np.asarray(ring, dtype=float)
                    if coordinates.ndim != 2 or coordinates.shape[1] < 2:
                        raise ValueError(
                            f"{compound} ring {ring_index} is invalid."
                        )
                    if len(coordinates) > 1 and np.allclose(
                        coordinates[0, :2],
                        coordinates[-1, :2],
                    ):
                        coordinates = coordinates[:-1]
                    if len(coordinates) < 3:
                        raise ValueError(
                            f"{compound} ring {ring_index} is too short."
                        )
                    native_rings.append(coordinates[:, :2])
                    ring_id = f"{compound}:{ring_index}"
                    ids.append(ring_id)
                    level_values.append(level)
                    compounds.append(compound)
                    ring_indices.append(ring_index)
                    holes.append(ring_index > 0)

        longitude, latitude = observed_polygon_arrays(
            self._observed_polygon_cache,
            resolved,
            source_key=(
                self.layer_name,
                self.source,
                self._source_revision,
            ),
            build=lambda: self._transform_rings(
                native_rings, resolved
            ),
        )
        positions = [
            index
            for index, level in enumerate(level_values)
            if level in selected_levels
        ]

        return SphericalPolygons(
            lon_deg=tuple(longitude[index] for index in positions),
            lat_deg=tuple(latitude[index] for index in positions),
            coordinate_spec=observer_altaz_spec(
                resolved,
                position_status=PositionStatus.APPARENT,
                provider="astropy Milky Way isophotes"
            ),
            ids=[ids[index] for index in positions],
            metadata={
                "source": self.source,
                "coordinate_system": "altaz",
                "level": np.asarray(level_values, dtype=object)[positions],
                "compound_id": np.asarray(compounds, dtype=object)[positions],
                "ring_index": np.asarray(ring_indices, dtype=int)[positions],
                "is_hole": np.asarray(holes, dtype=bool)[positions],
                # OL1 supplies the valid outer contour, but its
                # sphere-spanning GeoJSON exterior cannot be face-filled
                # safely as an ordinary planar compound path.  Retain all
                # of its boundaries while filling the nested inner levels.
                "compound_fill": np.asarray(
                    [level != "ol1" for level in level_values],
                    dtype=bool,
                )[positions],
                "semantic_entity_keys": np.asarray(
                    [f"isophote_{level}" for level in level_values],
                    dtype=object,
                )[positions],
                "semantic_entity_display_names": np.asarray(
                    [f"Isophote {str(level).upper()}" for level in level_values],
                    dtype=object,
                )[positions],
            },
        )

    @staticmethod
    def _transform_rings(rings, observer):
        if not rings:
            return (), ()
        return icrs_curve_arrays_to_altaz(
            tuple(np.asarray(ring[:, 0], dtype=float) for ring in rings),
            tuple(np.asarray(ring[:, 1], dtype=float) for ring in rings),
            observer,
            provider="Milky Way isophotes",
        )
