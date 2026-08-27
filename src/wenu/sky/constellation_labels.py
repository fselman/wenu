"""Constellation label anchors represented as spherical point geometry."""

from __future__ import annotations

from collections import defaultdict

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.semantic_identity import semantic_key


class ConstellationLabels(GeometricalObject):
    """Compute projection-independent constellation label anchors."""

    layer_name = "constellation_labels"

    LABEL_OVERRIDES = {
        "SER1": "SerCap",
        "SER2": "SerCau",
    }

    def __init__(
        self,
        stars,
        *,
        selected=None,
        boundaries=None,
        min_stars=3,
        system="western",
    ):
        self.stars = stars
        self.selected = None if selected is None else set(selected)
        self.boundaries = boundaries
        self.min_stars = int(min_stars)
        self.system = system
        self.semantic_system_key = semantic_key(
            system,
            field="constellation system key",
        )

    def set_boundaries(self, boundaries):
        self.boundaries = boundaries
        return boundaries

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        min_stars=None,
    ) -> SphericalPoints:
        selected = (
            self.selected if selected is None else set(selected)
        )
        min_stars = (
            self.min_stars if min_stars is None else int(min_stars)
        )
        frame = getattr(
            self.stars,
            "source_catalog",
            self.stars.hip_df,
        )
        if frame is None or len(frame) == 0:
            return self._empty()

        ra_deg = frame["ra_degrees"].to_numpy(dtype=float)
        dec_deg = frame["dec_degrees"].to_numpy(dtype=float)
        valid_coordinates = np.isfinite(ra_deg) & np.isfinite(dec_deg)
        if not np.any(valid_coordinates):
            return self._empty()
        coordinates = SkyCoord(
            ra=ra_deg[valid_coordinates] * u.deg,
            dec=dec_deg[valid_coordinates] * u.deg,
            frame="icrs",
        )
        abbreviations = np.asarray(
            coordinates.get_constellation(short_name=True),
            dtype=object,
        )
        apparent = coordinates.transform_to(observer.altaz_frame)
        apparent_lon_deg = apparent.az.to_value(u.deg)
        apparent_lat_deg = apparent.alt.to_value(u.deg)
        groups = defaultdict(list)
        group_labels = np.asarray(abbreviations, dtype=object).copy()
        if self.boundaries is not None:
            serpens = abbreviations == "Ser"
            if np.any(serpens):
                identifiers = self.boundaries.regions_of(
                    ra_deg[valid_coordinates][serpens],
                    dec_deg[valid_coordinates][serpens],
                    candidates={"SER1", "SER2"},
                )
                group_labels[serpens] = [
                    self.LABEL_OVERRIDES.get(identifier, "Ser")
                    for identifier in identifiers
                ]

        for index, (abbreviation, label) in enumerate(
            zip(abbreviations, group_labels, strict=True)
        ):
            if (
                selected is not None
                and abbreviation not in selected
                and label not in selected
            ):
                continue
            groups[label].append(index)

        lon_deg = []
        lat_deg = []
        labels = []
        for label, indices in groups.items():
            if len(indices) < min_stars:
                continue
            lon, lat = self._spherical_mean(
                apparent_lon_deg[indices],
                apparent_lat_deg[indices],
            )
            lon_deg.append(lon)
            lat_deg.append(lat)
            labels.append(label)

        return SphericalPoints(
            lon_deg=np.asarray(lon_deg, dtype=float),
            lat_deg=np.asarray(lat_deg, dtype=float),
            labels=np.asarray(labels, dtype=object),
            metadata={
                "kind": "constellation_labels",
                "system": self.system,
                "semantic_entity_keys": tuple(
                    semantic_key(label, field="constellation key")
                    for label in labels
                ),
                "semantic_entity_display_names": tuple(labels),
            },
        )

    @staticmethod
    def _spherical_mean(lon_deg, lat_deg):
        lon = np.radians(np.asarray(lon_deg, dtype=float))
        lat = np.radians(np.asarray(lat_deg, dtype=float))
        vectors = np.column_stack(
            (
                np.cos(lat) * np.cos(lon),
                np.cos(lat) * np.sin(lon),
                np.sin(lat),
            )
        )
        mean = np.mean(vectors, axis=0)
        norm = np.linalg.norm(mean)
        if norm == 0.0:
            return float(lon_deg[0]), float(lat_deg[0])
        mean /= norm
        return (
            float(np.degrees(np.arctan2(mean[1], mean[0])) % 360.0),
            float(np.degrees(np.arcsin(mean[2]))),
        )

    def _empty(self):
        return SphericalPoints(
            lon_deg=np.asarray([], dtype=float),
            lat_deg=np.asarray([], dtype=float),
            labels=np.asarray([], dtype=object),
            metadata={
                "kind": "constellation_labels",
                "system": self.system,
                "semantic_entity_keys": (),
                "semantic_entity_display_names": (),
            },
        )
