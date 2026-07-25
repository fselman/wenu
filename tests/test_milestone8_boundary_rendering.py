"""Regression test for transitional boundary rendering."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from wenu.projected import ProjectedPolygon, ProjectedPolygons
from wenu.renderers.constellation_boundaries import (
    ConstellationBoundaryRenderingAdapter,
)
from wenu.spherical import SphericalPolygons


class StubBoundaries:
    def spherical_geometry(self, observer):
        return SphericalPolygons(
            lon_deg=([0.0, 10.0, 10.0, 0.0, 0.0],),
            lat_deg=([20.0, 20.0, 30.0, 30.0, 20.0],),
            ids=["TST"],
        )


class StubProjection:
    def project_geometry(self, geometry):
        return ProjectedPolygons(
            items=[
                ProjectedPolygon(
                    x=geometry.lon_deg[0],
                    y=geometry.lat_deg[0],
                    name="TST",
                )
            ]
        )


def test_adapter_renders_projected_boundary_outline():
    adapter = ConstellationBoundaryRenderingAdapter(
        StubBoundaries(),
        SimpleNamespace(),
    )
    figure, ax = plt.subplots()

    artists = adapter.draw(ax, StubProjection())

    assert len(artists) == 1
    np.testing.assert_allclose(
        artists[0].get_xdata(),
        [0.0, 10.0, 10.0, 0.0, 0.0],
    )
    plt.close(figure)
