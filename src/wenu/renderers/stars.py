"""Temporary renderer compatibility for the Stars domain layer."""

from __future__ import annotations

import numpy as np

from wenu.renderers import layers, render_points


class StarsRenderingAdapter:
    """Bridge geometry-only Stars to the pre-migration drawing pipeline.

    Constellation classes temporarily consume the projected arrays exposed
    here. That dependency is removed when those classes migrate in their
    dedicated roadmap milestones.
    """

    def __init__(self, stars, observer):
        self.stars = stars
        self.observer = observer
        self.geometry = None
        self.projected = None
        self.alt = None
        self.az = None
        self.x = None
        self.y = None
        self.sizes = None
        self.artist = None

    @property
    def hip_df(self):
        return self.stars.hip_df

    @property
    def hip_index(self):
        return self.stars.hip_index

    def prepare(
        self,
        projection,
        alt_min=-10.0,
    ):
        self.geometry = self.stars.spherical_geometry(
            self.observer,
            alt_min=alt_min,
        )
        self.projected = projection.project_geometry(self.geometry)

        self.az = self.geometry.lon_deg
        self.alt = self.geometry.lat_deg
        self.x = self.projected.x
        self.y = self.projected.y
        self.sizes = self.compute_sizes()

        self._check_alignment()
        return self.x, self.y

    def compute_sizes(
        self,
        scale=1.5,
        reference_magnitude=5.0,
        exponent=0.35,
        minimum=1.0,
    ):
        if self.geometry is None:
            raise RuntimeError("Stellar geometry has not been prepared.")

        magnitudes = np.asarray(
            self.geometry.metadata["magnitude"],
            dtype=float,
        )
        sizes = scale * 10.0 ** (
            exponent * (reference_magnitude - magnitudes)
        )
        self.sizes = np.maximum(sizes, minimum)
        return self.sizes

    def draw(
        self,
        ax,
        projection,
        color="white",
        alt_min=-10.0,
        zorder=layers.STARS,
        **scatter_kwargs,
    ):
        self.prepare(
            projection=projection,
            alt_min=alt_min,
        )
        self.artist = render_points(
            ax,
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
                "Star catalogue and rendering arrays are not aligned: "
                f"{lengths}"
            )

