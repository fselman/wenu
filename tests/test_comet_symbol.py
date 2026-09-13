"""Canonical reusable comet-symbol geometry contracts."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
from matplotlib.path import Path

from wenu.charts.style_components import ChartStyle, SolarSystemStyle
from wenu.charts.styles import PublicationStyle
from wenu.rendering.symbols import COMET_SYMBOL_GEOMETRY, DEFAULT_SYMBOLS


def test_comet_symbol_geometry_is_one_immutable_wenu_value():
    geometry = COMET_SYMBOL_GEOMETRY

    assert geometry.circle_radius == pytest.approx(0.2304)
    assert len(geometry.short_spoke_angles_deg) == 7
    assert geometry.tail_angles_deg == pytest.approx((-12.5, 0.0, 12.5))
    assert geometry.tail_outer_radii[0] == geometry.tail_outer_radii[2]
    exposed_outer = geometry.outer_tail_radius - geometry.circle_radius
    exposed_central = geometry.central_tail_radius - geometry.circle_radius
    assert exposed_central == pytest.approx(1.5 * exposed_outer)
    with pytest.raises(FrozenInstanceError):
        geometry.tail_fan_angle_deg = 30.0


def test_comet_symbol_is_constructed_once_and_reused_by_name():
    symbol = DEFAULT_SYMBOLS.comet

    assert isinstance(symbol, Path)
    assert DEFAULT_SYMBOLS["comet"] is symbol
    assert DEFAULT_SYMBOLS.symbols["comet"] is symbol
    assert symbol is not DEFAULT_SYMBOLS.planetary_nebula


def test_comet_symbol_has_one_circle_seven_short_and_three_tail_strokes():
    symbol = DEFAULT_SYMBOLS.comet

    assert sum(symbol.codes == Path.MOVETO) == 11
    assert sum(symbol.codes == Path.CLOSEPOLY) == 1


def test_comet_line_appearance_is_style_owned_not_symbol_owned():
    first = ChartStyle(
        solar_system=SolarSystemStyle(comet_color="#123456")
    ).as_publication_style()
    second = ChartStyle(
        solar_system=SolarSystemStyle(comet_color="#abcdef")
    ).as_publication_style()

    assert first.comet_color == "#123456"
    assert second.comet_color == "#abcdef"
    assert first.comet_symbol_size == pytest.approx(30.8)
    assert first.comet_linewidth == pytest.approx(0.8)
    assert DEFAULT_SYMBOLS.comet is DEFAULT_SYMBOLS["comet"]


def test_publication_style_does_not_fall_back_to_venus_for_comets():
    style = PublicationStyle(comet_color="cyan", venus_color="magenta")

    assert style.comet_color == "cyan"
    assert style.comet_color != style.venus_color


def test_comet_layer_uses_canonical_marker_and_comet_style():
    class Layer:
        body_descriptor = SimpleNamespace(body_class="comet")
        request_draw_label = True

    class Sky:
        def __getattr__(self, name):
            del name
            return None

    layer = Layer()
    sky = Sky()
    sky.solar_system_bodies = {"2p": layer}
    sky.magellanic_cloud_isophotes = {}
    sky.coordinate_grids = ()
    sky.layers = ()

    options = PublicationStyle(comet_color="cyan").layer_options(sky)[layer]

    assert options["render"]["style"]["marker"] is DEFAULT_SYMBOLS.comet
    assert options["render"]["style"]["edgecolors"] == "cyan"
    assert options["render"]["label_style"]["color"] == "cyan"
