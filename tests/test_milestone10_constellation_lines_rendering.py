"""Milestone 10 rendering tests for constellation lines."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from wenu.projected import ProjectedCurve, ProjectedCurves
from wenu.renderers.constellation_lines import (
    ConstellationLinesRenderingAdapter,
)
from wenu.spherical import SphericalCurves


class StubLines:
    def spherical_geometry(self, observer):
        return SphericalCurves(
            lon_deg=([0.0, 1.0], [2.0, 3.0]),
            lat_deg=([10.0, 20.0], [10.0, -1.0]),
            names=["Cru", "Cru"],
        )


class StubProjection:
    def __init__(self):
        self.calls = 0

    def project_geometry(self, geometry):
        self.calls += 1
        return ProjectedCurves(
            items=[
                ProjectedCurve(x=lon, y=lat)
                for lon, lat in zip(
                    geometry.lon_deg,
                    geometry.lat_deg,
                )
            ]
        )


def test_adapter_projects_once_and_filters_hidden_edges():
    projection = StubProjection()
    adapter = ConstellationLinesRenderingAdapter(
        StubLines(),
        SimpleNamespace(),
    )
    figure, ax = plt.subplots()

    artists = adapter.draw(ax, projection)

    assert projection.calls == 1
    assert len(artists) == 1
    np.testing.assert_allclose(artists[0].get_xdata(), [0.0, 1.0])
    plt.close(figure)


def test_adapter_applies_maximum_projected_length():
    projection = StubProjection()
    adapter = ConstellationLinesRenderingAdapter(
        StubLines(),
        SimpleNamespace(),
        max_segment_length=0.5,
    )
    figure, ax = plt.subplots()

    assert adapter.draw(ax, projection) == []
    plt.close(figure)

