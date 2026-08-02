"""Milestone 44D chart credits and cumulative stellar counts."""

from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np

from wenu import FooterOptions, Viewport
from wenu.charts.footer_furniture import (
    draw_chart_footer,
    resolved_footer_text,
)
from wenu.charts.magnitude_legend import (
    cumulative_visible_star_counts,
    stellar_magnitude_scale,
)
from wenu.charts.magnitude_legend_matplotlib import (
    stellar_magnitude_handles,
)
from wenu.charts.rendered_legend_composition import _resolved_footprint
from wenu import BinocularChart


def geometry(magnitudes, x=None, y=None):
    magnitudes = np.asarray(magnitudes, dtype=float)
    spherical = SimpleNamespace(
        metadata={"magnitude": magnitudes}
    )
    projected = SimpleNamespace(
        x=np.asarray(
            np.zeros(magnitudes.size) if x is None else x,
            dtype=float,
        ),
        y=np.asarray(
            np.zeros(magnitudes.size) if y is None else y,
            dtype=float,
        ),
    )
    return spherical, projected


def test_cumulative_counts_use_only_rendered_geometry():
    spherical, projected = geometry([-1.0, 0.4, 1.8, 2.2])
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (-1, 0, 1, 2),
        effective_limit=2.0,
    )

    assert counts == (1, 1, 2, 3)


def test_counts_respect_viewport_and_custom_footprint():
    spherical, projected = geometry(
        [0.0, 0.5, 1.0, 1.5],
        x=[0.0, 0.4, 0.8, 2.0],
        y=[0.0, 0.0, 0.0, 0.0],
    )
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (0, 1, 2),
        effective_limit=2.0,
        footprint_contains=lambda x, y: np.hypot(x, y) <= 0.5,
    )

    assert counts == (1, 2, 2)


def test_circular_chart_predicate_excludes_viewport_corners():
    chart = BinocularChart(45.0, 180.0)
    contains = _resolved_footprint(chart, None)
    viewport = chart.chart_context.viewport
    center_x = (viewport.x_min + viewport.x_max) / 2.0
    center_y = (viewport.y_min + viewport.y_max) / 2.0

    assert bool(contains(np.asarray([center_x]), np.asarray([center_y]))[0])
    assert not bool(
        contains(
            np.asarray([viewport.x_max]),
            np.asarray([viewport.y_max]),
        )[0]
    )


def test_explicit_and_vertex_stars_count_when_they_were_rendered():
    # The rendered geometry is intentionally the authority: these two
    # retained stars need no catalogue-global identity lookup here.
    spherical, projected = geometry([1.2, 1.9])
    counts = cumulative_visible_star_counts(
        spherical,
        projected,
        Viewport(-1.0, 1.0, -1.0, 1.0),
        (1, 2),
        effective_limit=2.0,
    )

    assert counts == (0, 2)


def test_count_labels_are_optional_and_keep_signed_magnitudes():
    plain = stellar_magnitude_scale(-1.0, 1.0)
    counted = stellar_magnitude_scale(
        -1.0,
        1.0,
        cumulative_counts=(1, 3, 8),
    )

    assert [handle.get_label() for handle in stellar_magnitude_handles(plain)] == [
        "-1",
        "0",
        "1",
    ]
    assert [
        handle.get_label() for handle in stellar_magnitude_handles(counted)
    ] == ["-1 (1)", "0 (3)", "1 (8)"]


def test_footer_sides_are_independent_and_version_is_resolved():
    left = resolved_footer_text(
        FooterOptions(copyright="© Chart author"),
        package_version="9.8.7",
    )
    right = resolved_footer_text(
        FooterOptions(application=True),
        package_version="9.8.7",
    )

    assert left == ("© Chart author", None)
    assert right == (None, "Wenu 9.8.7")


def test_footer_artists_use_figure_margin_and_reserve_axes_space():
    figure, ax = plt.subplots(figsize=(7.0, 5.0))
    renderer = SimpleNamespace(ax=ax)
    mode = SimpleNamespace(font_scale=1.0)
    result = draw_chart_footer(
        renderer,
        FooterOptions(
            application=True,
            copyright="© Chart author",
        ),
        mode,
        package_version="9.8.7",
    )

    assert [artist.get_ha() for artist in result.artists] == ["left", "right"]
    assert [artist.get_position()[0] for artist in result.artists] == [0.01, 0.99]
    assert all(artist.get_position()[1] < ax.get_position().y0 for artist in result.artists)
    plt.close(figure)


def test_empty_footer_draws_nothing_and_changes_no_layout():
    figure, ax = plt.subplots()
    before = ax.get_position().bounds
    result = draw_chart_footer(
        SimpleNamespace(ax=ax),
        FooterOptions(),
        SimpleNamespace(font_scale=1.0),
    )

    assert result is None
    assert ax.get_position().bounds == before
    plt.close(figure)
