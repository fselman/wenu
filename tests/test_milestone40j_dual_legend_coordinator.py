from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend

import wenu.charts.legend_composition as composition
from wenu import (
    ComposedChartLegends,
    LegendPlacement,
    default_chart_legend_plan,
    draw_planned_chart_legends,
)


class Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def star_geometry():
    return (
        SimpleNamespace(
            metadata={"magnitude": np.asarray([-1.0, 0.0, 2.0])}
        ),
        SimpleNamespace(
            x=np.asarray([0.0, 0.2, 0.4]),
            y=np.asarray([0.0, 0.2, 0.4]),
        ),
    )


def fake_object_drawer(
    ax,
    chart,
    sky,
    style,
    *,
    grid=None,
    title=None,
    context_lines=None,
):
    ax.plot([], [], marker="s", label="Galaxy")
    return ax.legend(title=title or "Objects")


def test_coordinator_draws_and_preserves_both_legends(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        fake_object_drawer,
    )
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        default_chart_legend_plan("regional"),
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert isinstance(result, ComposedChartLegends)
    assert isinstance(result.objects, Legend)
    assert isinstance(result.stars.artist, Legend)
    assert len(result.artists) == 2
    assert result.objects in ax.get_children()
    assert result.stars.artist in ax.get_children()
    plt.close(figure)


def test_disabled_object_legend_is_not_called(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("object drawer must not be called")

    monkeypatch.setattr(composition, "draw_chart_legend", fail)
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        default_chart_legend_plan("binocular"),
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert result.objects is None
    assert result.stars.drawn
    plt.close(figure)


def test_disabled_star_legend_is_not_drawn(monkeypatch):
    monkeypatch.setattr(
        composition,
        "draw_chart_legend",
        fake_object_drawer,
    )
    figure, ax = plt.subplots()
    spherical, projected = star_geometry()
    plan = default_chart_legend_plan("regional").with_stars(
        enabled=False
    )
    result = draw_planned_chart_legends(
        ax,
        object(),
        object(),
        object(),
        plan,
        star_spherical=spherical,
        star_projected=projected,
        viewport=Viewport(),
        effective_limit=3.0,
    )
    assert result.objects is not None
    assert result.stars is None
    assert result.artists == (result.objects,)
    plt.close(figure)


def test_explicit_anchor_is_applied():
    figure, ax = plt.subplots()
    legend = ax.legend([], [], loc="upper right")
    placement = LegendPlacement(
        location="lower left",
        anchor=(0.25, 0.35),
    )
    composition.apply_legend_placement(legend, placement)
    bounds = legend.get_bbox_to_anchor().bounds
    display_anchor = ax.transAxes.transform((0.25, 0.35))
    assert bounds[0] == display_anchor[0]
    assert bounds[1] == display_anchor[1]
    plt.close(figure)


def test_outside_placement_uses_an_automatic_anchor():
    figure, ax = plt.subplots()
    legend = ax.legend([], [], loc="upper right")
    placement = LegendPlacement(
        location="upper right",
        outside=True,
    )
    composition.apply_legend_placement(legend, placement)
    bounds = legend.get_bbox_to_anchor().bounds
    expected = ax.transAxes.transform((1.02, 1.0))
    assert bounds[0] == expected[0]
    assert bounds[1] == expected[1]
    plt.close(figure)


def test_public_api_exports_composition():
    from wenu import draw_planned_chart_legends as exported

    assert exported is draw_planned_chart_legends
