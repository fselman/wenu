"""Regression tests for the transitional Stars rendering adapter."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PathCollection

from wenu.objects.stars import Stars
from wenu.projected import ProjectedPoints
from wenu.renderers import layers
from wenu.renderers.stars import StarsRenderingAdapter
from wenu.spherical import SphericalPoints


class DummyProjection:
    def project_geometry(self, geometry):
        return ProjectedPoints(
            x=geometry.lon_deg,
            y=geometry.lat_deg,
            ids=geometry.ids,
            metadata=geometry.metadata,
        )


def test_adapter_renders_stars_without_polluting_domain_layer(monkeypatch):
    observer = SimpleNamespace()
    stars = Stars(observer=observer)
    stars.hip_df = pd.DataFrame(
        {"magnitude": [1.0, 2.0]},
        index=[100, 200],
    )

    geometry = SphericalPoints(
        lon_deg=[10.0, 20.0],
        lat_deg=[30.0, 40.0],
        ids=[100, 200],
        metadata={
            "catalog": "hipparcos",
            "magnitude": np.array([1.0, 2.0]),
        },
    )

    monkeypatch.setattr(
        stars,
        "spherical_geometry",
        lambda supplied_observer, alt_min=-10.0: geometry,
    )

    adapter = StarsRenderingAdapter(stars, observer)
    fig, ax = plt.subplots()
    artist = adapter.draw(ax, DummyProjection())

    assert isinstance(artist, PathCollection)
    assert artist.get_zorder() == layers.STARS
    np.testing.assert_allclose(
        artist.get_offsets(),
        [[10.0, 30.0], [20.0, 40.0]],
    )
    assert adapter.hip_index == {100: 0, 200: 1}
    assert not hasattr(stars, "artist")

    plt.close(fig)
