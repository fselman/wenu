"""Observer-local altitude-zero reference geometry."""

from __future__ import annotations

import numpy as np

from wenu.coordinates import observer_altaz_spec

from wenu.geometry.spherical import SphericalPolygons
from wenu.sky.coordinate_grids import AltAzGrid
from wenu.sky.geometrical_object import GeometricalObject


class HorizonReference(GeometricalObject):
    """The observer horizon as one semantic spherical reference curve."""

    layer_name = "horizon"

    def __init__(self, observer=None, *, samples=721):
        if int(samples) < 4:
            raise ValueError("samples must be at least 4.")
        self.observer = observer
        self.samples = int(samples)

    def spherical_geometry(self, observer):
        """Return the closed altitude-zero curve for ``observer``."""
        resolved = self.observer if observer is None else observer
        if resolved is None:
            raise RuntimeError(
                "An Observer is required for horizon geometry."
            )
        geometry = AltAzGrid(
            resolved,
            samples=self.samples,
        ).horizon()
        geometry.metadata["reference"] = "horizon"
        return geometry

    def visible_hemisphere_geometry(
        self,
        observer,
        *,
        radial_step_deg=5.0,
    ):
        """Return tessellated altitude-nonnegative mask openings."""
        horizon = self.spherical_geometry(observer)
        azimuth = np.asarray(horizon.lon_deg[0], dtype=float)
        step = float(radial_step_deg)
        if not np.isfinite(step) or not 0.0 < step <= 45.0:
            raise ValueError(
                "radial_step_deg must be finite and between 0 and 45."
            )
        altitude = np.arange(0.0, 90.0, step, dtype=float)
        altitude = np.concatenate((altitude, [90.0]))
        longitudes = []
        latitudes = []
        for start, stop in zip(azimuth, np.roll(azimuth, -1)):
            ascending = np.full(altitude.shape, start, dtype=float)
            descending = np.full(altitude.shape, stop, dtype=float)
            longitudes.append(np.concatenate((
                ascending,
                descending[-2::-1],
            )))
            latitudes.append(np.concatenate((
                altitude,
                altitude[-2::-1],
            )))
        count = len(longitudes)
        return SphericalPolygons(
            lon_deg=tuple(longitudes),
            lat_deg=tuple(latitudes),
            coordinate_spec=observer_altaz_spec(
                resolved, provider="wenu analytic horizon"
            ),
            ids=np.asarray(
                [f"above_horizon_{index}" for index in range(count)],
                dtype=object,
            ),
            names=np.asarray(["above_horizon"] * count, dtype=object),
            metadata={
                "mask_opening": "above_horizon",
                "source_coordinate_system": "altaz",
                "minimum_altitude_deg": 0.0,
            },
        )