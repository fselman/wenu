"""Regression tests for canonical pre-projection polygon clipping."""

from pathlib import Path

import numpy as np

from wenu.geometry.projected import ProjectedPolygons
from wenu.geometry.spherical import SphericalPolygons
from wenu.geometry.viewport import Viewport
from wenu.charts.regional import RegionalChart
from wenu.projections import StereographicProjection
from wenu.rendering import (
    clip_polygons_to_latitude,
    project_geometry_for_viewport,
    project_polygons_to_projection_cap,
    projection_cap_for_viewport,
)
from wenu.sky import CelestialSphere
from wenu.sky.sky_layer import SkyLayer


class PolygonLayer(SkyLayer):
    def spherical_geometry(self, observer):
        return SphericalPolygons(
            lon_deg=(
                [-10.0, 10.0, 10.0, -10.0],
                [-10.0, 10.0, 10.0, -10.0],
            ),
            lat_deg=(
                [80.0, 80.0, 60.0, 60.0],
                [-50.0, -50.0, -70.0, -70.0],
            ),
            names=("near", "far"),
            metadata={"level": np.asarray([1, 2])},
        )


class RecordingRenderer:
    def __init__(self):
        self.viewport = None
        self.geometry = None

    def apply_viewport(self, viewport):
        self.viewport = viewport

    def draw(self, geometry, **style):
        self.geometry = geometry
        return ()


def test_viewport_cap_contains_all_four_corners():
    projection = StereographicProjection(radius=2.0)
    viewport = Viewport(-0.5, 0.75, -0.25, 0.6)
    cap = projection_cap_for_viewport(projection, viewport)
    corner_radius = max(
        np.hypot(x, y)
        for x in (viewport.x_min, viewport.x_max)
        for y in (viewport.y_min, viewport.y_max)
    )
    corner_angle = projection.angular_radius_for_projected_radius(
        corner_radius
    )
    assert cap > corner_angle
    assert cap < 90.0


def test_polygons_are_clipped_before_the_unsafe_full_projection():
    projection = StereographicProjection()
    viewport = Viewport(-0.6, 0.6, -0.6, 0.6)
    projected = project_geometry_for_viewport(
        PolygonLayer().spherical_geometry(object()),
        projection=projection,
        viewport=viewport,
    )
    assert isinstance(projected, ProjectedPolygons)
    assert [polygon.name for polygon in projected] == ["near"]
    assert projected.metadata["level"].tolist() == [1]
    assert projected.metadata["projection_domain_clipped"]
    assert np.all(np.isfinite(projected[0].x))
    assert np.all(np.isfinite(projected[0].y))


def test_regional_chart_uses_canonical_projection_before_prepare():
    sky = CelestialSphere(object())
    layer = sky.add(PolygonLayer())
    renderer = RecordingRenderer()
    observed = {}

    def prepare(spherical, projected):
        observed["names"] = [item.name for item in projected]
        return projected

    chart = RegionalChart(
        center_alt_deg=90.0,
        center_az_deg=0.0,
        field_width_deg=34.0,
        field_height_deg=34.0,
    )
    chart.render(
        sky,
        renderer=renderer,
        layer_options={
            layer: {
                "prepare": prepare,
            }
        },
    )
    assert renderer.viewport == chart.viewport
    assert observed["names"] == ["near"]
    assert [item.name for item in renderer.geometry] == ["near"]


def test_projection_domain_and_horizon_clipping_remain_composable():
    spherical = PolygonLayer().spherical_geometry(object())
    projected = project_polygons_to_projection_cap(
        spherical,
        projection=StereographicProjection(),
        angular_radius_deg=45.0,
    )
    clipped = clip_polygons_to_latitude(
        spherical,
        projected,
        minimum=70.0,
    )
    assert [polygon.name for polygon in clipped] == ["near"]
    assert np.all(np.isfinite(clipped[0].x))
    assert np.all(np.isfinite(clipped[0].y))


def test_summer_triangle_is_part_of_chart_regression_suite():
    source = Path("examples/atlas_summer_triangle.py").read_text(
        encoding="utf-8"
    )
    assert "RegionalChart.from_constellations(" in source
    assert "sky.add_milky_way_isophotes()" in source
    assert "clip_polygons_to_projection_cap" not in source


def test_circumpolar_lmc_boundary_crosses_projected_lmc():
    namespace = {}
    source = Path("examples/circumpolar_atlas.py").read_text(
        encoding="utf-8"
    )
    exec(compile(source, "circumpolar_atlas.py", "exec"), namespace)
    sky, chart, _, _ = namespace["build_chart"]()
    lmc = sky.magellanic_cloud_isophotes["lmc"]
    spherical = lmc.spherical_geometry(sky.observer)
    projected = chart.projection.project_polygons(spherical)
    field_radius = chart.projection.projected_radius(
        chart.angular_radius_deg
    )
    radii = np.concatenate(
        [np.hypot(polygon.x, polygon.y) for polygon in projected]
    )
    assert np.any(radii < field_radius)
    assert np.any(radii > field_radius)
