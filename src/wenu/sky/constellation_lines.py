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
    _SERPENS_COMPONENTS = ("Ser1", "Ser2")

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
        requested = self._expanded_names(constellations)
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
                (name, []) for name in self._expanded_names(
                    self.constellations
                )
            )

        accepted = (
            None
            if self.constellations is None
            else self._expanded_names(self.constellations)
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
                    accepted is not None
                    and abbreviation not in accepted
                    and not (
                        abbreviation == "Ser"
                        and set(self._SERPENS_COMPONENTS) & accepted
                    )
                ):
                    continue

                try:
                    edge_count = int(parts[1])
                    hip_ids = [int(value) for value in parts[2:]]
                except ValueError as error:
                    raise ValueError(
                        f"Invalid .fab line at {path}:{line_number}\n"
                        f"{raw_line.rstrip()}"
                    ) from error

                if len(hip_ids) < 2:
                    continue

                if abbreviation == "Ser" and len(hip_ids) == 2 * edge_count:
                    components = self._serpens_components(hip_ids)
                    for name, edges in zip(
                        self._SERPENS_COMPONENTS, components, strict=True
                    ):
                        if accepted is None or name in accepted:
                            self.edges.extend(edges)
                            self.edges_by_constellation.setdefault(
                                name, []
                            ).extend(edges)
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

    @classmethod
    def _expanded_names(cls, names):
        expanded = set(map(str, names))
        if "Ser" in expanded:
            expanded.remove("Ser")
            expanded.update(cls._SERPENS_COMPONENTS)
        return frozenset(expanded)

    @staticmethod
    def _serpens_components(hip_ids):
        """Return both Ser figures while retaining their visual bridge."""
        edges = list(zip(hip_ids[::2], hip_ids[1::2], strict=True))
        components = []
        remaining = edges[:]
        while remaining:
            component = [remaining.pop(0)]
            vertices = set(component[0])
            changed = True
            while changed:
                changed = False
                retained = []
                for edge in remaining:
                    if vertices.intersection(edge):
                        component.append(edge)
                        vertices.update(edge)
                        changed = True
                    else:
                        retained.append(edge)
                remaining = retained
            components.append(component)
        if len(components) != 2:
            raise ValueError(
                "The packaged Serpens figure must contain two components."
            )
        components[0].append(
            (components[0][-1][1], components[1][0][0])
        )
        return tuple(components)

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
            requested = self._expanded_names(selected)
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

        # Reuse the maximal stellar transformation without changing the
        # renderer-facing active stellar selection.
        source, alt_deg, az_deg = self.stars.observed_altaz(observer)
        source_positions = {
            int(hip_id): index
            for index, hip_id in enumerate(source.index)
        }
        catalogue_index = {
            int(hip_id): source_positions[int(hip_id)]
            for hip_id in self.stars.catalog.index
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
