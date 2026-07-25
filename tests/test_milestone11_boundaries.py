"""Milestone 11 completion tests for constellation boundaries."""

from collections import OrderedDict
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from astropy.time import Time

from wenu.projected import ProjectedPolygon, ProjectedPolygons
from wenu.renderers.constellation_boundaries import (
    ConstellationBoundaryRenderingAdapter,
)
from wenu.sky.constellation_boundaries import ConstellationBoundaries
from wenu.spherical import SphericalPolygons


def make_boundaries():
    boundaries = object.__new__(ConstellationBoundaries)
    boundaries.observer = None
    boundaries.boundaries_name = "iau"
    boundaries.filename = None
    boundaries.constellations = None
    boundaries.sampling_step_deg = 2.0
    boundaries.vertices = OrderedDict(
        {
            "TST": np.asarray(
                [
                    [1.0, -20.0],
                    [2.0, -20.0],
                    [2.0, -10.0],
                    [1.0, -10.0],
                ],
                dtype=float,
            )
        }
    )
    boundaries.sampled_vertices = OrderedDict()
    return boundaries


def make_observer(time):
    return SimpleNamespace(
        t_astropy=Time(time),
        lat_deg=-33.0,
        lon_deg=-71.5,
        elevation_m=52.0,
    )


def test_boundary_geometry_is_evaluated_at_observer_time():
    boundaries = make_boundaries()

    first = boundaries.spherical_geometry(
        make_observer("2026-08-16T01:00:00")
    )
    second = boundaries.spherical_geometry(
        make_observer("2026-08-16T07:00:00")
    )

    # Native B1875 sampling is stable, but its observer-time Alt/Az
    # realization must change with time.
    assert not np.allclose(first.lon_deg[0], second.lon_deg[0])
    assert not np.allclose(first.lat_deg[0], second.lat_deg[0])
    assert first.metadata["source_equinox"] == "B1875.0"
    assert second.metadata["source_equinox"] == "B1875.0"


class StubBoundaries:
    def spherical_geometry(self, observer):
        return SphericalPolygons(
            lon_deg=([0.0, 10.0, 10.0, 0.0, 0.0],),
            lat_deg=([20.0, 20.0, 30.0, 30.0, 20.0],),
            ids=["TST"],
            names=["TST"],
        )


class CountingProjection:
    def __init__(self):
        self.calls = 0

    def project_geometry(self, geometry):
        self.calls += 1
        return ProjectedPolygons(
            items=[
                ProjectedPolygon(
                    x=geometry.lon_deg[0],
                    y=geometry.lat_deg[0],
                    name="TST",
                )
            ]
        )


def test_boundary_renderer_projects_collection_exactly_once():
    projection = CountingProjection()
    adapter = ConstellationBoundaryRenderingAdapter(
        StubBoundaries(),
        SimpleNamespace(),
    )
    figure, ax = plt.subplots()

    artists = adapter.draw(ax, projection)

    assert projection.calls == 1
    assert len(artists) == 1
    plt.close(figure)

