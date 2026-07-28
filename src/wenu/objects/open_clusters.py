"""Vectorized fixed-symbol layer for Galactic open clusters."""

from __future__ import annotations

from importlib.resources import as_file
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table

from wenu.geometry.spherical import SphericalPoints
from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import nonstellar_catalog_path


class OpenClusters(AstronomicalObject):
    """Established and likely optically visible Galactic open clusters."""

    layer_name = "open_clusters"

    def __init__(self, observer, *, selected=None):
        self.observer = observer
        self.selected = None if selected is None else tuple(selected)
        self.catalog = None
        self.source = None

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
        return self.catalog

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
                ids=identifiers,
                labels=identifiers,
                names=identifiers,
                metadata=metadata,
            )

        centers = SkyCoord(
            ra=np.asarray(table["ra_deg"], dtype=float) * u.deg,
            dec=np.asarray(table["dec_deg"], dtype=float) * u.deg,
            frame="icrs",
        )
        horizontal = centers.transform_to(resolved.altaz_frame)
        return SphericalPoints(
            lon_deg=horizontal.az.to_value(u.deg),
            lat_deg=horizontal.alt.to_value(u.deg),
            ids=identifiers,
            labels=identifiers,
            names=identifiers,
            metadata=metadata,
        )
