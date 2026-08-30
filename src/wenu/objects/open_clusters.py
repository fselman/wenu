"""Vectorized fixed-symbol layer for Galactic open clusters."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path

import numpy as np
from astropy.table import Table

from wenu.coordinates import PositionStatus
from wenu.coordinates import icrs_catalogue_spec, observer_altaz_spec
from wenu.geometry.spherical import SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path
from wenu.sky.observed_cache import catalogue_point_altaz


class OpenClusters(AstronomicalObject):
    """Established and likely optically visible Galactic open clusters."""

    layer_name = "open_clusters"

    def __init__(self, observer, *, selected=None):
        self.observer = observer
        self.selected = None if selected is None else tuple(selected)
        self.catalog = None
        self.source = None
        self._source_revision = 0
        self._observed_point_cache = {}

    def load(self, *, filename=None):
        """Load the normalized Dias/HEASARC catalogue snapshot."""
        if filename is None:
            resource = nonstellar_catalog_path("open_clusters")
            with as_file(resource) as path:
                self.source = resource
                table = Table.read(path)
        else:
            self.source = Path(filename)
            table = Table.read(self.source)
        self._validate(table)
        self.catalog = table
        self._source_revision += 1
        self._observed_point_cache.clear()
        return self.catalog

    def position(self, instant=None) -> SphericalPoints:
        """Return selected native open-cluster catalogue centres in ICRS."""
        del instant
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call open_clusters.load() first."
            )
        table = self._selected_table(None)
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": "openclust",
            "coordinate_system": "icrs",
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = np.asarray(table[name])
        provenance = () if self.source is None else (str(self.source),)
        return SphericalPoints(
            lon_deg=np.asarray(table["ra_deg"], dtype=float),
            lat_deg=np.asarray(table["dec_deg"], dtype=float),
            coordinate_spec=icrs_catalogue_spec(
                "Dias/HEASARC open-cluster catalogue",
                provenance=provenance,
            ),
            ids=identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )

    @staticmethod
    def _validate(table):
        required = {
            "identifier",
            "ra_deg",
            "dec_deg",
            "apparent_diameter_arcmin",
            "object_type",
        }
        missing = required.difference(table.colnames)
        if missing:
            raise ValueError(
                "Open-cluster catalogue is missing columns: "
                + ", ".join(sorted(missing))
            )

    def _selected_table(self, selected):
        selection = self.selected if selected is None else selected
        if selection is None:
            return self.catalog
        catalogue_ids = np.asarray(
            [
                str(value).strip().casefold()
                for value in self.catalog["identifier"]
            ],
            dtype=object,
        )
        indices = []
        for requested in selection:
            matches = np.flatnonzero(
                catalogue_ids == str(requested).strip().casefold()
            )
            if matches.size:
                indices.append(int(matches[0]))
        return self.catalog[np.asarray(indices, dtype=int)]

    def spherical_geometry(
        self,
        observer,
        *,
        selected=None,
        minimum_size_arcmin=None,
    ) -> SphericalPoints:
        """Return vectorized Alt/Az centers for open-cluster symbols."""
        if self.catalog is None:
            raise RuntimeError(
                "The catalogue has not been loaded. "
                "Call open_clusters.load() first."
            )
        resolved = self.observer if observer is None else observer
        if resolved is None or not hasattr(resolved, "altaz_frame"):
            raise ValueError(
                "An observer with an altaz_frame is required."
            )
        table = self._selected_table(selected)
        if minimum_size_arcmin is not None:
            minimum = float(minimum_size_arcmin)
            if not np.isfinite(minimum) or minimum < 0.0:
                raise ValueError(
                    "minimum_size_arcmin must be finite and "
                    "non-negative."
                )
            sizes = np.asarray(
                table["apparent_diameter_arcmin"],
                dtype=float,
            )
            table = table[np.isfinite(sizes) & (sizes >= minimum)]
        identifiers = np.asarray(table["identifier"], dtype=object)
        metadata = {
            "catalog": "openclust",
            "coordinate_system": "altaz",
            "geometry_kind": "cartographic_symbol",
            "symbol": "open_cluster",
        }
        for name in table.colnames:
            if name not in ("identifier", "ra_deg", "dec_deg"):
                metadata[name] = np.asarray(table[name])

        if len(table) == 0:
            return SphericalPoints(
                lon_deg=np.asarray([], dtype=float),
                lat_deg=np.asarray([], dtype=float),
                coordinate_spec=observer_altaz_spec(
                    resolved, position_status=PositionStatus.APPARENT, provider="astropy OpenClust"
                ),
                ids=identifiers,
                labels=identifiers,
                names=identifiers,
                metadata=metadata,
            )

        azimuth, altitude = catalogue_point_altaz(
            self._observed_point_cache,
            resolved,
            source_table=self.catalog,
            selected_table=table,
            source_key=("open_clusters", self._source_revision),
        )
        return SphericalPoints(
            lon_deg=azimuth,
            lat_deg=altitude,
            coordinate_spec=observer_altaz_spec(
                resolved, position_status=PositionStatus.APPARENT, provider="astropy OpenClust"
            ),
            ids=identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )