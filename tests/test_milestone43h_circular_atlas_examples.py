"""Declarative contracts for circular atlas examples."""

import ast
from pathlib import Path

import pytest


EXAMPLES = (
    Path("tests/fixtures/example_regressions/circumpolar_atlas.py"),
    Path("tests/fixtures/example_regressions/la_ligua_planisphere.py"),
)


def calls_named(tree, name):
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id == name
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == name
            )
        )
    )


@pytest.mark.parametrize("path", EXAMPLES)
def test_example_uses_one_canonical_export(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "draw_chart_legend") == ()
    assert calls_named(tree, "layer_options") == ()


@pytest.mark.parametrize("path", EXAMPLES)
def test_example_contains_no_grid_anchor_implementation(path):
    source = path.read_text(encoding="utf-8")

    assert "label_anchor" not in source
    assert "np.hypot" not in source
    assert "np.nanmedian" not in source
    assert "lambda curve" not in source


@pytest.mark.parametrize("path", EXAMPLES)
def test_example_requests_integrated_legends(path):
    source = path.read_text(encoding="utf-8")

    assert "legends=LegendOptions(" in source
    assert "objects=True" in source
    assert "stellar_magnitudes=False" in source
    assert "context=True" in source
