"""Milky Way surface-brightness isophote layer."""

from __future__ import annotations

import json

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from wenu.geometry.spherical import SphericalPolygons
from wenu.resources import milky_way_isophotes_path
from wenu.sky.sky_layer import SkyLayer


class MilkyWayIsophotes(SkyLayer):
    """Nested Milky Way isophotes with GeoJSON ring topology preserved."""

    layer_name = "milky_way_isophotes"
    available_levels = ("ol1", "ol2", "ol3", "ol4", "ol5")
    default_levels = ("ol2", "ol3", "ol4", "ol5")

    def __init__(self, observer, *, levels=None):
        self.observer = observer
        self.levels = self._validate_levels(levels)
        self.features = None
        self.source = None

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

        longitude = []
        latitude = []
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
        for level in selected_levels:
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
                    equatorial = SkyCoord(
                        ra=np.mod(coordinates[:, 0], 360.0) * u.deg,
                        dec=coordinates[:, 1] * u.deg,
                        frame="icrs",
                    )
                    horizontal = equatorial.transform_to(
                        resolved.altaz_frame
                    )
                    longitude.append(horizontal.az.to_value(u.deg))
                    latitude.append(horizontal.alt.to_value(u.deg))
                    ring_id = f"{compound}:{ring_index}"
                    ids.append(ring_id)
                    level_values.append(level)
                    compounds.append(compound)
                    ring_indices.append(ring_index)
                    holes.append(ring_index > 0)

        return SphericalPolygons(
            lon_deg=tuple(longitude),
            lat_deg=tuple(latitude),
            ids=ids,
            metadata={
                "source": self.source,
                "coordinate_system": "altaz",
                "level": np.asarray(level_values, dtype=object),
                "compound_id": np.asarray(compounds, dtype=object),
                "ring_index": np.asarray(ring_indices, dtype=int),
                "is_hole": np.asarray(holes, dtype=bool),
            },
        )
