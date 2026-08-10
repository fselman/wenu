"""Constellation-line topology expressed as observer-time spherical geometry."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path
from types import MappingProxyType
import warnings

import numpy as np

from wenu.resources import constellation_lines_path
from wenu.sky.geometrical_object import GeometricalObject
from wenu.geometry.spherical import SphericalCurves


class UnresolvedConstellationStarWarning(UserWarning):
    """A constellation figure references stars absent from the catalogue."""


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

    @property
    def star_ids(self):
        """Immutable, deduplicated identifiers in the loaded line system."""
        return frozenset(
            hip_id
            for edge in self.edges
            for hip_id in edge
        )

    @property
    def star_ids_by_constellation(self):
        """Immutable mapping of figure abbreviation to stellar identifiers."""
        return MappingProxyType(
            {
                abbreviation: frozenset(
                    hip_id
                    for edge in edges
                    for hip_id in edge
                )
                for abbreviation, edges
                in self.edges_by_constellation.items()
            }
        )

    def star_ids_for(self, constellations=None):
        """Return deduplicated identifiers for selected loaded figures.

        ``None`` returns all identifiers. Unknown abbreviations are reported
        rather than silently ignored.
        """
        if constellations is None:
            return self.star_ids
        requested = frozenset(str(name) for name in constellations)
        unknown = requested.difference(self.edges_by_constellation)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise KeyError(f"Unknown loaded constellation figure(s): {names}")
        return frozenset(
            hip_id
            for abbreviation in requested
            for edge in self.edges_by_constellation[abbreviation]
            for hip_id in edge
        )

    @property
    def resolvable_star_ids(self):
        """Identifiers that are present in the active stellar catalogue."""
        available = self._catalogue_star_ids()
        return self.star_ids.intersection(available)

    @property
    def unresolved_star_ids(self):
        """Identifiers referenced by figures but absent from the catalogue."""
        available = self._catalogue_star_ids()
        return self.star_ids.difference(available)

    def _catalogue_star_ids(self):
        catalog = getattr(self.stars, "catalog", None)
        if catalog is None:
            catalog = getattr(self.stars, "hip_df", None)
        if catalog is None:
            return frozenset()
        return frozenset(int(value) for value in catalog.index)

    def require_resolved_star_ids(self):
        """Return identifiers or raise with a complete missing-ID diagnostic."""
        missing = self.unresolved_star_ids
        if missing:
            values = ", ".join(str(value) for value in sorted(missing))
            raise LookupError(
                "Constellation-line stars are absent from the stellar "
                f"catalogue: {values}"
            )
        return self.star_ids

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
        if self.constellations is not None:
            self.edges_by_constellation.update(
                (name, []) for name in self.constellations
            )

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

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
    ) -> SphericalCurves:
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

        if selected is None:
            selected_names = tuple(self.edges_by_constellation)
        else:
            requested = frozenset(str(name) for name in selected)
            self.star_ids_for(requested)
            selected_names = tuple(
                name
                for name in self.edges_by_constellation
                if name in requested
            )
        selected_star_ids = self.star_ids_for(selected_names)
        missing = selected_star_ids.difference(self._catalogue_star_ids())
        if missing:
            values = ", ".join(str(value) for value in sorted(missing))
            warnings.warn(
                "Constellation-line stars are absent from the stellar "
                f"catalogue and cannot be drawn: {values}",
                UnresolvedConstellationStarWarning,
                stacklevel=2,
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

        for abbreviation in selected_names:
            edges = self.edges_by_constellation[abbreviation]
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
                "star_ids": self.star_ids,
                "resolvable_star_ids": self.resolvable_star_ids,
                "unresolved_star_ids": missing,
            },
        )
