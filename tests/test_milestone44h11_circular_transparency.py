"""Milestone 44H.1.1 circular-background transparency contracts."""

import matplotlib.pyplot as plt

from wenu import BinocularChart, MatplotlibRenderer, compose_chart
from wenu.charts.export_workflow import _composition_export_options
from wenu.charts.regional import ExportOptions
from wenu.geometry.projected import ProjectedCurve


def circle():
    return ProjectedCurve(
        x=[-1.0, 0.0, 1.0, 0.0],
        y=[0.0, 1.0, 0.0, -1.0],
        closed=True,
    )


def test_circular_background_uses_transparent_canvas(tmp_path):
    figure, axes = plt.subplots(figsize=(2.0, 2.0), dpi=50)
    renderer = MatplotlibRenderer(axes)
    axes.set_xlim(-1.2, 1.2)
    axes.set_ylim(-1.2, 1.2)
    axes.set_aspect("equal")
    axes.set_xticks([])
    axes.set_yticks([])

    background = renderer.set_circular_background(
        circle(),
        color="#123456",
    )
    renderer.set_clip_boundary(
        circle(),
        style={"facecolor": "none", "edgecolor": "black"},
    )
    output = tmp_path / "circular.png"
    ExportOptions(
        dpi=50,
        bbox_inches=None,
        transparent=True,
        facecolor="none",
    ).save(figure, output)

    image = plt.imread(output)
    assert image[0, 0, 3] == 0.0
    center = image[image.shape[0] // 2, image.shape[1] // 2]
    assert center[3] == 1.0
    assert background.get_facecolor()[3] == 1.0
    plt.close(figure)


def test_circular_composition_defaults_to_transparent_export():
    composition = compose_chart(
        BinocularChart(45.0, 180.0),
        style="cartoon",
        mode="presentation",
    )

    options = _composition_export_options(composition)

    assert options.transparent is True
    assert options.facecolor == "none"
