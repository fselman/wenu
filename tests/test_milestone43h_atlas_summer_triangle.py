"""Declarative export contracts for the Summer Triangle atlas example."""

import ast
from pathlib import Path


EXAMPLE = Path("tests/fixtures/example_regressions/atlas_summer_triangle.py")


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


def test_example_uses_one_canonical_composed_export():
    source = EXAMPLE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(EXAMPLE))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "draw_chart_legend") == ()
    assert calls_named(tree, "layer_options") == ()


def test_example_requests_integrated_object_and_context_legends():
    source = EXAMPLE.read_text(encoding="utf-8")

    assert "legends=LegendOptions(" in source
    assert "objects=True" in source
    assert "stellar_magnitudes=False" in source
    assert "context=True" in source


def test_example_has_no_legacy_export_or_legend_imports():
    tree = ast.parse(
        EXAMPLE.read_text(encoding="utf-8"),
        filename=str(EXAMPLE),
    )
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "ExportOptions" not in imported
    assert "draw_chart_legend" not in imported
