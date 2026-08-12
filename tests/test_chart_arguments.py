"""Milestone 44F.B.1 shared chart-control contracts."""

import argparse

import pytest

from wenu import (
    ChartStyleOverrides,
    RegionalChart,
    add_chart_arguments,
    chart_content_options,
    chart_detail_overrides,
    chart_legend_selection,
    chart_style_overrides,
    compose_chart,
)


def parser():
    value = argparse.ArgumentParser()
    return add_chart_arguments(
        value,
        default_output="output/reference.png",
    )


def test_shared_content_and_legends_are_opt_in():
    arguments = parser().parse_args([])

    assert chart_content_options(arguments).magnitude_limit is None
    assert chart_content_options(arguments).constellation_lines is False
    assert chart_content_options(arguments).constellation_labels is False
    assert chart_content_options(arguments).constellation_boundaries is False
    assert chart_content_options(arguments).horizon is False
    assert chart_content_options(arguments).horizon_mask is False
    assert chart_content_options(arguments).equatorial_grid is False
    assert chart_content_options(arguments).equatorial_grid_labels is False
    assert chart_content_options(arguments).ecliptic_grid is False
    assert chart_content_options(arguments).ecliptic_grid_labels is False
    assert chart_content_options(arguments).galactic_grid is False
    assert chart_content_options(arguments).galactic_grid_labels is False
    assert chart_content_options(arguments).grid_references == frozenset()
    assert chart_content_options(arguments).poles is False
    assert chart_content_options(arguments).pole_labels is False
    assert chart_legend_selection(arguments).objects is False
    assert chart_legend_selection(arguments).stellar_magnitudes is False
    assert chart_legend_selection(arguments).stellar_counts is False


def test_shared_content_switches_resolve_independently():
    arguments = parser().parse_args(
        [
            "--magnitude-limit", "4.5",
            "--constellation-lines",
            "--constellation-labels",
            "--constellation-boundaries",
            "--horizon",
            "--horizon-mask",
            "--equatorial-grid",
            "--equatorial-grid-labels",
            "--ecliptic-grid",
            "--ecliptic-grid-labels",
            "--galactic-grid",
            "--galactic-grid-labels",
            "--grid-references", "equatorial,ecliptic,galactic",
            "--poles",
            "--pole-labels",
        ]
    )
    content = chart_content_options(arguments)

    assert content.magnitude_limit == pytest.approx(4.5)
    assert content.constellation_lines is True
    assert content.constellation_labels is True
    assert content.constellation_boundaries is True
    assert content.horizon is True
    assert content.horizon_mask is True
    assert content.equatorial_grid is True
    assert content.equatorial_grid_labels is True
    assert content.ecliptic_grid is True
    assert content.ecliptic_grid_labels is True
    assert content.galactic_grid is True
    assert content.galactic_grid_labels is True
    assert content.grid_references == frozenset(
        {"equatorial", "ecliptic", "galactic"}
    )
    assert content.poles is True
    assert content.pole_labels is True


def test_magnitude_limit_must_be_finite():
    with pytest.raises(ValueError):
        chart_content_options(
            parser().parse_args(["--magnitude-limit", "nan"])
        )


def test_grid_reference_selection_is_comma_separated_and_validated():
    selected = chart_content_options(
        parser().parse_args(
            ["--grid-references", "equatorial, galactic"]
        )
    )
    all_references = chart_content_options(
        parser().parse_args(["--grid-references", "all"])
    )

    assert selected.grid_references == frozenset(
        {"equatorial", "galactic"}
    )
    assert all_references.grid_references == frozenset(
        {"equatorial", "ecliptic", "galactic"}
    )
    with pytest.raises(SystemExit):
        parser().parse_args(
            ["--grid-references", "all,ecliptic"]
        )
    with pytest.raises(SystemExit):
        parser().parse_args(["--grid-references", "horizontal"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--references"])


def test_legend_convenience_and_individual_switches():
    both = chart_legend_selection(parser().parse_args(["--legends"]))
    objects = chart_legend_selection(
        parser().parse_args(["--object-legend"])
    )
    counted = chart_legend_selection(
        parser().parse_args(["--magnitude-legend", "--star-counts"])
    )
    counts_without_scale = chart_legend_selection(
        parser().parse_args(["--star-counts"])
    )

    assert both.objects is True
    assert both.stellar_magnitudes is True
    assert objects.objects is True
    assert objects.stellar_magnitudes is False
    assert counted.stellar_magnitudes is True
    assert counted.stellar_counts is True
    assert counts_without_scale.stellar_counts is False


def test_style_arguments_resolve_to_immutable_overrides():
    arguments = parser().parse_args(
        [
            "--constellation-line-width", "2.25",
            "--constellation-line-color", "white",
            "--constellation-label-color", "gold",
            "--constellation-boundary-width", "0.75",
            "--constellation-boundary-color", "silver",
        ]
    )

    assert chart_style_overrides(arguments) == ChartStyleOverrides(
        constellation_linewidth=2.25,
        constellation_line_color="white",
        constellation_label_color="gold",
        boundary_linewidth=0.75,
        boundary_color="silver",
        draw_coordinate_labels=None,
    )


def test_grid_labels_enable_only_matching_grid_in_detail():
    arguments = parser().parse_args(["--ecliptic-grid-labels"])
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)
    composition = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
        detail_overrides=chart_detail_overrides(arguments),
        style_overrides=chart_style_overrides(arguments),
    )

    assert "ecliptic_grid" in composition.detail.enabled_layers
    assert "equatorial_grid" not in composition.detail.enabled_layers
    assert "galactic_grid" not in composition.detail.enabled_layers
    assert composition.detail.grid_label_layers == frozenset(
        {"ecliptic_grid"}
    )
    assert composition.style.grids.draw_coordinate_labels is False


@pytest.mark.parametrize("name", [
    "constellation_linewidth",
    "boundary_linewidth",
])
def test_style_widths_must_be_finite_and_non_negative(name):
    with pytest.raises(ValueError):
        ChartStyleOverrides(**{name: -0.1})
    with pytest.raises(ValueError):
        ChartStyleOverrides(**{name: float("nan")})


def test_explicit_style_values_apply_after_mode_defaults():
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)
    default = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
    )
    overridden = compose_chart(
        chart,
        style="cartoon",
        mode="presentation",
        style_overrides=ChartStyleOverrides(
            constellation_linewidth=2.25,
            constellation_line_color="white",
        ),
    )

    assert default.style.grids.constellation_line_color == "#FFE066"
    assert overridden.style.grids.constellation_linewidth == pytest.approx(
        2.25
    )
    assert overridden.style.grids.constellation_line_color == "white"
    assert overridden.context == default.context
    assert overridden.detail == default.detail


def test_empty_overrides_preserve_resolved_mode_style():
    chart = RegionalChart(45.0, 180.0, 20.0, 15.0)
    default = compose_chart(chart, style="atlas", mode="presentation")
    empty = compose_chart(
        chart,
        style="atlas",
        mode="presentation",
        style_overrides=ChartStyleOverrides(),
    )

    assert empty.style == default.style
    assert empty.context == default.context
