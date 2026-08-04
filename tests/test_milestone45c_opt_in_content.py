"""Milestone 45C contracts for explicit celestial reference content."""

import argparse
from types import SimpleNamespace

import pytest

from wenu import (
    AdaptiveDetailPolicy,
    CartoonDetailPolicy,
    add_chart_arguments,
    chart_detail_overrides,
)
from wenu.charts.detail import apply_detail_overrides
from wenu.charts.detail_application import apply_resolved_detail


OPTIONAL_LAYERS = frozenset(
    {
        "constellation_lines",
        "constellation_labels",
        "constellation_boundaries",
        "equatorial_grid",
        "ecliptic_grid",
        "galactic_grid",
    }
)


class Layer:
    def __init__(self, name, coordinate_system=None):
        self.layer_name = name
        if coordinate_system is not None:
            self.coordinate_system = coordinate_system


def parser():
    value = argparse.ArgumentParser()
    return add_chart_arguments(value, default_output="output/test.png")


def adaptive_detail():
    return AdaptiveDetailPolicy().resolve(
        SimpleNamespace(
            visible_solid_angle_sq_deg=400.0,
            angular_area_deg2=400.0,
        ),
        SimpleNamespace(width_inches=7.0, font_scale=1.0, symbol_scale=1.0),
    )


def test_default_arguments_disable_all_optional_content():
    overrides = chart_detail_overrides(parser().parse_args([]))

    for base in (
        adaptive_detail(),
        CartoonDetailPolicy().resolve(object(), object()),
    ):
        detail = apply_detail_overrides(base, overrides)
        assert all(not detail.layer_enabled(name) for name in OPTIONAL_LAYERS)
        assert detail.grid_label_layers == frozenset()
        assert detail.constellation_star_mode == "none"


@pytest.mark.parametrize(
    ("option", "layer"),
    (
        ("--constellation-lines", "constellation_lines"),
        ("--constellation-labels", "constellation_labels"),
        ("--constellation-boundaries", "constellation_boundaries"),
        ("--equatorial-grid", "equatorial_grid"),
        ("--ecliptic-grid", "ecliptic_grid"),
        ("--galactic-grid", "galactic_grid"),
    ),
)
def test_each_content_switch_enables_only_its_layer(option, layer):
    overrides = chart_detail_overrides(parser().parse_args([option]))
    detail = apply_detail_overrides(adaptive_detail(), overrides)

    assert detail.layer_enabled(layer)
    assert all(
        not detail.layer_enabled(other)
        for other in OPTIONAL_LAYERS - {layer}
    )
    assert detail.constellation_star_mode == (
        "selected" if layer == "constellation_lines" else "none"
    )


@pytest.mark.parametrize(
    ("option", "layer"),
    (
        ("--equatorial-grid-labels", "equatorial_grid"),
        ("--ecliptic-grid-labels", "ecliptic_grid"),
        ("--galactic-grid-labels", "galactic_grid"),
    ),
)
def test_grid_label_switch_enables_only_matching_grid(option, layer):
    overrides = chart_detail_overrides(parser().parse_args([option]))
    detail = apply_detail_overrides(adaptive_detail(), overrides)

    assert detail.grid_label_layers == frozenset({layer})
    assert detail.layer_enabled(layer)
    assert all(
        not detail.layer_enabled(other)
        for other in OPTIONAL_LAYERS - {layer}
    )


def test_grid_labels_are_applied_per_grid_object_not_global_style():
    grids = tuple(
        Layer("coordinates_grid", name)
        for name in ("equatorial", "ecliptic", "galactic")
    )
    sky = SimpleNamespace(layers=grids)
    overrides = chart_detail_overrides(
        parser().parse_args(["--ecliptic-grid-labels"])
    )
    detail = apply_detail_overrides(adaptive_detail(), overrides)
    application = apply_resolved_detail(
        sky,
        detail,
        base_layer_options={
            grid: {"render": {"draw_labels": True}} for grid in grids
        },
    )

    assert tuple(
        application.layer_options[grid]["render"]["draw_labels"]
        for grid in grids
    ) == (False, True, False)


def test_removed_generic_grid_switches_are_rejected():
    with pytest.raises(SystemExit):
        parser().parse_args(["--coordinate-grid"])
    with pytest.raises(SystemExit):
        parser().parse_args(["--coordinate-grid-labels"])
