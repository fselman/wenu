from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend import Legend

from wenu import (
    StellarMagnitudeLegendStyle,
    draw_styled_stellar_magnitude_legend,
)


class Viewport:
    x_min = -1.0
    x_max = 1.0
    y_min = -1.0
    y_max = 1.0


def geometry():
    return (
        SimpleNamespace(
            metadata={"magnitude": np.asarray([-1.2, 0.2, 2.8])}
        ),
        SimpleNamespace(
            x=np.asarray([0.0, 0.2, 0.4]),
            y=np.asarray([0.0, 0.2, 0.4]),
        ),
    )


def test_default_style_is_separate_from_chart_style():
    style = StellarMagnitudeLegendStyle()
    assert style.enabled
    assert style.location == "lower right"
    assert style.title == "Stars"


def test_drawing_options_are_complete_and_stable():
    style = StellarMagnitudeLegendStyle(
        location="upper left",
        frame_on=False,
        font_size=8.0,
    )
    options = style.drawing_options()
    assert options["location"] == "upper left"
    assert options["frame_on"] is False
    assert options["font_size"] == 8.0
    assert "enabled" not in options


def test_styled_wrapper_draws_requested_legend():
    figure, ax = plt.subplots()
    spherical, projected = geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=3.0,
        color="navy",
        legend_style=StellarMagnitudeLegendStyle(
            location="upper left",
            title="Magnitude",
        ),
    )
    assert isinstance(result.artist, Legend)
    assert result.artist.get_title().get_text() == "Magnitude"
    assert result.scale.color == "navy"
    plt.close(figure)


def test_disabled_style_calculates_statistics_but_draws_nothing():
    figure, ax = plt.subplots()
    spherical, projected = geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=3.0,
        legend_style=StellarMagnitudeLegendStyle(enabled=False),
    )
    assert result.statistics.visible_count == 3
    assert result.scale is None
    assert result.artist is None
    plt.close(figure)


def test_two_legends_remain_present():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")
    spherical, projected = geometry()
    result = draw_styled_stellar_magnitude_legend(
        ax,
        spherical,
        projected,
        Viewport(),
        effective_limit=3.0,
        legend_style=StellarMagnitudeLegendStyle(
            location="lower right"
        ),
    )
    legends = [
        artist for artist in ax.get_children()
        if isinstance(artist, Legend)
    ]
    assert object_legend in legends
    assert result.artist in legends
    plt.close(figure)


def test_visual_example_is_importable_and_writes_output(tmp_path):
    import importlib.util
    from pathlib import Path

    path = Path("examples/stellar_magnitude_legend.py")
    specification = importlib.util.spec_from_file_location(
        "stellar_magnitude_legend_example",
        path,
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    destination = tmp_path / "reference.png"
    figure, _, object_legend, result = module.draw_reference(
        destination,
        dpi=80,
    )
    assert destination.is_file()
    assert object_legend is not result.artist
    assert result.drawn
    plt.close(figure)
