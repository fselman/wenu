"""Regression tests for the transitional celestial-point renderer."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from wenu.projected import ProjectedPoints
from wenu.renderers.celestial_points import (
    CelestialPointsRenderingAdapter,
)
from wenu.spherical import SphericalPoints


class StubPoints:
    def spherical_geometry(self, observer):
        return SphericalPoints(
            lon_deg=[10.0, 20.0],
            lat_deg=[30.0, -5.0],
            labels=["visible", "hidden"],
            metadata={
                "marker": np.asarray(["+", "x"], dtype=object),
                "size": np.asarray([40.0, 30.0]),
                "color": np.asarray(["cyan", "white"], dtype=object),
                "zorder": np.asarray([None, None], dtype=object),
                "style": (
                    {"fontsize": 11, "label_offset": (0.1, 0.2)},
                    {},
                ),
            },
        )


class StubProjection:
    def __init__(self):
        self.calls = 0

    def project_geometry(self, geometry):
        self.calls += 1
        return ProjectedPoints(
            x=geometry.lon_deg,
            y=geometry.lat_deg,
            labels=geometry.labels,
            metadata=geometry.metadata,
        )


def test_adapter_projects_collection_once_and_filters_visibility():
    projection = StubProjection()
    adapter = CelestialPointsRenderingAdapter(
        StubPoints(),
        SimpleNamespace(),
    )
    figure, ax = plt.subplots()

    artists = adapter.draw(ax, projection)

    assert projection.calls == 1
    assert len(artists) == 2
    assert artists[1].get_text() == "visible"
    assert artists[1].get_position() == (10.1, 30.2)
    plt.close(figure)

