"""Milestone 44F canonical planisphere and regional examples."""

import ast
import importlib.util
from pathlib import Path

import pytest

from wenu import chart_product_options, compose_chart


EXAMPLES = (
    Path("examples/planisphere.py"),
    Path("examples/regional_constellation_group.py"),
    Path("examples/regional_constellation.py"),
)


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calls_named(tree, name):
    return tuple(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id == name
            or isinstance(node.func, ast.Attribute) and node.func.attr == name
        )
    )


@pytest.mark.parametrize("path", EXAMPLES)
def test_canonical_examples_use_public_composition_and_export(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    assert calls_named(tree, "add_chart_product_arguments")
    assert calls_named(tree, "chart_product_options")
    assert calls_named(tree, "compose_chart")
    assert calls_named(tree, "export")
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "set_clip_boundary") == ()
    assert calls_named(tree, "set_clip_path") == ()


@pytest.mark.parametrize("path", EXAMPLES)
def test_all_selects_four_products_for_every_family(path):
    module = load(path)
    arguments = module.parser().parse_args(["--all"])
    options = chart_product_options(arguments)

    assert len(options.products) == 4


def test_group_mask_is_union_of_selected_iau_regions():
    module = load(EXAMPLES[1])
    _, summer, _ = module.build_chart("summer-triangle", mask=True)
    _, center, _ = module.build_chart("galactic-center", mask=True)

    assert summer.outside_mask_constellations == module.GROUPS[
        "summer-triangle"
    ]["boundaries"]
    assert center.outside_mask_constellations == module.GROUPS[
        "galactic-center"
    ]["boundaries"]
    assert center.outside_mask_constellations[-1] == "Ser"


def test_single_mask_follows_exactly_one_iau_region():
    module = load(EXAMPLES[2])
    _, chart = module.build_chart("Cru", mask=True)

    assert chart.outside_mask_constellations == ("Cru",)
    assert chart.label_selection == ("Cru",)


def test_group_framing_accepts_width_height_and_position_angle():
    module = load(EXAMPLES[1])
    _, chart, _ = module.build_chart(
        "summer-triangle",
        field_width_deg=80.0,
        field_height_deg=50.0,
        position_angle_deg=17.0,
    )

    assert chart.field_width_deg == pytest.approx(80.0)
    assert chart.field_height_deg == pytest.approx(50.0)
    assert chart.position_angle_deg == pytest.approx(17.0)


def test_single_framing_accepts_width_height_and_position_angle():
    module = load(EXAMPLES[2])
    arguments = module.parser().parse_args([])
    _, default = module.build_chart("Cru")
    _, rotated = module.build_chart(
        "Cru",
        field_width_deg=20.0,
        field_height_deg=12.0,
        position_angle_deg=-25.0,
    )

    assert arguments.field_width == pytest.approx(18.0)
    assert arguments.field_height == pytest.approx(16.0)
    assert default.field_width_deg == pytest.approx(18.0)
    assert default.field_height_deg == pytest.approx(16.0)
    assert rotated.field_width_deg == pytest.approx(20.0)
    assert rotated.field_height_deg == pytest.approx(12.0)
    assert rotated.position_angle_deg == pytest.approx(-25.0)


def test_style_and_mode_do_not_change_example_geometry():
    module = load(EXAMPLES[2])
    _, chart = module.build_chart("Cru", mask=False)
    contexts = [
        compose_chart(chart, style=style, mode=mode).context
        for style in ("atlas", "cartoon")
        for mode in ("print", "presentation")
    ]

    assert all(
        context.viewport == contexts[0].viewport
        and context.tangent_longitude_deg
        == contexts[0].tangent_longitude_deg
        and context.tangent_latitude_deg
        == contexts[0].tangent_latitude_deg
        for context in contexts
    )


@pytest.mark.parametrize("path", EXAMPLES)
def test_atlas_examples_declare_stellar_detail_for_legends(path):
    source = path.read_text(encoding="utf-8")
    expected_limit = 5.0 if path == EXAMPLES[0] else 6.5

    assert "FixedDetailPolicy" in source
    assert f"star_magnitude_limit={expected_limit}" in source
    assert 'product.style == "cartoon"' in source


def test_object_rich_examples_use_curated_catalogue_selections():
    for path in EXAMPLES[:2]:
        source = path.read_text(encoding="utf-8")
        assert "add_open_clusters(selected=" in source
        assert "add_planetary_nebulae(selected=" in source
        assert "add_supernova_remnants(selected=" in source


@pytest.mark.parametrize("path", EXAMPLES)
def test_pole_crosses_and_labels_are_independently_optional(path):
    module = load(path)

    crosses_only = module.parser().parse_args(["--poles"])
    labeled = module.parser().parse_args(["--poles", "--pole-labels"])

    assert crosses_only.poles is True
    assert crosses_only.pole_labels is False
    assert labeled.poles is True
    assert labeled.pole_labels is True
    assert "labels=arguments.pole_labels" in path.read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("path", EXAMPLES)
def test_examples_use_compact_configurable_context(path):
    module = load(path)
    arguments = module.parser().parse_args([])

    assert arguments.center is True
    assert arguments.grid is True
    assert arguments.location is False
    assert arguments.date is False
    assert arguments.local_time is False
    source = path.read_text(encoding="utf-8")
    assert "chart_context_lines(" in source
    assert "labels=False" in source


def test_planisphere_uses_magnitude_five():
    source = EXAMPLES[0].read_text(encoding="utf-8")
    assert source.count("star_magnitude_limit=5.0") == 1
    assert 'sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)' in source


def test_planisphere_catalogue_retains_constellation_line_vertices():
    module = load(EXAMPLES[0])
    sky, _ = module.build_chart()

    assert {78400, 107608}.issubset(set(sky.stars.catalog.index))
