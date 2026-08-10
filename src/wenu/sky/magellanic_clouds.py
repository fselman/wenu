"""Gaia-derived Magellanic Cloud isophote layers."""

from __future__ import annotations

import json

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from wenu.geometry.spherical import SphericalPolygons
from wenu.resources import magellanic_cloud_isophotes_path
from wenu.sky.sky_layer import SkyLayer


class MagellanicCloudIsophotes(SkyLayer):
    """Nested isophotes for either the Large or Small Magellanic Cloud."""

    layer_name = "magellanic_cloud_isophotes"
    available_clouds = ("lmc", "smc")
    available_levels = (1, 2, 3, 4)
    default_levels = available_levels

    def __init__(self, observer, *, cloud, levels=None):
        self.observer = observer
        self.cloud = self._validate_cloud(cloud)
        self.levels = self._validate_levels(levels)
        self.features = None
        self.fractions = None
        self.source = None

    @classmethod
    def _validate_cloud(cls, cloud):
        cloud = str(cloud).lower()
        if cloud not in cls.available_clouds:
            available = ", ".join(cls.available_clouds)
            raise ValueError(
                f"Unknown Magellanic Cloud: {cloud!r}. "
                f"Available clouds: {available}."
            )
        return cloud

    @classmethod
    def _validate_levels(cls, levels):
        if levels is None:
            return cls.default_levels
        levels = tuple(int(level) for level in levels)
        unknown = set(levels).difference(cls.available_levels)
        if unknown:
            raise ValueError(
                "Unknown Magellanic Cloud isophote level(s): "
                + ", ".join(str(level) for level in sorted(unknown))
            )
        if len(set(levels)) != len(levels):
            raise ValueError(
                "Magellanic Cloud isophote levels must be unique."
            )
        return tuple(
            level for level in cls.available_levels if level in levels
        )

    def load(self, filename=None):
        """Load and validate one Cloud's canonical GeoJSON snapshot."""
        path = (
            magellanic_cloud_isophotes_path(self.cloud)
            if filename is None
            else filename
        )
        with open(path, encoding="utf-8") as stream:
            document = json.load(stream)
        if document.get("type") != "FeatureCollection":
            raise ValueError(
                "Magellanic Cloud data must be a FeatureCollection."
            )

        document_cloud = str(
            document.get("properties", {}).get("cloud", self.cloud)
        ).lower()
        if document_cloud != self.cloud:
            raise ValueError(
                f"Expected {self.cloud.upper()} data, found "
                f"{document_cloud.upper()}."
            )

        features = {}
        fractions = {}
        for feature in document.get("features", ()):
            properties = feature.get("properties", {})
            feature_cloud = str(
                properties.get("cloud", self.cloud)
            ).lower()
            if feature_cloud != self.cloud:
                raise ValueError(
                    f"Unexpected Cloud in feature: {feature_cloud!r}."
                )
            try:
                level = int(properties["level"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    "Every Magellanic Cloud feature must have an "
                    "integer level."
                ) from error
            geometry = feature.get("geometry", {})
            if level not in self.available_levels:
                raise ValueError(
                    f"Unexpected isophote level: {level!r}."
                )
            if level in features:
                raise ValueError(
                    f"Duplicate isophote level: {level!r}."
                )
            if geometry.get("type") != "MultiPolygon":
                raise ValueError(
                    f"Level {level} must use GeoJSON MultiPolygon "
                    "geometry."
                )
            features[level] = geometry["coordinates"]
            fractions[level] = float(
                properties.get("fraction_of_peak", np.nan)
            )

        ordered = tuple(
            level for level in self.available_levels if level in features
        )
        if ordered != self.available_levels:
            raise ValueError(
                "Magellanic Cloud data must contain levels 1 through 4."
            )
        self.features = features
        self.fractions = fractions
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
        fractions = []
        compounds = []
        ring_indices = []
        holes = []
        clouds = []

        selected_levels = (
            self.levels
            if levels is None
            else self._validate_levels(levels)
        )
        for level in selected_levels:
            for polygon_index, polygon in enumerate(self.features[level]):
                compound = f"{self.cloud}:{level}:{polygon_index}"
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
                    ids.append(f"{compound}:{ring_index}")
                    level_values.append(level)
                    fractions.append(self.fractions[level])
                    compounds.append(compound)
                    ring_indices.append(ring_index)
                    holes.append(ring_index > 0)
                    clouds.append(self.cloud)

        return SphericalPolygons(
            lon_deg=tuple(longitude),
            lat_deg=tuple(latitude),
            ids=ids,
            metadata={
                "source": self.source,
                "coordinate_system": "altaz",
                "cloud": np.asarray(clouds, dtype=object),
                "level": np.asarray(level_values, dtype=int),
                "fraction_of_peak": np.asarray(fractions, dtype=float),
                "compound_id": np.asarray(compounds, dtype=object),
                "ring_index": np.asarray(ring_indices, dtype=int),
                "is_hole": np.asarray(holes, dtype=bool),
            },
        )
