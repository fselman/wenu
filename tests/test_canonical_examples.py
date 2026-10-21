"""Shared behavioral contracts for Wenu's canonical examples."""

import ast
from functools import lru_cache
import importlib.util
from pathlib import Path

import pytest

from wenu import CANONICAL_CHART_PRODUCTS, chart_product_options


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATHS = (
    ROOT / "examples" / "all_sky.py",
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
        "--constellation-labels", "Vir",
        "--constellation-boundaries", "Vir",
        "--horizon",
        "--horizon-mask",
        "--grid-references", "all",
        "--poles",
        "--pole-labels",
        "--object-legend",
        "--magnitude-legend",
        "--star-counts",
        "--credits",
    ])

    assert arguments.magnitude_limit == pytest.approx(4.25)
    assert arguments.constellation_labels == [("Vir",)]
    assert arguments.constellation_boundaries == [("Vir",)]
    assert arguments.horizon is True
    assert arguments.horizon_mask is True
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
        "generate_celestial_sphere",
        "get_chart_view",
        "add_chart_cli_arguments",
        "draw_chart_view_from_arguments",
    ):
        assert calls_named(tree, required)
    for prohibited in (
        "build_chart_request",
        "generate_chart_request",
        "compose_chart",
        "export",
        "savefig",
        "set_clip_boundary",
        "set_clip_path",
        "clip_to_boundary",
    ):
        assert calls_named(tree, prohibited) == ()


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_examples_are_short_declarations(path):
    assert len(path.read_text(encoding="utf-8").splitlines()) < 85


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


@pytest.mark.parametrize("path", EXAMPLE_PATHS)
def test_example_preparation_refusal_releases_owned_observer(path, monkeypatch):
    from types import SimpleNamespace
    module = load_example(path)
    closed = []
    active = SimpleNamespace(close=lambda: closed.append(True))
    monkeypatch.setattr(module, "Observer", lambda **kwargs: active)
    monkeypatch.setattr(module, "generate_celestial_sphere", object)
    def refuse(*args, **kwargs):
        raise RuntimeError("public view refusal")
    monkeypatch.setattr(module, "get_chart_view", refuse)
    with pytest.raises(RuntimeError, match="public view refusal"):
        module.chart_view(module.parser().parse_args([]))
    assert closed == [True]


@pytest.mark.parametrize("filename", ("planisphere.py", "binocular_object.py"))
def test_example_product_setup_refusal_releases_prepared_observer(filename, monkeypatch):
    from types import SimpleNamespace
    module = load_example(ROOT / "examples" / filename)
    closed = []
    def refuse(*args, **kwargs): raise RuntimeError("product setup refusal")
    if filename == "planisphere.py":
        view = SimpleNamespace(observer=SimpleNamespace(close=lambda: closed.append(True)))
        monkeypatch.setattr(module, "chart_cli_furniture", refuse)
    else:
        class View:
            observer = SimpleNamespace(close=lambda: closed.append(True))
            @property
            def target(self): return refuse()
        view = View()
    monkeypatch.setattr(module, "chart_view", lambda arguments: view)
    with pytest.raises(RuntimeError, match="product setup refusal"):
        module.generate(module.parser().parse_args([]))
    assert closed == [True]
