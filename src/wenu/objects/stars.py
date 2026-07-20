# src/wenu/objects/stars.py

from importlib.resources import as_file

import numpy as np

from skyfield.api import Star
from skyfield.data import hipparcos

from wenu.resources import catalog_path


class Stars:
    """
    Hipparcos star field.

    The full magnitude-limited catalogue is stored in ``catalog``.
    The currently selected stars are stored in ``hip_df``.
    """

    def __init__(
        self,
        observer,
        catalog="hipparcos",
        magnitude_limit=5.5,
    ):
        self.observer = observer
        self.catalog_name = catalog
        self.magnitude_limit = magnitude_limit

        # Magnitude-limited catalogue; never modified by altitude filtering.
        self.catalog = None

        # Current altitude-filtered catalogue.
        self.hip_df = None

        # Skyfield Star object corresponding to self.catalog.
        self.skyfield_stars = None

        # Current calculated/projected coordinates.
        self.alt = None
        self.az = None
        self.x = None
        self.y = None
        self.sizes = None

        self.projection = None
        self.artist = None

    def load(self, 
             *,
             catalog=None,
             filename=None,):
        """
        Load a stellar catalog and apply the magnitude limit.

        Parameters
        ----------
        catalog : str, optional
            Name of a catalogue bundled with Wenu. Defaults to the
            catalogue specified when the Stars object was created.

        filename : str or path-like, optional
            Explicit catalogue filename. This is retained as an override
            for external or user-supplied catalogue files.
        """

        if catalog is not None:
            self.catalog_name = catalog

        if filename is not None:
            with open(filename, "rb") as file:
                hip = hipparcos.load_dataframe(file)
        else:
            resource = catalog_path(self.catalog_name)

            with as_file(resource) as path:
                with open(path, "rb") as file:
                    hip = hipparcos.load_dataframe(file)

        self.catalog = hip[
            hip["magnitude"] <= self.magnitude_limit
        ].copy()

        self.hip_df = self.catalog.copy()

        self.skyfield_stars = Star(
            ra_hours=self.catalog["ra_hours"].to_numpy(),
            dec_degrees=self.catalog["dec_degrees"].to_numpy(),
        )

        return self.catalog

    def compute_altaz(self, alt_min=-10.0):
        """
        Compute apparent Alt/Az and select stars above ``alt_min``.

        This method always starts from the unchanged magnitude-limited
        catalogue, so repeated calls remain consistent.
        """

        if self.catalog is None or self.skyfield_stars is None:
            raise RuntimeError(
                "Hipparcos has not been loaded. Call stars.load() first."
            )

        apparent = (
            self.observer.skyfield
            .at(self.observer.t)
            .observe(self.skyfield_stars)
            .apparent(deflectors=[])
        )

        alt, az, _ = apparent.altaz()

        alt_all = np.asarray(alt.degrees)
        az_all = np.asarray(az.degrees)

        mask = alt_all > alt_min

        # Always filter the original catalogue, never the previous selection.
        self.hip_df = self.catalog.iloc[
            np.flatnonzero(mask)
        ].copy()

        self.alt = alt_all[mask]
        self.az = az_all[mask]

        return self.alt, self.az

    def project(self, projection):
        """
        Project the current Alt/Az coordinates.
        """

        if self.alt is None or self.az is None:
            raise RuntimeError(
                "Alt/Az has not been computed. "
                "Call compute_altaz() first."
            )

        self.projection = projection
        self.x, self.y = projection.project(
            self.alt,
            self.az,
        )

        self.x = np.asarray(self.x)
        self.y = np.asarray(self.y)

        return self.x, self.y

    def compute_sizes(
        self,
        scale=1.5,
        reference_magnitude=5.0,
        exponent=0.35,
        minimum=1.0,
    ):
        """
        Compute Matplotlib marker areas from stellar magnitudes.
        """

        if self.hip_df is None or len(self.hip_df) == 0:
            raise RuntimeError("No currently selected stars.")

        magnitudes = self.hip_df[
            "magnitude"
        ].to_numpy()

        sizes = scale * 10.0 ** (
            exponent * (
                reference_magnitude - magnitudes
            )
        )

        sizes = np.maximum(
            sizes,
            minimum,
        )

        self.sizes = sizes
        return sizes


    def prepare(
        self,
        projection,
        alt_min=-10.0,
    ):
        """
        Compute Alt/Az, project the stars, and calculate marker sizes.
        """

        self.compute_altaz(
            alt_min=alt_min,
        )

        self.project(
            projection,
        )

        self.compute_sizes()

        self._check_alignment()

        return self.x, self.y

    def draw(
        self,
        ax,
        projection,
        color="white",
        alt_min=-10.0,
        zorder=3,
        **scatter_kwargs,
    ):
        """
        Prepare and draw the Hipparcos star field.
        """

        self.prepare(
            projection=projection,
            alt_min=alt_min,
        )

        self.artist = ax.scatter(
            self.x,
            self.y,
            s=self.sizes,
            c=color,
            linewidths=0,
            zorder=zorder,
            **scatter_kwargs,
        )

        return self.artist

    def _check_alignment(self):
        """
        Verify that the catalogue and coordinate arrays remain aligned.
        """

        lengths = {
            "hip_df": len(self.hip_df),
            "alt": len(self.alt),
            "az": len(self.az),
            "x": len(self.x),
            "y": len(self.y),
            "sizes": len(self.sizes),
        }

        if len(set(lengths.values())) != 1:
            raise RuntimeError(
                "Star catalogue and projected arrays "
                "are not aligned: "
                f"{lengths}"
            )

    @property
    def hip_index(self):
        """
        Map HIP identifier to row position in the current projected arrays.
        """

        if self.hip_df is None:
            return {}

        return {
            int(hip_id): index
            for index, hip_id
            in enumerate(self.hip_df.index)
        }
