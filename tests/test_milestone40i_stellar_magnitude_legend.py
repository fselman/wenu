import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.legend import Legend

from wenu.charts.magnitude_legend import (
    StellarMagnitudeScale,
    stellar_magnitude_scale,
)
from wenu.charts.magnitude_legend_matplotlib import (
    draw_stellar_magnitude_legend,
    stellar_magnitude_handles,
)


def scale():
    return stellar_magnitude_scale(
        -1.2,
        4.8,
        area_scale=1.7,
        color="black",
        alpha=0.8,
        title="Stellar magnitude",
    )


def test_handles_use_integer_magnitude_labels():
    handles = stellar_magnitude_handles(scale())
    assert [handle.get_label() for handle in handles] == [
        "-1", "0", "1", "2", "3", "4"
    ]


def test_handle_sizes_are_square_roots_of_scatter_areas():
    current = scale()
    handles = stellar_magnitude_handles(current)
    for entry, handle in zip(current.entries, handles):
        assert handle.get_markersize() ** 2 == pytest.approx(entry.area)


def test_legend_uses_scale_title_and_requested_location():
    figure, ax = plt.subplots()
    legend = draw_stellar_magnitude_legend(
        ax,
        scale(),
        location="upper left",
    )
    assert isinstance(legend, Legend)
    assert legend.get_title().get_text() == "Stellar magnitude"
    assert [text.get_text() for text in legend.get_texts()] == [
        "-1", "0", "1", "2", "3", "4"
    ]
    plt.close(figure)


def test_magnitude_legend_preserves_existing_object_legend():
    figure, ax = plt.subplots()
    ax.plot([], [], marker="s", label="Galaxy")
    object_legend = ax.legend(loc="upper right")

    magnitude_legend = draw_stellar_magnitude_legend(
        ax,
        scale(),
        location="lower right",
    )

    assert ax.get_legend() is object_legend
    legends = [
        artist
        for artist in ax.get_children()
        if isinstance(artist, Legend)
    ]
    assert object_legend in legends
    assert magnitude_legend in legends
    assert magnitude_legend is not object_legend
    plt.close(figure)


def test_empty_scale_does_not_add_a_legend():
    figure, ax = plt.subplots()
    empty = StellarMagnitudeScale(
        entries=(),
        color="black",
        alpha=1.0,
        title="Stellar magnitude",
    )
    assert draw_stellar_magnitude_legend(ax, empty) is None
    assert not any(
        isinstance(artist, Legend)
        for artist in ax.get_children()
    )
    plt.close(figure)


def test_public_api_exports_renderer():
    from wenu import draw_stellar_magnitude_legend as exported

    assert exported is draw_stellar_magnitude_legend
