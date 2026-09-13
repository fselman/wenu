"""Canonical reusable comet-symbol geometry contracts."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
from matplotlib.path import Path
import numpy as np

from wenu.antisolar import (
    angular_separation_deg,
    antisolar_reference_direction,
)
from wenu.charts.style_components import ChartStyle, SolarSystemStyle
from wenu.charts.styles import PublicationStyle
from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.geometry.projected import ProjectedPoints
from wenu.geometry.spherical import SphericalPoints
from wenu.rendering.symbols import COMET_SYMBOL_GEOMETRY, DEFAULT_SYMBOLS
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor


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
    assert DEFAULT_SYMBOLS.comet_head is DEFAULT_SYMBOLS["comet_head"]
    assert DEFAULT_SYMBOLS.comet_head is not symbol


def test_comet_symbol_has_one_circle_seven_short_and_three_tail_strokes():
    symbol = DEFAULT_SYMBOLS.comet

    assert sum(symbol.codes == Path.MOVETO) == 11
    assert sum(symbol.codes == Path.CLOSEPOLY) == 1
    assert sum(DEFAULT_SYMBOLS.comet_head.codes == Path.MOVETO) == 8
    assert sum(DEFAULT_SYMBOLS.comet_head.codes == Path.CLOSEPOLY) == 1


def test_comet_line_appearance_is_style_owned_not_symbol_owned():
    first = ChartStyle(
        solar_system=SolarSystemStyle(comet_color="#123456")
    ).as_publication_style()
    second = ChartStyle(
        solar_system=SolarSystemStyle(comet_color="#abcdef")
    ).as_publication_style()

    assert first.comet_color == "#123456"
    assert second.comet_color == "#abcdef"
    assert first.comet_symbol_size == pytest.approx(492.8)
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

    spherical = SphericalPoints(
        [10.0, 10.01], [20.0, 20.0],
        coordinate_spec=CoordinateSpec(
            frame="icrs", origin="observer",
            position_status=PositionStatus.APPARENT,
        ),
        ids=["comet_2p", "comet_2p__antisolar_reference"],
        labels=["2P", None], names=["2P/Encke", None],
    )
    projected = ProjectedPoints(
        [1.0, 1.0], [2.0, 3.0],
        ids=spherical.ids, labels=spherical.labels, names=spherical.names,
        metadata={"comet_symbol_orientation_reference_index": 1},
    )
    prepared = options["prepare"](spherical, projected)
    render = options["render"](spherical, prepared)

    assert len(prepared) == 1
    assert prepared.metadata["comet_symbol_rotation_deg"] == pytest.approx(90)
    assert render["style"]["marker"] is not DEFAULT_SYMBOLS.comet
    assert render["style"]["edgecolors"] == "cyan"
    assert render["label_style"]["color"] == "cyan"


def test_antisolar_reference_is_a_small_offset_on_the_tail_axis():
    comet = (347.16284728400217, 11.5633172622082)
    sun = (227.79603677620744, -17.8009756969018)

    reference = antisolar_reference_direction(comet, sun)

    assert angular_separation_deg(comet, reference) == pytest.approx(1 / 60)


@pytest.mark.parametrize("sun", ((10.01, 20.0), (190.0, -20.0)))
def test_antisolar_reference_fails_closed_near_solar_alignment(sun):
    with pytest.raises(ValueError, match="orientation exclusion"):
        antisolar_reference_direction((10.0, 20.0), sun)


def test_suppressed_tail_uses_the_canonical_head_only_symbol():
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
    options = PublicationStyle().layer_options(sky)[layer]
    spherical = SphericalPoints(
        [10.0], [20.0],
        coordinate_spec=CoordinateSpec(
            frame="icrs", origin="observer",
            position_status=PositionStatus.APPARENT,
        ),
    )
    projected = ProjectedPoints(
        [1.0], [2.0], metadata={"comet_tail_suppressed": True}
    )

    prepared = options["prepare"](spherical, projected)
    render = options["render"](spherical, prepared)

    assert len(prepared) == 1
    assert render["style"]["marker"] is DEFAULT_SYMBOLS.comet_head


def test_comet_symbol_orientation_follows_projected_axis_without_mutation():
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
    options = PublicationStyle().layer_options(sky)[layer]
    spherical = SphericalPoints(
        [0.0, 0.01], [10.0, 10.0],
        coordinate_spec=CoordinateSpec(
            frame="icrs", origin="observer",
            position_status=PositionStatus.APPARENT,
        ),
    )
    original_vertices = DEFAULT_SYMBOLS.comet.vertices.copy()

    for coordinates, expected in (
        (([0.0, 1.0], [0.0, 0.0]), 0.0),
        (([0.0, 0.0], [0.0, -1.0]), -90.0),
    ):
        projected = ProjectedPoints(
            *coordinates,
            metadata={"comet_symbol_orientation_reference_index": 1},
        )
        prepared = options["prepare"](spherical, projected)
        assert prepared.metadata["comet_symbol_rotation_deg"] == pytest.approx(
            expected
        )
        render = options["render"](spherical, prepared)
        assert render["style"]["marker"] is not DEFAULT_SYMBOLS.comet

    assert np.array_equal(DEFAULT_SYMBOLS.comet.vertices, original_vertices)


def test_comet_symbol_has_comet_specific_semantic_path():
    descriptor = SolarSystemBodyDescriptor(
        target="2p", entity_key="comet_2p", display_name="2P/Encke",
        selection_key="2p", body_class="comet",
        canonical_designation="2P/Encke", iau_number=2,
    )
    layer = SimpleNamespace(
        layer_name="comet_2p", body_descriptor=descriptor,
        display_kind="symbolic_point",
    )

    assert semantic_layer_identity(layer).semantic_path == (
        "sky", "solar_system", "minor_bodies", "comets", "2p",
    )
