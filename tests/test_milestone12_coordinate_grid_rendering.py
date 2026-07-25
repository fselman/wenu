"""Milestone 12 rendering tests for coordinate grids."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from wenu.projected import ProjectedCurve, ProjectedCurves, ProjectedGrid
from wenu.renderers.coordinate_grids import (
    CoordinatesGridRenderingAdapter,
)
from wenu.spherical import SphericalCurves, SphericalGrid


class CountingProjection:
    def __init__(self):
        self.calls = 0

    def project_geometry(self, geometry):
        self.calls += 1
        return ProjectedGrid(
            components={
                name: ProjectedCurves(
                    items=[
                        ProjectedCurve(x=lon, y=lat)
                        for lon, lat in zip(
                            curves.lon_deg,
                            curves.lat_deg,
                        )
                    ]
                )
                for name, curves in geometry.components.items()
            }
        )


def test_complete_grid_is_projected_exactly_once():
    geometry = SphericalGrid(
        components={
            "meridians": SphericalCurves(
                lon_deg=([0.0, 1.0],),
                lat_deg=([10.0, 20.0],),
            ),
            "parallels": SphericalCurves(
                lon_deg=([2.0, 3.0],),
                lat_deg=([30.0, 40.0],),
                closed=[True],
            ),
        }
    )
    projection = CountingProjection()
    adapter = CoordinatesGridRenderingAdapter(observer=object())
    figure, ax = plt.subplots()

    artists = adapter.draw_grid(ax, projection, geometry)

    assert projection.calls == 1
    assert len(artists) == 2
    plt.close(figure)


def test_closed_visibility_run_is_joined_across_sample_seam():
    segments = CoordinatesGridRenderingAdapter._visible_segments(
        x=[0.0, 1.0, 2.0, 3.0, 4.0],
        y=[0.0, 1.0, 2.0, 3.0, 4.0],
        altitude=[10.0, 10.0, -1.0, 10.0, 10.0],
        closed=True,
        min_altitude=0.0,
    )

    assert len(segments) == 1
    x, _ = segments[0]
    assert x.tolist() == [3.0, 4.0, 0.0, 1.0]

