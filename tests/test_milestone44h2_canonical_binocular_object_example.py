"""Milestone 44H.2 canonical selected-object binocular example."""

import ast
import importlib.util
from pathlib import Path

import pytest

from wenu import BinocularChart, BoundaryKind, chart_product_options


EXAMPLE = Path("examples/binocular_object.py")


def load():
    spec = importlib.util.spec_from_file_location("binocular_object", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calls_named(tree, names):
    return tuple(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in names
    )


def test_example_uses_uniform_interface_without_rendering_internals():
    source = EXAMPLE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EXAMPLE))

    assert "add_chart_arguments" in source
    assert "chart_detail_overrides(arguments)" in source
    assert "chart_style_overrides(arguments)" in source
    assert "BinocularChart.from_coordinate" in source
    assert "RegionalChart" not in source
    assert "Circle" not in source
    assert "ExportOptions" not in source
    assert calls_named(
        tree,
        {"savefig", "set_clip_boundary", "set_clip_path"},
    ) == ()


def test_target_registry_includes_cen_a_and_omega_cen():
    module = load()

    assert tuple(module.TARGETS) == ("centaurus-a", "omega-centauri")
    assert module.TARGETS["centaurus-a"].identifier == "NGC 5128"
    assert module.TARGETS["omega-centauri"].identifier == "NGC 5139"


@pytest.mark.parametrize("target_key", ["centaurus-a", "omega-centauri"])
def test_chart_is_centered_on_selected_catalogue_target(target_key):
    module = load()
    sky, chart, target = module.build_chart(target_key, 7.0)
    horizontal = target.coordinate.transform_to(sky.observer.altaz_frame)
    x, y = chart.projection.project_spherical(
        horizontal.az.deg,
        horizontal.alt.deg,
    )

    assert isinstance(chart, BinocularChart)
    assert chart.field_diameter_deg == pytest.approx(7.0)
    assert chart.chart_context.boundary_kind == BoundaryKind.CIRCULAR
    assert x == pytest.approx(0.0, abs=2.0e-8)
    assert y == pytest.approx(0.0, abs=2.0e-8)
    assert sky.galaxies is not None
    assert sky.globular_clusters is not None


@pytest.mark.parametrize("target_key", ["centaurus-a", "omega-centauri"])
def test_all_selects_four_products_per_target(target_key):
    module = load()
    arguments = module.parser().parse_args([
        "--target", target_key,
        "--all-products",
    ])
    options = chart_product_options(arguments)

    assert len(options.products) == 4
    assert [
        path.name
        for _, path in options.outputs(stem=f"binocular-{target_key}")
    ] == [
        f"binocular-{target_key}-atlas-print.png",
        f"binocular-{target_key}-atlas-presentation.png",
        f"binocular-{target_key}-cartoon-print.png",
        f"binocular-{target_key}-cartoon-presentation.png",
    ]


def test_shared_content_legend_credit_and_field_switches_are_available():
    arguments = load().parser().parse_args([
        "--target", "omega-centauri",
        "--field-diameter", "8.0",
        "--magnitude-limit", "7.25",
        "--constellation-labels",
        "--constellation-boundaries",
        "--grid-references", "all",
        "--poles",
        "--pole-labels",
        "--object-legend",
        "--magnitude-legend",
        "--star-counts",
        "--credits",
    ])

    assert arguments.target == "omega-centauri"
    assert arguments.field_diameter == pytest.approx(8.0)
    assert arguments.magnitude_limit == pytest.approx(7.25)
    assert arguments.constellation_labels is True
    assert arguments.constellation_boundaries is True
    assert arguments.grid_references == frozenset(
        {"equatorial", "ecliptic", "galactic"}
    )
    assert arguments.poles is True
    assert arguments.pole_labels is True
    assert arguments.object_legend is True
    assert arguments.magnitude_legend is True
    assert arguments.star_counts is True
    assert arguments.credits is True


def test_cartoon_retains_both_supported_target_layer_types():
    module = load()

    assert module.STAR_MAGNITUDE_LIMIT == pytest.approx(11.0)
    assert module.CARTOON_CONTENT_LAYERS == frozenset({
        "stars",
        "constellation_lines",
        "galaxies",
        "globular_clusters",
    })
