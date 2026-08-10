"""Shared behavioral contracts for Wenu's canonical examples."""

import ast
from functools import lru_cache
import importlib.util
from pathlib import Path

import pytest

from wenu import CANONICAL_CHART_PRODUCTS, chart_product_options


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATHS = (
    ROOT / "examples" / "planisphere.py",
    ROOT / "examples" / "regional_constellation_group.py",
    ROOT / "examples" / "regional_constellation.py",
    ROOT / "examples" / "circumpolar.py",
    ROOT / "examples" / "binocular_object.py",
)


@lru_cache(maxsize=None)
def load_example(path):
    spec = importlib.util.spec_from_file_location(
        f"canonical_{path.stem}", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def calls_named(tree, name):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name)
            and node.func.id == name
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == name
        )
    )


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_selected_product_uses_the_shared_cli_contract(path):
    arguments = load_example(path).parser().parse_args([
        "--style", "cartoon",
        "--mode", "presentation",
        "--output", "output/documented.png",
    ])
    options = chart_product_options(arguments)

    assert options.style == "cartoon"
    assert options.mode == "presentation"
    assert options.output == Path("output/documented.png")
    assert len(options.products) == 1


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_all_products_use_the_deterministic_shared_matrix(path):
    arguments = load_example(path).parser().parse_args([
        "--all-products",
        "--output", "output/gallery",
    ])
    options = chart_product_options(arguments)

    assert options.products == CANONICAL_CHART_PRODUCTS
    assert [
        output.name
        for _, output in options.outputs(stem=path.stem)
    ] == [
        f"{path.stem}-atlas-print.png",
        f"{path.stem}-atlas-presentation.png",
        f"{path.stem}-cartoon-print.png",
        f"{path.stem}-cartoon-presentation.png",
    ]


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_shared_content_legend_and_credit_controls_are_available(path):
    arguments = load_example(path).parser().parse_args([
        "--magnitude-limit", "4.25",
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

    assert arguments.magnitude_limit == pytest.approx(4.25)
    assert arguments.constellation_labels is True
    assert arguments.constellation_boundaries is True
    assert arguments.grid_references == frozenset({
        "equatorial", "ecliptic", "galactic",
    })
    assert arguments.poles is True
    assert arguments.pole_labels is True
    assert arguments.object_legend is True
    assert arguments.magnitude_legend is True
    assert arguments.star_counts is True
    assert arguments.credits is True


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_examples_use_public_composition_without_rendering_internals(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for required in (
        "add_chart_arguments",
        "chart_product_options",
        "compose_chart",
        "export",
    ):
        assert calls_named(tree, required)
    for prohibited in (
        "savefig",
        "set_clip_boundary",
        "set_clip_path",
        "clip_to_boundary",
    ):
        assert calls_named(tree, prohibited) == ()


def test_regression_fixtures_are_test_local():
    fixtures = ROOT / "tests" / "fixtures" / "example_regressions"

    assert fixtures.is_dir()
    assert all(
        path.suffix == ".py"
        for path in fixtures.iterdir()
        if path.is_file()
    )


def test_tests_do_not_reference_deleted_user_examples():
    fixtures = ROOT / "tests" / "fixtures" / "example_regressions"
    deleted = {path.name for path in fixtures.iterdir()}

    for test in (ROOT / "tests").glob("test_*.py"):
        source = test.read_text(encoding="utf-8")
        for name in deleted:
            assert f"examples/{name}" not in source
