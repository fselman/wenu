"""Milestone 46A observer-local AltAz grid contracts."""

import argparse
from types import SimpleNamespace

import numpy as np

from wenu import (
    AltAzGrid,
    AtlasChartStyle,
    CelestialSphere,
    Observer,
    add_chart_arguments,
    chart_detail_overrides,
)
from wenu.charts.detail import AdaptiveDetailPolicy, apply_detail_overrides
from wenu.charts.detail_application import apply_resolved_detail


class Grid:
    layer_name = "coordinates_grid"

    def __init__(self, coordinate_system):
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
        SimpleNamespace(
            width_inches=7.0,
            font_scale=1.0,
            symbol_scale=1.0,
        ),
    )


def test_altaz_geometry_is_native_and_horizon_is_opt_in():
    grid = AltAzGrid(
        None,
        azimuth=(0, 90),
        altitude=(15, 30),
        samples=5,
    )
    geometry = grid.spherical_geometry(
        SimpleNamespace(
            t_astropy=SimpleNamespace(
                isot="2026-08-28T00:00:00.000", scale="utc"
            )
        )
    )

    assert set(geometry.components) == {"meridians", "parallels"}
    meridians = geometry.components["meridians"]
    parallels = geometry.components["parallels"]
    assert np.all(meridians.lon_deg[0] == 0.0)
    assert np.all(meridians.lon_deg[1] == 90.0)
    assert np.all(parallels.lat_deg[0] == 15.0)
    assert np.all(parallels.lat_deg[1] == 30.0)
    assert geometry.metadata["coordinate_system"] == "altaz"


def test_registered_altaz_grid_uses_observer_and_direct_geometry():
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    sky = CelestialSphere(observer)
    grid = sky.add_altaz_grid(azimuth=(0, 90), altitude=(15, 30))

    assert grid in sky.layers
    assert grid.observer is observer
    assert grid.coordinate_system == "altaz"
    assert grid.include_horizon is False


def test_altaz_switch_and_labels_are_independent_and_opt_in():
    for option, labels in (
        ("--altaz-grid", frozenset()),
        ("--altaz-grid-labels", frozenset({"altaz_grid"})),
    ):
        overrides = chart_detail_overrides(parser().parse_args([option]))
        detail = apply_detail_overrides(adaptive_detail(), overrides)

        assert detail.layer_enabled("altaz_grid")
        assert not detail.layer_enabled("equatorial_grid")
        assert detail.grid_label_layers == labels


def test_altaz_labels_apply_only_to_altaz_object():
    grids = tuple(
        AltAzGrid(None) if name == "altaz" else Grid(name)
        for name in ("altaz", "equatorial", "ecliptic", "galactic")
    )
    sky = SimpleNamespace(layers=grids)
    overrides = chart_detail_overrides(
        parser().parse_args(["--altaz-grid-labels"])
    )
    detail = apply_detail_overrides(adaptive_detail(), overrides)
    application = apply_resolved_detail(sky, detail)

    assert tuple(
        application.layer_options[grid]["render"]["draw_labels"]
        for grid in grids
    ) == (True, False, False, False)


def test_atlas_print_altaz_line_and_label_color_is_gray():
    options = AtlasChartStyle().as_publication_style()._grid_options(
        AltAzGrid(None)
    )["render"]

    assert options["style"]["color"] == "#707070"
    assert options["label_style"]["color"] == "#707070"


def test_altaz_labels_contain_only_numeric_degree_values():
    formatter = AtlasChartStyle().as_publication_style()._coordinate_label

    assert formatter("azimuth_330") == "330°"
    assert formatter("altitude_45") == "+45°"
