"""Rendered circular-planisphere composition contracts."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu import FullSkyChart, MatplotlibRenderer, compose_chart
from wenu.charts.export_workflow import _composition_export_options
from wenu.charts.legend_composition import apply_legend_placement
from wenu.charts.legend_plan import default_chart_legend_plan


pytestmark = pytest.mark.visual


class RecordingRenderer:
    def __init__(self):
        self.calls = []

    def set_circular_background(self, boundary, *, color):
        self.calls.append(("background", boundary, color))

    def set_clip_boundary(self, boundary, *, style):
        self.calls.append(("boundary", boundary, style))

    def set_axes_frame_visible(self, visible):
        self.calls.append(("frame", visible))


class EmptySky:
    stars = None
    nonstellar = None
    galaxies = None
    milky_way_isophotes = None
    magellanic_clouds = None
    globular_clusters = None
    open_clusters = None
    supernova_remnants = None
    planetary_nebulae = None
    constellation_lines = None
    constellation_labels = None
    constellation_boundaries = None
    coordinate_grids = ()
    points = None
    layers = ()

    def draw_chart(self, **kwargs):
        return SimpleNamespace(**kwargs)


@pytest.mark.parametrize("style", ["atlas", "cartoon"])
@pytest.mark.parametrize("mode", ["print", "presentation"])
def test_full_sky_uses_shared_opaque_circular_background(style, mode):
    chart = FullSkyChart()
    composition = compose_chart(chart, style=style, mode=mode)
    renderer = RecordingRenderer()

    chart.render(EmptySky(), renderer, style=composition.style)

    background = renderer.calls[0]
    boundary = renderer.calls[1]
    assert background[0] == "background"
    assert np.array_equal(background[1].x, chart.horizon.x)
    assert np.array_equal(background[1].y, chart.horizon.y)
    assert background[2] == composition.style.canvas.sky_color
    assert boundary[0] == "boundary"
    assert np.array_equal(boundary[1].x, chart.horizon.x)
    assert np.array_equal(boundary[1].y, chart.horizon.y)
    assert boundary[2]["facecolor"] == "none"
    assert boundary[2]["edgecolor"] is not None


def test_planisphere_export_has_transparent_corner_and_opaque_center(tmp_path):
    chart = FullSkyChart()
    composition = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )
    figure, ax = plt.subplots(figsize=(2.0, 2.0), dpi=50)
    renderer = MatplotlibRenderer(ax)
    ax.set_xlim(chart.viewport.x_min, chart.viewport.x_max)
    ax.set_ylim(chart.viewport.y_min, chart.viewport.y_max)
    ax.set_aspect("equal")
    ax.set_axis_off()
    chart.render(EmptySky(), renderer, style=composition.style)

    output = tmp_path / "planisphere.png"
    options = _composition_export_options(composition)
    options.save(figure, output)
    image = plt.imread(output)

    assert image[0, 0, 3] == 0.0
    center = image[image.shape[0] // 2, image.shape[1] // 2]
    assert center[3] == 1.0
    plt.close(figure)


def test_default_planisphere_legends_are_outside_and_disjoint_from_axes():
    plan = default_chart_legend_plan("planisphere")
    assert plan.objects.outside is True
    assert plan.stars.outside is True
    assert plan.objects.location == "upper right"
    assert plan.stars.location == "lower right"

    figure, ax = plt.subplots()
    object_line, = ax.plot([], [], label="Objects")
    objects = ax.legend(handles=[object_line], loc="upper right")
    ax.add_artist(objects)
    star_line, = ax.plot([], [], label="Magnitudes")
    stars = ax.legend(handles=[star_line], loc="lower right")
    apply_legend_placement(objects, plan.objects)
    apply_legend_placement(stars, plan.stars)
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    axes_bounds = ax.get_window_extent(renderer)

    assert not objects.get_window_extent(renderer).overlaps(axes_bounds)
    assert not stars.get_window_extent(renderer).overlaps(axes_bounds)
    plt.close(figure)


def test_horizon_geometry_and_visibility_do_not_depend_on_content():
    chart = FullSkyChart()
    baseline = chart.horizon
    hidden = compose_chart(chart, style="atlas")
    populated = compose_chart(chart, style="atlas")

    assert np.array_equal(chart.horizon.x, baseline.x)
    assert np.array_equal(chart.horizon.y, baseline.y)
    assert np.array_equal(hidden.context.clip_boundary.x, baseline.x)
    assert np.array_equal(hidden.context.clip_boundary.y, baseline.y)
    assert np.array_equal(populated.context.clip_boundary.x, baseline.x)
    assert np.array_equal(populated.context.clip_boundary.y, baseline.y)
