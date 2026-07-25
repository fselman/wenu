"""Stellar catalogue layer producing spherical point geometry."""

from __future__ import annotations

from importlib.resources import as_file

import numpy as np
from skyfield.api import Star
from skyfield.data import hipparcos

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.resources import catalog_path
from wenu.spherical import SphericalPoints


class Stars(AstronomicalObject):
    """A magnitude-limited stellar catalogue."""

    layer_name = "stars"

    def __init__(
        self,
        observer,
        catalog="hipparcos",
        magnitude_limit=5.5,
    ):
        self.observer = observer
        self.catalog_name = catalog
        self.magnitude_limit = magnitude_limit

        # Stable magnitude-limited catalogue.
        self.catalog = None

        # Current observer/altitude selection.
        self.hip_df = None

        # Skyfield representation of the stable catalogue.
        self.skyfield_stars = None

    def load(
        self,
        *,
        catalog=None,
        filename=None,
    ):
        """Load a stellar catalogue and apply the magnitude limit."""
        if catalog is not None:
            self.catalog_name = catalog

        if filename is not None:
            with open(filename, "rb") as file:
                source = hipparcos.load_dataframe(file)
        else:
            resource = catalog_path(self.catalog_name)

            with as_file(resource) as path:
                with open(path, "rb") as file:
                    source = hipparcos.load_dataframe(file)

        self.catalog = source[
            source["magnitude"] <= self.magnitude_limit
        ].copy()
        self.hip_df = self.catalog.copy()

        self.skyfield_stars = Star(
            ra_hours=self.catalog["ra_hours"].to_numpy(),
            dec_degrees=self.catalog["dec_degrees"].to_numpy(),
        )

        return self.catalog

    def compute_altaz(
        self,
        alt_min=-10.0,
        *,
        observer=None,
    ):
        """Return apparent Alt/Az and select stars above ``alt_min``."""
        if self.catalog is None or self.skyfield_stars is None:
            raise RuntimeError(
                "Hipparcos has not been loaded. Call stars.load() first."
            )

        resolved_observer = self.observer if observer is None else observer

        if resolved_observer is None:
            raise ValueError(
                "An observer is required to compute stellar coordinates."
            )

        apparent = (
            resolved_observer.skyfield
            .at(resolved_observer.t)
            .observe(self.skyfield_stars)
            .apparent(deflectors=[])
        )

        alt, az, _ = apparent.altaz()
        alt_all = np.asarray(alt.degrees)
        az_all = np.asarray(az.degrees)
        mask = alt_all > alt_min

        # Always filter the stable catalogue, never the previous selection.
        self.hip_df = self.catalog.iloc[
            np.flatnonzero(mask)
        ].copy()

        return alt_all[mask], az_all[mask]

    def spherical_geometry(
        self,
        observer,
        *,
        alt_min=-10.0,
    ) -> SphericalPoints:
        """Return observer-dependent stellar positions as spherical points."""
        alt_deg, az_deg = self.compute_altaz(
            alt_min=alt_min,
            observer=observer,
        )

        magnitudes = self.hip_df["magnitude"].to_numpy(copy=True)
        hip_ids = self.hip_df.index.to_numpy(copy=True)

        metadata = {
            "catalog": self.catalog_name,
            "magnitude": magnitudes,
        }

        # Preserve colour information when supplied by a catalogue. The
        # bundled Hipparcos table does not currently provide such a column.
        if "color" in self.hip_df.columns:
            metadata["color"] = self.hip_df[
                "color"
            ].to_numpy(copy=True)

        return SphericalPoints(
            lon_deg=az_deg,
            lat_deg=alt_deg,
            ids=hip_ids,
            metadata=metadata,
        )

    @property
    def hip_index(self):
        """Map HIP identifier to row position in the active selection."""
        if self.hip_df is None:
            return {}

        return {
            int(hip_id): index
            for index, hip_id in enumerate(self.hip_df.index)
        }

