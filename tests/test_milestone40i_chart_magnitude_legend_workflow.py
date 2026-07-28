from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.legend import Legend

from wenu.charts.magnitude_legend_workflow import (
    StellarMagnitudeLegendResult,
    draw_visible_stellar_magnitude_legend,
)


class Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def geometry():
    spherical = SimpleNamespace(
        metadata={
            "magnitude": np.asarray(
                [-1.2, 0.4, 2.2, 4.7, 1.0],
                dtype=float,
            )
        }
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.4, -0.5, 0.8, 2.0]),
        y=np.asarray([0.0, 0.3, 0.5, -0.7, 0.0]),
    )
    return spherical, projected


def test_workflow_uses_only_visible_stars():
    figure, ax = plt.subplots()
    spherical, projected = geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=4.0,
        area_scale=1.5,
    )
    assert isinstance(result, StellarMagnitudeLegendResult)
    assert result.statistics.visible_count == 3
    assert result.statistics.brightest_magnitude == pytest.approx(-1.2)
    assert result.statistics.faintest_magnitude == pytest.approx(2.2)
    assert [entry.magnitude for entry in result.scale.entries] == [
        -1, 0, 1, 2
    ]
    assert isinstance(result.artist, Legend)
    assert result.drawn
    plt.close(figure)


def test_workflow_preserves_the_existing_object_legend():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")
    spherical, projected = geometry()

    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=4.0,
        location="lower right",
    )
    assert ax.get_legend() is object_legend
    assert result.artist is not object_legend
    plt.close(figure)


def test_workflow_respects_a_chart_footprint():
    figure, ax = plt.subplots()
    spherical, projected = geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=4.0,
        footprint_contains=lambda x, y: x * x + y * y <= 0.25,
    )
    assert result.statistics.visible_count == 2
    assert [entry.magnitude for entry in result.scale.entries] == [-1, 0]
    plt.close(figure)


def test_empty_visible_set_produces_no_scale_or_artist():
    figure, ax = plt.subplots()
    spherical, projected = geometry()
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=-2.0,
    )
    assert result.statistics.visible_count == 0
    assert result.scale is None
    assert result.artist is None
    assert not result.drawn
    plt.close(figure)


def test_interval_without_an_integer_produces_no_artist():
    figure, ax = plt.subplots()
    spherical = SimpleNamespace(
        metadata={"magnitude": np.asarray([0.1, 0.8])}
    )
    projected = SimpleNamespace(
        x=np.asarray([0.0, 0.2]),
        y=np.asarray([0.0, 0.2]),
    )
    result = draw_visible_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=1.0,
    )
    assert result.statistics.visible_count == 2
    assert result.scale is not None
    assert result.scale.entries == ()
    assert result.artist is None
    plt.close(figure)


def test_public_api_exports_workflow():
    from wenu import draw_visible_stellar_magnitude_legend as exported

    assert exported is draw_visible_stellar_magnitude_legend
