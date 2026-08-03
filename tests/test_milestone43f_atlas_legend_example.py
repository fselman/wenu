"""Canonical-workflow contracts for the atlas legend example."""

import ast
from pathlib import Path


EXAMPLE = Path("tests/fixtures/example_regressions/atlas_style.py")


def source():
    return EXAMPLE.read_text(encoding="utf-8")


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


def test_example_requests_all_canonical_atlas_legends():
    text = source()
    assert 'style="atlas"' in text
    assert "mode=PrintMode(width_inches=10.0, dpi=600)" in text
    assert "objects=True" in text
    assert "stellar_magnitudes=True" in text
    assert "context=True" in text


def test_example_exports_composition_and_saves_only_once():
    tree = ast.parse(source(), filename=str(EXAMPLE))
    exports = calls_named(tree, "export")

    assert len(exports) == 1
    assert any(
        keyword.arg == "composition"
        for keyword in exports[0].keywords
    )
    assert calls_named(tree, "savefig") == ()
    assert calls_named(tree, "draw_chart_legend") == ()


def test_example_has_no_legacy_legend_or_export_coordination_imports():
    tree = ast.parse(source(), filename=str(EXAMPLE))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "draw_chart_legend" not in imported
    assert "ExportOptions" not in imported
