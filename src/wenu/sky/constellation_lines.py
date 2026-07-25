"""Constellation-line topology expressed as observer-time spherical geometry."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path

import numpy as np

from wenu.resources import constellation_lines_path
from wenu.sky.geometrical_object import GeometricalObject
from wenu.spherical import SphericalCurves


class ConstellationLines(GeometricalObject):
    """HIP-to-HIP constellation edges evaluated for an observer."""

    layer_name = "constellation_lines"

    def __init__(
        self,
        stars,
        system="western",
        filename=None,
        constellations=None,
    ):
        # Accept the temporary StarsRenderingAdapter during migration, but
        # retain only its domain object.
        self.stars = getattr(stars, "stars", stars)
        self.system = system
        self.filename = None if filename is None else Path(filename)
        self.constellations = (
            None if constellations is None else set(constellations)
        )
        self.edges = []
        self.edges_by_constellation = {}
        self.load()

    def load(self):
        """Read constellation connectivity from a Stellarium-style .fab file."""
        if self.filename is not None:
            if not self.filename.exists():
                raise FileNotFoundError(
                    f"Constellation file not found: {self.filename}"
                )
            return self._load_file(self.filename)

        resource = constellation_lines_path(self.system)
        with as_file(resource) as path:
            return self._load_file(path)

    def _load_file(self, path):
        path = Path(path)
        self.edges.clear()
        self.edges_by_constellation.clear()

        with path.open("r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) < 4:
                    continue

                abbreviation = parts[0]
                if (
                    self.constellations is not None
                    and abbreviation not in self.constellations
                ):
                    continue

                try:
                    int(parts[1])
                    hip_ids = [int(value) for value in parts[2:]]
                except ValueError as error:
                    raise ValueError(
                        f"Invalid .fab line at {path}:{line_number}\n"
                        f"{raw_line.rstrip()}"
                    ) from error

                if len(hip_ids) < 2:
                    continue

                constellation_edges = [
                    (int(hip1), int(hip2))
                    for hip1, hip2 in zip(hip_ids[:-1], hip_ids[1:])
                ]
                self.edges.extend(constellation_edges)
                self.edges_by_constellation.setdefault(
                    abbreviation, []
                ).extend(constellation_edges)

        return self.edges

    def spherical_geometry(self, observer) -> SphericalCurves:
        """Return apparent Alt/Az line segments at the observer's time."""
        if observer is None:
            raise RuntimeError(
                "An Observer is required for constellation-line geometry."
            )
        if self.stars is None or self.stars.catalog is None:
            raise RuntimeError(
                "The stellar catalogue has not been loaded."
            )
        if self.stars.skyfield_stars is None:
            raise RuntimeError(
                "The stellar Skyfield representation is unavailable."
            )

        # Evaluate the stable catalogue directly. Do not call
        # Stars.spherical_geometry(), because that deliberately updates the
        # renderer-facing active selection.
        apparent = (
            observer.skyfield
            .at(observer.t)
            .observe(self.stars.skyfield_stars)
            .apparent(deflectors=[])
        )
        altitude, azimuth, _ = apparent.altaz()
        alt_deg = np.asarray(altitude.degrees, dtype=float)
        az_deg = np.asarray(azimuth.degrees, dtype=float)
        catalogue_index = {
            int(hip_id): index
            for index, hip_id in enumerate(self.stars.catalog.index)
        }

        lon_curves = []
        lat_curves = []
        identifiers = []
        names = []
        hip_edges = []

        for abbreviation, edges in self.edges_by_constellation.items():
            for edge_number, (hip1, hip2) in enumerate(edges):
                if hip1 not in catalogue_index or hip2 not in catalogue_index:
                    continue
                first = catalogue_index[hip1]
                second = catalogue_index[hip2]
                lon_curves.append(
                    np.asarray([az_deg[first], az_deg[second]])
                )
                lat_curves.append(
                    np.asarray([alt_deg[first], alt_deg[second]])
                )
                identifiers.append(
                    f"{abbreviation}:{edge_number}:{hip1}-{hip2}"
                )
                names.append(abbreviation)
                hip_edges.append((hip1, hip2))

        if not lon_curves:
            # SphericalCurves permits an empty collection.
            lon_curves = ()
            lat_curves = ()

        return SphericalCurves(
            lon_deg=tuple(lon_curves),
            lat_deg=tuple(lat_curves),
            ids=identifiers,
            names=names,
            metadata={
                "system": self.system,
                "coordinate_system": "altaz",
                "hip_edges": tuple(hip_edges),
            },
        )

